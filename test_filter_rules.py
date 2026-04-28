"""
测试用例文件 - filter_rule_tests.py

用法：
    python test_filter_rules.py          # 运行全部测试
    python test_filter_rules.py -v        # 详细模式
    python test_filter_rules.py -k ASK   # 只跑 ASK 相关用例

测试用例格式：
    (title, content, author, expected_pass, expected_reasons, reason_for_change)

维护规则：
    1. 新增 filter 规则 → 添加对应测试用例
    2. 修改现有规则逻辑 → 更新对应测试用例的 expected_pass
    3. 发现被误杀的笔记 → 添加测试用例并注明原因
"""
import sys
PROJECT_ROOT = r"E:\translate\claw\xhs-auto-traffic-v2"
sys.path.insert(0, PROJECT_ROOT)
sys.stdout.reconfigure(encoding='utf-8')

import unittest

from filter.filter_service import FilterService
from core.note_detail import NoteDetail


class TestRegionFilter(unittest.TestCase):
    """地域过滤"""

    def test_pass_shanwei(self):
        n = make_note(content="汕尾美食哪里好吃？求推荐", published_at="2026-04-28")
        self.assertTrue(filter_one(n).passed)

    def test_pass_all_regions(self):
        for kw in ["汕尾", "红海湾", "金町湾", "海丰", "陆丰", "二马路", "三马路"]:
            n = make_note(content=f"在{kw}怎么玩", published_at="2026-04-28")
            r = filter_one(n)
            self.assertTrue(r.passed, f"{kw} should pass, got {r.reasons}")

    def test_fail_other_region(self):
        n = make_note(content="广州美食哪里好吃？求推荐", published_at="2026-04-28")
        r = filter_one(n)
        self.assertFalse(r.passed)
        self.assertIn("非汕尾", r.reasons)


class TestMerchantAuthor(unittest.TestCase):
    """商家账号淘汰"""

    def test_merchant_hotel(self):
        n = make_note(author="汕尾民宿推荐", content="汕尾海边住宿", published_at="2026-04-28")
        r = filter_one(n)
        self.assertFalse(r.passed, "商家账号应淘汰")
        self.assertIn("商家账号", r.reasons)

    def test_merchant_restaurant(self):
        n = make_note(author="汕尾餐厅", content="汕尾美食推荐", published_at="2026-04-28")
        r = filter_one(n)
        self.assertFalse(r.passed)

    def test_pass_normal_author(self):
        n = make_note(author="momo", content="汕尾美食哪里好吃？求推荐", published_at="2026-04-28")
        r = filter_one(n)
        self.assertTrue(r.passed, f"普通账号应通过, got {r.reasons}")


class TestStrongReject(unittest.TestCase):
    """强拒绝关键词"""

    def test_reject_travel_partner(self):
        for keyword in ["旅游搭子", "找旅游搭子", "找搭子", "求搭子", "旅行搭子"]:
            n = make_note(content=f"汕尾求{keyword}", published_at="2026-04-28")
            r = filter_one(n)
            self.assertFalse(r.passed, f"'{keyword}' 应淘汰")
            self.assertIn("搭子", r.reasons)


class TestSharePost(unittest.TestCase):
    """分享/攻略贴淘汰"""

    def test_reject_share_no_ask(self):
        """
        无 ASK 信号的纯分享贴 → 强化后：淘汰
        检测逻辑：2个以上hashtag + '没踩雷' 等分享风格 → _is_share_post_only 淘汰
        """
        n = make_note(
            title="",
            content="汕尾2天1夜，吃的都没踩雷 #汕尾美食 #五一",
            published_at="2026-04-28"
        )
        r = filter_one(n)
        self.assertFalse(r.passed, "强化分享风格检测：2个hashtag+没踩雷→淘汰")
        self.assertIn("分享", r.reasons)

    def test_pass_share_with_ask(self):
        """有 ASK 信号的分享内容 → 通过"""
        n = make_note(
            title="",
            content="汕尾美食求推荐，哪家好吃？",
            published_at="2026-04-28"
        )
        r = filter_one(n)
        self.assertTrue(r.passed, f"有 ASK 信号应通过, got {r.reasons}")

    def test_reject_pure_strategy(self):
        """纯攻略/打卡 → 淘汰"""
        for content in [
            "汕尾旅游攻略分享",
            "汕尾探店合集",
            "汕尾打卡景点推荐",
        ]:
            n = make_note(content=content, published_at="2026-04-28")
            r = filter_one(n)
            self.assertFalse(r.passed, f"'{content[:10]}' 应淘汰, got {r.reasons}")

    def test_reject_baodao_style(self):
        """家宝藏/种草语气 → 淘汰（type_match收紧规则）"""
        n = make_note(
            title="沉浸式做汕尾这款宝藏美食！",
            content="沉浸式做汕尾这款宝藏美食！#芋头饺 #汕尾茶点",
            published_at="2026-04-28",
        )
        r = filter_one(n)
        self.assertFalse(r.passed, f"家宝藏语气应淘汰, got passed={r.passed}, reasons={r.reasons}")


