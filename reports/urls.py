from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    # Report 一覧/詳細/作成/編集/削除
    path("", views.ReportListView.as_view(), name="report_list"),                 # /reports/
    path("create/", views.ReportCreateView.as_view(), name="report_create"),      # /reports/create/
    path("<int:pk>/", views.ReportDetailView.as_view(), name="report_detail"),    # /reports/1/
    path("<int:pk>/edit/", views.ReportUpdateView.as_view(), name="report_update"),
    path("<int:pk>/delete/", views.ReportDeleteView.as_view(), name="report_delete"),
    path("export/", views.report_export_csv, name="report_export_csv"),

    # ダッシュボード
    path("dashboard/", views.dashboard, name="dashboard"),

    # 顧客
    path("customers/", views.CustomerListView.as_view(), name="customer_list"),
    path("customers/create/", views.CustomerCreateView.as_view(), name="customer_create"),
    path("customers/<int:pk>/", views.CustomerDetailView.as_view(), name="customer_detail"),
    path("customers/<int:pk>/edit/", views.CustomerUpdateView.as_view(), name="customer_update"),
    path("customers/<int:pk>/delete/", views.CustomerDeleteView.as_view(), name="customer_delete"),

    # 案件
    path("deals/", views.DealListView.as_view(), name="deal_list"),
    path("deals/create/", views.DealCreateView.as_view(), name="deal_create"),
    path("deals/<int:pk>/", views.DealDetailView.as_view(), name="deal_detail"),
    path("deals/<int:pk>/edit/", views.DealUpdateView.as_view(), name="deal_update"),
    path("deals/<int:pk>/delete/", views.DealDeleteView.as_view(), name="deal_delete"),

    # ナレッジ
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

    # Voice Logger ページ
    path("voice-logger/", views.voice_logger, name="voice_logger"),
]
