"""실패 유형 5개와 기본행렬 문제의 Rule을 재실행 가능한 방식으로 보정한다.

프로젝트 루트에서 실행:
    python -m scripts.problems.migrate_linear_algebra_runtime_rules \
        --input data/generation_rules/linear_algebra.json \
        --output data/generation_rules/linear_algebra.json

같은 경로를 쓰면 변경 전 JSON을 .before-runtime-v3.bak으로 백업한다.
Template JSON을 직접 수정하지 않는다. 변경 후 Template/Preview를 재생성한다.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any


TARGET_TYPES = frozenset({
    "algebraic_expansion_verification", "matrix_to_vector_equation",
    "gram_schmidt_orthogonalization", "qr_factorization_calculation",
    "quadratic_form_transformation", "elementary_inverse_calculation",
})


def repair_rule(rule: dict[str, Any]) -> bool:
    """알고 있는 선형대수 Rule만 보정하고 이미 보정된 값은 그대로 유지."""
    kind = rule.get("problem_type")
    if kind not in TARGET_TYPES or rule.get("subject_id") != "linear_algebra":
        return False
    before = json.dumps(rule, sort_keys=True, ensure_ascii=False)
    construction = rule["construction"]
    parameters = rule["parameter_spec"]

    if kind == "algebraic_expansion_verification":
        construction["text_templates"] = [
            "두 행렬에 대해 (A+B)^2를 AB와 BA의 순서를 구별하여 전개한 뒤 계산하시오.\n"
            "A = {{ A }}, B = {{ B }}"
        ]
    elif kind == "matrix_to_vector_equation":
        rule.setdefault("symbol_spec", {})["x"] = {
            "role": "unknown", "dimension": "A.cols",
            "assumptions": {"real": True},
            "description": "A의 열 개수와 같은 길이의 미지수 열벡터",
        }
        required = construction.setdefault("required_objects", [])
        if "x" not in required:
            required.append("x")
    elif kind == "gram_schmidt_orthogonalization":
        parameters["V"]["generator"] = "orthogonal_integer_norm_columns"
    elif kind == "qr_factorization_calculation":
        parameters["A"]["generator"] = "orthogonal_integer_norm_columns"
    elif kind == "quadratic_form_transformation":
        parameters["A"]["generator"] = "small_integer_spectrum_symmetric"
    elif kind == "elementary_inverse_calculation":
        parameters["E"]["generator"] = "elementary_matrix"

    return json.dumps(rule, sort_keys=True, ensure_ascii=False) != before


def migrate(input_file: Path, output_file: Path) -> list[str]:
    catalog = json.loads(input_file.read_text(encoding="utf-8"))
    if catalog.get("subject_id") != "linear_algebra" or not isinstance(catalog.get("rules"), list):
        raise ValueError("선형대수 GenerationRuleCatalog JSON이 필요합니다.")
    seen: set[str] = set()
    changed: list[str] = []
    for rule in catalog["rules"]:
        kind = rule.get("problem_type")
        if kind not in TARGET_TYPES:
            continue
        if kind in seen:
            raise ValueError(f"중복 problem_type: {kind}")
        seen.add(kind)
        if repair_rule(rule):
            changed.append(kind)
    if seen != TARGET_TYPES:
        raise ValueError(f"대상 Rule이 빠졌습니다: {sorted(TARGET_TYPES - seen)}")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    if input_file.resolve() == output_file.resolve() and changed:
        backup = output_file.with_suffix(output_file.suffix + ".before-runtime-v3.bak")
        if not backup.exists():
            shutil.copy2(input_file, backup)
    if changed or input_file.resolve() != output_file.resolve():
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=output_file.parent,
                                         suffix=".tmp", delete=False) as temporary:
            json.dump(catalog, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
            temp_path = Path(temporary.name)
        os.replace(temp_path, output_file)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="선형대수 Rule 실행 오류 보정")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    changed = migrate(args.input, args.output)
    print(f"수정 {len(changed)}개: {', '.join(changed) if changed else '없음 (이미 반영됨)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
