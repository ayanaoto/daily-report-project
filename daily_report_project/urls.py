from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 1. 管理サイト用のURL
    path("admin/", admin.site.urls),

    # 2. ログイン/ログアウトなどの認証機能用のURL
    path("accounts/", include("django.contrib.auth.urls")),

    # 3. あなたが作成したアプリ (reports) のURL
    path("", include("reports.urls", namespace="reports")),
]

# 開発モードの場合に、ユーザーがアップロードしたファイル（メディアファイル）を配信するための設定
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)