from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Report (日報)
    path('', views.ReportListView.as_view(), name='report_list'),
    path('reports/<int:pk>/', views.ReportDetailView.as_view(), name='report_detail'),
    path('reports/create/', views.ReportCreateView.as_view(), name='report_create'),
    path('reports/<int:pk>/update/', views.ReportUpdateView.as_view(), name='report_update'),
    path('reports/<int:pk>/delete/', views.ReportDeleteView.as_view(), name='report_confirm_delete'),

    # Customer (顧客)
    path('customers/', views.CustomerListView.as_view(), name='customer_list'),
    path('customers/create/', views.CustomerCreateView.as_view(), name='customer_create'),
    path('customers/<int:pk>/', views.CustomerDetailView.as_view(), name='customer_detail'),
    path('customers/<int:pk>/update/', views.CustomerUpdateView.as_view(), name='customer_update'),
    path('customers/<int:pk>/delete/', views.CustomerDeleteView.as_view(), name='customer_delete'),

    # Deal (案件)
    path('deals/', views.DealListView.as_view(), name='deal_list'),
    path('deals/create/', views.DealCreateView.as_view(), name='deal_create'),
    path('deals/<int:pk>/', views.DealDetailView.as_view(), name='deal_detail'),
    path('deals/<int:pk>/update/', views.DealUpdateView.as_view(), name='deal_update'),
    path('deals/<int:pk>/delete/', views.DealDeleteView.as_view(), name='deal_delete'),

    # Troubleshooting (トラブルシュート)
    path('troubleshooting/', views.TroubleshootingListView.as_view(), name='troubleshooting_list'),
    path('troubleshooting/create/', views.TroubleshootingCreateView.as_view(), name='troubleshooting_create'),
    path('troubleshooting/<int:pk>/', views.TroubleshootingDetailView.as_view(), name='troubleshooting_detail'),
    path('troubleshooting/<int:pk>/update/', views.TroubleshootingUpdateView.as_view(), name='troubleshooting_update'),
    path('troubleshooting/<int:pk>/delete/', views.TroubleshootingDeleteView.as_view(), name='troubleshooting_delete'),

    # ToDo (RequiredItem)
    path('todos/', views.TodoListView.as_view(), name='todo_list'),
    path('todos/create/', views.TodoCreateView.as_view(), name='todo_create'),
    path('todos/<int:pk>/toggle/', views.todo_toggle, name='todo_toggle'),
    path('todos/<int:pk>/update/', views.TodoUpdateView.as_view(), name='todo_update'),
    path('todos/<int:pk>/delete/', views.TodoDeleteView.as_view(), name='todo_delete'),
    path('todos/export/', views.todo_export_csv, name='todo_export_csv'),

    # Dashboard (分析)
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Account & Profile
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('profile/', views.profile_update, name='profile_update'),
]