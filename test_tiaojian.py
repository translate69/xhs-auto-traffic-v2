"""Add test case for the 宝藏 note that should fail"""
import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
sys.stdout.reconfigure(encoding="utf-8")

from filter.filter_service import FilterService
from core.note_detail import NoteDetail

svc = FilterService()

# Case: 宝藏美食分享风格 → 应淘汰
note = NoteDetail(
    title="沉浸式做汕尾这款宝藏美食！",
    content="沉浸式做汕尾这款宝藏美食！#芋头饺 #汕尾茶点供应 #手工芋",
    url="https://www.xiaohongshu.com/search_result/69ef1538000000003601bdb6",
    xsec_token="ABO6-Khbl",
    published_at="2026-04-28",
)
result = svc.filter_one(note)
print(f"宝藏美食 content: passed={result.passed}, reasons={result.reasons}")

# Case: 真实游客有type无ask → 应通过（问句语气）
note2 = NoteDetail(
    title="汕尾美食哪里好吃",
    content="准备去汕尾玩三天，有什么美食推荐吗？住在金町湾方便吗？",
    url="https://www.xiaohongshu.com/search_result/abc123",
    published_at="2026-04-28",
)
result2 = svc.filter_one(note2)
print(f"真实游客问句: passed={result2.passed}, reasons={result2.reasons}")

# Case: 真实游客有type无ask → 应通过（意图词）
note3 = NoteDetail(
    title="汕尾旅游",
    content="打算周末去汕尾自驾，想问问哪里适合赶海，住宿推荐哪里",
    url="https://www.xiaohongshu.com/search_result/def456",
    published_at="2026-04-28",
)
result3 = svc.filter_one(note3)
print(f"真实游客打算: passed={result3.passed}, reasons={result3.reasons}")

# Case: 宝藏+无问句+无意图词 → 应淘汰
note4 = NoteDetail(
    title="汕尾美食",
    content="这家刨冰夏天必须吃上，超级宝藏店铺，推荐给大家",
    url="https://www.xiaohongshu.com/search_result/ghi789",
    published_at="2026-04-28",
)
result4 = svc.filter_one(note4)
print(f"宝藏推荐风格: passed={result4.passed}, reasons={result4.reasons}")

print("\nAll tests done")