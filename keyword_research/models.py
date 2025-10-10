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
        (0, 'در حال انجام'),
        (1, 'تکمیل شده'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    created_date = models.DateTimeField(default=timezone.now)
    status = models.IntegerField(choices=STATUS_CHOICES, default=0)
    
    def __str__(self):
        return f"{self.name} - {self.user.username}"