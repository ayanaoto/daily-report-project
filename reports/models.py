# reports/models.py
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta
from django.urls import reverse

class Customer(models.Model):
    """顧客モデル"""
    customer_name = models.CharField("顧客名", max_length=100)
    account_manager = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="営業担当")
    created_at = models.DateTimeField("作成日時", default=timezone.now)

    def __str__(self):
        return self.customer_name


class Deal(models.Model):
    """案件モデル"""
    STATUS_CHOICES = [
        ('discussion', '商談中'),
        ('proposal', '提案済'),
        ('won', '受注'),
        ('lost', '失注'),
        ('working', '作業中'),
        ('completed', '完了'),
    ]
    deal_name = models.CharField("案件名", max_length=200)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="顧客")
    person_in_charge = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="担当者")
    amount = models.IntegerField("金額", default=0)
    status = models.CharField("ステータス", max_length=20, choices=STATUS_CHOICES, default='discussion')
    created_at = models.DateTimeField("作成日時", default=timezone.now)

    def __str__(self):
        return self.deal_name


class Report(models.Model):
    """日報モデル"""
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="作成者")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="顧客")
    title = models.CharField("件名", max_length=200)
    content = models.TextField("内容")
    created_at = models.DateTimeField("作成日時", default=timezone.now)

    def __str__(self):
        return self.title


class WorkLog(models.Model):
    """作業日報モデル"""
    PROGRESS_CHOICES = [
        ('not_started', '未着手'),
        ('in_progress', '作業中'),
        ('completed', '完了'),
    ]
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="作業者")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="顧客")
    deal = models.ForeignKey(Deal, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="案件")
    work_date = models.DateField("作業日")
    work_hours = models.DurationField("作業時間", default=timedelta)
    progress_status = models.CharField("進捗状況", max_length=20, choices=PROGRESS_CHOICES, default='not_started')
    repair_needed = models.TextField("修理・対応が必要な事項", blank=True, null=True)
    remarks = models.TextField("備考", blank=True, null=True)
    attachment = models.FileField("添付ファイル", upload_to='attachments/', blank=True, null=True)
    created_at = models.DateTimeField("登録日時", default=timezone.now)

    def __str__(self):
        return f"{self.work_date} - {self.customer.customer_name}"


class RequiredItem(models.Model):
    """必要物品(ToDo)モデル"""
    title = models.CharField("項目", max_length=200)
    deal = models.ForeignKey(
        Deal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="関連案件",
        related_name="required_items"
    )
    is_done = models.BooleanField("完了", default=False)
    completed_at = models.DateTimeField("完了日時", null=True, blank=True)
    created_at = models.DateTimeField("作成日時", default=timezone.now)

    class Meta:
        verbose_name = "必要物品"
        verbose_name_plural = "必要物品"
        ordering = ["is_done", "deal__deal_name", "title"]

    def __str__(self):
        return f"{self.title} ({'済' if self.is_done else '未'})"

    def mark_toggle(self):
        self.is_done = not self.is_done
        self.completed_at = timezone.now() if self.is_done else None
        self.save(update_fields=["is_done", "completed_at"])


class DealStatusLog(models.Model):
    """案件ステータスの変更履歴モデル"""
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name="status_logs", verbose_name="案件")
    status = models.CharField("ステータス", max_length=50)
    timestamp = models.DateTimeField("変更日時", default=timezone.now)

    class Meta:
        verbose_name = "案件ステータス履歴"
        verbose_name_plural = "案件ステータス履歴"
        ordering = ["deal", "timestamp"]

    def __str__(self):
        status_display = dict(Deal.STATUS_CHOICES).get(self.status, self.status)
        return f"{self.deal.deal_name} -> {status_display} ({self.timestamp.strftime('%Y-%m-%d')})"


# --- トラブルシュート報告書 ---
class TroubleshootingReport(models.Model):
    """トラブルシュート報告書モデル"""
    title = models.CharField("タイトル", max_length=200)
    location = models.CharField("場所・機器", max_length=200)
    symptom = models.TextField("症状・問題")
    solution = models.TextField("対応・解決策")
    keywords = models.CharField("検索キーワード", max_length=200, blank=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="報告者")
    created_at = models.DateTimeField("作成日時", default=timezone.now)
    updated_at = models.DateTimeField("更新日時", auto_now=True)

    class Meta:
        verbose_name = "トラブルシュート報告書"
        verbose_name_plural = "トラブルシュート報告書"
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('troubleshooting_detail', kwargs={'pk': self.pk})
