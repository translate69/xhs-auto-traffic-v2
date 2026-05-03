"""Deep debug: why has_signal finds 求 in 69ef3f8f content"""
import sys, re
sys.path.insert(0, r'E:\translate\claw\xhs-auto-traffic-v2')
from filter.filter_service import has_signal, ASK_SIGNALS

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
text_lower = content_no_tags.lower()

# Find all occurrences of '求'
print("All '求' occurrences in content_no_tags:")
import re
for m in re.finditer('求', text_lower):
    idx = m.start()
    ctx_start = max(0, idx - 5)
    ctx_end = min(len(text_lower), idx + 8)
    print(f"  pos {idx}: ...{repr(text_lower[ctx_start:ctx_end])}...")

print()
# Test has_signal for each ASK_SIGNAL keyword
print("Testing has_signal for key ASK_SIGNALs:")
for kw in ['求', '求推荐', '想去', '好想去', '打算']:
    if kw in text_lower:
        idx = text_lower.find(kw)
        print(f"  '{kw}' found at {idx}")
        # Check negation context
        if idx >= 2:
            pre = text_lower[idx-2:idx]
            print(f"    pre-chars: {repr(pre)}")
        # Check the char after
        if idx + len(kw) < len(text_lower):
            after = text_lower[idx+len(kw)]
            print(f"    after-char: {repr(after)}")

print()
# Check what the test script shows
result = has_signal(content_no_tags, ['求'])
print(f"has_signal(content_no_tags, ['求']) = {result}")

# Now check has any ask
result_all = has_signal(content_no_tags, ASK_SIGNALS)
print(f"has_signal(content_no_tags, ASK_SIGNALS) = {result_all}")
print("ASK_SIGNALS that match:", [kw for kw in ASK_SIGNALS if has_signal(content_no_tags, [kw])])