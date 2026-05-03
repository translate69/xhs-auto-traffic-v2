# -*- coding: utf-8 -*-
"""运行 pipeline 测试"""
import subprocess
import sys

keyword = "汕尾亲子游"  # 正确的关键词
limit = 8

result = subprocess.run(
    [sys.executable, "main.py", "--keyword", keyword, "--limit", str(limit), "--debug"],
    capture_output=False,
    text=True,
    cwd=r"E:\translate\claw\xhs-auto-traffic-v2",
    encoding="utf-8"
)