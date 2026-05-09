# -*- coding: utf-8 -*-
"""检查这两个 note_id 是否在历史数据里"""
import json, os, glob, sys
sys.stdout.reconfigure(encoding='utf-8')

target = ['69f76a0d000000002202b546', '69fe050a000000002003b0c8']

# Search all runs files
print("=== Search runs files ===")
all_runs = glob.glob('data/collected/runs/*.jsonl')
found_runs = {}
for fpath in sorted(all_runs):
    with open(fpath, encoding='utf-8') as f:
        for line in f:
            d = json.loads(line)
            nid = d.get('note_id') or ''
            if any(t in nid for t in target):
                fname = os.path.basename(fpath)
                found_runs.setdefault(nid, []).append((fname, d))

for nid, recs in found_runs.items():
    print(f"\nnote_id={nid}:")
    for fname, d in recs:
        print(f"  [{fname}] passed={d.get('filter_passed')} reason={d.get('filter_reasons','')}")
        print(f"    title={d.get('title','')[:50]}")

if not found_runs:
    print("Not found in any runs files")

# Search all collected jsonl files
print("\n=== Search all collected JSONL ===")
all_collected = glob.glob('data/collected/*.jsonl')
found_collected = {}
for fpath in sorted(all_collected):
    fname = os.path.basename(fpath)
    with open(fpath, encoding='utf-8') as f:
        for line in f:
            try:
                d = json.loads(line)
            except:
                continue
            nid = d.get('note_id') or ''
            if any(t in nid for t in target):
                found_collected.setdefault(nid, []).append((fname, d))

for nid, recs in found_collected.items():
    print(f"\nnote_id={nid}:")
    for fname, d in recs:
        print(f"  [{fname}] passed={d.get('filter_passed')} reason={d.get('filter_reasons','')}")
        print(f"    title={d.get('title','')[:50]}")

if not found_collected:
    print("Not found in any collected JSONL")

# Check RecentStorage for these IDs
print("\n=== Check RecentStorage ===")
from utils.storage import RecentStorage
rs = RecentStorage()
for nid in target:
    is_recent = rs.is_recent(nid)
    print(f"  {nid}: is_recent={is_recent}")