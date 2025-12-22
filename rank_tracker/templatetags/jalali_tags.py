"""
فیلترهای تبدیل تاریخ میلادی به شمسی (جلالی)
"""
from django import template
from jdatetime import datetime as jdatetime

register = template.Library()


@register.filter(name='jalali')
def jalali(value, format_string='%Y/%m/%d'):
    """
    تبدیل تاریخ میلادی به شمسی

    استفاده:
        {{ date_value|jalali }}
        {{ date_value|jalali:"%Y/%m/%d %H:%M" }}
    """
    if not value:
        return ''

    try:
        # تبدیل به jdatetime
        j_date = jdatetime.fromgregorian(datetime=value)
        return j_date.strftime(format_string)
    except:
        # اگر خطایی رخ داد، تاریخ اصلی را برگردان
        return str(value)


@register.filter(name='jalali_date')
def jalali_date(value):
    """
    تبدیل تاریخ به فرمت کوتاه شمسی (بدون ساعت)
    مثال: 1403/09/30
    """
    return jalali(value, '%Y/%m/%d')


@register.filter(name='jalali_datetime')
def jalali_datetime(value):
    """
    تبدیل تاریخ به فرمت کامل شمسی (با ساعت)
    مثال: 1403/09/30 14:25
    """
    return jalali(value, '%Y/%m/%d %H:%M')
