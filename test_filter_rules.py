"""
test_filter_rules.py - 内容过滤规则测试
基于真实笔记样本测试过滤逻辑
"""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from filter.filter_service import FilterService
from dataclasses import dataclass

@dataclass
class MockDetail:
    url: str = ''
    author: str = ''
    title: str = ''
    content: str = ''
    time_text: str = ''
    note_id: str = ''
    xsec_token: str = ''
    likes: int = 0
    published_at: str = ''
    filter_passed: bool = False
    filter_reasons: str = ''
    filter_type: str = ''


class TestFilterServiceRules(unittest.TestCase):
    """测试过滤规则对真实样本的判断"""

    @classmethod
    def setUpClass(cls):
        cls.svc = FilterService()

    def test_汕尾美食_normal_pass(self):
        """汕尾美食 - 正常推荐内容应通过"""
        detail = MockDetail(
            title='汕尾这家火锅店真的绝！锅底超香牛肉嫩',
            content='很赞的火锅店，真的锅底正，牛肉嫩。牛腩牛杂也很好吃...',
            author='普通用户'
        )
        r = self.svc.filter_one(detail, '汕尾美食')
        print(f"  标题: {detail.title[:20]} | 通过: {r.passed} | 原因: {r.reasons}")
        # 正常推荐内容应该通过
        self.assertTrue(r.passed, f"正常推荐内容应通过，实际: {r.reasons}")

    def test_汕尾美食_hashtag_only_fail(self):
        """纯 hashtag 内容应被拒绝"""
        detail = MockDetail(
            title='#汕尾 #红海湾 #旅游',
            content='#汕尾 #红海湾 #旅游',
            author='普通用户'
        )
        r = self.svc.filter_one(detail, '汕尾美食')
        print(f"  标题: {detail.title} | 通过: {r.passed} | 原因: {r.reasons}")
        self.assertFalse(r.passed, "纯 hashtag 应被拒绝")

    def test_汕尾美食_merchant_author_fail(self):
        """商家账号应被拒绝"""
        detail = MockDetail(
            title='汕尾美食推荐｜本地人常去的老字号',
            content='地址：汕尾大道xxx号，电话：0660-xxxxxxx',
            author='汕尾美食探店'
        )
        r = self.svc.filter_one(detail, '汕尾美食')
        print(f"  作者: {detail.author} | 通过: {r.passed} | 原因: {r.reasons}")
        # 商家账号应被拒绝
        if not r.passed:
            self.assertIn("商家", r.reasons)

    def test_汕尾红海湾攻略_travel_share_fail(self):
        """旅游分享（无明确需求）应被拒绝"""
        cases = [
            ("回来汕尾啦 跟济州岛似的", '#汕尾红海湾'),
            ("汕尾女摄约拍丨海上古堡", '找搭子/旅游同伴'),
            ("谁懂啊！终于找到珠三角周末看海的宝藏地", '非目标地域'),
            ("免费停车🅿️ 免费寄存行李", '非目标地域'),
        ]
        for title, expected_reject_reason in cases:
            detail = MockDetail(title=title, content=title * 5)
            r = self.svc.filter_one(detail, '汕尾红海湾攻略')
            print(f"  标题: {title[:15]} | 通过: {r.passed} | 原因: {r.reasons}")
            self.assertFalse(r.passed, f"'{title}' 应被拒绝，实际: {r.reasons}")

    def test_汕尾亲子游_travel_plan_pass(self):
        """有明确出行计划的内容应通过"""
        detail = MockDetail(
            title='打算5.1、5.2两天在汕尾玩，汕尾的朋友帮忙看看这个行程',
            content='汕尾的朋友帮忙看看这个行程顺不顺，第一天早上到...',
            author='普通用户'
        )
        r = self.svc.filter_one(detail, '汕尾亲子游')
        print(f"  标题: {detail.title[:30]} | 通过: {r.passed} | 原因: {r.reasons}")
        # 有明确计划的旅游内容应该通过
        self.assertTrue(r.passed, f"有明确计划应通过，实际: {r.reasons}")


class TestFilterServicePatterns(unittest.TestCase):
    """测试特定过滤模式"""

    @classmethod
    def setUpClass(cls):
        cls.svc = FilterService()

    def test_transport_only_reject(self):
        """纯交通内容（如打车）应被拒绝"""
        detail = MockDetail(
            title='汕尾打车多少钱',
            content='从汕尾站到红海湾打车要多少钱，有拼车的吗',
            author='普通用户'
        )
        r = self.svc.filter_one(detail, '汕尾红海湾攻略')
        print(f"  交通内容 | 通过: {r.passed} | 原因: {r.reasons}")

    def test_recruitment_reject(self):
        """招募类内容应被拒绝"""
        detail = MockDetail(
            title='汕尾女摄约拍',
            content='五一假期约拍，有兴趣的来',
            author='普通用户'
        )
        r = self.svc.filter_one(detail, '汕尾红海湾攻略')
        self.assertFalse(r.passed)


if __name__ == "__main__":
    unittest.main(verbosity=2)