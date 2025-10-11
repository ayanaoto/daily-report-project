# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from typing import Optional, Iterable
from django.db.models import Q, Model, QuerySet, CharField, TextField
from django.http import HttpResponse
from django.utils.encoding import smart_str
import csv

DATE_FIELD_CANDIDATES = ["date", "report_date", "created_at", "updated_at"]

def _detect_date_field(model_cls) -> Optional[str]:
    names = {f.name for f in model_cls._meta.get_fields()}
    for cand in DATE_FIELD_CANDIDATES:
        if cand in names:
            return cand
    return None

def _text_field_names(model_cls) -> Iterable[str]:
    for f in model_cls._meta.get_fields():
        if isinstance(getattr(f, "remote_field", None), object) and getattr(f.remote_field, "model", None):
            continue  # 外部キーの name ではなく文字列フィールドだけ
        if isinstance(getattr(f, "target_field", f), (CharField, TextField)):
            yield f.name

def filter_queryset(qs: QuerySet, request) -> tuple[QuerySet, dict]:
    """start/end/q を用いた安全なフィルタ。存在しないフィールドには触れない。"""
    model_cls = qs.model
    params = {
        "start": (request.GET.get("start") or "").strip(),
        "end": (request.GET.get("end") or "").strip(),
        "q": (request.GET.get("q") or "").strip(),
    }

    # 日付フィールド検出
    date_field = _detect_date_field(model_cls)
    if date_field:
        if params["start"]:
            try:
                dt = datetime.fromisoformat(params["start"])
                qs = qs.filter(**{f"{date_field}__date__gte": dt.date()})
            except ValueError:
                pass
        if params["end"]:
            try:
                dt = datetime.fromisoformat(params["end"])
                qs = qs.filter(**{f"{date_field}__date__lte": dt.date()})
            except ValueError:
                pass

    # キーワード全文検索（Char/Text をまとめて OR）
    if params["q"]:
        q = Q()
        for name in _text_field_names(model_cls):
            q |= Q(**{f"{name}__icontains": params["q"]})
        if q:
            qs = qs.filter(q)

    return qs, params

class FilteredListMixin:
    """ListView で使うと、?start&end&q を自動適用します。"""
    def get_queryset(self):
        qs = super().get_queryset()
        qs, _ = filter_queryset(qs, self.request)
        return qs

def export_queryset_to_csv(qs: QuerySet, filename: str = "reports.csv") -> HttpResponse:
    """クエリセットを “全カラム動的” でCSV化。"""
    model_cls = qs.model
    fields = [f for f in model_cls._meta.fields]  # Concrete fields
    headers = [f.name for f in fields]

    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(resp)
    writer.writerow(headers)
    for obj in qs.iterator():
        row = []
        for f in fields:
            val = getattr(obj, f.name, "")
            row.append(smart_str(val))
        writer.writerow(row)
    return resp
