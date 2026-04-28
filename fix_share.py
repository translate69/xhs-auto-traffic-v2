"""Fix _is_share_post_only"""
import re

path = r"E:\translate\claw\xhs-auto-traffic-v2\filter\filter_service.py"
with open(path, "r", encoding="utf-8") as f:
    file_text = f.read()

start_marker = '    def _is_share_post_only(self, title: str, content: str)'
start_idx = file_text.find(start_marker)
if start_idx == -1:
    print("START NOT FOUND")
else:
    rest = file_text[start_idx:]
    matches = list(re.finditer(r'\n    def [_\w]+\(', rest))
    end_idx = start_idx + matches[0].start() if matches else start_idx + len(rest)
    old_func = file_text[start_idx:end_idx]
    print(f"Found function, len={len(old_func)}")

    new_func = '''    def _is_share_post_only(self, title: str, content: str) -> str | None:
        """检查是否为纯分享/攻略贴。返回淘汰原因或 None"""
        combined = title + " " + content
        title_has_explicit_ask = has_signal(title, ASK_SIGNALS)
        # 推荐格式（「xxx推荐xxx」）不算求助信号
        if self._is_recommendation_format(title):
            title_has_explicit_ask = False
        content_has_ask = has_signal(content, ["求", "想问", "请问", "求指教"])
        title_has_bang = "帮我" in title or "帮帮我" in title or "帮忙" in title
        has_any_ask = title_has_explicit_ask or content_has_ask or title_has_bang

        if has_any_ask:
            return None  # 有求助信号，不淘汰

        if any(kw in combined for kw in HOTEL_PRAISE_KEYWORDS):
            return "纯酒店夸赞广告"
        if any(kw in combined for kw in TEAM_BUILD_KEYWORDS):
            return "纯团建广告"

        # 「xxx推荐xxx」格式标题 → 纯分享推荐，不算求助
        if self._is_recommendation_format(title):
            return "纯分享攻略贴"

        if any(kw in combined for kw in SHARE_POST_KEYWORDS):
            return "纯分享攻略贴"

        # 强化：纯分享风格
        share_style = (
            content.count("#") >= 2 or
            "打卡" in combined or
            "合集" in combined or
            (title.startswith(("我的", "我在", "我吃", "这次", "终于", "终于打卡"))) or
            (re.search(r"^[在我]\s*\S+", combined.lstrip()) and "推荐" in combined) or
            "没踩雷" in combined or "没踩坑" in combined
        )
        if share_style and not has_any_ask:
            return "纯分享攻略贴"

        return None
'''

    new_text = file_text[:start_idx] + new_func + file_text[end_idx:]
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_text)
    print("REPLACED OK")