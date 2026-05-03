# -*- coding: utf-8 -*-
"""避免 PowerShell 中文乱码，直接在 Python 里调用 run_all"""
import sys, os

os.chdir(r"E:\translate\claw\xhs-auto-traffic-v2")
sys.path.insert(0, ".")

# 方式A: 用 run_all 的 main 函数 + 覆盖 sys.argv
sys.argv = ["run_all.py", "--keyword", "汕尾海边民宿推荐", "--limit", "8", "--debug"]

import run_all
run_all.main()