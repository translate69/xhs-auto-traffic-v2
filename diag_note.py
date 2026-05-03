# -*- coding: utf-8 -*-
import json, sys, os
from pathlib import Path

sys.path.insert(0, ".")
os.chdir(r"E:\translate\claw\xhs-auto-traffic-v2")

from filter.filter_service import FilterService

runs_dir = Path("data/collected/runs")
target_id = "69ef89c2"

note_data = None
for f in runs_dir.glob("*.jsonl"):
    try:
        with open(f, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if target_id in obj.get("url", ""):
                        note_data = obj
                        break
                except:
                    continue
        if note_data:
            break
    except:
        continue

if not note_data:
    print("未找到该笔记")
    sys.exit(1)

print(f"笔记内容: {note_data.get('content','')}")
print()

from core.note_detail import NoteDetail

from core.note_detail import NoteDetail

detail = NoteDetail(
    url=note_data.get("url",""),
    xsec_token=note_data.get("xsec_token",""),
    author=note_data.get("author",""),
    time_text=note_data.get("time_text",""),
    title=note_data.get("title",""),
    content=note_data.get("content",""),
    images=note_data.get("images",[]),
    tags=note_data.get("tags",[]),
    likes=note_data.get("likes",0),
    collects=note_data.get("collects",0),
    comments=note_data.get("comments",0),
    published_at=note_data.get("published_at",""),
)
detail._filter_result = None

svc = FilterService()
result = svc.filter_one(detail)

print(f"过滤结果: passed={result.passed}")
print(f"原因: {result.reasons}")
print(f"类型: {result.note_type}")