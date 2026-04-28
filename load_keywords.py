"""关键词配置加载器"""
from pathlib import Path

KEYWORDS_FILE = Path(__file__).parent / "keywords.txt"


def load_keywords() -> list[dict]:
    """
    加载 keywords.txt，返回:
        [{"keyword": "汕尾美食", "group": "core"}, ...]
    """
    keywords = []
    if not KEYWORDS_FILE.exists():
        return keywords

    for line in KEYWORDS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.rsplit(",", 1)
        keyword = parts[0].strip()
        group = parts[1].strip() if len(parts) > 1 else "core"
        if keyword:
            keywords.append({"keyword": keyword, "group": group})

    return keywords


def get_keywords_by_group(group: str | None = None) -> list[dict]:
    """按分组筛选，group=None 返回全部"""
    all_kw = load_keywords()
    if group is None:
        return all_kw
    return [kw for kw in all_kw if kw["group"] == group]


if __name__ == "__main__":
    # 测试
    all_kw = load_keywords()
    print(f"共加载 {len(all_kw)} 个关键词")
    for kw in all_kw:
        print(f"  [{kw['group']}] {kw['keyword']}")