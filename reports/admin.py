from django.contrib import admin
from .models import (
    Customer, Deal, Report, WorkLog, 
    RequiredItem, DealStatusLog, TroubleshootingReport
)

# --- ここからがカスタマイズです ---

class DealStatusLogInline(admin.TabularInline):
    """案件モデルの編集画面内で、ステータス履歴を一緒に編集できるようにする設定"""
    model = DealStatusLog
    extra = 1
    readonly_fields = ('timestamp',)

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'account_manager', 'created_at')
    search_fields = ('customer_name',)
    list_filter = ('account_manager',)

@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ('deal_name', 'customer', 'person_in_charge', 'status', 'amount', 'created_at')
    list_filter = ('status', 'person_in_charge', 'customer')
    search_fields = ('deal_name', 'customer__customer_name')
    inlines = [DealStatusLogInline]

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'customer', 'author', 'created_at')
    search_fields = ('title', 'content')
    list_filter = ('author', 'customer')

@admin.register(WorkLog)
class WorkLogAdmin(admin.ModelAdmin):
    list_display = ('work_date', 'customer', 'deal', 'author', 'progress_status')
    list_filter = ('progress_status', 'author', 'customer')
    search_fields = ('deal__deal_name', 'remarks', 'repair_needed')
    date_hierarchy = 'work_date'

@admin.register(RequiredItem)
# ★★★ ここが修正箇所です ★★★
class RequiredItemAdmin(admin.ModelAdmin):
    list_display = ("title", "deal", "is_done", "completed_at")
    list_filter = ("is_done", "deal__person_in_charge")
    search_fields = ("title", "deal__deal_name")
    autocomplete_fields = ['deal']

@admin.register(TroubleshootingReport)
class TroubleshootingReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'author', 'updated_at')
    search_fields = ('title', 'location', 'symptom', 'solution', 'keywords')
    list_filter = ('author',)
    date_hierarchy = 'created_at'

# DealStatusLogはDealのページで一緒に編集するため、単独の登録は不要にする
# もし単独でも表示したい場合は、以下のコメントを外してください
# @admin.register(DealStatusLog)
# class DealStatusLogAdmin(admin.ModelAdmin):
#     list_display = ("deal", "status", "timestamp")
#     list_filter = ("status", "deal__person_in_charge")
#     search_fields = ("deal__deal_name",)