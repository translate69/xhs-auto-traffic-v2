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

        # ── FilterService 重度过滤 ────────────────────────
        filter_svc = FilterService()
        filtered = filter_svc.filter_all(enriched)
        print(f"[main] 筛选完成: {len(filtered)} 条通过")

        records = filtered

    # ── 输出 ──────────────────────────────────────────────
    if records:
        feishu = FeishuOutputService()
        feishu.write(records)
        print(f"[main] 飞书写入完成: {len(records)} 条")

    return records


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
