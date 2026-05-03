"""Test run_all with keyword argument"""
import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
sys.stdout.reconfigure(encoding="utf-8")

from load_keywords import load_keywords

all_kw = load_keywords()
print(f"Total keywords: {len(all_kw)}")
for kw in all_kw:
    print(f"  [{kw['group']}] {kw['keyword']}")

# Check filtering
target = "汕尾美食"
filtered = [kw for kw in all_kw if kw["keyword"] == target]
print(f"\nFiltered for '{target}': {len(filtered)}")