"""
feishu_client.py - 飞书 API 客户端

直接从 v1 write_feishu.py 迁移，调整 table_id 为 v2 专用表。
"""
from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime
from pathlib import Path

import config

# ─── 凭证获取 ────────────────────────────────────────────────


_token_cache: str = ""
_token_cache_time: float = 0.0
_TOKEN_CACHE_TTL: float = 60.0  # token 有效期 60s，复用同一 token


def _get_tenant_token() -> str:
    """获取 tenant_access_token（带进程内缓存，60s 内复用）"""
    global _token_cache, _token_cache_time
    import time as _time

    # 缓存有效期内直接返回
    if _token_cache and (_time.time() - _token_cache_time) < _TOKEN_CACHE_TTL:
        return _token_cache

    app_id = os.environ.get("FEISHU_APP_ID", "")
    app_secret = os.environ.get("FEISHU_APP_SECRET", "")

    if not app_id or not app_secret:
        secret_file = Path(__file__).parent.parent / "secrets.json"
        if secret_file.exists():
            try:
                secrets = json.loads(secret_file.read_text(encoding="utf-8"))
                app_id = app_id or secrets.get("feishu_app_id", "")
                app_secret = app_secret or secrets.get("feishu_app_secret", "")
            except Exception:
                pass

    if not app_id or not app_secret:
        return ""

    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            result = json.load(resp)
            token = result.get("tenant_access_token", "")
            if token:
                _token_cache = token
                _token_cache_time = _time.time()
            return token
    except Exception:
        return ""


# ─── 读取已写入的 note_id（幂等用）────────────────────────


def load_existing_note_ids() -> set[str]:
    """获取飞书表格中已存在的所有 note_id（幂等去重用）"""
    records = _load_all_records_raw()
    ids = set()
    for rec in records:
        fields = rec.get("fields", {})
        note_id = fields.get("笔记ID", "")
        if note_id:
            ids.add(note_id)
    return ids


def load_all_records() -> list[dict]:
    """
    读取表格全部记录（自动翻页），返回 dict 列表。
    每条记录包含所有字段。
    """
    records = _load_all_records_raw()
    results = []
    for rec in records:
        fields = rec.get("fields", {})
        results.append({
            "record_id": rec.get("record_id", ""),
            "note_id": fields.get("笔记ID", ""),
            "title": fields.get("标题", ""),
            "note_url": _extract_url(fields.get("链接")),
            "content": fields.get("正文内容", ""),
            "author": fields.get("作者", ""),
            "likes": fields.get("点赞", 0),
            "collects": fields.get("收藏", 0),
            "comments": fields.get("评论数", 0),
            "published_at": _parse_timestamp_ms(fields.get("笔记时间")),
            "time_text": fields.get("展示时间", ""),
            "type": fields.get("类型", ""),
            "tags": fields.get("标签", ""),
            "reasons": fields.get("筛选原因", ""),
            "keyword": fields.get("采集关键词", ""),
            "cover_image": _extract_url(fields.get("封面图")),
        })
    return results


def check_note_exists(note_id: str) -> tuple[bool, str]:
    """
    查询指定 note_id 是否已存在于表格。
    返回 (exists, record_id)。若不存在 record_id 为空字符串。
    """
    records = _load_all_records_raw()
    for rec in records:
        fields = rec.get("fields", {})
        if fields.get("笔记ID", "") == note_id:
            return True, rec.get("record_id", "")
    return False, ""


def delete_record(record_id: str) -> bool:
    """
    根据 record_id 删除表格中的一条记录。
    返回 True 删除成功，False 失败。
    """
    token = os.environ.get("FEISHU_TOKEN", "") or _get_tenant_token()
    if not token:
        print("[Feishu] 无有效 token")
        return False

    app_token = config.FEISHU_APP_TOKEN
    table_id = config.FEISHU_TABLE_ID
    url = (f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}"
           f"/tables/{table_id}/records/{record_id}")

    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"},
        method="DELETE",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.load(resp)
            return result.get("code") == 0
    except Exception as e:
        print(f"[Feishu] 删除失败 {record_id}: {e}")
        return False


def update_record_fields(record_id: str, fields: dict) -> bool:
    """
    根据 record_id 更新记录的指定字段。
    返回 True 成功，False 失败。
    """
    token = os.environ.get("FEISHU_TOKEN", "") or _get_tenant_token()
    if not token:
        return False
    app_token = config.FEISHU_APP_TOKEN
    table_id = config.FEISHU_TABLE_ID
    url = (f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}"
           f"/tables/{table_id}/records/{record_id}")
    payload = json.dumps({"fields": fields}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="PUT",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.load(resp).get("code") == 0
    except Exception:
        return False


def mark_notified(note_ids: list[str]) -> tuple[int, int]:
    """
    批量将指定 note_id 对应的记录标记为已通知（勾选"已通知"字段）。
    返回 (updated, failed)。
    """
    updated = 0
    failed = 0
    for nid in note_ids:
        exists, record_id = check_note_exists(nid)
        if not exists or not record_id:
            failed += 1
            continue
        if update_record_fields(record_id, {"已通知": True}):
            updated += 1
        else:
            failed += 1
    return updated, failed


def batch_delete_note_ids(note_ids: list[str]) -> tuple[int, int]:
    """
    批量删除指定 note_id 对应的记录。
    返回 (deleted, failed)。
    """
    deleted = 0
    failed = 0
    for nid in note_ids:
        exists, record_id = check_note_exists(nid)
        if not exists or not record_id:
            print(f"[Feishu] [{nid}] 不存在，跳过")
            failed += 1
            continue
        if delete_record(record_id):
            print(f"[Feishu] [{nid}] 删除成功")
            deleted += 1
        else:
            print(f"[Feishu] [{nid}] 删除失败")
            failed += 1
    print(f"[Feishu] 批量删除完成: 删除 {deleted}，失败 {failed}")
    return deleted, failed


# ─── 内部辅助 ────────────────────────────────────────────────


def _load_all_records_raw() -> list[dict]:
    """读取表格所有记录（自动翻页），返回 raw items 列表"""
    token = os.environ.get("FEISHU_TOKEN", "") or _get_tenant_token()
    if not token:
        return []

    app_token = config.FEISHU_APP_TOKEN
    table_id = config.FEISHU_TABLE_ID
    base_url = (f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}"
                f"/tables/{table_id}/records")

    all_records: list[dict] = []
    page_token = ""

    while True:
        url = f"{base_url}?page_size=500"
        if page_token:
            url += f"&page_token={page_token}"

        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {token}"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.load(resp)
                items = result.get("data", {}).get("items", [])
                all_records.extend(items)
                has_more = result.get("data", {}).get("has_more", False)
                page_token = result.get("data", {}).get("page_token", "")
                if not has_more or not page_token:
                    break
        except Exception:
            break

    return all_records


