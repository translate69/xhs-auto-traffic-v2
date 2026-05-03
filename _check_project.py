"""Check project code status"""
import subprocess, os

proj = r'E:\translate\claw\xhs-auto-traffic-v2'

# Git status
r = subprocess.run(['git', 'status', '--short'], capture_output=True, cwd=proj)
print('=== Git Status ===')
print(r.stdout.decode())

# Key files
key_files = [
    'main.py', 'config.py',
    'filter/filter_service.py',
    'filter/review_service.py',
    'filter/classifier.py',
    'core/note_detail.py',
    'core/search_collector.py',
    'output/feishu_service.py',
]
print('\n=== Key Files ===')
for f in key_files:
    path = os.path.join(proj, f)
    size = os.path.getsize(path) if os.path.exists(path) else 0
    print(f'  {f}: {size} bytes')

# Filter service functions
print('\n=== filter_service.py functions ===')
with open(os.path.join(proj, 'filter/filter_service.py'), encoding='utf-8') as f:
    lines = f.readlines()
funcs = [l.strip() for l in lines if l.strip().startswith('def ') and not l.strip().startswith('def has_signal')]
for f in funcs:
    print(f'  {f}')
print(f'  has_signal (standalone): {lines[0] if lines else ""}')

# Review service
print('\n=== review_service.py ===')
with open(os.path.join(proj, 'filter/review_service.py'), encoding='utf-8') as f:
    rs = f.read()
rs_lines = rs.split('\n')
funcs_rs = [l.strip() for l in rs_lines if l.strip().startswith('def ')]
for f in funcs_rs:
    print(f'  {f}')

# Main.py stages
print('\n=== main.py stage options ===')
with open(os.path.join(proj, 'main.py'), encoding='utf-8') as f:
    main_lines = f.read()
import re
stage_match = re.search(r'--stage.*?{[^}]+}', main_lines)
if stage_match:
    print(f'  {stage_match.group()}')

# Count untracked debug files
r2 = subprocess.run(['git', 'ls-files', '--others', '--exclude-standard'], capture_output=True, cwd=proj)
others = r2.stdout.decode().strip().split('\n')
debug_files = [f for f in others if f.startswith('_debug') or f.startswith('_test') or f.startswith('_check')]
print(f'\n=== Untracked debug/test files: {len(debug_files)} ===')
for f in debug_files[:20]:
    print(f'  {f}')
if len(debug_files) > 20:
    print(f'  ... and {len(debug_files)-20} more')