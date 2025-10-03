# -*- coding: utf-8 -*-
"""
voice_logs/views.py
- /api/voice-logs/ : POST/GET の簡易API（Bearerトークン認証、Idempotency-Key対応）
- /api/tts/        : （任意）Azure TTS プロキシ
"""

from __future__ import annotations

import json
import hashlib
from datetime import datetime, date
from typing import Optional

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import Field

# ---- VoiceLog モデルは reports 側を使用（INSTALLED_APPS に voice_logs を入れなくてOK） ----
from reports.models import VoiceLog


# ------------------------------------------------------------
# 認可（超シンプル Bearer）
# ------------------------------------------------------------
def _auth_ok(request: HttpRequest) -> bool:
    """
    Authorization: Bearer <token> が settings.FIELDNOTE_API_TOKEN と一致するかを判定。
    """
    expect = getattr(settings, "FIELDNOTE_API_TOKEN", "")
    token = (request.headers.get("Authorization") or "").replace("Bearer", "").strip()
    return bool(expect) and token == expect


# ------------------------------------------------------------
# ISO8601 パース
# ------------------------------------------------------------
def _parse_iso_dt(s: str) -> Optional[datetime]:
    """
    '2025-09-29T09:16:43.315+09:00' / '2025-09-29T00:16:43Z' / '2025-09-29 09:16:43'
    のような文字列をなるべく素直に解釈。失敗で None。
    """
    if not s:
        return None
    try:
        s2 = s.strip().replace("Z", "+00:00")
        return datetime.fromisoformat(s2)
    except Exception:
        return None


# ------------------------------------------------------------
# JSON デコード（BOM/charset 耐性）
# ------------------------------------------------------------
def _decode_json_body(request: HttpRequest) -> dict:
    """
    Content-Type の charset を尊重して JSON を読む。
    - UTF-8 の場合は BOM 対応の 'utf-8-sig' で decode
    - それ以外は request.encoding を信頼（無ければ utf-8-sig）
    """
    body: bytes = request.body or b""
    enc = (request.encoding or "utf-8").lower()
    if enc.startswith("utf-8"):
        enc = "utf-8-sig"
    try:
        return json.loads(body.decode(enc))
    except Exception:
        # まれに charset が嘘のクライアントがあるため、最後に utf-8-sig でも再挑戦
        return json.loads(body.decode("utf-8-sig"))


# ------------------------------------------------------------
# ts フィールドの型を動的に判定（DateTimeField かどうか）
# ------------------------------------------------------------
def _ts_field_is_datetime() -> bool:
    try:
        f: Field = VoiceLog._meta.get_field("ts")
        return f.get_internal_type() in ("DateTimeField",)
    except Exception:
        return False


