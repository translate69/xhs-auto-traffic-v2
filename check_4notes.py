"""检查 4 条笔记为何全部被过滤"""
import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
sys.stdout.reconfigure(encoding='utf-8')

from core.note_detail import NoteDetail
from filter.filter_service import FilterService

notes = [
    NoteDetail(url="/search_result/69eec404000000002301705d", content="觅食主要区域为二马路周边与美团/🤓摘要：mvp芬芳美...", author="", published_at="2026-04-28"),
    NoteDetail(url="/search_result/69ed91500000000036031b84", content="在海丰公平食一顿牛肉，每一口都系惊喜！ #公平兴记鲜切牛肉火...", author="", published_at="2026-04-28"),
    NoteDetail(url="/search_result/69ed660f000000002202b76a", content="#家常菜 #好吃又简单 #家乡美食 #汕尾尼阿解...", author="", published_at="2026-04-28"),
    NoteDetail(url="/search_result/69ecd224000000002003aa3a", content="#汕尾美食 #姜薯 #腐乳鸡翅 #汕尾甜品 #汕尾生腌感觉...", author="", published_at="2026-04-28"),
]

svc = FilterService()
for i, n in enumerate(notes, 1):
    r = svc.filter_one(n)
    print(f"[{i}] passed={r.passed}, reasons={r.reasons}, type={r.note_type}")
    print(f"     content: {n.content[:40]}...")
    print()