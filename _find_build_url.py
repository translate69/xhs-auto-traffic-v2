import glob

for py in ["core/note_detail.py"]:
    content = open(py, encoding="utf-8", errors="replace").read()
    for i, line in enumerate(content.split("\n"), 1):
        if "_build_detail_url" in line or "explore" in line or "detail_url" in line:
            print(f"{py}:{i}: {line.strip()}")
