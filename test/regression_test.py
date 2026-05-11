"""
回归测试：每次改 filter 规则前跑一遍
确保历史上误判的笔记仍然被正确拒绝（filter + review 双层 gate）

用法：
    python test/regression_test.py
"""
import sys
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from filter.filter_service import FilterService
from filter.review_service import ReviewService
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
    rev = ReviewService()
    all_pass = True

    # 用测试时间：2天前来保证在5天窗口内（不受时间过滤影响）
    test_date = datetime.now(timezone.utc) - timedelta(days=2)
    test_date_str = test_date.strftime("%Y-%m-%d")

    print(f"回归测试：{len(notes)} 条问题笔记（测试时间：{test_date_str}）\n")

    for item in notes:
        note = NoteDetail(
            title=item.get("title", ""),
            content=item["content"],
            url="https://www.xiaohongshu.com/explore/" + item["note_id"],
            xsec_token="",
            published_at=test_date_str,
        )
        note._note_id = item["note_id"]
        result = svc.filter_one(note)

        # 附上 filter_result 让 review 读取
        note.filter_passed = result.passed
        note.filter_reasons = result.reasons
        note._filter_result = result

        # review gate（镜像执行）
        review_result = rev._review_one(note)

        # 最终判定：filter AND review 都要通过才算 pass
        final_pass = result.passed and review_result.passed
        expected = item.get("expected", False)

        status = "✅" if final_pass == expected else "❌"
        if final_pass != expected:
            all_pass = False

        filter_status = "PASS" if result.passed else "REJECT"
        review_status = "PASS" if review_result.passed else "REJECT"

        print(f"{status} [{item['note_id'][:8]}] filter={filter_status} review={review_status} expected={expected}")
        print(f"   原因: {item['reason']}")
        print(f"   filter 结果: {result.reasons}")
        print(f"   review 结果: {review_result.reason}")
        print()

    if all_pass:
        print("✅ 回归测试全部通过")
    else:
        print("❌ 回归测试有退化！请检查规则变更")

    return all_pass


if __name__ == "__main__":
    success = run_regression()
    sys.exit(0 if success else 1)
