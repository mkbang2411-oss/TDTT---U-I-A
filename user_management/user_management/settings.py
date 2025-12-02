from pathlib import Path

import os

from dotenv import load_dotenv 

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
# tìm và tải tệp .env ở thư mục gốc
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/


SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'corsheaders',

    # Django mặc định
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Allauth
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google', # Bật Google

    # App
    'accounts',
]
SITE_ID = 1

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'user_management.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,   
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'user_management.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR.parent, 'frontend'),
]

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTHENTICATION_BACKENDS = [
    # Django mặc định
    'django.contrib.auth.backends.ModelBackend',

    # Django Allauth
    'allauth.account.auth_backends.AuthenticationBackend',
]




CORS_ALLOW_CREDENTIALS = True

# Cho phép trình duyệt gửi các header này
CORS_ALLOW_HEADERS = [
    'content-type',
    'x-csrftoken',  # Cho phép header CSRF
    'x-requested-with',
]

# Cấu hình hành vi đăng nhập
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Cấu hình email
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = 'none'

# 1. Tắt tính năng tự động đăng nhập sau khi đăng ký
ACCOUNT_LOGIN_ON_SIGNUP = False

# 2. Chỉ định URL để chuyển hướng đến SAU KHI ĐĂNG KÝ
ACCOUNT_SIGNUP_REDIRECT_URL = '/accounts/login/'

# Bỏ qua trang xác nhận khi đăng nhập bằng social
SOCIALACCOUNT_LOGIN_ON_GET = True

# Tự động tạo tài khoản cho lần đăng nhập Google đầu tiên
SOCIALACCOUNT_AUTO_SIGNUP = True

# Gắn custom adapter để kiểm soát flow khi email đã tồn tại
SOCIALACCOUNT_ADAPTER = 'accounts.adapters.CustomSocialAccountAdapter'

# Gắn custom account adapter để kiểm tra OTP trước khi đăng ký
ACCOUNT_ADAPTER = 'accounts.adapters.CustomAccountAdapter'

# URL để truy cập ảnh trên trình duyệt
MEDIA_URL = '/media/'

# Đường dẫn thư mục thực tế trên máy tính để lưu file
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ===================================================
# ✅ PRODUCTION SETTINGS - CLOUDFLARE TUNNEL
# ===================================================

# Cho phép Nginx làm reverse proxy
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Tin tưởng Nginx header
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# Session & Cookie settings
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False  # ✅ Đổi thành False để test local + tunnel

# CSRF settings
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SECURE = False  # ✅ Đổi thành False để test

# ✅ CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS = [
    'http://localhost',
    'http://127.0.0.1',
    'http://localhost:5000',
    'http://127.0.0.1:5000',
    'https://raising-crm-neighbors-dave.trycloudflare.com',
    'https://resolve-shanghai-hanging-critical.trycloudflare.com',
    'https://annex-occurrence-hobbies-rio.trycloudflare.com'
]

# ✅ CORS settings
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    'http://localhost',
    'http://127.0.0.1',
    'http://localhost:5000',
    'http://127.0.0.1:5000',
    'https://raising-crm-neighbors-dave.trycloudflare.com',
    'https://resolve-shanghai-hanging-critical.trycloudflare.com',
    'https://annex-occurrence-hobbies-rio.trycloudflare.com',
]

CORS_ALLOW_HEADERS = [
    'content-type',
    'x-csrftoken',
    'x-requested-with',
    'authorization',
]

# ==========================================
# 📧 CẤU HÌNH EMAIL SMTP (GMAIL)
# ==========================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')  # Email của bạn
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')  # App Password
DEFAULT_FROM_EMAIL = os.environ.get('EMAIL_HOST_USER')

# Thời gian hết hạn OTP (phút)
OTP_EXPIRY_MINUTES = 5

# Session timeout cho OTP verification
SESSION_COOKIE_AGE = 1800  # 30 phút
# OTP SESSION_TIMEOUT_MINUTES = 30  # Timeout cho session verify OTP

# Security settings
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# Cache configuration for rate limiting
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}