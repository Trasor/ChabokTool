from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.conf import settings
from .models import Transaction, UserCredit
import requests
import json


# قیمت هر 1000 کردیت
CREDIT_PRICE_PER_1000 = 500000  # 500,000 تومان

# ZarinPal Config
ZARINPAL_WEBGATE = 'https://sandbox.zarinpal.com/pg/v4/payment/request.json'
ZARINPAL_STARTPAY = 'https://sandbox.zarinpal.com/pg/StartPay/'
ZARINPAL_VERIFY = 'https://sandbox.zarinpal.com/pg/v4/payment/verify.json'


@login_required
def buy_credit(request):
    """صفحه خرید کردیت"""
    
    # دریافت یا ساخت موجودی کاربر
    user_credit, created = UserCredit.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        try:
            credit_amount = int(request.POST.get('credit_amount', 0))
            
            # چک حداقل 200 کردیت
            if credit_amount < 200:
                messages.error(request, '❌ حداقل مقدار خرید 200 کردیت است.')
                return redirect('buy_credit')
            
            # محاسبه قیمت
            price = int((credit_amount / 1000) * CREDIT_PRICE_PER_1000)
            
            # ساخت تراکنش
            transaction = Transaction.objects.create(
                user=request.user,
                credit_amount=credit_amount,
                price=price,
                status='pending'
            )
            
            # ارسال به ZarinPal
            return redirect_to_zarinpal(request, transaction)
            
        except ValueError:
            messages.error(request, '❌ لطفاً عدد معتبر وارد کنید.')
            return redirect('buy_credit')
    
    context = {
        'user_credit': user_credit,
        'price_per_1000': CREDIT_PRICE_PER_1000,
    }
    return render(request, 'billing/buy_credit.html', context)


def redirect_to_zarinpal(request, transaction):
    """ارسال درخواست به ZarinPal و Redirect"""
    
    payload = {
        "merchant_id": settings.ZARINPAL_MERCHANT_ID,
        "amount": transaction.price,  # به تومان
        "description": f"خرید {transaction.credit_amount} کردیت",
        "callback_url": settings.ZARINPAL_CALLBACK_URL,
        "metadata": {
            "email": request.user.email if request.user.email else "user@example.com",  # ✅ فیکس
            "mobile": "09123456789"  # ✅ فیکس - موبایل تستی
        }
    }
    
    try:
        response = requests.post(ZARINPAL_WEBGATE, json=payload, timeout=10)
        result = response.json()
        
        if result.get('data') and result['data'].get('code') == 100:
            authority = result['data']['authority']
            
            # ذخیره Authority
            transaction.authority = authority
            transaction.save()
            
            # Redirect به درگاه
            return redirect(f"{ZARINPAL_STARTPAY}{authority}")
        else:
            messages.error(request, f"❌ خطا در اتصال به درگاه: {result.get('errors', 'نامشخص')}")
            transaction.status = 'failed'
            transaction.save()
            return redirect('transactions_list')
    
    except Exception as e:
        messages.error(request, f'❌ خطا: {str(e)}')
        transaction.status = 'failed'
        transaction.save()
        return redirect('transactions_list')


@login_required
def verify_payment(request):
    """Callback از ZarinPal"""
    
    authority = request.GET.get('Authority')
    status = request.GET.get('Status')
    
    if not authority or status != 'OK':
        messages.error(request, '❌ پرداخت لغو شد یا با خطا مواجه شد.')
        return redirect('transactions_list')
    
    try:
        transaction = Transaction.objects.get(authority=authority, user=request.user)
    except Transaction.DoesNotExist:
        messages.error(request, '❌ تراکنش یافت نشد.')
        return redirect('transactions_list')
    
    # Verify با ZarinPal
    payload = {
        "merchant_id": settings.ZARINPAL_MERCHANT_ID,
        "amount": transaction.price,
        "authority": authority
    }
    
    try:
        response = requests.post(ZARINPAL_VERIFY, json=payload, timeout=10)
        result = response.json()
        
        if result.get('data') and result['data'].get('code') == 100:
            # پرداخت موفق
            ref_id = result['data']['ref_id']
            
            transaction.status = 'paid'
            transaction.ref_id = ref_id
            transaction.paid_at = timezone.now()
            transaction.save()
            
            # اضافه کردن کردیت به حساب کاربر
            user_credit, created = UserCredit.objects.get_or_create(user=request.user)
            user_credit.balance += transaction.credit_amount
            user_credit.save()
            
            messages.success(request, f'✅ پرداخت موفق! {transaction.credit_amount} کردیت به حساب شما اضافه شد. (کد پیگیری: {ref_id})')
        else:
            transaction.status = 'failed'
            transaction.save()
            messages.error(request, f'❌ پرداخت ناموفق: {result.get("errors", "نامشخص")}')
    
    except Exception as e:
        transaction.status = 'failed'
        transaction.save()
        messages.error(request, f'❌ خطا در تایید پرداخت: {str(e)}')
    
    return redirect('transactions_list')


@login_required
def pay_transaction(request, transaction_id):
    """پرداخت مجدد تراکنش pending"""
    
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    
    if transaction.status != 'pending':
        messages.warning(request, '⚠️ این تراکنش قبلاً پردازش شده است.')
        return redirect('transactions_list')
    
    # ارسال به ZarinPal
    return redirect_to_zarinpal(request, transaction)


@login_required
def transactions_list(request):
    """لیست تراکنش‌های کاربر (صورتحساب‌ها)"""
    
    transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')
    
    # موجودی فعلی
    user_credit, created = UserCredit.objects.get_or_create(user=request.user)
    
    context = {
        'transactions': transactions,
        'user_credit': user_credit,
    }
    return render(request, 'billing/transactions_list.html', context)