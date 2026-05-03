"""
回归测试：每次改 filter 规则前跑一遍
确保历史上误判的笔记仍然被正确拒绝

用法：
    python test/regression_test.py
"""
import sys
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from filter.filter_service import FilterService
from core.note_detail import NoteDetail


def load_problem_notes():
    path = ROOT / "test" / "corpus" / "problem_notes.json"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run_regression():
    notes = load_problem_notes()
    if not notes:
        print("问题笔记库为空，跳过回归测试")
        return True

    svc = FilterService()
    all_pass = True

    print(f"回归测试：{len(notes)} 条问题笔记\n")

    for item in notes:
        note = NoteDetail(
            title=item.get("title", ""),
            content=item["content"],
            url="https://www.xiaohongshu.com/explore/" + item["note_id"],
            xsec_token="",
            published_at="2026-04-28",
        )
        result = svc.filter_one(note)
        expected = item.get("expected", False)

        status = "✅" if result.passed == expected else "❌"
        if result.passed != expected:
            all_pass = False

        print(f"{status} [{item['note_id'][:8]}] expected={expected} got={result.passed}")
        print(f"   原因: {item['reason']}")
        print(f"   结果: {result.reasons}\n")

    if all_pass:
        print("✅ 回归测试全部通过")
    else:
        print("❌ 回归测试有退化！请检查规则变更")

    return all_pass


if __name__ == "__main__":
    success = run_regression()
    sys.exit(0 if success else 1)
