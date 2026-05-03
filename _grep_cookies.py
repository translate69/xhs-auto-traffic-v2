import os, glob

for py in glob.glob("*.py"):
    if py.startswith("_"):
        try:
            content = open(py, encoding="utf-8", errors="replace").read()
            if "xhs_cookies" in content or "COOKIE_FILE" in content or "add_cookies" in content:
                print(f"{py}:")
                for i, line in enumerate(content.split("\n"), 1):
                    if "xhs_cookies" in line or "COOKIE_FILE" in line or "add_cookies" in line:
                        print(f"  {i}: {line.strip()}")
        except:
            pass
