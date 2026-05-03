"""测试9条问题笔记的filter行为"""
import sys
sys.path.insert(0, r'E:\translate\claw\xhs-auto-traffic-v2')
from filter.filter_service import FilterService

svc = FilterService()
notes_to_test = [
    ('test9876543210', '测试标题2', '这是一条测试记录', '测试作者', False),
    ('test5555555555', '测试字段修复', '验证时间字段是否正确', '测试作者', False),
    ('69ef3f8f', '五一反向旅行！广东3天2晚小众海边亲子游',
     '如果你想51带娃去海边，又不想人挤人，那我推荐广东汕尾这个小众城市！不用做攻略，直接🐎住着这里！\n🚗DAY1金町湾沙滩',
     '步仔不fancy', False),
    ('69ee1e4d', '今日份汕尾·西沙滩日落🌇',
     '西沙滩的日落。今日份没在正前方，原来日落方向随着季节变化...by the way 🚗就停路边很方便。',
     'Chimei', False),
    ('69ee2bd1', '今天，看海🌊',
     '这种海浪拍打礁石的画面你们见过吗\n在汕尾红海湾可以见到☺️☺️',
     '大厂离职后回家开饭店', False),
    ('69edd4ab', '为了这口 我可以三刷广东汕尾🦪🦀🦑🍣🦐🦞',
     '生腌脑袋直接狂喜！新鲜度完全在线...已经在想什么时候再来汕尾吃了！',
     '桃子🍑', False),
    ('69f5c8d9', '五一漳浦小狗游记1',
     '整体路线：五一从深圳自驾到漳浦...',
     '奶白白白', False),
    ('69f1d781', '性价比不高但是胜在民宿好的台山大海',
     '趁着广交会之前赶紧带娃去溜达溜达...',
     'mumu麻咪', False),
    ('69ece2e4', '带一岁宝宝—五一错峰汕尾两日游Day1',
     '交通:🚄深圳坪山—汕尾站50¥...行程安排都比较宽松...',
     'Min 🎏', False),
]

results = []
for nid, title, content, author, expected in notes_to_test:
    class MockDetail:
        pass
    detail = MockDetail()
    detail.note_id = nid
    detail.title = title
    detail.content = content
    detail.author = author
    detail.published_at = '2026-05-01'
    detail.url = ''
    detail.xsec_token = ''
    detail.keyword = ''

    r = svc.filter_one(detail)
    merchant = svc._is_merchant_author(author)
    share_reject = svc._is_share_post_only(title, content)

    status = 'OK' if r.passed == expected else 'FAIL'
    results.append({
        'note_id': nid,
        'passed': r.passed,
        'expected': expected,
        'status': status,
        'reasons': r.reasons,
        'merchant': merchant,
        'share_reject': share_reject,
        'title': title[:40],
    })
    print(f'{status}: {nid} | passed={r.passed} expected={expected} | reasons={r.reasons[:40] if r.reasons else "(empty)"} | merchant={merchant} | share_reject={share_reject}')

print()
ok = sum(1 for x in results if x['status'] == 'OK')
print(f'Summary: {ok}/{len(results)} OK')
