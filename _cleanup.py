import os, sys
sys.path.insert(0, '.')
os.chdir(r"E:\translate\claw\xhs-auto-traffic-v2")

for f in ["data/collected/runs/2026-04-29_深圳周末游.jsonl",
          "data/collected/runs/2026-04-29_汕尾美食.jsonl"]:
    if os.path.exists(f):
        os.remove(f)
        print(f"Removed: {f}")
    else:
        print(f"Not found: {f}")
print("Done")
