from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Report, Customer, Deal, RequiredItem, DealStatusLog, TroubleshootingReport
from .forms import ReportForm, CustomerForm, TroubleshootingReportForm
from django.http import JsonResponse, HttpResponse
from janome.tokenizer import Tokenizer
from datetime import timedelta, datetime
from collections import Counter, defaultdict
from django.core.exceptions import PermissionDenied
from django.db.models import Sum, Count, Q, OuterRef, Subquery
from django.contrib.auth.models import User
from django.utils import timezone
import csv

# ===================================================================
# 日報 (Report) のビュー
# ===================================================================

@login_required
def report_list(request):
    reports = Report.objects.filter(author=request.user).order_by('-work_date')
    return render(request, 'reports/report_list.html', {'reports': reports})

@login_required
def report_detail(request, pk):
    report = get_object_or_404(Report, pk=pk)
    if report.author != request.user and not request.user.is_superuser:
        raise PermissionDenied
    return render(request, 'reports/report_detail.html', {'report': report})

@login_required
def report_create(request):
    if request.method == 'POST':
        form = ReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.author = request.user
            hours = form.cleaned_data.get('hours', 0)
            minutes = form.cleaned_data.get('minutes', 0)
            report.work_hours = timedelta(hours=hours or 0, minutes=minutes or 0)
            report.save()
            return redirect('report_list')
    else:
        form = ReportForm()
    return render(request, 'reports/report_form.html', {'form': form})

@login_required
def report_update(request, pk):
    report = get_object_or_404(Report, pk=pk)
    if report.author != request.user and not request.user.is_superuser:
        raise PermissionDenied
    
    if request.method == 'POST':
        form = ReportForm(request.POST, request.FILES, instance=report)
        if form.is_valid():
            report = form.save(commit=False)
            hours = form.cleaned_data.get('hours', 0)
            minutes = form.cleaned_data.get('minutes', 0)
            report.work_hours = timedelta(hours=hours or 0, minutes=minutes or 0)
            report.save()
            return redirect('report_detail', pk=pk)
    else:
        total_seconds = report.work_hours.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        form = ReportForm(instance=report, initial={'hours': hours, 'minutes': minutes})
        
    return render(request, 'reports/report_form.html', {'form': form, 'report': report})

@login_required
def report_delete(request, pk):
    report = get_object_or_404(Report, pk=pk)
    if report.author != request.user and not request.user.is_superuser:
        raise PermissionDenied
        
    if request.method == 'POST':
        report.delete()
        return redirect('report_list')
    return render(request, 'reports/report_confirm_delete.html', {'report': report})

# ===================================================================
# 顧客 (Customer) と案件 (Deal) のビュー
# ===================================================================

@login_required
def customer_list(request):
    customers = Customer.objects.filter(account_manager=request.user).order_by('-created_at')
    return render(request, 'reports/customer_list.html', {'customers': customers})

@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if customer.account_manager != request.user and not request.user.is_superuser:
        raise PermissionDenied
    
    deals = customer.deal_set.all()
    reports = Report.objects.filter(customer_name=customer.customer_name)
    context = {
        'customer': customer,
        'deals': deals,
        'reports': reports,
    }
    return render(request, 'reports/customer_detail.html', context)

@login_required
def customer_update(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if customer.account_manager != request.user and not request.user.is_superuser:
        raise PermissionDenied
    
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('customer_detail', pk=pk)
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'reports/customer_form.html', {'form': form, 'customer': customer})

@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if customer.account_manager != request.user and not request.user.is_superuser:
        raise PermissionDenied
    
    if request.method == 'POST':
        customer.delete()
        return redirect('customer_list')
    return render(request, 'reports/customer_confirm_delete.html', {'customer': customer})

@login_required
def deal_list(request):
    deals = Deal.objects.filter(customer__account_manager=request.user).order_by('-id')
    return render(request, 'reports/deal_list.html', {'deals': deals})

def load_deals(request):
    customer_id = request.GET.get('customer_id')
    deals = Deal.objects.filter(
        customer_id=customer_id, 
        customer__account_manager=request.user
    ).order_by('deal_name')
    return JsonResponse(list(deals.values('id', 'deal_name')), safe=False)

# ===================================================================
# ダッシュボード (Dashboard)
# ===================================================================

