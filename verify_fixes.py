"""Verify all fixes work"""
import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
sys.stdout.reconfigure(encoding="utf-8")

from core.note_detail import NoteDetail
from filter.filter_service import FilterService
from output.feishu_service import FeishuOutputService

# Test 1: NoteDetail.note_id property
n = NoteDetail(
    url="https://www.xiaohongshu.com/search_result/abc123DEF?sid=xxx",
    xsec_token="tok123",
    content="汕尾美食求推荐",
)
print(f"note_id from search_result URL: {n.note_id!r}")

# Test 2: FilterService flow with filter_result stored
svc = FilterService()
n2 = NoteDetail(title="汕尾美食求推荐", content="汕尾美食求推荐", published_at="2026-04-28")
r = svc.filter_one(n2)
print(f"filter: passed={r.passed}, reasons={r.reasons}, type={r.note_type}")

# Test 3: FeishuOutputService._note_detail_to_row
svc2 = FeishuOutputService()
row = svc2._note_detail_to_row(n2)
print(f"feishu row:")
print(f"  note_id={row['note_id']!r}")
print(f"  note_url={row['note_url'][:70]!r}")
print(f"  type={row['type']!r}")
print(f"  reasons={row['reasons']!r}")
print(f"  title={row['title']!r}")

# Test 4: Full pipeline - NoteDetail with note_url
n3 = NoteDetail(
    url="https://www.xiaohongshu.com/search_result/abc123?sid=xxx&xsec_token=tok123",
    xsec_token="tok123",
    author="测试用户",
    content="汕尾两天怎么安排？求推荐美食",
    published_at="2026-04-28",
    tags=["汕尾", "美食"],
    images=["http://example.com/img.jpg"],
    likes=100,
    collects=50,
    comments=20,
)
row3 = svc2._note_detail_to_row(n3)
print(f"\nFull pipeline feishu row:")
print(f"  note_id={row3['note_id']!r}")
print(f"  note_url={row3['note_url'][:70]!r}")
print(f"  cover_image={row3['cover_image']!r}")
print(f"  tags={row3['tags']!r}")