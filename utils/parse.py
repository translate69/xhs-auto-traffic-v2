"""
parse.py - 时间解析工具

来自原 collect.py，逻辑 1:1 迁移，不改动。
"""
from __future__ import annotations

import calendar
import re
from datetime import datetime


# ─── 常量 ──────────────────────────────────────────────────

_TIME_UNIT_PATTERN = r"天前|小时前|分钟前|秒前|天$|小时$|分钟$|秒$"
_TIME_SUFFIX_PATTERN = re.compile(r"\d+\s*(?:" + _TIME_UNIT_PATTERN + r")")


# ─── parse_published_at ───────────────────────────────────


def parse_published_at(time_text: str) -> datetime | None:
    """
    解析小红书时间文本为 datetime。
    格式支持：
      · 2026-04-28（ISO 格式）
      · 2分钟前 / 3小时前 / 5天前
      · 昨天
      · 04-28（月-日，自动补今年或去年）
    """
    if not time_text:
        return None

    now = datetime.now()

    # 去除 (X天) 后缀
    time_text = re.sub(r"\s*\(\d+\s*[\u4e00-\u9fff]\)\s*$", "", time_text)

    # 完整日期格式
    if re.match(r"^\d{4}-\d{2}-\d{2}", time_text):
        try:
            return datetime.strptime(time_text[:10], "%Y-%m-%d")
        except ValueError:
            return None

    # 分钟前
    m = re.match(r"(\d+)分钟前", time_text)
    if m:
        return now.replace(second=0, microsecond=0)

    # 小时前
    m = re.match(r"(\d+)小时前", time_text)
    if m:
        hours = int(m.group(1))
        return now.replace(hour=now.hour - hours, minute=0, second=0, microsecond=0)

    # 昨天
    if "昨天" in time_text:
        yesterday = now.day - 1
        year, month = now.year, now.month
        if yesterday < 1:
            year = year - 1 if month == 1 else year
            month = 12 if month == 1 else month - 1
            yesterday = calendar.monthrange(year, month)[1]
        return now.replace(year=year, month=month, day=yesterday, hour=0, minute=0, second=0, microsecond=0)

    # 天前
    m = re.match(r"(\d+)天前", time_text)
    if m:
        days = int(m.group(1))
        return now.replace(day=now.day - days, hour=0, minute=0, second=0, microsecond=0)

    # 月-日 格式
    m = re.match(r"(\d{2})-(\d{2})", time_text)
    if m:
        month, day = int(m.group(1)), int(m.group(2))
        try:
            return datetime(now.year, month, day)
        except ValueError:
            return datetime(now.year - 1, month, day)

    return None
