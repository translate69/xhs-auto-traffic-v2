"""Write deep review results to file"""
import sys, os, re
sys.path.insert(0, r'E:\translate\claw\xhs-auto-traffic-v2')
from pathlib import Path

out = []

# 1. Log directory
log_dir = Path(r'E:\translate\claw\xhs-auto-traffic-v2\logs')
out.append(f'=== logs/ dir: {len(list(log_dir.glob("*")))} files ===')
for f in sorted(log_dir.glob('*'))[-5:]:
    out.append(f'  {f.name}: {f.stat().st_size} bytes')

# 2. Browser crash recovery
out.append('\n=== browser_manager.py key sections ===')
with open(r'E:\translate\claw\xhs-auto-traffic-v2\core\browser_manager.py', encoding='utf-8') as f:
    bm = f.read()
critical_lines = [l.rstrip() for l in bm.split('\n') if any(kw in l.lower() for kw in ['crash', 'restart', 'relaunch', 'try:', 'except', 'finally'])]
out.append('\n'.join(critical_lines[:30]))

# 3. run_batch.py
out.append('\n=== run_batch.py (full) ===')
with open(r'E:\translate\claw\xhs-auto-traffic-v2\run_batch.py', encoding='utf-8') as f:
    rb_lines = f.read().split('\n')
out.append('\n'.join(rb_lines))

# 4. config TIME_THRESHOLD
out.append('\n=== config TIME_THRESHOLD_DAYS ===')
with open(r'E:\translate\claw\xhs-auto-traffic-v2\config.py', encoding='utf-8') as f:
    cfg_lines = f.read().split('\n')
out.append('\n'.join(l for l in cfg_lines if 'TIME' in l or 'threshold' in l.lower() or 'days' in l.lower()))

# 5. main.py empty handling
out.append('\n=== main.py flow (checking empty/passed len) ===')
with open(r'E:\translate\claw\xhs-auto-traffic-v2\main.py', encoding='utf-8') as f:
    main_lines = f.read().split('\n')
out.append('\n'.join(l.rstrip() for l in main_lines))

# 6. Check batch_write for dedup
out.append('\n=== feishu_client batch_write ===')
with open(r'E:\translate\claw\xhs-auto-traffic-v2\utils\feishu_client.py', encoding='utf-8') as f:
    fc = f.read()
idx = fc.find('def batch_write')
if idx >= 0:
    out.append(fc[idx:idx+1500])

# 7. Check load_existing_note_ids
out.append('\n=== feishu_client load_existing_note_ids ===')
idx2 = fc.find('def load_existing_note_ids')
if idx2 >= 0:
    out.append(fc[idx2:idx2+1000])

# 8. Check search_collector for browser error recovery
out.append('\n=== search_collector: error recovery ===')
with open(r'E:\translate\claw\xhs-auto-traffic-v2\core\search_collector.py', encoding='utf-8') as f:
    sc = f.read()
sc_critical = [l.rstrip() for l in sc.split('\n') if any(kw in l.lower() for kw in ['except', 'retry', 'crash', 'restart', 'relauch'])]
out.append('\n'.join(sc_critical[:20]))

# 9. Check note_detail for error recovery
out.append('\n=== note_detail: error recovery ===')
with open(r'E:\translate\claw\xhs-auto-traffic-v2\core\note_detail.py', encoding='utf-8') as f:
    nd = f.read()
nd_critical = [l.rstrip() for l in nd.split('\n') if any(kw in l.lower() for kw in ['except', 'retry', 'crash', 'finally'])]
out.append('\n'.join(nd_critical[:20]))

# Write to file
with open(r'E:\translate\claw\xhs-auto-traffic-v2\_deep_review_report.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('Written _deep_review_report.txt')