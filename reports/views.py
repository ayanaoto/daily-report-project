# reports/views.py
from __future__ import annotations

import csv
import io
import json
import os
import uuid
from datetime import datetime, timedelta, date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.base import ContentFile
from django.db.models import Q
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

# ---- .env ロード（保険） ----
try:
    from dotenv import load_dotenv
    load_dotenv(override=False)
except Exception:
    pass

# ---- アプリ内 import ----
from .forms import (
    CustomerForm,
    DealForm,
    ProfileForm,
    ReportAttachmentFormSet,
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

# Azure TTS ユーティリティ（ある場合のみ）
try:
    from .utils.azure_tts import synthesize_mp3  # (text:str, voice:str) -> bytes
except Exception:
    synthesize_mp3 = None


# =========================
# 共通ユーティリティ
# =========================

def _names(model) -> set[str]:
    return {f.name for f in model._meta.get_fields()}

def _detect_report_date_field() -> str | None:
    names = _names(Report)
    for c in ("date", "report_date", "created_at", "updated_at"):
        if c in names:
            return c
    return None

def _apply_filters_to_reports(qs, request: HttpRequest):
    start = (request.GET.get("start") or "").strip()
    end = (request.GET.get("end") or "").strip()
    q = (request.GET.get("q") or "").strip()

    date_field = _detect_report_date_field()
    if date_field:
        if start:
            try:
                qs = qs.filter(**{f"{date_field}__date__gte": datetime.fromisoformat(start).date()})
            except Exception:
                pass
        if end:
            try:
                qs = qs.filter(**{f"{date_field}__date__lte": datetime.fromisoformat(end).date()})
            except Exception:
                pass

    if q:
        names = _names(Report)
        qq = Q()
        for f in ("title", "location", "content", "remarks"):
            if f in names:
                qq |= Q(**{f"{f}__icontains": q})
        if qq:
            qs = qs.filter(qq)

    return qs

def _apply_ordering_to_reports(qs, request: HttpRequest):
    """?sort=created|-created|id|-id|author|-author"""
    sort = (request.GET.get("sort") or "").strip()
    names = _names(Report)
    mapping = {
        "created": "created_at" if "created_at" in names else "id",
        "-created": "-created_at" if "created_at" in names else "-id",
        "id": "id",
        "-id": "-id",
        "author": "author__username",
        "-author": "-author__username",
    }
    key = mapping.get(sort)
    if key:
        return qs.order_by(key)
    # 既定は新着順
    return qs.order_by("-created_at") if "created_at" in names else qs.order_by("-id")


# =========================
# アカウント
# =========================

class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("reports:report_list")

    def form_valid(self, form):
        r = super().form_valid(form)
        login(self.request, form.instance)
        return r


@login_required
def profile_update(request: HttpRequest) -> HttpResponse:
    profile = getattr(request.user, "profile", None)
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "プロフィールを保存しました。")
            return redirect("reports:report_list")
    else:
        form = ProfileForm(instance=profile)
    return render(request, "reports/profile_form.html", {"form": form})


# =========================
# Reports 一覧/詳細/作成/編集/削除/CSV
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
        except Exception:
            pass
        return super().get_paginate_by(queryset)

    def get_queryset(self):
        user = self.request.user
        qs = Report.objects.all() if user.is_superuser else Report.objects.filter(author=user)
        qs = _apply_filters_to_reports(qs, self.request)
        qs = _apply_ordering_to_reports(qs, self.request)
        return qs


class ReportDetailView(LoginRequiredMixin, DetailView):
    model = Report
    template_name = "reports/report_detail.html"

    def get_queryset(self):
        user = self.request.user
        return Report.objects.all() if user.is_superuser else Report.objects.filter(author=user)


class ReportCreateView(LoginRequiredMixin, CreateView):
    model = Report
    form_class = ReportForm
    template_name = "reports/report_form.html"
    success_url = reverse_lazy("reports:report_list")  # フォールバック

    def get_initial(self):
        initial = super().get_initial()
        today = date.today()
        names = _names(Report)
        if "date" in names:
            initial.setdefault("date", today)
        if "report_date" in names:
            initial.setdefault("report_date", today)
        initial.setdefault("hours", 0)
        initial.setdefault("minutes", 0)
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx["att_formset"] = ReportAttachmentFormSet(self.request.POST, self.request.FILES)
        else:
            ctx["att_formset"] = ReportAttachmentFormSet()
        return ctx

    def form_valid(self, form):
        form.instance.author = self.request.user
        # 時分 → work_hours がある場合はそこへ
        hours = form.cleaned_data.get("hours") or 0
        minutes = form.cleaned_data.get("minutes") or 0
        if hasattr(form.instance, "work_hours"):
            form.instance.work_hours = timedelta(hours=hours, minutes=minutes)

        r = super().form_valid(form)

        # 添付ファイル
        formset = ReportAttachmentFormSet(self.request.POST, self.request.FILES, instance=self.object)
        if formset.is_valid():
            formset.save()
        else:
            messages.warning(self.request, "一部の添付ファイルに不備があります。")

        messages.success(self.request, "日報を作成しました。")
        return r

    def get_success_url(self):
        # 作成後は詳細へ → すぐ再編集できる
        return reverse_lazy("reports:report_detail", kwargs={"pk": self.object.pk})


