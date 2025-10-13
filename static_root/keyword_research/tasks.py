from celery import shared_task
from .models import Keyword, ResearchRequest
import pandas as pd
from django.conf import settings
import requests
import time

@shared_task
def process_keyword_research(request_id, user_id, file_path, description):
    user = User.objects.get(id=user_id)
    req = ResearchRequest.objects.get(id=request_id)
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif file_path.endswith('.xlsx'):
        df = pd.read_excel(file_path)
    else:
        return "فقط CSV یا XLSX پشتیبانی می‌شود."

    # ذخیره داده‌ها از ستون‌ها (فرض: ستون 0 ID, 1 keyword, 2 search_volume, 3 word_count)
    keywords = []
    for index, row in df.iterrows():
        keywords.append({
            'id': index + 1,
            'keyword': row.iloc[1],
            'search_volume': row.iloc[2],
            'word_count': row.iloc[3] if len(row) > 3 else 0,
        })

    # فراخوانی Apify API برای هر کلمه
    for kw_data in keywords:
        keyword = kw_data['keyword']
        try:
            # API call به Apify
            url = "https://api.apify.com/v2/acts/apify~google-search-scraper/runs"
            payload = {
                "queries": keyword,
                "maxPagesPerQuery": 2  # 2 صفحه برای 10 لینک کامل
            }
            headers = {
                "Authorization": f"Bearer {settings.APIFY_TOKEN}",
                "Content-Type": "application/json"
            }
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 201:
                run_data = response.json()
                run_id = run_data['data']['id']
                # منتظر تمام شدن run (poll)
                while True:
                    status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={settings.APIFY_TOKEN}"
                    status_response = requests.get(status_url)
                    status_data = status_response.json()
                    if status_data['data']['status'] == 'SUCCEEDED':
                        # گرفتن نتایج
                        dataset_id = status_data['data']['defaultDatasetId']
                        results_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={settings.APIFY_TOKEN}&format=json"
                        results_response = requests.get(results_url)
                        results = results_response.json()
                        links = []
                        for result in results:
                            links.extend([item['url'] for item in result['organicResults'] if 'url' in item])
                        links = links[:10]  # حداکثر 10
                        links_str = " -------------- ".join(links) if links else ""
                        break
                    elif status_data['data']['status'] in ['FAILED', 'ABORTED']:
                        links_str = "خطا در API"
                        break
                    time.sleep(5)  # poll هر 5 ثانیه
            else:
                links_str = "خطا در API"
            # ذخیره در دیتابیس با user
            Keyword.objects.create(
                user=user,
                id=kw_data['id'],
                keyword=keyword,
                search_volume=kw_data['search_volume'],
                links=links_str,
                word_count=kw_data['word_count'],
                description=description,
                status=0
            )
            time.sleep(1)  # delay برای rate limit Apify
        except Exception as e:
            # ذخیره بدون لینک با user
            Keyword.objects.create(
                user=user,
                id=kw_data['id'],
                keyword=keyword,
                search_volume=kw_data['search_volume'],
                links="خطا",
                word_count=kw_data['word_count'],
                description=description,
                status=0
            )

        # به‌روزرسانی status درخواست به تکمیل شده
        req.status = 1
        req.save()
        return "پروسس تموم شد"