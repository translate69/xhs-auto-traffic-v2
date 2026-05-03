import sys, pathlib, json
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from output.feishu_service import FeishuOutputService, NoteDetail
from filter.filter_service import FilterService

# Load data - 汕尾去哪吃
files = list(pathlib.Path('data/collected/runs').glob('*去哪吃*'))
if not files:
    print("No file found")
    sys.exit(1)

lines = files[0].read_text('utf-8', errors='replace').strip().split('\n')
print(f"Loaded {len(lines)} notes")

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
    nd.keyword = '汕尾去哪吃'
    details.append(nd)

print(f"\n=== Filter ===")
fs = FilterService()
passed = fs.filter_all(details, keyword='汕尾去哪吃')
print(f"Filter: {len(passed)}/{len(details)} passed")

if passed:
    print(f"\n=== Feishu Write ===")
    feishu = FeishuOutputService()
    result = feishu.write_records(passed)
    print(f"Feishu: {result}")
else:
    print("No notes passed filter, skipping Feishu write")