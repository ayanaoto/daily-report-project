from dotenv import load_dotenv
load_dotenv()  # C:\Users\pc\.env を読む（起動場所が C:\Users\pc 前提）

import os, io, logging
from fastapi import FastAPI, Body, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import azure.cognitiveservices.speech as speechsdk

logging.getLogger().setLevel(logging.INFO)

def env_snapshot():
    return {
        "AZURE_SPEECH_KEY_set": bool(os.getenv("AZURE_SPEECH_KEY")),
        "AZURE_SPEECH_REGION": os.getenv("AZURE_SPEECH_REGION"),
        "AZURE_SPEECH_VOICE": os.getenv("AZURE_SPEECH_VOICE"),
    }

app = FastAPI()

@app.get("/api/envcheck")
def envcheck():
    snap = env_snapshot()
    logging.info(f"envcheck: {snap}")
    return {"ok": True, "env": snap}

@app.post("/api/tts/")
def tts(payload: dict = Body(...)):
    snap = env_snapshot()
    if not snap["AZURE_SPEECH_KEY_set"] or not snap["AZURE_SPEECH_REGION"]:
        # 何が無いかを返して可視化
        missing = []
        if not snap["AZURE_SPEECH_KEY_set"]:
            missing.append("AZURE_SPEECH_KEY")
        if not snap["AZURE_SPEECH_REGION"]:
            missing.append("AZURE_SPEECH_REGION")
        return JSONResponse({"ok": False, "reason": "azure_not_configured", "missing": missing, "env": snap}, status_code=500)

    text  = (payload.get("text") or "").strip()
    voice = payload.get("voice") or (snap["AZURE_SPEECH_VOICE"] or "ja-JP-NanamiNeural")
    if not text:
        raise HTTPException(400, "text is required")

    speech_config = speechsdk.SpeechConfig(
        subscription=os.getenv("AZURE_SPEECH_KEY"),
        region=os.getenv("AZURE_SPEECH_REGION")
    )
    speech_config.speech_synthesis_voice_name = voice
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
    )

    buf = io.BytesIO()
    out = speechsdk.audio.PushAudioOutputStream()
    out.set_callback(speechsdk.audio.PushAudioOutputStreamCallback(
        audio_chunk_received=lambda e: buf.write(e.audio),
        synthesis_completed=lambda e: None
    ))
    synth = speechsdk.SpeechSynthesizer(
        speech_config, speechsdk.audio.AudioOutputConfig(stream=out)
    )
    r = synth.speak_text_async(text).get()

    if r.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        detail = getattr(getattr(r, "cancellation_details", None), "error_details", "unknown_error")
        raise HTTPException(500, f"synthesis_failed: {detail}")

    buf.seek(0)
    return StreamingResponse(buf, media_type="audio/mpeg")
