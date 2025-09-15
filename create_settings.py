# create_settings.py - ایجاد پنل تنظیمات
from pathlib import Path

print("⚙️ ایجاد پنل تنظیمات...")
print("=" * 40)

def create_core_models():
    """ایجاد core/models.py"""
    content = '''from django.db import models

class PlatformSetting(models.Model):
    """تنظیمات قابل تغییر پلتفرم"""
    SETTING_TYPES = [
        ('text', 'متن'),
        ('number', 'عدد'),
        ('boolean', 'بله/خیر'),
        ('email', 'ایمیل'),
    ]
    
    key = models.CharField(max_length=100, unique=True, verbose_name='کلید')
    value = models.TextField(verbose_name='مقدار')
    setting_type = models.CharField(max_length=10, choices=SETTING_TYPES, default='text', verbose_name='نوع')
    title = models.CharField(max_length=255, verbose_name='عنوان')
    description = models.TextField(blank=True, verbose_name='توضیحات')
    group = models.CharField(max_length=50, verbose_name='گروه')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'تنظیم'
        verbose_name_plural = 'تنظیمات'
        ordering = ['group', 'key']
    
    def __str__(self):
        return f"{self.title} ({self.key})"
    
    @classmethod
    def get_value(cls, key, default=None):
        try:
            setting = cls.objects.get(key=key, is_active=True)
            if setting.setting_type == 'boolean':
                return setting.value.lower() in ['true', '1', 'yes']
            elif setting.setting_type == 'number':
                return int(setting.value) if setting.value.isdigit() else default
            return setting.value
        except cls.DoesNotExist:
            return default
'''
    
    file_path = Path("backend") / "core" / "models.py"
    file_path.write_text(content, encoding='utf-8')
    print("✅ core/models.py ایجاد شد")

def create_core_admin():
    """ایجاد core/admin.py"""
    content = '''from django.contrib import admin
from .models import PlatformSetting

@admin.register(PlatformSetting)
class PlatformSettingAdmin(admin.ModelAdmin):
    list_display = ('title', 'key', 'group', 'setting_type', 'is_active')
    list_filter = ('group', 'setting_type', 'is_active')
    search_fields = ('title', 'key', 'description')
    list_editable = ('is_active',)
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('title', 'key', 'group', 'setting_type')
        }),
        ('مقدار', {
            'fields': ('value', 'description')
        }),
        ('وضعیت', {
            'fields': ('is_active',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # در حالت ویرایش
            return ['key']
        return []
'''
    
    file_path = Path("backend") / "core" / "admin.py"
    file_path.write_text(content, encoding='utf-8')
    print("✅ core/admin.py ایجاد شد")

def create_core_urls():
    """ایجاد core/urls.py"""
    content = '''from django.urls import path
from . import views

urlpatterns = [
    path('settings/', views.settings_view, name='settings'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
]
'''
    
    file_path = Path("backend") / "core" / "urls.py"
    file_path.write_text(content, encoding='utf-8')
    print("✅ core/urls.py ایجاد شد")

def create_core_views():
    """ایجاد core/views.py"""
    content = '''from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from .models import PlatformSetting
import json

@staff_member_required
def settings_view(request):
    """صفحه تنظیمات"""
    if request.method == 'POST':
        # ذخیره تنظیمات
        data = json.loads(request.body)
        for key, value in data.items():
            try:
                setting = PlatformSetting.objects.get(key=key)
                setting.value = str(value)
                setting.save()
            except PlatformSetting.DoesNotExist:
                pass
        
        return JsonResponse({'success': True, 'message': 'تنظیمات ذخیره شد'})
    
    # دریافت تنظیمات
    settings = PlatformSetting.objects.filter(is_active=True).order_by('group', 'key')
    settings_dict = {}
    
    for setting in settings:
        if setting.group not in settings_dict:
            settings_dict[setting.group] = []
        
        settings_dict[setting.group].append({
            'key': setting.key,
            'title': setting.title,
            'value': setting.value,
            'type': setting.setting_type,
            'description': setting.description
        })
    
    return render(request, 'admin/settings.html', {'settings': settings_dict})

@staff_member_required  
def dashboard_view(request):
    """داشبورد مدیریت"""
    stats = {
        'total_settings': PlatformSetting.objects.count(),
        'active_settings': PlatformSetting.objects.filter(is_active=True).count(),
    }
    
    return render(request, 'admin/dashboard.html', {'stats': stats})
'''
    
    file_path = Path("backend") / "core" / "views.py"
    file_path.write_text(content, encoding='utf-8')
    print("✅ core/views.py ایجاد شد")

