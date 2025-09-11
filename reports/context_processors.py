# reports/context_processors.py

from django.conf import settings

def site_brand(request):
    """
    全テンプレートで {{ site_brand }} を使えるようにする。
    settings.SITE_BRAND が無ければ "FieldNote"。
    """
    return {"site_brand": getattr(settings, "SITE_BRAND", "FieldNote")}