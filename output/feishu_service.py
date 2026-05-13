"""
feishu_service.py - 飞书输出服务

v2 专用飞书写入：
- 写入目标：v2 专用 Bitable 表（tblvxlFAqO5hP4fD）
- 幂等写入：先查 note_id 是否已存在，跳过重复
- 凭证：环境变量 FEISHU_APP_ID / FEISHU_APP_SECRET 或 secrets.json
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import config
from core.note_detail import NoteDetail

from utils.feishu_client import (
    batch_write,
    load_existing_note_ids,
    load_all_records,
    _load_all_records_raw,
    check_note_exists,
    delete_record,
    batch_delete_note_ids,
    mark_notified,
)


class FeishuOutputService:
    """
    飞书输出服务（v2 专用）。

    使用：
        svc = FeishuOutputService()
        svc.write(note_details)   # 传入 NoteDetail 列表
    """

    def __init__(self):
        self.input_path = config.FEISHU_DIR / "filtered_for_feishu.jsonl"

    def write(self, records: list[NoteDetail | dict], keyword: str = ""):
        """
        写入飞书 Bitable（幂等：跳过已存在的 note_id）。
        records 可以是 NoteDetail 对象列表（来自 FilterService），
        也可以是 dict 列表（直接读文件时的格式）。
        """
        # 转换 NoteDetail → dict
        rows = []
        for item in records:
            if isinstance(item, NoteDetail):
                # 注入 keyword（每条笔记可以不同，这里统一用同一个）
                if not getattr(item, "keyword", ""):
                    item.keyword = keyword
                row = self._note_detail_to_row(item)
            else:
                row = dict(item)
                if keyword and not row.get("keyword"):
                    row["keyword"] = keyword
            rows.append(row)

        print(f"[FeishuOutput] 待写入 {len(rows)} 条")

        # 同时写 JSONL 文件（供调试 / 备用）
        self._write_jsonl(rows)

        # 调用飞书 API 写入
        written, skipped, failed = batch_write(rows)

        print(f"[FeishuOutput] 写入完成: 写入 {written}，跳过 {skipped}，失败 {failed}")

    def _note_detail_to_row(self, detail: NoteDetail) -> dict:
        """NoteDetail → 飞书字段格式 dict"""
        # ── 构建 note_id ─────────────────────────────
        note_id = detail.note_id  # 优先用 property

        # ── 构建 note_url ────────────────────────────
        if detail.url and detail.xsec_token:
            m = re.search(r"search_result/([a-fA-F0-9]+)", detail.url, re.IGNORECASE)
            if m:
                note_url = (
                    f"https://www.xiaohongshu.com/explore/{m.group(1)}"
                    f"?xsec_token={detail.xsec_token}&xsec_source=pc_search"
                )
            else:
                note_url = detail.url
        elif detail.url:
            note_url = detail.url
        else:
            note_url = ""

        # ── 标题 ────────────────────────────────────
        if detail.title:
            title = detail.title[:50]
        elif detail.content:
            title = detail.content[:50]
        else:
            title = ""

        # ── filter_result ──────────────────────────
        fr = detail.filter_result
        type_str = fr.note_type if fr else ""
        # MultiSelect 字段需要列表格式
        note_type_list = [t.strip() for t in type_str.split(",") if t.strip()] if type_str else []
        reasons_str = fr.reasons if fr else ""

        return {
            "title": title,
            "note_url": note_url,
            "note_id": note_id,
            "type": note_type_list,
            "content": detail.content if detail.content else "",
            "author": detail.author or "",
            "likes": detail.likes or 0,
            "collects": detail.collects or 0,
            "comments": detail.comments or 0,
            "published_at": detail.published_at or "",
            "time_text": detail.time_text or "",
            "cover_image": detail.images[0] if detail.images else "",
            "tags": ",".join(detail.tags) if detail.tags else "",
            "keyword": getattr(detail, "keyword", "") or "",
            "collected_at": getattr(detail, "collected_at", "") or "",
            "reasons": reasons_str,
        }

    def _write_jsonl(self, rows: list[dict]):
        """写 jsonl 文件（备用）"""
        config.FEISHU_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.input_path, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def load_from_file(self) -> list[dict]:
        """读取已过滤的文件（供单独触发飞书写入时使用）"""
        if not self.input_path.exists():
            return []

        records = []
        with open(self.input_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        return records

    def read_all_from_feishu(self) -> list[dict]:
        """
        从飞书表格读取所有记录。
        返回每条记录的 dict（含 note_id / title / content / author 等关键字段）。
        """
        records = load_all_records()
        print(f"[FeishuOutput] 从表格读取到 {len(records)} 条记录")
        return records

    def check_note_in_feishu(self, note_id: str) -> tuple[bool, str]:
        """
        查询指定 note_id 是否已在飞书表格中。
        返回 (exists, record_id)。
        """
        return check_note_exists(note_id)

    def delete_note(self, note_id: str) -> bool:
        """
        删除飞书表格中指定 note_id 的一条记录。
        先查 record_id 再删除。返回是否成功。
        """
        exists, record_id = check_note_exists(note_id)
        if not exists or not record_id:
            print(f"[FeishuOutput] [{note_id}] 不存在于表格")
            return False
        ok = delete_record(record_id)
        if ok:
            print(f"[FeishuOutput] [{note_id}] 删除成功")
        else:
            print(f"[FeishuOutput] [{note_id}] 删除失败")
        return ok

    def delete_notes(self, note_ids: list[str]) -> tuple[int, int]:
        """
        批量删除指定 note_id 列表对应的记录。
        返回 (deleted, failed)。
        """
        return batch_delete_note_ids(note_ids)

    def get_notified_note_ids(self) -> set[str]:
        """
        返回当前表格中已勾选"已通知"的 note_id 集合。
        """
        raw_records = _load_all_records_raw()
        notified = set()
        for raw in raw_records:
            fields = raw.get("fields", {})
            nid = fields.get("笔记ID", "")
            if nid and fields.get("已通知"):
                notified.add(nid)
        return notified

    def mark_notified(self, note_ids: list[str]) -> tuple[int, int]:
        """
        批量标记指定 note_id 为已通知。
        返回 (updated, failed)。
        """
        return mark_notified(note_ids)

    def get_unnotified_records(self) -> list[dict]:
        """
        返回所有"已通知"未勾选的记录原始字典（含 fields）。
        用于通知模块查询孤儿笔记。
        """
        notified_ids = self.get_notified_note_ids()
        raw_records = _load_all_records_raw()
        return [
            r for r in raw_records
            if r.get("fields", {}).get("笔记ID") not in notified_ids
            and r.get("fields", {}).get("笔记ID")
        ]
