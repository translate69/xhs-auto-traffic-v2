"""v1 vs v2 关键差异对比测试"""
import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
sys.stdout.reconfigure(encoding='utf-8')

from core.note_detail import NoteDetail
from filter.filter_service import FilterService

svc = FilterService()

print("=== v2 现有过滤行为测试 ===\n")

cases = [
    # 酒店夸赞 - v1有专门规则
    ("有温度的酒店推荐给大家", "普通用户", "酒店夸赞"),
    ("不舍得离开这家民宿", "普通用户", "酒店夸赞"),
    ("强烈推荐这家酒店", "普通用户", "酒店夸赞"),
    ("太好住了必须推荐", "普通用户", "酒店夸赞"),

    # 团建 - v1有专门规则
    ("汕尾团建去哪里好", "普通用户", "团建"),
    ("10人起接的团建别墅", "普通用户", "团建"),

    # 推荐格式 - v1有 is_recommendation_share_format
    ("汕尾美食推荐住宿", "普通用户", "推荐格式标题"),
    ("汕尾必玩景点推荐", "普通用户", "推荐格式标题"),
    ("美食推荐汕尾", "普通用户", "推荐格式标题"),

    # ASK 通过类
    ("汕尾美食求推荐", "普通用户", "ASK求推荐"),
    ("有没有人知道汕尾哪里好玩", "普通用户", "知道信号"),
    ("请问汕尾怎么玩", "普通用户", "请问信号"),

    # 有地域但无信号
    ("汕尾2天1夜吃的都没踩雷", "普通用户", "纯分享打卡"),
    ("在海丰怎么玩", "普通用户", "有地域无信号"),
]

for content, author, label in cases:
    n = NoteDetail(content=content, author=author, published_at="2026-04-28")
    r = svc.filter_one(n)
    print(f"[{label}] content={content[:25]!r}")
    print(f"         author={author!r} -> passed={r.passed}, reasons={r.reasons}, type={r.note_type}")
    print()