def create_settings_template():
    """ایجاد template تنظیمات"""
    content = '''{% extends "admin/base.html" %}
{% load static %}

{% block title %}تنظیمات پلتفرم{% endblock %}

{% block extrahead %}
<style>
    .settings-container {
        max-width: 800px;
        margin: 20px auto;
        background: white;
        padding: 30px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .settings-group {
        margin-bottom: 30px;
        border: 1px solid #ddd;
        border-radius: 8px;
        overflow: hidden;
    }
    .group-header {
        background: #f8f9fa;
        padding: 15px;
        font-weight: bold;
        border-bottom: 1px solid #ddd;
    }
    .setting-item {
        padding: 15px;
        border-bottom: 1px solid #eee;
    }
    .setting-item:last-child {
        border-bottom: none;
    }
    .setting-label {
        font-weight: bold;
        margin-bottom: 5px;
    }
    .setting-input {
        width: 100%;
        padding: 8px;
        border: 1px solid #ddd;
        border-radius: 4px;
        margin-bottom: 5px;
    }
    .setting-description {
        font-size: 12px;
        color: #666;
    }
    .save-btn {
        background: #28a745;
        color: white;
        padding: 12px 25px;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        font-size: 16px;
    }
    .save-btn:hover {
        background: #218838;
    }
    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 10px;
        border-radius: 4px;
        margin-bottom: 20px;
        display: none;
    }
</style>
{% endblock %}

{% block content %}
<div class="settings-container">
    <h1>⚙️ تنظیمات پلتفرم</h1>
    
    <div id="success-message" class="success-message">
        تنظیمات با موفقیت ذخیره شد!
    </div>
    
    <form id="settings-form">
        {% for group_name, group_settings in settings.items %}
        <div class="settings-group">
            <div class="group-header">{{ group_name }}</div>
            
            {% for setting in group_settings %}
            <div class="setting-item">
                <div class="setting-label">{{ setting.title }}</div>
                
                {% if setting.type == 'boolean' %}
                    <select name="{{ setting.key }}" class="setting-input">
                        <option value="true" {% if setting.value == 'true' %}selected{% endif %}>بله</option>
                        <option value="false" {% if setting.value != 'true' %}selected{% endif %}>خیر</option>
                    </select>
                {% elif setting.type == 'number' %}
                    <input type="number" name="{{ setting.key }}" value="{{ setting.value }}" class="setting-input">
                {% else %}
                    <input type="text" name="{{ setting.key }}" value="{{ setting.value }}" class="setting-input">
                {% endif %}
                
                {% if setting.description %}
                    <div class="setting-description">{{ setting.description }}</div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        {% endfor %}
        
        <button type="submit" class="save-btn">💾 ذخیره تنظیمات</button>
    </form>
</div>

<script>
document.getElementById('settings-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const settings = {};
    
    for (let [key, value] of formData.entries()) {
        settings[key] = value;
    }
    
    fetch('/core/settings/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify(settings)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('success-message').style.display = 'block';
            setTimeout(() => {
                document.getElementById('success-message').style.display = 'none';
            }, 3000);
        }
    });
});
</script>
{% endblock %}'''
    
    templates_dir = Path("backend") / "templates" / "admin"
    templates_dir.mkdir(exist_ok=True)
    
    file_path = templates_dir / "settings.html"
    file_path.write_text(content, encoding='utf-8')
    print("✅ templates/admin/settings.html ایجاد شد")

def update_main_urls():
    """بروزرسانی urls اصلی"""
    content = '''# platform_api/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

# تغییر عنوان admin
admin.site.site_header = "پنل مدیریت ChabokTool"
admin.site.site_title = "ChabokTool Admin"
admin.site.index_title = "خوش آمدید به پنل مدیریت"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('core/', include('core.urls')),
    path('api/accounts/', include('accounts.urls')),
    path('api/modules/', include('modules.urls')),
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
]

# Static files برای development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
'''
    
    file_path = Path("backend") / "platform_api" / "urls.py"
    file_path.write_text(content, encoding='utf-8')
    print("✅ platform_api/urls.py بروزرسانی شد")

def main():
    """اجرای اصلی"""
    create_core_models()
    create_core_admin()
    create_core_urls()
    create_core_views()
    create_settings_template()
    update_main_urls()
    
    print("\n🎉 پنل تنظیمات ایجاد شد!")
    print("🔄 دستورات بعدی:")
    print("1. python manage.py makemigrations")
    print("2. python manage.py migrate") 
    print("3. python manage.py runserver")
    print("4. برو /admin/ و settings را اضافه کن")
    
    input("\nبرای خروج Enter بزنید...")

if __name__ == "__main__":
    main()