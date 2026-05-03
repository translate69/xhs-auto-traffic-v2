"""Pre-run smoke test for debug pipeline"""
import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
sys.stdout.reconfigure(encoding="utf-8")

from core.browser_manager import BrowserManager
from core.search_collector import SearchCollector
from core.note_detail import NoteDetailCollector
from filter.filter_service import FilterService
from output.feishu_service import FeishuOutputService
from utils.storage import CollectedStorage
from load_keywords import load_keywords
from core.note_detail import NoteDetail

print("=== Import Check ===")
kw = load_keywords()
print(f"Keywords loaded: {len(kw)}")

cs = CollectedStorage()
run_id = cs.make_run_id("汕尾美食")
print(f"Run ID: {run_id}")
print(f"Runs dir exists: {cs.RUNS_DIR.exists()}")

print("\n=== FeishuOutput Service ===")
n = NoteDetail(
    title="汕尾美食求推荐",
    content="求推荐汕尾好吃的",
    url="https://www.xiaohongshu.com/search_result/abc123DEF",
    xsec_token="tok123",
    author="测试用户",
    published_at="2026-04-28",
)
svc = FilterService()
r = svc.filter_one(n)
n.filter_result = r

fos = FeishuOutputService()
row = fos._note_detail_to_row(n)
print(f"note_id: {row['note_id']}")
print(f"note_url: {row['note_url'][:60]}")
print(f"type: {row['type']}")
print(f"reasons: {row['reasons']}")
print(f"keyword: {row['keyword']}")

print("\n=== BrowserManager ===")
with BrowserManager(headless=False) as (browser, context):
    page = context.new_page()
    page.goto("https://www.xiaohongshu.com", timeout=15000)
    print(f"Browser opened, title: {page.title()}")

print("\n=== All OK ===")