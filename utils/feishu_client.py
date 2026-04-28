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


def _get_tenant_token() -> str:
    """获取 tenant_access_token（环境变量优先，fallback 到 secrets.json）"""
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
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.load(resp)
            return result.get("tenant_access_token", "")
    except Exception:
        return ""


# ─── 读取已写入的 note_id（幂等用）────────────────────────


def load_existing_note_ids() -> set[str]:
    """获取飞书表格中已存在的所有 note_id（避免重复写入）"""
    token = os.environ.get("FEISHU_TOKEN", "") or _get_tenant_token()
    if not token:
        return set()

    existing_ids: set[str] = set()
    app_token = config.FEISHU_APP_TOKEN
    table_id = config.FEISHU_TABLE_ID
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records?page_size=500"

    try:
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {token}"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.load(resp)
            records = result.get("data", {}).get("items", [])
            for rec in records:
                fields = rec.get("fields", {})
                note_id = fields.get("笔记ID", "")
                if note_id:
                    existing_ids.add(note_id)
    except Exception:
        pass

    return existing_ids


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


def _to_url(val: str) -> dict:
    """URL 字符串 → 飞书 URL 字段格式"""
    if not val:
        return {"link": "", "text": ""}
    return {"link": val, "text": val}


def _build_fields(note_id: str, row: dict) -> dict:
    """将 row dict 映射为飞书字段（跟 v1 兼容）"""
    content = row.get("content", "")
    if len(content) > 500:
        content = content[:500] + "..."

    tags = row.get("tags", "")
    if isinstance(tags, list):
        tags = ",".join(tags)

    cover_image = row.get("cover_image", "")

    return {
        "笔记ID": note_id,
        "标题": row.get("title", ""),
        "链接": _to_url(row.get("note_url", "")),
        "正文摘要": content,
        "作者": row.get("author", ""),
        "点赞": int(row.get("likes", 0)) or 0,
        "收藏": int(row.get("collects", 0)) or 0,
        "评论数": int(row.get("comments", 0)) or 0,
        "笔记时间": _to_timestamp_ms(row.get("published_at", "")),
        "笔记类型": row.get("type", ""),
        "标签": tags,
        "封面图": cover_image,
        "通过原因": row.get("reasons", ""),
        "关键词": row.get("keyword", ""),
        "采集时间": row.get("collected_at", ""),
        "发布时间": row.get("published_at", ""),
    }


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


def batch_write(rows: list[dict], existing_ids: set[str] | None = None) -> tuple[int, int, int]:
    """
    批量写入飞书（幂等：跳过已存在的 note_id）。

    返回 (written, skipped, failed)。
    """
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