class ReportUpdateView(LoginRequiredMixin, UpdateView):
    model = Report
    form_class = ReportForm
    template_name = "reports/report_form.html"

    def get_queryset(self):
        user = self.request.user
        return Report.objects.all() if user.is_superuser else Report.objects.filter(author=user)

    def get_initial(self):
        initial = super().get_initial()
        # work_hours → 時分
        wh = getattr(self.object, "work_hours", None)
        if wh:
            sec = int(wh.total_seconds())
            initial["hours"] = sec // 3600
            initial["minutes"] = (sec % 3600) // 60
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx["att_formset"] = ReportAttachmentFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            ctx["att_formset"] = ReportAttachmentFormSet(instance=self.object)
        return ctx

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        formset = ReportAttachmentFormSet(self.request.POST, self.request.FILES, instance=self.object)
        if form.is_valid() and formset.is_valid():
            hours = form.cleaned_data.get("hours") or 0
            minutes = form.cleaned_data.get("minutes") or 0
            if hasattr(form.instance, "work_hours"):
                form.instance.work_hours = timedelta(hours=hours, minutes=minutes)
            self.object = form.save()
            formset.save()
            messages.success(self.request, "日報を更新しました。")
            return redirect(self.get_success_url())
        messages.warning(self.request, "入力内容に誤りがあります。")
        return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy("reports:report_detail", kwargs={"pk": self.object.pk})


class ReportDeleteView(LoginRequiredMixin, DeleteView):
    model = Report
    template_name = "reports/report_confirm_delete.html"
    success_url = reverse_lazy("reports:report_list")

    def get_queryset(self):
        user = self.request.user
        return Report.objects.all() if user.is_superuser else Report.objects.filter(author=user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "日報を削除しました。")
        return super().delete(request, *args, **kwargs)


