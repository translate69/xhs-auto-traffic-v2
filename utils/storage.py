"""
storage.py - 数据持久化

包含：
  - RecentStorage: 笔记去重（原有逻辑）
  - CollectedStorage: 中间文件存储（runs/ 结构）
"""
from __future__ import annotations

import json
import re
import time as _time
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock

import config


# ──────────────────────────────────────────────────────────
# RecentStorage（原有，去重逻辑不变）
# ──────────────────────────────────────────────────────────


class RecentStorage:
    """笔记去重器。启动时读取已有记录，构建 note_id set"""

    def __init__(self, filepath: Path | str | None = None):
        self._filepath = Path(filepath or (config.DATA_DIR / "collected_note_ids.jsonl"))
        self._seen: set[str] = set()
        self._count: int = 0
        self._lock = Lock()
        self._load()

    def _load(self):
        if not self._filepath.exists():
            return
        try:
            with open(self._filepath, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        note_id = entry.get("note_id")
                        if note_id:
                            self._seen.add(note_id)
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass

    def is_recent(self, note_id: str) -> bool:
        return note_id in self._seen

    def mark_seen(self, note_id: str):
        with self._lock:
            was_new = note_id not in self._seen
            self._seen.add(note_id)
            if was_new:
                try:
                    self._filepath.parent.mkdir(parents=True, exist_ok=True)
                    with open(self._filepath, "a", encoding="utf-8") as f:
                        entry = {"note_id": note_id, "collected_at": datetime.now().isoformat()}
                        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                except Exception:
                    pass
                self._count += 1
                if self._count % 20 == 0:
                    self._cleanup()

    def _cleanup(self, force: bool = False):
        if not self._filepath.exists():
            return
        cleanup_marker = self._filepath.parent / "_last_cleanup_timestamp"
        if not force and cleanup_marker.exists():
            try:
                last_ts = float(cleanup_marker.read_text(encoding="utf-8").strip())
                if _time.time() - last_ts < 6 * 3600:
                    return
            except Exception:
                pass

        cutoff = datetime.now() - timedelta(days=config.RECENT_DAYS)
        keep: list[str] = []
        try:
            with open(self._filepath, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        collected_at = entry.get("collected_at", "")
                        if collected_at:
                            dt = datetime.fromisoformat(collected_at)
                            if dt >= cutoff:
                                keep.append(line)
                    except (json.JSONDecodeError, ValueError):
                        continue
            with open(self._filepath, "w", encoding="utf-8") as f:
                for line in keep:
                    f.write(line + "\n")
            cleanup_marker.write_text(str(_time.time()), encoding="utf-8")
        except Exception:
            pass

    def __len__(self) -> int:
        return len(self._seen)


# ──────────────────────────────────────────────────────────
# CollectedStorage（新增，中间文件）
# ──────────────────────────────────────────────────────────


def _sanitize_filename(keyword: str) -> str:
    """将关键词转为安全的文件名（去除 Windows 非法字符）"""
    keyword = keyword.strip()
    # 替换 Windows 文件名非法字符为空格（空格再压缩为单个）
    keyword = re.sub(r'[/\\:*?"<>|]', ' ', keyword)
    keyword = re.sub(r'\s+', '_', keyword.strip())
    return keyword or "unknown"


class CollectedStorage:
    """
    中间文件存储（runs/ 结构）。

    文件结构：
      data/collected/runs/{date}_{time}_{keyword}.jsonl
      data/collected_manifest.jsonl

    存储时机：enrichment 完成后立即写入，支持断点恢复。
    清理策略：runs/ 下超过 30 天的文件每月删除一次。
    """

    MANIFEST_FILE = config.DATA_DIR / "collected_manifest.jsonl"
    RUNS_DIR = config.DATA_DIR / "collected" / "runs"

    def __init__(self):
        self._lock = Lock()
        self._ensure_dirs()

    def _ensure_dirs(self):
        self.RUNS_DIR.mkdir(parents=True, exist_ok=True)

    # ── run_id 生成 ───────────────────────────────────────

    def make_run_id(self, keyword: str) -> str:
        """生成 run_id: {date}_{time}_{keyword}"""
        now = datetime.now()
        ts = now.strftime("%Y-%m-%d_%H%M%S")
        safe_kw = _sanitize_filename(keyword)
        return f"{ts}_{safe_kw}"

    # ── 路径解析 ──────────────────────────────────────────

    def _run_id_to_path(self, run_id: str) -> Path:
        """
        从 run_id 提取日期和关键词，映射到实际文件路径。
        run_id 格式: {date}_{time}_{keyword}  →  文件名: {date}_{keyword}.jsonl
        多词关键词用 _ 连接，所以从第3段开始拼回关键词。
        """
        parts = run_id.split("_")
        date = parts[0]  # e.g. "2026-04-29"
        keyword = "_".join(parts[2:])  # e.g. "汕尾海边民宿推荐"
        return self.RUNS_DIR / f"{date}_{keyword}.jsonl"

    def run_file_path(self, run_id: str) -> Path:
        return self._run_id_to_path(run_id)

    def manifest_path(self) -> Path:
        return Path(self.MANIFEST_FILE)

    # ── 写入 NoteDetail 列表 ─────────────────────────────

    def save(self, run_id: str, keyword: str, details: list) -> Path:
        """
        将 NoteDetail 列表追加到 runs/ 下的文件（同一天同一关键词只对应一个文件）。
        返回文件路径。
        """
        path = self.run_file_path(run_id)
        path.parent.mkdir(parents=True, exist_ok=True)

        with self._lock:
            with open(path, "a", encoding="utf-8") as f:
                for detail in details:
                    # 兼容 NoteDetail dataclass 和 dict
                    if hasattr(detail, "__dict__"):
                        # dataclass → 提取所有字段
                        row = {
                            "url": detail.url or "",
                            "xsec_token": detail.xsec_token or "",
                            "author": detail.author or "",
                            "time_text": detail.time_text or "",
                            "title": detail.title or "",
                            "content": detail.content or "",
                            "images": detail.images or [],
                            "tags": detail.tags or [],
                            "likes": detail.likes or 0,
                            "collects": detail.collects or 0,
                            "comments": detail.comments or 0,
                            "published_at": detail.published_at or "",
                            "author_id": getattr(detail, "author_id", "") or "",
                            "keyword": keyword,
                            "collected_at": datetime.now().isoformat(),
                            "run_id": run_id,
                        }
                    else:
                        row = detail  # 已经是 dict
                        row["run_id"] = run_id  # 确保有 run_id 标识
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")

        return path

    # ── 读取（断点恢复用）────────────────────────────────

    def load(self, run_id: str) -> list[dict]:
        """
        读取指定 run_id 的中间文件，返回 list[dict]。
        文件可能包含多个 run 的数据（同一天同一关键词追加），
        只返回当前 run_id 的记录。
        """
        path = self.run_file_path(run_id)
        if not path.exists():
            return []

        records = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if rec.get("run_id") == run_id:
                        records.append(rec)
                except json.JSONDecodeError:
                    continue
        return records

    def exists(self, run_id: str) -> bool:
        """检查 run_id 文件是否已存在"""
        return self.run_file_path(run_id).exists()

    # ── manifest 追加 ───────────────────────────────────

    def append_manifest(self, run_id: str, keyword: str, note_count: int):
        """追加一行 manifest 记录"""
        entry = {
            "keyword": keyword,
            "run_id": run_id,
            "note_count": note_count,
            "completed_at": datetime.now().isoformat(),
        }
        with self._lock:
            self.manifest_path().parent.mkdir(parents=True, exist_ok=True)
            with open(self.manifest_path(), "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def read_manifest(self) -> list[dict]:
        """读取全部 manifest 记录"""
        path = self.manifest_path()
        if not path.exists():
            return []
        records = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return records

    # ── 清理（每月一次）────────────────────────────────

    def clean_old(self, days: int = 30) -> list[Path]:
        """
        删除 runs/ 下早于指定天数的文件。
        返回被删除的文件路径列表。
        """
        if not self.RUNS_DIR.exists():
            return []

        cutoff = datetime.now() - timedelta(days=days)
        deleted: list[Path] = []

        for f in self.RUNS_DIR.iterdir():
            if not f.is_file() or f.suffix != ".jsonl":
                continue
            # 文件名格式: {date}_{time}_{keyword}.jsonl
            # 从文件名提取日期部分
            name = f.stem  # 不含扩展名
            date_part = name.split("_")[0] if name else ""
            try:
                file_date = datetime.strptime(date_part, "%Y-%m-%d")
                if file_date < cutoff:
                    f.unlink(missing_ok=True)
                    deleted.append(f)
            except ValueError:
                # 日期解析失败，跳过
                continue

        # 同步清理 manifest（删除超过 30 天的 run 条目）
        self._clean_manifest(days)

        return deleted

    def _clean_manifest(self, days: int = 30):
        """清理 manifest 中超过天数的条目"""
        path = self.manifest_path()
        if not path.exists():
            return

        cutoff = datetime.now() - timedelta(days=days)
        keep: list[str] = []

        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        completed_at = entry.get("completed_at", "")
                        if completed_at:
                            dt = datetime.fromisoformat(completed_at)
                            if dt >= cutoff:
                                keep.append(line)
                    except (json.JSONDecodeError, ValueError):
                        continue
            with open(path, "w", encoding="utf-8") as f:
                for line in keep:
                    f.write(line + "\n")
        except Exception:
            pass