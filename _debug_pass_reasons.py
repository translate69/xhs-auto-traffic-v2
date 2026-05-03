"""Debug _get_pass_reasons for 69ef3f8f step by step"""
import sys, re
sys.path.insert(0, r'E:\translate\claw\xhs-auto-traffic-v2')
import importlib, importlib.util

# Force fresh load
for mod_name in list(sys.modules.keys()):
    if 'filter' in mod_name:
        del sys.modules[mod_name]

from filter.filter_service import has_signal, ASK_SIGNALS, TRIP_QUESTION_SIGNALS, URGENT_SIGNALS, FilterService
from filter.classifier import classify_types

title = '五一反向旅行！广东3天2晚小众海边亲子游'
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
content_no_tags = re.sub(r'#.+?(?=\s|#|$)', '', content)
note_types = classify_types(title, content_no_tags)
svc = FilterService()

print(f"note_types: {note_types}")
print(f"len(content_no_tags): {len(content_no_tags)}")
print()

# Step 1: ask signal
ask = has_signal(content_no_tags, ASK_SIGNALS)
print(f"Step1 ASK: has_signal(ASK_SIGNALS) = {ask}")

# Step 2: trip_question signal
tq = has_signal(content_no_tags, TRIP_QUESTION_SIGNALS)
print(f"Step2 TRIP_QUESTION: has_signal(TRIP_QUESTION_SIGNALS) = {tq}")

# Step 3: urgent signal
urg = has_signal(content_no_tags, URGENT_SIGNALS)
print(f"Step3 URGENT: has_signal(URGENT_SIGNALS) = {urg}")

if ask or tq or urg:
    print("→ Would return early with reasons")
else:
    print("→ Continue to weak_desire check...")
    weak_desire = any(p in content_no_tags for p in ["想去", "好想去", "打算"])
    print(f"  weak_desire = {weak_desire}")
    if weak_desire:
        consult = any(kw in content_no_tags for kw in ["求推荐", "求带", "有没有人", "求问"])
        print(f"  content_has_consult = {consult}")
    print()
    # type_match check
    type_match_kws = ["怎么安排", "来得及吗", "来得及么", "够吗", "合适吗", "可以吗", "方便吗", "行吗", "适合吗"]
    has_tm_kw = any(kw in content_no_tags for kw in type_match_kws)
    has_na = "哪儿" in content_no_tags
    print(f"  type_match_kws: {has_tm_kw} (found: {[kw for kw in type_match_kws if kw in content_no_tags]})")
    print(f"  '哪儿': {has_na}")
    
    unneg_intent = svc._has_unnegated_intent(content_no_tags)
    print(f"  len > 30: {len(content_no_tags) > 30}")
    print(f"  _has_unnegated_intent: {unneg_intent}")
    print()
    if note_types:
        # Check for ad语气
        has_ad = bool(__import__('re').search(r"宝藏|绝了|封神|太好吃|种草", content_no_tags))
        print(f"  note_types truthy: True")
        print(f"  ad语气 (宝藏/绝了/封神/太好吃/种草): {has_ad}")
        print(f"  → Would add type_match via len>30+unnegated_intent path")
        reasons = []
        if not has_ad:
            if has_tm_kw or has_na:
                reasons.append("type_match")
            elif len(content_no_tags) > 30 and unneg_intent:
                reasons.append("type_match")
        print(f"  final reasons: {reasons}")