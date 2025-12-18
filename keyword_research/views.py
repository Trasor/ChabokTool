from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from celery.result import AsyncResult
from WowDash.celery import app as celery_app
from .models import Keyword, ResearchRequest
from .tasks import process_keyword_research
import pandas as pd
from django.conf import settings
import os
import uuid
from urllib.parse import urlparse
from collections import Counter
from billing.models import UserCredit, Transaction
import openpyxl.styles


@login_required
def keyword_research(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        description = request.POST.get('description', '')
        ai_analysis = request.POST.get('ai_analysis') == 'on'
        
        if not file:
            messages.error(request, 'لطفاً فایل را انتخاب کنید.')
            return render(request, 'keyword_research/index.html')
        
        if not (file.name.endswith('.csv') or file.name.endswith('.xlsx')):
            messages.error(request, 'فقط CSV یا XLSX پشتیبانی می‌شود.')
            return render(request, 'keyword_research/index.html')
        
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file, header=0)
            else:
                df = pd.read_excel(file, header=0)
            
            if len(df.columns) > 3:
                messages.error(
                    request, 
                    f'❌ فرمت فایل اشتباه است! فایل شما {len(df.columns)} ستون دارد. '
                    f'لطفاً مطابق فایل راهنما عمل کنید (حداکثر 3 ستون).'
                )
                return render(request, 'keyword_research/index.html')
            
            if df.iloc[:, 0].isna().all():
                messages.error(
                    request,
                    '❌ ستون اول (Keyword) نمی‌تواند خالی باشد!'
                )
                return render(request, 'keyword_research/index.html')
            
            required_credits = len(df)
            file.seek(0)
            
        except Exception as e:
            messages.error(request, f'❌ خطا در خواندن فایل: {str(e)}')
            return render(request, 'keyword_research/index.html')
        
        user_credit, created = UserCredit.objects.get_or_create(user=request.user)
        
        if user_credit.balance < required_credits:
            shortage = required_credits - user_credit.balance
            credits_to_buy = max(shortage, 200)
            price = int((credits_to_buy / 1000) * 500000)
            
            transaction = Transaction.objects.create(
                user=request.user,
                credit_amount=credits_to_buy,
                price=price,
                status='pending'
            )
            
            messages.warning(
                request, 
                f'⚠️ جدول شما نیاز به {required_credits} کوئری دارد، اما موجودی فعلی {user_credit.balance} کردیت است.'
            )
            return redirect('transactions_list')
        
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
            status='pending',
            ai_analysis_enabled=ai_analysis
        )
        
        user_credit.balance -= required_credits
        user_credit.save()
        
        task = process_keyword_research.delay(research_request.id, file_path, description)
        
        research_request.task_id = task.id
        research_request.status = 'running'
        research_request.save()
        
        ai_msg = ' (با تحلیل هوشمند)' if ai_analysis else ''
        messages.success(request, f'درخواست "{research_request.name}" در حال پردازش است{ai_msg}. ({required_credits} کردیت)')
        return redirect('requests_list')
    
    return render(request, 'keyword_research/index.html')


@login_required
def requests_list(request):
    requests = ResearchRequest.objects.filter(user=request.user).order_by('-created_date')
    return render(request, 'keyword_research/requests_list.html', {'requests': requests})


@login_required
def request_detail(request, pk):
    req = get_object_or_404(ResearchRequest, pk=pk, user=request.user)
    
    pkw_keywords = Keyword.objects.filter(request=req, status=1).order_by('id')
    
    if request.GET.get('download'):
        return _generate_output_file(pkw_keywords, req)
    
    return render(request, 'keyword_research/request_detail.html', {
        'req': req,
        'keywords': pkw_keywords
    })


@login_required
def check_task_status(request):
    """
    API برای چک کردن وضعیت Task (Long Polling)
    """
    # Tasks در حال اجرا
    running_requests = ResearchRequest.objects.filter(
        user=request.user,
        status='running'
    ).values('id', 'status')
    
    # Tasks تکمیل شده اخیر (آخرین 5 تا)
    completed_requests = ResearchRequest.objects.filter(
        user=request.user,
        status__in=['completed', 'failed']
    ).order_by('-completed_date')[:5].values('id', 'status', 'error_message')
    
    return JsonResponse({
        'running': list(running_requests),
        'completed': list(completed_requests)
    })


