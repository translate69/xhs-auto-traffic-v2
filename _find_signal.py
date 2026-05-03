import sys
sys.path.insert(0, '.')
content = open("filter/filter_service.py", encoding="utf-8", errors="replace").read()
for i, line in enumerate(content.split("\n"), 1):
    if "def has_signal" in line or "has_signal" in line and "def" in line:
        print(f"{i}: {line.rstrip()}")
