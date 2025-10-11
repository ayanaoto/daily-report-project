from django.contrib import admin
from .models import (
    Customer,
    Deal,
    Report,
    Troubleshooting,
    RequiredItem
)

# 作成したモデルを管理サイトに登録
admin.site.register(Customer)
admin.site.register(Deal)
admin.site.register(Report)
admin.site.register(Troubleshooting)
admin.site.register(RequiredItem)