"""输出9条笔记的诊断信息到文件"""
import json
with open(r'E:\translate\claw\xhs-auto-traffic-v2\_probe_9_notes.json', encoding='utf-8') as f:
    data = json.load(f)

lines = []
for item in data:
    lines.append(f"=== {item['note_id']} ===")
    lines.append(f"RECORD_ID: {item['record_id']}")
    lines.append(f"reasons: {repr(item['reasons'])}")
    lines.append(f"author: {repr(item['author'])}")
    lines.append(f"title: {item['title']}")
    lines.append(f"content: {item['content'][:300] if item['content'] else '(empty)'}")
    lines.append("")

with open(r'E:\translate\claw\xhs-auto-traffic-v2\_probe_9_notes.txt', 'w', encoding='utf-8') as f:
    f.write("\n".join(lines))
