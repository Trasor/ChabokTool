from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
import math


class RankProject(models.Model):
    """پروژه ردیابی رتبه Google"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rank_projects')
    project_name = models.CharField(max_length=255, verbose_name='نام پروژه')
    target_domain = models.CharField(max_length=255, verbose_name='دامنه هدف')
    keyword_capacity = models.IntegerField(
        validators=[MinValueValidator(100)],
        verbose_name='ظرفیت کلمات کلیدی'
    )
    update_count_current_month = models.IntegerField(default=0, verbose_name='تعداد آپدیت این ماه')
    last_update_at = models.DateTimeField(null=True, blank=True, verbose_name='آخرین آپدیت')
    created_date = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    is_active = models.BooleanField(default=True, verbose_name='فعال')

    class Meta:
        db_table = 'rank_tracker_projects'
        verbose_name = 'پروژه ردیابی رتبه'
        verbose_name_plural = 'پروژه‌های ردیابی رتبه'
        ordering = ['-created_date']

    def __str__(self):
        return f"{self.project_name} ({self.target_domain})"

    @property
    def can_update(self):
        """آیا می‌تواند آپدیت کند؟ (محدودیت 4 بار در ماه)"""
        return self.update_count_current_month < 4

    @property
    def keywords_count(self):
        """تعداد کلمات کلیدی فعلی"""
        return self.keywords.count()

    @property
    def remaining_capacity(self):
        """ظرفیت باقیمانده"""
        return self.keyword_capacity - self.keywords_count

    def check_and_reset_monthly_counter(self):
        """بررسی و reset کردن شمارنده ماهانه در صورت نیاز"""
        if self.last_update_at:
            current_month = timezone.now().month
            last_update_month = self.last_update_at.month
            if current_month != last_update_month:
                self.update_count_current_month = 0
                self.save(update_fields=['update_count_current_month'])


class RankKeyword(models.Model):
    """کلمات کلیدی هر پروژه"""
    project = models.ForeignKey(RankProject, on_delete=models.CASCADE, related_name='keywords')
    keyword = models.CharField(max_length=500, verbose_name='کلمه کلیدی')
    current_rank = models.IntegerField(null=True, blank=True, verbose_name='رتبه فعلی')
    previous_rank = models.IntegerField(null=True, blank=True, verbose_name='رتبه قبلی')
    highest_rank = models.IntegerField(null=True, blank=True, verbose_name='بهترین رتبه')

    # اطلاعات صفحه رتبه گرفته
    ranked_url = models.URLField(max_length=1000, null=True, blank=True, verbose_name='URL صفحه')
    ranked_page_title = models.CharField(max_length=500, null=True, blank=True, verbose_name='عنوان صفحه')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')

    class Meta:
        db_table = 'rank_tracker_keywords'
        verbose_name = 'کلمه کلیدی'
        verbose_name_plural = 'کلمات کلیدی'
        unique_together = ('project', 'keyword')
        ordering = ['keyword']

    def __str__(self):
        return f"{self.keyword} - Rank: {self.current_rank or 'N/A'}"

    @property
    def page_number(self):
        """شماره صفحه (هر 10 نتیجه = 1 صفحه)"""
        if self.current_rank:
            return math.ceil(self.current_rank / 10)
        return None

    @property
    def rank_change(self):
        """تغییر رتبه نسبت به قبل"""
        if self.current_rank and self.previous_rank:
            return self.previous_rank - self.current_rank  # مثبت = بهبود
        return None

    @property
    def average_rank(self):
        """میانگین رتبه از تاریخچه"""
        history = self.history.all()
        if history.exists():
            total = sum(h.rank for h in history if h.rank)
            return round(total / history.count(), 1) if history.count() > 0 else None
        return None

    def update_rank(self, new_rank, ranked_url=None, ranked_title=None):
        """آپدیت رتبه و ذخیره در تاریخچه"""
        self.previous_rank = self.current_rank
        self.current_rank = new_rank

        # ذخیره URL و title صفحه
        if ranked_url:
            self.ranked_url = ranked_url
        if ranked_title:
            self.ranked_page_title = ranked_title

        # آپدیت بهترین رتبه
        if new_rank and (not self.highest_rank or new_rank < self.highest_rank):
            self.highest_rank = new_rank

        self.save()

        # ذخیره در تاریخچه
        RankHistory.objects.create(
            keyword=self,
            rank=new_rank,
            ranked_url=ranked_url,
            ranked_page_title=ranked_title
        )


class RankHistory(models.Model):
    """تاریخچه رتبه‌ها برای نمایش Chart"""
    keyword = models.ForeignKey(RankKeyword, on_delete=models.CASCADE, related_name='history')
    rank = models.IntegerField(null=True, blank=True, verbose_name='رتبه')
    ranked_url = models.URLField(max_length=1000, null=True, blank=True, verbose_name='URL صفحه')
    ranked_page_title = models.CharField(max_length=500, null=True, blank=True, verbose_name='عنوان صفحه')
    checked_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ بررسی')

    class Meta:
        db_table = 'rank_tracker_history'
        verbose_name = 'تاریخچه رتبه'
        verbose_name_plural = 'تاریخچه رتبه‌ها'
        ordering = ['-checked_at']

    def __str__(self):
        return f"{self.keyword.keyword} - {self.rank} - {self.checked_at.date()}"
