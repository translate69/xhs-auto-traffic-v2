"""Deep check: browser crash recovery, log dir, cron trigger, empty pipeline"""
import sys, os, re
sys.path.insert(0, r'E:\translate\claw\xhs-auto-traffic-v2')

from pathlib import Path

# 1. Log directory
log_dir = Path(r'E:\translate\claw\xhs-auto-traffic-v2\logs')
print(f'=== logs/ dir ===')
print(f'  exists: {log_dir.exists()}')
if log_dir.exists():
    files = list(log_dir.glob('*'))
    print(f'  files: {len(files)}')
    for f in sorted(files)[-5:]:
        print(f'    {f.name}: {f.stat().st_size} bytes')

# 2. Browser crash recovery in browser_manager.py
print('\n=== browser_manager.py: crash recovery ===')
with open(r'E:\translate\claw\xhs-auto-traffic-v2\core\browser_manager.py', encoding='utf-8') as f:
    bm = f.read()
for line in bm.split('\n'):
    if any(kw in line.lower() for kw in ['crash', 'restart', 'relaunch', 'retry', 'error', 'fail']):
        print(f'  {line.rstrip()}')

# 3. Check run_batch.py for cron trigger
print('\n=== run_batch.py ===')
with open(r'E:\translate\claw\xhs-auto-traffic-v2\run_batch.py', encoding='utf-8') as f:
    rb = f.read()
print(rb[:3000])

# 4. Check config for TIME_THRESHOLD_DAYS
print('\n=== config TIME_THRESHOLD_DAYS ===')
with open(r'E:\translate\claw\xhs-auto-traffic-v2\config.py', encoding='utf-8') as f:
    cfg = f.read()
for line in cfg.split('\n'):
    if 'TIME' in line or 'threshold' in line.lower() or 'days' in line.lower():
        print(f'  {line.rstrip()}')

# 5. Check main.py - does it handle empty results?
print('\n=== main.py: empty results handling ===')
with open(r'E:\translate\claw\xhs-auto-traffic-v2\main.py', encoding='utf-8') as f:
    main_content = f.read()
if 'filtered' in main_content or 'passed' in main_content:
    for line in main_content.split('\n'):
        if 'filtered' in line or ('len(passed)' in line or 'len(feeds)' in line):
            print(f'  {line.rstrip()}')