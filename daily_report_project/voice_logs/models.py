from django.db import models

class VoiceLog(models.Model):
    """
    音声メモ等のテキスト記録。
    - ts: 記録時刻（未指定時はAPIで自動補完）
    - when: 任意の“日付”（期日のような使い方）
    """
    text = models.TextField()
    intent = models.CharField(max_length=50, default="note")
    ts = models.DateTimeField(null=True, blank=True)
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lon = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    customer = models.CharField(max_length=255, null=True, blank=True)
    when = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")

    def __str__(self):
        return f"[{self.id}] {self.intent}: {self.text[:30]}"
