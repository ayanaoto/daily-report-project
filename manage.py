#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配布向け“最小改造”版 manage.py
- 引数なし（= ダブルクリック想定）で runserver を自動実行
- 8000 が使用中なら 8001, 8002, 8010, 8080 の順で空きポートへ
- PyInstaller 環境では --noreload を付与
"""

import os
import sys
import socket
import time
import threading
import webbrowser
from pathlib import Path

# .env をプロジェクト直下から明示読み込み
from dotenv import load_dotenv
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env", override=False)

APP_HOST = "127.0.0.1"
CANDIDATE_PORTS = [8000, 8001, 8002, 8010, 8080]


def _is_port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        return s.connect_ex((APP_HOST, port)) != 0


def _pick_free_port() -> int:
    for p in CANDIDATE_PORTS:
        if _is_port_free(p):
            return p
    return 8000


def _open_browser_when_ready(url: str, timeout=20):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            import urllib.request

            with urllib.request.urlopen(url, timeout=0.5) as _:
                webbrowser.open(url)
                return
        except Exception:
            time.sleep(0.5)


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "daily_report_project.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Did you activate the virtualenv?"
        ) from exc

    auto_open = False
    if len(sys.argv) == 1:
        port = _pick_free_port()
        sys.argv += ["runserver", f"{APP_HOST}:{port}", "--noreload"]
        auto_open = True
        url = f"http://{APP_HOST}:{port}/"
        threading.Thread(target=_open_browser_when_ready, args=(url,), daemon=True).start()

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
