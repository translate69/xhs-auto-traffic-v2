import sys
sys.path.insert(0, '.')
content = open("keywords.txt", encoding="utf-8", errors="replace").read()
for i, line in enumerate(content.split("\n"), 1):
    line = line.strip()
    if line and not line.startswith("#"):
        print(f"{i}: {line}")
