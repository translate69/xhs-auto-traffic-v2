# -*- coding: utf-8 -*-
"""触发 run_all.py single keyword"""
import sys, os
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
os.chdir(r"E:\translate\claw\xhs-auto-traffic-v2")

import run_all
sys.argv = ["run_all.py", "--keyword", "汕尾海边民宿推荐", "--limit", "8", "--debug"]
run_all.main()