@login_required
def dashboard(request):
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    base_reports = Report.objects.all()
    base_deals = Deal.objects.all()

    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        base_reports = base_reports.filter(work_date__gte=start_date)
        base_deals = base_deals.filter(customer__created_at__gte=start_date)
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        base_reports = base_reports.filter(work_date__lte=end_date)
        base_deals = base_deals.filter(customer__created_at__lte=end_date)

    if not request.user.is_superuser:
        reports = base_reports.filter(author=request.user)
        deals = base_deals.filter(customer__account_manager=request.user)
    else:
        reports = base_reports
        deals = base_deals

    # --- ステータス別集計 ---
    latest_status = DealStatusLog.objects.filter(deal=OuterRef('pk')).order_by('-timestamp')
    deals = deals.annotate(latest_status=Subquery(latest_status.values('status')[:1]))
    deal_status_data = deals.values('latest_status').annotate(count=Count('id')).order_by('latest_status')
    deal_status_labels = [item['latest_status'] or "未設定" for item in deal_status_data]
    deal_status_amounts = [item['count'] for item in deal_status_data]

    # --- 担当者別の案件数 ---
    won_deals_by_user = (
        deals.filter(latest_status='won')
        .values('customer__account_manager__username')
        .annotate(count=Count('id'))
        .order_by('customer__account_manager__username')
    )
    user_labels = [item['customer__account_manager__username'] for item in won_deals_by_user]
    user_deal_counts = [item['count'] for item in won_deals_by_user]

    # --- カテゴリ別集計（補修・草刈り・塗装などをキーワード判定） ---
    categories = ["補修", "草刈り", "塗装", "清掃", "点検"]
    category_counts = Counter()
    for report in reports:
        text = f"{report.work_details or ''} {report.remarks or ''}"
        for cat in categories:
            if cat in text:
                category_counts[cat] += 1
    category_labels = list(category_counts.keys())
    category_data = list(category_counts.values())

    context = {
        'deal_status_chart_data': {'labels': deal_status_labels, 'data': deal_status_amounts},
        'user_deals_chart_data': {'labels': user_labels, 'data': user_deal_counts},
        'category_chart_data': {'labels': category_labels, 'data': category_data},
        'start_date': start_date_str,
        'end_date': end_date_str,
    }
    return render(request, 'reports/dashboard.html', context)

# ===================================================================
# ToDo (RequiredItem)
# ===================================================================

@login_required
def todo_list(request):
    show = request.GET.get("show", "open")
    case = request.GET.get("case", "").strip()
    todos_qs = RequiredItem.objects.select_related('deal').all()
    if show != "all":
        todos_qs = todos_qs.filter(is_done=False)
    if case:
        todos_qs = todos_qs.filter(deal__deal_name__icontains=case)
    todos = todos_qs.order_by("is_done", "deal__deal_name", "title")
    context = { 'todos': todos, 'show': show, 'case': case }
    return render(request, 'reports/todo_list.html', context)

@login_required
def todo_toggle(request, pk):
    if request.method != "POST":
        return HttpResponse(status=405)
    item = get_object_or_404(RequiredItem, pk=pk)
    item.mark_toggle()
    return redirect(request.META.get("HTTP_REFERER") or 'todo_list')

@login_required
def todo_export_csv(request):
    show = request.GET.get("show", "open")
    case = request.GET.get("case", "").strip()
    qs = RequiredItem.objects.select_related('deal').all()
    if show != "all":
        qs = qs.filter(is_done=False)
    if case:
        qs = qs.filter(deal__deal_name__icontains=case)
    resp = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    resp["Content-Disposition"] = 'attachment; filename="todo_export.csv"'
    w = csv.writer(resp)
    w.writerow(["案件名", "項目", "状態", "完了日時"])
    for it in qs.order_by("is_done", "deal__deal_name", "title"):
        deal_name = it.deal.deal_name if it.deal else "案件未指定"
        w.writerow([deal_name, it.title, "済" if it.is_done else "未", it.completed_at or ""])
    return resp

# ===================================================================
# トラブルシュート報告書
# ===================================================================

@login_required
def troubleshooting_list(request):
    query = request.GET.get('q', '').strip()
    reports = TroubleshootingReport.objects.all()
    if query:
        reports = reports.filter(
            Q(title__icontains=query) |
            Q(location__icontains=query) |
            Q(symptom__icontains=query) |
            Q(solution__icontains=query) |
            Q(keywords__icontains=query)
        ).distinct()
    context = { 'reports': reports, 'query': query }
    return render(request, 'reports/troubleshooting_list.html', context)

@login_required
def troubleshooting_detail(request, pk):
    report = get_object_or_404(TroubleshootingReport, pk=pk)
    return render(request, 'reports/troubleshooting_detail.html', {'report': report})

@login_required
def troubleshooting_create(request):
    if request.method == 'POST':
        form = TroubleshootingReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.author = request.user
            report.save()
            return redirect('troubleshooting_detail', pk=report.pk)
    else:
        form = TroubleshootingReportForm()
    return render(request, 'reports/troubleshooting_form.html', {'form': form})

@login_required
def troubleshooting_update(request, pk):
    report = get_object_or_404(TroubleshootingReport, pk=pk)
    if report.author != request.user and not request.user.is_superuser:
        raise PermissionDenied
    if request.method == 'POST':
        form = TroubleshootingReportForm(request.POST, instance=report)
        if form.is_valid():
            form.save()
            return redirect('troubleshooting_detail', pk=pk)
    else:
        form = TroubleshootingReportForm(instance=report)
    return render(request, 'reports/troubleshooting_form.html', {'form': form, 'report': report})

@login_required
def troubleshooting_delete(request, pk):
    report = get_object_or_404(TroubleshootingReport, pk=pk)
    if report.author != request.user and not request.user.is_superuser:
        raise PermissionDenied
    if request.method == 'POST':
        report.delete()
        return redirect('troubleshooting_list')
    return render(request, 'reports/troubleshooting_confirm_delete.html', {'report': report})
