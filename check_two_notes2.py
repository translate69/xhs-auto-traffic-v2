# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('data/collected/runs/2026-05-09_汕尾美食.jsonl', encoding='utf-8') as f:
    lines = f.readlines()

print('Total:', len(lines))

for i, line in enumerate(lines):
    d = json.loads(line)
    url = d.get('url', '')
    nid = d.get('note_id', '')
    if '69f76a0d' in url or '69f76a0d' in nid or '69fe050a' in url or '69fe050a' in nid:
        print(f"\n=== Line {i+1} ===")
        print(f"  note_id: {nid}")
        print(f"  url: {url[:80]}")
        print(f"  title: {d.get('title', '')}")
        print(f"  author: {d.get('author', '')}")
        print(f"  filter_passed: {d.get('filter_passed')}")
        print(f"  filter_reasons: {d.get('filter_reasons', '')}")
        print(f"  content: {d.get('content', '')}")
