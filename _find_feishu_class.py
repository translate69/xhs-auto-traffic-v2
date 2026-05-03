import subprocess, sys, pathlib, json

result = subprocess.run(
    [sys.executable, "-c",
     "import output.feishu_service as fs; print([x for x in dir(fs) if not x.startswith('_')])"],
    capture_output=True, text=True, encoding="utf-8", errors="replace",
    cwd=r'E:\translate\claw\xhs-auto-traffic-v2'
)
print(result.stdout)
print(result.stderr)