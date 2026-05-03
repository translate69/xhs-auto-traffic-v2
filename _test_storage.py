# -*- coding: utf-8 -*-
import sys; sys.path.insert(0, ".")
from utils.storage import CollectedStorage
from pathlib import Path

s = CollectedStorage()

# 模拟两个不同时间戳，同一关键词
run_id1 = "2026-04-29_054847_汕尾海边民宿推荐"
run_id2 = "2026-04-29_092504_汕尾海边民宿推荐"
run_id3 = "2026-04-29_092504_汕尾美食推荐"

path1 = s._run_id_to_path(run_id1)
path2 = s._run_id_to_path(run_id2)
path3 = s._run_id_to_path(run_id3)

print(f"run_id1: {run_id1}")
print(f"文件1: {path1.name}")
print()
print(f"run_id2: {run_id2}")
print(f"文件2: {path2.name}")
print(f"文件1==文件2: {path1 == path2}")
print()
print(f"run_id3: {run_id3}")
print(f"文件3: {path3.name}")
print(f"文件1!=文件3: {path1 != path3}")
