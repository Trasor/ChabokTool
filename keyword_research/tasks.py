from celery import shared_task
from django.conf import settings
from django.utils import timezone
import asyncio
import aiohttp
import time
import pandas as pd
from .models import Keyword, ResearchRequest
from .rate_limiter import SerperRateLimiter


# ✅ Rate Limiter مرکزی
RATE_LIMITER = SerperRateLimiter(max_qps=45)


@shared_task(bind=True, max_retries=0, queue='chaboktool_queue')
def process_keyword_research(self, request_id, file_path, description):
    """Task اصلی برای پردازش keyword research"""
    
    worker_name = self.request.hostname
    task_id_short = self.request.id[:8]
    
    print(f"\n{'='*60}")
    print(f"[{worker_name}] [{task_id_short}] STARTED")
    print(f"[{worker_name}] [{task_id_short}] Request ID: {request_id}")
    print(f"[{worker_name}] [{task_id_short}] SERP Provider: {settings.SERP_PROVIDER}")
    print(f"[{worker_name}] [{task_id_short}] Current QPS: {RATE_LIMITER.get_current_qps()}/45")
    print(f"{'='*60}\n")
    
    try:
        research_request = ResearchRequest.objects.get(id=request_id)
        research_request.status = 'running'
        research_request.save()
        
        # خواندن فایل
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, header=0)
        else:
            df = pd.read_excel(file_path, header=0)
        
        # پاک کردن Keywords قبلی
        Keyword.objects.filter(request=research_request).delete()
        
        # چک Duplicate Task
        existing_count = Keyword.objects.filter(request=research_request).count()
        if existing_count > 0:
            print(f"[{worker_name}] [{task_id_short}] ⚠️ DUPLICATE! Aborting.")
            research_request.status = 'failed'
            research_request.error_message = 'Duplicate task detected'
            research_request.save()
            return {'status': 'failed', 'error': 'Duplicate task'}
        
        total_keywords = len(df)
        print(f"[{worker_name}] [{task_id_short}] Total keywords: {total_keywords}")
        print(f"[{worker_name}] [{task_id_short}] AI Analysis: {'✅ Enabled' if research_request.ai_analysis_enabled else '❌ Disabled'}")
        
        task_start_time = time.time()
        
        # ✅ مرحله 1: جمع‌آوری داده‌ها
        keywords_data = []
        for index, row in df.iterrows():
            original_id = index + 1
            keyword = str(row.iloc[0]).strip()
            
            try:
                search_volume = int(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else 0
            except (ValueError, TypeError):
                search_volume = 0
            
            try:
                word_count = int(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else None
            except (ValueError, TypeError):
                word_count = None
            
            keywords_data.append({
                'original_id': original_id,
                'keyword': keyword,
                'search_volume': search_volume,
                'word_count': word_count
            })
        
        # ✅ مرحله 2: پردازش Parallel با Rate Limiting
        print(f"[{worker_name}] [{task_id_short}] Starting Parallel Processing (45 QPS)...")
        api_start = time.time()
        
        if settings.SERP_PROVIDER == 'serper':
            results = _fetch_serper_batch(keywords_data, worker_name, task_id_short, batch_size=50)
        else:
            # Apify Sequential (چون Async نداره)
            results = []
            for kw_data in keywords_data:
                links_str, titles_str = _fetch_apify_links(kw_data['keyword'], worker_name, task_id_short)
                results.append((links_str, titles_str))
                time.sleep(0.5)
        
        api_duration = time.time() - api_start
        print(f"[{worker_name}] [{task_id_short}] API Phase: {api_duration:.2f}s ({api_duration/60:.2f} min)")
        
        # ✅ مرحله 3: ذخیره در دیتابیس
        for kw_data, (links_str, titles_str) in zip(keywords_data, results):
            Keyword.objects.create(
                user=research_request.user,
                request=research_request,
                original_id=kw_data['original_id'],
                keyword=kw_data['keyword'],
                search_volume=kw_data['search_volume'],
                links=links_str,
                meta_titles=titles_str,
                word_count=kw_data['word_count'],
                status=0,
                description=description,
                akw_str=""
            )
        
        # ✅ مرحله 4: مقایسه PKW/AKW
        compare_start = time.time()
        print(f"[{worker_name}] [{task_id_short}] Starting PKW/AKW comparison...")
        
        _process_pkw_akw_comparison_in_task(research_request)
        
        compare_duration = time.time() - compare_start
        print(f"[{worker_name}] [{task_id_short}] Comparison: {compare_duration:.2f}s")
        
        # ✅ مرحله 5: تحلیل AI (اگه فعال بود)
        if research_request.ai_analysis_enabled:
            try:
                from ai_analyzer.analyzer import analyze_all_pkw
                analyze_all_pkw(research_request, worker_name, task_id_short)
            except Exception as e:
                print(f"[{worker_name}] [{task_id_short}] ❌ AI Analysis failed: {str(e)}")
        
        # تکمیل موفق
        research_request.status = 'completed'
        research_request.completed_date = timezone.now()
        research_request.save()
        
        total_time = time.time() - task_start_time
        
        print(f"\n{'='*60}")
        print(f"[{worker_name}] [{task_id_short}] COMPLETED")
        print(f"  ├─ API calls: {api_duration:.2f}s ({api_duration/total_time*100:.1f}%)")
        print(f"  ├─ Comparison: {compare_duration:.2f}s")
        print(f"  └─ Total: {total_time:.2f}s ({total_time/60:.2f} min)")
        print(f"{'='*60}\n")
        
        return {'status': 'completed', 'total': total_keywords}
    
    except Exception as e:
        print(f"\n[{worker_name}] [{task_id_short}] ❌ FAILED: {str(e)}\n")
        research_request.status = 'failed'
        research_request.error_message = str(e)
        research_request.completed_date = timezone.now()
        research_request.save()
        return {'status': 'failed', 'error': str(e)}


# ============================================================================
# Async Functions (45 QPS Parallel با Rate Limiting)
# ============================================================================

async def _fetch_serper_links_async(session, keyword, worker_name, task_id_short):
    """دریافت Async از Serper با Rate Limiting"""
    
    # ✅ گرفتن Token از Rate Limiter (حداکثر 30 ثانیه صبر)
    if not RATE_LIMITER.acquire(count=1, timeout=30):
        print(f"[{worker_name}] [{task_id_short}] ⚠️ '{keyword}' Rate Limit Timeout!")
        return "خطا", ""
    
    url = "https://google.serper.dev/search"
    payload = {
        "q": keyword,
        "gl": "ir",
        "hl": "fa",
        "num": 10,
        "location": "Germany"
    }
    headers = {
        "X-API-KEY": settings.SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    
    for attempt in range(3):
        try:
            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 429:
                    wait_time = (2 ** attempt)
                    print(f"[{worker_name}] [{task_id_short}] ⚠️ '{keyword}' RATE LIMIT! Retry {attempt+1}/3")
                    await asyncio.sleep(wait_time)
                    continue
                
                if response.status == 200:
                    data = await response.json()
                    results = data.get('organic', [])[:10]
                    
                    if len(results) >= 10:
                        links = [result.get('link', '') for result in results]
                        titles = [result.get('title', '') for result in results]
                        
                        links_str = " -------------- ".join(links)
                        titles_str = "\n".join(titles)
                        
                        return links_str, titles_str
                    else:
                        return "خطا", ""
                else:
                    if attempt < 2:
                        await asyncio.sleep(1)
                        continue
                    return "خطا", ""
        
        except Exception as e:
            if attempt < 2:
                await asyncio.sleep(1)
                continue
            print(f"[{worker_name}] [{task_id_short}] ❌ '{keyword}': {str(e)}")
            return "خطا", ""
    
    return "خطا", ""


async def _fetch_batch_async(keywords_data, worker_name, task_id_short):
    """پردازش Batch به صورت Async"""
    async with aiohttp.ClientSession() as session:
        tasks = []
        for kw_data in keywords_data:
            task = _fetch_serper_links_async(
                session, 
                kw_data['keyword'], 
                worker_name, 
                task_id_short
            )
            tasks.append(task)
        
        # اجرای همزمان (با Rate Limiting)
        results = await asyncio.gather(*tasks)
        return results


def _fetch_serper_batch(keywords_data, worker_name, task_id_short, batch_size=50):
    """Wrapper برای Async → Sync با Rate Limiting"""
    
    # تقسیم به Batch های 50 تایی
    batches = [keywords_data[i:i + batch_size] for i in range(0, len(keywords_data), batch_size)]
    
    all_results = []
    
    for batch_index, batch in enumerate(batches):
        current_qps = RATE_LIMITER.get_current_qps()
        print(f"[{worker_name}] [{task_id_short}] 📦 Batch {batch_index+1}/{len(batches)} ({len(batch)} keywords) | QPS: {current_qps}/45")
        
        # اجرای Async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(_fetch_batch_async(batch, worker_name, task_id_short))
        loop.close()
        
        all_results.extend(results)
        
        # Delay بین Batch ها (0.5s برای Safety)
        if batch_index < len(batches) - 1:
            time.sleep(0.5)
    
    return all_results


# ============================================================================
# Sync Functions (Fallback - Apify)
# ============================================================================

def _fetch_apify_links(keyword, worker_name, task_id_short):
    """دریافت لینک‌ها از Apify (Sequential - Fallback)"""
    import requests
    
    url = "https://api.apify.com/v2/acts/apify~google-search-scraper/runs"
    payload = {"queries": keyword, "maxPagesPerQuery": 2}
    headers = {
        "Authorization": f"Bearer {settings.APIFY_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = None
        for attempt in range(5):
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=120)
                if response.status_code == 429:
                    wait_time = (2 ** attempt)
                    print(f"[{worker_name}] [{task_id_short}] ⚠️ RATE LIMIT! Retry {attempt+1}/5")
                    time.sleep(wait_time)
                    continue
                break
            except requests.exceptions.RequestException:
                if attempt < 4:
                    time.sleep(1)
                else:
                    return "خطا", ""
        
        if response and response.status_code == 201:
            run_data = response.json()
            run_id = run_data['data']['id']
            
            max_wait = 600
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={settings.APIFY_TOKEN}"
                status_response = requests.get(status_url, timeout=30)
                status_data = status_response.json()
                
                if status_data['data']['status'] == 'SUCCEEDED':
                    dataset_id = status_data['data']['defaultDatasetId']
                    results_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={settings.APIFY_TOKEN}&format=json"
                    results_response = requests.get(results_url, timeout=60)
                    results = results_response.json()
                    
                    links = []
                    for result in results:
                        if 'organicResults' in result:
                            links.extend([item['url'] for item in result['organicResults'] if 'url' in item])
                    
                    links = links[:10]
                    links_str = " -------------- ".join(links) if len(links) == 10 else "خطا"
                    return links_str, ""
                
                elif status_data['data']['status'] in ['FAILED', 'ABORTED']:
                    return "خطا", ""
                
                time.sleep(5)
            
            return "خطا", ""
        else:
            return "خطا", ""
    
    except Exception as e:
        print(f"[{worker_name}] [{task_id_short}] ❌ EXCEPTION: {str(e)}")
        return "خطا", ""


# ============================================================================
# PKW/AKW Comparison
# ============================================================================

def _process_pkw_akw_comparison_in_task(research_request):
    """مقایسه و تشخیص PKW/AKW"""
    keywords = list(Keyword.objects.filter(request=research_request).order_by('id'))
    zero_status_keywords = [kw for kw in keywords if kw.status == 0]
    
    i = 0
    while i < len(zero_status_keywords):
        kw1 = zero_status_keywords[i]
        d1_links = set(kw1.links.split(" -------------- ")) if kw1.links and "خطا" not in kw1.links else set()
        
        j = i + 1
        while j < len(zero_status_keywords):
            kw2 = zero_status_keywords[j]
            d2_links = set(kw2.links.split(" -------------- ")) if kw2.links and "خطا" not in kw2.links else set()
            
            score = len(d1_links.intersection(d2_links))
            
            if score >= 6:
                if kw1.search_volume > kw2.search_volume or (kw1.search_volume == kw2.search_volume and kw1.id < kw2.id):
                    kw1.status = 1
                    kw1.search_volume += kw2.search_volume
                    
                    if kw1.akw_str:
                        kw1.akw_str += f" - {kw2.keyword}:{kw2.search_volume}"
                    else:
                        kw1.akw_str = f"{kw2.keyword}:{kw2.search_volume}"
                    
                    kw1.save()
                    kw2.status = 2
                    kw2.save()
                    zero_status_keywords.pop(j)
                    continue
                else:
                    kw2.status = 1
                    kw2.search_volume += kw1.search_volume
                    
                    if kw2.akw_str:
                        kw2.akw_str += f" - {kw1.keyword}:{kw1.search_volume}"
                    else:
                        kw2.akw_str = f"{kw1.keyword}:{kw1.search_volume}"
                    
                    kw2.save()
                    kw1.status = 2
                    kw1.save()
                    zero_status_keywords.pop(i)
                    i -= 1
                    break
            
            j += 1
        
        i += 1
    
    for kw in zero_status_keywords:
        kw.status = 1
        kw.save()