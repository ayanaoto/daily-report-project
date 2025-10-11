# daily_report_project/urls.py

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

# reportsアプリからビューをインポート
from reports import views as report_views

urlpatterns = [
    path("admin/", admin.site.urls),

    # サインアップページのURL
    path("accounts/signup/", report_views.SignUpView.as_view(), name="signup"),

    # Django標準の認証URL（ログイン、ログアウトなど）
    path("accounts/", include("django.contrib.auth.urls")),

    # トップページは /reports/ へリダイレクト
    path("", RedirectView.as_view(url="/reports/", permanent=False)),

    # reportsアプリのURL
    path("reports/", include("reports.urls")),

    # ▼▼▼ API用のURLをここに追加 ▼▼▼
    path("api/voice-logs/", report_views.api_voice_logs, name="api_voice_logs"),
    path("api/tts/", report_views.api_tts, name="api_tts"),
]