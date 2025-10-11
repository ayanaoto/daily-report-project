# reports/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Report, RequiredItem
import re
import unicodedata

# 【追加】エラー解消のために必要なimport
from datetime import datetime, date
from django.utils import timezone


# ==== デバッグフラグ ====
DEBUG_EXTRACT = False  # Trueにすると、ターミナルに抽出の詳細ログが表示されます

# ----------------------------------------------------------------------
# ヘルパー関数: 複数の候補から安全にフィールド値を取得
# ----------------------------------------------------------------------
def _get_attr(obj, names: list[str], default: str = ""):
    """
    オブジェクトから属性値を取得します。
    namesリストに ['work_content', 'content'] のように複数の候補を指定できます。
    """
    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)
            if value is not None:
                return value
    return default

# ----------------------------------------------------------------------
# テキストから必要な物品を抽出する関数
# ----------------------------------------------------------------------
def extract_needed_items_final(text: str) -> list[str]:
    if not text or not text.strip():
        return []

    text_norm = unicodedata.normalize("NFKC", text)
    SEP_CLASS = r"とや、"
    SEP = rf"[{SEP_CLASS}]"
    PARTICLES = "がをはもにへでの"
    PARTICLE_CLASS = f"[{PARTICLES}]"
    ITEM_TOKEN = r"[^\s。、．，！？…{}{}]+".format(SEP_CLASS, PARTICLES)
    ITEM_GROUP = rf"{ITEM_TOKEN}(?:{SEP}{ITEM_TOKEN})*"
    OPTIONAL_PARTICLE = r"(?:[がをはもにへでとや、の]?)*"
    TRIGGER_CORE = r"(?:必要|用意|準備|購入|手配|いる|要る)"
    AFTER_TRIGGER_TAIL = r"(?:する|した|して|します|し|予定|でした|です|だ|で|ます|しておく|する予定)?"
    
    pat_pair_needed = re.compile(rf"(?P<a>{ITEM_TOKEN})と(?P<b>{ITEM_TOKEN})[がは]{OPTIONAL_PARTICLE}(?:必要){AFTER_TRIGGER_TAIL}")
    pat_direct = re.compile(rf"(?P<items>{ITEM_GROUP}){OPTIONAL_PARTICLE}(?P<trg>{TRIGGER_CORE}){AFTER_TRIGGER_TAIL}")
    pat_sahen = re.compile(rf"(?P<items>{ITEM_GROUP}){OPTIONAL_PARTICLE}(?P<trg>購入|用意|準備){OPTIONAL_PARTICLE}(?:する|した|して|します|する予定)")
    pat_bridge = re.compile(rf"(?P<items>{ITEM_GROUP}){OPTIONAL_PARTICLE}(?:[^\s。！？…]{{1,10}}){{0,3}}(?P<trg>{TRIGGER_CORE}){AFTER_TRIGGER_TAIL}")

    STOPWORDS = {"今日", "きょう", "今日は", "きょうは", "明日", "あした", "明後日", "あさって", "あと", "それから", "さらに", "追加で", "予定", "以上", "等", "など"}
    TRIGGER_ALL = re.compile(r"(必要|用意|準備|購入|手配|いる|要る)")
    LEADING_CONNECTIVE = re.compile(r"^(?:今日は|きょうは|今日|きょう|あと|それから|さらに)")
    STRIP_PUNCT_HEAD = re.compile(r"^[、。．，…！？!?\-—・:：;；（）\(\)\[\]「」『』\"'`]+")
    STRIP_PUNCT_TAIL = re.compile(r"[、。．，…！？!?\-—・:：;；（）\(\)\[\]「」『』\"'`]+$")

    def _choose_by_particles(s: str) -> str:
        parts = re.split(PARTICLE_CLASS, s)
        if len(parts) <= 1: return s
        left, right = parts[0], parts[-1]
        left_clean, right_clean = TRIGGER_ALL.sub("", left), TRIGGER_ALL.sub("", right)
        candidates = [c for c in [left_clean.strip(), right_clean.strip()] if c]
        if not candidates: return s
        if len(candidates) == 2: return candidates[0] if len(candidates[0]) >= len(candidates[1]) else candidates[1]
        return candidates[0]

    def _clean_item(raw: str) -> str | None:
        s = raw.strip()
        if not s: return None
        s = STRIP_PUNCT_HEAD.sub("", s)
        s = STRIP_PUNCT_TAIL.sub("", s)
        s = LEADING_CONNECTIVE.sub("", s)
        s = TRIGGER_ALL.sub("", s)
        if re.search(PARTICLE_CLASS, s): s = _choose_by_particles(s)
        s = STRIP_PUNCT_HEAD.sub("", s)
        s = STRIP_PUNCT_TAIL.sub("", s)
        s = re.sub(rf"^{PARTICLE_CLASS}+", "", s)
        s = re.sub(rf"{PARTICLE_CLASS}+$", "", s)
        is_kanji_1char = bool(re.fullmatch(r"[\u4E00-\u9FFF]", s))
        if not s or s in STOPWORDS or (len(s) == 1 and not is_kanji_1char): return None
        return s

    found_spans, items = set(), set()
    for m in pat_pair_needed.finditer(text_norm):
        span = m.span()
        if span in found_spans: continue
        found_spans.add(span)
        a, b = _clean_item(m.group("a")), _clean_item(m.group("b"))
        if a: items.add(a)
        if b: items.add(b)

    for pat in [pat_direct, pat_sahen, pat_bridge]:
        for m in pat.finditer(text_norm):
            span = m.span()
            if span in found_spans: continue
            found_spans.add(span)
            for raw in re.split(SEP, m.group("items")):
                cleaned = _clean_item(raw)
                if cleaned: items.add(cleaned)
    return list(items)

# ----------------------------------------------------------------------
# Reportモデル保存後のシグナルハンドラ
# ----------------------------------------------------------------------
@receiver(post_save, sender=Report)
def report_post_save_handler(sender, instance: Report, created: bool, **kwargs):
    print(f"✅ Report保存後: シグナル発火 ID: {instance.id}")

    work_content = _get_attr(instance, ["work_content", "content", "作業内容"], "")
    note = _get_attr(instance, ["note", "remarks", "備考"], "")
    text_to_analyze = f"{work_content}\n{note}".strip()

    if not text_to_analyze:
        print("⚠️ 対象テキストが空のため、ToDo作成をスキップしました。")
        return

    print(f"📝 解析対象テキスト:\n---\n{text_to_analyze}\n---")
    
    found_items = extract_needed_items_final(text_to_analyze)
    print(f"🔍 抽出されたアイテム: {found_items}")

    date_field = _get_attr(instance, ["date", "report_date", "created_at"])
    report_date = date_field if isinstance(date_field, (datetime, date)) else timezone.now()
    todo_title = f"{report_date.strftime('%Y/%m/%d')}の日報から自動作成"
    
    existing_todo, deleted = RequiredItem.objects.filter(
        assignee=instance.author,
        title=todo_title,
    ).delete()
    if deleted:
        print(f"🗑️ 既存のまとめToDoを削除しました: {deleted}")

    if not found_items:
        print("ℹ️ 抽出アイテムがないため、ToDoは作成しません。")
        return

    todo_body = "\n".join(f"・{item}" for item in found_items)

    try:
        RequiredItem.objects.create(
            title=todo_title,
            assignee=instance.author,
            required_items_list=todo_body,
            is_done=False,
        )
        print(f"✅ ToDo作成成功: '{todo_title}'")
    except Exception as e:
        print(f"❌ ToDo作成中にエラーが発生しました: {e}")