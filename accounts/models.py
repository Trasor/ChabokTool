from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
import random
import string


class User(AbstractUser):
    """
    Custom User Model با فیلدهای اضافی برای سیستم احراز هویت پیشرفته
    """
    # فیلدهای شخصی
    first_name = models.CharField(max_length=150, verbose_name='نام')
    last_name = models.CharField(max_length=150, verbose_name='نام خانوادگی')

    # شماره تلفن با اعتبارسنجی
    phone_regex = RegexValidator(
        regex=r'^09\d{9}$',
        message="شماره تلفن باید به فرمت 09123456789 باشد"
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=11,
        unique=True,
        verbose_name='شماره تلفن'
    )

    # ایمیل (برای login و بازیابی رمز)
    email = models.EmailField(
        unique=True,
        verbose_name='ایمیل'
    )

    # عکس پروفایل
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        null=True,
        blank=True,
        verbose_name='تصویر پروفایل'
    )

    # وضعیت تایید
    is_phone_verified = models.BooleanField(default=False, verbose_name='شماره تایید شده')
    is_email_verified = models.BooleanField(default=False, verbose_name='ایمیل تایید شده')

    # تاریخ عضویت
    date_joined = models.DateTimeField(default=timezone.now, verbose_name='تاریخ عضویت')

    # آخرین ورود
    last_login = models.DateTimeField(null=True, blank=True, verbose_name='آخرین ورود')

    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"

    def get_full_name(self):
        """نام کامل کاربر"""
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        """نام کوتاه کاربر"""
        return self.first_name


class OTPVerification(models.Model):
    """
    مدل برای ذخیره کدهای OTP برای تایید شماره تلفن
    """
    phone_number = models.CharField(max_length=11, verbose_name='شماره تلفن')
    otp_code = models.CharField(max_length=6, verbose_name='کد OTP')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')
    expires_at = models.DateTimeField(verbose_name='زمان انقضا')
    is_used = models.BooleanField(default=False, verbose_name='استفاده شده')
    attempts = models.IntegerField(default=0, verbose_name='تعداد تلاش')

    class Meta:
        verbose_name = 'تایید OTP'
        verbose_name_plural = 'تاییدهای OTP'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.phone_number} - {self.otp_code}"

    @staticmethod
    def generate_otp():
        """تولید کد OTP 6 رقمی"""
        return ''.join(random.choices(string.digits, k=6))

    def is_expired(self):
        """بررسی انقضای کد"""
        return timezone.now() > self.expires_at

    def is_valid(self):
        """بررسی معتبر بودن کد"""
        return not self.is_used and not self.is_expired() and self.attempts < 5


class LoginAttempt(models.Model):
    """
    ثبت تلاش‌های ناموفق ورود برای امنیت
    """
    username = models.CharField(max_length=150, verbose_name='نام کاربری')
    ip_address = models.GenericIPAddressField(verbose_name='آدرس IP')
    attempted_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان تلاش')
    success = models.BooleanField(default=False, verbose_name='موفقیت‌آمیز')
    user_agent = models.TextField(blank=True, verbose_name='User Agent')

    class Meta:
        verbose_name = 'تلاش ورود'
        verbose_name_plural = 'تلاش‌های ورود'
        ordering = ['-attempted_at']

    def __str__(self):
        status = "موفق" if self.success else "ناموفق"
        return f"{self.username} - {self.ip_address} - {status}"
