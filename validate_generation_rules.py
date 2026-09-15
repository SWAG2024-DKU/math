from __future__ import annotations

from collections import Counter

from app.problems.problem_type_extractor import extract_from_directory
from app.problems.generation_rule_registry import has_rule, list_rules


def main() -> None:
    items = extract_from_directory("data/concepts")

    missing: list[tuple[str, str]] = []

    for item in items:
        if not has_rule(item.subject_id, item.problem_type):
            missing.append((item.subject_id, item.problem_type))

    rules = list_rules()
    status_counts = Counter(rule.status for rule in rules)

    print(f"Concept에서 추출된 Problem Type 항목: {len(items)}")
    print(f"Generation Rule 수(subject/problem_type): {len(rules)}")
    print(f"Rule 상태: {dict(status_counts)}")
    print(f"누락 Rule: {len(set(missing))}")

    if missing:
        for subject_id, problem_type in sorted(set(missing)):
            print(f"[MISSING] {subject_id} / {problem_type}")
        raise SystemExit(1)

    print("전체 Problem Type에 Generation Rule이 등록되어 있습니다.")


if __name__ == "__main__":
    main()
