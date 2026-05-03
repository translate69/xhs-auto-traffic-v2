"""检查2条误通过笔记的filter行为"""
import sys, re
sys.path.insert(0, r'E:\translate\claw\xhs-auto-traffic-v2')
from filter.filter_service import FilterService, ASK_SIGNALS, SHARE_POST_KEYWORDS, HOTEL_PRAISE_KEYWORDS

svc = FilterService()

cases = [
    ('69ef3f8f', '五一反向旅行！广东3天2晚小众海边亲子游',
     '如果你想51带娃去海边，又不想人挤人，那我推荐广东汕尾这个小众城市！不用做攻略，直接🐎住着这里！\n🚗DAY1金町湾沙滩🏖️➡️Day2沙舍尾➕凤山旅游度假区➡️Day3红海湾一日游🏖️\n\n之前出去旅行每次都要手动搜索🔍景点之间的位置，用了百度地图的小度想想行程助手，输入想去的目的地和要求，它一键出路线攻略，对宝妈来说真的太节省时间了！\n✅添加专属喜好、一键规划路线\n✅随时mark修改行程\n✅贴心提醒：海边防晒&退潮时间\n\nDay1️⃣金町湾沙滩\n海上香格里拉：拥有7公里长的原生沙滩，沙子很细！\n✔️风帆礼堂：白色建筑+椰林，双层轨道巴士🚌\n✔️鲸湾小镇：坐海上小火车（🎫抖🎵便宜）\n✔️',
     '步仔不fancy'),
    ('69ee2bd1', '今天，看海🌊',
     '这种海浪拍打礁石的画面你们见过吗\n在汕尾红海湾可以见到☺️☺️\n#我们看海去 #汕尾#汕尾红海湾',
     '大厂离职后回家开饭店'),
]

for nid, title, content, author in cases:
    print(f'=== {nid} ===')
    print(f'is_recommendation_format: {svc._is_recommendation_format(title)}')
    print(f'is_share_post_only: {svc._is_share_post_only(title, content)}')
    content_no_tags = re.sub(r'#.+?(?=\s|#|$)', '', content)
    combined = title + ' ' + content_no_tags
    print(f'content hashtag count: {content.count("#")}')

    ask_signals_found = [kw for kw in ASK_SIGNALS if kw in combined]
    share_signals_found = [kw for kw in SHARE_POST_KEYWORDS if kw in combined]
    hotel_signals_found = [kw for kw in HOTEL_PRAISE_KEYWORDS if kw in combined]

    print(f'ASK signals found: {ask_signals_found}')
    print(f'SHARE signals found: {share_signals_found}')
    print(f'HOTEL_PRAISE signals found: {hotel_signals_found}')

    from filter.filter_service import has_signal
    title_has_ask = has_signal(title, ASK_SIGNALS)
    content_has_ask = has_signal(content_no_tags, ASK_SIGNALS)
    print(f'has_signal(title, ASK_SIGNALS): {title_has_ask}')
    print(f'has_signal(content_no_tags, ASK_SIGNALS): {content_has_ask}')

    r = svc.filter_one.__func__(svc, type('obj', (object,), {
        'title': title, 'content': content, 'author': author,
        'published_at': '2026-05-01', 'url': '', 'xsec_token': '', 'keyword': ''
    })())
    print(f'filter_one result: passed={r.passed} reasons={r.reasons}')
    print()
