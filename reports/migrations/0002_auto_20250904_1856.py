# reports/migrations/0002_auto_20250904_1856.py

from django.db import migrations
from django.contrib.auth import get_user_model

def create_superuser(apps, schema_editor):
    User = get_user_model()

    # ↓↓↓ あなたの管理者情報に書き換えてください ↓↓↓
    username = "pc"
    email = "toshikazu.1976.12.8@gmail.com"
    password = "mokomoko2024"

    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f"スーパーユーザー '{username}' を作成しました。")

class Migration(migrations.Migration):

    dependencies = [
        # この数字は、あなたの環境の一個前のマイグレーションファイル名に合わせます
        # 多くの場合は '0001_initial' です
        ('reports', '0001_initial'), 
    ]

    operations = [
        migrations.RunPython(create_superuser),
    ]