# reports/views.py
from __future__ import annotations

import csv
import json
import hashlib
import os
from datetime import datetime, timedelta, date
from typing import Optional

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

# azure_tts.py が無い環境でも動くように try/except
try:
    from .utils.azure_tts import synthesize_mp3
except Exception:
    synthesize_mp3 = None


# =========================
# 共通ユーティリティ
# =========================

def _detect_report_date_field() -> str | None:
    """Reportモデル内で日付に使えそうなフィールド名を自動検出"""
    names = {f.name for f in Report._meta.get_fields()}
    for c in ("date", "report_date", "created_at", "updated_at"):
        if c in names:
            return c
    return None


def _apply_filters(qs, request: HttpRequest):
    """一覧系でクエリパラメータに応じたフィルタリングを適用"""
    start = (request.GET.get("start") or "").strip()
    end = (request.GET.get("end") or "").strip()
    query = (request.GET.get("q") or "").strip()

    date_field = _detect_report_date_field()
    if date_field:
        if start:
            try:
                qs = qs.filter(**{f"{date_field}__date__gte": datetime.fromisoformat(start).date()})
            except ValueError:
                pass
        if end:
            try:
                qs = qs.filter(**{f"{date_field}__date__lte": datetime.fromisoformat(end).date()})
            except ValueError:
                pass

    if query:
        names = {f.name for f in Report._meta.get_fields()}
        q = Q()
        # 現行モデルに存在するテキスト項目のみ
        for f in ("location", "content", "remarks"):
            if f in names:
                q |= Q(**{f"{f}__icontains": query})
        if q:
            qs = qs.filter(q)
    return qs


def _apply_ordering(qs, request: HttpRequest):
    """一覧のソートを適用"""
    sort = (request.GET.get("sort") or "").strip()
    names = {f.name for f in Report._meta.get_fields()}
    mapping = {
        "created": "created_at" if "created_at" in names else "id",
        "-created": "-created_at" if "created_at" in names else "-id",
        "id": "id",
        "-id": "-id",
        "author": "author__username",
        "-author": "-author__username",
    }
    key = mapping.get(sort)
    return qs.order_by(key) if key else qs.order_by("-created_at") if "created_at" in names else qs.order_by("-id")


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

    def get_paginate_by(self, queryset):
        try:
            n = int(self.request.GET.get("per_page", "") or 0)
            if 5 <= n <= 100:
                return n
        except ValueError:
            pass
        return super().get_paginate_by(queryset)

    def get_queryset(self):
        qs = Report.objects.all() if self.request.user.is_superuser else Report.objects.filter(author=self.request.user)
        qs = _apply_filters(qs, self.request)
        qs = _apply_ordering(qs, self.request)
        return qs


class ReportDetailView(LoginRequiredMixin, DetailView):
    model = Report
    template_name = "reports/report_detail.html"

    def get_queryset(self):
        return Report.objects.all() if self.request.user.is_superuser else Report.objects.filter(author=self.request.user)


class ReportCreateView(LoginRequiredMixin, CreateView):
    model = Report
    form_class = ReportForm
    template_name = "reports/report_form.html"
    success_url = reverse_lazy("reports:report_list")

    def get_initial(self):
        initial = super().get_initial()
        today = datetime.now().date()
        names = {f.name for f in Report._meta.get_fields()}
        if "date" in names:
            initial.setdefault("date", today)
        if "report_date" in names:
            initial.setdefault("report_date", today)
        initial.setdefault("hours", 0)
        initial.setdefault("minutes", 0)
        initial.setdefault("_from_voice_logger", self.request.GET.get("draft") == "1")
        return initial

    def form_valid(self, form):
        form.instance.author = self.request.user
        hours = form.cleaned_data.get("hours") or 0
        minutes = form.cleaned_data.get("minutes") or 0
        if hasattr(form.instance, "work_hours"):
            form.instance.work_hours = timedelta(hours=hours, minutes=minutes)

        resp = super().form_valid(form)
        messages.success(self.request, "日報を登録しました。")
        return resp


