#!/usr/bin/env python3
"""
run_batch.py - 串行执行关键词采集任务

支持参数：
    python run_batch.py --limit 50 --timeout 600
    python run_batch.py --keyword 汕尾美食 --limit 30
    python run_batch.py --restart-browser-every 3  # 每3个关键词重启浏览器（避免内存累积）
"""
from __future__ import annotations

import argparse
import os
import signal
import sys
import threading
import time
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
import config
from core.browser_manager import BrowserManager
from core.search_collector import SearchCollector
from core.note_detail import NoteDetailCollector
from filter.filter_service import FilterService
from filter.review_service import ReviewService
from output.feishu_service import FeishuOutputService
from utils.storage import CollectedStorage, RecentStorage

LOG_DIR = PROJECT_ROOT / "logs"


def _get_log_path(keyword: str) -> Path:
    """返回该关键词今日日志路径：logs/{keyword}_YYYY-MM-DD.log"""
    today = datetime.now().strftime("%Y-%m-%d")
    path = LOG_DIR / f"{keyword}_{today}.log"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    return path


def _log(keyword: str, level: str, msg: str, module: str = "run_batch"):
    """写入日志行到关键词当日文件，同时保留 stdout 输出"""
    ts = datetime.now().strftime("%H:%M")
    line = f"{ts} [{keyword}] [{level}] [{module}] {msg}"
    print(line)
    try:
        with open(_get_log_path(keyword), "a", encoding="utf-8", buffering=1) as f:
            f.write(line + "\n")
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        pass


def _load_storage():
    return CollectedStorage()


