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

@login_required
def keyword_research(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        description = request.POST.get('description', '')
        
        if not file:
            messages.error(request, 'لطفاً فایل را انتخاب کنید.')
            return render(request, 'keyword_research/index.html')
        
        # بررسی فرمت فایل
        if not (file.name.endswith('.csv') or file.name.endswith('.xlsx')):
            messages.error(request, 'فقط CSV یا XLSX پشتیبانی می‌شود.')
            return render(request, 'keyword_research/index.html')
        
        # ذخیره فایل با UUID برای جلوگیری از مشکل فارسی
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        # نام فایل جدید با UUID (برای support فارسی)
        file_extension = os.path.splitext(file.name)[1]
        safe_filename = f"{uuid.uuid4().hex}{file_extension}"
        file_path = os.path.join(upload_dir, safe_filename)
        
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        
        # ساخت ResearchRequest
        name = ' '.join(description.split()[:3]) + '...' if description else file.name
        research_request = ResearchRequest.objects.create(
            user=request.user,
            name=name,
            status='pending'
        )
        
        # اجرای task در background
        task = process_keyword_research.delay(
            research_request.id,
            file_path,
            description
        )
        
        # ذخیره task_id
        research_request.task_id = task.id
        research_request.status = 'running'
        research_request.save()
        
        # پیغام موفقیت
        messages.success(request, f'درخواست "{research_request.name}" در حال پردازش است. لطفاً صبر کنید...')
        
        # ریدایرکت به لیست درخواست‌ها
        return redirect('requests_list')
    
    return render(request, 'keyword_research/index.html')


@login_required
def requests_list(request):
    requests = ResearchRequest.objects.filter(user=request.user).order_by('-created_date')
    return render(request, 'keyword_research/requests_list.html', {'requests': requests})


@login_required
def request_detail(request, pk):
    req = get_object_or_404(ResearchRequest, pk=pk, user=request.user)
    
    # فقط PKW ها (منطق مقایسه قبلاً در task انجام شده)
    pkw_keywords = Keyword.objects.filter(user=request.user, status=1).order_by('id')
    
    # دانلود فایل خروجی
    if request.GET.get('download'):
        return _generate_output_file(pkw_keywords, req)
    
    return render(request, 'keyword_research/request_detail.html', {
        'req': req,
        'keywords': pkw_keywords
    })


def _generate_output_file(pkw_keywords, req):
    """
    ساخت فایل خروجی
    فقط کلمات با status=1 (PKW) در فایل خروجی قرار میگیرن
    """
    data = []
    
    for kw in pkw_keywords:
        data.append({
            'ID': kw.id,
            'Keyword': kw.keyword,
            'Search Volume': kw.search_volume,
            'Links': kw.links,
            'AKW': kw.akw_str,
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