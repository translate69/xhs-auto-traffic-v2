import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import json
from dataclasses import fields
from core.note_detail import NoteDetail
from filter.filter_service import FilterService

# 读取 enrichment 结果
enrichment_file = "data/collected/runs/2026-04-29_深圳周末游.jsonl"
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

# 逐条过 filter，输出原因
filter_svc = FilterService()
print(f"Total: {len(notes)} notes\n")

for nd in notes:
    result = filter_svc.filter_one(nd)
    content_preview = (nd.content or "")[:50].replace("\n", " ")
    print(f"note_id: {nd.note_id}")
    print(f"  title: {(nd.title or '')[:40]}")
    print(f"  content: {content_preview}...")
    print(f"  content_len: {len(nd.content or '')}")
    print(f"  PASSED: {result.passed}")
    print(f"  type: {result.note_type}")
    print(f"  reasons: {result.reasons}")
    print()