class ReportUpdateView(LoginRequiredMixin, UpdateView):
    model = Report
    form_class = ReportForm
    template_name = "reports/report_form.html"

    def get_queryset(self):
        return Report.objects.all() if self.request.user.is_superuser else Report.objects.filter(author=self.request.user)

    def get_initial(self):
        initial = super().get_initial()
        if getattr(self.object, "work_hours", None):
            sec = self.object.work_hours.total_seconds()
            initial["hours"] = int(sec // 3600)
            initial["minutes"] = int((sec % 3600) // 60)
        return initial

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            hours = form.cleaned_data.get("hours") or 0
            minutes = form.cleaned_data.get("minutes") or 0
            if hasattr(form.instance, "work_hours"):
                form.instance.work_hours = timedelta(hours=hours, minutes=minutes)
            self.object = form.save()
            messages.success(self.request, "日報を更新しました。")
            return redirect(self.get_success_url())
    # フォーム不正時
        messages.warning(self.request, "入力に誤りがあります。")
        return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy("reports:report_detail", kwargs={"pk": self.object.pk})


class ReportDeleteView(LoginRequiredMixin, DeleteView):
    model = Report
    template_name = "reports/report_confirm_delete.html"
    success_url = reverse_lazy("reports:report_list")

    def get_queryset(self):
        return Report.objects.all() if self.request.user.is_superuser else Report.objects.filter(author=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "日報を削除しました。")
        return super().delete(request, *args, **kwargs)


@require_GET
@login_required
def report_export_csv(request: HttpRequest) -> HttpResponse:
    """フィルタ済み日報のCSVエクスポート（現行モデルに合わせた列）"""
    qs = Report.objects.all() if request.user.is_superuser else Report.objects.filter(author=request.user)
    qs = _apply_filters(qs, request)
    qs = _apply_ordering(qs, request)

    names = {f.name for f in Report._meta.get_fields()}
    cols = ["id"]
    # 現行項目のみ（titleはモデルから除去済み）
    for c in ("created_at", "date", "report_date", "author", "location", "content", "remarks", "work_hours", "progress"):
        if c in names:
            cols.append(c)

    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = 'attachment; filename="reports_filtered.csv"'
    w = csv.writer(resp)
    w.writerow(cols)
    for o in qs.iterator():
        row = []
        for c in cols:
            row.append(str(getattr(o, c, "")))
        w.writerow(row)
    return resp


# =========================
# Customer / Deal
# =========================

class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = "reports/customer_list.html"
    context_object_name = "customers"


class CustomerDetailView(LoginRequiredMixin, DetailView):
    model = Customer
    template_name = "reports/customer_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        customer = self.get_object()
        ctx["deals"] = Deal.objects.filter(customer=customer)
        return ctx


class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = "reports/customer_form.html"
    success_url = reverse_lazy("reports:customer_list")


class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = "reports/customer_form.html"

    def get_success_url(self):
        return reverse_lazy("reports:customer_detail", kwargs={"pk": self.object.pk})


class CustomerDeleteView(LoginRequiredMixin, DeleteView):
    model = Customer
    template_name = "reports/customer_confirm_delete.html"
    success_url = reverse_lazy("reports:customer_list")


class DealListView(LoginRequiredMixin, ListView):
    model = Deal
    template_name = "reports/deal_list.html"
    context_object_name = "deals"


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

    def get_success_url(self):
        return reverse_lazy("reports:deal_detail", kwargs={"pk": self.object.pk})


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
    context_object_name = "items"

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(title__icontains=q)
                | Q(symptom__icontains=q)
                | Q(solution__icontains=q)
                | Q(keywords__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["query"] = self.request.GET.get("q", "")
        return ctx


class TroubleshootingDetailView(LoginRequiredMixin, DetailView):
    model = Troubleshooting
    template_name = "reports/troubleshooting_detail.html"
    context_object_name = "report"


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

    def get_success_url(self):
        return reverse_lazy("reports:troubleshooting_detail", kwargs={"pk": self.object.pk})


class TroubleshootingDeleteView(LoginRequiredMixin, DeleteView):
    model = Troubleshooting
    template_name = "reports/troubleshooting_confirm_delete.html"
    success_url = reverse_lazy("reports:troubleshooting_list")
    context_object_name = "report"


# =========================
# ToDo
# =========================

class TodoListView(LoginRequiredMixin, ListView):
    model = RequiredItem
    template_name = "reports/todo_list.html"
    context_object_name = "items"

    def get_queryset(self):
        return RequiredItem.objects.filter(assignee=self.request.user).order_by('is_done', '-created_at')


class TodoCreateView(LoginRequiredMixin, CreateView):
    model = RequiredItem
    form_class = RequiredItemForm
    template_name = "reports/todo_form.html"
    success_url = reverse_lazy("reports:todo_list")

    def form_valid(self, form):
        # assignee未入力でも自分にアサイン
        if not form.cleaned_data.get('assignee'):
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
    todo = get_object_or_404(RequiredItem, pk=pk, assignee=request.user)
    todo.is_done = not todo.is_done
    todo.save()
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


@login_required
@require_POST
def todo_delete_selected(request):
    """チェックボックスで選択された複数のToDo項目を削除"""
    todo_ids = request.POST.getlist('todo_ids')

    if not todo_ids:
        messages.warning(request, "削除するToDoが選択されていません。")
        return redirect("reports:todo_list")

    items_to_delete = RequiredItem.objects.filter(pk__in=todo_ids, assignee=request.user)
    count = items_to_delete.count()
    if count > 0:
        items_to_delete.delete()
        messages.success(request, f"{count}件のToDoを削除しました。")
    return redirect("reports:todo_list")


# =========================
# ダッシュボード + データAPI
# =========================
@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """ダッシュボード（テンプレート側JSから dashboard_data を叩く）"""
    today = datetime.now().date()
    date_field = _detect_report_date_field()
    qs_all = Report.objects.all()
    if date_field:
        today_qs = qs_all.filter(**{f"{date_field}__date": today})
        month_qs = qs_all.filter(**{f"{date_field}__date__gte": today.replace(day=1)})
    else:
        today_qs = Report.objects.none()
        month_qs = qs_all

    def sum_hours(qs):
        if "work_hours" not in {f.name for f in Report._meta.get_fields()}:
            return 0.0
        agg = qs.aggregate(total=Sum("work_hours"))
        td = agg.get("total")
        return round(td.total_seconds() / 3600, 2) if td else 0.0

    context = {
        "today_count": today_qs.count(),
        "month_count": month_qs.count(),
        "today_hours": sum_hours(today_qs),
        "month_hours": sum_hours(month_qs),
        "by_author": qs_all.values("author__username").annotate(cnt=Count("id")).order_by("-cnt")[:5],
    }
    return render(request, "reports/dashboard.html", context)


@login_required
def dashboard_data(request: HttpRequest) -> JsonResponse:
    """ダッシュボードの各種カード・グラフ用データを返すAPI（テンプレ側で fetch する）"""
    today = datetime.now().date()
    date_field = _detect_report_date_field()

    qs = Report.objects.all()
    if date_field:
        today_qs = qs.filter(**{f"{date_field}__date": today})
        month_qs = qs.filter(**{f"{date_field}__date__gte": today.replace(day=1)})
    else:
        today_qs = Report.objects.none()
        month_qs = qs

    # 著者別件数
    by_user = list(qs.values("author__username").annotate(count=Count("id")).order_by("-count"))

    # 進捗別件数
    names = {f.name for f in Report._meta.get_fields()}
    by_progress = []
    if "progress" in names:
        by_progress = list(qs.values("progress").annotate(count=Count("id")).order_by("-count"))

    # 集計
    cards = {
        "user_total_count": qs.count(),
        "group_total_count": month_qs.count(),
        "achievement_rate": round((today_qs.count() / month_qs.count()) * 100, 1) if month_qs.exists() else 0.0,
    }

    return JsonResponse({
        "ok": True,
        "cards": cards,
        "charts": {
            "by_user": by_user,
            "by_progress": by_progress,
        }
    })


# =========================
# Voice Logger
# =========================
@login_required
def voice_logger(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "reports/voice_logger.html",
        {"api_token": getattr(settings, "FIELDNOTE_API_TOKEN", "devtoken")},
    )


# =========================
# API（NeoInfinity→FieldNote 連携 / Azure TTS）
# =========================
def _auth_ok(request: HttpRequest) -> bool:
    expect = getattr(settings, "FIELDNOTE_API_TOKEN", "")
    token = (request.headers.get("Authorization") or "").replace("Bearer", "").strip()
    return bool(expect) and token == expect


def _parse_iso_dt(s: str) -> Optional[datetime]:
    if not s:
        return None
    try:
        s2 = s.strip().replace("Z", "+00:00")
        return datetime.fromisoformat(s2)
    except Exception:
        return None


def _decode_json_body(request: HttpRequest) -> dict:
    body: bytes = request.body or b""
    enc = (request.encoding or "utf-8").lower()
    if enc.startswith("utf-8"):
        enc = "utf-8-sig"
    try:
        return json.loads(body.decode(enc))
    except Exception:
        return json.loads(body.decode("utf-8-sig"))


def _ts_field_is_datetime() -> bool:
    try:
        f: Field = VoiceLog._meta.get_field("ts")
        return f.get_internal_type() in ("DateTimeField",)
    except Exception:
        return False


@csrf_exempt
def api_voice_logs(request: HttpRequest) -> HttpResponse:
    if not _auth_ok(request):
        return JsonResponse({"ok": False, "error": "unauthorized"}, status=401)

    if request.method == "POST":
        try:
            data = _decode_json_body(request)
        except Exception:
            return JsonResponse({"ok": False, "error": "invalid_json"}, status=400)

        text = (data.get("text") or "").strip()
        if not text:
            return JsonResponse({"ok": False, "error": "text_required"}, status=400)

        ts_in = data.get("ts")
        if ts_in in ("", None):
            ts_dt = timezone.now()
        elif isinstance(ts_in, str):
            ts_dt = _parse_iso_dt(ts_in) or timezone.now()
        else:
            ts_dt = ts_in

        if _ts_field_is_datetime():
            ts_store = ts_dt
        else:
            ts_store = timezone.localtime(ts_dt, timezone.get_fixed_timezone(9 * 60)).isoformat()

        when_in = data.get("when")
        if isinstance(when_in, str) and when_in:
            try:
                when_val: Optional[date] = datetime.fromisoformat(when_in).date()
            except Exception:
                when_val = None
        else:
            when_val = when_in

        idem = (request.headers.get("Idempotency-Key") or data.get("id") or "").strip()
        cache_key = None
        if idem:
            cache_key = f"voice_idem:{hashlib.sha256(idem.encode()).hexdigest()}"
            existed = cache.get(cache_key)
            if existed:
                return JsonResponse({"ok": True, "id": existed, "duplicate": True}, status=201)

        obj = VoiceLog.objects.create(
            text=text,
            intent=(data.get("intent") or "note"),
            ts=ts_store,
            lat=data.get("lat"),
            lon=data.get("lon"),
            amount=data.get("amount"),
            customer=(data.get("customer") or None) or None,
            when=when_val,
        )
        if cache_key:
            cache.set(cache_key, obj.id, timeout=3600)
        return JsonResponse({"ok": True, "id": obj.id}, status=201)

    # GET: 最新 n 件を返す
    try:
        limit = int(request.GET.get("limit", "20"))
    except ValueError:
        limit = 20
    limit = max(1, min(100, limit))

    jst = timezone.get_fixed_timezone(9 * 60)
    is_dt = _ts_field_is_datetime()
    items = []
    for o in VoiceLog.objects.order_by("-id")[:limit]:
        ts_out: Optional[str] = None
        if is_dt:
            if isinstance(o.ts, datetime):
                ts_out = timezone.localtime(o.ts, jst).isoformat()
        else:
            if isinstance(o.ts, str) and o.ts.strip():
                dtp = _parse_iso_dt(o.ts)
                if dtp:
                    ts_out = timezone.localtime(dtp, jst).isoformat()
        if ts_out is None and isinstance(o.created_at, datetime):
            ts_out = timezone.localtime(o.created_at, jst).isoformat()
        items.append({
            "id": o.id,
            "text": o.text,
            "intent": o.intent,
            "ts": ts_out,
            "lat": o.lat,
            "lon": o.lon,
            "amount": o.amount,
            "customer": o.customer,
            "when": o.when,
            "created_at": o.created_at,
        })
    return JsonResponse({"ok": True, "items": items})


@csrf_exempt
@require_GET
def api_envcheck(request: HttpRequest) -> HttpResponse:
    key = getattr(settings, "AZURE_SPEECH_KEY", "") or os.getenv("AZURE_SPEECH_KEY", "")
    region = getattr(settings, "AZURE_SPEECH_REGION", "") or os.getenv("AZURE_SPEECH_REGION", "")
    voice = getattr(settings, "AZURE_SPEECH_VOICE", "") or os.getenv("AZURE_SPEECH_VOICE", "")

    def ascii_ok(s: str) -> bool:
        try:
            (s or "").encode("ascii")
            return True
        except UnicodeEncodeError:
            return False

    data = {
        "ok": True,
        "env": {
            "AZURE_SPEECH_KEY_set": bool(key),
            "AZURE_SPEECH_KEY_ascii": ascii_ok(key),
            "AZURE_SPEECH_REGION": region or None,
            "AZURE_SPEECH_VOICE": voice or None,
        },
    }
    return JsonResponse(data)


def _get_azure_key_and_region() -> tuple[str, str]:
    key = getattr(settings, "AZURE_SPEECH_KEY", "") or os.getenv("AZURE_SPEECH_KEY", "")
    region = getattr(settings, "AZURE_SPEECH_REGION", "") or os.getenv("AZURE_SPEECH_REGION", "japaneast")
    return key, region


@csrf_exempt
@require_POST
def api_tts(request: HttpRequest) -> HttpResponse:
    try:
        data = _decode_json_body(request)
    except Exception:
        return HttpResponseBadRequest("invalid json")

    text = (data.get("text") or "").strip()
    if not text:
        return HttpResponseBadRequest("text required")

    key, region = _get_azure_key_and_region()
    if not key:
        return JsonResponse({"ok": False, "reason": "azure_not_configured"}, status=400)

    try:
        key.encode("ascii")
    except UnicodeEncodeError:
        return JsonResponse(
            {"ok": False, "reason": "invalid_key_non_ascii", "hint": "AZURE_SPEECH_KEY に全角/日本語が含まれています。実キーを設定してください。"},
            status=400,
        )

    voice = (data.get("voice") or getattr(settings, "AZURE_SPEECH_VOICE", "") or "ja-JP-NanamiNeural")
    style = (data.get("style") or "")
    degree = data.get("styledegree", None)
    rate_in = data.get("rate", "-6%")
    pitch = str(data.get("pitch", "+1%"))
    fmt = data.get("format", "audio-24khz-48kbitrate-mono-mp3")
    rate = f"{rate_in:.0f}%" if isinstance(rate_in, (int, float)) else str(rate_in)

    prosody = f"<prosody rate='{rate}' pitch='{pitch}'>{_esc(text)}</prosody>"
    if style:
        attrs = [f"style='{style}'"]
        if degree is not None:
            attrs.append(f"styledegree='{degree}'")
        attr_str = " ".join(attrs)
        express = f"<mstts:express-as {attr_str}>{prosody}</mstts:express-as>"
    else:
        express = prosody

    ssml = (
        "<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' "
        "xmlns:mstts='https://www.w3.org/2001/mstts' xml:lang='ja-JP'>"
        f"<voice xml:lang='ja-JP' name='{voice}'>{express}</voice>"
        "</speak>"
    ).encode("utf-8")

    url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
    headers = {
        "Ocp-Apim-Subscription-Key": key,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": fmt,
        "User-Agent": "FieldNote-VoiceLogger",
    }
    try:
        r = requests.post(url, headers=headers, data=ssml, timeout=15)
    except requests.RequestException as e:
        return HttpResponseServerError(f"azure request failed: {e}")

    if r.status_code != 200:
        return HttpResponseBadRequest(f"azure error: {r.status_code} {r.text}")

    return HttpResponse(r.content, content_type=r.headers.get("Content-Type", "audio/mpeg"))


@csrf_exempt
@require_POST
def tts_save_api(request: HttpRequest) -> HttpResponse:
    try:
        data = _decode_json_body(request)
    except Exception:
        return JsonResponse({"ok": False, "reason": "invalid_json"}, status=400)

    text = (data.get("text") or "").strip()
    if not text:
        return JsonResponse({"ok": False, "reason": "empty_text"}, status=400)

    key, region = _get_azure_key_and_region()
    if not key:
        return JsonResponse({"ok": False, "reason": "azure_not_configured"}, status=500)

    try:
        key.encode("ascii")
    except UnicodeEncodeError:
        return JsonResponse({"ok": False, "reason": "invalid_key_non_ascii"}, status=400)

    voice = (data.get("voice") or getattr(settings, "AZURE_SPEECH_VOICE", "") or "ja-JP-NanamiNeural").strip()
    fmt = (data.get("format") or "audio-24khz-48kbitrate-mono-mp3").strip()

    if synthesize_mp3 is None:
        return JsonResponse({"ok": False, "reason": "azure_tts_not_imported"}, status=501)

    try:
        audio_bytes = synthesize_mp3(text=text, region=region, key=key, voice=voice, fmt=fmt)
    except Exception as e:
        return JsonResponse({"ok": False, "reason": "azure_error", "detail": str(e)}, status=502)

    now = dt.datetime.now()
    rel_dir = Path("tts") / f"{now:%Y}" / f"{now:%m}" / f"{now:%d}"
    filename = f"{now:%H%M%S}_{uuid.uuid4().hex}.mp3"
    rel_path = rel_dir / filename
    saved_path = default_storage.save(str(rel_path), ContentFile(audio_bytes))
    relative = settings.MEDIA_URL.rstrip("/") + "/" + saved_path.replace("\\", "/")
    url = request.build_absolute_uri(relative)
    return JsonResponse({"ok": True, "url": url, "path": saved_path})


@csrf_exempt
@require_GET
def api_voices(request: HttpRequest) -> HttpResponse:
    key, region = _get_azure_key_and_region()
    if not key:
        return JsonResponse({"ok": False, "reason": "azure_not_configured"}, status=400)
    try:
        key.encode("ascii")
    except UnicodeEncodeError:
        return JsonResponse({"ok": False, "reason": "invalid_key_non_ascii"}, status=400)

    url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/voices/list"
    headers = {"Ocp-Apim-Subscription-Key": key, "User-Agent": "FieldNote-VoiceLogger"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
    except requests.RequestException as e:
        return HttpResponseServerError(f"azure request failed: {e}")

    if r.status_code != 200:
        return HttpResponseBadRequest(f"azure error: {r.status_code} {r.text}")

    try:
        arr = r.json()
    except Exception:
        return HttpResponseServerError("invalid response from azure")

    return JsonResponse(arr, safe=False)


# =========================
# PDF View (Placeholder)
# =========================
@login_required
def report_pdf_view(request, pk):
    """
    PDF表示用の仮ビュー。
    urls.pyからの参照エラーを防ぐために配置。
    """
    report = get_object_or_404(Report, pk=pk)

    html_content = f"""
    <html>
    <body>
        <h1>日報PDF (未実装)</h1>
        <p>これは日報ID: {report.pk} のためのPDFです。</p>
        <p>報告者: {report.author.username}</p>
        <p>場所: {report.location}</p>
        <p>内容:</p>
        <pre>{report.content}</pre>
    </body>
    </html>
    """
    return HttpResponse(html_content)
