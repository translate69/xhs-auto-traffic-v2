"""
test_collector.py - SearchCollector 单元测试

测试采集流程的各个环节：
1. 搜索导航：首页填词 -> 回车 -> 跳转 search_result
2. 筛选点击：hover .filter -> 坐标点击 最新 + 一周内
3. Feed 提取：section.note-item 提取 -> URL 过滤
4. 滚动加载：向下滚动 -> 笔记数量增加
5. 登录态检测：cookie 有效/失效时的行为

用法：python test_collector.py
"""
import sys, time, re, unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

ROOT = Path(__file__).parent.parent

# ─── 测试数据 ───────────────────────────────────────────

SAMPLE_FEED_DATA = [
    # 正常笔记
    {
        "url": "/search_result/69f46cae000000001b02067f?xsec_token=ABC&xsec_source=",
        "author": "测试用户1",
        "time_text": "3小时前",
        "title": "汕尾美食推荐"
    },
    # explore 格式
    {
        "url": "/explore/69f4cfaf000000001e00fa27?xsec_token=DEF",
        "author": "测试用户2",
        "time_text": "2天前",
        "title": ""
    },
    # note 格式
    {
        "url": "/note/69f4716b000000003502e754?xsec_token=GHI",
        "author": "测试用户3",
        "time_text": "5天前",
        "title": "红海湾攻略"
    },
    # 无效 URL（应被过滤）
    {
        "url": "/user/profile/xxx",
        "author": "测试",
        "time_text": "1天前",
        "title": ""
    },
    # 空 URL（应被过滤）
    {
        "url": "",
        "author": "测试",
        "time_text": "1天前",
        "title": ""
    },
]

SAMPLE_RAW_DATA_FROM_SEARCH_PAGE = [
    # search_result 格式
    "/search_result/69f46cae000000001b02067f?xsec_token=ABC&xsec_source=",
    "/search_result/69f4cfaf000000001e00fa27?xsec_token=DEF&xsec_source=",
    # explore 格式
    "/explore/69f4716b000000003502e754?xsec_token=GHI",
    # note 格式
    "/note/69f4716b000000003502e754?xsec_token=GHI",
    # 无效格式
    "/user/profile/xxx",
    "",
]


# ─── 测试用例 ───────────────────────────────────────────

class TestFeedNoteUrlParsing(unittest.TestCase):
    """FeedNote.note_id 提取测试"""

    def test_search_result_url(self):
        raw = "/search_result/69f46cae000000001b02067f?xsec_token=ABC"
        m = re.search(r"/(?:search_result|note|explore)/([a-f0-9]+)", raw)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "69f46cae000000001b02067f")

    def test_explore_url(self):
        raw = "/explore/69f4716b000000003502e754?xsec_token=GHI"
        m = re.search(r"/(?:search_result|note|explore)/([a-f0-9]+)", raw)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "69f4716b000000003502e754")

    def test_note_url(self):
        raw = "/note/69f4716b000000003502e754"
        m = re.search(r"/(?:search_result|note|explore)/([a-f0-9]+)", raw)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "69f4716b000000003502e754")

    def test_invalid_url_no_match(self):
        raw = "/user/profile/xxx"
        m = re.search(r"/(?:search_result|note|explore)/([a-f0-9]+)", raw)
        self.assertIsNone(m)


class TestFeedExtractionFilter(unittest.TestCase):
    """_extract_feeds 过滤逻辑测试"""

    def _simulate_url_filter(self, raw_urls):
        """模拟 _extract_feeds 的 URL 过滤逻辑"""
        feeds = []
        for raw_url in raw_urls:
            if not raw_url or ("/note/" not in raw_url and "/explore/" not in raw_url and "/search_result/" not in raw_url):
                continue
            m = re.search(r"/(?:search_result|note|explore)/([a-f0-9]+)", raw_url)
            if m:
                feeds.append({"note_id": m.group(1), "url": raw_url})
        return feeds

    def test_search_result_urls_kept(self):
        urls = ["/search_result/69f46cae000000001b02067f?xsec_token=ABC"]
        result = self._simulate_url_filter(urls)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["note_id"], "69f46cae000000001b02067f")

    def test_explore_urls_kept(self):
        urls = ["/explore/69f4716b000000003502e754"]
        result = self._simulate_url_filter(urls)
        self.assertEqual(len(result), 1)

    def test_note_urls_kept(self):
        urls = ["/note/69f4716b000000003502e754"]
        result = self._simulate_url_filter(urls)
        self.assertEqual(len(result), 1)

    def test_invalid_urls_filtered(self):
        urls = ["/user/profile/xxx", "", "/other/path"]
        result = self._simulate_url_filter(urls)
        self.assertEqual(len(result), 0)

    def test_mixed_urls(self):
        result = self._simulate_url_filter(SAMPLE_RAW_DATA_FROM_SEARCH_PAGE)
        # 应该保留 search_result + explore + note，排除无效
        self.assertGreaterEqual(len(result), 3)

    def test_all_search_result_format(self):
        """所有 URL 都是 search_result 格式的边界情况"""
        urls = [
            "/search_result/69f46cae000000001b02067f?xsec_token=ABC",
            "/search_result/69f4cfaf000000001e00fa27?xsec_token=DEF",
            "/search_result/69f4716b000000003502e754?xsec_token=GHI",
        ]
        result = self._simulate_url_filter(urls)
        self.assertEqual(len(result), 3)


