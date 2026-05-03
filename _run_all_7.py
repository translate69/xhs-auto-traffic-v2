"""
_run_all_7.py - 跑全部7个核心关键词
"""
import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    from _pipeline_debug import install_debug_log, log_stage
    install_debug_log(__file__)
except ImportError:
    def log_stage(s, flush=True):
        from datetime import datetime
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] {s}", flush=flush)

log_stage("=" * 50, flush=True)
log_stage("开始跑全部 7 个核心关键词", flush=True)

import os
from run_all import run_keyword
from utils.storage import CollectedStorage

keywords = [
    "汕尾旅游攻略",
    "汕尾住宿推荐",
    "汕尾美食推荐",
    "汕尾去哪吃",
    "汕尾去哪住",
    "汕尾旅游",
    "汕尾美食",
]

storage = CollectedStorage()
results = []

for kw in keywords:
    bp = f"data/collected/runs/2026-04-29_{kw}.jsonl"
    if os.path.exists(bp):
        os.remove(bp)
        print(f"Deleted breakpoint: {bp}")

    log_stage(f"========== 开始: {kw} ==========", flush=True)
    try:
        n = run_keyword(kw, limit=5, headless=False, storage=storage)
        results.append((kw, n, "OK"))
        log_stage(f"完成: {kw} → {n} 条通过", flush=True)
    except Exception as e:
        results.append((kw, 0, f"异常: {e}"))
        log_stage(f"异常: {kw} → {e}", flush=True)

log_stage("=" * 50, flush=True)
log_stage("全部完成，结果汇总：", flush=True)
total = 0
for kw, n, status in results:
    log_stage(f"  {kw}: {n} 条 ({status})", flush=True)
    total += n

log_stage(f"总计通过: {total} 条", flush=True)
print("\n全部完成!")
