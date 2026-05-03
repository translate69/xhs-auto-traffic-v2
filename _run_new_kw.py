"""
_run_new_kw.py - 定时 pipeline 脚本（供 cron 调用）
用法: python _run_new_kw.py [关键词] [limit]
默认: 关键词=汕尾美食, limit=5
"""
import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ─── 调试日志 ────────────────────────────────────────────
try:
    from _pipeline_debug import install_debug_log, log_stage
    install_debug_log(__file__)
except ImportError:
    def log_stage(s, flush=True):
        from datetime import datetime
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] {s}", flush=flush)

log_stage("脚本开始", flush=True)

# ─── 参数解析 ────────────────────────────────────────────
keyword = sys.argv[1] if len(sys.argv) > 1 else "汕尾美食"
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
log_stage(f"关键词={keyword}, limit={limit}", flush=True)

# ─── 业务代码 ────────────────────────────────────────────
import os
from datetime import datetime

from run_all import run_keyword
from utils.storage import CollectedStorage

storage = CollectedStorage()

# 删除断点文件（避免跳过采集）
bp = f"data/collected/runs/2026-04-29_{keyword}.jsonl"
if os.path.exists(bp):
    os.remove(bp)
    print(f"Deleted breakpoint: {bp}")

log_stage("开始 pipeline")

try:
    run_keyword(keyword, limit, False, storage)
    log_stage("Pipeline 执行完成", flush=True)
except Exception as e:
    log_stage(f"Pipeline 异常: {e}", flush=True)
    import traceback
    traceback.print_exc()

print("\nDone!")
log_stage("脚本退出", flush=True)
