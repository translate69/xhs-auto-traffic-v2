"""Check FeishuOutputService write and keywords"""
import os

proj = r'E:\translate\claw\xhs-auto-traffic-v2'

# Check keywords.txt
kw_file = os.path.join(proj, 'keywords.txt')
print('=== keywords.txt ===')
if os.path.exists(kw_file):
    with open(kw_file, encoding='utf-8') as f:
        lines = f.read().splitlines()
    for line in lines:
        if line.strip() and not line.strip().startswith('#'):
            print(f'  {line.strip()}')
    active = [l for l in lines if l.strip() and not l.strip().startswith('#')]
    print(f'Total active keywords: {len(active)}')

# Check FeishuOutputService.write handles NoteDetail
print()
print('=== FeishuOutputService.write ===')
with open(os.path.join(proj, 'output/feishu_service.py'), encoding='utf-8') as f:
    fs = f.read()
idx = fs.find('def write(')
print(fs[idx:idx+800])

# Check _note_detail_to_row
idx2 = fs.find('def _note_detail_to_row')
if idx2 >= 0:
    print('\n=== _note_detail_to_row ===')
    print(fs[idx2:idx2+600])