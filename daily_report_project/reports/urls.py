from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    # ダッシュボード
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/data/", views.dashboard_data, name="dashboard_data"),  # ← 新規

    # 日報
    path("", views.ReportListView.as_view(), name="report_list"),
    path("reports/<int:pk>/", views.ReportDetailView.as_view(), name="report_detail"),
    path("reports/new/", views.ReportCreateView.as_view(), name="report_create"),
    path("reports/<int:pk>/edit/", views.ReportUpdateView.as_view(), name="report_update"),
    path("reports/<int:pk>/delete/", views.ReportDeleteView.as_view(), name="report_delete"),
    path("reports/export/csv/", views.report_export_csv, name="report_export_csv"),

    # 顧客
    path("customers/", views.CustomerListView.as_view(), name="customer_list"),
    path("customers/new/", views.CustomerCreateView.as_view(), name="customer_create"),
    path("customers/<int:pk>/", views.CustomerDetailView.as_view(), name="customer_detail"),
    path("customers/<int:pk>/edit/", views.CustomerUpdateView.as_view(), name="customer_update"),
    path("customers/<int:pk>/delete/", views.CustomerDeleteView.as_view(), name="customer_delete"),

    # 案件
    path("deals/", views.DealListView.as_view(), name="deal_list"),
    path("deals/new/", views.DealCreateView.as_view(), name="deal_create"),
    path("deals/<int:pk>/", views.DealDetailView.as_view(), name="deal_detail"),
    path("deals/<int:pk>/edit/", views.DealUpdateView.as_view(), name="deal_update"),
    path("deals/<int:pk>/delete/", views.DealDeleteView.as_view(), name="deal_delete"),

    # トラブルシューティング
    path("troubles/", views.TroubleshootingListView.as_view(), name="troubleshooting_list"),
    path("troubles/new/", views.TroubleshootingCreateView.as_view(), name="troubleshooting_create"),
    path("troubles/<int:pk>/", views.TroubleshootingDetailView.as_view(), name="troubleshooting_detail"),
    path("troubles/<int:pk>/edit/", views.TroubleshootingUpdateView.as_view(), name="troubleshooting_update"),
    path("troubles/<int:pk>/delete/", views.TroubleshootingDeleteView.as_view(), name="troubleshooting_delete"),

    # ToDo
    path("todo/", views.TodoListView.as_view(), name="todo_list"),
    path("todo/new/", views.TodoCreateView.as_view(), name="todo_create"),
    path("todo/<int:pk>/edit/", views.TodoUpdateView.as_view(), name="todo_update"),
    path("todo/<int:pk>/delete/", views.TodoDeleteView.as_view(), name="todo_delete"),
    path("todo/toggle/<int:pk>/", views.todo_toggle, name="todo_toggle"),
    path("todo/export/csv/", views.todo_export_csv, name="todo_export_csv"),
    path("todo/delete_selected/", views.todo_delete_selected, name="todo_delete_selected"),

    # プロフィール
    path("profile/", views.profile_update, name="profile"),

    # 音声ログ
    path("voice-logger/", views.voice_logger, name="voice_logger"),

    # API
    path("api/voice-logs/", views.api_voice_logs, name="api_voice_logs"),
    path("api/envcheck/", views.api_envcheck, name="api_envcheck"),
    path("api/tts/", views.api_tts, name="api_tts"),
    path("api/tts/save/", views.tts_save_api, name="tts_save_api"),
    path("api/voices/", views.api_voices, name="api_voices"),
]
