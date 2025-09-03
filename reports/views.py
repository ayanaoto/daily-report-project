# reports/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.core.exceptions import PermissionDenied
from django.db.models import Sum, Count, Q
from django.contrib.auth.models import User
from django.utils import timezone

from janome.tokenizer import Tokenizer
from datetime import timedelta, datetime
from collections import defaultdict
import csv

# モデル & フォーム
from .models import (
    Report, Customer, Deal, WorkLog,
    RequiredItem, DealStatusLog, TroubleshootingReport
)
from .forms import (
    ReportForm, CustomerForm, WorkLogForm, TroubleshootingReportForm
)

# -------------------------
# 日報
# -------------------------
@login_required
def report_list(request):
    reports = Report.objects.filter(author=request.user).order_by('-created_at')
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
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.author = request.user
            report.save()
            return redirect('report_list')
    else:
        form = ReportForm()
    return render(request, 'reports/report_create.html', {'form': form})

@login_required
def report_update(request, pk):
    report = get_object_or_404(Report, pk=pk)
    if report.author != request.user and not request.user.is_superuser:
        raise PermissionDenied
    if request.method == 'POST':
        form = ReportForm(request.POST, instance=report)
        if form.is_valid():
            form.save()
            return redirect('report_detail', pk=pk)
    else:
        form = ReportForm(instance=report)
    return render(request, 'reports/report_create.html', {'form': form})

@login_required
def report_delete(request, pk):
    report = get_object_or_404(Report, pk=pk)
    if report.author != request.user and not request.user.is_superuser:
        raise PermissionDenied
    if request.method == 'POST':
        report.delete()
        return redirect('report_list')
    return render(request, 'reports/report_confirm_delete.html', {'report': report})

# -------------------------
# 顧客
# -------------------------
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
    reports = customer.report_set.all()
    return render(request, 'reports/customer_detail.html', {'customer': customer, 'deals': deals, 'reports': reports})

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

# -------------------------
# 案件
# -------------------------
@login_required
def deal_list(request):
    deals = Deal.objects.filter(customer__account_manager=request.user).order_by('-created_at')
    return render(request, 'reports/deal_list.html', {'deals': deals})

# -------------------------
# 作業ログ
# -------------------------
@login_required
def work_log_list(request):
    work_logs = WorkLog.objects.filter(author=request.user).order_by('-work_date')
    return render(request, 'reports/work_log_list.html', {'work_logs': work_logs})

@login_required
def work_log_create(request):
    if request.method == 'POST':
        form = WorkLogForm(request.POST, request.FILES)
        if form.is_valid():
            work_log = form.save(commit=False)
            work_log.author = request.user
            hours = form.cleaned_data.get('hours', 0)
            minutes = form.cleaned_data.get('minutes', 0)
            if hours or minutes:
                work_log.work_hours = timedelta(hours=hours or 0, minutes=minutes or 0)
            work_log.save()
            return redirect('work_log_list')
    else:
        form = WorkLogForm()
    return render(request, 'reports/work_log_form.html', {'form': form})

@login_required
def work_log_detail(request, pk):
    work_log = get_object_or_404(WorkLog, pk=pk)
    if work_log.author != request.user and not request.user.is_superuser:
        raise PermissionDenied
    return render(request, 'reports/work_log_detail.html', {'work_log': work_log})

@login_required
def work_log_update(request, pk):
    work_log = get_object_or_404(WorkLog, pk=pk)
    if work_log.author != request.user and not request.user.is_superuser:
        raise PermissionDenied
    if request.method == 'POST':
        form = WorkLogForm(request.POST, request.FILES, instance=work_log)
        if form.is_valid():
            updated_log = form.save(commit=False)
            hours = form.cleaned_data.get('hours', 0)
            minutes = form.cleaned_data.get('minutes', 0)
            if hours or minutes:
                updated_log.work_hours = timedelta(hours=hours or 0, minutes=minutes or 0)
            updated_log.save()
            return redirect('work_log_detail', pk=pk)
    else:
        form = WorkLogForm(instance=work_log)
    return render(request, 'reports/work_log_form.html', {'form': form, 'work_log': work_log})

@login_required
def work_log_delete(request, pk):
    work_log = get_object_or_404(WorkLog, pk=pk)
    if work_log.author != request.user and not request.user.is_superuser:
        raise PermissionDenied
    if request.method == 'POST':
        work_log.delete()
        return redirect('work_log_list')
    return render(request, 'reports/work_log_confirm_delete.html', {'work_log': work_log})

