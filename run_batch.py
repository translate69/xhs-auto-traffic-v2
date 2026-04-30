"""
run_batch.py - 分批独立执行关键词任务

每个关键词作为独立进程跑，超时自动 kill，进程完全隔离。
超时时间默认 10 分钟，可通过 --timeout 参数调整。

用法：
    python run_batch.py                          # 跑全部关键词
    python run_batch.py --keyword 汕尾美食       # 只跑单个
    python run_batch.py --limit 50              # 每关键词采集50条
    python run_batch.py --timeout 600           # 超时10分钟（默认）
    python run_batch.py --dry-run               # 只看要跑哪些，不实际执行
"""
import argparse
import subprocess
import sys
import time
import os
import uuid
from pathlib import Path
from datetime import datetime

# 项目根目录
PROJECT_ROOT = Path(__file__).parent
MAIN_SCRIPT = PROJECT_ROOT / "main.py"

# 默认超时时间（秒）
DEFAULT_TIMEOUT = 600  # 10分钟

# 修复 Windows 环境下 Python 子进程的中文输出问题
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def _load_storage():
    """动态导入 CollectedStorage"""
    import importlib.util
    storage_path = str(PROJECT_ROOT / "utils" / "storage.py")
    spec = importlib.util.spec_from_file_location("storage", storage_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.CollectedStorage()


def load_keywords(keywords_txt: Path | None = None) -> list[dict]:
    """加载关键词配置"""
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


def run_keyword_with_retry(keyword: str, limit: int, timeout: int, debug: bool, max_retries: int = 2, retry_interval: int = 10) -> tuple[bool, bool, float]:
    """带重试的关键字执行，检测到0结果时自动重试"""
    last_error = None
    for attempt in range(max_retries + 1):
        success, timed_out, elapsed, stdout, stderr = run_keyword_subprocess(
            keyword=keyword, limit=limit, timeout=timeout, debug=debug
        )
        # 检测是否0结果（不是进程失败，只是采集为0）
        zero_results = (
            "无采集结果" in stdout
            or "采集完成: 0" in stdout
            or (not timed_out and success and "0 条" in stdout)
        )
        if zero_results and attempt < max_retries:
            print(f"[{keyword}] 采集0条，{retry_interval}s后重试（第{attempt+1}/{max_retries}次）...")
            time.sleep(retry_interval)
            continue
        return success, timed_out, elapsed, stdout, stderr
    # shouldn't reach here but just in case
    return success, timed_out, elapsed, stdout, stderr

    # 用临时文件捕获输出，避免 Windows 控制台 GBK 编码问题
    task_id = uuid.uuid4().hex[:8]
    stdout_file = PROJECT_ROOT / "logs" / f"_stdout_{task_id}.tmp"
    stderr_file = PROJECT_ROOT / "logs" / f"_stderr_{task_id}.tmp"
    stdout_file.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        str(MAIN_SCRIPT),
        "--keyword", keyword,
        "--limit", str(limit),
    ]
    if debug:
        cmd.append("--debug")

    start_time = time.time()
    timed_out = False
    success = True

    print(f"[{keyword}] 启动 subprocess (timeout={timeout}s)")

    # 创建子进程，环境变量强制 UTF-8
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}

    try:
        with open(stdout_file, "w", encoding="utf-8", errors="replace") as fout, \
             open(stderr_file, "w", encoding="utf-8", errors="replace") as ferr:

            proc = subprocess.Popen(
                cmd,
                stdout=fout,
                stderr=ferr,
                cwd=str(PROJECT_ROOT),
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )

            try:
                proc.wait(timeout=timeout)
                elapsed = time.time() - start_time
                print(f"[{keyword}] 完成，耗时 {elapsed:.1f}s")

            except subprocess.TimeoutExpired:
                timed_out = True
                elapsed = time.time() - start_time
                print(f"[{keyword}] 超时（{timeout}s），强制终止进程")

                proc.kill()
                proc.wait(timeout=10)
                print(f"[{keyword}] 进程已终止")
            finally:
                success = proc.returncode == 0

    finally:
        pass

    # 读取输出
    stdout = stdout_file.read_text(encoding="utf-8", errors="replace")
    stderr = stderr_file.read_text(encoding="utf-8", errors="replace")

    # 清理临时文件
    try:
        stdout_file.unlink(missing_ok=True)
        stderr_file.unlink(missing_ok=True)
    except Exception:
        pass

    return success, timed_out, elapsed, stdout, stderr


