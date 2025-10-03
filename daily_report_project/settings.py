from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url

# =====================================================================
# 基本セットアップ
# =====================================================================

# .env を読み込み（ローカル開発時に使用。本番 Render では環境変数をダッシュボードで設定）
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# シークレットキー（本番は必ず環境変数で上書き）
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key-change-me")

# DEBUG（既定: false。本番安全側）
DEBUG = os.getenv("DJANGO_DEBUG", "false").lower() in ("1", "true", "yes", "on")

# 許可ホスト：カンマ区切り。未指定なら開発用にワイルドカード
if os.getenv("ALLOWED_HOSTS"):
    ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()]
else:
    ALLOWED_HOSTS = ["*"]

# CSRF信頼オリジン（https://xxxxx.onrender.com のように https で）
_csrf = os.getenv("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf.split(",") if o.strip()]

# CORS（必要に応じて。未設定なら空）
_cors = os.getenv("CORS_ALLOWED_ORIGINS", "")
CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors.split(",") if o.strip()]
CORS_ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() in ("1", "true", "yes", "on")

# =====================================================================
# アプリケーション定義
# =====================================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # サードパーティ
    "corsheaders",  # CORS 対応

    # プロジェクトアプリ
    "voice_logs",
    "reports",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    # CORS は CommonMiddleware より前、できれば先頭付近
    "corsheaders.middleware.CorsMiddleware",

    # WhiteNoise（静的ファイル配信）
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
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
        "DIRS": [BASE_DIR / "templates"],  # 任意: プロジェクト直下 templates/
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

# =====================================================================
# データベース
# =====================================================================

# 環境に DATABASE_URL があれば（本番/Postgres）→ dj_database_url を使う
# それ以外（ローカル/SQLite）→ 素の辞書で設定（sslmode を付けない）
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=os.getenv("DB_SSL_REQUIRE", "true").lower() in ("1", "true", "yes", "on"),
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# =====================================================================
# 言語・時刻
# =====================================================================

LANGUAGE_CODE = "ja"
TIME_ZONE = "Asia/Tokyo"
USE_I18N = True
USE_TZ = True  # DBはUTC、表示はTIME_ZONE

# =====================================================================
# 静的/メディア
# =====================================================================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# WhiteNoise：圧縮＋ハッシュ付きファイルを配信
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
# Render の Persistent Disk を /var/media にマウントして使う想定
MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", "/var/media"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =====================================================================
# セキュリティ（本番向け）
# =====================================================================

if not DEBUG:
    # 逆プロキシ（Render）経由の https を信頼
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True

    # Cookie の secure
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # HSTS（段階的導入推奨）
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "86400"))  # 1日
    SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "false").lower() in ("1", "true", "yes", "on")
    SECURE_HSTS_PRELOAD = os.getenv("SECURE_HSTS_PRELOAD", "false").lower() in ("1", "true", "yes", "on")

# =====================================================================
# ロギング（簡易）
# =====================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "[{levelname}] {asctime} {name}: {message}", "style": "{"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
}

# =====================================================================
# 外部サービス（Azure Speech / その他）
# =====================================================================

AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY", "")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION", "")
AZURE_SPEECH_VOICE = os.getenv("AZURE_SPEECH_VOICE", "ja-JP-NanamiNeural")

# 外部サービス/トークン類（追加）
FIELDNOTE_API_TOKEN = os.getenv("FIELDNOTE_API_TOKEN", "")


# 必要なら他設定値もここに集約
# 例:
# TTS_TIMEOUT = int(os.getenv("TTS_TIMEOUT", "15"))
# API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "60/min")
