# daily_report_project/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # ★★★ ログイン/ログアウト機能を有効化 ★★★
    path('accounts/', include('django.contrib.auth.urls')),
    
    # アプリケーションのURL
    path('', include('reports.urls')), 
]