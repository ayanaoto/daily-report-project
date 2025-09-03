# daily_report_project/settings.py

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# SECURITY WARNING: keep the secret key used in production secret!
# 将来インターネットに公開する際は、このキーを新しいものに置き換えてください。
SECRET_KEY = 'django-insecure-your-secret-key' # このキーはご自身のものに置き換えてください

# SECURITY WARNING: don't run with debug turned on in production!
# ★ デプロイ（公開）のため、DEBUGはFalseに設定
DEBUG = False

# ★ Render.comからのアクセスを許可
ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    # ★ 管理画面のデザインテーマ 'jazzmin' を一番上に追加
    'jazzmin',
    
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'reports', # reportsアプリ
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
        # プロジェクト直下の 'templates' フォルダを指定
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


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'ja'
TIME_ZONE = 'Asia/Tokyo'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'

# ★ `collectstatic`で集めるファイルの置き場所を定義
STATIC_ROOT = BASE_DIR / 'staticfiles'


# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ログイン・ログアウト後のリダイレクト先
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'


# Jazzminのデザイン設定
JAZZMIN_SETTINGS = {
    "site_title": "業務アプリ管理",
    "site_header": "業務アプリ",
    "site_brand": "業務アプリ",
    "welcome_sign": "ようこそ、業務アプリ管理画面へ",
    "copyright": "My Company",
    "theme": "darkly",
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