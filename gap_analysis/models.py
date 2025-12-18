from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class GapKeyword(models.Model):
    """مدل برای ذخیره کلمات و لینک‌های رقبا"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    request = models.ForeignKey('GapRequest', on_delete=models.CASCADE, related_name='keywords')
    keyword = models.CharField(max_length=500)  # کلمه کلیدی
    competitor = models.CharField(max_length=255)  # دامنه رقیب
    link = models.TextField(blank=True, default="-")  # لینک پیدا شده یا "-"
    
    class Meta:
        unique_together = ('request', 'keyword', 'competitor')
    
    def __str__(self):
        return f"{self.keyword} - {self.competitor}"


class GapRequest(models.Model):
    """مدل برای درخواست Gap Analysis"""
    STATUS_CHOICES = [
        ('pending', 'در حال انتظار'),
        ('running', 'در حال انجام'),
        ('completed', 'تکمیل شده'),
        ('failed', 'ناموفق'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)  # 3 کلمه اول توضیحات + "..."
    description = models.TextField(blank=True)  # توضیحات کامل کاربر
    created_date = models.DateTimeField(default=timezone.now)
    completed_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    task_id = models.CharField(max_length=255, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} - {self.user.username}"
    
    @property
    def duration(self):
        """محاسبه مدت زمان انجام"""
        if self.completed_date and self.created_date:
            delta = self.completed_date - self.created_date
            minutes = int(delta.total_seconds() / 60)
            seconds = int(delta.total_seconds() % 60)
            return f"{minutes}m {seconds}s"
        return "-"