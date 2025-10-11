# reports/views.py
from __future__ import annotations

import csv
import json
import hashlib
import os
from datetime import datetime, timedelta, date
from typing import List, Optional

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.db.models import Q, Count, Sum, Field
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseServerError,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.utils import timezone

try:
    from dotenv import load_dotenv
    base_dir = getattr(settings, "BASE_DIR", None)
    if base_dir:
        load_dotenv(os.path.join(base_dir, ".env"), override=False)
    else:
        load_dotenv(override=False)
except Exception:
    pass

from .forms import (
    CustomerForm,
    DealForm,
    ProfileForm,
    ReportForm,
    RequiredItemForm,
    SignUpForm,
    TroubleshootingForm,
)
from .models import (
    Customer,
    Deal,
    Report,
    RequiredItem,
    Troubleshooting,
    VoiceLog,
)

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from pathlib import Path
import uuid
import datetime as dt

try:
    from .utils.azure_tts import synthesize_mp3
except ImportError:
    synthesize_mp3 = None


# =========================
# 共通ユーティリティ
# =========================

def _detect_report_date_field() -> str | None:
    names = {f.name for f in Report._meta.get_fields()}
    for c in ("date", "report_date", "created_at", "updated_at"):
        if c in names:
            return c
    return None


def _apply_filters(qs, request: HttpRequest):
    start = (request.GET.get("start") or "").strip()
    end = (request.GET.get("end") or "").strip()
    query = (request.GET.get("q") or "").strip()

    date_field = _detect_report_date_field()
    if date_field:
        if start:
            try: qs = qs.filter(**{f"{date_field}__date__gte": datetime.fromisoformat(start).date()})
            except ValueError: pass
        if end:
            try: qs = qs.filter(**{f"{date_field}__date__lte": datetime.fromisoformat(end).date()})
            except ValueError: pass

    if query:
        q_objects = Q()
        if hasattr(Report, 'title'): q_objects |= Q(title__icontains=query)
        if hasattr(Report, 'location'): q_objects |= Q(location__icontains=query)
        if hasattr(Report, 'work_content'): q_objects |= Q(work_content__icontains=query)
        if hasattr(Report, 'note'): q_objects |= Q(note__icontains=query)
        if hasattr(Report, 'customer'): q_objects |= Q(customer__company_name__icontains=query)
        qs = qs.filter(q_objects)
    return qs


def _apply_ordering(qs, request: HttpRequest):
    sort = (request.GET.get("sort") or "").strip()
    key_map = {
        "created": "created_at", "-created": "-created_at",
        "author": "author__username", "-author": "-author__username",
    }
    order_key = key_map.get(sort, "-created_at")
    return qs.order_by(order_key)


def _esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# =========================
# サインアップ / プロフィール
# =========================

class SignUpView(CreateView):
    form_class = SignUpForm
    success_url = reverse_lazy("reports:report_list")
    template_name = "registration/signup.html"

    def form_valid(self, form):
        resp = super().form_valid(form)
        login(self.request, form.instance)
        return resp


@login_required
def profile_update(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, "プロフィールを保存しました。")
            return redirect("reports:report_list")
    else:
        form = ProfileForm(instance=request.user.profile)
    return render(request, "reports/profile_form.html", {"form": form})


# =========================
# Report 一覧/詳細/作成/編集/削除
# =========================

class ReportListView(LoginRequiredMixin, ListView):
    model = Report
    template_name = "reports/report_list.html"
    context_object_name = "reports"
    paginate_by = 10

    def get_queryset(self):
        qs = Report.objects.select_related('author').all()
        qs = _apply_filters(qs, self.request)
        qs = _apply_ordering(qs, self.request)
        return qs


class ReportDetailView(LoginRequiredMixin, DetailView):
    model = Report
    template_name = "reports/report_detail.html"


class ReportCreateView(LoginRequiredMixin, CreateView):
    model = Report
    form_class = ReportForm
    template_name = "reports/report_form.html"
    success_url = reverse_lazy("reports:report_list")

    def form_valid(self, form):
        form.instance.author = self.request.user
        hours = form.cleaned_data.get("hours") or 0
        minutes = form.cleaned_data.get("minutes") or 0
        form.instance.work_hours = timedelta(hours=hours, minutes=minutes)
        return super().form_valid(form)


