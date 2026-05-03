import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

content = open("filter/filter_service.py", encoding="utf-8", errors="replace").read()
for i, line in enumerate(content.split("\n"), 1):
    if "汕尾" in line or "地域" in line or "SHANWEI" in line.upper():
        print(f"{i}: {line}")
