import json
import sys
sys.path.insert(0, r'E:\translate\claw\xhs-auto-traffic-v2')

from filter.filter_service import FilterService

svc = FilterService()

# Load note directly from runs
from pathlib import Path
RUN_DIR = Path(r'E:\translate\claw\xhs-auto-traffic-v2\data\collected\runs')

files = sorted(RUN_DIR.glob('*.jsonl'), key=lambda f: f.stat().st_mtime, reverse=True)
target_note_id = '69f333680000000038035df0'

for f in files:
    try:
        with open(f, 'r', encoding='utf-8', errors='replace') as fp:
            for line in fp:
                rec = json.loads(line.strip())
                if rec.get('note_id') == target_note_id:
                    print('FOUND in', f.name)
                    print('keyword:', rec.get('keyword'))
                    print('title:', rec.get('title'))
                    print('author:', rec.get('author'))
                    print('content:', rec.get('content', '')[:300])
                    print('tags:', rec.get('tags', []))
                    print('filter_passed:', rec.get('filter_passed'))
                    print('filter_reasons:', rec.get('filter_reasons'))
                    print()
                    # Run filter on this note
                    from core.note_detail import NoteDetail
                    note = NoteDetail(
                        url=rec.get('url', ''),
                        title=rec.get('title', ''),
                        author=rec.get('author', ''),
                        content=rec.get('content', ''),
                        published_at=rec.get('published_at', ''),
                    )
                    note.xsec_token = rec.get('xsec_token', '') or ''
                    note.time_text = rec.get('time_text', '') or ''
                    note.images = rec.get('images', []) or []
                    note.tags = rec.get('tags', []) or []
                    note.likes = rec.get('likes', 0) or 0
                    note.collects = rec.get('collects', 0) or 0
                    note.comments = rec.get('comments', 0) or 0
                    note.author_id = rec.get('author_id', '') or ''
                    note.keyword = rec.get('keyword', '') or ''

                    result = svc.filter_one(note)
                    print('--- Filter Result ---')
                    print('passed:', result.filter_passed)
                    print('reasons:', result.filter_reasons)
                    print('type:', result.filter_type)
                    print()
                    # Show intermediate steps
                    content = rec.get('content', '')
                    content_no_tags = svc._strip_tags(content) if hasattr(svc, '_strip_tags') else content
                    print('content_no_tags:', content_no_tags[:200])
                    break
    except Exception as e:
        print('err:', e)