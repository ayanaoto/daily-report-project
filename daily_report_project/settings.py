# daily_report_project/settings.py

from pathlib import Path
import os
import dj_database_url

# =========================================
# 基本設定
# =========================================
BASE_DIR = Path(__file__).resolve().parent.parent

# .env を読む（ローカル開発用）
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

# セキュリティキー（本番では必ずRenderの環境変数で設定）
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-insecure")

# デバッグモード（本番ではRenderの環境変数で DEBUG=0 を設定）
DEBUG = os.getenv("DEBUG", "1") == "1"

# ホスト設定
# 【重要修正】ローカルホストに加えて、Renderの公開ホスト名を環境変数から自動で追加する
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# CSRF設定（Renderのドメインを許可）
CSRF_TRUSTED_ORIGINS = []
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")


# =========================================
# アプリケーション定義
# =========================================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "reports.apps.ReportsConfig",
    "corsheaders",
    "widget_tweaks",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "daily_report_project.urls"
WSGI_APPLICATION = "daily_report_project.wsgi.application"
ASGI_APPLICATION = "daily_report_project.asgi.application"

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

# =========================================
# データベース設定
# =========================================
DATABASES = {
    "default": dj_database_url.config(
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
        conn_max_age=600,
    )
}

# =========================================
# 認証/ログイン
# =========================================
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# =========================================
# 国際化
# =========================================
LANGUAGE_CODE = "ja"
TIME_ZONE = "Asia/Tokyo"
USE_I18N = True
USE_TZ = True

# =========================================
# 静的ファイル & メディアファイル
# =========================================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    }
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# =========================================
# キャッシュ設定 (Idempotency-Keyなどで使用)
# =========================================
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}

# =========================================
# その他
# =========================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
CORS_ALLOW_ALL_ORIGINS = True

# アプリケーション固有の環境変数
FIELDNOTE_API_TOKEN = os.getenv("FIELDNOTE_API_TOKEN")
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")
AZURE_SPEECH_VOICE = os.getenv("AZURE_SPEECH_VOICE")