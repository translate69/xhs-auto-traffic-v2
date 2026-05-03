"""Debug why 69ef3f8f still passes - trace every step"""
import sys, re
sys.path.insert(0, r'E:\translate\claw\xhs-auto-traffic-v2')
# Force reload
import importlib
import filter.filter_service as fs
importlib.reload(fs)

from filter.filter_service import has_signal, ASK_SIGNALS, TRIP_QUESTION_SIGNALS, URGENT_SIGNALS, FilterService
from filter.classifier import classify_types

content = (
    '如果你想51带娃去海边，又不想人挤人，那我推荐广东汕尾这个小众城市！不用做攻略，直接🐎住着这里！\n'
    '🚗DAY1金町湾沙滩🏖️➡️Day2沙舍尾➕凤山旅游度假区➡️Day3红海湾一日游🏖️\n\n'
    '之前出去旅行每次都要手动搜索🔍景点之间的位置，用了百度地图的小度想想行程助手，输入想去的目的地和要求，它一键出路线攻略，对宝妈来说真的太节省时间了！\n'
    '✅添加专属喜好、一键规划路线\n'
    '✅随时mark修改行程\n'
    '✅贴心提醒：海边防晒&退潮时间\n\n'
    'Day1️⃣金町湾沙滩\n'
    '海上香格里拉：拥有7公里长的原生沙滩，沙子很细！\n'
    '✔️风帆礼堂：白色建筑+椰林，双层轨道巴士🚌\n'
    '✔️鲸湾小镇：坐海上小火车（🎫抖🎵便宜）\n'
    '✔️'
)
title = '五一反向旅行！广东3天2晚小众海边亲子游'
content_no_tags = re.sub(r'#.+?(?=\s|#|$)', '', content)
CJK = frozenset(range(0x4E00, 0x9FFF + 1)) | frozenset(range(0x3400, 0x4DBF + 1))

svc = FilterService()
note_types = classify_types(title, content_no_tags)

print("Step-by-step for 69ef3f8f:")
print("  note_types:", note_types)
print()

# Check ASK_SIGNALS - each one individually
ask_hits = []
for kw in ASK_SIGNALS:
    kw_lower = kw.lower()
    if kw_lower in content_no_tags.lower():
        # Check CJK prefix for single-char "求"
        idx = content_no_tags.lower().find(kw_lower)
        cjk_pre = False
        if kw == "求" and len(kw) == 1:
            pre_char = content_no_tags[idx - 1] if idx > 0 else ''
            cjk_pre = ord(pre_char) in CJK if pre_char else False
        ask_hits.append((kw, idx, cjk_pre))

print("ASK_SIGNALS hits in content:")
for kw, idx, cjk_pre in ask_hits:
    ctx_start = max(0, idx - 3)
    ctx_end = min(len(content_no_tags), idx + len(kw) + 3)
    print(f"  '{kw}' at {idx}: CJK-preced={cjk_pre}, ctx={repr(content_no_tags[ctx_start:ctx_end])}")

print()
print("has_signal for ['求']:", has_signal(content_no_tags, ['求']))
print("has_signal for ASK_SIGNALS:", has_signal(content_no_tags, ASK_SIGNALS))

# Check the actual _get_pass_reasons
print()
print("_get_pass_reasons:", svc._get_pass_reasons(title, content, note_types))