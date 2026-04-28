"""
storage.py - 去重存储

来自原 recent_collector.py，逻辑 1:1 迁移。
格式：data/collected_note_ids.jsonl
"""
from __future__ import annotations

import json
import time as _time
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock

import config


class RecentStorage:
    """
    笔记去重器。

    · 启动时读取已有记录，构建 note_id set
    · is_recent() 检查是否在最近 N 天内采过
    · mark_seen() 追加新记录
    · 每 20 条增量清理过期数据（超过 7 天的旧记录）
    """

    def __init__(self, filepath: Path | str | None = None):
        self._filepath = Path(filepath or (config.DATA_DIR / "collected_note_ids.jsonl"))
        self._seen: set[str] = set()
        self._count: int = 0
        self._lock = Lock()
        self._load()

    def _load(self):
        """启动时读取，构建 note_id set"""
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
        """检查 note_id 是否在最近 7 天内已采过"""
        return note_id in self._seen

    def mark_seen(self, note_id: str):
        """记录 note_id 已采集（追加到文件）"""
        with self._lock:
            was_new = note_id not in self._seen
            self._seen.add(note_id)

            if was_new:
                try:
                    self._filepath.parent.mkdir(parents=True, exist_ok=True)
                    with open(self._filepath, "a", encoding="utf-8") as f:
                        entry = {
                            "note_id": note_id,
                            "collected_at": datetime.now().isoformat(),
                        }
                        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                except Exception:
                    pass

                self._count += 1
                if self._count % 20 == 0:
                    self._cleanup()

    def _cleanup(self, force: bool = False):
        """清理超过 7 天的旧记录"""
        if not self._filepath.exists():
            return

        # 每 6 小时最多清理一次
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
