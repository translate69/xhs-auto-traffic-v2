"""
_verify_filter.py - 筛选验证脚本

用法：
    python _verify_filter.py                              # 验证最新跑的结果
    python _verify_filter.py --run-id 2026-04-30_xxxxxx  # 验证指定 run
    python _verify_filter.py --list                       # 列出所有 run
"""
import argparse
import json
import re
import sys
sys.path.insert(0, r'E:\translate\claw\xhs-auto-traffic-v2')
sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
from filter.filter_service import FilterService, has_signal, ASK_SIGNALS, TRIP_QUESTION_SIGNALS, URGENT_SIGNALS
from core.note_detail import NoteDetail

PROJECT_ROOT = Path(r'E:\translate\claw\xhs-auto-traffic-v2')
RUN_DIR = PROJECT_ROOT / "data" / "collected" / "runs"
svc = FilterService()

TAG_PATTERN = re.compile(r'#\S+')

# ─── 信号解释 ──────────────────────────────────────────────


def _strip_tags(text: str) -> str:
    return TAG_PATTERN.sub('', text)


def _explain_signal(text: str, signal_list: list[str], label: str) -> str | None:
    """
    检查 text 中是否有 signal_list 里的信号词，返回触发词和位置。
    返回格式：「触发词:位置:前后文」
    """
    text_lower = text.lower()
    for sig in signal_list:
        idx = text_lower.find(sig.lower())
        if idx == -1:
            continue
        # 获取前后文（各5字）
        pre = text[max(0, idx - 5):idx]
        post = text[idx + len(sig):idx + len(sig) + 5]
        return f"「{sig}」位置[{idx}] 前={repr(pre)} 后={repr(post)}"
    return None


def _is_negated(text: str, sig: str) -> str | None:
    """
    检测信号词是否被否定。
    返回 None = 未被否定，返回字符串 = 否定原因说明
    """
    text_lower = text.lower()
    sig_lower = sig.lower()
    idx = text_lower.find(sig_lower)
    if idx == -1:
        return None

    # 前缀否定（向前看2字）
    NEG_SINGLE = ["不", "没", "别", "莫", "勿", "未", "否", "休", "甭"]
    NEG_PHRASE = ["不想", "不要", "不是", "不含", "没兴趣", "不考虑", "不去", "不知道",
                  "不了解", "不清楚", "不确定", "没吃过", "没尝过"]

    if idx >= 2:
        pre = text_lower[max(0, idx - 2):idx]
        if pre and pre[-1] in NEG_SINGLE:
            return f"前有单字否定「{pre[-1]}」"
        for n in NEG_PHRASE:
            if n in pre:
                return f"前有否定短语「{n}」"

    # 后缀否定（信号词后紧跟否定字）
    after_pos = idx + len(sig)
    if after_pos < len(text_lower):
        after_char = text_lower[after_pos]
        if after_char in NEG_SINGLE:
            return f"后有否定「{after_char}」（{text[after_pos:after_pos+3]}）"
        # 完整否定短语
        after_window = text_lower[after_pos:after_pos + 4]
        for n in ["不重要", "无所谓", "没关系", "不在意", "不关心", "不去"]:
            if n in after_window:
                return f"后有否定短语「{n}」"

    return None


def _is_self_talk(text: str, sig: str) -> str | None:
    """
    检测信号词是否出现在自言自语语境中（如「我要想想有什么可以打包」）。
    返回 None = 非自言自语，返回字符串 = 可疑原因说明
    """
    # 强信号不视为自言自语
    STRONG_SIGS = ["求", "想问", "请问", "帮我", "帮帮我", "求指教", "求推荐", "求带", "求攻略"]
    if sig in STRONG_SIGS:
        return None

    text_lower = text.lower()
    sig_lower = sig.lower()
    idx = text_lower.find(sig_lower)
    if idx == -1:
        return None

    # 前缀是这些词 → 自言自语
    SELF_TALK_PRE = ["想想", "想一想", "看看有没有", "看看有什么",
                     "想想有", "想知道", "想知道有"]
    for pre_phrase in SELF_TALK_PRE:
        pre_start = max(0, idx - len(pre_phrase))
        if text_lower[pre_start:idx] == pre_phrase:
            return f"前有自言自语前缀「{pre_phrase}」"

    # 「有什么/有没有」后面是这些词 → 自言自语
    if sig in ["有什么", "有没有"]:
        after_pos = idx + len(sig)
        if after_pos < len(text_lower):
            after_2 = text_lower[after_pos:after_pos+2]
            if after_2 in ["可以", "要", "能", "的"]:
                return f"「{sig}」+「{after_2}」组合，自言自语可能性高"

    return None


