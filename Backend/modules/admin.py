from django.contrib import admin
from .models import ModuleCategory, Module, UserModule

@admin.register(ModuleCategory)
class ModuleCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_en', 'order', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'name_en', 'description')
    prepopulated_fields = {'slug': ('name_en',)}
    list_editable = ('order', 'is_active')

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'module_type', 'pricing_type', 'price', 'status', 'is_featured', 'purchase_count')
    list_filter = ('category', 'module_type', 'pricing_type', 'status', 'is_featured', 'created_at')
    search_fields = ('name', 'name_en', 'description')
    prepopulated_fields = {'slug': ('name_en',)}
    list_editable = ('status', 'is_featured', 'price')
    readonly_fields = ('id', 'download_count', 'purchase_count', 'created_at', 'updated_at')
    
    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('name', 'name_en', 'slug', 'category', 'description', 'short_description')
        }),
        ('تنظیمات فنی', {
            'fields': ('module_type', 'version', 'min_wp_version')
        }),
        ('قیمت‌گذاری', {
            'fields': ('pricing_type', 'price', 'monthly_price', 'credit_cost')
        }),
        ('محتوا', {
            'fields': ('features', 'requirements')
        }),
        ('رسانه', {
            'fields': ('icon', 'banner', 'demo_url')
        }),
        ('وضعیت', {
            'fields': ('status', 'is_featured', 'is_popular')
        }),
        ('آمار', {
            'fields': ('download_count', 'purchase_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(UserModule)
class UserModuleAdmin(admin.ModelAdmin):
    list_display = ('user', 'module', 'license_key', 'price_paid', 'is_active', 'purchased_at')
    list_filter = ('module', 'is_active', 'purchased_at')
    search_fields = ('user__email', 'license_key', 'module__name')
    readonly_fields = ('license_key', 'purchased_at')
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('user', 'module', 'license_key', 'price_paid')
        }),
        ('تنظیمات دامنه', {
            'fields': ('allowed_domains', 'max_domains')
        }),
        ('وضعیت', {
            'fields': ('is_active', 'expires_at', 'purchased_at')
        }),
    )
