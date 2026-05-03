"""
pipeline_debug.py - 精准定位 SIGKILL 位置的日志工具（独立版）

使用方法：
    import sys; sys.path.insert(0, '.'); from _pipeline_debug import log_stage, install_debug_log; install_debug_log(__file__)

    在关键位置调用：
        log_stage("启动浏览器")
        log_stage("创建上下文")
        log_stage("注入Cookie")
        log_stage("打开页面")
        log_stage("滚动加载")
        log_stage("提取数据")
        log_stage(f"处理笔记: {note_id}")
        log_stage("关闭Page")
        log_stage("Pipeline完成")

flush=True  强制刷到磁盘，kill 前最后一行动态能保留
"""
from __future__ import annotations

import os
import sys
import time as _time
from datetime import datetime

_log_fp = None
_log_enabled = False
_log_path = ""


def _log_path_for(caller_file: str) -> str:
    """日志路径：与 caller 脚本同目录"""
    base = os.path.splitext(caller_file)[0]
    return base + "_debug.log"


def install_debug_log(caller_file: str = ""):
    """在脚本启动时调用，安装日志系统"""
    global _log_fp, _log_enabled, _log_path

    if not caller_file:
        caller_file = sys.argv[0] if sys.argv else "pipeline"

    _log_path = _log_path_for(caller_file)
    _log_enabled = True

    # 每次运行清空旧日志
    try:
        _log_fp = open(_log_path, "w", encoding="utf-8", buffering=1)
        _log_fp.write(f"[{_now()}] [START] log_path={_log_path}\n")
        _log_fp.flush()
    except Exception as e:
        print(f"[WARN] debug log init failed: {e}", flush=True)
        _log_enabled = False


def log_stage(stage: str, flush: bool = True):
    """
    打印带时间戳的阶段日志。
    flush=True  → 强制刷到磁盘（kill 前最后一行动态可见）
    """
    ts = _now()
    line = f"[{ts}] {stage}\n"

    # 1. 打印到 stdout（用户在控制台能看到）
    print(line, end="", flush=True)

    # 2. 写入日志文件
    if _log_enabled and _log_fp:
        try:
            _log_fp.write(line)
            if flush:
                _log_fp.flush()
                os.fsync(_log_fp.fileno())  # 关键：确保 kill 前数据落盘
        except Exception:
            pass


def _now() -> str:
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


# ─── 自动插桩 ─────────────────────────────────────────

def instrument_file(filepath: str) -> str:
    """
    扫描文件，在关键阶段自动插入 log_stage()。
    返回修改后的代码内容（不直接覆盖文件）。
    """
    with open(filepath, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    # 关键模式 → 阶段名
    patterns = [
        ("playwright.chromium.launch",             "启动浏览器"),
        ("new_context",                           "创建上下文"),
        ("add_cookies",                           "注入Cookie"),
        ("page.goto",                             "打开页面(开始)"),
        ("wait_for_selector",                     "等待页面元素"),
        ("scroll",                                "滚动加载"),
        ("_extract_feeds",                         "提取Feeds数据"),
        ("_extract_detail",                        "提取笔记详情"),
        ("page.close",                            "关闭Page"),
        ("browser.close",                         "关闭浏览器"),
        ("return feeds",                          "返回结果"),
        ("CollectedStorage",                       "初始化存储"),
    ]

    result = []
    for i, line in enumerate(lines):
        result.append(line)
        for pattern, stage_name in patterns:
            if pattern in line:
                # 找缩进
                indent = " " * max(0, len(line) - len(line.lstrip()))
                result.append(f"{indent}log_stage(\"[{os.path.basename(filepath)}] {stage_name}\")\n")
                break

    return "".join(result)


if __name__ == "__main__":
    import glob
    # 扫描同目录下的主要脚本
    targets = ["run_all.py", "core/search_collector.py", "core/note_detail.py"]
    for t in targets:
        if os.path.exists(t):
            patched = instrument_file(t)
            print(f"\n{'='*60}")
            print(f"文件: {t}")
            print(f"{'='*60}")
            # 找插入点
            for i, line in enumerate(patched.split("\n")):
                if "log_stage" in line:
                    print(f"  line {i+1}: {line.rstrip()}")
