"""
test_enrichment.py - Enrichment 流程测试
测试 NoteDetailCollector 对真实笔记的提取能力
"""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import config
config.HEADLESS = False  # 有头模式

from core.browser_manager import BrowserManager
from core.note_detail import NoteDetailCollector
from dataclasses import dataclass

@dataclass
class FeedNote:
    note_id: str
    url: str
    xsec_token: str
    author: str = ""
    time_text: str = ""
    title: str = ""


class TestEnrichmentExtraction(unittest.TestCase):
    """测试详情页提取完整性"""

    @classmethod
    def setUpClass(cls):
        cls.browser = BrowserManager()
        cls.browser.__enter__()
        _, cls.context = cls.browser.browsers[0]
        cls.page = cls.context.new_page()

    @classmethod
    def tearDownClass(cls):
        cls.page.close()
        cls.browser.__exit__(None, None, None)

    def test_detail_page_extracts_content(self):
        """验证详情页能提取到 content"""
        collector = NoteDetailCollector(self.page)
        feed = FeedNote(
            note_id="69f07da50000000038034854",
            url="/search_result/69f07da50000000038034854?xsec_token=AB8iUZ9FGWg0X_b7ICWd5HSoGdTD_k13l9A13eUOzVM1k=&xsec_source=",
            xsec_token="AB8iUZ9FGWg0X_b7ICWd5HSoGdTD_k13l9A13eUOzVM1k=",
            author="测试",
            time_text="3小时前"
        )
        detail = collector._enrich_single(feed, self.page)
        self.assertIsNotNone(detail)
        self.assertGreater(len(detail.content), 10, "content 应该超过 10 字符")
        print(f"  content: {detail.content[:50]}...")

    def test_detail_page_extracts_title(self):
        """验证详情页能提取到 title"""
        collector = NoteDetailCollector(self.page)
        feed = FeedNote(
            note_id="69f07da50000000038034854",
            url="/search_result/69f07da50000000038034854?xsec_token=AB8iUZ9FGWg0X_b7ICWd5HSoGdTD_k13l9A13eUOzVM1k=&xsec_source=",
            xsec_token="AB8iUZ9FGWg0X_b7ICWd5HSoGdTD_k13l9A13eUOzVM1k=",
        )
        detail = collector._enrich_single(feed, self.page)
        self.assertIsNotNone(detail)
        self.assertGreater(len(detail.title), 0, "title 不应为空")
        print(f"  title: {detail.title}")

    def test_goto_with_search_result_url(self):
        """验证 search_result 格式 URL 可以正常访问详情页"""
        url = "https://www.xiaohongshu.com/search_result/69f07da50000000038034854?xsec_token=AB8iUZ9FGWg0X_b7ICWd5HSoGdTD_k13l9A13eUOzVM1k=&xsec_source="
        self.page.goto(url, wait_until="domcontentloaded")
        self.page.wait_for_timeout(2000)
        # 页面应该加载成功，不崩溃
        self.assertIn("xiaohongshu", self.page.url())
        print(f"  页面 URL: {self.page.url}")


if __name__ == "__main__":
    unittest.main(verbosity=2)