from celery import shared_task
from django.conf import settings
from django.utils import timezone
import requests
import time
import pandas as pd
from urllib.parse import urlparse
from .models import GapRequest, GapKeyword


def extract_domain(url):
    """استخراج دامنه از URL (با پشتیبانی subdomain)"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain if domain else None
    except:
        return None


def check_competitor_in_links(links, competitor_domain):
    """
    چک کردن لینک‌ها برای پیدا کردن دامنه رقیب
    Returns: لینک کامل اولین match یا None
    """
    competitor_clean = competitor_domain.lower().replace('www.', '').replace('https://', '').replace('http://', '')
    
    for link in links:
        link_domain = extract_domain(link)
        if link_domain and competitor_clean in link_domain:
            return link
    
    return None


@shared_task(bind=True, max_retries=0)
def process_gap_analysis(self, request_id, file_path, description):
    """Task اصلی برای Gap Analysis"""
    try:
        gap_request = GapRequest.objects.get(id=request_id)
        gap_request.status = 'running'
        gap_request.save()
        
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        competitors_dict = {}
        
        for index, row in df.iterrows():
            competitor_domain = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else None
            competitor_brand = str(row.iloc[2]).strip() if len(row) > 2 and pd.notna(row.iloc[2]) else competitor_domain
            
            if competitor_domain and competitor_domain not in competitors_dict:
                competitors_dict[competitor_domain] = competitor_brand
        
        keywords = df.iloc[:, 1].dropna().astype(str).str.strip().unique().tolist()
        keywords = [k for k in keywords if k]
        
        total_queries = len(keywords) * len(competitors_dict)
        current_query = 0
        
        print(f"\n[GAP ANALYSIS] Starting: {len(keywords)} keywords × {len(competitors_dict)} competitors = {total_queries} queries")
        
        GapKeyword.objects.filter(request=gap_request).delete()
        
        for keyword in keywords:
            for competitor_domain, competitor_brand in competitors_dict.items():
                current_query += 1
                
                query = f"{keyword} {competitor_brand}"
                
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': current_query,
                        'total': total_queries,
                        'query': query
                    }
                )
                
                print(f"[{current_query}/{total_queries}] Searching: {query}")
                
                url = "https://api.apify.com/v2/acts/apify~google-search-scraper/runs"
                payload = {
                    "queries": query,
                    "maxPagesPerQuery": 1
                }
                headers = {
                    "Authorization": f"Bearer {settings.APIFY_TOKEN}",
                    "Content-Type": "application/json"
                }
                
                found_link = "-"
                
                try:
                    response = None
                    for attempt in range(5):
                        try:
                            response = requests.post(url, json=payload, headers=headers, timeout=120)
                            if response.status_code == 429:
                                wait_time = (2 ** attempt)
                                print(f"  [Retry {attempt+1}] Rate limit! Waiting {wait_time}s...")
                                time.sleep(wait_time)
                                continue
                            break
                        except requests.exceptions.RequestException as e:
                            if attempt < 4:
                                print(f"  [Retry {attempt+1}] Error: {str(e)}")
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
                                
                                found_link = check_competitor_in_links(links, competitor_domain)
                                if found_link:
                                    print(f"  Found: {found_link}")
                                else:
                                    found_link = "-"
                                    print(f"  Not found in top 10")
                                
                                break
                            
                            elif status_data['data']['status'] in ['FAILED', 'ABORTED']:
                                print(f"  API failed")
                                break
                            
                            time.sleep(5)
                        else:
                            print(f"  Timeout")
                    
                    else:
                        print(f"  API error: {response.status_code if response else 'No response'}")
                
                except Exception as e:
                    print(f"  Exception: {str(e)}")
                
                GapKeyword.objects.update_or_create(
                    user=gap_request.user,
                    request=gap_request,
                    keyword=keyword,
                    competitor=competitor_brand,
                    defaults={'link': found_link if found_link else "-"}
                )
                
                time.sleep(1)
        
        gap_request.status = 'completed'
        gap_request.completed_date = timezone.now()
        gap_request.save()
        
        print(f"\n[GAP ANALYSIS] Completed successfully!")
        
        return {'status': 'completed', 'total': total_queries}
    
    except Exception as e:
        gap_request.status = 'failed'
        gap_request.error_message = str(e)
        gap_request.completed_date = timezone.now()
        gap_request.save()
        
        print(f"\n[GAP ANALYSIS] Failed: {str(e)}")
        
        return {'status': 'failed', 'error': str(e)}