def _extract_url(field_val) -> str:
    """从飞书 URL 字段格式中提取链接字符串"""
    if not field_val:
        return ""
    if isinstance(field_val, str):
        return field_val
    if isinstance(field_val, dict):
        return field_val.get("link", "")
    return ""


def _parse_timestamp_ms(ts_ms) -> str:
    """毫秒时间戳 → YYYY-MM-DD 字符串"""
    if not ts_ms:
        return ""
    try:
        return datetime.fromtimestamp(int(ts_ms) / 1000).strftime("%Y-%m-%d")
    except Exception:
        return ""


# ─── 单条写入 ────────────────────────────────────────────────


def _to_timestamp_ms(val: str) -> int | None:
    """ISO 8601 日期字符串 → 毫秒时间戳"""
    if not val:
        return None
    try:
        dt = datetime.fromisoformat(val.replace("Z", "+00:00").split(".")[0])
        return int(dt.timestamp() * 1000)
    except Exception:
        return None


def _to_url(val: str) -> dict | None:
    """URL 字符串 → 飞书 URL 字段格式，空时返回 None 跳过该字段"""
    if not val:
        return None
    return {"link": val, "text": val}


def _build_fields(note_id: str, row: dict) -> dict:
    """将 row dict 映射为飞书字段（跟 v1 兼容）"""
    content = row.get("content", "")
    pass  # no truncation

    tags = row.get("tags", "")
    if isinstance(tags, list):
        tags = ",".join(tags)

    cover_image = row.get("cover_image", "")

    from datetime import datetime
    now_ms = int(datetime.now().timestamp() * 1000)

    fields = {
        "笔记ID": note_id,
        "标题": row.get("title", ""),
        "链接": _to_url(row.get("note_url", "")),
        "正文内容": content,
        "作者": row.get("author", ""),
        "点赞": int(row.get("likes", 0)) or 0,
        "收藏": int(row.get("collects", 0)) or 0,
        "评论数": int(row.get("comments", 0)) or 0,
        "笔记时间": _to_timestamp_ms(row.get("published_at", "")),
        "展示时间": row.get("time_text", ""),
        "类型": row.get("type", ""),
        "标签": tags,
        "筛选原因": row.get("reasons", ""),
        "采集关键词": row.get("keyword", ""),
        "采集时间": now_ms,
    }

    # 封面图有值才加（URL 字段不能为空对象）
    if cover_image:
        fields["封面图"] = _to_url(cover_image)

    return fields


def write_single_record(note_id: str, row: dict) -> bool:
    """
    写入单条记录到飞书 Bitable。
    返回 True 写入成功，False 失败或已存在。
    """
    token = os.environ.get("FEISHU_TOKEN", "") or _get_tenant_token()
    if not token:
        print("[Feishu] 无有效 token，跳过写入")
        return False

    app_token = config.FEISHU_APP_TOKEN
    table_id = config.FEISHU_TABLE_ID
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"

    fields = _build_fields(note_id, row)
    payload = json.dumps({"fields": fields}, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.load(resp)
            if result.get("data", {}).get("record"):
                return True
            code = result.get("code")
            if code == 99991663:
                return False  # 已存在
            return False
    except Exception:
        return False


def batch_write(rows: list[dict] | dict, existing_ids: set[str] | None = None) -> tuple[int, int, int]:
    """
    批量写入飞书（幂等：跳过已存在的 note_id）。
    支持单个 dict 或 list[dict]。

    返回 (written, skipped, failed)。
    """
    # 兼容单个 dict 输入
    if isinstance(rows, dict):
        rows = [rows]

    if existing_ids is None:
        existing_ids = load_existing_note_ids()

    print(f"[Feishu] 当前表格已有 {len(existing_ids)} 条记录")

    written = 0
    skipped = 0
    failed = 0

    for row in rows:
        note_id = row.get("note_id", "")
        if not note_id:
            # 从 URL 提取
            import re
            m = re.search(r"search_result/([a-fA-F0-9]+)", row.get("url", ""), re.IGNORECASE)
            if m:
                note_id = m.group(1)
            else:
                failed += 1
                continue

        if note_id in existing_ids:
            skipped += 1
            print(f"[Feishu] [{note_id}] 已存在，跳过")
            continue

        ok = write_single_record(note_id, row)
        if ok:
            written += 1
            existing_ids.add(note_id)
            print(f"[Feishu] [{note_id}] 写入成功: {row.get('title', '')[:30]}")
        else:
            failed += 1
            print(f"[Feishu] [{note_id}] 写入失败")

    print(f"[Feishu] 完成: 写入 {written}，跳过 {skipped}，失败 {failed}")
    return written, skipped, failed