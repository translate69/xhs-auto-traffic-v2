"""
parse.py - 时间解析工具

来自原 collect.py，逻辑 1:1 迁移，不改动。
"""
from __future__ import annotations

import calendar
import re
from datetime import datetime, timedelta


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
        past = now - timedelta(hours=hours)
        return past.replace(minute=0, second=0, microsecond=0)

    # 昨天
    if "昨天" in time_text:
        yesterday_day = now.day - 1
        year, month = now.year, now.month
        if yesterday_day < 1:
            # Go back to previous month
            year = year - 1 if month == 1 else year
            month = 12 if month == 1 else month - 1
            yesterday_day = calendar.monthrange(year, month)[1]
        try:
            return now.replace(year=year, month=month, day=yesterday_day, hour=0, minute=0, second=0, microsecond=0)
        except ValueError:
            return None

    # 天前
    m = re.match(r"(\d+)天前", time_text)
    if m:
        days = int(m.group(1))
        try:
            past_day = now.day - days
            if past_day < 1:
                # Crossed month boundary
                year, month = now.year, now.month
                while past_day < 1:
                    year = year - 1 if month == 1 else year
                    month = 12 if month == 1 else month - 1
                    past_day += calendar.monthrange(year, month)[1]
                return now.replace(year=year, month=month, day=past_day, hour=0, minute=0, second=0, microsecond=0)
            else:
                return now.replace(day=past_day, hour=0, minute=0, second=0, microsecond=0)
        except ValueError:
            return None

    # 月-日 格式
    m = re.match(r"(\d{2})-(\d{2})", time_text)
    if m:
        month, day = int(m.group(1)), int(m.group(2))
        # Validate month and day
        if month < 1 or month > 12:
            return None
        max_day = calendar.monthrange(now.year, month)[1]
        if day < 1 or day > max_day:
            day = min(day, max_day)
        try:
            return datetime(now.year, month, day)
        except ValueError:
            try:
                return datetime(now.year - 1, month, day)
            except ValueError:
                return None

    return None