"""检查69ef3f8f为什么还通过type_match"""
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
print('has ask:', has_signal(content_no_tags, ASK_SIGNALS))
print('has trip_question:', has_signal(content_no_tags, TRIP_QUESTION_SIGNALS))
print('has urgent:', has_signal(content_no_tags, URGENT_SIGNALS))
print('weak_desire:', any(p in content_no_tags for p in ['想去', '好想去', '打算']))

if any(p in content_no_tags for p in ['想去', '好想去', '打算']):
    consult = any(kw in content_no_tags for kw in ['求推荐', '求带', '有没有人', '求问'])
    print('consult:', consult)

print('_has_unnegated_intent:', svc._has_unnegated_intent(content_no_tags))
print('len:', len(content_no_tags))
print()
print('=== _get_pass_reasons result ===')
result = svc._get_pass_reasons(title, content, note_types)
print('reasons:', result)
