"""Check main.py stage options and pipeline flow"""
import os

proj = r'E:\translate\claw\xhs-auto-traffic-v2'

# Read main.py
with open(os.path.join(proj, 'main.py'), encoding='utf-8') as f:
    content = f.read()

print('=== main.py stage option ===')
import re
# Find all stage-related lines
for line in content.split('\n'):
    if 'stage' in line.lower() or 'collect' in line.lower() or 'feishu' in line.lower():
        print(f'  {line.rstrip()}')

print('\n=== main.py key flow ===')
# Find key method calls
in_main = content[content.find('def main'):]
func_lines = [l.rstrip() for l in in_main.split('\n')[:60] if l.strip() and not l.strip().startswith('#')]
for l in func_lines[:30]:
    print(f'  {l}')

print('\n=== config FEISHU_DIR ===')
with open(os.path.join(proj, 'config.py'), encoding='utf-8') as f:
    cfg = f.read()
for line in cfg.split('\n'):
    if 'FEISHU' in line or 'feishu' in line:
        print(f'  {line.rstrip()}')

print('\n=== review_service.py key rules ===')
with open(os.path.join(proj, 'filter/review_service.py'), encoding='utf-8') as f:
    rs = f.read()
# Show the merchant author and recommendation format methods
for line in rs.split('\n'):
    stripped = line.strip()
    if any(kw in stripped for kw in ['MERCHANT', 'SHARE', 'reasons', 'reject', 'def _is']):
        print(f'  {line.rstrip()}')