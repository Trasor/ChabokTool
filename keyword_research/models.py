from django.db import models
from django.conf import settings
from django.utils import timezone


class ResearchRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در حال انتظار'),
        ('running', 'در حال انجام'),
        ('completed', 'تکمیل شده'),
        ('failed', 'ناموفق'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    created_date = models.DateTimeField(default=timezone.now)
    completed_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    task_id = models.CharField(max_length=255, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    ai_analysis_enabled = models.BooleanField(default=False)  # ✅ جدید
    
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


class Keyword(models.Model):
    STATUS_CHOICES = [
        (0, 'مقایسه نشده'),
        (1, 'PKW (Primary Keyword)'),
        (2, 'AKW (Auxiliary Keyword)'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    request = models.ForeignKey(ResearchRequest, on_delete=models.CASCADE, related_name='keywords')
    original_id = models.IntegerField(null=True, blank=True)
    keyword = models.CharField(max_length=255)
    search_volume = models.IntegerField()
    links = models.TextField(blank=True)
    word_count = models.IntegerField(null=True, blank=True)  # ✅ آپدیت: nullable
    status = models.IntegerField(choices=STATUS_CHOICES, default=0)
    description = models.TextField(blank=True)
    akw_str = models.TextField(blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    
    # ✅ فیلدهای جدید AI
    meta_titles = models.TextField(blank=True, null=True)
    search_intent = models.CharField(max_length=100, blank=True, null=True)
    intent_mapping = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self):
        return self.keyword