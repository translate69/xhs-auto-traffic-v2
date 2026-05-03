"""Debug why 69ef3f8f still passes"""
import sys, re
sys.path.insert(0, r'E:\translate\claw\xhs-auto-traffic-v2')
from filter.filter_service import FilterService, has_signal, ASK_SIGNALS, TRIP_QUESTION_SIGNALS, URGENT_SIGNALS
from filter.classifier import classify_types

svc = FilterService()

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

print('note_types:', note_types)
print('content length:', len(content_no_tags))
print()
print('ASK signals found:', [kw for kw in ASK_SIGNALS if kw in content_no_tags.lower()])
print('TRIP_QUESTION found:', [kw for kw in TRIP_QUESTION_SIGNALS if has_signal(content_no_tags, [kw])])
print('URGENT found:', [kw for kw in URGENT_SIGNALS if has_signal(content_no_tags, [kw])])
print()
print('weak_desire (想去/好想去/打算):', any(p in content_no_tags for p in ['想去', '好想去', '打算']))
print('consult (求推荐/求带/有没有人/求问):', any(kw in content_no_tags for kw in ['求推荐', '求带', '有没有人', '求问']))
print()
print('_has_unnegated_intent:', svc._has_unnegated_intent(content_no_tags))
print()
print('=== _get_pass_reasons ===')
result = svc._get_pass_reasons(title, content, note_types)
print('reasons:', result)
print()

# Check the type_match specific keywords
type_match_kws = ["怎么安排", "来得及吗", "来得及么", "够吗", "合适吗", "可以吗", "方便吗", "行吗", "适合吗", "哪儿"]
print('type_match keywords in content:')
for kw in type_match_kws:
    if kw in content_no_tags.lower():
        print(f'  FOUND: {repr(kw)}')