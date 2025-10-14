# reports/models.py
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver
import re # 正規表現のインポート

# ===== ユーザープロフィールモデル =====
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    background_image = models.ImageField("背景画像", upload_to='backgrounds/', null=True, blank=True)
    def __str__(self): return self.user.username

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created: Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

# ===== 顧客モデル =====
class Customer(models.Model):
    company_name = models.CharField("会社名", max_length=200, unique=True)
    contact_person = models.CharField("担当者名", max_length=100, blank=True)
    phone_number = models.CharField("電話番号", max_length=20, blank=True)
    email_address = models.EmailField("メールアドレス", blank=True)
    account_manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="担当者")
    created_at = models.DateTimeField("登録日", default=timezone.now)
    def __str__(self): return self.company_name

# ===== 案件モデル =====
class Deal(models.Model):
    STATUS_CHOICES = [('proposal', '提案中'), ('in_progress', '進行中'), ('won', '受注'), ('lost', '失注')]
    deal_name = models.CharField("案件名", max_length=200)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="deals", verbose_name="顧客")
    status = models.CharField("ステータス", max_length=20, choices=STATUS_CHOICES, default='proposal')
    amount = models.DecimalField("金額", max_digits=10, decimal_places=0, default=0)
    close_date = models.DateField("受注予定日", null=True, blank=True)
    created_at = models.DateTimeField("作成日時", default=timezone.now)
    def __str__(self): return self.deal_name

# ===== 日報モデル =====
class Report(models.Model):
    PROGRESS_CHOICES = [('not_started', '未着手'), ('in_progress', '作業中'), ('completed', '完了')]
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="報告者")
    location = models.CharField("場所", max_length=200)
    progress = models.CharField("進捗", max_length=20, choices=PROGRESS_CHOICES, default='in_progress')
    work_hours = models.DurationField("作業時間", default=timedelta)
    content = models.TextField("作業内容")
    remarks = models.TextField("備考", blank=True)
    created_at = models.DateTimeField("作成日時", default=timezone.now)
    def __str__(self): return f"{self.location} - {self.created_at:%Y-%m-%d}"
    def get_absolute_url(self): return reverse('reports:report_detail', kwargs={'pk': self.pk})

# ===== 添付ファイルモデル =====
def attachment_upload_to(instance, filename):
    dt = timezone.now(); rid = instance.report_id or 0
    return f"uploads/{dt:%Y/%m/%d}/report_{rid}/{filename}"
class ReportAttachment(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="attachments", verbose_name="日報")
    file = models.FileField("ファイル", upload_to=attachment_upload_to)
    title = models.CharField("タイトル", max_length=200, blank=True)
    created_at = models.DateTimeField("登録日時", auto_now_add=True)
    class Meta: ordering = ["-id"]
    def __str__(self): return self.title or (self.file.name if self.file else "attachment")
    @property
    def url(self):
        try: return self.file.url
        except Exception: return ""

# ===== トラブルシュートモデル =====
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
    def __str__(self): return self.title
    def get_absolute_url(self): return reverse('reports:troubleshooting_detail', kwargs={'pk': self.pk})

# ===== ToDoモデル (変更なし) =====
class RequiredItem(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="required_items", verbose_name="関連日報", null=True, blank=True)
    title = models.CharField("タイトル", max_length=200)
    description = models.TextField("詳細メモ", blank=True)
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, null=True, blank=True, verbose_name="関連案件")
    assignee = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="担当者", null=True, blank=True)
    is_done = models.BooleanField("完了", default=False)
    created_at = models.DateTimeField("作成日時", default=timezone.now)
    def __str__(self): return self.title

# ▼▼▼【ここから追加】▼▼▼
# ===== 必要物リストモデル (新規) =====
class RequiredMaterial(models.Model):
    STATUS_CHOICES = [
        ('needed', '必要'),
        ('procured', '調達済'),
    ]
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="required_materials", verbose_name="関連日報")
    name = models.CharField("物品名", max_length=200)
    quantity = models.CharField("数量", max_length=100, blank=True, default="1")
    status = models.CharField("状態", max_length=20, choices=STATUS_CHOICES, default='needed')
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="追加者")
    created_at = models.DateTimeField("作成日時", default=timezone.now)

    class Meta:
        ordering = ['status', '-created_at']

    def __str__(self):
        return self.name
# ▲▲▲【ここまで】▲▲▲

# ===== 音声ログモデル (変更なし) =====
def voicelog_upload_to(instance, filename):
    dt = timezone.now(); return f"voicelog/{dt:%Y/%m/%d}/{filename}"
class VoiceLog(models.Model):
    text = models.TextField("本文"); intent = models.CharField("意図", max_length=50, default="note")
    ts = models.CharField("送信時刻(ISO文字列)", max_length=50); lat = models.FloatField("緯度", null=True, blank=True)
    lon = models.FloatField("経度", null=True, blank=True); amount = models.IntegerField("金額(円)", null=True, blank=True)
    customer = models.CharField("顧客", max_length=120, null=True, blank=True)
    when = models.CharField("予定時刻(ISO文字列)", max_length=50, null=True, blank=True)
    created_at = models.DateTimeField("受信日時", auto_now_add=True); audio_file = models.FileField("音声ファイル", upload_to=voicelog_upload_to, null=True, blank=True)
    mime_type = models.CharField("MIME", max_length=100, blank=True, default=""); duration_sec = models.FloatField("長さ(秒)", default=0.0)
    class Meta:
        ordering = ["-id"]; indexes = [ models.Index(fields=["intent"]), models.Index(fields=["created_at"]), ]
    def __str__(self):
        head = (self.text or "")[:30].replace("\n", " "); return f"[{self.intent}] {head}..."
    @property
    def file_url(self) -> str:
        try: return self.file.url
        except Exception: return ""

# ▼▼▼【ここを修正】▼▼▼
# シグナル: 日報の備考欄から「必要物」を自動作成するように変更
@receiver(post_save, sender=Report)
def create_materials_from_remarks(sender, instance, **kwargs):
    if not instance.remarks:
        return

    # 備考欄の各行をチェック
    for line in instance.remarks.splitlines():
        line = line.strip()
        # 「〇〇が必要」というパターンにマッチするか確認
        match = re.match(r'^(.*?)が必要$', line)
        if match:
            items_text = match.group(1).strip()
            # 「、」や全角の「，」で区切って複数のアイテムに対応
            item_names = [item.strip() for item in re.split(r'[、，,]', items_text) if item.strip()]
            
            for item_name in item_names:
                # 既に同じ日報に同じアイテムがなければ作成
                RequiredMaterial.objects.get_or_create(
                    report=instance,
                    name=item_name,
                    defaults={'added_by': instance.author}
                )
# ▲▲▲【ここまで】▲▲▲