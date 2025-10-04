# inspect_env.py
env_path = '.env'
print(f"Inspecting raw content of file: {env_path}")
try:
    # バイナリモードでファイルを開き、生のバイトデータを確認する
    with open(env_path, 'rb') as f:
        raw_content = f.read()
        print(f"Raw bytes: {raw_content}")

        # UTF-8としてデコードを試みる
        print(f"Decoded as UTF-8: {raw_content.decode('utf-8')}")
except Exception as e:
    print(f"Error reading file: {e}")