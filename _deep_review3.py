"""Deep analysis: run_batch.py vs main.py review gate gap"""
import sys, os, re
sys.path.insert(0, r'E:\translate\claw\xhs-auto-traffic-v2')

# Check if run_batch.py uses ReviewService
with open(r'E:\translate\claw\xhs-auto-traffic-v2\run_batch.py', encoding='utf-8') as f:
    rb = f.read()

print('=== run_batch.py: uses ReviewService? ===')
print('ReviewService' in rb)  # False
print()

# Check filter flow in run_batch vs main
print('=== run_batch.py filter flow ===')
for i, line in enumerate(rb.split('\n')):
    if any(kw in line for kw in ['filter', 'Review', 'review', 'feishu', 'passed_note']):
        print(f'  {i+1}: {line.rstrip()}')

print()
print('=== main.py filter flow ===')
with open(r'E:\translate\claw\xhs-auto-traffic-v2\main.py', encoding='utf-8') as f:
    main = f.read()
for i, line in enumerate(main.split('\n')):
    if any(kw in line for kw in ['filter', 'Review', 'review', 'feishu', 'passed_note']):
        print(f'  {i+1}: {line.rstrip()}')

# Check how main.py passes data to feishu
print()
print('=== main.py: how feishu gets data ===')
idx = main.find('feishu.write')
print(main[idx-200:idx+300])

# Check run_batch how feishu gets data
print()
print('=== run_batch.py: how feishu gets data ===')
idx_rb = rb.find('feishu.write')
print(rb[idx_rb-300:idx_rb+200])

# Check if run_batch writes filtered_for_feishu.jsonl
print()
print('=== run_batch.py writes jsonl files? ===')
for kw in ['filtered_for_feishu', 'reviewed_for_feishu', 'jsonl', 'save']:
    if kw in rb:
        print(f'  Found: {kw}')
        for i, line in enumerate(rb.split('\n')):
            if kw in line:
                print(f'    {i+1}: {line.rstrip()}')