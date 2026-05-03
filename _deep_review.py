"""Deep review: check for production cron readiness issues"""
import sys, os, re
sys.path.insert(0, r'E:\translate\claw\xhs-auto-traffic-v2')
for k in list(sys.modules.keys()):
    if 'filter' in k or 'output' in k: del sys.modules[k]

from output.feishu_service import FeishuOutputService

# 1. Check FeishuOutputService for deduplication
import inspect
src = inspect.getsource(FeishuOutputService.write)
print('=== FeishuOutputService.write ===')
print(src[:3000])

# 2. Check if there's existing data deduplication logic
print('\n=== Checking for dedup in feishu_service ===')
with open(r'E:\translate\claw\xhs-auto-traffic-v2\output\feishu_service.py', encoding='utf-8') as f:
    fs_content = f.read()
for line in fs_content.split('\n'):
    if any(kw in line.lower() for kw in ['dedup', 'duplicate', 'exist', 'skip', 'already']):
        print(f'  {line.rstrip()}')