def extract_domain(url):
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain if domain else None
    except:
        return None


def get_top_akw_from_keywords(keywords_str):
    if not keywords_str:
        return ""
    
    try:
        parts = keywords_str.split(" - ")
        keyword_data = []
        
        for part in parts:
            if ":" in part:
                kw, sv = part.rsplit(":", 1)
                try:
                    keyword_data.append({"keyword": kw.strip(), "sv": int(sv)})
                except ValueError:
                    continue
        
        if keyword_data:
            if all(item["sv"] == 0 for item in keyword_data):
                import random
                return random.choice(keyword_data)["keyword"]
            
            top = max(keyword_data, key=lambda x: x["sv"])
            return top["keyword"]
    except:
        pass
    
    return ""


def get_keywords_without_sv(keywords_str, exclude_keyword=None):
    if not keywords_str:
        return ""
    
    try:
        parts = keywords_str.split(" - ")
        keywords = []
        
        for part in parts:
            if ":" in part:
                kw, _ = part.rsplit(":", 1)
                kw = kw.strip()
                
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
    all_domains = []
    
    for kw in pkw_keywords:
        if kw.links and kw.links != "خطا":
            links = kw.links.split(" -------------- ")
            for link in links:
                domain = extract_domain(link)
                if domain:
                    all_domains.append(domain)
    
    counter = Counter(all_domains)
    top_competitors = counter.most_common(top_n)
    
    return top_competitors


def _generate_output_file(pkw_keywords, req):
    data_tab1 = []
    
    for kw in pkw_keywords:
        top_akw = get_top_akw_from_keywords(kw.akw_str)
        keywords_clean = get_keywords_without_sv(kw.akw_str, exclude_keyword=top_akw)
        
        if kw.links and kw.links != "خطا":
            links_formatted = kw.links.replace(" -------------- ", "\n")
        else:
            links_formatted = ""
            
        data_tab1.append({
            'PKW': kw.keyword,
            'Search Volume': kw.search_volume,
            'AKW': top_akw,
            'Keywords': keywords_clean,
            'Word Count': kw.word_count if kw.word_count else '',
            'Links': links_formatted,
            'Search Intent': kw.search_intent or '',
            'Intent Mapping': kw.intent_mapping or '',
            'Meta Titles': kw.meta_titles or '',
        })
    
    df_tab1 = pd.DataFrame(data_tab1)
    
    competitors = get_top_competitors(pkw_keywords, top_n=10)
    
    data_tab2 = []
    for domain, count in competitors:
        data_tab2.append({
            'رقبا': f"https://{domain}",
            'تعداد تکرار': count
        })
    
    df_tab2 = pd.DataFrame(data_tab2)
    
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{req.name}_output.xlsx"'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df_tab1.to_excel(writer, sheet_name='Keywords', index=False)
        df_tab2.to_excel(writer, sheet_name='رقبا', index=False)
        
        worksheet = writer.sheets['Keywords']
        for col in ['F', 'I']:
            for cell in worksheet[col]:
                cell.alignment = openpyxl.styles.Alignment(wrap_text=True, vertical='top')
    
    return response


@login_required
def delete_request(request, request_id):
    req = get_object_or_404(ResearchRequest, id=request_id, user=request.user)
    
    if req.status in ['running', 'pending'] and req.task_id:
        try:
            celery_app.control.revoke(req.task_id, terminate=True, signal='SIGKILL')
            messages.warning(request, f'⚠️ Task متوقف شد: {req.name}')
        except Exception as e:
            messages.error(request, f'❌ خطا: {str(e)}')
    
    Keyword.objects.filter(request=req).delete()
    
    req_name = req.name
    req.delete()
    
    messages.success(request, f'✅ درخواست "{req_name}" حذف شد.')
    return redirect('requests_list')


@login_required
def download_sample_file(request):
    sample_data = {
        'Keyword': ['پت شاپ', 'پت شاپ آنلاین', 'پت شاپ تهران'],
        'Search Volume': [1000, 800, 600],
        'Word Count': [2, 3, 3]
    }
    
    df = pd.DataFrame(sample_data)
    
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="sample_keywords.xlsx"'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Keywords', index=False)
    
    return response