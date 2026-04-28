"""
诊断 FilterService 过滤结果
"""
import sys
sys.path.insert(0, "E:\\translate\\claw\\xhs-auto-traffic-v2")
sys.stdout.reconfigure(encoding='utf-8')

from core.note_detail import NoteDetail
from filter.filter_service import FilterService
from utils.parse import parse_published_at

# 用 enrichment 成功的真实数据模拟
test_cases = [
    {
        "content": "汕尾2天1夜，吃的都没踩雷\n#汕尾美食 #五一 #美食特种兵 #五一旅游攻略 #汕尾 #汕尾",
        "author": "momo",
        "published_at": "2026-04-28",
        "time_text": "2小时前",
        "url": "/explore/69f065e2000000001f001cbe",
    },
    {
        "content": "分享去汕尾玩了一天，去了红海湾和海边",
        "author": "龙龙",
        "published_at": "2026-04-27",
        "time_text": "昨天 23:18",
        "url": "/explore/69ef7e3f000000003501d790",
    },
    {
        "content": "汕尾美食哪里好吃？求推荐",
        "author": "SereneSage",
        "published_at": "2026-04-27",
        "time_text": "昨天 23:17",
        "url": "/explore/69ef7dfd000000003501d652",
    },
]

svc = FilterService()

for i, tc in enumerate(test_cases):
    print(f"\n--- 测试用例 {i+1} ---")
    print(f"  content:    {tc['content'][:50]}")
    print(f"  author:     {tc['author']}")
    print(f"  published_at: {tc['published_at']}")
    print(f"  time_text:  {tc['time_text']}")

    # 1. parse_published_at
    dt = parse_published_at(tc['time_text'])
    print(f"  parse_published_at('{tc['time_text']}'): {dt}")

    # 2. 构建 NoteDetail
    note = NoteDetail(
        content=tc['content'],
        author=tc['author'],
        published_at=tc['published_at'],
        time_text=tc['time_text'],
        url=tc['url'],
        likes=34,
        collects=30,
        comments=2,
    )

    # 3. 过滤
    try:
        result = svc.filter_one(note)
        print(f"  filter_one result: passed={result.passed}, reasons={result.reasons}")
    except Exception as e:
        print(f"  filter_one EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
