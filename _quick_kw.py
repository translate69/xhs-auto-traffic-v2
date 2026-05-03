import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from _pipeline_debug import install_debug_log, log_stage
install_debug_log(__file__)

import os
from run_all import run_keyword
from utils.storage import CollectedStorage

keyword = "汕尾美食"
limit = 5
storage = CollectedStorage()

bp = f"data/collected/runs/2026-04-29_{keyword}.jsonl"
if os.path.exists(bp):
    os.remove(bp)

log_stage(f"开始: {keyword}", flush=True)
try:
    n = run_keyword(keyword, limit, False, storage)
    log_stage(f"完成: {keyword} → {n} 条通过", flush=True)
except Exception as e:
    log_stage(f"异常: {e}", flush=True)
print("Done!")
