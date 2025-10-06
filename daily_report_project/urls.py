from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LoginView, LogoutView
from reports import views as report_views

urlpatterns = [
    path("admin/", admin.site.urls),

    # 認証
    path("accounts/login/", LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
    path("accounts/", include("django.contrib.auth.urls")),

    # ← ここを 'reports/' で include（/reports/…, /reports/1/ でアクセス可能）
    path("reports/", include(("reports.urls", "reports"), namespace="reports")),

    # API
    path("api/voice-logs/", report_views.api_voice_logs, name="api_voice_logs"),
    path("api/tts/", report_views.api_tts, name="api_tts"),
]

# 開発時のみメディア/スタティック配信
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
