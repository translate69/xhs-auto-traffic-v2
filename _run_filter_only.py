"""
_run_filter_only.py - 只跑 filter + feishu 写入（enrichment 结果已保存在 jsonl）
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

log_stage("脚本开始", flush=True)

import json
from dataclasses import fields
from core.note_detail import NoteDetail
from filter.filter_service import FilterService
from output.feishu_service import FeishuOutputService

# 读取 enrichment 结果
enrichment_file = "data/collected/runs/2026-04-29_深圳周末游.jsonl"
log_stage(f"读取 enrichment 结果: {enrichment_file}")

notes = []
with open(enrichment_file, encoding="utf-8", errors="replace") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        valid_fields = {f.name for f in fields(NoteDetail)}
        filtered = {k: v for k, v in d.items() if k in valid_fields}
        nd = NoteDetail(**filtered)
        nd.keyword = "深圳周末游"
        notes.append(nd)

log_stage(f"读取 {len(notes)} 条 enrichment 结果")

# Filter
keyword = "深圳周末游"
log_stage(f"开始 FilterService.filter_all(keyword={keyword})")
filter_svc = FilterService()
passed = filter_svc.filter_all(notes, keyword=keyword)
log_stage(f"Filter 通过: {len(passed)} 条", flush=True)

# Feishu
if passed:
    log_stage(f"开始 FeishuOutputService.write({len(passed)} 条)")
    feishu = FeishuOutputService()
    feishu.write(passed, keyword=keyword)
    log_stage("Feishu 写入完成", flush=True)
else:
    log_stage("无通过笔记，跳过飞书写入", flush=True)

log_stage("全部完成", flush=True)
print("Done!")