def load_keywords(keywords_txt: Path | None = None) -> list[dict]:
    keywords_txt = keywords_txt or (PROJECT_ROOT / "keywords.txt")
    keywords = []
    with open(keywords_txt, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.rsplit(",", 1)
            keyword = parts[0].strip()
            group = parts[1].strip() if len(parts) > 1 else "default"
            keywords.append({"keyword": keyword, "group": group})
    return keywords


def run_one_keyword(
    browser_manager: BrowserManager,
    keyword: str,
    limit: int,
    timeout: int,
    storage: CollectedStorage,
) -> dict:
    run_id = storage.make_run_id(keyword)
    result = {
        "run_id": run_id,
        "keyword": keyword,
        "success": False,
        "passed_count": 0,
        "feeds_count": 0,
        "elapsed": 0.0,
        "error": None,
    }
    context = None
    timer = None

    try:
        context = browser_manager.browser.new_context(
            viewport=config.VIEWPORT,
            user_agent=config.USER_AGENT,
        )
        context.add_init_script(
            """Object.defineProperty(navigator, 'webdriver', {
                get: () => false, configurable: true
            });"""
        )
        browser_manager._load_cookies_to_context(context)
        start_time = time.time()

        def timeout_handler():
            _log(keyword, "WARN", f"⏰ 超时（{timeout}s），将在当前笔记完成后停止")

        timer = threading.Timer(timeout, timeout_handler)
        timer.start()

        # 搜索采集
        collector = SearchCollector(browser_manager.browser, context)
        feeds = collector.collect(keyword, limit=limit)
        result["feeds_count"] = len(feeds)
        _log(keyword, "INFO", f"采集完成: {len(feeds)} 条 Feeds")

        # Enrichment
        detail_collector = NoteDetailCollector(browser_manager.browser, context, browser_manager.cookie_file)
        notes = detail_collector.enrich_all(feeds)
        # 丢弃不可访问的帖子（删/私/限）
        accessible_notes = [n for n in notes if n.content != "[内容无法获取]"]
        dropped = len(notes) - len(accessible_notes)
        _log(keyword, "INFO", f"enrichment 完成: {len(notes)} 条（丢弃 {dropped} 条不可见帖子）")
        notes = accessible_notes
        for note in notes:
            dur = round(time.time() - start_time, 1)
            if note.content and not note.is_hashtag_fallback:
                _log(keyword, "DEBUG", f"PASS {note.note_id} Detail (duration={dur}s)", module="Detail")
            else:
                reason = "hashtag正文" if note.is_hashtag_fallback else "内容为空"
                _log(keyword, "DEBUG", f"FAIL {note.note_id} Detail {reason} (duration={dur}s)", module="Detail")

        # FilterService
        filter_svc = FilterService()
        passed_notes = []
        for note in notes:
            r = filter_svc.filter_one(note, keyword=keyword)
            note.filter_passed = r.passed
            note.filter_reasons = r.reasons if r.reasons is not None else ""
            note.filter_result = r
            if r.passed:
                _log(keyword, "DEBUG", f"PASS {note.note_id} Filter (reasons={r.reasons})", module="Filter")
                passed_notes.append(note)
            else:
                _log(keyword, "DEBUG", f"FAIL {note.note_id} Filter {r.reasons} (duration={round(time.time()-start_time,1)}s)", module="Filter")
        result["passed_count"] = len(passed_notes)
        _log(keyword, "INFO", f"筛选完成: {len(passed_notes)}/{len(notes)} 条通过")

        # ReviewService（强制 gate）
        review_svc = ReviewService()
        reviewed = review_svc.review(passed_notes, keyword=keyword)
        for note in reviewed:
            _log(keyword, "DEBUG", f"PASS {note.note_id} Review", module="Review")
        for note in passed_notes:
            if not any(n.note_id == note.note_id for n in reviewed):
                _log(keyword, "DEBUG", f"FAIL {note.note_id} Review (reasons={note.filter_reasons}) (duration={round(time.time()-start_time,1)}s)", module="Review")
        _log(keyword, "INFO", f"复查完成: {len(reviewed)} 条终审通过")

        # 写入飞书
        if reviewed:
            try:
                feishu = FeishuOutputService()
                feishu.input_path = review_svc.output_path
                written, skipped, failed = feishu.write(reviewed, keyword=keyword)
                _log(keyword, "INFO", f"飞书写入完成: 写入={written} 跳过={skipped} 失败={failed}")
            except Exception as e:
                _log(keyword, "ERROR", f"飞书写入失败: {e}")

        # 企业微信通知（采集结果推送给运营群）
        # 从飞书表格直接查询所有"已通知"未勾选的笔记进行通知（覆盖孤儿笔记）
        # 发送后仅标记真正发送成功的
        try:
            feishu_svc = FeishuOutputService()

            # 从飞书表格捞所有未通知的笔记（含本次新建 + 历史孤儿）
            unnotified_raw = feishu_svc.get_unnotified_records()

            if not unnotified_raw:
                _log(keyword, "INFO", "微信通知: 全部已通知，跳过")
            else:
                # 转换为 dict 格式供 notify_notes 使用
                unnotified_notes = []
                for r in unnotified_raw:
                    f = r["fields"]
                    url_field = f.get("链接", "")
                    url = url_field.get("link", url_field) if isinstance(url_field, dict) else url_field
                    unnotified_notes.append({
                        "note_id": f.get("笔记ID", ""),
                        "title": f.get("标题", ""),
                        "note_url": url,
                        "type": f.get("类型", ""),
                    })

                from utils.notify_client import notify_notes as _send_notify
                sent_ids = _send_notify(unnotified_notes, dry_run=False)
                if sent_ids:
                    feishu_svc.mark_notified(sent_ids)
                    _log(keyword, "INFO", f"微信通知发送完成 ({len(sent_ids)} 条)")
                else:
                    _log(keyword, "INFO", "微信通知全部失败，未标记已通知")
        except Exception as e:
            _log(keyword, "ERROR", f"微信通知失败: {e}")

        storage.save(run_id, keyword, notes)
        storage.append_manifest(run_id, keyword, len(passed_notes))

        result["elapsed"] = time.time() - start_time
        result["success"] = True

    except Exception as e:
        import traceback
        result["error"] = str(e)
        _log(keyword, "ERROR", f"❌ 失败: {e}")
        traceback.print_exc()

    finally:
        if timer:
            timer.cancel()
        if context:
            try:
                context.close()
            except Exception:
                pass
        elapsed = result.get("elapsed", 0)
        status = "✅" if result["success"] else "❌"
        _log(keyword, "INFO" if result["success"] else "ERROR", f"{status} 完成，耗时 {elapsed:.1f}s")

    return result


def run_with_browser_restart(
    keywords: list[dict],
    limit: int,
    timeout: int,
    restart_every: int,
):
    """每隔 N 个关键词重启一次浏览器，避免内存累积"""
    storage = _load_storage()
    results = []
    total = len(keywords)

    for i, kw_info in enumerate(keywords, 1):
        keyword = kw_info["keyword"]
        group = kw_info["group"]

        # 每 N 个关键词重启一次浏览器
        if i == 1 or (i - 1) % restart_every == 0:
            if i > 1:
                _log(keyword, "INFO", f"[{i-1}] 重启浏览器（每 {restart_every} 个关键词自动重启）")
                browser_mgr.__exit__(None, None, None)
                time.sleep(3)  # 等待旧进程完全退出
                _log(keyword, "INFO", f"[{i}] 启动新浏览器")
                browser_mgr = BrowserManager()
                browser, _ = browser_mgr.__enter__()
            else:
                _log(keyword, "INFO", "启动 Playwright Browser")
                browser_mgr = BrowserManager()
                browser, _ = browser_mgr.__enter__()
                _log(keyword, "INFO", "Browser 启动成功，开始采集")

        _log(keyword, "INFO", f"开始采集 [{i}/{total}] [{group}] {keyword}")

        result = run_one_keyword(
            browser_manager=browser_mgr,
            keyword=keyword,
            limit=limit,
            timeout=timeout,
            storage=storage,
        )
        results.append(result)

        # 批次间休息
        if i < total:
            _log(keyword, "INFO", "休息 5s...")
            time.sleep(5)

    # 最终清理
    try:
        browser_mgr.__exit__(None, None, None)
    except Exception:
        pass

    return results


def main():
    parser = argparse.ArgumentParser(description="串行执行关键词采集任务")
    parser.add_argument("--keyword", "-k", type=str, default=None)
    parser.add_argument("--limit", "-l", type=int, default=50)
    parser.add_argument("--timeout", "-t", type=int, default=600)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--group", type=str, default=None)
    parser.add_argument("--keywords-file", type=str, default=None)
    parser.add_argument(
        "--restart-browser-every", type=int, default=0,
        help="每N个关键词重启浏览器（默认0=不重启，3-5较安全）"
    )
    args = parser.parse_args()

    keywords_file = Path(args.keywords_file) if args.keywords_file else None
    all_kw = load_keywords(keywords_file)
    if args.group:
        all_kw = [kw for kw in all_kw if kw["group"] == args.group]
    if args.keyword:
        all_kw = [kw for kw in all_kw if kw["keyword"] == args.keyword]

    if not all_kw:
        print("没有要跑的关键词")
        return

    print(f"待执行 {len(all_kw)} 个关键词，超时={args.timeout}s，limit={args.limit}")
    if args.restart_browser_every > 0:
        print(f"浏览器重启策略: 每 {args.restart_browser_every} 个关键词重启一次")

    if args.dry_run:
        for kw in all_kw:
            print(f"  [{kw['group']}] {kw['keyword']}")
        return

    if args.restart_browser_every > 0:
        results = run_with_browser_restart(
            all_kw, args.limit, args.timeout, args.restart_browser_every
        )
    else:
        # 原有逻辑：整个批次共用一个浏览器
        storage = _load_storage()
        browser_mgr = BrowserManager()
        browser_started = False
        results = []
        try:
            browser, _ = browser_mgr.__enter__()
            browser_started = True
            print("Browser 启动成功，开始采集")
            for i, kw_info in enumerate(all_kw, 1):
                keyword = kw_info["keyword"]
                group = kw_info["group"]
                _log(keyword, "INFO", f"开始采集 [{i}/{len(all_kw)}] [{group}] {keyword}")
                result = run_one_keyword(
                    browser_manager=browser_mgr,
                    keyword=keyword,
                    limit=args.limit,
                    timeout=args.timeout,
                    storage=storage,
                )
                results.append(result)
                if i < len(all_kw):
                    _log(keyword, "INFO", "休息 5s...")
                    time.sleep(5)
        finally:
            if browser_started:
                print("关闭 Browser...")
                browser_mgr.__exit__(None, None, None)

    # 汇总报告
    print("执行完毕")
    success_cnt = sum(1 for r in results if r["success"])
    pass_cnt = sum(r["passed_count"] for r in results)
    print(f"关键词: {len(results)} 个，成功: {success_cnt}，共通过: {pass_cnt} 条")
    for r in results:
        status = "✅" if r["success"] else "❌"
        error = f" ({r['error']})" if r["error"] else ""
        print(f"  {status} [{r['keyword']}] 通过={r['passed_count']} Feeds={r['feeds_count']} {r['elapsed']:.1f}s{error}")


if __name__ == "__main__":
    main()