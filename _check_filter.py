import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import json, glob, os

# 1. 检查 enrichment 结果
files = glob.glob("data/collected/runs/*深圳周末游*.jsonl")
if files:
    lines = open(files[0], encoding="utf-8", errors="replace").readlines()
    print(f"Enrichment results: {len(lines)} lines in {files[0]}")
    for i, line in enumerate(lines[:3]):
        d = json.loads(line)
        print(f"  [{i+1}] id={d.get('note_id','N/A')} title={d.get('title','?')[:40]}")
        print(f"       content={d.get('content','?')[:60]}")

# 2. 检查 filtered_for_feishu.jsonl
ff = "data/filtered_for_feishu.jsonl"
if os.path.exists(ff):
    lines = open(ff, encoding="utf-8", errors="replace").readlines()
    print(f"\nFiltered for feishu: {len(lines)} lines")
    for line in lines[-3:]:
        d = json.loads(line)
        print(f"  note_id={d.get('note_id','?')} keyword={d.get('keyword','?')}")
else:
    print(f"\n{ff}: NOT FOUND (filter may not have run)")

# 3. 检查 _pipeline_debug.log 最后20行
log_path = "_pipeline_debug.log"
if os.path.exists(log_path):
    lines = open(log_path, encoding="utf-8", errors="replace").readlines()
    print(f"\n_debug.log: {len(lines)} lines")
    for line in lines[-20:]:
        print(f"  {line.rstrip()}")
else:
    print(f"\n{log_path}: NOT FOUND")
