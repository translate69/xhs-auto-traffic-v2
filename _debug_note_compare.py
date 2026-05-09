# -*- coding: utf-8 -*-
"""对比：搜索标题 vs 详情页实际内容"""
import json, sys, os
sys.stdout.reconfigure(encoding='utf-8')

RUNS_FILE = 'data/collected/runs/2026-05-09_汕尾3天2晚攻略.jsonl'
OUTPUT = 'data/note_compare.txt'

with open(RUNS_FILE, encoding='utf-8') as f, open(OUTPUT, 'w', encoding='utf-8') as out:
    for i, line in enumerate(f):
        d = json.loads(line)
        title = (d.get('title') or '')[:30]
        content = (d.get('content') or '')[:60]
        reasons = d.get('filter_reasons', '')
        url = d.get('url', '')
        note_id = d.get('note_id', d.get('url', ''))
        # extract note_id from url if not present
        if not note_id or note_id == '':
            import re
            m = re.search(r'search_result/([a-f0-9]+)', url)
            note_id = m.group(1) if m else '?'
        out.write(f"[{i+1}] note_id={note_id}\n")
        out.write(f"    搜索标题: {title}\n")
        out.write(f"    详情内容: {content}\n")
        out.write(f"    filter: {reasons}\n")
        out.write(f"    URL: {url[:80]}\n")
        out.write("\n")

print(f"Done, see {OUTPUT}")
