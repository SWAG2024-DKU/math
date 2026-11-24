from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.problems.generation_rule_registry import get_rule
from app.problems.problem_type_extractor import extract_from_directory
from app.problems.template_builder import build_template
from scripts.problems.common.generation_rule_validator import (
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
    """기존 템플릿 또는 격리된 선형대수 후보 템플릿을 생성한다.

    --candidate-rule-catalog 사용 시 전역/캐시 registry를 절대 읽지 않는다.
    후보 저장소는 기존 data/problem_templates와 겹칠 수 없다.
    """
    import hashlib

    parser = argparse.ArgumentParser(
        description="Concept + Generation Rule -> 검수용 ProblemTemplate"
    )
    parser.add_argument("--concept-dir", type=Path, default=DEFAULT_CONCEPT_DIR)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--subject", type=str, default=None)
    parser.add_argument("--ready-only", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--candidate-rule-catalog", type=Path,
                        help="Part 4에서 생성한 후보 GenerationRuleCatalog JSON (선형대수 전용)")
    parser.add_argument("--policy-version", type=str,
                        help="후보 생성 정책 식별자 (manifest 기록)")
    parser.add_argument("--seed", type=int, default=17,
                        help="재현성 감사용 seed (Template 생성 자체는 랜덤 샘플링하지 않음)")
    args = parser.parse_args()
    candidate = args.candidate_rule_catalog is not None
    if not candidate and args.policy_version:
        parser.error("--policy-version은 --candidate-rule-catalog와 함께 사용하세요.")
    if candidate and args.subject not in (None, "linear_algebra"):
        parser.error("후보 Rule은 --subject linear_algebra만 지원합니다.")
    if candidate and args.ready_only:
        parser.error("확장 후보는 검수 전 draft이므로 --ready-only를 사용할 수 없습니다.")
    if candidate and args.output_dir is None:
        parser.error("후보 모드에서는 --output-dir을 명시해야 합니다.")

    def resolve(path: Path) -> Path:
        return (path if path.is_absolute() else PROJECT_ROOT / path).resolve()

    concept_dir = resolve(args.concept_dir)
    output_dir = resolve(args.output_dir or DEFAULT_OUTPUT_DIR)
    if candidate:
        old_templates = resolve(DEFAULT_OUTPUT_DIR)
        original_rules = resolve(PROJECT_ROOT / "data" / "generation_rules")
        # 원본 또는 그 내부/상위 경로를 지정하면 자식 파일을 덮어쓸 위험이 있다.
        for original in (old_templates, original_rules):
            if output_dir == original or output_dir in original.parents or original in output_dir.parents:
                parser.error("후보 출력 경로는 원본 data 디렉터리와 분리해야 합니다.")
        if output_dir.exists() and any(output_dir.iterdir()):
            parser.error("후보 output-dir은 비어 있어야 합니다. 실행마다 새 디렉터리를 지정하세요.")

    candidate_catalog = None
    candidates: dict[tuple[str, str], object] = {}
    input_sha256 = None
    rule_catalog_path = None
    if candidate:
        from app.schemas.generation_rule import GenerationRuleCatalog
        rule_catalog_path = resolve(args.candidate_rule_catalog)
        if not rule_catalog_path.is_file():
            parser.error(f"후보 Rule 파일이 없습니다: {rule_catalog_path}")
        catalog_bytes = rule_catalog_path.read_bytes()
        candidate_catalog = GenerationRuleCatalog.model_validate_json(catalog_bytes)
        if candidate_catalog.subject_id != "linear_algebra":
            parser.error("후보 Rule catalog의 subject_id는 linear_algebra여야 합니다.")
        for rule in candidate_catalog.rules:
            key = (rule.subject_id, rule.problem_type)
            if key in candidates:
                raise ValueError(f"후보 카탈로그 중복 문제 유형: {key}")
            candidates[key] = rule
        input_sha256 = hashlib.sha256(catalog_bytes).hexdigest()

    items = extract_from_directory(concept_dir)
    subject_filter = "linear_algebra" if candidate else args.subject
    if subject_filter:
        items = [x for x in items if x.subject_id == subject_filter]
    if not items:
        raise SystemExit("생성 대상 Problem Type이 없습니다.")

    counts = Counter()
    generated_files: list[str] = []
    records: list[dict[str, object]] = []
    checked_rules: set[tuple[str, str]] = set()
    blocked_rules: dict[tuple[str, str], str] = {}
    used_rule_keys: set[tuple[str, str]] = set()

    for item in items:
        key = (item.subject_id, item.problem_type)
        record: dict[str, object] = {
            "subject_id": item.subject_id,
            "unit_id": item.unit_id,
            "concept_id": item.concept_id,
            "problem_type": item.problem_type,
        }
        records.append(record)
        try:
            rule = candidates.get(key) if candidate else get_rule(*key)
            if rule is None:
                raise KeyError(f"후보 Rule 없음: {key}")
            used_rule_keys.add(key)
            record["generation_rule_id"] = rule.rule_id

            # 다른 과목의 기존 명시적 계약/제외 로직 보존.
            if not candidate and item.subject_id == "probability_statistics":
                from scripts.problems.probability_statistics.probability_statistics_rule_profiles import MARKER, is_supported_pair
                if MARKER in (rule.notes or "") and not is_supported_pair(item.concept_id, item.problem_type):
                    counts["excluded_contract_pairs"] += 1
                    record.update(status="excluded", reason="supported_pair 계약 외")
                    continue

            if key in blocked_rules:
                raise ValueError(blocked_rules[key])
            if key not in checked_rules:
                try:
                    issues = ensure_generation_rule_valid(rule)
                except GenerationRuleValidationError as exc:
                    blocked_rules[key] = str(exc)
                    counts["blocked_by_rule_validation"] += 1
                    raise
                counts["rule_warnings"] += sum(issue.severity == "warning" for issue in issues)
                checked_rules.add(key)
            template = build_template(item, rule, candidate_mode=True) if candidate else build_template(item, rule)
            record["template_id"] = template.template_id
            record["template_status"] = template.status
            record["executable"] = template.executable
            counts[template.status] += 1
            if args.ready_only and template.status != "ready":
                counts["skipped_draft"] += 1
                record.update(status="skipped", reason="ready-only 조건 미충족")
                continue

            relative = Path(item.subject_id) / item.unit_id / safe_filename(
                f"{item.concept_id}__{item.problem_type}.json"
            )
            target = output_dir / relative
            if target.exists() and not args.overwrite:
                counts["skipped_existing"] += 1
                record.update(status="skipped", reason="기존 파일 존재", template_file=str(relative))
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(template.model_dump_json(indent=2), encoding="utf-8")
            generated_files.append(relative.as_posix())
            record.update(status="saved", template_file=relative.as_posix())
            counts["saved"] += 1
        except Exception as exc:
            counts["failed"] += 1
            record.update(status="failed", error_type=type(exc).__name__, error=str(exc))
            print(f"[FAIL] {item.subject_id} / {item.concept_id} / {item.problem_type}: {exc}")

    if candidate:
        for key in sorted(set(candidates) - used_rule_keys):
            counts["unused_candidate_rules"] += 1
            records.append({
                "subject_id": key[0], "problem_type": key[1],
                "status": "excluded", "reason": "Concept 대상에 없는 후보 Rule",
            })

    manifest = {
        "schema_version": "1.1.0" if candidate else "1.0.0",
        "object_type": "problem_template_manifest",
        "candidate": candidate,
        "purpose": "temporary_human_review" if candidate else "template_generation",
        "publishable": False if candidate else None,
        "subject_filter": subject_filter,
        "ready_only": args.ready_only,
        "source_rule_catalog": str(rule_catalog_path) if candidate else "default_registry",
        "source_rule_catalog_sha256": input_sha256,
        "policy_version": args.policy_version,
        "seed": args.seed,
        "counts": dict(counts),
        "generated_files": generated_files,
        "records": records,
        "failed_items": [r for r in records if r.get("status") == "failed"],
        "skipped_items": [r for r in records if r.get("status") in {"excluded", "skipped"}],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_name = f"manifest_{safe_filename(subject_filter)}.json" if subject_filter else "manifest.json"
    (output_dir / manifest_name).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"[DONE] 대상={len(items)} 저장={counts['saved']} 실패={counts['failed']} "
          f"제외={counts['excluded_contract_pairs'] + counts['unused_candidate_rules']} "
          f"출력={output_dir / manifest_name}")
    if counts["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
