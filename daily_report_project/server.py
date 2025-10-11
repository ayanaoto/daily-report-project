# server.py — FastAPI + Azure Speech (TTS) 安定版

from dotenv import load_dotenv
from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

import os
from fastapi import FastAPI, Body, HTTPException, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import azure.cognitiveservices.speech as speechsdk
import logging

app = FastAPI(title="FieldNote TTS API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番は絞ってください
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def envs():
    key    = os.getenv("AZURE_SPEECH_KEY")
    region = os.getenv("AZURE_SPEECH_REGION")
    voice  = os.getenv("AZURE_SPEECH_VOICE") or "ja-JP-NanamiNeural"
    return key, region, voice

@app.get("/api/envcheck")
def envcheck():
    key, region, voice = envs()
    return {"ok": True, "env": {
        "AZURE_SPEECH_KEY_set": bool(key),
        "AZURE_SPEECH_REGION": region,
        "AZURE_SPEECH_VOICE": voice,
    }}

@app.get("/api/voices")
def voices():
    key, region, _ = envs()
    missing = []
    if not key:    missing.append("AZURE_SPEECH_KEY")
    if not region: missing.append("AZURE_SPEECH_REGION")
    if missing:
        return JSONResponse({"ok": False, "reason":"azure_not_configured","missing":missing}, status_code=500)

    speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
    result = speechsdk.SpeechSynthesizer.get_voices_async(
        speech_config=speech_config, locale="ja-JP"
    ).get()
    return {"ok": True, "count": len(result.voices), "voices": [v.short_name for v in result.voices]}

logger = logging.getLogger("uvicorn.error")

@app.post("/api/tts/")
def tts(payload: dict = Body(...)):
    try:
        key, region, default_voice = envs()
        missing = []
        if not key:    missing.append("AZURE_SPEECH_KEY")
        if not region: missing.append("AZURE_SPEECH_REGION")
        if missing:
            return JSONResponse({"ok": False, "reason":"azure_not_configured","missing":missing}, status_code=500)

        text  = (payload.get("text") or "").strip()
        voice = payload.get("voice") or default_voice
        if not text:
            raise HTTPException(400, "text is required")

        speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
        speech_config.speech_synthesis_voice_name = voice
        speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
        )
        result = speechsdk.SpeechSynthesizer(speech_config=speech_config).speak_text_async(text).get()

        if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
            detail = "unknown_error"
            cd = getattr(result, "cancellation_details", None)
            if cd:
                detail = getattr(cd.reason, "name", detail)
                if cd.error_details:
                    detail += f": {cd.error_details}"
            return JSONResponse({"ok": False, "reason":"synthesis_failed", "detail": detail, "voice": voice}, status_code=500)

        return Response(content=result.audio_data, media_type="audio/mpeg",
                        headers={"Content-Disposition": 'inline; filename="tts.mp3"'})
    except Exception as e:
        logger.exception("tts endpoint crashed")
        return JSONResponse({"ok": False, "reason":"exception", "detail": str(e)}, status_code=500)

@app.post("/api/tts_wav/")
def tts_wav(payload: dict = Body(...)):
    key, region, default_voice = envs()
    missing = []
    if not key:    missing.append("AZURE_SPEECH_KEY")
    if not region: missing.append("AZURE_SPEECH_REGION")
    if missing:
        return JSONResponse({"ok": False, "reason":"azure_not_configured","missing":missing}, status_code=500)

    text  = (payload.get("text") or "").strip()
    voice = payload.get("voice") or default_voice
    if not text:
        raise HTTPException(400, "text is required")

    speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
    speech_config.speech_synthesis_voice_name = voice
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm
    )
    result = speechsdk.SpeechSynthesizer(speech_config=speech_config).speak_text_async(text).get()
    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        cd = getattr(result, "cancellation_details", None)
        detail = (getattr(cd, "error_details", None) or "unknown_error")
        raise HTTPException(500, f"synthesis_failed: {detail}")

    return Response(result.audio_data, media_type="audio/wav",
                    headers={"Content-Disposition":'inline; filename="tts.wav"'})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
