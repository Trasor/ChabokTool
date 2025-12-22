"""
فرم‌های مربوط به Rank Tracker
"""
from django import forms
from .models import RankProject, RankKeyword
import re


class ProjectCreateForm(forms.ModelForm):
    """فرم ساخت پروژه جدید"""

    class Meta:
        model = RankProject
        fields = ['project_name', 'target_domain', 'keyword_capacity']
        widgets = {
            'project_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام پروژه را وارد کنید'
            }),
            'target_domain': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'example.com',
                'dir': 'ltr'
            }),
            'keyword_capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 100,
                'step': 100,
                'value': 100
            })
        }
        labels = {
            'project_name': 'نام پروژه',
            'target_domain': 'دامنه هدف',
            'keyword_capacity': 'ظرفیت کلمات کلیدی'
        }
        help_texts = {
            'target_domain': 'دامنه را بدون http:// و www وارد کنید (مثال: digikala.com)',
            'keyword_capacity': 'تعداد کلمات کلیدی که می‌خواهید ردیابی کنید (حداقل 100)'
        }

    def clean_target_domain(self):
        """اعتبارسنجی و نرمال‌سازی دامنه"""
        domain = self.cleaned_data.get('target_domain')

        if not domain:
            raise forms.ValidationError('دامنه نمی‌تواند خالی باشد.')

        # حذف http://, https://, www.
        domain = domain.lower().strip()
        domain = re.sub(r'^https?://', '', domain)
        domain = re.sub(r'^www\.', '', domain)
        domain = domain.rstrip('/')

        # بررسی فرمت دامنه
        domain_pattern = r'^[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,}$'
        if not re.match(domain_pattern, domain):
            raise forms.ValidationError('فرمت دامنه صحیح نیست. مثال: example.com')

        return domain

    def clean_keyword_capacity(self):
        """اعتبارسنجی ظرفیت"""
        capacity = self.cleaned_data.get('keyword_capacity')

        if capacity < 100:
            raise forms.ValidationError('حداقل ظرفیت 100 کلمه است.')

        if capacity % 100 != 0:
            raise forms.ValidationError('ظرفیت باید مضربی از 100 باشد.')

        return capacity


class KeywordAddForm(forms.Form):
    """فرم اضافه کردن کلمه کلیدی به صورت دستی"""
    keywords = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': 'هر کلمه کلیدی را در یک خط وارد کنید...\nمثال:\nخرید گوشی\nقیمت لپ تاپ\nبهترین تبلت'
        }),
        label='کلمات کلیدی',
        help_text='هر کلمه کلیدی را در یک خط جداگانه وارد کنید'
    )

    def clean_keywords(self):
        """اعتبارسنجی و پاکسازی کلمات کلیدی"""
        keywords_text = self.cleaned_data.get('keywords')

        if not keywords_text:
            raise forms.ValidationError('لطفاً حداقل یک کلمه کلیدی وارد کنید.')

        # تبدیل به لیست و حذف خطوط خالی
        keywords = [
            line.strip()
            for line in keywords_text.split('\n')
            if line.strip()
        ]

        if not keywords:
            raise forms.ValidationError('هیچ کلمه کلیدی معتبری یافت نشد.')

        # حذف تکراری‌ها
        keywords = list(dict.fromkeys(keywords))

        return keywords


class KeywordImportForm(forms.Form):
    """فرم آپلود فایل Excel"""
    file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls'
        }),
        label='فایل Excel',
        help_text='فایل Excel با فرمت نمونه آپلود کنید (ستون: keyword)'
    )

    def clean_file(self):
        """اعتبارسنجی فایل"""
        file = self.cleaned_data.get('file')

        if not file:
            raise forms.ValidationError('لطفاً فایل را انتخاب کنید.')

        # بررسی پسوند
        if not (file.name.endswith('.xlsx') or file.name.endswith('.xls')):
            raise forms.ValidationError('فقط فایل‌های Excel (.xlsx, .xls) مجاز هستند.')

        # بررسی حجم (حداکثر 2MB)
        if file.size > 2 * 1024 * 1024:
            raise forms.ValidationError('حجم فایل نباید بیشتر از 2 مگابایت باشد.')

        return file
