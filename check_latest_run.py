# -*- coding: utf-8 -*-
import json, sys, glob
sys.stdout.reconfigure(encoding='utf-8')

files = sorted(glob.glob('data/collected/runs/2026-05-09_*.jsonl'))
latest = files[-1]
with open(latest, encoding='utf-8') as f:
    lines = f.readlines()

passed = []
rejected_non_geo = []  # 非目标地域
rejected_no_demand = []  # 无明确需求
other = []

for line in lines:
    d = json.loads(line)
    reasons = d.get('filter_reasons', '')
    if d.get('filter_passed'):
        passed.append(d)
    elif '非目标地域' in reasons:
        rejected_non_geo.append(d)
    elif '无明确需求' in reasons:
        rejected_no_demand.append(d)
    else:
        other.append((reasons, d))

print(f"Total: {len(lines)}, Passed: {len(passed)}, NonGeo: {len(rejected_non_geo)}, NoDemand: {len(rejected_no_demand)}, Other: {len(other)}")

print("\n=== NoDemand samples (first 3) ===")
for d in rejected_no_demand[:3]:
    print(f"  [{d.get('note_id')}] {d.get('title','')[:40]}")
    print(f"    content: {d.get('content','')[:100]}")
    print(f"    reasons: {d.get('filter_reasons','')}")

print("\n=== Other samples ===")
for r, d in other[:5]:
    print(f"  reason={r}")
    print(f"  [{d.get('note_id')}] {d.get('title','')[:40]}")
    print(f"    content: {d.get('content','')[:100]}")