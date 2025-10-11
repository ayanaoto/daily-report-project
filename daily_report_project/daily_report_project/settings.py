# daily_report_project/settings.py  —— 省略なし・そのまま置き換え

from pathlib import Path
import os

# ===== .env ロード =====
#   プロジェクト直下 (manage.py と同階層) の .env を読み込みます
#   例: FIELDNOTE_API_TOKEN=devtoken
try:
    from dotenv import load_dotenv  # pip install python-dotenv
    _BASE_DIR = Path(__file__).resolve().parent.parent
    load_dotenv(_BASE_DIR / ".env")
except Exception:
    _BASE_DIR = Path(__file__).resolve().parent.parent

BASE_DIR = _BASE_DIR

# ===== セキュリティ / デバッグ =====
SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-key")
DEBUG = os.getenv("DEBUG", "1") == "1"

# ===== 許可ホスト / CSRF =====
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
ext_host = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if ext_host:
    ALLOWED_HOSTS.append(ext_host)

CSRF_TRUSTED_ORIGINS = []
ext_url = os.getenv("RENDER_EXTERNAL_URL")
if ext_url:
    CSRF_TRUSTED_ORIGINS.append(ext_url)

# ===== アプリ =====
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",

    "corsheaders",

    # あなたのアプリ
    "reports.apps.ReportsConfig",
    # "voice_logs",  # 使っていなければコメントのまま
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
ASGI_APPLICATION = "daily_report_project.asgi.application"

# ===== DB =====
# まずは SQLite（Render 等では DATABASE_URL で上書き）
try:
    import dj_database_url  # pip install dj-database-url
    DATABASES = {
        "default": dj_database_url.config(
            default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
            conn_max_age=600,
        )
    }
except Exception:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ===== 認証/ログイン =====
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# ===== i18n / tz =====
LANGUAGE_CODE = "ja"
TIME_ZONE = "Asia/Tokyo"
USE_I18N = True
USE_TZ = True

# ===== 静的/メディア =====
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

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ===== CORS（開発用に全許可）=====
CORS_ALLOW_ALL_ORIGINS = True

# ===== キャッシュ（Idempotency-Key 等に使用可）=====
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "fieldnote-cache",
    }
}

# ======== ここが重要：APIトークン定義 ========
# ローカル開発では .env が無くても動くように、DEBUG=1 の時は 'devtoken' を既定値に。
FIELDNOTE_API_TOKEN = os.getenv(
    "FIELDNOTE_API_TOKEN",
    "devtoken" if DEBUG else ""
)

# ===== Azure（必要なら）=====
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")
AZURE_SPEECH_VOICE = os.getenv("AZURE_SPEECH_VOICE")
