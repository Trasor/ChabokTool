from celery import shared_task
from django.conf import settings
from django.utils import timezone
import requests
import time
import pandas as pd
from .models import Keyword, ResearchRequest


@shared_task(bind=True, max_retries=0)
def process_keyword_research(self, request_id, file_path, description):
    """
    Task اصلی برای پردازش keyword research
    """
    try:
        # گرفتن request از دیتابیس
        research_request = ResearchRequest.objects.get(id=request_id)
        research_request.status = 'running'
        research_request.save()
        
        # خواندن فایل
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:  # xlsx
            df = pd.read_excel(file_path)
        
        # پاک کردن keyword های قبلی
        Keyword.objects.filter(user=research_request.user).delete()
        
        total_keywords = len(df)
        
        # مرحله 1: پردازش هر keyword و فراخوانی API
        for index, row in df.iterrows():
            # ساختار صحیح فایل Excel:
            # ستون 0: ID
            # ستون 1: Keyword
            # ستون 2: Search Volume
            # ستون 3: Word Count (اختیاری)
            
            keyword = str(row.iloc[1]).strip()  # ستون 1
            
            try:
                search_volume = int(row.iloc[2])  # ستون 2
            except (ValueError, TypeError):
                search_volume = 0
            
            try:
                word_count = int(row.iloc[3]) if len(row) > 3 and pd.notna(row.iloc[3]) else len(keyword.split())
            except (ValueError, TypeError):
                word_count = len(keyword.split())
            
            # به‌روزرسانی progress
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': index + 1,
                    'total': total_keywords,
                    'keyword': keyword
                }
            )
            
            # فراخوانی API با retry logic
            url = "https://api.apify.com/v2/acts/apify~google-search-scraper/runs"
            payload = {
                "queries": keyword,
                "maxPagesPerQuery": 2
            }
            headers = {
                "Authorization": f"Bearer {settings.APIFY_TOKEN}",
                "Content-Type": "application/json"
            }
            
            links_str = ""
            
            try:
                # Retry با exponential backoff
                response = None
                for attempt in range(5):  # 5 تلاش
                    try:
                        response = requests.post(url, json=payload, headers=headers, timeout=120)
                        if response.status_code == 429:  # Rate limit
                            wait_time = (2 ** attempt)
                            print(f"[Retry {attempt+1}] Rate limit! Waiting {wait_time}s for {keyword}...")
                            time.sleep(wait_time)
                            continue
                        break  # موفق شد
                    except requests.exceptions.RequestException as e:
                        if attempt < 4:
                            print(f"[Retry {attempt+1}] Error for {keyword}: {str(e)}")
                            time.sleep(1)
                        else:
                            print(f"[Failed] Max retries for {keyword}")
                            response = None
                            break
                
                if response and response.status_code == 201:
                    run_data = response.json()
                    run_id = run_data['data']['id']
                    
                    # منتظر نتیجه
                    max_wait = 600  # 10 دقیقه
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
                            
                            # استخراج لینک‌ها
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
                        links_str = "خطا"  # timeout
                else:
                    links_str = "خطا"
            
            except Exception as e:
                links_str = "خطا"
                print(f"Error processing keyword {keyword}: {str(e)}")
            
            # ذخیره keyword با status=0
            Keyword.objects.create(
                user=research_request.user,
                id=index + 1,
                keyword=keyword,
                search_volume=search_volume,
                links=links_str,
                word_count=word_count,
                status=0,  # مقایسه نشده
                description=description,
                akw_str=""
            )
            
            time.sleep(1)  # delay برای rate limit
        
        # مرحله 2: اجرای منطق مقایسه PKW/AKW
        _process_pkw_akw_comparison_in_task(research_request.user)
        
        # تکمیل موفق
        research_request.status = 'completed'
        research_request.completed_date = timezone.now()
        research_request.save()
        
        return {'status': 'completed', 'total': total_keywords}
    
    except Exception as e:
        # خطا
        research_request.status = 'failed'
        research_request.error_message = str(e)
        research_request.completed_date = timezone.now()
        research_request.save()
        
        return {'status': 'failed', 'error': str(e)}


def _process_pkw_akw_comparison_in_task(user):
    """
    فرآیند مقایسه کلمات و تشخیص PKW/AKW
    این تابع در task اجرا میشه (نه در view)
    """
    keywords = list(Keyword.objects.filter(user=user).order_by('id'))
    zero_status_keywords = [kw for kw in keywords if kw.status == 0]
    
    i = 0
    while i < len(zero_status_keywords):
        kw1 = zero_status_keywords[i]
        d1_links = set(kw1.links.split(" -------------- ")) if kw1.links and kw1.links != "خطا" and kw1.links != "خطا در API" else set()
        
        j = i + 1
        while j < len(zero_status_keywords):
            kw2 = zero_status_keywords[j]
            d2_links = set(kw2.links.split(" -------------- ")) if kw2.links and kw2.links != "خطا" and kw2.links != "خطا در API" else set()
            
            score = len(d1_links.intersection(d2_links))
            
            if score >= 6:
                if kw1.search_volume > kw2.search_volume or (kw1.search_volume == kw2.search_volume and kw1.id < kw2.id):
                    # kw1 = PKW, kw2 = AKW
                    kw1.status = 1  # PKW
                    kw1.search_volume += kw2.search_volume
                    
                    if kw1.akw_str:
                        kw1.akw_str += f" - {kw2.keyword}"
                    else:
                        kw1.akw_str = kw2.keyword
                    
                    kw1.save()
                    
                    kw2.status = 2  # AKW
                    kw2.save()
                    
                    zero_status_keywords.pop(j)
                    continue
                else:
                    # kw2 = PKW, kw1 = AKW
                    kw2.status = 1  # PKW
                    kw2.search_volume += kw1.search_volume
                    
                    if kw2.akw_str:
                        kw2.akw_str += f" - {kw1.keyword}"
                    else:
                        kw2.akw_str = kw1.keyword
                    
                    kw2.save()
                    
                    kw1.status = 2  # AKW
                    kw1.save()
                    
                    zero_status_keywords.pop(i)
                    i -= 1
                    break
            
            j += 1
        
        i += 1
    
    # کلمات باقی‌مانده با status=0 به PKW تبدیل میشن
    for kw in zero_status_keywords:
        kw.status = 1  # PKW
        kw.save()