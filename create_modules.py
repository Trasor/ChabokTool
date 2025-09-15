# create_modules.py - سیستم ماژول‌ها کامل
from pathlib import Path

print("📦 ایجاد سیستم ماژول‌ها...")
print("=" * 40)

def create_modules_models():
    """ایجاد modules/models.py کامل"""
    content = '''from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class ModuleCategory(models.Model):
    """دسته‌بندی ماژول‌ها"""
    name = models.CharField(max_length=100, verbose_name='نام')
    name_en = models.CharField(max_length=100, verbose_name='نام انگلیسی')
    slug = models.SlugField(unique=True, verbose_name='اسلاگ')
    description = models.TextField(verbose_name='توضیحات')
    icon = models.CharField(max_length=50, default='fas fa-cog', verbose_name='آیکون')
    color = models.CharField(max_length=7, default='#007bff', verbose_name='رنگ')
    order = models.IntegerField(default=0, verbose_name='ترتیب')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'دسته‌بندی ماژول'
        verbose_name_plural = 'دسته‌بندی‌های ماژول'
    
    def __str__(self):
        return self.name

class Module(models.Model):
    """ماژول‌های پلتفرم"""
    MODULE_TYPES = [
        ('wordpress_plugin', 'افزونه وردپرس'),
        ('online_tool', 'ابزار آنلاین'),
        ('api_service', 'سرویس API'),
    ]
    
    PRICING_TYPES = [
        ('one_time', 'پرداخت یکباره'),
        ('monthly', 'اشتراک ماهانه'),
        ('credit_based', 'بر اساس اعتبار'),
        ('free', 'رایگان'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'فعال'),
        ('maintenance', 'در حال تعمیر'),
        ('coming_soon', 'به زودی'),
        ('deprecated', 'منسوخ شده'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name='نام')
    name_en = models.CharField(max_length=100, verbose_name='نام انگلیسی')
    slug = models.SlugField(unique=True, verbose_name='اسلاگ')
    description = models.TextField(verbose_name='توضیحات کامل')
    short_description = models.CharField(max_length=255, verbose_name='توضیحات کوتاه')
    category = models.ForeignKey(ModuleCategory, on_delete=models.CASCADE, verbose_name='دسته‌بندی')
    
    # اطلاعات فنی
    module_type = models.CharField(max_length=20, choices=MODULE_TYPES, verbose_name='نوع ماژول')
    version = models.CharField(max_length=20, default='1.0.0', verbose_name='نسخه')
    min_wp_version = models.CharField(max_length=10, blank=True, verbose_name='حداقل نسخه وردپرس')
    
    # قیمت‌گذاری
    pricing_type = models.CharField(max_length=15, choices=PRICING_TYPES, verbose_name='نوع قیمت‌گذاری')
    price = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name='قیمت (تومان)')
    monthly_price = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True, verbose_name='قیمت ماهانه')
    credit_cost = models.IntegerField(null=True, blank=True, verbose_name='هزینه اعتبار')
    
    # ویژگی‌ها
    features = models.TextField(help_text='هر ویژگی در یک خط', verbose_name='ویژگی‌ها')
    requirements = models.TextField(blank=True, verbose_name='پیش‌نیازها')
    
    # وضعیت
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active', verbose_name='وضعیت')
    is_featured = models.BooleanField(default=False, verbose_name='ویژه')
    is_popular = models.BooleanField(default=False, verbose_name='محبوب')
    
    # رسانه
    icon = models.ImageField(upload_to='module_icons/', blank=True, verbose_name='آیکون')
    banner = models.ImageField(upload_to='module_banners/', blank=True, verbose_name='بنر')
    demo_url = models.URLField(blank=True, verbose_name='لینک دمو')
    
    # آمار
    download_count = models.IntegerField(default=0, verbose_name='تعداد دانلود')
    purchase_count = models.IntegerField(default=0, verbose_name='تعداد خرید')
    
    # تاریخ
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_featured', '-is_popular', 'name']
        verbose_name = 'ماژول'
        verbose_name_plural = 'ماژول‌ها'
    
    def __str__(self):
        return self.name
    
    def get_features_list(self):
        """بازگردانی ویژگی‌ها به صورت لیست"""
        return [f.strip() for f in self.features.split('\\n') if f.strip()]

class UserModule(models.Model):
    """ماژول‌های خریداری شده توسط کاربران"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='کاربر')
    module = models.ForeignKey(Module, on_delete=models.CASCADE, verbose_name='ماژول')
    
    # اطلاعات خرید
    purchased_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ خرید')
    price_paid = models.DecimalField(max_digits=10, decimal_places=0, verbose_name='مبلغ پرداختی')
    
    # License
    license_key = models.CharField(max_length=64, unique=True, verbose_name='کلید مجوز')
    allowed_domains = models.TextField(help_text='هر دامنه در یک خط', blank=True, verbose_name='دامنه‌های مجاز')
    max_domains = models.IntegerField(default=1, verbose_name='حداکثر دامنه')
    
    # وضعیت
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ انقضا')
    
    class Meta:
        unique_together = ['user', 'module']
        verbose_name = 'ماژول کاربر'
        verbose_name_plural = 'ماژول‌های کاربران'
    
    def __str__(self):
        return f"{self.user.email} - {self.module.name}"
    
    def save(self, *args, **kwargs):
        if not self.license_key:
            import secrets
            self.license_key = f"CT-{secrets.token_hex(16).upper()}"
        super().save(*args, **kwargs)
    
    def get_allowed_domains_list(self):
        """بازگردانی دامنه‌های مجاز به صورت لیست"""
        return [d.strip() for d in self.allowed_domains.split('\\n') if d.strip()]
'''
    
    file_path = Path("backend") / "modules" / "models.py"
    file_path.write_text(content, encoding='utf-8')
    print("✅ modules/models.py ایجاد شد")

