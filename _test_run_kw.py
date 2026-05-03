import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from run_all import run_keyword
from utils.storage import CollectedStorage

keyword = "汕尾美食"
limit = 5
storage = CollectedStorage()

import os
bp = f"data/collected/runs/2026-04-29_{keyword}.jsonl"
if os.path.exists(bp):
    os.remove(bp)
    print(f"Deleted breakpoint: {bp}")

run_keyword(keyword, limit, False, storage)
print("\nDone!")