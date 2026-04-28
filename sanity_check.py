"""Sanity check all v2 modules"""
import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")

from core.browser_manager import BrowserManager
from core.search_collector import SearchCollector
from core.note_detail import NoteDetail
from core.scroll_helper import ScrollHelper
from filter.filter_service import FilterService, has_signal
from filter.classifier import classify_types, classify_type
from output.feishu_service import FeishuOutputService
from utils.parse import parse_published_at
from utils.text import clean_author
from utils.storage import RecentStorage

print("All imports OK")
print(f"FilterService public methods: {[m for m in dir(FilterService) if not m.startswith('_')]}")

# Quick smoke test
svc = FilterService()
n = NoteDetail(title="汕尾美食求推荐", content="汕尾美食求推荐", published_at="2026-04-28")
r = svc.filter_one(n)
print(f"Quick filter test: passed={r.passed}, reasons={r.reasons}, type={r.note_type}")