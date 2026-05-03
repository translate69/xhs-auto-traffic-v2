# -*- coding: utf-8 -*-
import json, sys, os
from pathlib import Path

sys.path.insert(0, ".")
os.chdir(r"E:\translate\claw\xhs-auto-traffic-v2")

runs_dir = Path("data/collected/runs")
target_id = "69ef89c2"

note = None
for f in runs_dir.glob("*.jsonl"):
    try:
        with open(f, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if target_id in obj.get("url", ""):
                        note = obj
                        print(f"Found in: {f.name}")
                        break
                except:
                    continue
        if note:
            break
    except:
        continue

if note:
    print(f"\n笔记内容:")
    print(f"  content: {note.get('content','')}")
    print(f"  title: {note.get('title','')}")
    print(f"  author: {note.get('author','')}")
    print(f"  tags: {note.get('tags','')}")
    print(f"  keyword: {note.get('keyword','')}")
    print(f"  likes/collects/comments: {note.get('likes',0)}/{note.get('collects',0)}/{note.get('comments',0)}")
    print()
    print("关键词检测:")
    content = note.get("content","")
    print(f"  含'汕尾': {'汕尾' in content}")
    print(f"  含'求': {'求' in content}")
    print(f"  含'推荐': {'推荐' in content}")
    print(f"  含'酒店': {'酒店' in content}")
    print(f"  含'民宿': {'民宿' in content}")
    print(f"  含'新疆': {'新疆' in content}")
    print(f"  content长度: {len(content)}")
else:
    print("未找到该笔记")
