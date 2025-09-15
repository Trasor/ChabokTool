# create_users.py - سیستم کاربران کامل
from pathlib import Path

print("👤 ایجاد سیستم کاربران...")
print("=" * 40)

def create_user_models():
    """ایجاد accounts/models.py"""
    content = '''from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """کاربر سفارشی"""
    email = models.EmailField(unique=True, verbose_name='ایمیل')
    phone = models.CharField(max_length=15, blank=True, verbose_name='شماره تلفن')
    
    # اطلاعات تکمیلی
    company_name = models.CharField(max_length=255, blank=True, verbose_name='نام شرکت')
    website = models.URLField(blank=True, verbose_name='وب‌سایت')
    
    # وضعیت حساب
    email_verified = models.BooleanField(default=False, verbose_name='ایمیل تأیید شده')
    is_premium = models.BooleanField(default=False, verbose_name='اکانت پریمیوم')
    
    # مالی
    credit_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='موجودی اعتبار')
    
    # تاریخ
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ثبت نام')
    last_login_at = models.DateTimeField(null=True, blank=True, verbose_name='آخرین ورود')
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'
    
    def __str__(self):
        return f"{self.email} ({self.username})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

class UserProfile(models.Model):
    """پروفایل کاربر"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='کاربر')
    avatar = models.ImageField(upload_to='avatars/', blank=True, verbose_name='تصویر پروفایل')
    bio = models.TextField(max_length=500, blank=True, verbose_name='درباره من')
    address = models.TextField(blank=True, verbose_name='آدرس')
    city = models.CharField(max_length=100, blank=True, verbose_name='شهر')
    
    # تنظیمات اعلان‌ها
    email_notifications = models.BooleanField(default=True, verbose_name='اعلان‌های ایمیل')
    sms_notifications = models.BooleanField(default=False, verbose_name='اعلان‌های پیامک')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'پروفایل کاربر'
        verbose_name_plural = 'پروفایل‌های کاربران'
    
    def __str__(self):
        return f"پروفایل {self.user.email}"
'''
    
    file_path = Path("backend") / "accounts" / "models.py"
    file_path.write_text(content, encoding='utf-8')
    print("✅ accounts/models.py ایجاد شد")

def create_user_admin():
    """ایجاد accounts/admin.py"""
    content = '''from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'پروفایل'

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_premium', 'credit_balance', 'email_verified', 'created_at')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'email_verified', 'is_premium', 'created_at')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'company_name')
    ordering = ('-created_at',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('اطلاعات اضافی', {
            'fields': ('email_verified', 'is_premium', 'credit_balance', 'phone', 'company_name', 'website')
        }),
    )
    
    readonly_fields = ('created_at', 'last_login_at')
'''
    
    file_path = Path("backend") / "accounts" / "admin.py"
    file_path.write_text(content, encoding='utf-8')
    print("✅ accounts/admin.py ایجاد شد")

