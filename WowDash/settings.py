"""
Django settings for WowDash project.
"""

from pathlib import Path
from decouple import config
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = ['dncbot.ir', '178.239.147.121', 'www.dncbot.ir', '*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'keyword_research',
    'gap_analysis',
    'billing',
    'channels',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'WowDash.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR, "templates"],
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

WSGI_APPLICATION = 'WowDash.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'fa-ir'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'static_root'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ✅ API Tokens (داینامیک از .env)
APIFY_TOKEN = config('APIFY_TOKEN', default='')
SERPER_API_KEY = config('SERPER_API_KEY', default='')

# ✅ انتخاب SERP API Provider
# گزینه‌ها: 'serper' یا 'apify'
SERP_PROVIDER = config('SERP_PROVIDER', default='serper')

# Celery Configuration
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = None
CELERY_TASK_SOFT_TIME_LIMIT = None
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# ✅ Queue اختصاصی ChabokTool
CELERY_TASK_DEFAULT_QUEUE = 'chaboktool_queue'
CELERY_TASK_DEFAULT_EXCHANGE = 'chaboktool_exchange'
CELERY_TASK_DEFAULT_ROUTING_KEY = 'chaboktool'

# Login Settings
LOGIN_URL = 'signin'
LOGIN_REDIRECT_URL = 'index'
LOGOUT_REDIRECT_URL = 'signin'

# ZarinPal Configuration
ZARINPAL_MERCHANT_ID = 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
ZARINPAL_SANDBOX = True
ZARINPAL_CALLBACK_URL = 'https://dncbot.ir/billing/verify/'

# ✅ AI Configuration
AI_ENABLED = config('AI_ENABLED', default=False, cast=bool)
AI_PROVIDER = config('AI_PROVIDER', default='gemini')

# API Keys
GEMINI_API_KEY = config('GEMINI_API_KEY', default='')
OPENAI_API_KEY = config('OPENAI_API_KEY', default='')
ANTHROPIC_API_KEY = config('ANTHROPIC_API_KEY', default='')

# Rate Limiting
AI_RATE_LIMIT_DELAY = config('AI_RATE_LIMIT_DELAY', default=4, cast=int)

# ✅ Redis Configuration (اضافه کن)
REDIS_HOST = config('REDIS_HOST', default='localhost')
REDIS_PORT = config('REDIS_PORT', default=6379, cast=int)
REDIS_DB = config('REDIS_DB', default=0, cast=int)

ASGI_APPLICATION = 'WowDash.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(config('REDIS_HOST', default='localhost'), config('REDIS_PORT', default=6379, cast=int))],
        },
    },
}