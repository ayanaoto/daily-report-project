# daily_report_project/settings.py

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-your-secret-key' # このキーはご自身のものに置き換えてください

DEBUG = True
ALLOWED_HOSTS = ['*']

# ★★★ ここからが追記箇所 ★★★
# onrender.comからの接続を信頼する設定
CSRF_TRUSTED_ORIGINS = ['https://*.onrender.com']
# ★★★ ここまでが追記箇所 ★★★

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'reports',
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

ROOT_URLCONF = 'daily_report_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'daily_report_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

LANGUAGE_CODE = 'ja'
TIME_ZONE = 'Asia/Tokyo'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'
CSRF_TRUSTED_ORIGINS = ['https://*.onrender.com']

# ★★★ ここからが修正箇所です ★★★
JAZZMIN_SETTINGS = {
    "site_title": "FieldNote Admin",
    "site_header": "FieldNote",
    "site_brand": "FieldNote",
    "welcome_sign": "FieldNote へようこそ",
    "copyright": "My Company",
    "theme": "darkly",
    "ui_tweaks": { "sidebar_fixed": True, "navbar_fixed": True },
    "icons": {
        "auth.user": "fas fa-user", "auth.Group": "fas fa-users",
        "reports.Customer": "fas fa-building", "reports.Deal": "fas fa-handshake",
        "reports.Report": "fas fa-file-alt", "reports.RequiredItem": "fas fa-check-square",
        "reports.DealStatusLog": "fas fa-history", "reports.TroubleshootingReport": "fas fa-wrench",
    },
}