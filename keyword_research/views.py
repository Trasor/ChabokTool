from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Keyword, ResearchRequest
from .tasks import process_keyword_research
import pandas as pd
from django.conf import settings
import os
import uuid
from urllib.parse import urlparse
from collections import Counter


@login_required
def keyword_research(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        description = request.POST.get('description', '')
        
        if not file:
            messages.error(request, 'لطفاً فایل را انتخاب کنید.')
            return render(request, 'keyword_research/index.html')
        
        if not (file.name.endswith('.csv') or file.name.endswith('.xlsx')):
            messages.error(request, 'فقط CSV یا XLSX پشتیبانی می‌شود.')
            return render(request, 'keyword_research/index.html')
        
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        file_extension = os.path.splitext(file.name)[1]
        safe_filename = f"{uuid.uuid4().hex}{file_extension}"
        file_path = os.path.join(upload_dir, safe_filename)
        
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        
        name = ' '.join(description.split()[:3]) + '...' if description else file.name
        research_request = ResearchRequest.objects.create(
            user=request.user,
            name=name,
            status='pending'
        )
        
        task = process_keyword_research.delay(research_request.id, file_path, description)
        
        research_request.task_id = task.id
        research_request.status = 'running'
        research_request.save()
        
        messages.success(request, f'درخواست "{research_request.name}" در حال پردازش است.')
        return redirect('requests_list')
    
    return render(request, 'keyword_research/index.html')


@login_required
def requests_list(request):
    requests = ResearchRequest.objects.filter(user=request.user).order_by('-created_date')
    return render(request, 'keyword_research/requests_list.html', {'requests': requests})


@login_required
def request_detail(request, pk):
    req = get_object_or_404(ResearchRequest, pk=pk, user=request.user)
    pkw_keywords = Keyword.objects.filter(user=request.user, status=1).order_by('id')
    
    if request.GET.get('download'):
        return _generate_output_file(pkw_keywords, req)
    
    return render(request, 'keyword_research/request_detail.html', {
        'req': req,
        'keywords': pkw_keywords
    })


def extract_domain(url):
    """استخراج دامنه از URL"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        # حذف www.
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain if domain else None
    except:
        return None


def get_top_akw_from_keywords(keywords_str):
    """پیدا کردن کلمه با بیشترین search volume در Keywords"""
    if not keywords_str:
        return ""
    
    try:
        # Parse: "keyword1:800 - keyword2:600 - keyword3:500"
        parts = keywords_str.split(" - ")
        keyword_data = []
        
        for part in parts:
            if ":" in part:
                kw, sv = part.rsplit(":", 1)  # از راست split کن (برای handle کردن : در URL)
                keyword_data.append({"keyword": kw.strip(), "sv": int(sv)})
        
        if keyword_data:
            # پیدا کردن کلمه با بیشترین search volume
            top = max(keyword_data, key=lambda x: x["sv"])
            return top["keyword"]
    except:
        pass
    
    return ""


def get_keywords_without_sv(keywords_str, exclude_keyword=None):
    """حذف search volume از Keywords + حذف کلمه خاص"""
    if not keywords_str:
        return ""
    
    try:
        parts = keywords_str.split(" - ")
        keywords = []
        
        for part in parts:
            if ":" in part:
                kw, _ = part.rsplit(":", 1)
                kw = kw.strip()
                
                # حذف کلمه‌ای که به AKW رفته
                if exclude_keyword and kw == exclude_keyword:
                    continue
                
                keywords.append(kw)
            else:
                part = part.strip()
                if exclude_keyword and part == exclude_keyword:
                    continue
                keywords.append(part)
        
        return " - ".join(keywords)
    except:
        return keywords_str


def get_top_competitors(pkw_keywords, top_n=10):
    """پیدا کردن 10 سایت برتر با بیشترین تکرار"""
    all_domains = []
    
    for kw in pkw_keywords:
        if kw.links and kw.links != "خطا":
            links = kw.links.split(" -------------- ")
            for link in links:
                domain = extract_domain(link)
                if domain:
                    all_domains.append(domain)
    
    # شمارش و مرتب‌سازی
    counter = Counter(all_domains)
    top_competitors = counter.most_common(top_n)
    
    return top_competitors


def _generate_output_file(pkw_keywords, req):
    """ساخت فایل Excel با 2 تب"""
    
    # تب 1: PKW ها
    data_tab1 = []
    
    for kw in pkw_keywords:
    # پیدا کردن AKW (کلمه با بیشترین search volume در Keywords)
    top_akw = get_top_akw_from_keywords(kw.akw_str)
    
    # Keywords بدون search volume و بدون کلمه‌ای که به AKW رفت
    keywords_clean = get_keywords_without_sv(kw.akw_str, exclude_keyword=top_akw)
        
        data_tab1.append({
            'ID': kw.id,
            'PKW': kw.keyword,
            'Search Volume': kw.search_volume,
            'AKW': top_akw,
            'Keywords': keywords_clean,
            'Word Count': kw.word_count,
            'Links': kw.links,
        })
    
    df_tab1 = pd.DataFrame(data_tab1)
    
    # تب 2: رقبا
    competitors = get_top_competitors(pkw_keywords, top_n=10)
    
    data_tab2 = []
    for domain, count in competitors:
        data_tab2.append({
            'رقبا': f"https://{domain}",
            'تعداد تکرار': count
        })
    
    df_tab2 = pd.DataFrame(data_tab2)
    
    # ساخت Excel با 2 تب
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{req.name}_output.xlsx"'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df_tab1.to_excel(writer, sheet_name='Keywords', index=False)
        df_tab2.to_excel(writer, sheet_name='رقبا', index=False)
    
    return response