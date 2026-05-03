"""验证 69f1020c 笔记的 enrichment 结果"""
import sys
sys.path.insert(0, ".")

from pathlib import Path
import config
from core.browser_manager import BrowserManager
from core.note_detail import NoteDetailCollector
from core.search_collector import FeedNote

# 目标笔记的 FeedNote
feed = FeedNote(
    url="/search_result/69f1020c000000001a02e734?xsec_token=ABqssVzyXvPNzrtSnmMRGiY_RXDEyGn_uwJH8cN5hIJDI%3D&xsec_source=pc_search",
    xsec_token="ABqssVzyXvPNzrtSnmMRGiY_RXDEyGn_uwJH8cN5hIJDI%3D",
    author="",
    time_text="",
    title="求汕尾值得去的海边与美食",
)

with BrowserManager(headless=False) as (browser, context):
    collector = NoteDetailCollector(browser, context)
    
    print("=== 测试 enrichment ===")
    print(f"feed.url: {feed.url}")
    print(f"feed.xsec_token: {feed.xsec_token}")
    print()
    
    detail = collector._enrich_single(feed, max_retries=1)
    
    print()
    print("=== 结果 ===")
    print(f"content: {detail.content}")
    print(f"title: {detail.title}")
    print(f"author: {detail.author}")
    print(f"published_at: {detail.published_at}")
    print(f"time_text: {detail.time_text}")
    print(f"images: {detail.images}")
    print(f"likes: {detail.likes}, collects: {detail.collects}, comments: {detail.comments}")