"""
classifier.py - 笔记类型分类

来自原 filter.py，classify_type / classify_types，1:1 迁移。
"""
from __future__ import annotations

import re
from typing import Literal

# ─── 类型模式 ────────────────────────────────────────────

TYPE_SIGNALS_REGEX: dict[str, list[str]] = {
    "美食推荐": [
        r"吃[啥么些什么]", r"喝[啥么些什么]", r"去哪[吃喝]",
        r"美[食吃]", r"餐[厅食]",
        r"大排档", r"海鲜", r"小吃", r"早茶", r"食店", r"咖啡", r"下午茶",
    ],
    "住宿推荐": [
        r"住哪", r"住宿", r"民宿", r"酒店", r"客栈", r"[订租]房",
        r"哪家好", r"哪一家好", r"住哪个",
    ],
    "行程规划": [
        r"几[天晚个]", r"[天日][晚号]", r"行程", r"自驾", r"路线", r"攻略",
    ],
    "景点推荐": [
        r"景点", r"打卡", r"风景", r"日出", r"日落", r"赶海",
        r"沙滩", r"海边", r"网红", r"海湾", r"岛屿",
    ],
}

TYPE_PRIORITY: list[str] = ["美食推荐", "住宿推荐", "行程规划", "景点推荐"]


def classify_type(title: str, content: str) -> str:
    """单类型分类（兼容保留），返回第一个命中的类型"""
    types = classify_types(title, content)
    return types[0] if types else "其他"


def classify_types(title: str, content: str) -> list[str]:
    """
    多类型分类。
    返回所有命中的需求类型列表，按 TYPE_PRIORITY 顺序。
    """
    text = (title + " " + content).lower()
    matched: list[str] = []

    for type_name in TYPE_PRIORITY:
        patterns = TYPE_SIGNALS_REGEX.get(type_name, [])
        for pattern in patterns:
            if re.search(pattern, text):
                matched.append(type_name)
                break

    return matched
