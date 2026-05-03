"""Test run_batch flow with correct date"""
import sys, re
sys.path.insert(0, r'E:\translate\claw\xhs-auto-traffic-v2')
from filter.filter_service import FilterService
from filter.review_service import ReviewService
from datetime import datetime, timedelta

class MockNote:
    def __init__(self, title, content, author='', days_ago=0):
        self.title = title
        self.content = content
        self.author = author
        self.keyword = ''
        self.filter_passed = False
        self.filter_reasons = ''
        self.filter_result = None
        self.note_id = 'test123'
        self.url = ''
        self.xsec_token = ''
        self.images = []
        # Set published_at to N days ago
        pub_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        self.published_at = pub_date
        self.likes = 100
        self.collects = 10
        self.comments = 5

svc = FilterService()
review_svc = ReviewService()

# Test 1: 69ef3f8f - 纯分享攻略，should NOT pass filter
bad_note = MockNote(
    '五一反向旅行！广东3天2晚小众海边亲子游',
    '如果你想51带娃去海边，又不想人挤人，那我推荐广东汕尾这个小众城市！不用做攻略，直接🐎住着这里！\n🚗DAY1金町湾沙滩',
    days_ago=2
)
r = svc.filter_one(bad_note, keyword='汕尾美食')
bad_note.filter_passed = r.passed
bad_note.filter_reasons = r.reasons
bad_note.filter_result = r
print(f'Bad note Filter: passed={r.passed}, reasons={r.reasons}')
rev_bad = review_svc.review([bad_note], keyword='汕尾美食')
print(f'Bad note Review: {len(rev_bad)} passed ✓' if len(rev_bad) == 0 else f'FAIL: got {len(rev_bad)}')

# Test 2: good real request - should pass both
good_note = MockNote(
    '汕尾3天怎么安排合适',
    '计划去汕尾玩3天2晚，求推荐美食和住宿，有什么必去的景点吗？方便的话可以说下交通',
    days_ago=1
)
r2 = svc.filter_one(good_note, keyword='汕尾美食')
good_note.filter_passed = r2.passed
good_note.filter_reasons = r2.reasons
good_note.filter_result = r2
print(f'Good note Filter: passed={r2.passed}, reasons={r2.reasons}')
rev_good = review_svc.review([good_note], keyword='汕尾美食')
print(f'Good note Review: {len(rev_good)} passed ✓' if len(rev_good) == 1 else f'FAIL: got {len(rev_good)}')

# Test 3: merchant author - passes filter, fails review
merchant_note = MockNote(
    '汕尾民宿推荐',
    '这家民宿超赞，海景房性价比很高，来汕尾玩推荐住这里',
    author='汕尾海景民宿小助手',
    days_ago=2
)
r3 = svc.filter_one(merchant_note, keyword='汕尾美食')
merchant_note.filter_passed = r3.passed
merchant_note.filter_reasons = r3.reasons
merchant_note.filter_result = r3
print(f'Merchant Filter: passed={r3.passed}, reasons={r3.reasons}')
rev_merchant = review_svc.review([merchant_note], keyword='汕尾美食')
print(f'Merchant Review: {len(rev_merchant)} passed ✓' if len(rev_merchant) == 0 else f'FAIL: got {len(rev_merchant)}')

print()
all_ok = len(rev_bad) == 0 and len(rev_good) == 1 and len(rev_merchant) == 0
print('All tests passed ✓' if all_ok else 'Some tests FAILED')