import glob, os

content = open("core/browser_manager.py", encoding="utf-8", errors="replace").read()
hits = [(i+1, line) for i, line in enumerate(content.split("\n")) if "cookie" in line.lower() or "xhs_cookies" in line.lower()]
print(f"browser_manager.py - {len(hits)} hits:")
for lineno, line in hits:
    print(f"  {lineno}: {line.strip()}")
