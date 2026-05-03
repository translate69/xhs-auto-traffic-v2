import subprocess

out = subprocess.check_output(
    ["tasklist", "/FI", "IMAGENAME eq chrome.exe", "/FO", "CSV", "/NH"],
    text=True
)
lines = [l for l in out.strip().split("\n") if "chrome.exe" in l]
print(f"Total chrome.exe: {len(lines)}")

large_pids = []
for line in lines:
    # Format: "chrome.exe","PID","Console","1","289,420 K"
    parts = [p.strip('"') for p in line.split(",")]
    if len(parts) < 5:
        continue
    pid = parts[1]
    mem_raw = parts[4]  # e.g. "289,420 K"
    try:
        mem_k = int(mem_raw.replace(",", "").replace("K", "").replace("k", "").replace(" ", ""))
        mem_mb = mem_k // 1024
        if mem_mb > 100:
            print(f"  PID {pid}: {mem_mb:>6} MB <<< PLAYWRIGHT")
            large_pids.append(pid)
        elif mem_mb > 20:
            print(f"  PID {pid}: {mem_mb:>6} MB")
    except ValueError:
        pass

if large_pids:
    print(f"\nKilling {len(large_pids)} Playwright Chrome processes...")
    for pid in large_pids:
        subprocess.run(["taskkill", "/F", "/PID", pid], timeout=10)
        print(f"  Killed PID {pid}")
    print("Cleanup done")
else:
    print("No large Playwright processes (>100MB)")
