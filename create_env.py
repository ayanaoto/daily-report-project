# create_env.py

# content 変数の中身をこちらに差し替えてください
content = """FIELDNOTE_API_TOKEN=devtoken
DJANGO_DEBUG=true
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8001,http://localhost:8001
AZURE_SPEECH_KEY=2cSFCbIUuQY4feRU326LbhuzjgEvOblkN1x2TJeqMfttqjjYv1rFJQQJ99BIACi0881XJ3w3AAAYACOGuEO6
AZURE_SPEECH_REGION=japaneast
AZURE_SPEECH_VOICE=ja-JP-NanamiNeural
"""
# ▲▲▲▲▲ 文字列はここで終わり ▲▲▲▲▲

try:
    # 'utf-8' を指定することでBOMなしのファイルが作成されます
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(content)
    print(".env file has been recreated successfully by Python with Azure keys. (BOM Free)")
except Exception as e:
    print(f"Error creating file: {e}")