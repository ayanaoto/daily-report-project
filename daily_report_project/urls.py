# daily_report_project/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# reportsアプリからサインアップ用のビューをインポートします
from reports import views as reports_views

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # Django標準の認証URL（ログイン、ログアウト等）
    path("accounts/", include("django.contrib.auth.urls")),
    # 新規登録(signup)用のURL
    path("accounts/signup/", reports_views.SignUpView.as_view(), name="signup"),

    # ▼▼▼【ここが最重要】▼▼▼
    # "/" や "/reports/" へのアクセスはすべて reports.urls に任せる
    # これで /reports/voice-logger/ のようなURLが正しく解決されるようになります。
    path("", include("reports.urls")), 
    # ▲▲▲【ここまで】▲▲▲
]

# 開発環境でメディアファイルを配信するための設定
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)