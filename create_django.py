# create_django.py - ایجاد فایل‌های Django
import os
from pathlib import Path

print("🔧 ایجاد فایل‌های Django...")
print("=" * 40)

def create_manage_py():
    """ایجاد فایل manage.py"""
    content = '''#!/usr/bin/env python
import os
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'platform_api.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
'''
    
    file_path = Path("backend") / "manage.py"
    file_path.write_text(content, encoding='utf-8')
    print("✅ manage.py ایجاد شد")

def create_settings():
    """ایجاد فایل settings.py"""
    content = '''# platform_api/settings.py
import os
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = 'chaboktool-secret-key-change-later'
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# Brand settings (قابل تغییر از پنل مدیریت)
BRAND_NAME = 'ChabokTool'
BRAND_DOMAIN = 'chaboktool.com'

# Applications
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
]

LOCAL_APPS = [
    'core',
    'accounts',
    'modules',
    'payments',
    'licenses',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Middleware
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'platform_api.urls'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Database (SQLite برای سادگی)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Internationalization
LANGUAGE_CODE = 'fa'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'PAGE_SIZE': 20
}

# CORS
CORS_ALLOW_ALL_ORIGINS = True

# Default primary key
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# تنظیمات قابل تغییر از پنل مدیریت
EDITABLE_SETTINGS = {
    'ZARINPAL_MERCHANT_ID': '',
    'ZARINPAL_SANDBOX': True,
    'SMS_API_KEY': '',
    'SMS_SENDER': '',
    'EMAIL_HOST_USER': '',
    'EMAIL_HOST_PASSWORD': '',
    'BRAND_LOGO': '',
    'SUPPORT_EMAIL': 'support@chaboktool.com',
    'SUPPORT_PHONE': '',
}
'''
    
    settings_dir = Path("backend") / "platform_api"
    settings_file = settings_dir / "settings.py"
    settings_file.write_text(content, encoding='utf-8')
    print("✅ settings.py ایجاد شد")

def create_urls():
    """ایجاد فایل urls.py"""
    content = '''# platform_api/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    path('api/modules/', include('modules.urls')),
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
]

# Static files برای development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
'''
    
    urls_file = Path("backend") / "platform_api" / "urls.py"
    urls_file.write_text(content, encoding='utf-8')
    print("✅ urls.py ایجاد شد")

def create_wsgi():
    """ایجاد فایل wsgi.py"""
    content = '''import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'platform_api.settings')
application = get_wsgi_application()
'''
    
    wsgi_file = Path("backend") / "platform_api" / "wsgi.py"
    wsgi_file.write_text(content, encoding='utf-8')
    print("✅ wsgi.py ایجاد شد")

def main():
    """اجرای اصلی"""
    create_manage_py()
    create_settings()
    create_urls()
    create_wsgi()
    
    print("\n🎉 فایل‌های Django ایجاد شدند!")
    print("🔄 مرحله بعد: نصب Django")
    print("\nدستور بعدی: cd backend")
    print("سپس: pip install -r requirements.txt")
    
    input("\nبرای خروج Enter بزنید...")

if __name__ == "__main__":
    main()