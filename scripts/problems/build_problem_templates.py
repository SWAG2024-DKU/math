from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.problems.generation_rule_registry import get_rule
from app.problems.problem_type_extractor import extract_from_directory
from app.problems.template_builder import build_template
from scripts.problems.generation_rule_validator import (
    GenerationRuleValidationError,
    ensure_generation_rule_valid,
)


DEFAULT_CONCEPT_DIR = PROJECT_ROOT / "data" / "concepts"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "problem_templates"


def safe_filename(value: str) -> str:
    value = re.sub(r"[^0-9A-Za-z._-]+", "_", value)
    return value.strip("._")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Concept + Problem Type + Generation Rule로 ProblemTemplate JSON을 생성합니다."
    )
    parser.add_argument(
        "--concept-dir",
        type=Path,
        default=DEFAULT_CONCEPT_DIR,
        help="Concept JSON 루트 디렉터리",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="ProblemTemplate 저장 루트 디렉터리",
    )
    parser.add_argument(
        "--subject",
        type=str,
        default=None,
        help="특정 subject_id만 생성 (예: linear_algebra)",
    )
    parser.add_argument(
        "--ready-only",
        action="store_true",
        help="ready Template만 저장하고 draft_auto 기반 Template은 건너뜁니다.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="동일한 출력 파일이 있으면 덮어씁니다.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    concept_dir = args.concept_dir
    if not concept_dir.is_absolute():
        concept_dir = PROJECT_ROOT / concept_dir

    output_dir = args.output_dir
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir

    items = extract_from_directory(concept_dir)

    if args.subject:
        items = [
            item
            for item in items
            if item.subject_id == args.subject
        ]

    if not items:
        raise SystemExit("생성 대상 Problem Type이 없습니다.")

    counts = Counter()
    generated_files: list[str] = []
    checked_rules: set[tuple[str, str]] = set()
    blocked_rules: dict[tuple[str, str], str] = {}

    for item in items:
        try:
            rule = get_rule(item.subject_id, item.problem_type)
            rule_key = (item.subject_id, item.problem_type)
            if rule_key in blocked_rules:
                counts["blocked_by_rule_validation"] += 1
                raise ValueError(blocked_rules[rule_key])

            if rule_key not in checked_rules:
                try:
                    # 검증기의 상태별 강도를 그대로 사용한다.
                    # error는 차단하고 draft_auto 등의 warning은 초안 생성을 허용한다.
                    issues = ensure_generation_rule_valid(rule)
                except GenerationRuleValidationError as exc:
                    blocked_rules[rule_key] = str(exc)
                    counts["blocked_by_rule_validation"] += 1
                    raise
                checked_rules.add(rule_key)
                warnings = [issue for issue in issues if issue.severity == "warning"]
                counts["rule_warnings"] += len(warnings)
                if warnings:
                    print(
                        f"[WARN] {rule.rule_id}: 정적 검사 경고 {len(warnings)}건 "
                        "(오류가 아니므로 생성은 계속합니다.)"
                    )
            template = build_template(item, rule)
        except Exception as exc:
            counts["failed"] += 1
            print(
                f"[FAIL] {item.subject_id} / {item.concept_id} / "
                f"{item.problem_type}: {exc}"
            )
            continue

        counts[template.status] += 1

        if args.ready_only and template.status != "ready":
            counts["skipped_draft"] += 1
            continue

        target_dir = (
            output_dir
            / item.subject_id
            / item.unit_id
        )
        target_dir.mkdir(parents=True, exist_ok=True)

        filename = safe_filename(
            f"{item.concept_id}__{item.problem_type}.json"
        )
        target = target_dir / filename

        if target.exists() and not args.overwrite:
            counts["skipped_existing"] += 1
            continue

        target.write_text(
            template.model_dump_json(indent=2),
            encoding="utf-8",
        )
        generated_files.append(str(target.relative_to(output_dir)))
        counts["saved"] += 1

    manifest = {
        "schema_version": "1.0.0",
        "object_type": "problem_template_manifest",
        "subject_filter": args.subject,
        "ready_only": args.ready_only,
        "counts": dict(counts),
        "generated_files": generated_files,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_name = (
        f"manifest_{safe_filename(args.subject)}.json"
        if args.subject
        else "manifest.json"
    )
    (output_dir / manifest_name).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\n=== ProblemTemplate 생성 결과 ===")
    print(f"대상: {len(items)}")
    print(f"ready: {counts['ready']}")
    print(f"draft: {counts['draft']}")
    print(f"저장: {counts['saved']}")
    print(f"기존 파일 건너뜀: {counts['skipped_existing']}")
    print(f"draft 건너뜀: {counts['skipped_draft']}")
    print(f"실패: {counts['failed']}")
    print(f"정적 검사로 차단된 대상: {counts['blocked_by_rule_validation']}")
    print(f"정적 오류 Rule 수: {len(blocked_rules)}")
    print(f"Rule 정적 검사 경고: {counts['rule_warnings']}")
    if counts["blocked_by_rule_validation"]:
        print("[주의] 차단된 대상의 기존 JSON은 자동 삭제하지 않습니다.")
    print(f"출력 디렉터리: {output_dir}")

    if counts["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