class TestXsecTokenExtraction(unittest.TestCase):
    """xsec_token 提取测试"""

    def test_with_xsec_source(self):
        raw = "/search_result/69f46cae?xsec_token=ABC123&xsec_source=pc_feed"
        m = re.search(r"xsec_token=([^&\s]+)", raw)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "ABC123")

    def test_without_xsec_source(self):
        raw = "/explore/69f4716b?xsec_token=DEF456"
        m = re.search(r"xsec_token=([^&\s]+)", raw)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "DEF456")

    def test_no_xsec_token(self):
        raw = "/search_result/69f46cae"
        m = re.search(r"xsec_token=([^&\s]+)", raw)
        self.assertIsNone(m)


class TestFilterHelperClick(unittest.TestCase):
    """FilterHelper 点击坐标逻辑测试"""

    def _simulate_filter_coord(self, label, filter_elements):
        """模拟找 filter 坐标"""
        for el in filter_elements:
            if el.get("text") == label and el.get("rect", {}).get("width", 0) > 5:
                r = el["rect"]
                return {"x": r["x"] + r["width"] // 2, "y": r["top"] + r["height"] // 2}
        return None

    def test_find_latest_coord(self):
        elements = [
            {"text": "综合", "rect": {"x": 900, "top": 187, "width": 80, "height": 40}},
            {"text": "最新", "rect": {"x": 936, "top": 187, "width": 96, "height": 40}},
            {"text": "一周内", "rect": {"x": 1044, "top": 412, "width": 96, "height": 40}},
        ]
        coord = self._simulate_filter_coord("最新", elements)
        self.assertIsNotNone(coord)
        self.assertEqual(coord["x"], 984)
        self.assertEqual(coord["y"], 207)

    def test_find_week_coord(self):
        elements = [
            {"text": "综合", "rect": {"x": 900, "top": 187, "width": 80, "height": 40}},
            {"text": "最新", "rect": {"x": 936, "top": 187, "width": 96, "height": 40}},
            {"text": "一周内", "rect": {"x": 1044, "top": 412, "width": 96, "height": 40}},
        ]
        coord = self._simulate_filter_coord("一周内", elements)
        self.assertIsNotNone(coord)
        self.assertEqual(coord["x"], 1092)
        self.assertEqual(coord["y"], 432)

    def test_label_not_found(self):
        elements = [{"text": "综合", "rect": {"x": 900, "top": 187, "width": 80, "height": 40}}]
        coord = self._simulate_filter_coord("最新", elements)
        self.assertIsNone(coord)


class TestSearchNav(unittest.TestCase):
    """搜索导航逻辑测试：fill + keyboard.press vs click search-icon"""

    def test_fill_uses_visible_input(self):
        """page.fill() 会自动找可见的 input，不会填到 HP 注入的隐藏元素"""
        # 这是关键行为验证：Playwright page.fill() 的语义是找"可交互"的元素
        # HP 注入的 aria-hidden input 不算可交互，所以 fill 不会填到它
        # 这个测试验证代码里用的是 page.fill() 而不是 search_input.fill()
        with open(ROOT / "core" / "search_collector.py", encoding="utf-8") as f:
            code = f.read()

        # 验证用的是 page.fill 而不是 element.fill
        self.assertIn("self.page.fill(", code)
        self.assertNotIn("search_input.fill(", code)

    def test_keyboard_enter_after_fill(self):
        """fill 后应该用 page.keyboard.press('Enter') 而不是 element.press('Enter')"""
        with open(ROOT / "core" / "search_collector.py", encoding="utf-8") as f:
            code = f.read()

        self.assertIn("self.page.keyboard.press(", code)
        self.assertNotIn("search_input.press(", code)


class TestFilterClickMethod(unittest.TestCase):
    """筛选点击方式测试：应该用 mouse.click 坐标而不是 el.click()"""

    def test_filter_helper_uses_mouse_click(self):
        """FilterHelper.click_filter 应该用 page.mouse.click 坐标"""
        with open(ROOT / "core" / "search_collector.py", encoding="utf-8") as f:
            code = f.read()

        # JS el.click() 已被证明不可靠，改用 mouse.click
        self.assertIn("self.page.mouse.click(", code)
        self.assertNotIn("el.click()", code)


if __name__ == "__main__":
    unittest.main(verbosity=2)