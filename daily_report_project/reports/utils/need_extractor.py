# reports/utils/need_extractor.py
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Iterable, List, Optional

@dataclass
class NeededItem:
    name: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    note: Optional[str] = None

# 例: 「LANケーブル 5本が必要」「HDMIケーブル×2本」「予備バッテリーが必要です」
# よくある言い回し・数量表現をざっくり拾う軽量ルール
_QUANT_PAT = r'(?P<qty>\d+(?:\.\d+)?)\s*(?P<unit>個|枚|本|台|m|メートル|箱|セット|式|袋|巻|本体|枚組)?'
_ITEM_PATTERNS: List[re.Pattern] = [
    # 1) 「XXX が必要」「XXX を用意」「XXX を持参」「XXX 手配」
    re.compile(r'(?P<name>[\wぁ-んァ-ン一-龥A-Za-z0-9\-\s＋\+／/_.]+?)\s*(?:の)?\s*(?:{q})?\s*(?:が必要|を用意|を手配|を持参|を購入|が足りない)'.format(q=_QUANT_PAT)),
    # 2) 「必要: XXX」や「必要→ XXX」
    re.compile(r'(?:必要|要品|Required)\s*[:：⇒→-]\s*(?P<name>[\wぁ-んァ-ン一-龥A-Za-z0-9\-\s＋\+／/_.]+?)\s*(?:{q})?\b'.format(q=_QUANT_PAT)),
    # 3) 「XXX ×3本」「XXX 3本」
    re.compile(r'(?P<name>[\wぁ-んァ-ン一-龥A-Za-z0-9\-\s＋\+／/_.]+?)\s*(?:×|x)?\s*{q}\b'.format(q=_QUANT_PAT)),
]

_BAD_CHARS = re.compile(r'^[\s・\-_/＋\+]+$')

def _clean(s: str) -> str:
    s = s.strip(" \t\r\n・-_/＋+　")
    return s

def extract_needed_items(text: str) -> List[NeededItem]:
    """
    本文から必要物品候補を抽出（重複名は数量統合）。
    """
    if not text:
        return []
    candidates: List[NeededItem] = []

    # 句点/改行で分割して走査（過検知抑制）
    lines: Iterable[str] = re.split(r'[。\n\r]+', text)
    for line in lines:
        line = line.strip()
        if not line:
            continue
        for pat in _ITEM_PATTERNS:
            for m in pat.finditer(line):
                name = _clean(m.group('name') or '')
                if not name or _BAD_CHARS.match(name):
                    continue
                qty = None
                unit = None
                if 'qty' in m.groupdict() and m.group('qty'):
                    try:
                        qty = float(m.group('qty'))
                    except ValueError:
                        qty = None
                if 'unit' in m.groupdict():
                    unit = m.group('unit')
                    if unit:
                        unit = unit.strip()
                candidates.append(NeededItem(name=name, quantity=qty, unit=unit, note=line))

    # 名前でまとめて数量合算（単位が一致する場合）
    merged: dict[tuple[str, Optional[str]], NeededItem] = {}
    for it in candidates:
        key = (it.name, it.unit)
        if key not in merged:
            merged[key] = NeededItem(name=it.name, quantity=it.quantity, unit=it.unit, note=it.note)
        else:
            if it.quantity is not None:
                merged[key].quantity = (merged[key].quantity or 0) + it.quantity
            # メモは残す（最新行で上書きせず追記）
            if it.note and merged[key].note:
                if it.note not in merged[key].note:
                    merged[key].note += f" / {it.note}"
            elif it.note:
                merged[key].note = it.note

    return list(merged.values())