# Ajax: 案件リスト取得
def load_deals(request):
    customer_id = request.GET.get('customer_id')
    deals = Deal.objects.filter(customer_id=customer_id, customer__account_manager=request.user).order_by('deal_name')
    return JsonResponse(list(deals.values('id', 'deal_name')), safe=False)

# -------------------------
# ダッシュボード
# -------------------------
@login_required
def dashboard(request):
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    base_work_logs = WorkLog.objects.all()
    base_deals = Deal.objects.all()

    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        base_work_logs = base_work_logs.filter(work_date__gte=start_date)
        base_deals = base_deals.filter(created_at__gte=start_date)
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        base_work_logs = base_work_logs.filter(work_date__lte=end_date)
        base_deals = base_deals.filter(created_at__lte=end_date)

    if not request.user.is_superuser:
        work_logs = base_work_logs.filter(author=request.user)
        deals = base_deals.filter(person_in_charge=request.user)
    else:
        work_logs = base_work_logs
        deals = base_deals

    managers_with_deals = User.objects.filter(deal__isnull=False).distinct().annotate(
        deal_count=Count('deal')
    ).prefetch_related('deal_set').order_by('username')

    # 案件進捗可視化
    deals_for_gantt = deals.prefetch_related('status_logs')
    status_durations = []
    for deal in deals_for_gantt:
        logs = list(deal.status_logs.order_by('timestamp'))
        durations = []
        total_days = 0
        if logs:
            first_log_date = logs[0].timestamp
            total_days = max(1, (timezone.now() - first_log_date).days)
        for i, log in enumerate(logs):
            start_date = log.timestamp
            end_date = logs[i + 1].timestamp if i + 1 < len(logs) else timezone.now()
            duration_days = max(0, (end_date - start_date).days)
            percentage = round((duration_days / total_days) * 100) if total_days > 0 else 0
            durations.append({
                "status": log.status,
                "get_status_display": dict(Deal.STATUS_CHOICES).get(log.status, log.status),
                "days": duration_days,
                "percentage": percentage
            })
        if durations:
            status_durations.append({"deal": deal, "durations": durations, "total_days": total_days})

    # 必要物品の抽出
    t = Tokenizer()
    needed_items = defaultdict(list)
    for log in work_logs:
        deal_name = log.deal.deal_name if log.deal else "案件未指定"
        texts_to_check = f"{log.repair_needed or ''} {log.remarks or ''}"
        tokens = list(t.tokenize(texts_to_check))
        for i, token in enumerate(tokens):
            if token.part_of_speech.startswith('名詞'):
                if i + 1 < len(tokens) and tokens[i+1].surface == '必要':
                    needed_items[deal_name].append(token.surface)
                elif i + 2 < len(tokens) and tokens[i+1].surface == 'が' and tokens[i+2].surface == '必要':
                    needed_items[deal_name].append(token.surface)

    # 集計
    deal_status_data = deals.values('status').annotate(total_amount=Sum('amount')).order_by('status')
    deal_status_labels = [dict(Deal.STATUS_CHOICES).get(item['status']) for item in deal_status_data]
    deal_status_amounts = [item['total_amount'] for item in deal_status_data]

    work_log_status_data = work_logs.values('progress_status').annotate(count=Count('id')).order_by('progress_status')
    work_log_status_labels = [dict(WorkLog.PROGRESS_CHOICES).get(item['progress_status']) for item in work_log_status_data]
    work_log_status_counts = [item['count'] for item in work_log_status_data]

    won_deals_by_user = deals.filter(status='won', person_in_charge__isnull=False).values(
        'person_in_charge__username'
    ).annotate(count=Count('id')).order_by('person_in_charge__username')
    user_labels = [item['person_in_charge__username'] for item in won_deals_by_user]
    user_deal_counts = [item['count'] for item in won_deals_by_user]

    context = {
        'start_date': start_date_str,
        'end_date': end_date_str,
        'deal_status_chart_data': {'labels': deal_status_labels, 'data': deal_status_amounts},
        'work_log_status_chart_data': {'labels': work_log_status_labels, 'data': work_log_status_counts},
        'user_deals_chart_data': {'labels': user_labels, 'data': user_deal_counts},
        "managers_with_deals": managers_with_deals,
        "status_durations": status_durations,
        'needed_items': dict(needed_items),
    }
    return render(request, 'reports/dashboard.html', context)

# -------------------------
# ToDo (必要物品)
# -------------------------
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
    return render(request, 'reports/todo_list.html', {'todos': todos, 'show': show, 'case': case})

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

# -------------------------
# トラブルシュート
# -------------------------
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
    return render(request, 'reports/troubleshooting_list.html', {'reports': reports, 'query': query})

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
            return redirect('troubleshooting_detail', pk=report.pk)
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
