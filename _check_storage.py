import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from utils.storage import CollectedStorage
from datetime import datetime
from utils.parse import parse_published_at

storage = CollectedStorage()
print(f"Storage type: {type(storage)}")
print(f"Storage dir: {[x for x in dir(storage) if not x.startswith('__')]}")

# 检查 recent 文件
import os
recent = "data/collected/recent.jsonl"
if os.path.exists(recent):
    lines = open(recent, encoding="utf-8", errors="replace").readlines()
    print(f"recent.jsonl: {len(lines)} lines")
else:
    print(f"{recent} not found")

# 测试时间解析
now = datetime.now()
for t in ["4天前", "1天前", "04-12", "昨天 18:18"]:
    dt = parse_published_at(t)
    if dt:
        print(f"parse('{t}') = {dt}, age={(now-dt).days}")
    else:
        print(f"parse('{t}') = None")