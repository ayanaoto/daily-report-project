from django.urls import path
from . import views

urlpatterns = [
    # ★★★ トップページのURLに 'report_list' の名前を設定 ★★★
    path('', views.report_list, name='report_list'),
    
    path('create/', views.report_create, name='report_create'),
    path('reports/<int:pk>/', views.report_detail, name='report_detail'),
    path('reports/<int:pk>/update/', views.report_update, name='report_update'),
    path('reports/<int:pk>/delete/', views.report_delete, name='report_delete'),
    path('ajax/load-deals/', views.load_deals, name='ajax_load_deals'),
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('customers/<int:pk>/update/', views.customer_update, name='customer_update'),
    path('customers/<int:pk>/delete/', views.customer_delete, name='customer_delete'),
    path('deals/', views.deal_list, name='deal_list'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('todos/', views.todo_list, name='todo_list'), 
    path('todos/<int:pk>/toggle/', views.todo_toggle, name='todo_toggle'),
    path('todos/export.csv/', views.todo_export_csv, name='todo_export_csv'),
    path('troubleshooting/', views.troubleshooting_list, name='troubleshooting_list'),
    path('troubleshooting/create/', views.troubleshooting_create, name='troubleshooting_create'),
    path('troubleshooting/<int:pk>/', views.troubleshooting_detail, name='troubleshooting_detail'),
    path('troubleshooting/<int:pk>/update/', views.troubleshooting_update, name='troubleshooting_update'),
    path('troubleshooting/<int:pk>/delete/', views.troubleshooting_delete, name='troubleshooting_delete'),
]