@login_required
def report_export_csv(request: HttpRequest) -> HttpResponse:
    user = request.user
    qs = Report.objects.all() if user.is_superuser else Report.objects.filter(author=user)
    qs = _apply_filters_to_reports(qs, request)
    qs = _apply_ordering_to_reports(qs, request)

    # ダンプするカラムを決める（存在するものだけ）
    names = _names(Report)
    cols = [c for c in ("id", "created_at", "date", "report_date", "title", "location", "content", "remarks", "author") if c in names]

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(cols)
    for r in qs:
        row = []
        for c in cols:
            v = getattr(r, c, "")
            if c in ("created_at", "date", "report_date") and v:
                try:
                    v = v.strftime("%Y-%m-%d %H:%M" if hasattr(v, "hour") else "%Y-%m-%d")
                except Exception:
                    pass
            row.append(str(v) if v is not None else "")
        w.writerow(row)

    resp = HttpResponse(buf.getvalue(), content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = 'attachment; filename="reports.csv"'
    return resp


# =========================
# Dashboard（簡易）
# =========================

@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    user = request.user
    qs = Report.objects.all() if user.is_superuser else Report.objects.filter(author=user)
    qs = _apply_filters_to_reports(qs, request)

    total = qs.count()
    latest = qs.order_by("-id")[:10]
    return render(request, "reports/dashboard.html", {
        "total": total,
        "latest": latest,
    })


# =========================
# Customers
# =========================

class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = "reports/customer_list.html"
    context_object_name = "customers"


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


# =========================
# Deals
# =========================

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
    context_object_name = "items"


class TroubleshootingDetailView(LoginRequiredMixin, DetailView):
    model = Troubleshooting
    template_name = "reports/troubleshooting_detail.html"


class TroubleshootingCreateView(LoginRequiredMixin, CreateView):
    model = Troubleshooting
    form_class = TroubleshootingForm
    template_name = "reports/troubleshooting_form.html"
    success_url = reverse_lazy("reports:troubleshooting_list")


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
# ToDo（RequiredItem）
# =========================

class TodoListView(LoginRequiredMixin, ListView):
    model = RequiredItem
    template_name = "reports/todo_list.html"
    context_object_name = "items"

class TodoCreateView(LoginRequiredMixin, CreateView):
    model = RequiredItem
    form_class = RequiredItemForm
    template_name = "reports/todo_form.html"
    success_url = reverse_lazy("reports:todo_list")

class TodoUpdateView(LoginRequiredMixin, UpdateView):
    model = RequiredItem
    form_class = RequiredItemForm
    template_name = "reports/todo_form.html"
    success_url = reverse_lazy("reports:todo_list")

class TodoDeleteView(LoginRequiredMixin, DeleteView):
    model = RequiredItem
    template_name = "reports/todo_confirm_delete.html"
    success_url = reverse_lazy("reports:todo_list")

@login_required
def todo_toggle(request: HttpRequest, pk: int) -> HttpResponse:
    item = get_object_or_404(RequiredItem, pk=pk)
    item.is_done = not bool(item.is_done)
    item.save(update_fields=["is_done"])
    messages.success(request, "完了状態を切り替えました。")
    return redirect("reports:todo_list")

@login_required
def todo_export_csv(request: HttpRequest) -> HttpResponse:
    qs = RequiredItem.objects.all().order_by("-id")
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "title", "deal", "is_done"])
    for r in qs:
        w.writerow([r.id, r.title, getattr(r.deal, "deal_name", ""), "1" if r.is_done else "0"])
    resp = HttpResponse(buf.getvalue(), content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = 'attachment; filename="todo.csv"'
    return resp


# =========================
# Voice Logger（ページ）
# =========================

@login_required
def voice_logger(request: HttpRequest) -> HttpResponse:
    return render(request, "reports/voice_logger.html")


# =========================
# API: Voice Logs
# =========================

@csrf_exempt
@require_POST
def api_voice_logs(request: HttpRequest) -> JsonResponse:
    """
    JSON 例:
    {
      "text": "現場到着、作業開始",
      "intent": "note",
      "ts": "2025-01-01T10:00:00+09:00",
      "lat": 35.0, "lon": 139.0,
      "amount": 1200,
      "customer": "ACME",
      "when": "今日の午前",
      "audio_b64": "data:audio/webm;base64,...."  # 任意
    }
    """
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"ok": False, "reason": "invalid_json"}, status=400)

    vo = VoiceLog()
    for f in ("text", "intent", "ts", "lat", "lon", "amount", "customer", "when"):
        if f in payload:
            setattr(vo, f, payload.get(f))

    # 音声（Base64 Data URL）
    audio_b64 = payload.get("audio_b64")
    if audio_b64 and isinstance(audio_b64, str) and ";base64," in audio_b64:
        head, b64 = audio_b64.split(";base64,", 1)
        mime = head.split(":", 1)[1] if ":" in head else "application/octet-stream"
        import base64
        try:
            blob = base64.b64decode(b64)
            ext = ".webm" if "webm" in mime else ".mp3" if "mpeg" in mime or "mp3" in mime else ".bin"
            fname = f"voicelog/{timezone.now():%Y/%m/%d}/{uuid.uuid4().hex}{ext}"
            vo.audio_file.save(fname, ContentFile(blob), save=False)
            if hasattr(vo, "mime_type"):
                vo.mime_type = mime
            if hasattr(vo, "duration_sec") and not getattr(vo, "duration_sec", None):
                vo.duration_sec = 0
        except Exception:
            pass

    vo.save()
    return JsonResponse({"ok": True, "id": vo.id})


# =========================
# API: TTS
# =========================

@csrf_exempt
@require_POST
def api_tts(request: HttpRequest) -> HttpResponse:
    """
    入力: {"text":"こんにちは","voice":"ja-JP-NanamiNeural"}
    出力: audio/mpeg（MP3）
    """
    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"ok": False, "reason": "invalid_json"}, status=400)

    text = (body.get("text") or "").strip()
    voice = (body.get("voice") or "").strip() or os.getenv("AZURE_SPEECH_VOICE") or "ja-JP-NanamiNeural"

    # Azure 設定チェック
    speech_key = os.getenv("AZURE_SPEECH_KEY") or getattr(settings, "AZURE_SPEECH_KEY", None)
    speech_region = os.getenv("AZURE_SPEECH_REGION") or getattr(settings, "AZURE_SPEECH_REGION", None)

    if not (speech_key and speech_region and synthesize_mp3):
        return JsonResponse({"ok": False, "reason": "azure_not_configured"}, status=400)

    if not text:
        return JsonResponse({"ok": False, "reason": "empty_text"}, status=400)

    try:
        blob = synthesize_mp3(text=text, voice=voice)
        resp = HttpResponse(blob, content_type="audio/mpeg")
        resp["Content-Disposition"] = 'inline; filename="tts.mp3"'
        return resp
    except Exception as e:
        return JsonResponse({"ok": False, "reason": f"azure_error:{e}"}, status=500)
