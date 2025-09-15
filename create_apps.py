# create_apps.py - ایجاد فایل‌های app ها
from pathlib import Path

print("📱 ایجاد فایل‌های Apps...")
print("=" * 40)

def create_accounts_urls():
    """ایجاد accounts/urls.py"""
    content = '''from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
]
'''
    
    file_path = Path("backend") / "accounts" / "urls.py"
    file_path.write_text(content, encoding='utf-8')
    print("✅ accounts/urls.py ایجاد شد")

def create_accounts_views():
    """ایجاد accounts/views.py"""
    content = '''from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def login_view(request):
    """ورود کاربران"""
    if request.method == 'POST':
        return JsonResponse({'message': 'Login page - به زودی آماده میشه'})
    return JsonResponse({'error': 'فقط POST مجاز است'})

@csrf_exempt
def register_view(request):
    """ثبت نام کاربران"""
    if request.method == 'POST':
        return JsonResponse({'message': 'Register page - به زودی آماده میشه'})
    return JsonResponse({'error': 'فقط POST مجاز است'})

@csrf_exempt
def profile_view(request):
    """پروفایل کاربر"""
    return JsonResponse({'message': 'Profile page - به زودی آماده میشه'})
'''
    
    file_path = Path("backend") / "accounts" / "views.py"
    file_path.write_text(content, encoding='utf-8')
    print("✅ accounts/views.py ایجاد شد")

def create_modules_urls():
    """ایجاد modules/urls.py"""
    content = '''from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.module_list, name='module_list'),
    path('detail/<int:module_id>/', views.module_detail, name='module_detail'),
]
'''
    
    file_path = Path("backend") / "modules" / "urls.py"
    file_path.write_text(content, encoding='utf-8')
    print("✅ modules/urls.py ایجاد شد")

def create_modules_views():
    """ایجاد modules/views.py"""
    content = '''from django.http import JsonResponse

def module_list(request):
    """لیست ماژول‌ها"""
    modules = [
        {
            'id': 1,
            'name': 'Comment Scheduler',
            'description': 'زمان‌بندی کامنت‌های وردپرس',
            'price': 400,
            'status': 'فعال'
        },
        {
            'id': 2, 
            'name': 'Keyword Research',
            'description': 'تحقیق کلمات کلیدی',
            'price': 150,
            'status': 'به زودی'
        }
    ]
    
    return JsonResponse({'modules': modules})

def module_detail(request, module_id):
    """جزئیات ماژول"""
    return JsonResponse({
        'id': module_id,
        'message': f'جزئیات ماژول {module_id} - به زودی آماده میشه'
    })
'''
    
    file_path = Path("backend") / "modules" / "views.py"
    file_path.write_text(content, encoding='utf-8')
    print("✅ modules/views.py ایجاد شد")

def create_home_template():
    """ایجاد صفحه اصلی"""
    content = '''<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChabokTool - پلتفرم ابزارهای SEO</title>
    <style>
        body {
            font-family: 'Tahoma', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            text-align: center;
            max-width: 600px;
        }
        h1 {
            color: #333;
            margin-bottom: 20px;
            font-size: 2.5em;
        }
        .success {
            background: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
            border-right: 5px solid #28a745;
        }
        .links {
            margin-top: 30px;
        }
        .btn {
            display: inline-block;
            padding: 12px 25px;
            margin: 10px;
            background: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            transition: background 0.3s;
        }
        .btn:hover {
            background: #0056b3;
        }
        .api-test {
            margin-top: 30px;
            text-align: right;
        }
        .api-btn {
            background: #28a745;
            padding: 8px 15px;
            border: none;
            color: white;
            border-radius: 5px;
            cursor: pointer;
            margin: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 پلتفرم ChabokTool</h1>
        
        <div class="success">
            <strong>موفقیت!</strong> پلتفرم با موفقیت راه‌اندازی شد و آماده استفاده است.
        </div>
        
        <p>پلتفرم ابزارهای SEO و افزونه‌های وردپرس شما آماده است!</p>
        
        <div class="links">
            <a href="/admin/" class="btn">پنل مدیریت</a>
            <a href="/api/modules/list/" class="btn">API ماژول‌ها</a>
        </div>
        
        <div class="api-test">
            <h3>تست API:</h3>
            <button class="api-btn" onclick="testModules()">تست لیست ماژول‌ها</button>
            <button class="api-btn" onclick="testAccounts()">تست اکانت</button>
            
            <div id="result" style="margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 5px; display: none;"></div>
        </div>
    </div>
    
    <script>
        function testModules() {
            fetch('/api/modules/list/')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('result').style.display = 'block';
                    document.getElementById('result').innerHTML = '<strong>نتیجه تست ماژول‌ها:</strong><br>' + JSON.stringify(data, null, 2);
                });
        }
        
        function testAccounts() {
            fetch('/api/accounts/profile/')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('result').style.display = 'block';
                    document.getElementById('result').innerHTML = '<strong>نتیجه تست اکانت:</strong><br>' + JSON.stringify(data, null, 2);
                });
        }
    </script>
</body>
</html>'''
    
    file_path = Path("backend") / "templates" / "index.html"
    file_path.write_text(content, encoding='utf-8')
    print("✅ templates/index.html ایجاد شد")

def main():
    """اجرای اصلی"""
    create_accounts_urls()
    create_accounts_views()
    create_modules_urls()
    create_modules_views()
    create_home_template()
    
    print("\n🎉 همه فایل‌های App ایجاد شدند!")
    print("🔄 حالا Django رو تست کنیم:")
    print("\nدستور: python manage.py migrate")
    print("سپس: python manage.py runserver")
    
    input("\nبرای خروج Enter بزنید...")

if __name__ == "__main__":
    main()