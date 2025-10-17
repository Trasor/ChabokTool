from celery import shared_task
from django.conf import settings
from django.utils import timezone
import requests
import time
import pandas as pd
from .models import Keyword, ResearchRequest


@shared_task(bind=True, max_retries=0)
def process_keyword_research(self, request_id, file_path, description):
    """Task اصلی برای پردازش keyword research"""
    try:
        research_request = ResearchRequest.objects.get(id=request_id)
        research_request.status = 'running'
        research_request.save()
        
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        Keyword.objects.filter(user=research_request.user).delete()
        total_keywords = len(df)
        
        # زمان‌سنجی: شروع API calls
        api_total_time = 0
        
        # مرحله 1: پردازش هر keyword
        for index, row in df.iterrows():
            keyword = str(row.iloc[1]).strip()
            
            try:
                search_volume = int(row.iloc[2])
            except (ValueError, TypeError):
                search_volume = 0
            
            try:
                word_count = int(row.iloc[3]) if len(row) > 3 and pd.notna(row.iloc[3]) else len(keyword.split())
            except (ValueError, TypeError):
                word_count = len(keyword.split())
            
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': index + 1,
                    'total': total_keywords,
                    'keyword': keyword
                }
            )
            
            # زمان‌سنجی: شروع این API call
            api_start = time.time()
            
            # فراخوانی API
            url = "https://api.apify.com/v2/acts/apify~google-search-scraper/runs"
            payload = {"queries": keyword, "maxPagesPerQuery": 2}
            headers = {
                "Authorization": f"Bearer {settings.APIFY_TOKEN}",
                "Content-Type": "application/json"
            }
            
            links_str = ""
            
            try:
                response = None
                for attempt in range(5):
                    try:
                        response = requests.post(url, json=payload, headers=headers, timeout=120)
                        if response.status_code == 429:
                            wait_time = (2 ** attempt)
                            print(f"[Retry {attempt+1}] Rate limit! Waiting {wait_time}s for {keyword}...")
                            time.sleep(wait_time)
                            continue
                        break
                    except requests.exceptions.RequestException as e:
                        if attempt < 4:
                            print(f"[Retry {attempt+1}] Error for {keyword}: {str(e)}")
                            time.sleep(1)
                        else:
                            response = None
                            break
                
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
                            break
                        elif status_data['data']['status'] in ['FAILED', 'ABORTED']:
                            links_str = "خطا در API"
                            break
                        
                        time.sleep(5)
                    else:
                        links_str = "خطا"
                else:
                    links_str = "خطا"
            
            except Exception as e:
                links_str = "خطا"
                print(f"Error processing keyword {keyword}: {str(e)}")
            
            # زمان‌سنجی: پایان این API call
            api_end = time.time()
            api_total_time += (api_end - api_start)
            print(f"[TIME] Keyword '{keyword}' took {api_end - api_start:.2f}s")
            
            Keyword.objects.create(
                user=research_request.user,
                id=index + 1,
                keyword=keyword,
                search_volume=search_volume,
                links=links_str,
                word_count=word_count,
                status=0,
                description=description,
                akw_str=""
            )
            
            time.sleep(1)
        
        print(f"\n[TIME] Total API time: {api_total_time:.2f}s ({api_total_time/60:.2f} minutes)")
        
        # زمان‌سنجی: شروع مقایسه
        compare_start = time.time()
        
        # مرحله 2: مقایسه PKW/AKW
        _process_pkw_akw_comparison_in_task(research_request.user)
        
        compare_end = time.time()
        print(f"[TIME] Comparison took {compare_end - compare_start:.2f}s")
        
        # تکمیل موفق
        research_request.status = 'completed'
        research_request.completed_date = timezone.now()
        research_request.save()
        
        total_time = api_total_time + (compare_end - compare_start)
        print(f"\n[TIME SUMMARY]")
        print(f"  API calls: {api_total_time:.2f}s ({api_total_time/total_time*100:.1f}%)")
        print(f"  Comparison: {compare_end - compare_start:.2f}s ({(compare_end - compare_start)/total_time*100:.1f}%)")
        print(f"  Total: {total_time:.2f}s ({total_time/60:.2f} minutes)")
        
        return {'status': 'completed', 'total': total_keywords}
    
    except Exception as e:
        research_request.status = 'failed'
        research_request.error_message = str(e)
        research_request.completed_date = timezone.now()
        research_request.save()
        return {'status': 'failed', 'error': str(e)}


def _process_pkw_akw_comparison_in_task(user):
    """مقایسه و تشخیص PKW/AKW با ذخیره search volume اصلی"""
    keywords = list(Keyword.objects.filter(user=user).order_by('id'))
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
                    
                    # ذخیره با search volume اصلی
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
                    
                    # ذخیره با search volume اصلی
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