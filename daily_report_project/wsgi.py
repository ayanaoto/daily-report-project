# -*- coding: utf-8 -*-
"""
WSGI config for daily_report_project.
"""

import os
from pathlib import Path

# .env をプロジェクト直下から明示読み込み（Waitress/Gunicorn 入口）
from dotenv import load_dotenv
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env", override=False)

from django.core.wsgi import get_wsgi_application  # noqa: E402

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "daily_report_project.settings")
application = get_wsgi_application()
