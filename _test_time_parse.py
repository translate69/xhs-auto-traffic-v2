import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from datetime import datetime
from utils.parse import parse_published_at

now = datetime.now()
print(f"Today: {now}")

test_cases = [
    "4天前",
    "2天前", 
    "5天前",
    "04-12",
    "04-29",
]

for t in test_cases:
    dt = parse_published_at(t)
    if dt:
        age = (now - dt).days
        print(f"  '{t}' -> {dt} -> age={age} days -> {'PASS' if age <= 5 else 'FAIL'}")
    else:
        print(f"  '{t}' -> None")