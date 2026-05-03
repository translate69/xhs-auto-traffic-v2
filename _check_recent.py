import sys, json
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from utils.storage import RecentStorage

rs = RecentStorage()
print(f"RecentStorage seen count: {len(rs._seen)}")
print(f"First 10 note_ids:")
for nid in list(rs._seen)[:10]:
    print(f"  {nid}")

# Test is_recent on specific IDs from debug output
test_ids = [
    "69f065e2000000001f001cbe",
    "69ef913a000000002301c5a6",
    "69ef210e000000001e00fe7c",
    "69ef7e3f000000003501d790",
    "69ef7dfd000000003501d652",
]
print("\nis_recent tests:")
for nid in test_ids:
    print(f"  {nid}: {rs.is_recent(nid)}")