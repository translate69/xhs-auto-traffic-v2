import subprocess, sys, pathlib

result = subprocess.run(
    [sys.executable, "-c",
     """
import sys; sys.path.insert(0, '.')
from output.feishu_service import FeishuOutputService
print([x for x in dir(FeishuOutputService) if not x.startswith('_')])
"""],
    capture_output=True, text=True, encoding="utf-8", errors="replace",
    cwd=r'E:\translate\claw\xhs-auto-traffic-v2'
)
print(result.stdout)
print(result.stderr[:300] if result.stderr else "")