# ------------------------------------------------------------
# API: /api/voice-logs/
# ------------------------------------------------------------
@csrf_exempt
def api_voice_logs(request: HttpRequest) -> HttpResponse:
    """
    POST: JSON 保存（Idempotency-Key対応）
          -> 201 Created + {ok:true, id:int}
    GET : 直近一覧（ts は JST ISO8601 で返却。文字列保存や空の過去データも見栄え補正）
          -> 200 OK + {ok:true, items:[...]}
    """
    if not _auth_ok(request):
        return JsonResponse({"ok": False, "error": "unauthorized"}, status=401)

    # ----- POST: 保存 -----
    if request.method == "POST":
        try:
            data = _decode_json_body(request)
        except Exception:
            return JsonResponse({"ok": False, "error": "invalid_json"}, status=400)

        text = (data.get("text") or "").strip()
        if not text:
            return JsonResponse({"ok": False, "error": "text_required"}, status=400)

        # ts: 空/未指定なら現在時刻、文字列なら ISO8601 としてパース。失敗時は現在時刻。
        ts_in = data.get("ts")
        if ts_in in ("", None):
            ts_dt = timezone.now()
        elif isinstance(ts_in, str):
            ts_dt = _parse_iso_dt(ts_in) or timezone.now()
        else:
            # すでに datetime が来ている想定
            ts_dt = ts_in

        # モデルの ts フィールド型に応じて保存値を決定
        if _ts_field_is_datetime():
            ts_store = ts_dt  # DateTimeField ならそのまま datetime で保存
        else:
            # CharField/TextField 等なら ISO8601（JST）文字列で保存
            ts_store = timezone.localtime(
                ts_dt, timezone.get_fixed_timezone(9 * 60)
            ).isoformat()

        # when: 文字列なら日付として解釈（失敗は None）
        when_in = data.get("when")
        if isinstance(when_in, str) and when_in:
            try:
                when_val: Optional[date] = datetime.fromisoformat(when_in).date()
            except Exception:
                when_val = None
        else:
            when_val = when_in

        # 冪等キー（同一キーは同一IDを返す）
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

    # ----- GET: 一覧 -----
    try:
        limit = int(request.GET.get("limit", "20"))
    except ValueError:
        limit = 20
    limit = max(1, min(100, limit))

    items = []
    jst = timezone.get_fixed_timezone(9 * 60)  # +09:00
    is_dt_field = _ts_field_is_datetime()

    for o in VoiceLog.objects.order_by("-id")[:limit]:
        ts_out: Optional[str] = None

        if is_dt_field:
            # DateTimeField の場合：datetime が入っていれば JST ISO8601 に
            if isinstance(o.ts, datetime):
                ts_out = timezone.localtime(o.ts, jst).isoformat()
        else:
            # 文字列保存の場合：parse を試み、成功すれば JST ISO8601 に
            if isinstance(o.ts, str) and o.ts.strip():
                dt = _parse_iso_dt(o.ts)
                if dt:
                    ts_out = timezone.localtime(dt, jst).isoformat()

        # ts が空/不明なら created_at を代用（JST）
        if ts_out is None and isinstance(o.created_at, datetime):
            ts_out = timezone.localtime(o.created_at, jst).isoformat()

        items.append({
            "id": o.id,
            "text": o.text,
            "intent": o.intent,
            "ts": ts_out,               # JST の ISO8601 文字列（なければ created_at で補完）
            "lat": o.lat,
            "lon": o.lon,
            "amount": o.amount,
            "customer": o.customer,
            "when": o.when,
            "created_at": o.created_at,  # 必要なら .isoformat() に変更可
        })

    return JsonResponse({"ok": True, "items": items})


# ------------------------------------------------------------
# API: /api/tts/  （任意機能・使うときだけ urls.py で有効化）
# ------------------------------------------------------------
@csrf_exempt
@require_POST
def api_tts(request: HttpRequest) -> HttpResponse:
    """
    Azure TTS を叩いて音声を返す（キー未設定時は JSON で理由を返す）
    """
    import requests

    # JSON 受け取り
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"ok": False, "error": "invalid_json"}, status=400)

    text = (data.get("text") or "").strip()
    if not text:
        return JsonResponse({"ok": False, "error": "text_required"}, status=400)

    key = getattr(settings, "AZURE_SPEECH_KEY", "") or ""
    if not key:
        return JsonResponse({"ok": False, "reason": "azure_not_configured"}, status=400)

    region = getattr(settings, "AZURE_SPEECH_REGION", "japaneast")
    voice = (data.get("voice") or "ja-JP-NanamiNeural")
    style = (data.get("style") or "")
    degree = data.get("styledegree", None)
    rate_in = data.get("rate", "-6%")
    pitch = str(data.get("pitch", "+1%"))
    fmt = data.get("format", "audio-24khz-48kbitrate-mono-mp3")

    rate = f"{rate_in:.0f}%" if isinstance(rate_in, (int, float)) else str(rate_in)

    # --- SSML 組み立て（安全な属性連結） ---
    def _esc(s: str) -> str:
        return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

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
        "<speak version='1.0' "
        "xmlns='http://www.w3.org/2001/10/synthesis' "
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
        return JsonResponse({"ok": False, "error": f"azure_request_failed: {e}"}, status=500)

    if r.status_code != 200:
        return JsonResponse({"ok": False, "error": f"azure_error {r.status_code}: {r.text}"}, status=400)

    return HttpResponse(r.content, content_type=r.headers.get("Content-Type", "audio/mpeg"))
