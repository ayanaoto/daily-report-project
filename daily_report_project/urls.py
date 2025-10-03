from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.contrib import admin


# 追加: reports.views を直接 import（TTS API 用）
from reports import views as report_views

from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path("admin/", admin.site.urls),

    # 既存: Voice Logs API
    path("api/", include("voice_logs.urls")),  # ← /api/voice-logs/ が有効になる

    # 追加: TTS 関連 API を直下にマッピング
    path("api/tts/", report_views.api_tts, name="api_tts"),
    path("api/tts/save/", report_views.tts_save_api, name="api_tts_save"),
    path("api/envcheck", report_views.api_envcheck, name="api_envcheck"),
    path("api/voices", report_views.api_voices, name="api_voices"),

    # ログイン/ログアウト（ログインだけ自前テンプレ）
    path("accounts/login/", LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),

    # 残りの認証系（password_reset など）はDjango標準をそのまま使用
    path("accounts/", include("django.contrib.auth.urls")),

    # アプリ本体
    path("", include(("reports.urls", "reports"), namespace="reports")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