def main():
    parser = argparse.ArgumentParser(description="分批独立执行关键词任务")
    parser.add_argument("--keyword", "-k", type=str, default=None, help="只跑指定关键词")
    parser.add_argument("--limit", "-l", type=int, default=50, help="每个关键词采集数量（默认50）")
    parser.add_argument("--timeout", "-t", type=int, default=DEFAULT_TIMEOUT, help=f"单任务超时秒数（默认{DEFAULT_TIMEOUT}）")
    parser.add_argument("--debug", action="store_true", help="启用 headed 浏览器（可见）")
    parser.add_argument("--dry-run", action="store_true", help="只列出要跑的关键词，不实际执行")
    parser.add_argument("--group", type=str, default=None, help="只跑指定分组: core / longtail")
    parser.add_argument("--keywords-file", type=str, default=None, help="关键词文件路径（默认 keywords.txt）")

    args = parser.parse_args()

    # ── 加载关键词 ───────────────────────────────────────
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

    if args.dry_run:
        for kw in all_kw:
            print(f"  [{kw['group']}] {kw['keyword']}")
        return

    # ── 逐个执行 ─────────────────────────────────────────
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for i, kw_info in enumerate(all_kw, 1):
        keyword = kw_info["keyword"]
        group = kw_info["group"]

        print(f"\n{'='*50}")
        print(f"[{i}/{len(all_kw)}] 开始: [{group}] {keyword}")

        success, timed_out, elapsed, stdout, stderr = run_keyword_with_retry(
            keyword=keyword,
            limit=args.limit,
            timeout=args.timeout,
            debug=args.debug,
        )

        # 写日志
        log_file = log_dir / f"{keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"关键词: {keyword}\n")
            f.write(f"分组: {group}\n")
            f.write(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"耗时: {elapsed:.1f}s\n")
            f.write(f"超时: {'是' if timed_out else '否'}\n")
            f.write(f"成功: {'是' if success else '否'}\n")
            f.write(f"\n=== STDOUT ===\n")
            f.write(stdout)
            f.write(f"\n=== STDERR ===\n")
            f.write(stderr)

        status = "超时" if timed_out else ("成功" if success else "失败")
        results.append({
            "keyword": keyword,
            "group": group,
            "status": status,
            "elapsed": elapsed,
            "log": log_file.name,
        })

        print(f"[{keyword}] {status}，耗时 {elapsed:.1f}s")

        # 写 manifest（供 _verify_filter.py 使用）
        if success:
            try:
                storage = _load_storage()
                run_id = storage.make_run_id(keyword)
                storage.append_manifest(run_id, keyword, 1)
            except Exception:
                pass

        # 批次间休息
        if i < len(all_kw):
            print(f"[{keyword}] 休息 5 秒后继续...")
            time.sleep(5)

    # ── 汇总报告 ─────────────────────────────────────────
    print(f"\n{'='*50}")
    print(f"执行完毕，共 {len(all_kw)} 个关键词")

    success_count = sum(1 for r in results if r["status"] == "成功")
    timeout_count = sum(1 for r in results if r["status"] == "超时")
    fail_count = sum(1 for r in results if r["status"] == "失败")

    print(f"汇总: 成功={success_count}, 超时={timeout_count}, 失败={fail_count}")

    print(f"\n详细结果:")
    for r in results:
        print(f"  [{r['group']}] {r['keyword']}: {r['status']} ({r['elapsed']:.1f}s) -> logs/{r['log']}")


if __name__ == "__main__":
    main()