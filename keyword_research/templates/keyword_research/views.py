from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Keyword
import pandas as pd
from django.conf import settings
import os

def keyword_research(request):
    if request.method == 'POST':
        file = request.FILES['file']
        description = request.POST.get('description', '')
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith('.xlsx'):
            df = pd.read_excel(file)
        else:
            messages.error(request, 'فقط CSV یا XLSX پشتیبانی می‌شود.')
            return render(request, 'keyword_research/index.html')

        # پاک کردن دیتابیس قبلی (برای تست)
        Keyword.objects.all().delete()

        # ذخیره داده‌ها از ستون‌ها
        for index, row in df.iterrows():
            Keyword.objects.create(
                id=index + 1,  # ID از ردیف
                keyword=row.iloc[1],  # ستون دوم: کلمه
                search_volume=row.iloc[2],  # ستون سوم: search volume
                word_count=row.iloc[4],  # ستون پنجم: تعداد کلمات
                description=description,  # متاباکس حوزه برای همه
                status=0  # دیفالت
            )

        messages.success(request, 'فایل ایمپورت شد!')
        return redirect('keyword_research')

    return render(request, 'keyword_research/index.html')