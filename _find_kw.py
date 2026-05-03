import pathlib, json, sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

run_dir = pathlib.Path('E:/translate/claw/xhs-auto-traffic-v2/data/collected/runs')

# List all files
all_files = sorted(run_dir.glob('*.jsonl'))
print(f"Total: {len(all_files)} files")

# Find enrichment files (date_keyword.jsonl format - no time component)
enrichment_files = [f for f in all_files if f.name.startswith('2026-04-29_') and f.name.count('_') == 2]
print(f"\nEnrichment files: {len(enrichment_files)}")
for f in enrichment_files:
    lines = f.read_text('utf-8', errors='replace').strip().split('\n')
    print(f"  {len(lines):3d}条 {f.name}")

# Check 汕尾旅游攻略
matching = list(run_dir.glob('*汕尾旅游攻略*'))
print(f"\nFiles matching '汕尾旅游攻略':")
for f in matching:
    lines = f.read_text('utf-8', errors='replace').strip().split('\n')
    print(f"  {len(lines):3d}条 {f.name}")