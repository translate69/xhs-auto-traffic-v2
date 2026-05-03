import json, pathlib, sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from core.note_detail import NoteDetail
from filter.filter_service import FilterService

filter_svc = FilterService()

# 跑 longtail 关键词
kw = "深圳大鹏两天一夜团建方案"
f_path = pathlib.Path(r'E:\translate\claw\xhs-auto-traffic-v2\data\collected\runs\2026-04-29_深圳大鹏两天一夜团建方案.jsonl')

if not f_path.exists():
    print(f"文件不存在: {f_path.name}")
else:
    lines = f_path.read_text(encoding='utf-8', errors='replace').strip().split('\n')
    print(f"总 {len(lines)} 条笔记")

    passed_list = []
    for i, line in enumerate(lines):
        d = json.loads(line)
        title = (d.get('title') or '')[:40] or (d.get('content', '')[:40])
        print(f"\n[{i}] {title}")

        # Reconstruct NoteDetail
        valid_fields = {f.name for f in NoteDetail.__dataclass_fields__.values()}
        filtered = {k: v for k, v in d.items() if k in valid_fields}
        try:
            nd = NoteDetail(**filtered)
        except Exception as e:
            print(f"  建模范错误: {e}")
            continue
        nd.keyword = kw

        result = filter_svc.filter_one(nd, keyword=kw)
        print(f"  → passed={result.passed} type={result.note_type} reasons={result.reasons}")
        if result.passed:
            passed_list.append((title, result))

    print(f"\n通过: {len(passed_list)}/{len(lines)}")