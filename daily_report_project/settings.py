from pathlib import Path
import os

# =========================================
# 基本
# =========================================
BASE_DIR = Path(__file__).resolve().parent.parent

# .env を読む（python-dotenv をインストールしている前提。無くても動作はする）
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env", override=False)
except Exception:
    pass

# セキュリティキー
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")  # 本番は必ず環境変数で

# デバッグ
DEBUG = os.getenv("DEBUG", "1") == "1"  # ローカルは 1、本番は 0 推奨

# ホスト/CSRF
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",") if os.getenv("ALLOWED_HOSTS") else ["*"]
CSRF_TRUSTED_ORIGINS = [
    os.getenv("CSRF_ORIGIN", "https://*.onrender.com")
]

# =========================================
# アプリ
# =========================================
INSTALLED_APPS = [
    # Django標準
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # アプリ
    "reports",
]

# =========================================
# ミドルウェア
# =========================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Whitenoise を有効化（STATIC配信）
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# =========================================
# URL / WSGI / ASGI
# =========================================
ROOT_URLCONF = "daily_report_project.urls"

WSGI_APPLICATION = "daily_report_project.wsgi.application"
ASGI_APPLICATION = "daily_report_project.asgi.application"

# =========================================
# テンプレート
# =========================================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # プロジェクト直下 templates/ も使う
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
# データベース
#   - 既定：SQLite（ローカル）
#   - DATABASE_URL があれば Postgres 等に自動切替（本番向け）
# =========================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    try:
        import dj_database_url
        DATABASES["default"] = dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    except Exception:
        # dj-database-url が無い/壊れてもローカルSQLiteで継続
        pass

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
USE_L10N = True
USE_TZ = True  # DB はUTC、表示は Asia/Tokyo

# =========================================
# 静的/メディア
#   - Whitenoiseで本番配信（Manifest + 圧縮）
#   - 開発では collectstatic なしでも動作可（推奨は実行）
# =========================================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"     # collectstatic の出力先（本番）
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

# Whitenoise のストレージ
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    }
}

# アップロードメディア（ローカル開発用）
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# =========================================
# 既定のAutoField
# =========================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =========================================
# メール（開発はコンソール）
# =========================================
if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# =========================================
# セキュアヘッダ（本番のみ軽く）
# =========================================
if not DEBUG:
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "1") == "1"
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    # Proxy環境でのIP/HTTPS判定（Render等）
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# =========================================
# ログ（最低限）
# =========================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}

# =========================================
# Azure Speech（任意：あなたの既存コードが読む想定）
# =========================================
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY", "")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION", "japaneast")
AZURE_SPEECH_VOICE = os.getenv("AZURE_SPEECH_VOICE", "ja-JP-NanamiNeural")

# =========================================
# その他（必要に応じて追加）
# 例）REST Framework, CORS, Cache など
# =========================================
# ======== Production minimal ========
import os, dj_database_url
DEBUG = os.getenv("DEBUG", "0") == "1"
ALLOWED_HOSTS = ["*"]
CSRF_TRUSTED_ORIGINS = [os.getenv("CSRF_ORIGIN","https://*.onrender.com")]

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
STORAGES = {"staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"}}

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
# ===================================
