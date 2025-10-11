# voice_logs/models.py
from django.db import models
from reports.models import Customer

class VoiceLog(models.Model):
    text = models.TextField("テキスト")
    intent = models.CharField("インテント", max_length=50, default="note")
    
    # 【修正】default='' を追加
    ts = models.CharField("タイムスタンプ文字列", max_length=100, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    lat = models.FloatField("緯度", null=True, blank=True)
    lon = models.FloatField("経度", null=True, blank=True)
    amount = models.IntegerField("金額", null=True, blank=True)
    when = models.DateField("日付", null=True, blank=True)
    customer = models.ForeignKey(
        Customer, 
        verbose_name="顧客", 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )

    def __str__(self):
        return self.text[:50]