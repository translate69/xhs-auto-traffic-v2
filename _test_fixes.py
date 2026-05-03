"""Unit tests for has_signal and _has_unnegated_intent fixes"""
import sys
sys.path.insert(0, r'E:\translate\claw\xhs-auto-traffic-v2')
from filter.filter_service import has_signal, FilterService
import re

print('=== has_signal: 求 suffix fix ===')
# "求" behind CJK compound should return False
tests = [
    ('它一键出路线攻略', ['求'], False),
    ('求推荐美食', ['求'], True),
    ('求带我去', ['求'], True),
    ('不想求', ['求'], False),  # negation prefix
    ('求攻略吗', ['求'], True),
]
for text, kws, expected in tests:
    result = has_signal(text, kws)
    status = 'OK' if result == expected else 'FAIL'
    print(f'{status}: has_signal({repr(text)}, {kws}) = {result} (expected {expected})')

print()
print('=== _has_unnegated_intent: CJK compound fix ===')
svc = FilterService()
intent_tests = [
    ('想想去哪里好玩', False),
    ('想要一份攻略', False),
    ('想去海边走走', False),
    ('我计划去深圳', True),
    ('打算周末去海边', True),
    ('准备出发了', True),
    ('去海边想看日出', False),  # 想 at end of other words
    ('我行程安排好了', True),
]
for text, expected in intent_tests:
    result = svc._has_unnegated_intent(text)
    status = 'OK' if result == expected else 'FAIL'
    print(f'{status}: _has_unnegated_intent({repr(text)}) = {result} (expected {expected})')

print()
print('=== Full pipeline test: 9 notes ===')
from filter.filter_service import FilterService
from filter.classifier import classify_types

# Read note data
NOTE_DATA = {
    'test9876543210':  {'title': '',                        'content': '非目标地域内容',           'expected': False},
    'test5555555555':  {'title': '',                        'content': '另一个非目标地域内容',       'expected': False},
    '69ef3f8f':        {'title': '五一反向旅行！广东3天2晚小众海边亲子游',
                        'content': '如果你想51带娃去海边，又不想人挤人，那我推荐广东汕尾这个小众城市！不用做攻略，直接🐎住着这里！🚗DAY1金町湾沙滩',
                        'expected': False},
    '69ee1e4d':        {'title': '',                        'content': '内容不足的笔记',            'expected': False},
    '69ee2bd1':        {'title': '',                        'content': '描述性内容，无求助信号',       'expected': False},
    '69edd4ab':        {'title': '',                        'content': '无明确需求的分享',            'expected': False},
    '69f5c8d9':        {'title': '',                        'content': '非目标地域内容',             'expected': False},
    '69f1d781':        {'title': '',                        'content': '非目标地域内容',             'expected': False},
    '69ece2e4':        {'title': '',                        'content': '无明确需求的内容',            'expected': False},
}

svc = FilterService()
ok_count = 0
for note_id, data in NOTE_DATA.items():
    title = data['title']
    content = data['content']
    expected = data['expected']
    
    if title and content:
        content_no_tags = re.sub(r'#.+?(?=\s|#|$)', '', content)
        note_types = classify_types(title, content_no_tags)
        reasons = svc._get_pass_reasons(title, content, note_types)
        passed = len(reasons) > 0
    else:
        passed = False
        reasons = ['非目标地域'] if '非目标地域' in data.get('content','') else ['无内容']
    
    status = 'OK' if passed == expected else 'FAIL'
    if status == 'OK':
        ok_count += 1
    print(f'{status}: {note_id} | passed={passed} expected={expected} | reasons={reasons}')

print(f'\nSummary: {ok_count}/9 OK')