def _judge_note(note: NoteDetail) -> tuple[str, str, str]:
    """
    判断笔记是否应该通过。
    返回 (judgment, suspicious_flag, explanation_str)
    - judgment: "通过" | "不通过" | "需复核"
    - suspicious: "可疑" | "正常"
    - explanation: 判断理由
    """
    reasons = note.filter_reasons.split(",") if note.filter_reasons else []
    content_no_tags = _strip_tags(note.content)
    title = note.title or ""

    explanations = []
    suspicious = False
    judgment = "通过"  # 默认通过

    for reason in reasons:
        reason = reason.strip()
        if reason == "ask":
            detail = _explain_signal(content_no_tags, ASK_SIGNALS, "ask")
            if detail:
                sig_match = re.search(r'「(.+?)」', detail)
                sig_word = sig_match.group(1) if sig_match else ""
                negation = _is_negated(content_no_tags, sig_word) if sig_word else None
                self_talk = _is_self_talk(content_no_tags, sig_word) if sig_word else None
                if negation:
                    explanations.append(f"ASK信号「{sig_word}」被否定")
                    suspicious = True
                    judgment = "不通过"
                elif self_talk:
                    explanations.append(f"ASK信号「{sig_word}」疑似自言自语")
                    suspicious = True
                    judgment = "不通过"
                else:
                    explanations.append(f"ASK信号「{sig_word}」有效")
            else:
                title_detail = _explain_signal(title, ASK_SIGNALS, "ask")
                if title_detail:
                    explanations.append(f"标题ASK信号有效")
                else:
                    explanations.append("ASK来源不明确")
                    suspicious = True
                    judgment = "需复核"

        elif reason == "trip_question":
            detail = _explain_signal(content_no_tags, TRIP_QUESTION_SIGNALS, "trip_question")
            if detail:
                sig_match = re.search(r'「(.+?)」', detail)
                sig_word = sig_match.group(1) if sig_match else ""
                negation = _is_negated(content_no_tags, sig_word) if sig_word else None
                if negation:
                    explanations.append(f"出行提问「{sig_word}」被否定")
                    suspicious = True
                    judgment = "不通过"
                else:
                    explanations.append(f"出行提问「{sig_word}」有效")
            else:
                explanations.append("trip_question来源不明确")
                suspicious = True
                judgment = "需复核"

        elif reason == "urgent":
            detail = _explain_signal(content_no_tags, URGENT_SIGNALS, "urgent")
            if detail:
                explanations.append(f"紧急信号有效")
            else:
                explanations.append("urgent来源不明确")
                suspicious = True
                judgment = "需复核"

        elif reason == "weak_desire":
            explanations.append("弱意图+咨询组合，有限通过")

        elif reason == "type_match":
            ad语气 = re.search(r"(宝藏|绝了|封神|太好吃|种草|打卡)", content_no_tags)
            if ad语气:
                # 有广告语气但通过了type_match → 检查内容是否有具体价值
                # 简单判断：内容较长（>50字）且有具体名词（店名/菜名/地点）→ 有价值，通过
                has_specifics = len(content_no_tags) > 50 and re.search(r"[店名菜名地点]", content_no_tags)
                if has_specifics:
                    explanations.append(f"type_match通过，有广告语气但内容有具体价值")
                else:
                    explanations.append(f"type_match通过，但广告语气明显且内容空泛")
                    suspicious = True
                    judgment = "不通过"
            else:
                explanations.append(f"type_match通过（{note.filter_type}）")

    # 如果没有信号（reasons为空）但仍然通过 → 不正常
    if not reasons and note.filter_passed:
        explanations.append("无明确通过信号但通过了")
        suspicious = True
        judgment = "不通过"

    flag = "可疑" if suspicious else "正常"
    return judgment, flag, " | ".join(explanations)


# ─── 数据加载 ──────────────────────────────────────────────