def create_user_views():
    """ایجاد accounts/views.py جدید"""
    content = '''from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import User, UserProfile
import json

def register_view(request):
    """صفحه ثبت نام"""
    if request.method == 'POST':
        if request.content_type == 'application/json':
            # API request
            data = json.loads(request.body)
            email = data.get('email')
            username = data.get('username')
            password = data.get('password')
            first_name = data.get('first_name', '')
            last_name = data.get('last_name', '')
            
            # بررسی وجود کاربر
            if User.objects.filter(email=email).exists():
                return JsonResponse({'error': 'این ایمیل قبلاً ثبت شده است'}, status=400)
            
            if User.objects.filter(username=username).exists():
                return JsonResponse({'error': 'این نام کاربری قبلاً گرفته شده است'}, status=400)
            
            # ایجاد کاربر
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # ایجاد پروفایل
            UserProfile.objects.create(user=user)
            
            return JsonResponse({
                'success': True,
                'message': 'ثبت نام با موفقیت انجام شد',
                'user_id': user.id
            })
        
        else:
            # Form request
            email = request.POST.get('email')
            username = request.POST.get('username')
            password = request.POST.get('password')
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            
            if User.objects.filter(email=email).exists():
                messages.error(request, 'این ایمیل قبلاً ثبت شده است')
                return render(request, 'accounts/register.html')
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            UserProfile.objects.create(user=user)
            
            messages.success(request, 'ثبت نام با موفقیت انجام شد. حالا می‌توانید وارد شوید.')
            return redirect('login')
    
    return render(request, 'accounts/register.html')

def login_view(request):
    """صفحه ورود"""
    if request.method == 'POST':
        if request.content_type == 'application/json':
            # API request
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            
            try:
                user = User.objects.get(email=email)
                user = authenticate(request, username=user.username, password=password)
                
                if user:
                    login(request, user)
                    return JsonResponse({
                        'success': True,
                        'message': 'ورود موفقیت‌آمیز',
                        'user': {
                            'id': user.id,
                            'username': user.username,
                            'email': user.email,
                            'full_name': user.get_full_name()
                        }
                    })
                else:
                    return JsonResponse({'error': 'ایمیل یا رمز عبور اشتباه است'}, status=400)
            
            except User.DoesNotExist:
                return JsonResponse({'error': 'ایمیل یا رمز عبور اشتباه است'}, status=400)
        
        else:
            # Form request
            email = request.POST.get('email')
            password = request.POST.get('password')
            
            try:
                user = User.objects.get(email=email)
                user = authenticate(request, username=user.username, password=password)
                
                if user:
                    login(request, user)
                    return redirect('profile')
                else:
                    messages.error(request, 'ایمیل یا رمز عبور اشتباه است')
            
            except User.DoesNotExist:
                messages.error(request, 'ایمیل یا رمز عبور اشتباه است')
    
    return render(request, 'accounts/login.html')

@login_required
def profile_view(request):
    """صفحه پروفایل کاربر"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # بروزرسانی پروفایل
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.phone = request.POST.get('phone', '')
        request.user.company_name = request.POST.get('company_name', '')
        request.user.website = request.POST.get('website', '')
        request.user.save()
        
        profile.bio = request.POST.get('bio', '')
        profile.address = request.POST.get('address', '')
        profile.city = request.POST.get('city', '')
        profile.email_notifications = request.POST.get('email_notifications') == 'on'
        profile.sms_notifications = request.POST.get('sms_notifications') == 'on'
        profile.save()
        
        messages.success(request, 'پروفایل با موفقیت بروزرسانی شد')
    
    context = {
        'user': request.user,
        'profile': profile
    }
    
    return render(request, 'accounts/profile.html', context)

def logout_view(request):
    """خروج کاربر"""
    logout(request)
    messages.success(request, 'با موفقیت خارج شدید')
    return redirect('home')
'''
    
    file_path = Path("backend") / "accounts" / "views.py"
    file_path.write_text(content, encoding='utf-8')
    print("✅ accounts/views.py بروزرسانی شد")

def create_user_urls():
    """بروزرسانی accounts/urls.py"""
    content = '''from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
]
'''
    
    file_path = Path("backend") / "accounts" / "urls.py"
    file_path.write_text(content, encoding='utf-8')
    print("✅ accounts/urls.py بروزرسانی شد")

def update_settings():
    """بروزرسانی settings.py"""
    settings_path = Path("backend") / "platform_api" / "settings.py"
    content = settings_path.read_text(encoding='utf-8')
    
    # اضافه کردن AUTH_USER_MODEL
    if "AUTH_USER_MODEL" not in content:
        auth_line = "# Auth settings\nAUTH_USER_MODEL = 'accounts.User'\n"
        content = content.replace("# Default primary key", auth_line + "\n# Default primary key")
        
        settings_path.write_text(content, encoding='utf-8')
        print("✅ settings.py بروزرسانی شد")

def main():
    """اجرای اصلی"""
    create_user_models()
    create_user_admin()
    create_user_views()
    create_user_urls()
    update_settings()
    
    print("\n🎉 سیستم کاربران ایجاد شد!")
    print("🔄 دستورات بعدی:")
    print("1. python manage.py makemigrations accounts")
    print("2. python manage.py migrate")
    print("3. python manage.py runserver")
    print("4. تست ثبت نام و ورود")
    
    input("\nبرای خروج Enter بزنید...")

if __name__ == "__main__":
    main()