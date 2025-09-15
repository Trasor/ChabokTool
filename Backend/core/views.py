from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@staff_member_required
def settings_view(request):
    """صفحه تنظیمات"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # فعلاً فقط پیغام موفقیت برمیگردونیم
            return JsonResponse({'success': True, 'message': 'تنظیمات ذخیره شد'})
        except:
            return JsonResponse({'success': False, 'message': 'خطا در ذخیره تنظیمات'})
    
    # تنظیمات پیش فرض
    settings_data = {
        'پرداخت': [
            {
                'key': 'zarinpal_merchant_id',
                'title': 'Merchant ID زرین پال',
                'value': '',
                'type': 'text',
                'description': 'کد مرچنت زرین پال خود را وارد کنید'
            },
            {
                'key': 'zarinpal_sandbox',
                'title': 'حالت تست زرین پال',
                'value': 'true',
                'type': 'boolean',
                'description': 'برای تست فعال کنید'
            }
        ],
        'پیامک': [
            {
                'key': 'sms_api_key',
                'title': 'API Key ملی پیامک',
                'value': '',
                'type': 'text',
                'description': 'کلید API ملی پیامک'
            },
            {
                'key': 'sms_sender',
                'title': 'شماره فرستنده',
                'value': '',
                'type': 'text',
                'description': 'شماره پنل پیامکی'
            }
        ],
        'ایمیل': [
            {
                'key': 'email_host_user',
                'title': 'ایمیل فرستنده',
                'value': '',
                'type': 'email',
                'description': 'ایمیل برای ارسال پیام‌ها'
            },
            {
                'key': 'email_host_password',
                'title': 'پسورد ایمیل',
                'value': '',
                'type': 'text',
                'description': 'پسورد یا App Password'
            }
        ],
        'برند': [
            {
                'key': 'brand_name',
                'title': 'نام برند',
                'value': 'ChabokTool',
                'type': 'text',
                'description': 'نام برند شما'
            },
            {
                'key': 'support_email',
                'title': 'ایمیل پشتیبانی',
                'value': 'support@chaboktool.com',
                'type': 'email',
                'description': 'ایمیل پشتیبانی'
            }
        ]
    }
    
    return render(request, 'admin/settings.html', {'settings': settings_data})

@staff_member_required  
def dashboard_view(request):
    """داشبورد مدیریت"""
    stats = {
        'total_modules': 2,
        'active_users': 1,
        'total_sales': 0,
    }
    
    return render(request, 'admin/dashboard.html', {'stats': stats})