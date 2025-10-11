from django.urls import path
from .views import api_voice_logs, api_tts  # TTS使わなければ api_voice_logs だけ使う

urlpatterns = [
    path("voice-logs/", api_voice_logs, name="api_voice_logs"),
    # path("tts/", api_tts, name="api_tts"),  # 使うときだけ有効化
]
