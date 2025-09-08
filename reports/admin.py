# reports/admin.py

from django.contrib import admin
from .models import (
    Customer, Deal, Report, 
    RequiredItem, DealStatusLog, TroubleshootingReport
)

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'account_manager', 'created_at')
    search_fields = ('customer_name',)
    list_filter = ('account_manager',)

@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ('deal_name', 'customer')
    search_fields = ('deal_name', 'customer__customer_name')

# ★★★ ここからが修正箇所です ★★★
@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    # list_displayから存在しない'title'を削除し、新しい項目に入れ替え
    list_display = ('work_date', 'customer_name', 'deal_name', 'progress_status', 'author')
    # search_fieldsからも'title'を削除
    search_fields = ('customer_name', 'deal_name', 'work_details')
    list_filter = ('author', 'work_date', 'progress_status')
    date_hierarchy = 'work_date'
# ★★★ ここまでが修正箇所です ★★★

@admin.register(RequiredItem)
class RequiredItemAdmin(admin.ModelAdmin):
    list_display = ("title", "deal", "is_done", "completed_at")
    list_filter = ("is_done",)
    search_fields = ("title", "deal__deal_name")
    autocomplete_fields = ['deal']

@admin.register(TroubleshootingReport)
class TroubleshootingReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'author', 'updated_at')
    search_fields = ('title', 'location', 'work_details', 'symptom', 'solution', 'keywords')
    list_filter = ('author',)
    date_hierarchy = 'created_at'

# DealStatusLogはDealのページで一緒に編集するため、単独の登録は不要にする
# @admin.register(DealStatusLog)
# class DealStatusLogAdmin(admin.ModelAdmin):
#     ...