def load_run(run_id: str) -> list[dict]:
    """扫描 runs/*.jsonl，按 run_id 精确匹配；失败则按 keyword 模糊匹配最新文件"""
    files = sorted(RUN_DIR.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)

    # 方法1：精确匹配 run_id（读取完整文件内容）
    for fpath in files:
        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                all_lines = [l.strip() for l in f if l.strip()]
                for line in all_lines:
                    rec = json.loads(line)
                    if rec.get("run_id") == run_id:
                        # 精确匹配成功，返回文件全部内容
                        return [json.loads(l) for l in all_lines]
        except Exception:
            continue

    # 方法2：从 run_id 提取 keyword 部分，按 keyword 找最新文件
    # run_id 格式: "2026-04-30_104845_汕尾去哪吃" → keyword = "汕尾去哪吃"
    parts = run_id.split("_")
    if len(parts) >= 3:
        keyword_from_run_id = "_".join(parts[2:])
        candidates = []
        for fpath in files:
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        rec = json.loads(line.strip())
                        rec_kw = rec.get("keyword", "")
                        rec_rid = rec.get("run_id", "")
                        if rec_kw == keyword_from_run_id and rec_rid:
                            candidates.append((fpath, rec_rid))
            except Exception:
                continue

        if candidates:
            # 取时间戳最新的
            best_fpath, best_rid = max(candidates, key=lambda x: x[1])
            with open(best_fpath, "r", encoding="utf-8", errors="replace") as f:
                records = [json.loads(l) for l in f if l.strip()]
                print(f"[调试] 精确匹配失败，按 keyword={keyword_from_run_id} 模糊匹配到 run_id={best_rid}（{len(records)} 条笔记）")
                return records

    print(f"[警告] run_id={run_id} 未找到数据")
    return []


def records_to_notes(records: list[dict]) -> list[NoteDetail]:
    notes = []
    for rec in records:
        note = NoteDetail(
            url=rec.get("url", ""),
            title=rec.get("title", ""),
            author=rec.get("author", ""),
            content=rec.get("content", ""),
            published_at=rec.get("published_at", ""),
        )
        note.xsec_token = rec.get("xsec_token", "") or ""
        note.time_text = rec.get("time_text", "") or ""
        note.images = rec.get("images", []) or []
        note.tags = rec.get("tags", []) or []
        note.likes = rec.get("likes", 0) or 0
        note.collects = rec.get("collects", 0) or 0
        note.comments = rec.get("comments", 0) or 0
        note.author_id = rec.get("author_id", "") or ""
        note.keyword = rec.get("keyword", "") or ""
        note._stored_passed = rec.get("filter_passed")
        note._stored_reasons = rec.get("filter_reasons", "")
        note.filter_type = rec.get("filter_type", "") or ""
        note.filter_passed = rec.get("filter_passed")
        note.filter_reasons = rec.get("filter_reasons", "") or ""
        notes.append(note)
    return notes


# ─── 核心验证 ──────────────────────────────────────────────


