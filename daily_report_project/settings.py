# -*- coding: utf-8 -*-
"""
Django settings for daily_report_project.
"""

from pathlib import Path
import os
import dj_database_url  # Renderのデータベース設定に必要

# プロジェクトルート（…/daily_report_project）
BASE_DIR = Path(__file__).resolve().parent.parent

# .env をプロジェクト直下から明示読み込み
from dotenv import load_dotenv
load_dotenv(dotenv_path=BASE_DIR / ".env", override=False)

# ここから通常の設定
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key")

# Renderの本番環境では DEBUG=False になるように修正
DEBUG = os.getenv("DJANGO_DEBUG", "false").lower() == "true"

ALLOWED_HOSTS = [
    *[h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()],
] or ["127.0.0.1", "localhost"]

CSRF_TRUSTED_ORIGINS = [
    *[u.strip() for u in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if u.strip()],
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",  # WhiteNoiseをAdminより上に配置
    "django.contrib.staticfiles",
    "corsheaders",
    "reports",
    "voice_logs",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # WhiteNoiseのミドルウェア
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "daily_report_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "daily_report_project.wsgi.application"

# ▼▼▼▼▼ データベース設定をRender用に修正 ▼▼▼▼▼
DATABASES = {
    'default': dj_database_url.config(
        # ローカルでDATABASE_URLが設定されていない場合は、SQLiteを使用する
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}'
    )
}
# ▲▲▲▲▲ ここまで修正 ▲▲▲▲▲

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ja"
TIME_ZONE = "Asia/Tokyo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---- アプリ用環境変数 ----
FIELDNOTE_API_TOKEN = os.getenv("FIELDNOTE_API_TOKEN", "")
CORS_ALLOW_ALL_ORIGINS = True

AZURE_SPEECH_KEY = os.getenv('AZURE_SPEECH_KEY')
AZURE_SPEECH_REGION = os.getenv('AZURE_SPEECH_REGION')
AZURE_SPEECH_VOICE = os.getenv('AZURE_SPEECH_VOICE')

# ▼▼▼▼▼ ここから追記 ▼▼▼▼▼
# Renderのホスト名を自動でALLOWED_HOSTSに追加する
if external_host := os.getenv('RENDER_EXTERNAL_HOSTNAME'):
    ALLOWED_HOSTS.append(external_host)
# ▲▲▲▲▲ ここまで追記 ▲▲▲▲▲