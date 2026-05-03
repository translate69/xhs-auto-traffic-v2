import sys
sys.path.insert(0, '.')
content = open("utils/feishu_client.py", encoding="utf-8", errors="replace").read()
for i, line in enumerate(content.split("\n"), 1):
    if "无有效" in line or "token" in line.lower():
        print(f"{i}: {line.rstrip()}")
