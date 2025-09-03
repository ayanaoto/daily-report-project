#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配布向け“最小改造”版 manage.py
- 引数なし（= ダブルクリック想定）で runserver を自動実行
- 起動完了をポーリングして既定ブラウザを自動で開く
- 8000 が使用中なら 8001, 8002, 8010, 8080 の順で自動で空きポートに切替
- PyInstaller 実行環境では autoreload が失敗するため --noreload を必ず付与
"""

import os
import sys
import socket
import time
import threading
import webbrowser

# ====== 配布向けの簡易設定 ======
APP_HOST = "127.0.0.1"
CANDIDATE_PORTS = [8000, 8001, 8002, 8010, 8080]
OPEN_TIMEOUT_SEC = 20
CHECK_INTERVAL_SEC = 0.25
# =============================

def _port_is_free(host: str, port: int) -> bool:
    """そのポートが空いているかを軽量にチェック"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        return s.connect_ex((host, port)) != 0

def _open_browser_when_ready(url: str, timeout: float = OPEN_TIMEOUT_SEC):
    """
    Django が立ち上がるまで TCP をポーリングして、開通したらブラウザを開く。
    url は "http://127.0.0.1:8000/" の形式を想定。
    """
    deadline = time.time() + timeout
    # 再起動直後などの TIME_WAIT を少し待つ
    time.sleep(1.0)
    host, port = url.split("//", 1)[1].rstrip("/").split(":")
    port = int(port)
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.2)
            if s.connect_ex((host, port)) == 0:
                try:
                    webbrowser.open(url)
                except Exception:
                    pass
                return
        time.sleep(CHECK_INTERVAL_SEC)
    # タイムアウト時は何もしない（配布向けに静かに失敗）

def _pick_free_port() -> int:
    """候補の中から空いているポートを一つ返す。全滅なら 8000 を返す。"""
    for p in CANDIDATE_PORTS:
        if _port_is_free(APP_HOST, p):
            return p
    return 8000

def main():
    """Django 標準の main に、ダブルクリック時の自動 runserver だけ足した最小改造"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'daily_report_project.settings')

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django が見つかりません。仮想環境や依存関係を確認してください。"
        ) from exc

    auto_open = False
    # ★ 引数なし＝ダブルクリック想定：自動で runserver を付与（PyInstaller対策で --noreload 必須）
    if len(sys.argv) == 1:
        port = _pick_free_port()
        sys.argv += ["runserver", f"{APP_HOST}:{port}", "--noreload"]
        auto_open = True
        # 起動検知→ブラウザ自動オープン（デーモンスレッドで並行実行）
        url = f"http://{APP_HOST}:{port}/"
        t = threading.Thread(target=_open_browser_when_ready, args=(url,), daemon=True)
        t.start()

    # 以降は通常の Django フロー
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
