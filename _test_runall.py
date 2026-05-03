# -*- coding: utf-8 -*-
import sys, os, io
sys.path.insert(0, ".")
os.chdir(r"E:\translate\claw\xhs-auto-traffic-v2")

# Fix stdout encoding for Chinese
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import config
from core.browser_manager import BrowserManager
from core.search_collector import SearchCollector
from core.note_detail import NoteDetailCollector
from filter.filter_service import FilterService
from utils.storage import CollectedStorage

keyword = "汕尾海边民宿推荐"
limit = config.DEFAULT_LIMIT

print(f"开始采集关键词: {keyword}")

storage = CollectedStorage()
run_id = storage.make_run_id(keyword)
print(f"run_id: {run_id}")

with BrowserManager(headless=True) as (browser, context):
    collector = SearchCollector(browser, context)
    feeds = collector.collect(keyword, limit=limit)
    print(f"搜索采集: {len(feeds)} 条")

    if not feeds:
        print("无采集结果")
    else:
        detail_collector = NoteDetailCollector(browser, context)
        enriched = detail_collector.enrich_all(feeds)
        print(f"enrichment: {len(enriched)} 条")

        # 写入中间文件
        run_file = storage.save(run_id, keyword, enriched)
        print(f"中间文件已写入: {run_file}")

# 检查生成的文件
import pathlib
runs_dir = pathlib.Path("data/collected/runs")
files = sorted(runs_dir.glob("2026-04-29_*.jsonl"))
print(f"\n当天文件列表:")
for f in files:
    print(f"  {f.name}")
