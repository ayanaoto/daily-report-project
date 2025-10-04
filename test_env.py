import os
from pathlib import Path
from dotenv import load_dotenv

# manage.py と同じ方法で .env を読み込む
BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR / ".env"

print(f"Attempting to load .env file from: {env_path}")

# ファイルが存在するかチェック
if env_path.exists():
    print(".env file FOUND.")
    load_dotenv(dotenv_path=env_path)
    token = os.getenv('FIELDNOTE_API_TOKEN')
    print(f"Value of FIELDNOTE_API_TOKEN is: '{token}'")
else:
    print(".env file NOT FOUND.")