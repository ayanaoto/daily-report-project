# server.py — FastAPI + Azure Speech (TTS) 改良版
# - .env を同階層から読み込み
# - /api/envcheck : 環境チェック
# - /api/voices   : 利用可能ボイス一覧（既定 ja-JP）
# - /api/tts      : 既定 MP3(24kHz/48kbps/Mono)。payload.format で wav 等に切替可

import os
import logging
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Body, HTTPException, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import azure.cognitiveservices.speech as speechsdk

# --- .env 読み込み（server.py と同じフォルダの .env を読む） ---
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# --- Logger / FastAPI 初期化 ---
logger = logging.getLogger("uvicorn.error")
app = FastAPI(title="FieldNote TTS API", version="1.1.0")

# CORS（必要なら有効。本番は allow_origins を絞る）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: 本番は特定のオリジンに限定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 環境変数ヘルパ ---
def envs():
    """
    Retrieves necessary environment variables for Azure Speech Service.
    優先順:
      1) AZURE_SPEECH_DEFAULT_VOICE
      2) AZURE_SPEECH_VOICE
      3) 'ja-JP-NanamiNeural'（既定）
    """
    key = os.getenv("AZURE_SPEECH_KEY")
    region = os.getenv("AZURE_SPEECH_REGION")
    default_voice = (
        os.getenv("AZURE_SPEECH_DEFAULT_VOICE")
        or os.getenv("AZURE_SPEECH_VOICE")
        or "ja-JP-NanamiNeural"
    )
    return key, region, default_voice


# --- ユーティリティ：出力フォーマット選択 ---
def select_output_format(fmt: str | None):
    """
    ペイロードの format 文字列を Speech SDK の出力フォーマットに変換。
    既定: 24kHz/48kbps/Mono MP3（Windows標準で再生しやすい）
    """
    if not fmt or fmt.lower() in ("mp3", "mp3_24k", "mp3_48k", "mp3_24khz"):
        return speechsdk.SpeechSynthesisOutputFormat.Audio24Khz48KBitRateMonoMp3
    fmt = fmt.lower()
    if fmt in ("mp3_16k", "mp3_32k"):
        return speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
    if fmt in ("wav", "pcm", "wav_16k"):
        return speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm
    if fmt in ("wav_24k", "pcm_24k"):
        return speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm
    # 不明指定は既定にフォールバック
    return speechsdk.SpeechSynthesisOutputFormat.Audio24Khz48KBitRateMonoMp3


# --- ヘルス/環境チェック ---
@app.get("/api/envcheck")
def envcheck():
    key, region, voice = envs()
    return {
        "ok": True,
        "env": {
            "AZURE_SPEECH_KEY_set": bool(key),
            "AZURE_SPEECH_REGION": region,
            "AZURE_SPEECH_VOICE": voice,
        },
    }


# --- 利用可能ボイス一覧（既定は ja-JP） ---
@app.get("/api/voices")
def voices(locale: str = "ja-JP"):
    try:
        key, region, _ = envs()
        missing = []
        if not key:
            missing.append("AZURE_SPEECH_KEY")
        if not region:
            missing.append("AZURE_SPEECH_REGION")
        if missing:
            return JSONResponse(
                {"ok": False, "reason": "azure_not_configured", "missing": missing},
                status_code=500,
            )

        cfg = speechsdk.SpeechConfig(subscription=key, region=region)
        res = speechsdk.SpeechSynthesizer.get_voices_async(
            speech_config=cfg, locale=locale
        ).get()
        return {"ok": True, "count": len(res.voices), "voices": [v.short_name for v in res.voices]}
    except Exception as e:
        logger.exception("voices endpoint crashed")
        return JSONResponse(
            {"ok": False, "reason": "exception", "detail": str(e)},
            status_code=500,
        )


# --- TTS 本体 ---
@app.post("/api/tts/")
def tts(payload: dict = Body(...)):
    """
    Text-to-Speech endpoint using Azure Cognitive Services.
    payload:
      - text   : 合成する文字列（必須）
      - voice  : 省略時は env の既定（例: ja-JP-NanamiNeural）
      - format : 'mp3_24k'（既定）, 'mp3_16k', 'wav', 'wav_24k' など
    """
    try:
        key, region, default_voice = envs()

        # 必須ENVを確認
        missing = []
        if not key:
            missing.append("AZURE_SPEECH_KEY")
        if not region:
            missing.append("AZURE_SPEECH_REGION")
        if missing:
            return JSONResponse(
                {"ok": False, "reason": "azure_not_configured", "missing": missing},
                status_code=500,
            )

        # 入力
        text = (payload.get("text") or "").strip()
        voice = payload.get("voice") or default_voice
        outfmt = select_output_format(payload.get("format"))

        if not text:
            raise HTTPException(status_code=400, detail="text is required")

        # Speech SDK 設定
        speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
        speech_config.speech_synthesis_voice_name = voice
        speech_config.set_speech_synthesis_output_format(outfmt)

        # 合成（audio_config=None → メモリに出力され result.audio_data に入る）
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config, audio_config=None
        )
        result = synthesizer.speak_text_async(text).get()

        # 失敗時は詳細をJSONで返す（Unauthorized / InvalidVoice / RegionMismatch 等）
        if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
            detail = "unknown_error"
            cd = getattr(result, "cancellation_details", None)
            if cd:
                detail = getattr(cd.reason, "name", detail)
                if cd.error_details:
                    detail += f": {cd.error_details}"
            return JSONResponse(
                {"ok": False, "reason": "synthesis_failed", "detail": detail, "voice": voice},
                status_code=500,
            )

        # 正常：バイトを直接返す（Content-Type はフォーマットに応じて）
        media = (
            "audio/mpeg"
            if "Mp3" in str(outfmt)
            else "audio/wav" if "Riff" in str(outfmt) else "application/octet-stream"
        )
        filename = "tts.mp3" if media == "audio/mpeg" else "tts.wav"

        return Response(
            content=result.audio_data,
            media_type=media,
            headers={"Content-Disposition": f'inline; filename="{filename}"'},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("tts endpoint crashed")
        return JSONResponse(
            {"ok": False, "reason": "exception", "detail": str(e)},
            status_code=500,
        )


# --- 直接起動用（任意） ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