class ReportUpdateView(LoginRequiredMixin, UpdateView):
    model = Report
    form_class = ReportForm
    template_name = "reports/report_form.html"
    success_url = reverse_lazy("reports:report_list")

    def get_initial(self):
        initial = super().get_initial()
        if self.object.work_hours:
            seconds = self.object.work_hours.total_seconds()
            initial['hours'] = int(seconds // 3600)
            initial['minutes'] = int((seconds % 3600) // 60)
        return initial

    def form_valid(self, form):
        hours = form.cleaned_data.get("hours") or 0
        minutes = form.cleaned_data.get("minutes") or 0
        form.instance.work_hours = timedelta(hours=hours, minutes=minutes)
        return super().form_valid(form)


class ReportDeleteView(LoginRequiredMixin, DeleteView):
    model = Report
    template_name = "reports/report_confirm_delete.html"
    success_url = reverse_lazy("reports:report_list")


@login_required
def report_export_csv(request: HttpRequest) -> HttpResponse:
    qs = Report.objects.select_related('author').all()
    qs = _apply_filters(qs, request)
    qs = _apply_ordering(qs, request)
    
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="reports.csv"'
    
    writer = csv.writer(response)
    header = ["ID", "作成日時", "報告者", "タイトル", "場所", "作業内容", "備考", "進捗", "作業時間(h)"]
    writer.writerow(header)
    
    for report in qs:
        hours = report.work_hours.total_seconds() / 3600 if report.work_hours else 0
        writer.writerow([
            report.id,
            timezone.localtime(report.created_at).strftime("%Y-%m-%d %H:%M"),
            report.author.username,
            report.title,
            report.location,
            report.work_content,
            report.note,
            report.get_progress_display(),
            f"{hours:.2f}"
        ])
    return response


# =========================
# Customer / Deal
# =========================
class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = "reports/customer_list.html"

class CustomerDetailView(LoginRequiredMixin, DetailView):
    model = Customer
    template_name = "reports/customer_detail.html"

class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = "reports/customer_form.html"
    success_url = reverse_lazy("reports:customer_list")

class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = "reports/customer_form.html"
    success_url = reverse_lazy("reports:customer_list")

class CustomerDeleteView(LoginRequiredMixin, DeleteView):
    model = Customer
    template_name = "reports/customer_confirm_delete.html"
    success_url = reverse_lazy("reports:customer_list")

class DealListView(LoginRequiredMixin, ListView):
    model = Deal
    template_name = "reports/deal_list.html"

class DealDetailView(LoginRequiredMixin, DetailView):
    model = Deal
    template_name = "reports/deal_detail.html"

class DealCreateView(LoginRequiredMixin, CreateView):
    model = Deal
    form_class = DealForm
    template_name = "reports/deal_form.html"
    success_url = reverse_lazy("reports:deal_list")

class DealUpdateView(LoginRequiredMixin, UpdateView):
    model = Deal
    form_class = DealForm
    template_name = "reports/deal_form.html"
    success_url = reverse_lazy("reports:deal_list")

class DealDeleteView(LoginRequiredMixin, DeleteView):
    model = Deal
    template_name = "reports/deal_confirm_delete.html"
    success_url = reverse_lazy("reports:deal_list")


# =========================
# Troubleshooting
# =========================
class TroubleshootingListView(LoginRequiredMixin, ListView):
    model = Troubleshooting
    template_name = "reports/troubleshooting_list.html"

class TroubleshootingDetailView(LoginRequiredMixin, DetailView):
    model = Troubleshooting
    template_name = "reports/troubleshooting_detail.html"

class TroubleshootingCreateView(LoginRequiredMixin, CreateView):
    model = Troubleshooting
    form_class = TroubleshootingForm
    template_name = "reports/troubleshooting_form.html"
    success_url = reverse_lazy("reports:troubleshooting_list")
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

class TroubleshootingUpdateView(LoginRequiredMixin, UpdateView):
    model = Troubleshooting
    form_class = TroubleshootingForm
    template_name = "reports/troubleshooting_form.html"
    success_url = reverse_lazy("reports:troubleshooting_list")

class TroubleshootingDeleteView(LoginRequiredMixin, DeleteView):
    model = Troubleshooting
    template_name = "reports/troubleshooting_confirm_delete.html"
    success_url = reverse_lazy("reports:troubleshooting_list")


# =========================
# ToDo
# =========================
class TodoListView(LoginRequiredMixin, ListView):
    model = RequiredItem
    context_object_name = "items"
    template_name = "reports/todo_list.html"
    def get_queryset(self):
        return RequiredItem.objects.filter(assignee=self.request.user).order_by('is_done', '-created_at')

class TodoCreateView(LoginRequiredMixin, CreateView):
    model = RequiredItem
    form_class = RequiredItemForm
    template_name = "reports/todo_form.html"
    success_url = reverse_lazy("reports:todo_list")
    def form_valid(self, form):
        form.instance.assignee = self.request.user
        return super().form_valid(form)

class TodoUpdateView(LoginRequiredMixin, UpdateView):
    model = RequiredItem
    form_class = RequiredItemForm
    template_name = "reports/todo_form.html"
    success_url = reverse_lazy("reports:todo_list")
    def get_queryset(self):
        return RequiredItem.objects.filter(assignee=self.request.user)

class TodoDeleteView(LoginRequiredMixin, DeleteView):
    model = RequiredItem
    template_name = "reports/todo_confirm_delete.html"
    success_url = reverse_lazy("reports:todo_list")
    def get_queryset(self):
        return RequiredItem.objects.filter(assignee=self.request.user)

@login_required
@require_POST
def todo_toggle(request: HttpRequest, pk: int) -> HttpResponse:
    item = get_object_or_404(RequiredItem, pk=pk, assignee=request.user)
    item.is_done = not item.is_done
    item.save()
    return redirect("reports:todo_list")

@login_required
@require_POST
def todo_delete_selected(request):
    todo_ids = request.POST.getlist('todo_ids')
    if todo_ids:
        items_to_delete = RequiredItem.objects.filter(pk__in=todo_ids, assignee=request.user)
        count = items_to_delete.count()
        if count > 0:
            items_to_delete.delete()
            messages.success(request, f"{count}件のToDoを削除しました。")
    else:
        messages.warning(request, "削除する項目が選択されていません。")
    return redirect("reports:todo_list")

@login_required
def todo_export_csv(request: HttpRequest) -> HttpResponse:
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = 'attachment; filename="todos.csv"'
    w = csv.writer(resp)
    w.writerow(["Item", "Deal", "Status"])
    for todo in RequiredItem.objects.filter(assignee=request.user):
        w.writerow([todo.title, str(todo.deal or ""), "Done" if todo.is_done else "Pending"])
    return resp

# =========================
# ダッシュボード
# =========================
@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    return render(request, "reports/dashboard.html")

@login_required
@require_GET
def dashboard_data(request: HttpRequest) -> JsonResponse:
    personal_reports = Report.objects.filter(author=request.user)
    group_reports = Report.objects.all()
    progress_display_map = dict(Report.PROGRESS_CHOICES)

    personal_progress_raw = personal_reports.values("progress").annotate(count=Count("id")).order_by("-count")
    personal_progress_count = [
        {"progress": progress_display_map.get(item['progress'], item['progress']), "count": item['count']}
        for item in personal_progress_raw
    ]
    
    personal_loc_hours_data = {}
    if hasattr(Report, 'work_hours') and hasattr(Report, 'location'):
        personal_loc_hours = personal_reports.exclude(location__exact='').values("location").annotate(total_duration=Sum("work_hours")).order_by("-total_duration")[:10]
        personal_loc_hours_data = {
            item["location"]: round(item["total_duration"].total_seconds() / 3600, 2)
            for item in personal_loc_hours if item["total_duration"]
        }

    group_progress_raw = group_reports.values("progress").annotate(count=Count("id")).order_by("-count")
    group_progress_count = [
        {"progress": progress_display_map.get(item['progress'], item['progress']), "count": item['count']}
        for item in group_progress_raw
    ]

    group_author_count = list(group_reports.values("author__username").annotate(count=Count("id")).order_by("-count"))
    
    total_group_count = group_reports.count()
    completed_group_count = group_reports.filter(progress="completed").count()
    completion_rate = round((completed_group_count / total_group_count) * 100, 1) if total_group_count > 0 else 0

    data = {
        "cards": { "user_total_count": personal_reports.count(), "group_total_count": total_group_count, "achievement_rate": completion_rate },
        "charts": {
            "personal_progress": personal_progress_count,
            "personal_location_hours": personal_loc_hours_data,
            "group_progress": group_progress_count,
            "group_author_count": group_author_count,
        }
    }
    return JsonResponse(data)

# =========================
# Voice Logger
# =========================
@login_required
def voice_logger(request: HttpRequest) -> HttpResponse:
    return render(request, "reports/voice_logger.html", {"api_token": getattr(settings, "FIELDNOTE_API_TOKEN", "devtoken")})

# =========================
# API
# =========================
def _auth_ok(request: HttpRequest) -> bool:
    token = (request.headers.get("Authorization", "").split(" ")[-1]).strip()
    return token and token == getattr(settings, "FIELDNOTE_API_TOKEN", "")

def _decode_json_body(request: HttpRequest) -> dict:
    try: return json.loads(request.body.decode('utf-8-sig'))
    except (json.JSONDecodeError, UnicodeDecodeError): return {}

@csrf_exempt
def api_voice_logs(request: HttpRequest) -> HttpResponse:
    if not _auth_ok(request):
        return JsonResponse({"ok": False, "error": "unauthorized"}, status=401)
    if request.method == 'POST':
        data = _decode_json_body(request)
        if not data.get("text"): return JsonResponse({"ok": False, "error": "text_required"}, status=400)
        customer_name = data.get("customer", "").strip()
        customer = Customer.objects.filter(company_name=customer_name).first() if customer_name else None
        idem_key = request.headers.get("Idempotency-Key", "").strip()
        if idem_key:
            cache_key = f"voice_idem:{idem_key}"
            if cached_id := cache.get(cache_key):
                return JsonResponse({"ok": True, "id": cached_id, "duplicate": True})
        log = VoiceLog.objects.create(
            text=data.get("text"), intent=data.get("intent", "note"), ts=data.get("ts", timezone.now().isoformat()),
            lat=data.get("lat"), lon=data.get("lon"), amount=data.get("amount"),
            when=data.get("when"), customer=customer,
        )
        if idem_key: cache.set(cache_key, log.id, timeout=3600)
        return JsonResponse({"ok": True, "id": log.id}, status=201)
    
    logs = VoiceLog.objects.select_related('customer').order_by('-id')[:20]
    items = [{
        "id": log.id, "text": log.text, "intent": log.intent, "ts": log.ts,
        "customer": log.customer.company_name if log.customer else None,
        "when": log.when.isoformat() if log.when else None,
        "lat": log.lat, "lon": log.lon, "amount": log.amount,
        "created_at": log.created_at.isoformat(),
    } for log in logs]
    return JsonResponse({"ok": True, "items": items})

@csrf_exempt
@require_POST
def api_tts(request: HttpRequest) -> HttpResponse:
    key = os.getenv("AZURE_SPEECH_KEY")
    region = os.getenv("AZURE_SPEECH_REGION", "japaneast")
    if not key or not region:
        return JsonResponse({"ok": False, "reason": "azure_not_configured"}, status=503)
    data = _decode_json_body(request)
    text = data.get("text", "").strip()
    if not text: return HttpResponseBadRequest("text is required")
    voice = data.get("voice", "ja-JP-NanamiNeural")
    ssml = f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='ja-JP'><voice name='{voice}'>{_esc(text)}</voice></speak>"
    headers = {"Ocp-Apim-Subscription-Key": key, "Content-Type": "application/ssml+xml", "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3"}
    try:
        response = requests.post(f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1", headers=headers, data=ssml.encode('utf-8'), timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        return JsonResponse({"ok": False, "reason": "tts_request_failed", "detail": str(e)}, status=502)
    return HttpResponse(response.content, content_type='audio/mpeg')