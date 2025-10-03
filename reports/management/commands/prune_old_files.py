# reports/management/commands/prune_old_files.py
import os
import sys
import time
import argparse
from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

DEFAULT_TARGETS = [
    # 必要に応じて追加/変更OK
    "voice_logs",          # 音声ログ保存先（例）
    "uploads",             # 汎用アップロード（例）
    "tmp",                 # 一時置き場（例）
]

class Command(BaseCommand):
    help = "指定ディレクトリ（MEDIA_ROOT配下）の古いファイルを削除します。（既定30日）"

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument("--days", type=int, default=30, help="しきい値（日）。既定: 30")
        parser.add_argument("--dry-run", action="store_true", help="削除は実行せず対象のみ表示")
        parser.add_argument("--targets", nargs="*", help=f"対象ディレクトリ（MEDIA_ROOTからの相対）。未指定なら {DEFAULT_TARGETS}")
        parser.add_argument("--verbose", action="store_true", help="詳細ログ出力")

    def handle(self, *args, **opts):
        days = opts["days"]
        dry = opts["dry_run"]
        verbose = opts["verbose"]
        targets = opts["targets"] or getattr(settings, "FIELDNOTE_PRUNE_TARGETS", DEFAULT_TARGETS)

        media_root = Path(getattr(settings, "MEDIA_ROOT", ""))
        if not media_root or not media_root.exists():
            self.stderr.write(self.style.ERROR("MEDIA_ROOT が設定されていないか存在しません。settings.py を確認してください。"))
            sys.exit(1)

        cutoff = datetime.now().timestamp() - days * 86400
        total_files = 0
        total_bytes = 0
        removed_files = 0
        removed_bytes = 0

        self.stdout.write(self.style.NOTICE(f"[PRUNE] MEDIA_ROOT={media_root} / days={days} / dry_run={dry}"))
        self.stdout.write(self.style.NOTICE(f"[PRUNE] targets={targets}"))

        for rel in targets:
            base = media_root / rel
            if not base.exists():
                if verbose:
                    self.stdout.write(f"  - skip: {base} (not exists)")
                continue

            for p in base.rglob("*"):
                if not p.is_file():
                    continue
                try:
                    stat = p.stat()
                except OSError:
                    continue

                total_files += 1
                total_bytes += stat.st_size
                if stat.st_mtime < cutoff:
                    if verbose:
                        age_days = (time.time() - stat.st_mtime) / 86400
                        self.stdout.write(f"  - old: {p}  ({age_days:.1f}d)  {stat.st_size} bytes")
                    if not dry:
                        try:
                            p.unlink()
                            removed_files += 1
                            removed_bytes += stat.st_size
                        except OSError as e:
                            self.stderr.write(self.style.WARNING(f"    failed: {p} ({e})"))

        self.stdout.write(self.style.SUCCESS(
            f"[PRUNE DONE] scanned={total_files} files ({total_bytes} bytes), "
            f"removed={removed_files} files ({removed_bytes} bytes), dry_run={dry}"
        ))
