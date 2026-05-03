"""Run single keyword debug pipeline"""
import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

import config
from core.browser_manager import BrowserManager
from core.search_collector import SearchCollector
from core.note_detail import NoteDetailCollector
from filter.filter_service import FilterService
from output.feishu_service import FeishuOutputService
from utils.storage import CollectedStorage

def main():
    keyword = "汕尾美食"
    limit = 20
    headless = False

    print(f"[启动] 关键词={keyword}, limit={limit}, headless={headless}", flush=True)

    storage = CollectedStorage()
    run_id = storage.make_run_id(keyword)
    print(f"[run_id] {run_id}", flush=True)

    # 采集 + enrichment
    with BrowserManager(headless=headless) as (browser, context):
        collector = SearchCollector(browser, context)
        feeds = collector.collect(keyword, limit=limit)
        print(f"[采集] {len(feeds)} 条笔记", flush=True)

        if not feeds:
            print("[退出] 无采集结果", flush=True)
            return

        detail_collector = NoteDetailCollector(browser, context)
        enriched = detail_collector.enrich_all(feeds)
        print(f"[Enrichment] {len(enriched)} 条成功", flush=True)

    # 写入中间文件
    run_file = storage.save(run_id, keyword, enriched)
    print(f"[中间文件] 已写入: {run_file.name}", flush=True)

    # 过滤
    filter_svc = FilterService()
    filtered = filter_svc.filter_all(enriched)
    print(f"[筛选] {len(filtered)} 条通过", flush=True)

    storage.append_manifest(run_id, keyword, len(enriched))

    if filtered:
        feishu = FeishuOutputService()
        feishu.write(filtered)
        print(f"[飞书] 写入 {len(filtered)} 条", flush=True)
    else:
        print("[飞书] 无通过记录", flush=True)

    print("[全部完成]", flush=True)

if __name__ == "__main__":
    main()