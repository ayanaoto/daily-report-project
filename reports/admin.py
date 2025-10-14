from django.contrib import admin
# ▼▼▼【ここを修正】▼▼▼
# .models から RequiredMaterial をインポートするリストに追加します
from .models import (
    Report, 
    RequiredItem, 
    Customer, 
    Deal, 
    Troubleshooting, 
    RequiredMaterial
)
# ▲▲▲【ここまで】▲▲▲


# 作成したモデルを管理サイトに登録
admin.site.register(Customer)
admin.site.register(Deal)
admin.site.register(Report)
admin.site.register(Troubleshooting)
admin.site.register(RequiredItem)
admin.site.register(RequiredMaterial) # この行を追加