from django import template
from django.utils import timezone
import jdatetime

register = template.Library()


@register.filter
def jalali_date(value):
    """تبدیل تاریخ میلادی به شمسی"""
    if not value:
        return ""
    
    # اگه timezone-aware باشه، به تهران تبدیل کن
    if timezone.is_aware(value):
        value = timezone.localtime(value)
    
    # تبدیل به شمسی
    j_date = jdatetime.datetime.fromgregorian(datetime=value)
    return j_date.strftime('%Y/%m/%d')


@register.filter
def jalali_datetime(value):
    """تبدیل تاریخ و ساعت میلادی به شمسی"""
    if not value:
        return ""
    
    # اگه timezone-aware باشه، به تهران تبدیل کن
    if timezone.is_aware(value):
        value = timezone.localtime(value)
    
    # تبدیل به شمسی
    j_date = jdatetime.datetime.fromgregorian(datetime=value)
    return j_date.strftime('%Y/%m/%d ساعت %H:%M')


@register.filter
def jalali_time(value):
    """نمایش فقط ساعت"""
    if not value:
        return ""
    
    # اگه timezone-aware باشه، به تهران تبدیل کن
    if timezone.is_aware(value):
        value = timezone.localtime(value)
    
    return value.strftime('%H:%M')