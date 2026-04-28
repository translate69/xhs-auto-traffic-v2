"""
text.py - 文本处理工具
"""
from __future__ import annotations

import re


# ─── 否定词 ──────────────────────────────────────────────

NEGATIONS = ["不想", "不要", "不是", "不含", "没兴趣", "不考虑", "不去"]


# ─── clean_author ─────────────────────────────────────────


def clean_author(author: str) -> tuple[str, str]:
    """
    清理作者名中的时间后缀（如"珍妮2天前" → "珍妮"）。
    返回 (清理后名字, 时间后缀)
    """
    from utils.parse import _TIME_SUFFIX_PATTERN

    m = _TIME_SUFFIX_PATTERN.search(author)
    time_suffix = m.group(0) if m else ""
    clean_name = _TIME_SUFFIX_PATTERN.sub("", author).strip()
    return clean_name, time_suffix


# ─── parse_likes ─────────────────────────────────────────


def parse_likes(likes_str: str) -> int:
    """解析点赞数字符串"""
    if likes_str in ("赞", "喜欢"):
        return 1
    try:
        return int(likes_str)
    except ValueError:
        return 0


# ─── has_signal ──────────────────────────────────────────


def has_signal(text: str, kw_list: list[str]) -> bool:
    """
    检查文本是否含信号词，且不在否定前缀后。
    否定前缀（前4字内含 NEGATIONS 之一则信号不成立）。
    """
    text_lower = text.lower()
    for kw in kw_list:
        idx = text_lower.find(kw.lower())
        if idx == -1:
            continue

        # CJK 前边界检查（防复合词，如"追求"中的"求"）
        if idx > 0:
            pre_char = text_lower[idx - 1]
            if 0x4E00 <= ord(pre_char) <= 0x9FFF:
                continue  # 复合词内部，跳过

        # 否定词检查
        for window in range(4, 0, -1):
            if idx >= window:
                pre = text_lower[idx - window:idx]
                if any(n in pre for n in NEGATIONS):
                    break
        else:
            return True

    return False


# ─── 通用文本工具 ────────────────────────────────────────


def strip_tags(text: str) -> str:
    """去掉文本中的 hashtag"""
    return re.sub(r'#.+?(?=\s|#|$)', '', text).strip()


def truncate(text: str, length: int = 200) -> str:
    """截断文本到指定长度"""
    return text[:length] + "..." if len(text) > length else text
