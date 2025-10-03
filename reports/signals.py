# reports/signals.py
from __future__ import annotations
import os
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Report, RequiredItem  # ← 既存モデル名を想定
from .utils.need_extractor import extract_needed_items

def _field_exists(model, field: str) -> bool:
    return field in {f.name for f in model._meta.get_fields() if hasattr(f, "name")}

def _safe_set(instance, field: str, value):
    if _field_exists(type(instance), field):
        setattr(instance, field, value)

def _compose_text(report: Report) -> str:
    """
    Report から抽出対象の本文を合成。
    例: report.content / report.remarks / report.memo 等、存在すれば連結。
    """
    parts = []
    for name in ("content", "remarks", "memo", "note", "notes", "detail", "description"):
        if hasattr(report, name):
            v = getattr(report, name) or ""
            if v:
                parts.append(str(v))
    return "\n".join(parts)

def _create_required_item_from_extraction(report: Report, name: str, qty, unit, src_note: str):
    """
    RequiredItem を安全に作成（存在フィールドのみセット）
    """
    # 重複防止キー：同一レポート×同名×単位（24h以内で同一はスキップ等、必要なら追加ロジック）
    existing_qs = RequiredItem.objects.filter(name=name)
    if _field_exists(RequiredItem, "source_report"):
        existing_qs = existing_qs.filter(source_report=report)
    elif _field_exists(RequiredItem, "source_id"):
        existing_qs = existing_qs.filter(source_id=report.pk)

    if existing_qs.exists():
        return  # 既に登録済みとみなす（必要なら数量加算などに変更可）

    item = RequiredItem()
    # 必須に近い
    if _field_exists(RequiredItem, "name"):
        item.name = name
    else:
        # name フィールドが無い場合に備えて title があるなら代用
        _safe_set(item, "title", name)

    # 数量/単位があれば反映
    if qty is not None:
        _safe_set(item, "quantity", qty)
    if unit:
        _safe_set(item, "unit", unit)

    # 状態のデフォルト（choicesがある場合は未手配/未着手に相当する値を使う）
    for f in ("status", "procurement_status", "state"):
        if _field_exists(RequiredItem, f) and getattr(item, f, None) in (None, ""):
            # 未手配/未着手っぽい既定値（無ければ空のまま）
            try:
                setattr(item, f, getattr(RequiredItem, f.upper() + "_CHOICES")[0][0])  # 選択肢先頭など
            except Exception:
                pass

    # 紐づけ
    if _field_exists(RequiredItem, "source_report"):
        item.source_report = report
    elif _field_exists(RequiredItem, "report"):
        item.report = report
    elif _field_exists(RequiredItem, "source_id"):
        item.source_id = report.pk

    # メモ/備考へ出典を残す
    msg = f"[自動抽出] {timezone.localtime().strftime('%Y-%m-%d %H:%M')} / report_id={report.pk} / 原文: {src_note}"
    for f in ("memo", "note", "notes", "remark", "remarks", "description"):
        if _field_exists(RequiredItem, f):
            cur = getattr(item, f, "") or ""
            setattr(item, f, (cur + ("\n" if cur else "") + msg))
            break

    item.save()

@receiver(post_save, sender=Report)
def report_post_save_autofill_required_items(sender, instance: Report, created, **kwargs):
    """
    Report 保存後、自動で本文を解析し RequiredItem を起票。
    環境変数 REQUIREMENTS_AUTOFILL が truthy のとき有効。
    """
    if os.environ.get("REQUIREMENTS_AUTOFILL", "1").lower() not in ("1", "true", "yes", "on"):
        return

    text = _compose_text(instance)
    if not text:
        return

    items = extract_needed_items(text)
    for it in items:
        _create_required_item_from_extraction(
            report=instance,
            name=it.name,
            qty=it.quantity,
            unit=it.unit,
            src_note=it.note or "",
        )
