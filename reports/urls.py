from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    # Report
    path("", views.ReportListView.as_view(), name="report_list"),
    path("reports/", views.ReportListView.as_view(), name="report_list"),
    path("reports/create/", views.ReportCreateView.as_view(), name="report_create"),
    path("reports/<int:pk>/", views.ReportDetailView.as_view(), name="report_detail"),
    path("reports/<int:pk>/edit/", views.ReportUpdateView.as_view(), name="report_update"),
    path("reports/<int:pk>/delete/", views.ReportDeleteView.as_view(), name="report_delete"),
    path("reports/export/", views.report_export_csv, name="report_export_csv"),

    # Dashboard（新規・分離）
    path("dashboard/", views.dashboard, name="dashboard"),

    # Customer
    path("customers/", views.CustomerListView.as_view(), name="customer_list"),
    path("customers/create/", views.CustomerCreateView.as_view(), name="customer_create"),
    path("customers/<int:pk>/", views.CustomerDetailView.as_view(), name="customer_detail"),
    path("customers/<int:pk>/edit/", views.CustomerUpdateView.as_view(), name="customer_update"),
    path("customers/<int:pk>/delete/", views.CustomerDeleteView.as_view(), name="customer_delete"),

    # Deal
    path("deals/", views.DealListView.as_view(), name="deal_list"),
    path("deals/create/", views.DealCreateView.as_view(), name="deal_create"),
    path("deals/<int:pk>/", views.DealDetailView.as_view(), name="deal_detail"),
    path("deals/<int:pk>/edit/", views.DealUpdateView.as_view(), name="deal_update"),
    path("deals/<int:pk>/delete/", views.DealDeleteView.as_view(), name="deal_delete"),

    # Troubleshooting
    path("troubleshooting/", views.TroubleshootingListView.as_view(), name="troubleshooting_list"),
    path("troubleshooting/create/", views.TroubleshootingCreateView.as_view(), name="troubleshooting_create"),
    path("troubleshooting/<int:pk>/", views.TroubleshootingDetailView.as_view(), name="troubleshooting_detail"),
    path("troubleshooting/<int:pk>/edit/", views.TroubleshootingUpdateView.as_view(), name="troubleshooting_update"),
    path("troubleshooting/<int:pk>/delete/", views.TroubleshootingDeleteView.as_view(), name="troubleshooting_delete"),

    # ToDo
    path("todo/", views.TodoListView.as_view(), name="todo_list"),
    path("todo/create/", views.TodoCreateView.as_view(), name="todo_create"),
    path("todo/<int:pk>/edit/", views.TodoUpdateView.as_view(), name="todo_update"),
    path("todo/<int:pk>/delete/", views.TodoDeleteView.as_view(), name="todo_delete"),
    path("todo/<int:pk>/toggle/", views.todo_toggle, name="todo_toggle"),
    path("todo/export/", views.todo_export_csv, name="todo_export_csv"),

    # Account
    path("signup/", views.SignUpView.as_view(), name="signup"),
    path("profile/", views.profile_update, name="profile"),

    # Voice Logger
    path("voice-logger/", views.voice_logger, name="voice_logger"),

    # API
    path("api/voice-logs/", views.api_voice_logs, name="api_voice_logs"),
    path("api/tts/", views.api_tts, name="api_tts"),
]
