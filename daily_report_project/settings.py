# daily_report_project/settings.py

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-your-secret-key' # このキーはご自身のものに置き換えてください
DEBUG = True
ALLOWED_HOSTS = []

# ★★★ ここからが修正箇所です ★★★
INSTALLED_APPS = [
    'jazzmin',  # jazzminを一番上に配置
    
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

LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# ★★★ Jazzminのデザイン設定 ★★★
JAZZMIN_SETTINGS = {
    "site_title": "業務アプリ管理",
    "site_header": "業務アプリ",
    "site_brand": "業務アプリ",
    "welcome_sign": "ようこそ、業務アプリ管理画面へ",
    "copyright": "My Company",
    "theme": "darkly", # ダークテーマを適用
    
    # ★ メインサイトへのリンクを有効化
    "show_ui_builder": True,

    "ui_tweaks": {
        "sidebar_fixed": True,
        "navbar_fixed": True,
    },
    "icons": {
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "reports.Customer": "fas fa-building",
        "reports.Deal": "fas fa-handshake",
        "reports.Report": "fas fa-file-alt",
        "reports.WorkLog": "fas fa-clock",
        "reports.RequiredItem": "fas fa-check-square",
        "reports.DealStatusLog": "fas fa-history",
        "reports.TroubleshootingReport": "fas fa-wrench",
    },
}