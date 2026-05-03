import pathlib, json, sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from output.feishu_service import FeishuOutputService, NoteDetail
from filter.filter_service import FilterService

run_dir = pathlib.Path('E:/translate/claw/xhs-auto-traffic-v2/data/collected/runs')
kw = "汕尾旅游攻略"

f = run_dir / f"2026-04-29_{kw}.jsonl"
lines = f.read_text('utf-8', errors='replace').strip().split('\n')
print(f"Enrichment: {len(lines)} records")

# Build NoteDetails
details = []
for line in lines:
    d = json.loads(line)
    nd = NoteDetail(
        title=d.get('title', ''),
        content=d.get('content', ''),
        author=d.get('author', ''),
        url=d.get('url', ''),
        likes=d.get('likes'),
        published_at=d.get('published_at', ''),
    )
    nd.keyword = kw
    details.append(nd)

print(f"NoteDetails built: {len(details)}")

# Filter
fs = FilterService()
passed = fs.filter_all(details, keyword=kw)
print(f"Filter: {len(passed)}/{len(details)} passed")

if passed:
    print(f"\nFeishu write...")
    feishu = FeishuOutputService()
    result = feishu.write(passed)
    print(f"Feishu: {result}")
else:
    print("No notes passed filter")