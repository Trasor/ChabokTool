from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, OTPVerification, LoginAttempt


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    پنل ادمین سفارشی برای مدل User
    """
    list_display = ['username', 'email', 'phone_number', 'get_full_name',
                    'is_phone_verified', 'is_email_verified', 'is_active', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'is_phone_verified',
                   'is_email_verified', 'date_joined']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'phone_number']
    ordering = ['-date_joined']

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('اطلاعات شخصی', {'fields': ('first_name', 'last_name', 'email',
                                       'phone_number', 'profile_picture')}),
        ('وضعیت تایید', {'fields': ('is_phone_verified', 'is_email_verified')}),
        ('دسترسی‌ها', {'fields': ('is_active', 'is_staff', 'is_superuser',
                                   'groups', 'user_permissions')}),
        ('تاریخ‌ها', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone_number', 'password1', 'password2'),
        }),
    )

    readonly_fields = ['date_joined', 'last_login']


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    """
    پنل ادمین برای مدیریت OTP
    """
    list_display = ['phone_number', 'otp_code', 'created_at', 'expires_at',
                    'is_used', 'attempts', 'status_badge']
    list_filter = ['is_used', 'created_at']
    search_fields = ['phone_number', 'otp_code']
    ordering = ['-created_at']
    readonly_fields = ['created_at']

    def status_badge(self, obj):
        if obj.is_used:
            return format_html('<span style="color: green;">✓ استفاده شده</span>')
        elif obj.is_expired():
            return format_html('<span style="color: red;">✗ منقضی شده</span>')
        else:
            return format_html('<span style="color: orange;">⏳ فعال</span>')
    status_badge.short_description = 'وضعیت'


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    """
    پنل ادمین برای نظارت بر تلاش‌های ورود
    """
    list_display = ['username', 'ip_address', 'attempted_at', 'success', 'status_badge']
    list_filter = ['success', 'attempted_at']
    search_fields = ['username', 'ip_address']
    ordering = ['-attempted_at']
    readonly_fields = ['username', 'ip_address', 'attempted_at', 'user_agent']

    def status_badge(self, obj):
        if obj.success:
            return format_html('<span style="color: green;">✓ موفق</span>')
        else:
            return format_html('<span style="color: red;">✗ ناموفق</span>')
    status_badge.short_description = 'نتیجه'

    def has_add_permission(self, request):
        """جلوگیری از اضافه کردن دستی"""
        return False

    def has_delete_permission(self, request, obj=None):
        """فقط سوپریوزر می‌تواند حذف کند"""
        return request.user.is_superuser
