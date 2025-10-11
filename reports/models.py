# reports/models.py
import os
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

# ===== ユーザープロフィールモデル =====
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    background_image = models.ImageField("背景画像", upload_to='backgrounds/', null=True, blank=True)

    def __str__(self):
        return self.user.username

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    # 既存のユーザーが更新された場合もprofileを保存
    if hasattr(instance, 'profile'):
        instance.profile.save()

# ===== 顧客モデル =====
class Customer(models.Model):
    company_name = models.CharField("会社名", max_length=200, unique=True)
    # 【修正】ビューやフォームに合わせて 'contact_name' に統一
    contact_name = models.CharField("担当者名", max_length=100, blank=True)
    phone_number = models.CharField("電話番号", max_length=20, blank=True)
    # 【修正】'email_address' から 'email' に統一
    email = models.EmailField("メールアドレス", blank=True)
    account_manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="担当者")
    created_at = models.DateTimeField("登録日", default=timezone.now)

    def __str__(self):
        return self.company_name

# ===== 案件モデル =====
class Deal(models.Model):
    STATUS_CHOICES = [('proposal', '提案中'), ('in_progress', '進行中'), ('won', '受注'), ('lost', '失注')]
    # 【修正】'deal_name' から 'name' に統一
    name = models.CharField("案件名", max_length=200)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="deals", verbose_name="顧客")
    status = models.CharField("ステータス", max_length=20, choices=STATUS_CHOICES, default='in_progress')
    amount = models.DecimalField("金額", max_digits=10, decimal_places=0, default=0)
    # 【修正】'close_date' から 'expected_order_date' に統一
    expected_order_date = models.DateField("受注予定日", null=True, blank=True)
    created_at = models.DateTimeField("作成日時", default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# ===== 日報モデル =====
class Report(models.Model):
    PROGRESS_CHOICES = [('not_started', '未着手'), ('in_progress', '作業中'), ('completed', '完了')]
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="報告者")
    # 【追加】タイトルフィールドを追加
    title = models.CharField("タイトル", max_length=200, default='')
    location = models.CharField("場所", max_length=200)
    progress = models.CharField("進捗", max_length=20, choices=PROGRESS_CHOICES, default='in_progress')
    work_hours = models.DurationField("作業時間", default=timedelta)
    # 【修正】'content'/'remarks' から 'work_content'/'note' に統一
    work_content = models.TextField("作業内容")
    note = models.TextField("備考", blank=True)
    created_at = models.DateTimeField("作成日時", default=timezone.now)

    def __str__(self):
        return self.title or f"{self.location} - {self.created_at:%Y-%m-%d}"

    def get_absolute_url(self):
        return reverse('reports:report_detail', kwargs={'pk': self.pk})

# ===== 添付ファイル =====
def attachment_upload_to(instance, filename):
    dt = timezone.now()
    rid = instance.report_id or 0
    return f"uploads/{dt:%Y/%m/%d}/report_{rid}/{filename}"

class ReportAttachment(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="attachments", verbose_name="日報")
    file = models.FileField("ファイル", upload_to=attachment_upload_to)
    title = models.CharField("タイトル", max_length=200, blank=True)
    created_at = models.DateTimeField("登録日時", auto_now_add=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.title or (self.file.name if self.file else "attachment")

# ===== ナレッジ（トラブルシュート） =====
class Troubleshooting(models.Model):
    title = models.CharField("タイトル", max_length=200)
    location = models.CharField("場所・機器", max_length=200)
    symptom = models.TextField("症状・問題")
    solution = models.TextField("対応・解決策")
    keywords = models.CharField("キーワード", max_length=255, blank=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="報告者")
    occurred_at = models.DateField("発生日", default=timezone.now)
    created_at = models.DateTimeField("作成日時", auto_now_add=True)
    updated_at = models.DateTimeField("更新日時", auto_now=True)

    def __str__(self):
        return self.title

# ===== ToDo =====
class RequiredItem(models.Model):
    title = models.CharField("項目", max_length=200)
    # 【再追加】'assignee' フィールドを追加
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="担当者")
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, null=True, blank=True, verbose_name="関連案件")
    # 【追加】日報からの自動作成時に使用
    required_items_list = models.TextField("必要物品リスト", blank=True)
    is_done = models.BooleanField("完了", default=False)
    created_at = models.DateTimeField("作成日時", default=timezone.now)

    def __str__(self):
        return self.title

# ===== 音声ログ =====
def voicelog_upload_to(instance, filename):
    dt = timezone.now()
    return f"voicelog/{dt:%Y/%m/%d}/{filename}"

class VoiceLog(models.Model):
    text = models.TextField("本文")
    intent = models.CharField("意図", max_length=50, default="note")
    ts = models.CharField("送信時刻(ISO文字列)", max_length=50, blank=True, default='')
    # 【修正】customerは文字列ではなくCustomerモデルへのForeignKeyに変更
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="顧客")
    when = models.DateField("日付", null=True, blank=True) # 文字列からDateFieldに変更
    lat = models.FloatField("緯度", null=True, blank=True)
    lon = models.FloatField("経度", null=True, blank=True)
    amount = models.IntegerField("金額(円)", null=True, blank=True)
    audio_file = models.FileField("音声ファイル", upload_to=voicelog_upload_to, null=True, blank=True)
    created_at = models.DateTimeField("受信日時", auto_now_add=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return (self.text or "")[:30]