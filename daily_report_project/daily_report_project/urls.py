from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import RedirectView
from reports import views as report_views

urlpatterns = [
    path("admin/", admin.site.urls),

    # ルート → /reports/ にリダイレクト
    path("", RedirectView.as_view(pattern_name="reports:report_list", permanent=False)),

    # 認証
    path("accounts/login/", LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
    path("accounts/", include("django.contrib.auth.urls")),

    # サインアップ（テンプレが {% url 'signup' %} を参照しても解決できるように）
    path("signup/", report_views.SignUpView.as_view(), name="signup"),

    # アプリ本体（/reports/...）
    path("reports/", include(("reports.urls", "reports"), namespace="reports")),

    # API
    path("api/voice-logs/", report_views.api_voice_logs, name="api_voice_logs"),
    path("api/tts/", report_views.api_tts, name="api_tts"),
]

# 開発時のみメディア配信（STATIC は WhiteNoise に任せる）
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
