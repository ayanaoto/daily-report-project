from django.contrib import admin
from .models import VoiceLog

@admin.register(VoiceLog)
class VoiceLogAdmin(admin.ModelAdmin):
    list_display = ("id", "intent", "text", "ts", "created_at")
    search_fields = ("text", "intent", "customer")
    list_filter = ("intent", "created_at")
    ordering = ("-created_at", "-id")
