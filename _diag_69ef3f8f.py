"""精准诊断 69ef3f8f 为什么 has_signal 返回 True"""
import sys, re
sys.path.insert(0, r'E:\translate\claw\xhs-auto-traffic-v2')
from filter.filter_service import has_signal, ASK_SIGNALS

# The full content of 69ef3f8f
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
combined = title + ' ' + content_no_tags

print('=== Checking which ASK_SIGNALS match ===')
for kw in ASK_SIGNALS:
    idx = combined.lower().find(kw.lower())
    if idx != -1:
        # Get surrounding context
        start = max(0, idx - 5)
        end = min(len(combined), idx + len(kw) + 5)
        ctx = combined[start:end]
        print(f'  FOUND "{kw}" at pos {idx}: "...{ctx}..."')

print()
print('=== Checking "求" specifically ===')
print('  "求" in combined:', '求' in combined)
print('  "求" in title:', '求' in title)
print('  "求" in content_no_tags:', '求' in content_no_tags)
print()
print('=== has_signal result ===')
print('  has_signal(content_no_tags, ASK_SIGNALS):', has_signal(content_no_tags, ASK_SIGNALS))
print('  has_signal(combined, ASK_SIGNALS):', has_signal(combined, ASK_SIGNALS))
