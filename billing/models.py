from django.db import models
from django.conf import settings
from django.utils import timezone


class UserCredit(models.Model):
    """موجودی کردیت کاربر"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='credit')
    balance = models.IntegerField(default=0)  # تعداد کردیت
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.balance} کردیت"
    
    class Meta:
        verbose_name = "موجودی کردیت"
        verbose_name_plural = "موجودی کردیت کاربران"


class Transaction(models.Model):
    """تراکنش‌های خرید کردیت"""
    STATUS_CHOICES = [
        ('pending', 'در انتظار پرداخت'),
        ('paid', 'پرداخت شده'),
        ('failed', 'ناموفق'),
        ('cancelled', 'لغو شده'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    credit_amount = models.IntegerField()  # تعداد کردیت
    price = models.IntegerField()  # قیمت به تومان
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # ZarinPal
    authority = models.CharField(max_length=255, blank=True, null=True)
    ref_id = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.credit_amount} کردیت - {self.get_status_display()}"
    
    class Meta:
        verbose_name = "تراکنش"
        verbose_name_plural = "تراکنش‌ها"
        ordering = ['-created_at']