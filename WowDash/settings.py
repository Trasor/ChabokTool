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
    # Apps
    'accounts',
    'keyword_research',
    'gap_analysis',
    'billing',
    'rank_tracker',
    # Third-party
    'channels',
    'defender',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'defender.middleware.FailedLoginMiddleware',  # محافظت از brute force
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
# برای sandbox از این merchant ID استفاده می‌شود
ZARINPAL_MERCHANT_ID = '00000000-0000-0000-0000-000000000000'
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

# ========================================
# 🔒 SECURITY SETTINGS - OWASP Compliant
# ========================================

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Password Hashing - استفاده از Argon2 (قوی‌ترین)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

# Session Security - 1 Hour Inactivity Timeout
SESSION_COOKIE_AGE = 3600  # 1 hour in seconds
SESSION_SAVE_EVERY_REQUEST = True  # برای refresh کردن session در هر request
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_SECURE = not DEBUG  # فقط HTTPS در production
SESSION_COOKIE_HTTPONLY = True  # جلوگیری از XSS
SESSION_COOKIE_SAMESITE = 'Lax'  # محافظت از CSRF

# CSRF Protection
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = False
CSRF_COOKIE_AGE = 31449600  # 1 year

# Security Headers (OWASP Recommended)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HTTPS Settings (فقط در production)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Django Defender Settings (Brute Force Protection)
DEFENDER_LOGIN_FAILURE_LIMIT = 5  # بعد از 5 بار تلاش ناموفق
DEFENDER_COOLOFF_TIME = 900  # 15 دقیقه مسدود (900 seconds)
DEFENDER_LOCKOUT_TEMPLATE = 'authentication/lockout.html'
DEFENDER_REDIS_URL = config('CELERY_BROKER_URL', default='redis://127.0.0.1:6379/0')
DEFENDER_STORE_ACCESS_ATTEMPTS = True
DEFENDER_USE_CELERY = False
DEFENDER_LOCK_OUT_BY_IP_AND_USERNAME = True

# Kavenegar SMS Configuration
KAVENEGAR_API_KEY = config('KAVENEGAR_API_KEY', default='')
KAVENEGAR_TEMPLATE = config('KAVENEGAR_TEMPLATE', default='verify')  # نام template برای OTP
KAVENEGAR_SENDER = config('KAVENEGAR_SENDER', default='')  # شماره ارسال‌کننده (اختیاری)

# reCAPTCHA Configuration
RECAPTCHA_SITE_KEY = config('RECAPTCHA_SITE_KEY', default='')
RECAPTCHA_SECRET_KEY = config('RECAPTCHA_SECRET_KEY', default='')
RECAPTCHA_VERIFY_URL = 'https://www.google.com/recaptcha/api/siteverify'

# Logging Configuration (برای نظارت امنیتی)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['file', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'accounts': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'defender': {
            'handlers': ['file', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}