def create_modules_admin():
    """ایجاد modules/admin.py"""
    content = '''from django.contrib import admin
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
'''
    
    file_path = Path("backend") / "modules" / "admin.py"
    file_path.write_text(content, encoding='utf-8')
    print("✅ modules/admin.py ایجاد شد")

def create_modules_views():
    """بروزرسانی modules/views.py"""
    content = '''from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Module, ModuleCategory, UserModule

def module_list(request):
    """لیست ماژول‌ها - API"""
    modules = Module.objects.filter(status='active')
    
    # فیلتر بر اساس دسته‌بندی
    category = request.GET.get('category')
    if category:
        modules = modules.filter(category__slug=category)
    
    modules_data = []
    for module in modules:
        modules_data.append({
            'id': str(module.id),
            'name': module.name,
            'short_description': module.short_description,
            'price': int(module.price),
            'pricing_type': module.get_pricing_type_display(),
            'module_type': module.get_module_type_display(),
            'category': module.category.name,
            'is_featured': module.is_featured,
            'is_popular': module.is_popular,
            'features': module.get_features_list()[:3],  # فقط 3 ویژگی اول
            'demo_url': module.demo_url
        })
    
    return JsonResponse({'modules': modules_data})

def module_detail(request, module_id):
    """جزئیات ماژول"""
    module = get_object_or_404(Module, id=module_id, status='active')
    
    # بررسی خرید کاربر
    user_has_module = False
    if request.user.is_authenticated:
        user_has_module = UserModule.objects.filter(
            user=request.user, 
            module=module, 
            is_active=True
        ).exists()
    
    data = {
        'id': str(module.id),
        'name': module.name,
        'description': module.description,
        'short_description': module.short_description,
        'price': int(module.price),
        'pricing_type': module.get_pricing_type_display(),
        'module_type': module.get_module_type_display(),
        'category': module.category.name,
        'version': module.version,
        'features': module.get_features_list(),
        'requirements': module.requirements,
        'demo_url': module.demo_url,
        'download_count': module.download_count,
        'user_has_module': user_has_module
    }
    
    return JsonResponse(data)

def categories_list(request):
    """لیست دسته‌بندی‌ها"""
    categories = ModuleCategory.objects.filter(is_active=True)
    
    categories_data = []
    for category in categories:
        categories_data.append({
            'slug': category.slug,
            'name': category.name,
            'description': category.description,
            'icon': category.icon,
            'color': category.color,
            'modules_count': category.module_set.filter(status='active').count()
        })
    
    return JsonResponse({'categories': categories_data})

@login_required
def user_modules(request):
    """ماژول‌های خریداری شده توسط کاربر"""
    user_modules = UserModule.objects.filter(user=request.user, is_active=True)
    
    modules_data = []
    for user_module in user_modules:
        modules_data.append({
            'module': {
                'id': str(user_module.module.id),
                'name': user_module.module.name,
                'version': user_module.module.version,
                'type': user_module.module.get_module_type_display()
            },
            'license_key': user_module.license_key,
            'purchased_at': user_module.purchased_at.strftime('%Y/%m/%d'),
            'allowed_domains': user_module.get_allowed_domains_list(),
            'max_domains': user_module.max_domains,
            'expires_at': user_module.expires_at.strftime('%Y/%m/%d') if user_module.expires_at else None
        })
    
    return JsonResponse({'user_modules': modules_data})
'''
    
    file_path = Path("backend") / "modules" / "views.py"
    file_path.write_text(content, encoding='utf-8')
    print("✅ modules/views.py بروزرسانی شد")

def create_modules_urls():
    """بروزرسانی modules/urls.py"""
    content = '''from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.module_list, name='module_list'),
    path('detail/<uuid:module_id>/', views.module_detail, name='module_detail'),
    path('categories/', views.categories_list, name='categories_list'),
    path('user-modules/', views.user_modules, name='user_modules'),
]
'''
    
    file_path = Path("backend") / "modules" / "urls.py"
    file_path.write_text(content, encoding='utf-8')
    print("✅ modules/urls.py بروزرسانی شد")

def main():
    """اجرای اصلی"""
    create_modules_models()
    create_modules_admin()
    create_modules_views()
    create_modules_urls()
    
    print("\n🎉 سیستم ماژول‌ها ایجاد شد!")
    print("🔄 دستورات بعدی:")
    print("1. python manage.py makemigrations modules")
    print("2. python manage.py migrate")
    print("3. python manage.py runserver")
    print("4. در پنل ادمین دسته‌بندی و ماژول Comment Scheduler اضافه کن")
    
    input("\nبرای خروج Enter بزنید...")

if __name__ == "__main__":
    main()