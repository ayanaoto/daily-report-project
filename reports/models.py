from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import timedelta

class Customer(models.Model):
    customer_name = models.CharField("顧客名", max_length=100)
    account_manager = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="営業担当")
    created_at = models.DateTimeField("作成日時", default=timezone.now)
    def __str__(self): return self.customer_name

class Deal(models.Model):
    deal_name = models.CharField("案件名", max_length=200)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="顧客")
    def __str__(self): return self.deal_name

class Report(models.Model):
    """日報モデル"""
    PROGRESS_CHOICES = [
        ('not_started', '未着手'),
        ('in_progress', '作業中'),
        ('completed', '完了'),
    ]
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="報告者")
    customer_name = models.CharField("場所・顧客名", max_length=200)
    deal_name = models.CharField("案件名", max_length=200, blank=True)
    work_date = models.DateField("作業日")
    
    # ★★★ ここからが修正箇所 ★★★
    progress_status = models.CharField("進捗", max_length=20, choices=PROGRESS_CHOICES, default='in_progress')
    work_hours = models.DurationField("作業時間", default=timedelta)
    # ★★★ ここまでが修正箇所 ★★★

    work_details = models.TextField("【最重要】今日の作業内容")
    remarks = models.TextField("所感・連絡事項など", blank=True)
    attachment = models.FileField("添付ファイル", upload_to='attachments/', blank=True, null=True)
    created_at = models.DateTimeField("作成日時", default=timezone.now)

    class Meta:
        ordering = ['-work_date']

    def __str__(self):
        return f"{self.work_date} - {self.customer_name}"
    
    def get_absolute_url(self):
        return reverse('report_detail', kwargs={'pk': self.pk})

# ... (以降の RequiredItem, DealStatusLog, TroubleshootingReport モデルは変更なし)
class RequiredItem(models.Model):
    title = models.CharField("項目", max_length=200)
    deal = models.ForeignKey(Deal, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="関連案件", related_name="required_items")
    is_done = models.BooleanField("完了", default=False)
    completed_at = models.DateTimeField("完了日時", null=True, blank=True)
    created_at = models.DateTimeField("作成日時", default=timezone.now)
    class Meta: verbose_name = "必要物品"; verbose_name_plural = "必要物品"; ordering = ["is_done", "deal__deal_name", "title"]
    def __str__(self): return f"{self.title} ({'済' if self.is_done else '未'})"
    def mark_toggle(self): self.is_done = not self.is_done; self.completed_at = timezone.now() if self.is_done else None; self.save(update_fields=["is_done", "completed_at"])

class DealStatusLog(models.Model):
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name="status_logs", verbose_name="案件")
    status = models.CharField("ステータス", max_length=50)
    timestamp = models.DateTimeField("変更日時", default=timezone.now)
    class Meta: verbose_name = "案件ステータス履歴"; verbose_name_plural = "案件ステータス履歴"; ordering = ["deal", "timestamp"]
    def __str__(self): return f"{self.deal.deal_name} -> {self.status} ({self.timestamp.strftime('%Y-%m-%d')})"

class TroubleshootingReport(models.Model):
    title = models.CharField("タイトル", max_length=200, help_text="例：揚水ポンプの送水不良")
    location = models.CharField("場所・機器", max_length=200, help_text="例：機械室 揚水ポンプ Model-102")
    work_details = models.TextField("今日の作業内容", default="")
    symptom = models.TextField("症状・問題", help_text="例：水を吸い上げず送水できない。")
    solution = models.TextField("対応・解決策", help_text="例：バルブを取り外し清掃、パッキン交換。")
    keywords = models.CharField("検索キーワード", max_length=200, blank=True, help_text="例：ポンプ, バルブ, 異音")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="報告者")
    created_at = models.DateTimeField("作成日時", default=timezone.now)
    updated_at = models.DateTimeField("更新日時", auto_now=True)
    class Meta: verbose_name = "トラブルシュート報告書"; verbose_name_plural = "トラブルシュート報告書"; ordering = ["-updated_at"]
    def __str__(self): return self.title
    def get_absolute_url(self): return reverse('troubleshooting_detail', kwargs={'pk': self.pk})