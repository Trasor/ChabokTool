from django.db import models
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
        return [f.strip() for f in self.features.split('\n') if f.strip()]

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
        return [d.strip() for d in self.allowed_domains.split('\n') if d.strip()]
