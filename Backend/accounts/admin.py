from django.contrib import admin
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
