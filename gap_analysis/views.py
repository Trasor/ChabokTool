from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from celery.result import AsyncResult
from WowDash.celery import app as celery_app
from django.http import HttpResponse
from .models import GapRequest, GapKeyword
from .tasks import process_gap_analysis
from billing.models import UserCredit, Transaction
import pandas as pd
from django.conf import settings
import os
import uuid


# قیمت هر 1000 کردیت
CREDIT_PRICE_PER_1000 = 500000


@login_required
def gap_analysis(request):
    """صفحه آپلود فایل Gap Analysis"""
    if request.method == 'POST':
        file = request.FILES.get('file')
        description = request.POST.get('description', '')
        
        if not file:
            messages.error(request, 'لطفاً فایل را انتخاب کنید.')
            return render(request, 'gap_analysis/index.html')
        
        if not (file.name.endswith('.csv') or file.name.endswith('.xlsx')):
            messages.error(request, 'فقط CSV یا XLSX پشتیبانی می‌شود.')
            return render(request, 'gap_analysis/index.html')
        
        # ✅ محاسبه کوئری مورد نیاز (سطرها × ستون‌ها)
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file, header=None)
            else:
                df = pd.read_excel(file, header=None)
            
            # تعداد کلمات یونیک (سطرها)
            keywords = df.iloc[:, 1].dropna().astype(str).str.strip().unique()
            num_keywords = len(keywords)
            
            # تعداد رقبای یونیک (ستون‌ها از دامنه)
            competitors = df.iloc[:, 0].dropna().astype(str).str.strip().unique()
            num_competitors = len(competitors)
            
            required_credits = num_keywords * num_competitors  # سطر × ستون
            file.seek(0)  # Reset file pointer
            
        except Exception as e:
            messages.error(request, f'❌ خطا در خواندن فایل: {str(e)}')
            return render(request, 'gap_analysis/index.html')
        
        # ✅ چک کردن موجودی کاربر
        user_credit, created = UserCredit.objects.get_or_create(user=request.user)
        
        if user_credit.balance < required_credits:
            # موجودی کافی نیست
            shortage = required_credits - user_credit.balance
            
            # حداقل 200 کردیت
            credits_to_buy = max(shortage, 200)
            price = int((credits_to_buy / 1000) * CREDIT_PRICE_PER_1000)
            
            # ساخت تراکنش خودکار
            transaction = Transaction.objects.create(
                user=request.user,
                credit_amount=credits_to_buy,
                price=price,
                status='pending'
            )
            
            messages.warning(
                request, 
                f'⚠️ جدول شما نیاز به بررسی {required_credits} کوئری دارد ({num_keywords} کلمه × {num_competitors} رقیب)، '
                f'اما موجودی فعلی شما {user_credit.balance} کردیت است. '
                f'ما برای شما یک صورتحساب به مبلغ {price:,} تومان ایجاد کردیم. '
                f'لطفاً ابتدا پرداخت کنید تا بتوانید درخواست خود را ثبت کنید.'
            )
            return redirect('transactions_list')
        
        # ادامه کد اصلی
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        file_extension = os.path.splitext(file.name)[1]
        safe_filename = f"{uuid.uuid4().hex}{file_extension}"
        file_path = os.path.join(upload_dir, safe_filename)
        
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        
        words = description.split()[:3]
        name = ' '.join(words) + '...' if words else file.name
        if len(name) > 50:
            name = name[:47] + '...'
        
        gap_request = GapRequest.objects.create(
            user=request.user,
            name=name,
            description=description,
            status='pending'
        )
        
        # ✅ کم کردن کردیت از حساب کاربر
        user_credit.balance -= required_credits
        user_credit.save()
        
        task = process_gap_analysis.delay(gap_request.id, file_path, description)
        
        gap_request.task_id = task.id
        gap_request.status = 'running'
        gap_request.save()
        
        messages.success(request, f'درخواست "{gap_request.name}" در حال پردازش است. ({required_credits} کردیت کسر شد)')
        return redirect('gap_requests_list')
    
    return render(request, 'gap_analysis/index.html')


@login_required
def gap_requests_list(request):
    """لیست درخواست‌های Gap Analysis"""
    requests = GapRequest.objects.filter(user=request.user).order_by('-created_date')
    return render(request, 'gap_analysis/requests_list.html', {'requests': requests})


@login_required
def gap_request_detail(request, pk):
    """جزئیات درخواست + دانلود Excel"""
    req = get_object_or_404(GapRequest, pk=pk, user=request.user)
    
    if request.GET.get('download'):
        return _generate_gap_output_file(req)
    
    # دریافت داده‌ها
    keywords_data = GapKeyword.objects.filter(request=req)
    
    # لیست یونیک برای نمایش
    unique_keywords = list(
        keywords_data.values_list('keyword', flat=True).distinct()
    )
    unique_competitors = list(
        keywords_data.values_list('competitor', flat=True).distinct()
    )
    
    return render(request, 'gap_analysis/request_detail.html', {
        'req': req,
        'keywords_data': keywords_data,
        'unique_keywords': unique_keywords,
        'unique_competitors': unique_competitors
    })


def _generate_gap_output_file(req):
    """ساخت فایل Excel خروجی - FIX distinct()"""
    
    # دریافت تمام داده‌ها (بدون order_by برای distinct درست!)
    keywords_data = GapKeyword.objects.filter(request=req)
    
    # لیست کلمات یونیک (بدون order_by!)
    unique_keywords = list(
        keywords_data.values_list('keyword', flat=True).distinct()
    )
    
    # لیست برندها یونیک (بدون order_by!)
    unique_brands = list(
        keywords_data.values_list('competitor', flat=True).distinct()
    )
    
    # ساخت dictionary برای DataFrame
    data = {'کلمات': unique_keywords}
    
    # برای هر برند، یک ستون بساز
    for brand in unique_brands:
        brand_links = []
        for keyword in unique_keywords:
            try:
                kw_obj = keywords_data.get(keyword=keyword, competitor=brand)
                brand_links.append(kw_obj.link)
            except GapKeyword.DoesNotExist:
                brand_links.append('-')
            except GapKeyword.MultipleObjectsReturned:
                kw_obj = keywords_data.filter(keyword=keyword, competitor=brand).first()
                brand_links.append(kw_obj.link if kw_obj else '-')
        
        data[brand] = brand_links
    
    df = pd.DataFrame(data)
    
    # ساخت Excel
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    # FIX Unicode: encode filename
    filename = f"{req.name}_gap_analysis.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Gap Analysis', index=False)
    
    return response


@login_required
def delete_gap_request(request, request_id):
    """حذف درخواست گپ - حتی در حال انجام"""
    req = get_object_or_404(GapRequest, id=request_id, user=request.user)
    
    # اگر task در حال اجراست، متوقفش کن
    if req.status in ['running', 'pending'] and req.task_id:
        try:
            # لغو task از Celery
            celery_app.control.revoke(req.task_id, terminate=True, signal='SIGKILL')
            messages.warning(request, f'⚠️ Task در حال اجرا متوقف شد: {req.name}')
        except Exception as e:
            messages.error(request, f'❌ خطا در متوقف کردن task: {str(e)}')
    
    # حذف کلمات مرتبط
    GapKeyword.objects.filter(request=req).delete()
    
    # حذف درخواست
    req_name = req.name
    req.delete()
    
    messages.success(request, f'✅ درخواست "{req_name}" با موفقیت حذف شد.')
    return redirect('gap_requests_list')