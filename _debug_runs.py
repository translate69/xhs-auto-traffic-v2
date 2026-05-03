import json
from pathlib import Path

PROJECT_ROOT = Path(r'E:\translate\claw\xhs-auto-traffic-v2')
RUN_DIR = PROJECT_ROOT / 'data' / 'collected' / 'runs'
MANIFEST = PROJECT_ROOT / 'data' / 'collected_manifest.jsonl'

# Read manifest for recent 04-30 entries
print("=== MANIFEST (04-30) ===")
with open(MANIFEST, 'r', encoding='utf-8', errors='replace') as f:
    for line in f:
        line = line.strip()
        if not line: continue
        try:
            e = json.loads(line)
            run_id = e.get('run_id', '')
            if '2026-04-30' in run_id:
                print(f"  manifest run_id: {run_id}")
                print(f"    keyword={e.get('keyword')}, note_count={e.get('note_count')}, completed={e.get('completed_at')}")
        except: pass

# Read runs/ directory - look for our 3 recent runs
print("\n=== RUNS FILES ===")
files = sorted(RUN_DIR.glob('*.jsonl'), key=lambda f: f.stat().st_mtime, reverse=True)
for f in files[:6]:
    print(f"  file: {f.name}  mtime:{f.stat().st_mtime}")

# Read actual data from 04-30 files with proper encoding
print("\n=== 04-30 FILES CONTENT ===")
for f in sorted(RUN_DIR.glob('*.jsonl'), key=lambda f: f.stat().st_mtime, reverse=True)[:4]:
    print(f"\nfile: {f.name}")
    # Try to read with utf-8, replace errors
    try:
        with open(f, 'r', encoding='utf-8', errors='replace') as fp:
            for i, line in enumerate(fp):
                if i >= 2: break
                rec = json.loads(line.strip())
                print(f"  rec run_id={rec.get('run_id', '')[:55]}")
                print(f"  keyword={rec.get('keyword', '')[:30]}")
                print(f"  filter_passed={rec.get('filter_passed')}, filter_reasons={rec.get('filter_reasons', '')[:20]}")
                print(f"  note_id={str(rec.get('note_id', ''))[:20]}")
    except Exception as e:
        print(f"  err: {e}")