# platform_api/settings.py
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

# Auth settings
AUTH_USER_MODEL = 'accounts.User'

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
