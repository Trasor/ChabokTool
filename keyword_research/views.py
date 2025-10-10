from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Keyword, ResearchRequest
import pandas as pd
from django.conf import settings
import requests
import time

@login_required
def keyword_research(request):
    if request.method == 'POST':
        file = request.FILES['file']
        description = request.POST.get('description', '')
        
        # بارگذاری فایل
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith('.xlsx'):
            df = pd.read_excel(file)
        else:
            messages.error(request, 'فقط CSV یا XLSX پشتیبانی می‌شود.')
            return render(request, 'keyword_research/index.html')
        
        # پاک کردن دیتابیس قبلی کاربر
        Keyword.objects.filter(user=request.user).delete()
        
        # ایجاد درخواست جدید
        name = ' '.join(description.split()[:3]) + '...'
        req = ResearchRequest.objects.create(
            user=request.user,
            name=name,
            status=0
        )
        
        # ذخیره کلمات از فایل
        keywords_data = []
        for index, row in df.iterrows():
            keywords_data.append({
                'id': index + 1,
                'keyword': row.iloc[1],
                'search_volume': row.iloc[2],
                'word_count': row.iloc[3] if len(row) > 3 else 0,
            })
        
        # فراخوانی API برای هر کلمه
        for kw_data in keywords_data:
            keyword = kw_data['keyword']
            try:
                # API call به Apify
                url = "https://api.apify.com/v2/acts/apify~google-search-scraper/runs"
                payload = {
                    "queries": keyword,
                    "maxPagesPerQuery": 2
                }
                headers = {
                    "Authorization": f"Bearer {settings.APIFY_TOKEN}",
                    "Content-Type": "application/json"
                }
                
                response = requests.post(url, json=payload, headers=headers)
                
                if response.status_code == 201:
                    run_data = response.json()
                    run_id = run_data['data']['id']
                    
                    # منتظر تمام شدن run
                    while True:
                        status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={settings.APIFY_TOKEN}"
                        status_response = requests.get(status_url)
                        status_data = status_response.json()
                        
                        if status_data['data']['status'] == 'SUCCEEDED':
                            dataset_id = status_data['data']['defaultDatasetId']
                            results_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={settings.APIFY_TOKEN}&format=json"
                            results_response = requests.get(results_url)
                            results = results_response.json()
                            
                            links = []
                            for result in results:
                                links.extend([item['url'] for item in result['organicResults'] if 'url' in item])
                            
                            links = links[:10]
                            links_str = " -------------- ".join(links) if len(links) == 10 else "خطا"
                            break
                        elif status_data['data']['status'] in ['FAILED', 'ABORTED']:
                            links_str = "خطا در API"
                            break
                        
                        time.sleep(5)
                else:
                    links_str = "خطا در API"
                
                # ذخیره در دیتابیس
                Keyword.objects.create(
                    user=request.user,
                    id=kw_data['id'],
                    keyword=keyword,
                    search_volume=kw_data['search_volume'],
                    links=links_str,
                    word_count=kw_data['word_count'],
                    description=description,
                    status=0  # همه شروع با status 0 میکنن
                )
                
                time.sleep(1)
                
            except Exception as e:
                messages.error(request, f'خطا برای کلمه {keyword}: {str(e)}')
                Keyword.objects.create(
                    user=request.user,
                    id=kw_data['id'],
                    keyword=keyword,
                    search_volume=kw_data['search_volume'],
                    links="خطا",
                    word_count=kw_data['word_count'],
                    description=description,
                    status=0
                )
        
        # به‌روزرسانی status درخواست
        req.status = 1
        req.save()
        
        messages.success(request, 'درخواست ایجاد و SERP تکمیل شد!')
        return redirect('requests_list')
    
    return render(request, 'keyword_research/index.html')


@login_required
def requests_list(request):
    requests = ResearchRequest.objects.filter(user=request.user).order_by('-created_date')
    return render(request, 'keyword_research/requests_list.html', {'requests': requests})


