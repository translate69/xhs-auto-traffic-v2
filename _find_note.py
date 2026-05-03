import json
from pathlib import Path

PROJECT_ROOT = Path(r'E:\translate\claw\xhs-auto-traffic-v2')
RUN_DIR = PROJECT_ROOT / 'data' / 'collected' / 'runs'

files = sorted(RUN_DIR.glob('*.jsonl'), key=lambda f: f.stat().st_mtime, reverse=True)
print(f"Files: {len(files)}")

# Find 汕尾去哪住 (count how many have this keyword)
for f in files[:6]:
    print(f"\n{f.name}:")
    try:
        with open(f, 'r', encoding='utf-8', errors='replace') as fp:
            for i, line in enumerate(fp):
                rec = json.loads(line.strip())
                print(f"  [{i}] run_id={rec.get('run_id', '')[:55]}")
                print(f"      keyword={rec.get('keyword', '')[:30]}")
                print(f"      filter_passed={rec.get('filter_passed')}, reasons={rec.get('filter_reasons', '')[:15]}")
                if i >= 1:
                    break
    except Exception as e:
        print(f"  err: {e}")