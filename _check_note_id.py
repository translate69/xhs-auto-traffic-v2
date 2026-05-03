import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from core.search_collector import FeedNote
import re

# 模拟 _extract_feeds 的 URL 处理
test_urls = [
    "https://www.xiaohongshu.com/search_result/69ec4d240000000036002fe2?xsec_token=ABVf4fdSa9h_eU4HCBCX-J",
    "https://www.xiaohongshu.com/search_result/69ef913a000000002301c5a6?xsec_token=ABO6-KhblprpGC2OS0LNdi",
]

import urllib.parse
for raw_url in test_urls:
    m = re.search(r"xsec_token=([^&\s]+)", raw_url)
    xsec_token = urllib.parse.unquote(m.group(1)) if m else ""
    print(f"URL: {raw_url[:80]}")
    print(f"  xsec_token: {xsec_token[:30]}")
    feed = FeedNote(url=raw_url, xsec_token=xsec_token, author="test", time_text="1天前", title="")
    print(f"  feed.note_id: {feed.note_id}")
    print()