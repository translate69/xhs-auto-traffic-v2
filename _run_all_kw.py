import subprocess, sys, time, os
from pathlib import Path

PROJECT_ROOT = Path("E:/translate/claw/xhs-auto-traffic-v2")
MAIN_SCRIPT = PROJECT_ROOT / "main.py"

keywords = [
    ("汕尾旅游攻略", "core"),
    ("汕尾住宿推荐", "core"),
    ("汕尾美食推荐", "core"),
    ("汕尾去哪吃", "core"),
    ("汕尾去哪住", "core"),
    ("汕尾旅游", "core"),
    ("汕尾美食", "core"),
    ("广州到汕尾自驾住哪", "longtail"),
    ("深圳到汕尾自驾住哪", "longtail"),
    ("汕尾红海湾民宿", "longtail"),
    ("汕尾红海湾攻略", "longtail"),
    ("汕尾3天2晚攻略", "longtail"),
    ("汕尾2天1晚行程", "longtail"),
    ("汕尾本地人推荐美食", "longtail"),
    ("汕尾海边民宿推荐", "longtail"),
    ("汕尾周末去哪玩", "longtail"),
    ("汕尾亲子游", "longtail"),
]

results = []
for i, (keyword, group) in enumerate(keywords, 1):
    print(f"\n[{i}/{len(keywords)}] [{group}] {keyword}")
    task_id = "tmp" + os.urandom(4).hex()
    stdout_f = PROJECT_ROOT / "logs" / f"_s_{task_id}.tmp"
    stderr_f = PROJECT_ROOT / "logs" / f"_e_{task_id}.tmp"

    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    cmd = [sys.executable, str(MAIN_SCRIPT), "--keyword", keyword, "--limit", "10"]

    for attempt in range(3):
        stdout_f.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(stdout_f, "w", encoding="utf-8", errors="replace") as fout, \
                 open(stderr_f, "w", encoding="utf-8", errors="replace") as ferr:
                proc = subprocess.Popen(cmd, stdout=fout, stderr=ferr,
                    cwd=str(PROJECT_ROOT), env=env,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
                try:
                    proc.wait(timeout=60)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
                    print(f"  超时")
                    continue
                break
        except Exception as e:
            print(f"  错误: {e}")
            continue

    time.sleep(2)

    stdout = ""
    try:
        stdout = stdout_f.read_text(encoding="utf-8", errors="replace")
    except:
        pass
    print(f"  stdout snippet: {stdout[:200].replace(chr(10),' ')}")

    try:
        stdout_f.unlink(missing_ok=True)
        stderr_f.unlink(missing_ok=True)
    except:
        pass

print("\n完成")