@login_required
def request_detail(request, pk):
    req = get_object_or_404(ResearchRequest, pk=pk, user=request.user)
    keywords = Keyword.objects.filter(user=request.user).order_by('id')
    
    # فرآیند مقایسه و تشخیص PKW/AKW
    _process_pkw_akw_comparison(keywords)
    
    # دانلود فایل خروجی
    if request.GET.get('download'):
        return _generate_output_file(keywords, req)
    
    return render(request, 'keyword_research/request_detail.html', {
        'req': req,
        'keywords': keywords
    })


def _process_pkw_akw_comparison(keywords):
    """
    فرآیند مقایسه کلمات و تشخیص PKW/AKW
    فقط کلمات با status=0 مقایسه میشن
    """
    # فیلتر کلمات با status=0 (مقایسه نشده)
    zero_status_keywords = [kw for kw in keywords if kw.status == 0]
    
    i = 0
    while i < len(zero_status_keywords):
        kw1 = zero_status_keywords[i]
        
        # لینک های kw1 به set
        d1_links = set(kw1.links.split(" -------------- ")) if kw1.links and kw1.links != "خطا" else set()
        
        j = i + 1
        while j < len(zero_status_keywords):
            kw2 = zero_status_keywords[j]
            
            # لینک های kw2 به set
            d2_links = set(kw2.links.split(" -------------- ")) if kw2.links and kw2.links != "خطا" else set()
            
            # محاسبه امتیاز تشابه
            score = len(d1_links.intersection(d2_links))
            
            # اگر امتیاز >= 6
            if score >= 6:
                # تعیین PKW و AKW بر اساس search volume
                if kw1.search_volume > kw2.search_volume or (
                    kw1.search_volume == kw2.search_volume and kw1.id < kw2.id
                ):
                    # kw1 = PKW, kw2 = AKW
                    kw1.status = 1  # PKW
                    kw1.search_volume += kw2.search_volume
                    
                    # اضافه کردن kw2 به AKW
                    if kw1.akw_str:
                        kw1.akw_str += f" - {kw2.keyword}"
                    else:
                        kw1.akw_str = kw2.keyword
                    
                    kw1.save()
                    
                    # kw2 به AKW تبدیل میشه
                    kw2.status = 2  # AKW
                    kw2.save()
                    
                    # حذف kw2 از لیست
                    zero_status_keywords.pop(j)
                    continue
                    
                else:
                    # kw2 = PKW, kw1 = AKW
                    kw2.status = 1  # PKW
                    kw2.search_volume += kw1.search_volume
                    
                    # اضافه کردن kw1 به AKW
                    if kw2.akw_str:
                        kw2.akw_str += f" - {kw1.keyword}"
                    else:
                        kw2.akw_str = kw1.keyword
                    
                    kw2.save()
                    
                    # kw1 به AKW تبدیل میشه
                    kw1.status = 2  # AKW
                    kw1.save()
                    
                    # حذف kw1 از لیست و break
                    zero_status_keywords.pop(i)
                    i -= 1
                    break
            
            j += 1
        
        i += 1
    
    # کلمات باقی مانده با status=0 به PKW مستقل تبدیل میشن
    for kw in zero_status_keywords:
        kw.status = 1  # PKW
        kw.save()


def _generate_output_file(keywords, req):
    """
    ساخت فایل خروجی
    فقط کلمات با status=1 (PKW) در فایل خروجی قرار میگیرن
    """
    data = []
    
    for kw in keywords:
        # فقط PKW ها (status=1)
        if kw.status == 1:
            data.append({
                'ID': kw.id,
                'Keyword': kw.keyword,
                'Search Volume': kw.search_volume,
                'Links': kw.links,
                'AKW': kw.akw_str,  # استفاده از akw_str
                'Word Count': kw.word_count,
            })
    
    # ساخت DataFrame
    df = pd.DataFrame(data)
    
    # ساخت response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{req.name}_output.xlsx"'
    
    df.to_excel(response, index=False)
    
    return response