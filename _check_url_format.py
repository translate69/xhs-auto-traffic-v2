import glob, os

files = ["output/feishu_service.py", "core/note_detail.py", "core/search_collector.py"]
for fname in files:
    if not os.path.exists(fname):
        print(f"{fname}: NOT FOUND")
        continue
    content = open(fname, encoding="utf-8", errors="replace").read()
    hits = [(i+1, line) for i, line in enumerate(content.split("\n")) if "explore" in line.lower() and "url" in line.lower()]
    if hits:
        print(f"\n{fname}:")
        for lineno, line in hits:
            print(f"  {lineno}: {line.strip()}")
    else:
        print(f"{fname}: no explore+url hits")
