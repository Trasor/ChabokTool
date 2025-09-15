from django.contrib.auth.models import AbstractUser
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
