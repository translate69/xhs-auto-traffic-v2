#!/usr/bin/env python3
"""
run_cron_batch.py - cron 驱动，每次跑3个关键词，10分钟循环一圈

工作流程：
1. 检查 .batch_lock 文件（防止并发重叠）
2. 读取 .batch_progress 获取当前批次
3. 启动后台子进程跑 run_batch.py（nohup，不 capture stdout）
4. 轮转批次进度
5. 等够10分钟退出

用法：cron 每10分钟触发一次
    */10 * * * * python E:/translate/claw/xhs-auto-traffic-v2/run_cron_batch.py
"""
from __future__ import annotations

import os
import sys
import time
import signal
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
LOCK_FILE = PROJECT_ROOT / ".batch_lock"
PROGRESS_FILE = PROJECT_ROOT / ".batch_progress"
LOG_FILE = PROJECT_ROOT / "logs" / "cron_batch.log"
PID_FILE = PROJECT_ROOT / ".playwright_pids"

# 批次配置（每批3个，最后一批2个）
BATCHES = [
    ["汕尾旅游攻略", "汕尾住宿推荐", "汕尾美食推荐"],
    ["汕尾去哪吃", "汕尾去哪住", "汕尾旅游"],
    ["汕尾美食", "广州到汕尾自驾住哪", "深圳到汕尾自驾住哪"],
    ["汕尾红海湾民宿", "汕尾红海湾攻略", "汕尾3天2晚攻略"],
    ["汕尾2天1晚行程", "汕尾本地人推荐美食", "汕尾海边民宿推荐"],
    ["汕尾周末去哪玩", "汕尾亲子游"],
]
BATCH_DELAY_SECONDS = 10 * 60  # 10分钟间隔


def _get_progress() -> int:
    try:
        return int(PROGRESS_FILE.read_text().strip())
    except Exception:
        return 0


def _set_progress(batch_idx: int):
    PROGRESS_FILE.write_text(str(batch_idx))


def _log(msg: str):
    ts = time.strftime("%m-%d %H:%M")
    line = f"{ts} [cron_batch] {msg}"
    try:
        print(line)
    except UnicodeEncodeError:
        # Windows GBK 环境：编码失败时用 fallback
        print(line.encode("utf-8", errors="replace").decode("utf-8", errors="replace"))
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _sigint_handler(signum, frame):
    _log("收到 SIGINT，清理锁文件")
    try:
        LOCK_FILE.unlink()
    except Exception:
        pass
    sys.exit(0)


signal.signal(signal.SIGINT, _sigint_handler)


def _is_process_alive(pid: int) -> bool:
    try:
        import psutil
        return psutil.pid_exists(pid)
    except Exception:
        return False


def _acquire_lock() -> bool:
    if LOCK_FILE.exists():
        try:
            pid = int(LOCK_FILE.read_text().strip())
            if _is_process_alive(pid):
                _log(f"进程 {pid} 还在跑，跳过本次")
                return False
        except Exception:
            pass
    LOCK_FILE.write_text(str(os.getpid()))
    return True


def _release_lock():
    try:
        LOCK_FILE.unlink()
    except Exception:
        pass


def _cleanup_playwright_pids():
    try:
        import json
        pids = json.loads(PID_FILE.read_text())
        killed = []
        for p in pids:
            try:
                subprocess.run(
                    ["taskkill", "/F", "/PID", str(p)],
                    capture_output=True, timeout=5
                )
                killed.append(p)
            except Exception:
                pass
        if killed:
            _log(f"清理 Playwright PIDs: {killed}")
    except Exception:
        pass


def main():
    # ---- 并发保护 ----
    if not _acquire_lock():
        sys.exit(0)

    # ---- 读进度 ----
    current = _get_progress()
    if current < 0 or current >= len(BATCHES):
        current = 0

    keywords = BATCHES[current]
    _log(f"批次 {current + 1}/{len(BATCHES)} | 关键词: {keywords}")

    # ---- 构造临时关键词文件 ----
    batch_file = PROJECT_ROOT / ".batch_current.txt"
    core_kw_set = {
        "汕尾旅游攻略", "汕尾住宿推荐", "汕尾美食推荐",
        "汕尾去哪吃", "汕尾去哪住", "汕尾旅游", "汕尾美食",
    }
    with open(batch_file, "w", encoding="utf-8") as f:
        for kw in keywords:
            group = "core" if kw in core_kw_set else "longtail"
            f.write(f"{kw},{group}\n")

    # ---- 启动后台子进程（不 capture，避免 buffer 阻塞）----
    start_time = time.time()
    log_out = PROJECT_ROOT / "logs" / f"batch_{current + 1}.log"
    log_err = PROJECT_ROOT / "logs" / f"batch_{current + 1}.err"

    child = subprocess.Popen(
        [sys.executable, "run_batch.py",
         "--keywords-file", str(batch_file),
         "--limit", "20",
         "--restart-browser-every", "3"],
        cwd=str(PROJECT_ROOT),
        stdout=open(log_out, "w", encoding="utf-8", buffering=1),
        stderr=open(log_err, "w", encoding="utf-8", buffering=1),
        stdin=subprocess.DEVNULL,  # 防止 stdin 阻塞
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
    )
    _log(f"子进程 PID={child.pid}，输出: {log_out.name}")

    # ---- 监控子进程，等它完成 ----
    try:
        retcode = child.wait(timeout=600)
        elapsed = time.time() - start_time
        if retcode == 0:
            _log(f"[OK] 完成，耗时 {elapsed:.0f}s")

            # 从 stdout 日志末尾提取通过条数
            try:
                lines = open(log_out, encoding="utf-8", errors="replace").readlines()
                summary_lines = [l.strip() for l in lines if "成功:" in l.strip()]
                if summary_lines:
                    _log(f"结果: {summary_lines[-1]}")
                else:
                    passed_lines = [l for l in lines if "共通过:" in l]
                    if passed_lines:
                        _log(f"结果: {passed_lines[-1].strip()}")
            except Exception as e:
                _log(f"读日志失败: {e}")
        else:
            _log(f"[FAIL] 子进程退出码 {retcode}")
            # 读错误日志
            if log_err.exists():
                err_content = open(log_err, encoding="utf-8", errors="replace").read()
                if err_content:
                    _log(f"stderr: {err_content[-500:]}")
    except subprocess.TimeoutExpired:
        _log(f"[WARN] 子进程超时（600s），强制终止")
        child.kill()
        child.wait()
    finally:
        # 清理 Playwright 残留进程
        _cleanup_playwright_pids()
        # 清理临时文件
        try:
            batch_file.unlink()
        except Exception:
            pass
        # 清理锁
        _release_lock()

    # ---- 更新进度 ----
    next_idx = (current + 1) % len(BATCHES)
    _set_progress(next_idx)
    if next_idx == 0:
        _log("轮回完成，重置到第1批")

    # ---- 等够10分钟 ----
    elapsed = time.time() - start_time
    if elapsed < BATCH_DELAY_SECONDS:
        sleep = BATCH_DELAY_SECONDS - elapsed
        _log(f"等 {sleep:.0f}s 到下一轮...")
        time.sleep(sleep)

    _log("本次完毕")


if __name__ == "__main__":
    main()