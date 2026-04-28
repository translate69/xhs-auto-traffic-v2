"""
xhs-auto-traffic-v2 唯一入口
用法：
    python main.py --keyword 汕尾美食 --limit 50
    python main.py --stage collect --keyword 汕尾美食 --limit 30
    python main.py --stage feishu
"""
import argparse
import sys
from pathlib import Path

# 确保项目根目录在 sys.path
sys.path.insert(0, str(Path(__file__).parent))

import config
from core.browser_manager import BrowserManager
from core.search_collector import SearchCollector
from core.note_detail import NoteDetailCollector
from filter.filter_service import FilterService
from output.feishu_service import FeishuOutputService


def run_collect(keyword: str, limit: int, headless: bool = True):
    """采集 + enrichment + 过滤，完整流程"""
    records = []

    with BrowserManager(headless=headless) as (browser, context):
        # ── 搜索采集 ─────────────────────────────────────
        collector = SearchCollector(browser, context)
        feeds = collector.collect(keyword, limit=limit)
        print(f"[main] 搜索采集完成: {len(feeds)} 条")

        if not feeds:
            print("[main] 无采集结果，退出")
            return []

        # ── 详情 enrichment ──────────────────────────────
        detail_collector = NoteDetailCollector(browser, context)
        enriched = detail_collector.enrich_all(feeds)
        print(f"[main] enrichment 完成: {len(enriched)} 条")

        # ── 记录「内容无法获取」的笔记（待人工确认）─────────
        unavailable_notes = [n for n in enriched if n.content == "[内容无法获取]"]
        if unavailable_notes:
            _write_unavailable(unavailable_notes, keyword)
            print(f"[main] 内容无法获取: {len(unavailable_notes)} 条（已写入待人工确认）")

        # ── FilterService 重度过滤 ────────────────────────
        filter_svc = FilterService()
        filtered = filter_svc.filter_all(enriched)
        print(f"[main] 筛选完成: {len(filtered)} 条通过")

        records = filtered

    # ── 输出 ──────────────────────────────────────────────
    if records:
        feishu = FeishuOutputService()
        feishu.write(records, keyword=keyword)
        print(f"[main] 飞书写入完成: {len(records)} 条")

    return records


def _write_unavailable(notes: list, keyword: str):
    """写入无法获取内容的笔记，供人工确认"""
    import json
    from datetime import datetime
    config.FEISHU_DIR.mkdir(parents=True, exist_ok=True)
    output_path = config.FEISHU_DIR / "unavailable_for_review.jsonl"
    rows = []
    for detail in notes:
        import re
        note_url = detail.url
        if "/explore/" not in note_url and "search_result/" in detail.url:
            m = re.search(r"search_result/([a-fA-F0-9]+)", detail.url)
            if m:
                note_id = m.group(1)
                note_url = f"https://www.xiaohongshu.com/explore/{note_id}?xsec_token={detail.xsec_token}&xsec_source=pc_search"
        rows.append({
            "title": detail.title or "",
            "note_url": note_url,
            "note_id": detail.note_id,
            "author": detail.author or "",
            "published_at": detail.published_at or "",
            "keyword": keyword,
            "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
    with open(output_path, "a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def run_feishu(data_dir: Path | None = None):
    """单独触发飞书写入"""
    import json
    from filter.filter_service import FilterService

    data_dir = data_dir or config.DATA_DIR
    input_path = data_dir / "filtered_for_feishu.jsonl"

    if not input_path.exists():
        print(f"[main] 文件不存在: {input_path}")
        return []

    records = []
    with open(input_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if records:
        feishu = FeishuOutputService()
        feishu.write(records)
        print(f"[main] 飞书写入完成: {len(records)} 条")

    return records


def main():
    parser = argparse.ArgumentParser(description="xhs-auto-traffic-v2")
    parser.add_argument("--keyword", "-k", type=str, help="搜索关键词")
    parser.add_argument("--limit", "-l", type=int, default=config.DEFAULT_LIMIT, help=f"采集数量（默认 {config.DEFAULT_LIMIT}）")
    parser.add_argument("--stage", "-s", type=str, default="all", choices=["all", "collect", "feishu"], help="运行阶段")
    parser.add_argument("--debug", action="store_true", help="调试模式（headed 浏览器）")
    parser.add_argument("--data-dir", type=str, default=None, help="数据目录")

    args = parser.parse_args()

    headless = not args.debug

    if args.stage == "collect":
        if not args.keyword:
            print("[main] collect 阶段需要 --keyword")
            sys.exit(1)
        run_collect(args.keyword, args.limit, headless=headless)

    elif args.stage == "feishu":
        data_dir = Path(args.data_dir) if args.data_dir else None
        run_feishu(data_dir)

    elif args.stage == "all":
        if not args.keyword:
            print("[main] all 阶段需要 --keyword")
            sys.exit(1)
        run_collect(args.keyword, args.limit, headless=headless)


if __name__ == "__main__":
    main()
