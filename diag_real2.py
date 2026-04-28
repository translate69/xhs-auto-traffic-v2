"""
诊断真实笔记过滤被拒原因
"""
import sys
sys.path.insert(0, "E:\\translate\\claw\\xhs-auto-traffic-v2")
sys.stdout.reconfigure(encoding='utf-8')

from filter.filter_service import (
    REGION_KEYWORDS, STRONG_REJECT_KEYWORDS, MERCHANT_AUTHOR_KEYWORDS,
    SHARE_POST_KEYWORDS, TRANSPORT_KEYWORDS, REJECT_PATTERNS, ASK_SIGNALS,
    TRIP_QUESTION_SIGNALS, URGENT_SIGNALS, has_signal, classify_types
)
from core.note_detail import NoteDetail
from filter.filter_service import FilterService
import re

# 实际 enrichment 数据（根据日志输出）
title = ""
content = "📍广东 汕尾 红海湾～\n周末出差有1天半的自由活动时间\n小红书看了看，还是不知道怎么安排..."
author = "momo"  # 从 enrichment 提取
published_at = "2026-04-27"

combined = title + " " + content
print(f"content: {content[:50]}")
print(f"author: {author}")
print()
print("--- 逐步检查 ---")
print(f"1. 地域: {any(kw in combined for kw in REGION_KEYWORDS)}")
print(f"2. 强拒绝: {any(kw in combined for kw in STRONG_REJECT_KEYWORDS)}")
print(f"3. 商家账号: {any(kw in author.lower() for kw in MERCHANT_AUTHOR_KEYWORDS)}")
print(f"4. ASK信号: {has_signal(content, ASK_SIGNALS)}")
print(f"5. 分享贴: {any(kw in combined for kw in SHARE_POST_KEYWORDS)}")
print(f"6. 交通: {any(kw in combined for kw in TRANSPORT_KEYWORDS)}")
ad = [p for p in REJECT_PATTERNS if re.search(p, combined, re.I)]
print(f"7. 广告pattern: {ad}")
print(f"8. trip问句: {has_signal(content, TRIP_QUESTION_SIGNALS)}")
print(f"9. urgent: {has_signal(content, URGENT_SIGNALS)}")
print(f"10. 弱意向(想去/好想去/打算): {any(p in content for p in ['想去','好想去','打算'])}")
print(f"11. note_types: {classify_types(title, content)}")
print()

# 最终结果
note = NoteDetail(content=content, author=author, published_at=published_at, url="")
svc = FilterService()
result = svc.filter_one(note)
print(f"最终: passed={result.passed}, reasons={result.reasons}, type={result.note_type}")
