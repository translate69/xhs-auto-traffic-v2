# -*- coding: utf-8 -*-
import sys, os, io
sys.path.insert(0, ".")
os.chdir(r"E:\translate\claw\xhs-auto-traffic-v2")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import config
from core.browser_manager import BrowserManager
from core.search_collector import SearchCollector, LoginRequiredError
from core.note_detail import NoteDetailCollector
from filter.filter_service import FilterService
from output.feishu_service import FeishuOutputService
from utils.storage import CollectedStorage
from core.note_detail import NoteDetail
from dataclasses import fields

keyword = "汕尾海边民宿推荐"
limit = config.DEFAULT_LIMIT
headless = False

print(f"关键词: {keyword}")
print(f"模式: headless={headless}")

storage = CollectedStorage()
run_id = storage.make_run_id(keyword)
print(f"run_id: {run_id}")

try:
    with BrowserManager(headless=headless) as (browser, context):
        collector = SearchCollector(browser, context)
        feeds = collector.collect(keyword, limit=limit)
        print(f"搜索采集: {len(feeds)} 条")

        if not feeds:
            print("无采集结果，退出")
        else:
            detail_collector = NoteDetailCollector(browser, context)
            enriched = detail_collector.enrich_all(feeds)
            print(f"enrichment: {len(enriched)} 条")

            run_file = storage.save(run_id, keyword, enriched)
            print(f"中间文件: {run_file.name}")

            # 过滤
            notes = []
            for d in enriched:
                if isinstance(d, NoteDetail):
                    notes.append(d)
                else:
                    valid_fields = {f.name for f in fields(NoteDetail)}
                    filtered = {k: v for k, v in d.items() if k in valid_fields}
                    notes.append(NoteDetail(**filtered))

            filter_svc = FilterService()
            passed = []
            for note in notes:
                fr = filter_svc.filter_one(note)
                if fr.passed:
                    note._filter_result = fr
                    passed.append(note)

            print(f"过滤通过: {len(passed)} 条")

            if passed:
                feishu = FeishuOutputService()
                feishu.write(passed)
                print(f"飞书写入: {len(passed)} 条")

except LoginRequiredError as e:
    print(f"\n⚠️ {e}")
except Exception as e:
    print(f"\n出错: {e}")
    import traceback
    traceback.print_exc()

# 文件列表
import pathlib
runs_dir = pathlib.Path("data/collected/runs")
files = sorted(runs_dir.glob("2026-04-29_*.jsonl"))
print(f"\n当天文件 ({len(files)}):")
for f in files:
    print(f"  {f.name}")
