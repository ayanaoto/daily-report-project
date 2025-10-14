# reports/urls.py
from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    # Report (日報)
    path("", views.ReportListView.as_view(), name="report_list"),
    path("reports/", views.ReportListView.as_view(), name="report_list_explicit"), # ルートパスからの遷移用
    path("reports/create/", views.ReportCreateView.as_view(), name="report_create"),
    path("reports/<int:pk>/", views.ReportDetailView.as_view(), name="report_detail"),
    path("reports/<int:pk>/edit/", views.ReportUpdateView.as_view(), name="report_update"),
    path("reports/<int:pk>/delete/", views.ReportDeleteView.as_view(), name="report_delete"),
    path("reports/export/", views.report_export_csv, name="report_export_csv"),
    path("reports/<int:pk>/pdf/", views.report_pdf_view, name="report_pdf"),

    # Profile & Dashboard
    path("reports/profile/", views.profile_update, name="profile"),
    path("reports/dashboard/", views.dashboard, name="dashboard"),
    path("reports/dashboard/data/", views.dashboard_data, name="dashboard_data"),

    # Required Materials (必要物リスト)
    path('reports/materials/', views.RequiredMaterialListView.as_view(), name='required_material_list'),
    path('reports/report/<int:report_pk>/add_material/', views.required_material_create, name='required_material_create'),
    path('reports/material/<int:pk>/toggle/', views.required_material_toggle_status, name='required_material_toggle_status'),
    path('reports/material/<int:pk>/delete/', views.RequiredMaterialDeleteView.as_view(), name='required_material_delete'),

    # Customer (顧客)
    path("reports/customers/", views.CustomerListView.as_view(), name="customer_list"),
    path("reports/customers/create/", views.CustomerCreateView.as_view(), name="customer_create"),
    path("reports/customers/<int:pk>/", views.CustomerDetailView.as_view(), name="customer_detail"),
    path("reports/customers/<int:pk>/edit/", views.CustomerUpdateView.as_view(), name="customer_update"),
    path("reports/customers/<int:pk>/delete/", views.CustomerDeleteView.as_view(), name="customer_delete"),

    # Deal (案件)
    path("reports/deals/", views.DealListView.as_view(), name="deal_list"),
    path("reports/deals/create/", views.DealCreateView.as_view(), name="deal_create"),
    path("reports/deals/<int:pk>/", views.DealDetailView.as_view(), name="deal_detail"),
    path("reports/deals/<int:pk>/edit/", views.DealUpdateView.as_view(), name="deal_update"),
    path("reports/deals/<int:pk>/delete/", views.DealDeleteView.as_view(), name="deal_delete"),

    # Troubleshooting (トラブルシュート)
    path("reports/troubleshooting/", views.TroubleshootingListView.as_view(), name="troubleshooting_list"),
    path("reports/troubleshooting/create/", views.TroubleshootingCreateView.as_view(), name="troubleshooting_create"),
    path("reports/troubleshooting/<int:pk>/", views.TroubleshootingDetailView.as_view(), name="troubleshooting_detail"),
    path("reports/troubleshooting/<int:pk>/edit/", views.TroubleshootingUpdateView.as_view(), name="troubleshooting_update"),
    path("reports/troubleshooting/<int:pk>/delete/", views.TroubleshootingDeleteView.as_view(), name="troubleshooting_delete"),

    # ToDo
    path("reports/todo/", views.TodoListView.as_view(), name="todo_list"),
    path("reports/todo/create/", views.TodoCreateView.as_view(), name="todo_create"),
    path("reports/todo/<int:pk>/edit/", views.TodoUpdateView.as_view(), name="todo_update"),
    path("reports/todo/<int:pk>/delete/", views.TodoDeleteView.as_view(), name="todo_delete"),
    path("reports/todo/<int:pk>/toggle/", views.todo_toggle, name="todo_toggle"),
    path("reports/todo/export/", views.todo_export_csv, name="todo_export_csv"),
    path("reports/todo/delete-selected/", views.todo_delete_selected, name="todo_delete_selected"),

    # Voice Logger
    path("reports/voice-logger/", views.voice_logger, name="voice_logger"),

    # API
    path("api/tts/", views.api_tts, name="api_tts"),
    path("api/voice_logs/", views.api_voice_logs, name="api_voice_logs"),
]