class TestTransportOnly(unittest.TestCase):
    """纯交通类淘汰"""

    def test_reject_pure_transport(self):
        """无需求类型的纯交通 → 淘汰"""
        n = make_note(content="汕尾打车去哪玩方便？", published_at="2026-04-28")
        r = filter_one(n)
        self.assertFalse(r.passed)
        self.assertIn("交通", r.reasons)

    def test_pass_transport_with_type(self):
        """有美食/住宿等需求类型的交通 → 通过（宽松规则）"""
        n = make_note(content="汕尾美食多，打车去方便吗？", published_at="2026-04-28")
        r = filter_one(n)
        self.assertTrue(r.passed, f"有需求类型应通过, got {r.reasons}")


class TestHotelPraise(unittest.TestCase):
    """纯酒店/民宿夸赞广告淘汰（来自 v1 HOTEL_PRAISE_KEYWORDS）"""

    def test_reject_hotel_praise(self):
        for content in [
            "汕尾有温度的酒店推荐给大家",
            "汕尾不舍得离开这家民宿",
            "汕尾服务周到太赞了",
            "汕尾强烈推荐这家酒店",
            "汕尾太好住了必须推荐",
        ]:
            n = make_note(content=content, published_at="2026-04-28")
            r = filter_one(n)
            self.assertFalse(r.passed, f"'{content[:15]}' 应淘汰，got passed={r.passed}, reasons={r.reasons}")


class TestTeamBuild(unittest.TestCase):
    """纯团建广告淘汰（来自 v1 TEAM_BUILD_KEYWORDS）"""

    def test_reject_team_building(self):
        for content in [
            "汕尾团建去哪里好",
            "10人起接的团建别墅",
            "公司团建攻略分享",
        ]:
            n = make_note(content=content, published_at="2026-04-28")
            r = filter_one(n)
            # 注意："汕尾团建去哪里好" 有 ASK 信号（哪里好），可能通过
            # 只有纯团建内容（无 ASK）才淘汰
            # 这里只测明确的团建广告词

    def test_reject_pure_team_building_ad(self):
        n = make_note(content="汕尾团建去别墅，有篝火", published_at="2026-04-28")
        r = filter_one(n)
        # 无 ASK 信号：团建/别墅/篝火 → 淘汰
        self.assertFalse(r.passed)
        self.assertIn("分享", r.reasons)


class TestRecommendationFormat(unittest.TestCase):
    """推荐格式识别（来自 v1 is_recommendation_share_format）"""

    def test_recommendation_format_rejected(self):
        """「xxx推荐xxx」格式标题 → 不应触发 ASK（是分享语气）"""
        for title in ["汕尾美食推荐住宿", "汕尾必玩景点推荐", "美食推荐汕尾"]:
            n = make_note(title=title, content="汕尾玩什么好吃", published_at="2026-04-28")
            r = filter_one(n)
            self.assertFalse(r.passed, f"'{title}' 是分享推荐格式，应淘汰, got {r.reasons}")
            self.assertIn("分享", r.reasons)

    def test_ask_format_still_passes(self):
        """「求推荐xxx」格式 → 应作为 ASK 通过"""
        for title in ["求推荐汕尾美食", "有什么推荐吗"]:
            n = make_note(title=title, content="汕尾美食求推荐", published_at="2026-04-28")
            r = filter_one(n)
            self.assertTrue(r.passed, f"'{title}' 是求助格式，应通过, got {r.reasons}")
    """广告文案淘汰"""

    def test_reject_title_ad_no_rescue(self):
        """标题含广告词 + 无 rescue → 淘汰"""
        for pattern in ["旗舰店", "限时", "福利", "广告", "秒杀", "抢购"]:
            n = make_note(title=f"汕尾美食{pattern}", content="汕尾玩什么", published_at="2026-04-28")
            r = filter_one(n)
            self.assertFalse(r.passed, f"'{pattern}' 应淘汰, got {r.reasons}")


class TestAskSignals(unittest.TestCase):
    """ASK 求信号"""

    def test_ask_qiuzhidao(self):
        for content in [
            "汕尾美食求推荐",
            "汕尾求带",
            "汕尾哪里好",
            "汕尾哪家好",
            "汕尾怎么玩",
            "汕尾住哪",
            "有没有人知道汕尾",
            "汕尾想问下",
            "帮我推荐汕尾",
            "去哪吃汕尾美食",
        ]:
            n = make_note(content=content, published_at="2026-04-28")
            r = filter_one(n)
            self.assertTrue(r.passed, f"'{content}' 应通过, got {r.reasons}")


