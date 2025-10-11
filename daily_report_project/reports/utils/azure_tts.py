# reports/utils/azure_tts.py
import requests


def synthesize_mp3(text: str, region: str, key: str, voice: str, fmt: str = "audio-24khz-48kbitrate-mono-mp3") -> bytes:
    """
    Azure Speech TTS に SSML を投げて MP3 などの音声バイト列を返す。
    失敗時は requests.HTTPError 等を raise する。
    """
    ssml = f"""<speak version="1.0" xml:lang="ja-JP"
      xmlns="http://www.w3.org/2001/10/synthesis"
      xmlns:mstts="https://www.w3.org/2001/mstts">
  <voice xml:lang="ja-JP" name="{voice}">
    <prosody rate="-6%" pitch="+1%">{_esc(text)}</prosody>
  </voice>
</speak>"""

    url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
    headers = {
        "Ocp-Apim-Subscription-Key": key,
        "X-Microsoft-OutputFormat": fmt,
        "Content-Type": "application/ssml+xml; charset=utf-8",
        "User-Agent": "FieldNote-Django",
    }

    resp = requests.post(url, headers=headers, data=ssml.encode("utf-8"), timeout=15)
    resp.raise_for_status()
    return resp.content


def _esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
