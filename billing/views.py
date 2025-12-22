from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.conf import settings
from .models import Transaction, UserCredit
import requests
import json
import logging

logger = logging.getLogger(__name__)


# قیمت هر 1000 کردیت
CREDIT_PRICE_PER_1000 = 500000  # 500,000 تومان

# ZarinPal Config
# URLs قدیمی (v4) - منسوخ شده
# ZARINPAL_WEBGATE = 'https://sandbox.zarinpal.com/pg/v4/payment/request.json'
# ZARINPAL_STARTPAY = 'https://sandbox.zarinpal.com/pg/StartPay/'
# ZARINPAL_VERIFY = 'https://sandbox.zarinpal.com/pg/v4/payment/verify.json'

# URLs جدید REST API
ZARINPAL_WEBGATE = 'https://sandbox.zarinpal.com/pg/rest/WebGate/PaymentRequest.json'
ZARINPAL_STARTPAY = 'https://sandbox.zarinpal.com/pg/StartPay/'
ZARINPAL_VERIFY = 'https://sandbox.zarinpal.com/pg/rest/WebGate/PaymentVerification.json'

# حالت Mock برای تست (اگه True باشه، واقعا پرداخت نمیره)
MOCK_PAYMENT = getattr(settings, 'MOCK_PAYMENT_FOR_DEV', False)


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

    # اگر حالت Mock فعال باشه، مستقیم کردیت اضافه کن (برای تست)
    if MOCK_PAYMENT:
        logger.info(f"🧪 Mock Payment Mode: Adding {transaction.credit_amount} credits to user {request.user.username}")

        # اضافه کردن کردیت
        user_credit, created = UserCredit.objects.get_or_create(user=request.user)
        user_credit.balance += transaction.credit_amount
        user_credit.save()

        # تغییر وضعیت تراکنش
        transaction.status = 'paid'
        transaction.ref_id = 'MOCK-' + str(transaction.id)
        transaction.paid_at = timezone.now()
        transaction.save()

        messages.success(request, f'✅ [تست] پرداخت موفق! {transaction.credit_amount} کردیت به حساب شما اضافه شد.')
        return redirect('transactions_list')

    # ادامه پرداخت واقعی با ZarinPal
    payload = {
        "MerchantID": settings.ZARINPAL_MERCHANT_ID,  # REST API از MerchantID استفاده می‌کنه
        "Amount": transaction.price,  # به تومان
        "Description": f"خرید {transaction.credit_amount} کردیت",
        "CallbackURL": settings.ZARINPAL_CALLBACK_URL,
        "Email": request.user.email if request.user.email else "user@example.com",
        "Mobile": "09123456789"
    }

    try:
        response = requests.post(ZARINPAL_WEBGATE, json=payload, timeout=10)

        # دیباگ: لاگ کردن response
        logger.info(f"ZarinPal Response Status: {response.status_code}")
        logger.info(f"ZarinPal Response Text: {response.text[:500]}")  # اولین 500 کاراکتر

        # بررسی status code
        if response.status_code != 200:
            messages.error(request, f"❌ خطا در اتصال به درگاه: HTTP {response.status_code}")
            transaction.status = 'failed'
            transaction.save()
            return redirect('transactions_list')

        # Parse کردن JSON
        try:
            result = response.json()
        except ValueError as json_error:
            logger.error(f"JSON Parse Error: {str(json_error)}")
            logger.error(f"Response Content: {response.text}")
            messages.error(request, f"❌ خطا در دریافت پاسخ از درگاه. لطفا دوباره تلاش کنید.")
            transaction.status = 'failed'
            transaction.save()
            return redirect('transactions_list')

        # بررسی پاسخ (REST API)
        # REST API: {"Status": 100, "Authority": "A00000000000000000000000000123456789"}
        if result.get('Status') == 100 and result.get('Authority'):
            authority = result['Authority']

            # ذخیره Authority
            transaction.authority = authority
            transaction.save()

            logger.info(f"✓ ZarinPal Authority received: {authority}")

            # Redirect به درگاه
            return redirect(f"{ZARINPAL_STARTPAY}{authority}")
        else:
            error_msg = result.get('errors', result.get('message', result.get('Status', 'نامشخص')))
            logger.error(f"✗ ZarinPal Error: Status={result.get('Status')}, Response={result}")
            messages.error(request, f"❌ خطا در اتصال به درگاه: {error_msg}")
            transaction.status = 'failed'
            transaction.save()
            return redirect('transactions_list')

    except requests.exceptions.Timeout:
        messages.error(request, '❌ زمان اتصال به درگاه تمام شد. لطفا دوباره تلاش کنید.')
        transaction.status = 'failed'
        transaction.save()
        return redirect('transactions_list')

    except requests.exceptions.ConnectionError:
        messages.error(request, '❌ خطا در اتصال به درگاه. لطفا اتصال اینترنت خود را بررسی کنید.')
        transaction.status = 'failed'
        transaction.save()
        return redirect('transactions_list')

    except Exception as e:
        logger.error(f"Unexpected error in redirect_to_zarinpal: {str(e)}", exc_info=True)
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
    
    # Verify با ZarinPal (REST API)
    payload = {
        "MerchantID": settings.ZARINPAL_MERCHANT_ID,
        "Amount": transaction.price,
        "Authority": authority
    }

    try:
        response = requests.post(ZARINPAL_VERIFY, json=payload, timeout=10)
        result = response.json()

        # REST API: {"Status": 100, "RefID": 123456789}
        if result.get('Status') == 100:
            # پرداخت موفق
            ref_id = str(result.get('RefID', ''))

            transaction.status = 'paid'
            transaction.ref_id = ref_id
            transaction.paid_at = timezone.now()
            transaction.save()

            # اضافه کردن کردیت به حساب کاربر
            user_credit, created = UserCredit.objects.get_or_create(user=request.user)
            user_credit.balance += transaction.credit_amount
            user_credit.save()

            logger.info(f"✓ Payment verified: RefID={ref_id}, Credits={transaction.credit_amount}")
            messages.success(request, f'✅ پرداخت موفق! {transaction.credit_amount} کردیت به حساب شما اضافه شد. (کد پیگیری: {ref_id})')
        else:
            transaction.status = 'failed'
            transaction.save()
            logger.error(f"✗ Payment verification failed: Status={result.get('Status')}, Response={result}")
            messages.error(request, f'❌ پرداخت ناموفق: وضعیت {result.get("Status")}')
    
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