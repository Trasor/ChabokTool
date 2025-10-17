from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Keyword(models.Model):
    STATUS_CHOICES = [
        (0, 'مقایسه نشده'),
        (1, 'PKW (Primary Keyword)'),
        (2, 'AKW (Auxiliary Keyword)'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    id = models.IntegerField(primary_key=True)
    keyword = models.CharField(max_length=255)
    search_volume = models.IntegerField()
    links = models.TextField(blank=True)
    word_count = models.IntegerField()
    status = models.IntegerField(choices=STATUS_CHOICES, default=0)
    description = models.TextField(blank=True)
    akw_str = models.TextField(blank=True)

    def __str__(self):
        return self.keyword

class ResearchRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در حال انتظار'),
        ('running', 'در حال انجام'),
        ('completed', 'تکمیل شده'),
        ('failed', 'ناموفق'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
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