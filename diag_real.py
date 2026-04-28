"""
诊断真实笔记为什么被过滤
"""
import sys
sys.path.insert(0, "E:\\translate\\claw\\xhs-auto-traffic-v2")
sys.stdout.reconfigure(encoding='utf-8')

from core.note_detail import NoteDetail
from filter.filter_service import FilterService

svc = FilterService()

# 真实 enrichment 数据
note = NoteDetail(
    content="广东 汕尾 红海湾～\n周末出差有1天半的自由活动时间\n小红书看了看，还是不知道怎么安排...",
    author="普通用户",
    published_at="2026-04-28",
    time_text="2小时前",
    url="/search_result/69ef5aaa000000002202aa1e?xsec_token=ABO6-Khbl...",
)

result = svc.filter_one(note)
print(f"passed={result.passed}, reasons={result.reasons}, type={result.note_type}")

# 逐步调试
from filter.filter_service import (
    REGION_KEYWORDS, STRONG_REJECT_KEYWORDS, MERCHANT_AUTHOR_KEYWORDS,
    SHARE_POST_KEYWORDS, TRANSPORT_KEYWORDS, REJECT_PATTERNS, ASK_SIGNALS,
    TRIP_QUESTION_SIGNALS, has_signal
)
import re

title = ""
content = note.content
combined = title + " " + content

print(f"\n--- 逐步检查 ---")
print(f"1. 地域: {any(kw in combined for kw in REGION_KEYWORDS)}")
print(f"2. 强拒绝: {any(kw in combined for kw in STRONG_REJECT_KEYWORDS)}")
print(f"3. 商家: {any(kw in content.lower() for kw in MERCHANT_AUTHOR_KEYWORDS)}")
print(f"4. ASK信号: {has_signal(content, ASK_SIGNALS)}")
print(f"5. 分享贴: {any(kw in combined for kw in SHARE_POST_KEYWORDS)}")
print(f"6. 交通: {any(kw in combined for kw in TRANSPORT_KEYWORDS)}")
print(f"7. 广告: {[p for p in REJECT_PATTERNS if re.search(p, combined, re.I)]}")
print(f"8. 问句信号: {has_signal(content, TRIP_QUESTION_SIGNALS)}")
