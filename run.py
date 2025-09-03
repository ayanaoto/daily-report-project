# run.py (最終修正版)

import os
import sys
import threading
import webbrowser
import time # ★ timeモジュールを追加
from waitress import serve
from daily_report_project.wsgi import application

# サーバーを起動する関数
def run_server():
    # 127.0.0.1のポート8000番でDjangoアプリを動かす
    serve(application, host='127.0.0.1', port='8000')

# アプリケーションがexeファイルとして実行されているか判定
if getattr(sys, 'frozen', False):
    # サーバーをバックグラウンドで起動
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    # ブラウザを起動して、アプリケーションのページを開く
    webbrowser.open('http://127.0.0.1:8000/')

    # ★★★ ここからが修正箇所 ★★★
    # input() の代わりに、無限ループでプログラムを待機させる
    # これにより、黒い画面が表示されなくてもプログラムは動き続ける
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sys.exit(0)
    # ★★★ ここまでが修正箇所 ★★★

else:
    # 通常のPython環境で実行された場合は、開発サーバーを起動する（テスト用）
    print("これはexe化用のスクリプトです。")
    print("開発時は python manage.py runserver を使用してください。")
    run_server()