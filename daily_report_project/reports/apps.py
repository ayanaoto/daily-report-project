# reports/apps.py
from django.apps import AppConfig

class ReportsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "reports"

    def ready(self):
        # シグナル登録
        from . import signals  # noqa: F401
