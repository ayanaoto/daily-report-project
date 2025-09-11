from pathlib import Path
import os
from django.contrib.messages import constants as messages

# ========== 基本設定 ==========
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-secret-change-me-for-development")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")


# ========== ブランド名 ==========
SITE_BRAND = "FieldNote"

# ========== アプリケーション定義 ==========
INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Whitenoise: 静的ファイル配信のために追加
    "whitenoise.runserver_nostatic",
    # 自作アプリ
    "reports",
]

# ========== ミドルウェア ==========
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Whitenoise: 静的ファイル配信のために追加
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "daily_report_project.urls"

# ========== テンプレート ==========
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
                "reports.context_processors.site_brand",
            ],
        },
    },
]

WSGI_APPLICATION = "daily_report_project.wsgi.application"

# ========== データベース ==========
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ========== パスワードバリデータ ==========
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ========== 国際化 ==========
LANGUAGE_CODE = "ja"
TIME_ZONE = "Asia/Tokyo"
USE_I18N = True
USE_TZ = True

# ========== 静的ファイル・メディアファイル ==========
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# Whitenoise用の設定
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# ========== Django メッセージ ==========
MESSAGE_TAGS = {
    messages.DEBUG: "debug",
    messages.INFO: "info",
    messages.SUCCESS: "success",
    messages.WARNING: "warning",
    messages.ERROR: "danger",
}

# ========== Jazzmin ==========
JAZZMIN_SETTINGS = {
    "site_title": SITE_BRAND,
    "site_header": SITE_BRAND,
    "site_brand": SITE_BRAND,
    "welcome_sign": f"{SITE_BRAND} 管理サイト",
    "copyright": f"© {SITE_BRAND}",
    "topmenu_links": [
        {"name": "メインサイトへ", "url": "/", "new_tab": False, "permissions": []},
    ],
    "theme": "darkly",
    "show_ui_builder": False,
}
JAZZMIN_UI_TWEAKS = {
    "navbar": "navbar-dark",
    "theme": "darkly",
    "dark_mode_theme": "darkly",
}

# ========== 本番環境向けセキュリティ設定 ==========
# RenderなどのPaaSでHTTPS通信を正しく認識させるための設定
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# CSRF対策で、許可するオリジンを環境変数から読み込む
CSRF_TRUSTED_ORIGINS = os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if os.environ.get("CSRF_TRUSTED_ORIGINS") else []