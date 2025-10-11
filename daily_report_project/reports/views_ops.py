from __future__ import annotations
import os, tempfile
from django.conf import settings
from django.http import JsonResponse
from django.db import connection

def health(request):
    checks = {}
    # DB
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        checks["db"] = True
    except Exception as e:
        checks["db"] = f"NG: {e}"

    # MEDIA_ROOT 書込
    try:
        mr = getattr(settings, "MEDIA_ROOT", None)
        if mr and os.path.isdir(mr):
            with tempfile.NamedTemporaryFile(dir=mr, delete=True) as f:
                f.write(b"ok")
        checks["media_rw"] = True
    except Exception as e:
        checks["media_rw"] = f"NG: {e}"

    # 必須/任意環境変数
    checks["AZURE_SPEECH_KEY"] = bool(getattr(settings, "AZURE_SPEECH_KEY", ""))
    checks["FIELDNOTE_API_TOKEN"] = bool(getattr(settings, "FIELDNOTE_API_TOKEN", ""))

    status = 200 if all(v is True or v for v in checks.values()) else 503
    return JsonResponse({"ok": status == 200, "checks": checks, "brand": getattr(settings, "SITE_BRAND", "FieldNote")}, status=status)
