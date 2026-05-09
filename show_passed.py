# -*- coding: utf-8 -*-
"""查看最新测试结果"""
import json, sys, os, glob
sys.stdout.reconfigure(encoding='utf-8')

files = sorted(glob.glob('data/collected/runs/2026-05-09_*.jsonl'), key=os.path.getmtime, reverse=True)
latest = files[0]
print(f"Latest: {os.path.basename(latest)}\n")

with open(latest, encoding='utf-8') as f:
    lines = f.readlines()

passed = [json.loads(l) for l in lines if json.loads(l).get('filter_passed')]
no_demand = [json.loads(l) for l in lines if not json.loads(l).get('filter_passed') and '无明确需求' in json.loads(l).get('filter_reasons', '')]
share = [json.loads(l) for l in lines if not json.loads(l).get('filter_passed') and '纯分享攻略贴' in json.loads(l).get('filter_reasons', '')]
other = [json.loads(l) for l in lines if not json.loads(l).get('filter_passed') and '无明确需求' not in json.loads(l).get('filter_reasons', '') and '纯分享攻略贴' not in json.loads(l).get('filter_reasons', '')]

print(f"Total: {len(lines)} | Passed: {len(passed)} | NoDemand: {len(no_demand)} | Share: {len(share)} | Other: {len(other)}\n")

if passed:
    print(f"=== 通过 ({len(passed)} 条) ===")
    for d in passed:
        print(f"  [{d.get('note_id')}] {d.get('title', '')[:50]}")
        print(f"    {d.get('content', '')[:80]}")
else:
    print("(无通过笔记)")
    print(f"\n无明确需求样本 (前3):")
    for d in no_demand[:3]:
        print(f"  {d.get('title', '')[:40]} | {d.get('content', '')[:60]}")
    print(f"\n纯分享攻略贴样本 (前3):")
    for d in share[:3]:
        print(f"  {d.get('title', '')[:40]} | {d.get('content', '')[:60]}")
    if other:
        print(f"\n其他样本:")
        for d in other[:3]:
            print(f"  reason={d.get('filter_reasons', '')} | {d.get('title', '')[:40]}")
