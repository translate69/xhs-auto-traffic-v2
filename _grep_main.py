import glob, os

target_files = ["run_all.py", "main.py", "run_single_debug.py", "run_debug.py"]
for fname in target_files:
    if not os.path.exists(fname):
        print(f"{fname}: NOT FOUND")
        continue
    content = open(fname, encoding="utf-8", errors="replace").read()
    hits = [(i+1, line) for i, line in enumerate(content.split("\n")) if "cookie" in line.lower() or "xhs_cookies" in line]
    if hits:
        print(f"\n{fname} - {len(hits)} hits:")
        for lineno, line in hits:
            print(f"  {lineno}: {line.strip()}")
    else:
        print(f"{fname}: no cookie references")