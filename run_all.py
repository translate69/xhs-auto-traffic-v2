"""
run_all.py - 全量关键词跑 pipeline

用法：
    python run_all.py                  # 跑全部关键词（正常模式）
    python run_all.py --dry-run         # 只看要跑哪些，不实际执行
    python run_all.py --keyword 汕尾美食  # 只跑单个关键词
    python run_all.py --cleanup         # 只执行清理（删除30天前文件）
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

import config
from core.browser_manager import BrowserManager
from core.search_collector import SearchCollector
from core.note_detail import NoteDetailCollector
from filter.filter_service import FilterService
from output.feishu_service import FeishuOutputService
from utils.storage import CollectedStorage
from load_keywords import load_keywords


def run_keyword(keyword: str, limit: int, headless: bool, storage: CollectedStorage):
    """
    执行单个关键词的完整 pipeline。

    断点恢复逻辑：
      1. 生成 run_id，检查 runs/ 目录是否有对应文件
      2. 有 → 直接从文件加载 NoteDetail，跳过采集+enrichment
      3. 无 → 正常采集+enrichment，完成后写入中间文件
    """
    run_id = storage.make_run_id(keyword)
    run_file = storage.run_file_path(run_id)

    # ── 断点恢复 ────────────────────────────────────────
    if storage.exists(run_id):
        print(f"[{keyword}] 发现已有文件，跳过采集+enrichment，直接加载")
        details = storage.load(run_id)  # list[dict]
        print(f"[{keyword}] 从断点恢复: {len(details)} 条")
    else:
        print(f"[{keyword}] 开始采集 (run_id={run_id})")

        # 采集 + enrichment
        with BrowserManager(headless=headless) as (browser, context):
            collector = SearchCollector(browser, context)
            feeds = collector.collect(keyword, limit=limit)
            print(f"[{keyword}] 搜索采集: {len(feeds)} 条")

            if not feeds:
                print(f"[{keyword}] 无采集结果，退出")
                return 0

            detail_collector = NoteDetailCollector(browser, context)
            enriched = detail_collector.enrich_all(feeds)
            print(f"[{keyword}] enrichment: {len(enriched)} 条")

        # ── 写入中间文件 ──────────────────────────────────
        run_file = storage.save(run_id, keyword, enriched)
        print(f"[{keyword}] 中间文件已写入: {run_file}")

        # 供下游使用（list[NoteDetail]，不是 dict）
        details = enriched

    # ── 过滤 + 飞书写入 ──────────────────────────────────
    from core.note_detail import NoteDetail
    from dataclasses import fields

    # dict → NoteDetail（断点恢复时是 dict，正常采集时是 NoteDetail）
    notes = []
    for d in details:
        if isinstance(d, NoteDetail):
            notes.append(d)
        else:
            # 从 dict 构造 NoteDetail（跳过不存在的字段）
            valid_fields = {f.name for f in fields(NoteDetail)}
            filtered = {k: v for k, v in d.items() if k in valid_fields}
            notes.append(NoteDetail(**filtered))

    filter_svc = FilterService()
    filtered = filter_svc.filter_all(notes)
    print(f"[{keyword}] 筛选通过: {len(filtered)} 条")

    # manifest 记录
    storage.append_manifest(run_id, keyword, len(notes))

    if filtered:
        feishu = FeishuOutputService()
        feishu.write(filtered)
        print(f"[{keyword}] 飞书写入: {len(filtered)} 条")

    return len(filtered)


def main():
    parser = argparse.ArgumentParser(description="xhs-auto-traffic-v2 全量跑")
    parser.add_argument("--keyword", "-k", type=str, default=None, help="只跑指定关键词")
    parser.add_argument("--limit", "-l", type=int, default=config.DEFAULT_LIMIT, help=f"采集数量（默认 {config.DEFAULT_LIMIT}）")
    parser.add_argument("--debug", action="store_true", help="headed 浏览器（可见）")
    parser.add_argument("--dry-run", action="store_true", help="只列出要跑的关键词，不实际执行")
    parser.add_argument("--cleanup", action="store_true", help="只执行清理（删除30天前文件）")
    parser.add_argument("--group", type=str, default=None, help="只跑指定分组: core / longtail")

    args = parser.parse_args()

    headless = not args.debug
    storage = CollectedStorage()

    # ── 清理模式 ─────────────────────────────────────────
    if args.cleanup:
        deleted = storage.clean_old(days=30)
        print(f"清理完成: 删除 {len(deleted)} 个旧文件")
        for f in deleted:
            print(f"  删除: {f.name}")
        return

    # ── 加载关键词 ───────────────────────────────────────
    all_kw = load_keywords()
    if args.group:
        all_kw = [kw for kw in all_kw if kw["group"] == args.group]
    if args.keyword:
        all_kw = [kw for kw in all_kw if kw["keyword"] == args.keyword]

    if not all_kw:
        print("没有要跑的关键词")
        return

    print(f"待执行 {len(all_kw)} 个关键词（headless={headless}）")

    if args.dry_run:
        for kw in all_kw:
            print(f"  [{kw['group']}] {kw['keyword']}")
        return

    # ── 逐个跑 ───────────────────────────────────────────
    total_passed = 0
    for kw_info in all_kw:
        keyword = kw_info["keyword"]
        print(f"\n{'='*50}")
        print(f"开始: [{kw_info['group']}] {keyword}")
        try:
            n = run_keyword(keyword, args.limit, headless, storage)
            total_passed += n
            print(f"完成: {keyword} → {n} 条通过")
        except Exception as e:
            print(f"出错: {keyword} → {e}")
            import traceback
            traceback.print_exc()

    print(f"\n全部完成：通过 {total_passed} 条")


if __name__ == "__main__":
    main()