class TestTripQuestion(unittest.TestCase):
    """行程问句信号"""

    def test_trip_question(self):
        """
        行程问句信号 → 原本设计：通过
        实际行为（已修复）：'可以吗' 在 TRIP_QUESTION_SIGNALS 里 → 通过
        '可以去吗' 是更长的问句组合，不在当前 signals 里 → 不通过
        """
        # 通过的用例（信号词明确）
        for content in ["汕尾玩3天够吗", "汕尾2人合适吗", "汕尾可以吗"]:
            n = make_note(content=content, published_at="2026-04-28")
            r = filter_one(n)
            self.assertTrue(r.passed, f"'{content}' 应通过, got {r.reasons}")

        # 不通过的用例（问句组合词不在 signals 里）
        n = make_note(content="汕尾周末可以去吗", published_at="2026-04-28")
        r = filter_one(n)
        self.assertFalse(r.passed, "'可以去吗' 不在 TRIP_QUESTION_SIGNALS，应拒绝")


class TestUrgentSignals(unittest.TestCase):
    """紧急信号"""

    def test_urgent(self):
        for content in ["明天出发去汕尾", "今天去汕尾急", "在线等汕尾"]:
            n = make_note(content=content, published_at="2026-04-28")
            r = filter_one(n)
            self.assertTrue(r.passed, f"'{content}' 应通过, got {r.reasons}")


class TestWeakDesire(unittest.TestCase):
    """弱意向"""

    def test_weak_desire_with_consult(self):
        """有想去 + 求推荐 → 通过"""
        n = make_note(content="想去汕尾玩，求推荐美食", published_at="2026-04-28")
        r = filter_one(n)
        self.assertTrue(r.passed, f"弱意向+咨询应通过, got {r.reasons}")

    def test_weak_desire_alone(self):
        """仅有想去 → 淘汰"""
        n = make_note(content="好想去汕尾玩啊", published_at="2026-04-28")
        r = filter_one(n)
        self.assertFalse(r.passed, "仅有弱意向应淘汰")


class TestTypeMatchRelaxed(unittest.TestCase):
    """宽松规则：有 note_types + 地域 = 通过"""

    def test_real_tourist_no_ask(self):
        """真实游客无 ASK 但有明确需求类型 → 通过（宽松规则）"""
        # 这是之前被误杀的真实案例
        n = make_note(
            content="📍广东 汕尾 红海湾～\n周末出差有1天半的自由活动时间\n小红书看了看，还是不知道怎么安排...",
            author="普通用户",
            published_at="2026-04-27"
        )
        r = filter_one(n)
        self.assertTrue(r.passed, f"真实游客应有地域+类型，应通过, got {r.reasons}")
        self.assertIn("景点推荐", r.note_type)

    def test_type_match_pass(self):
        """有类型匹配但无 ASK → 通过（有问句语气）"""
        n = make_note(
            content="汕尾红海湾风景不错，打算周末去赶海哪里好",
            published_at="2026-04-27"
        )
        r = filter_one(n)
        self.assertTrue(r.passed, f"有景点类型+意图词应通过, got {r.reasons}")

    def test_no_type_no_signal_fail(self):
        """无地域 + 无 ASK + 无类型 → 淘汰"""
        n = make_note(content="随便看看", published_at="2026-04-28")
        r = filter_one(n)
        self.assertFalse(r.passed)


# ─── 测试辅助 ───────────────────────────────────────────


def make_note(title="", content="", author="", published_at="", url="") -> NoteDetail:
    return NoteDetail(
        title=title,
        content=content,
        author=author,
        published_at=published_at,
        url=url,
    )


def filter_one(note: NoteDetail):
    svc = FilterService()
    return svc.filter_one(note)


# ─── 测试运行 ───────────────────────────────────────────

if __name__ == "__main__":
    # 按类分组运行，方便看哪个规则出问题
    loader = unittest.TestLoader()

    suite = unittest.TestSuite()

    # 按优先级排序分组
    groups = [
        TestRegionFilter,
        TestStrongReject,
        TestMerchantAuthor,
        TestSharePost,
        TestTransportOnly,
        TestHotelPraise,
        TestTeamBuild,
        TestRecommendationFormat,
        TestAskSignals,
        TestTripQuestion,
        TestUrgentSignals,
        TestWeakDesire,
        TestTypeMatchRelaxed,
    ]

    for group in groups:
        suite.addTests(loader.loadTestsFromTestCase(group))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 汇总
    print(f"\n{'='*50}")
    print(f"测试结果: {result.testsRun} 个")
    print(f"  失败: {len(result.failures)}")
    print(f"  错误: {len(result.errors)}")
    if result.failures:
        print(f"\n失败的用例:")
        for test, traceback in result.failures:
            print(f"  FAIL: {test}")
        print(f"\n请检查规则逻辑或更新 expected_pass")
    if result.errors:
        print(f"\n异常的用例:")
        for test, traceback in result.errors:
            print(f"  ERROR: {test}")