def verify_run(run_id: str) -> dict:
    records = load_run(run_id)
    if not records:
        return {}

    keyword = records[0].get("keyword", "")

    print(f"{'='*60}")
    print(f"验证 run_id: {run_id}")
    print(f"{'='*60}")
    print(f"关键词: {keyword}")
    print(f"笔记总数: {len(records)}")

    # Re-run filter on stored data
    notes = records_to_notes(records)
    fresh_results = svc.filter_all(notes)

    # Update filter_passed/reasons from fresh run
    fresh_map = {n.note_id: n for n in fresh_results}
    for note in notes:
        if note.note_id in fresh_map:
            fr = fresh_map[note.note_id]
            note.filter_passed = fr.filter_passed
            note.filter_reasons = fr.filter_reasons
            note.filter_type = fr.filter_type

    fresh_passed = [n for n in notes if n.filter_passed]
    changed = []

    for note in notes:
        stored = note._stored_passed
        fresh = note.filter_passed
        if stored != fresh:
            changed.append({
                "note_id": note.note_id,
                "title": note.title[:40],
                "stored_passed": stored,
                "fresh_passed": fresh,
                "stored_reasons": note._stored_reasons,
                "fresh_reasons": note.filter_reasons,
            })

    print(f"\n通过筛选的笔记（共 {len(fresh_passed)} 条）：")
    print(f"{'─'*60}")

    confirmed_pass = []   # 最终判断通过的
    auto_rejected = []    # 自动化判断为不通过的
    need_review = []       # 无法自动判断，需复核

    if not fresh_passed:
        print("  （无）")
    else:
        for i, note in enumerate(fresh_passed, 1):
            judgment, flag, explanation = _judge_note(note)
            content_snippet = note.content[:120] if note.content else '(无)'

            if judgment == "通过":
                status = "✅ 通过"
                confirmed_pass.append(note)
            elif judgment == "不通过":
                status = f"❌ 判断不通过（{explanation}）"
                auto_rejected.append((note, explanation))
            else:
                status = f"⚠️ 需复核（{explanation}）"
                need_review.append(note)

            print(f"\n  [{i}] {note.note_id or '(无id)'} {flag} | {status}")
            print(f"      title: {note.title[:50] if note.title else '(无标题)'}")
            print(f"      reasons: {note.filter_reasons}")
            print(f"      content: {content_snippet}...")

    if auto_rejected:
        print(f"\n自动化判断不通过（共 {len(auto_rejected)} 条）：")
        for note, explanation in auto_rejected:
            print(f"  ❌ {note.note_id or '(无id)'} | {note.title[:40] or '(无标题)'} | {explanation}")

    if need_review:
        print(f"\n需人工复核（共 {len(need_review)} 条）：")
        for note in need_review:
            print(f"  ⚠️ {note.note_id or '(无id)'} | {note.title[:40] or '(无标题)'}")

    if changed:
        print(f"\n⚠️  检测到 {len(changed)} 条结果变化：")
        for c in changed:
            print(f"\n  note_id: {c['note_id']}")
            print(f"  title: {c['title']}")
            print(f"  历史: passed={c['stored_passed']}, reasons={c['stored_reasons']}")
            print(f"  当前: passed={c['fresh_passed']}, reasons={c['fresh_reasons']}")

    total = len(records)
    stored_passed = sum(1 for r in records if r.get("filter_passed") is True)
    print(f"\n统计：总笔记={total}，原始通过={stored_passed}，filter通过={len(fresh_passed)}，确认通过={len(confirmed_pass)}，自动拒绝={len(auto_rejected)}，需复核={len(need_review)}，变化={len(changed)}")

    return {
        "run_id": run_id,
        "keyword": keyword,
        "passed_count": len(confirmed_pass),
        "auto_rejected": [n for n, _ in auto_rejected],
        "changed": changed,
        "confirmed_pass": confirmed_pass,
    }


def list_runs():
    files = sorted(RUN_DIR.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)
    entries = []
    seen = {}
    for fpath in files:
        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                first_line = f.readline()
                if first_line:
                    rec = json.loads(first_line.strip())
                    rid = rec.get("run_id", "")
                    if rid and rid not in seen:
                        seen[rid] = True
                        entries.append({
                            "run_id": rid,
                            "keyword": rec.get("keyword", ""),
                            "file": fpath.name,
                        })
                        # Count total
                        f.seek(0)
                        count = sum(1 for line in f if line.strip())
                        entries[-1]["note_count"] = count
        except Exception:
            continue

    entries.sort(key=lambda x: x["run_id"], reverse=True)

    print(f"{'run_id':<40} {'关键词':<20} {'笔记数':>6}")
    print("-" * 70)
    for e in entries[:20]:
        rid = e["run_id"]
        kw = e["keyword"][:18] if e["keyword"] else ""
        nc = e["note_count"]
        print(f"{rid:<40} {kw:<20} {nc:>6}")


# ─── 入口 ──────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="筛选验证脚本")
    parser.add_argument("--run-id", "-r", type=str, help="指定 run_id")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有 run")
    args = parser.parse_args()

    if args.list:
        list_runs()
    elif args.run_id:
        verify_run(args.run_id)
    else:
        manifest_path = PROJECT_ROOT / "data" / "collected_manifest.jsonl"
        if manifest_path.exists():
            with open(manifest_path, "r", encoding="utf-8", errors="replace") as f:
                lines = [l.strip() for l in f if l.strip()]
            if lines:
                last_entry = json.loads(lines[-1])
                latest_run_id = last_entry.get("run_id", "")
                print(f"自动选择最新 run: {latest_run_id}（{last_entry.get('keyword', '')}）\n")
                verify_run(latest_run_id)