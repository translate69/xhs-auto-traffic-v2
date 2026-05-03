import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import glob, json

# 找 enrichment 结果文件
files = sorted(glob.glob("data/collected/runs/*深圳周末游*.jsonl"))
print(f"Found files: {files}")

for f in files:
    print(f"\n=== {f} ===")
    lines = open(f, encoding="utf-8", errors="replace").readlines()
    print(f"Lines: {len(lines)}")
    for line in lines[:3]:
        d = json.loads(line)
        print(f"  note_id={d.get('note_id','?')[:20]} title={d.get('title','?')[:30]}")
