import subprocess

out = subprocess.check_output(
    ["tasklist", "/FI", "IMAGENAME eq chrome.exe", "/FO", "CSV", "/NH"],
    text=True, encoding="gbk"
)

lines = [l for l in out.strip().split("\n") if l]
print(f"Total Chrome processes: {len(lines)}")

large = []
small = []
for line in lines:
    # Format: "chrome.exe","PID","Console","1","MEM K"
    parts = line.split(",")
    if len(parts) < 5:
        continue
    pid = parts[1].strip().strip('"')
    mem = parts[4].strip().strip('"').replace(",", "").replace(" K", "").replace("K", "")
    try:
        mem_mb = int(mem) // 1024
    except:
        mem_mb = 0
    if mem_mb > 100:
        large.append((pid, mem_mb))
    elif mem_mb > 20:
        small.append((pid, mem_mb))

print(f"\nLarge (>100MB) - likely Playwright: {len(large)}")
for pid, mb in large:
    print(f"  PID {pid}: {mb} MB")

print(f"\nMedium (20-100MB): {len(small)}")
for pid, mb in small:
    print(f"  PID {pid}: {mb} MB")

if len(large) > 2:
    print(f"\n⚠️  {len(large)} large Chrome processes - likely orphaned Playwright")
    print("   Run cleanup?")
else:
    print("\n✅ Chrome processes look normal")
