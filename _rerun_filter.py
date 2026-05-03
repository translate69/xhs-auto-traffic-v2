import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from _pipeline_debug import install_debug_log, log_stage
install_debug_log(__file__)

import json
from dataclasses import fields
from core.note_detail import NoteDetail
from filter.filter_service import FilterService
from output.feishu_service import FeishuOutputService

enrichment_file = "data/collected/runs/2026-04-29_深圳周末游.jsonl"
log_stage(f"读取: {enrichment_file}")

notes = []
with open(enrichment_file, encoding="utf-8", errors="replace") as f:
    for line in f:
        line = line.strip()
        if not line: continue
        d = json.loads(line)
        valid_fields = {f.name for f in fields(NoteDetail)}
        filtered = {k: v for k, v in d.items() if k in valid_fields}
        nd = NoteDetail(**filtered)
        nd.keyword = "深圳周末游"
        notes.append(nd)

log_stage(f"读取 {len(notes)} 条")

keyword = "深圳周末游"
filter_svc = FilterService()
passed = filter_svc.filter_all(notes, keyword=keyword)
log_stage(f"Filter 通过: {len(passed)} 条")

if passed:
    feishu = FeishuOutputService()
    feishu.write(passed, keyword=keyword)
    log_stage("Feishu 写入完成", flush=True)
else:
    log_stage("无通过笔记", flush=True)
