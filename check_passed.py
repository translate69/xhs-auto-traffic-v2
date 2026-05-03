import json
from pathlib import Path

data_dir = Path('E:/translate/claw/xhs-auto-traffic-v2/data/collected/runs')
files = sorted(data_dir.glob('*.jsonl'), key=lambda f: f.stat().st_mtime, reverse=True)

passed_notes = []

for f in files:
    fname = f.name
    if '2026-05-02' not in fname and '2026-05-03' not in fname:
        continue
    with open(f, 'r', encoding='utf-8') as fp:
        for line in fp:
            try:
                obj = json.loads(line.strip())
                if obj.get('filter_passed') == True:
                    note_id = obj.get('note_id', '')
                    title = (obj.get('title') or '')[:40]
                    content = (obj.get('content') or '')[:60]
                    reasons = obj.get('filter_reasons', '')
                    url = obj.get('url', '')
                    published_at = obj.get('published_at', '')
                    passed_notes.append({
                        'file': fname,
                        'note_id': note_id,
                        'title': title,
                        'content': content,
                        'reasons': reasons,
                        'url': url,
                        'published_at': published_at
                    })
            except:
                pass

print(f'Total passed notes: {len(passed_notes)}')
for n in passed_notes:
    print(f'[{n["file"]}]')
    print(f'  note_id={n["note_id"]}')
    print(f'  reasons={n["reasons"]}')
    print(f'  title={n["title"]}')
    print(f'  content={n["content"]}')
    print(f'  url={n["url"]}')
    print()