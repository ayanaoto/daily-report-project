# reports/context_processors.py

# Pylance が django.conf を解決できない環境向けのフォールバック。
# 実行時には本物の settings が使われ、静的解析だけ静かにします。
try:
    from django.conf import settings  # type: ignore[import]
except Exception:  # 解析専用のダミー（実行時には通らない想定）
    class _DummySettings:
        SITE_BRAND = "FieldNote"
    settings = _DummySettings()  # type: ignore[assignment]

def site_brand(request):
    """
    全テンプレートにブランド名を渡す。
    例: {{ SITE_BRAND }} で参照可能。
    """
    return {
        "SITE_BRAND": getattr(settings, "SITE_BRAND", "FieldNote"),
    }
