from pathlib import Path
import os

# ========== 基本 ==========
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-secret-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")

# ========== ブランド名 ==========
SITE_BRAND = "FieldNote"

# ========== アプリ ==========
INSTALLED_APPS = [
    # Jazzmin は admin より前に
    "jazzmin",

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # 業務アプリ
    "reports",
]

# ========== ミドルウェア ==========
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
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
        "DIRS": [BASE_DIR / "templates"],  # プロジェクト共通テンプレート
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # ブランド名を常時テンプレへ
                "reports.context_processors.site_brand",
            ],
        },
    },
]

WSGI_APPLICATION = "daily_report_project.wsgi.application"

# ========== DB ==========
DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("DB_NAME", BASE_DIR / "db.sqlite3"),
        "USER": os.environ.get("DB_USER", ""),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", ""),
        "PORT": os.environ.get("DB_PORT", ""),
    }
}

# ========== パスワードバリデータ ==========
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ========== i18n / 時刻 ==========
LANGUAGE_CODE = "ja"
TIME_ZONE = "Asia/Tokyo"
USE_I18N = True
USE_TZ = True

# ========== スタティック/メディア ==========
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ========== Django メッセージ ==========
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: "debug",
    messages.INFO: "info",
    messages.SUCCESS: "success",
    messages.WARNING: "warning",
    messages.ERROR: "danger",
}

# ========== ログ（必要に応じて簡易設定） ==========
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}

# ========== Jazzmin ==========

JAZZMIN_SETTINGS = {
    "site_title": SITE_BRAND,
    "site_header": SITE_BRAND,
    "site_brand": SITE_BRAND,
    "welcome_sign": f"{SITE_BRAND} 管理サイト",
    "copyright": f"© {SITE_BRAND}",
    # 上部メニューにメインサイト導線
    "topmenu_links": [
        {"name": "メインサイトへ", "url": "/", "new_tab": False, "permissions": []},
    ],
    # テーマ（好みで変更可: darkly / cyborg / flatly / minty など）
    "theme": "darkly",
    "show_ui_builder": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar": "navbar-dark",
    "theme": "darkly",
    "dark_mode_theme": "darkly",
}

# セキュリティ（本番は適宜調整）
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https") if os.environ.get("RENDER") else None
CSRF_TRUSTED_ORIGINS = os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if os.environ.get("CSRF_TRUSTED_ORIGINS") else []
