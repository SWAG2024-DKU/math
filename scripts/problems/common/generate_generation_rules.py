"""5과목 GenerationRule catalog 생성·동기화 및 보완 Rule 반영.

기존 문제 설계를 보존하고 초안의 누락 메타데이터만 보완한다.
--rule-overrides에는 GenerationRuleCatalog 형식의 JSON을 지정한다.
과목별 실행 엔진·수학 검증기는 별도 구현 대상이며, 이 스크립트의 실행만으로
초안이 실행 가능하거나 검수 완료 상태로 승격되지는 않는다.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.schemas.concept import Concept, ConceptCatalog
from app.schemas.generation_rule import GenerationRule, GenerationRuleCatalog


DEFAULT_CONCEPT_DIR = PROJECT_ROOT / "data" / "concepts"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "generation_rules"

AUTO_NOTE = (
    "Concept generation_profile과 수학 메타데이터에서 자동 생성한 초안. "
    "parameter_spec, answer_spec.expression, construction을 실제 생성 엔진 연결 전에 검토해야 한다."
)

DEFAULT_DIFFICULTY_FACTORS = {
    "parameter_complexity": "파라미터 범위/차원/항의 수를 증가시켜 조절",
    "operation_steps": "필요 계산 단계 수를 증가시켜 조절",
}

SQUARE_MATRIX_KEYWORDS = (
    "determinant",
    "eigen",
    "inverse",
    "diagonal",
    "trace",
    "characteristic",
    "positive_definite",
    "spectral_decomposition",
    "lu_factorization",
)

PARAMETER_LIBRARY: dict[str, dict[str, Any]] = {
    "input": {
        "type": "symbolic_input",
        "description": "해당 problem_type에 필요한 입력값. 세부 샘플러 규칙은 후속 검토 필요",
    },
    "f": {
        "type": "expression",
        "description": "문제 유형에 적합한 단순 함수/수식",
        "allowed_families": [
            "polynomial",
            "rational",
            "exponential",
            "logarithmic",
            "trigonometric",
        ],
    },
    "A": {
        "type": "matrix",
        "description": "문제 유형에 맞는 작은 정수/유리수 행렬",
        "shape": {
            "rows": {"min": 2, "max": 4},
            "cols": {"min": 2, "max": 4},
        },
        "element_type": "integer",
        "element_min": -5,
        "element_max": 5,
    },
    "B": {
        "type": "matrix",
        "description": "A와 연산 가능한 작은 정수/유리수 행렬",
        "shape": {
            "rows": {"min": 2, "max": 4},
            "cols": {"min": 2, "max": 4},
        },
        "element_type": "integer",
        "element_min": -5,
        "element_max": 5,
    },
    "u": {
        "type": "vector",
        "description": "작은 정수 성분을 갖는 벡터",
        "shape": {"dimension": {"min": 2, "max": 3}},
        "element_type": "integer",
        "element_min": -5,
        "element_max": 5,
    },
    "v": {
        "type": "vector",
        "description": "u와 호환되는 차원의 벡터",
        "shape": {"dimension": "u.dimension"},
        "depends_on": ["u"],
        "element_type": "integer",
        "element_min": -5,
        "element_max": 5,
    },
    "equation": {
        "type": "equation",
        "description": "문제 유형에 맞는 미분방정식/변환 문제",
    },
    "data": {
        "type": "numeric_data",
        "description": "통계 문제 유형에 맞는 표본 또는 요약 통계량",
        "shape": {"size": {"min": 3, "max": 30}},
    },
}

SYMBOL_LIBRARY: dict[str, dict[str, Any]] = {
    "x": {
        "role": "independent_variable",
        "description": "주 독립변수",
    },
    "t": {
        "role": "independent_variable",
        "description": "시간 또는 주 독립변수",
    },
    "n": {
        "role": "index",
        "assumptions": {"integer": True, "nonnegative": True},
        "description": "수열·급수의 인덱스",
    },
}


class GenerationRuleBuildError(RuntimeError):
    pass


def _unique(items: Iterable[Any]) -> list[Any]:
    result: list[Any] = []
    for item in items:
        if item not in result:
            result.append(item)
    return result


def _resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def _load_concept_groups(
    concept_dir: Path,
    *,
    subject_filter: str | None = None,
) -> dict[tuple[str, str], list[Concept]]:
    """Concept JSON을 검증하고 (subject_id, problem_type)별로 묶는다."""

    groups: dict[tuple[str, str], list[Concept]] = defaultdict(list)

    files = sorted(concept_dir.rglob("*.json"))
    if not files:
        raise GenerationRuleBuildError(
            f"Concept JSON을 찾을 수 없습니다: {concept_dir}"
        )

    for path in files:
        with path.open("r", encoding="utf-8") as file:
            raw = json.load(file)

        catalog = ConceptCatalog.model_validate(raw)
        subject_id = catalog.subject.subject_id

        if subject_filter and subject_id != subject_filter:
            continue

        for concept in catalog.concepts:
            profile = concept.generation_profile
            if not profile.enabled:
                continue

            for problem_type in profile.supported_problem_types:
                groups[(subject_id, problem_type)].append(concept)

    return groups


def _normalize_legacy_constraint_encoding(rule: GenerationRule) -> GenerationRule:
    """JSON object가 문자열로 이중 저장된 기존 Constraint만 안전하게 변환한다."""

    data = rule.model_dump(mode="python", exclude_unset=True)
    changed = False

    for constraint in data.get("constraints", []):
        expression = constraint.get("expression")
        if not isinstance(expression, str):
            continue

        try:
            decoded = json.loads(expression)
        except json.JSONDecodeError:
            continue

        if not isinstance(decoded, dict):
            continue
        if not {"constraint_id", "rule"}.issubset(decoded):
            continue

        constraint["expression"] = decoded
        changed = True

    return GenerationRule.model_validate(data) if changed else rule


def _load_existing_rules(
    rule_dir: Path,
) -> dict[tuple[str, str], GenerationRule]:
    """현재 Rule catalog을 읽는다. 기존 curated/reviewed Rule 보존에 사용한다."""

    existing: dict[tuple[str, str], GenerationRule] = {}

    if not rule_dir.exists():
        return existing

    for path in sorted(rule_dir.glob("*.json")):
        if path.name == "manifest.json":
            continue

        with path.open("r", encoding="utf-8") as file:
            raw = json.load(file)

        catalog = GenerationRuleCatalog.model_validate(raw)
        if catalog.rule_count != len(catalog.rules):
            raise GenerationRuleBuildError(
                f"rule_count 불일치: {path} "
                f"({catalog.rule_count} != {len(catalog.rules)})"
            )

        for rule in catalog.rules:
            key = (rule.subject_id, rule.problem_type)
            if key in existing:
                raise GenerationRuleBuildError(
                    "중복 Generation Rule이 있습니다: "
                    f"{rule.subject_id} / {rule.problem_type}"
                )
            existing[key] = rule

    return existing


def _aggregate_metadata(concepts: list[Concept]) -> dict[str, Any]:
    if not concepts:
        raise GenerationRuleBuildError("빈 Concept 그룹입니다.")

    source_concept_ids = sorted({concept.concept_id for concept in concepts})
    source_formula_ids = sorted(
        {
            formula.formula_id
            for concept in concepts
            for formula in concept.formulas
            if formula.formula_id
        }
    )
    supported_answer_types = sorted(
        {
            answer_type
            for concept in concepts
            for answer_type in concept.generation_profile.supported_answer_types
        }
    )
    validators = sorted(
        {
            validator
            for concept in concepts
            for validator in concept.generation_profile.recommended_validators
        }
    )

    semantic_structure = _unique(
        objective.description
        for concept in concepts
        for objective in concept.learning_objectives
        if objective.description
    )[:4]

    constraints: list[dict[str, Any]] = []
    seen_conditions: set[str] = set()
    for concept in concepts:
        for condition in concept.application_conditions:
            rule = condition.rule
            condition_key = json.dumps(
                {
                    "left": rule.property,
                    "operator": rule.operator,
                    "right": rule.value,
                    "description": condition.description,
                },
                ensure_ascii=False,
                sort_keys=True,
                default=str,
            )
            if condition_key in seen_conditions:
                continue

            seen_conditions.add(condition_key)
            item = {
                "type": "concept_application_condition",
                "expression": {
                    "constraint_id": (
                        f"auto.{concept.concept_id}.{len(constraints) + 1}"
                    ),
                    "scope": "generation",
                    "description": condition.description,
                    "rule": {
                        "left": rule.property,
                        "operator": rule.operator,
                        "right": rule.value,
                    },
                    "on_failure": "resample",
                },
                "required": True,
                "description": condition.description,
            }
            constraints.append(item)
            if len(constraints) >= 12:
                break
        if len(constraints) >= 12:
            break

    difficulty_min = min(
        concept.generation_profile.difficulty_range.min
        for concept in concepts
    )
    difficulty_max = max(
        concept.generation_profile.difficulty_range.max
        for concept in concepts
    )

    return {
        "source_concept_ids": source_concept_ids,
        "source_formula_ids": source_formula_ids,
        "supported_answer_types": supported_answer_types,
        "validators": validators,
        "semantic_structure": semantic_structure,
        "constraints": constraints,
        "difficulty_min": difficulty_min,
        "difficulty_max": difficulty_max,
    }


def _fallback_parameter_names(subject_id: str, problem_type: str) -> list[str]:
    """
    신규 problem_type용 보수적 추론.

    기존 Rule이 있으면 그 parameter_spec을 그대로 보존한다. 이 함수는
    아직 Rule이 전혀 없는 신규 problem_type에만 사용되며, 자동 초안은
    executable=False / manual_review_required=True로 생성된다.
    """

    text = problem_type.lower()

    if subject_id == "probability_statistics":
        return ["data"]

    matrix_keywords = (
        "matrix",
        "eigen",
        "determinant",
        "rank",
        "svd",
        "pseudoinverse",
        "decomposition",
    )
    vector_keywords = (
        "vector",
        "dot_product",
        "cross_product",
        "projection",
        "orthogonality",
        "normal_line",
        "surface_normal",
    )
    vector_pair_keywords = (
        "dot_product",
        "cross_product",
        "projection",
        "orthogonality",
        "angle",
        "area_via_cross_product",
    )
    equation_keywords = (
        "ode",
        "pde",
        "differential_equation",
        "laplace",
        "boundary_condition",
    )
    function_keywords = (
        "derivative",
        "differentiation",
        "integral",
        "limit",
        "series",
        "optimization",
        "function",
        "extrema",
    )

    names: list[str] = []

    if any(keyword in text for keyword in matrix_keywords):
        names.append("A")
        if "matrix_multiplication" in text:
            names.append("B")

    if any(keyword in text for keyword in vector_keywords):
        names.append("u")
        if any(keyword in text for keyword in vector_pair_keywords):
            names.append("v")

    if any(keyword in text for keyword in function_keywords):
        names.append("f")

    if any(keyword in text for keyword in equation_keywords):
        names.append("equation")

    return _unique(names) or ["input"]


def _fallback_parameter_spec(subject_id: str, problem_type: str) -> dict[str, Any]:
    # TODO[LA-D001] _fallback_parameter_spec 구현
    # 1. 신규 초안의 기본값과 기존 curated/reviewed 규칙 갱신을 구분한다.
    # 2. PARAMETER_LIBRARY 변경만으로 기존 규칙이 갱신된다고 처리하지 않는다.
    raise NotImplementedError("TODO[LA-D001]: _fallback_parameter_spec")


def _fallback_symbol_spec(subject_id: str, problem_type: str) -> dict[str, Any]:
    """신규 초안에 필요한 비샘플링 수학 기호를 보수적으로 선언한다."""

    text = problem_type.lower()
    symbols: dict[str, Any] = {}

    function_keywords = (
        "derivative",
        "differentiation",
        "integral",
        "limit",
        "series",
        "optimization",
        "function",
        "extrema",
    )
    if any(keyword in text for keyword in function_keywords):
        symbols["x"] = copy.deepcopy(SYMBOL_LIBRARY["x"])

    if any(keyword in text for keyword in ("ode", "laplace", "time", "motion")):
        symbols["t"] = copy.deepcopy(SYMBOL_LIBRARY["t"])

    if "series" in text or "sequence" in text:
        symbols["n"] = copy.deepcopy(SYMBOL_LIBRARY["n"])

    return symbols


def _legacy_range_to_shape(
    spec: dict[str, Any],
    minimum_key: str,
    maximum_key: str,
) -> int | dict[str, int] | None:
    minimum = spec.get(minimum_key)
    maximum = spec.get(maximum_key)
    if not isinstance(minimum, int) or not isinstance(maximum, int):
        return None

    spec.pop(minimum_key, None)
    spec.pop(maximum_key, None)
    if minimum == maximum:
        return minimum
    return {"min": minimum, "max": maximum}


def _migrate_draft_structure(
    data: dict[str, Any],
    *,
    subject_id: str,
    problem_type: str,
) -> None:
    """draft_auto의 기존 평면형 파라미터를 신규 Schema로 자동 변환한다."""

    parameters = data.setdefault("parameter_spec", {})
    symbols = data.setdefault("symbol_spec", {})
    moved_symbols: set[str] = set()

    for name, spec in list(parameters.items()):
        if spec.get("type") == "symbol":
            fallback = copy.deepcopy(
                SYMBOL_LIBRARY.get(
                    name,
                    {
                        "role": "independent_variable",
                        "description": spec.get("description"),
                    },
                )
            )
            symbols.setdefault(name, fallback)
            parameters.pop(name)
            moved_symbols.add(name)
            continue

        if spec.get("shape") is not None:
            continue

        if spec.get("type") == "matrix":
            rows = _legacy_range_to_shape(spec, "rows_min", "rows_max")
            cols = _legacy_range_to_shape(spec, "cols_min", "cols_max")
            shape = {
                key: value
                for key, value in (("rows", rows), ("cols", cols))
                if value is not None
            }
            if shape:
                spec["shape"] = shape
        elif spec.get("type") == "vector":
            dimension = _legacy_range_to_shape(
                spec,
                "dimension_min",
                "dimension_max",
            )
            if dimension is not None:
                spec["shape"] = {"dimension": dimension}
        elif spec.get("type") == "numeric_data":
            size = _legacy_range_to_shape(spec, "size_min", "size_max")
            if size is not None:
                spec["shape"] = {"size": size}

    required_objects = data.get("construction", {}).get("required_objects", [])
    if moved_symbols:
        data["construction"]["required_objects"] = [
            name for name in required_objects if name not in moved_symbols
        ]

    fallback_symbols = _fallback_symbol_spec(subject_id, problem_type)
    for name, spec in fallback_symbols.items():
        if name not in parameters:
            symbols.setdefault(name, spec)

    text = problem_type.lower()
    if "A" in parameters and any(
        keyword in text for keyword in SQUARE_MATRIX_KEYWORDS
    ):
        if parameters["A"].get("shape") is None:
            parameters["A"]["shape"] = {}
        shape = parameters["A"]["shape"]
        if shape.get("rows") is not None:
            shape.setdefault("cols", "A.rows")

    if "A" in parameters and "B" in parameters and "matrix_multiplication" in text:
        if parameters["B"].get("shape") is None:
            parameters["B"]["shape"] = {}
        shape = parameters["B"]["shape"]
        shape.setdefault("rows", "A.cols")
        if shape.get("rows") == "A.cols":
            parameters["B"]["depends_on"] = _unique(
                [*parameters["B"].get("depends_on", []), "A"]
            )

    if "u" in parameters and "v" in parameters:
        if parameters["v"].get("shape") is None:
            parameters["v"]["shape"] = {}
        shape = parameters["v"]["shape"]
        shape.setdefault("dimension", "u.dimension")
        if shape.get("dimension") == "u.dimension":
            parameters["v"]["depends_on"] = _unique(
                [*parameters["v"].get("depends_on", []), "u"]
            )


def _ensure_linear_algebra_matrix_multiplication_shape(
    data: dict[str, Any],
) -> None:
    """기존 curated Rule에도 AB의 행렬 크기 관계를 채운다.

    A의 이미 검수한 크기와 B의 열 크기는 유지한다. B.rows만 A.cols에
    연결하며, 명시적인 의존관계도 기록한다. 재실행해도 같은 결과가 나온다.
    """

    if (data.get("subject_id"), data.get("problem_type")) != (
        "linear_algebra", "matrix_multiplication"
    ):
        return

    parameters = data.get("parameter_spec", {})
    left, right = parameters.get("A"), parameters.get("B")
    if not isinstance(left, dict) or not isinstance(right, dict):
        raise GenerationRuleBuildError(
            "linear_algebra/matrix_multiplication: A와 B 파라미터가 필요합니다."
        )
    if left.get("type") != "matrix" or right.get("type") != "matrix":
        raise GenerationRuleBuildError(
            "linear_algebra/matrix_multiplication: A와 B는 행렬이어야 합니다."
        )

    left_shape = left.setdefault("shape", {})
    right_shape = right.setdefault("shape", {})
    if not isinstance(left_shape, dict) or not isinstance(right_shape, dict):
        raise GenerationRuleBuildError(
            "linear_algebra/matrix_multiplication: shape는 객체여야 합니다."
        )
    left_shape.setdefault("rows", {"min": 2, "max": 3})
    left_shape.setdefault("cols", {"min": 2, "max": 3})
    right_shape["rows"] = "A.cols"
    right_shape.setdefault("cols", {"min": 2, "max": 3})
    right["depends_on"] = _unique([*right.get("depends_on", []), "A"])


def _migrate_linear_algebra_runtime_requirements(data: dict[str, Any]) -> None:
    # TODO[LA-D002] _migrate_linear_algebra_runtime_requirements 구현
    # 1. 회귀·고유값 등의 generator/allowed_families 강제 대입이 다양성 정책을 되돌리는지 확인한다.
    # 2. 정책 적용 순서를 명시하고 차원·종속성·기존 제약을 보존한다.
    raise NotImplementedError("TODO[LA-D002]: _migrate_linear_algebra_runtime_requirements")


def _migrate_linear_algebra_curated_shapes(data: dict[str, Any]) -> None:
    # TODO[LA-D003] _migrate_linear_algebra_curated_shapes 구현
    # 1. 유형별 차원 확장은 실제 정답 계산기·독립 검증기가 지원하는 범위만 허용한다.
    # 2. 서로 독립적으로 rows/cols를 확대해 정사각형·곱셈 차원 계약을 깨지 않는다.
    raise NotImplementedError("TODO[LA-D003]: _migrate_linear_algebra_curated_shapes")


def _fallback_answer_engine(subject_id: str, answer_type: str) -> tuple[str, str | None]:
    if subject_id == "probability_statistics" or answer_type == "numerical_approximation":
        return "numpy", None

    if answer_type in {"boolean", "classification", "string", "single_choice", "multiple_choice"}:
        return "python", None

    return "sympy", "simplify"


def _new_draft_rule(
    subject_id: str,
    problem_type: str,
    metadata: dict[str, Any],
) -> GenerationRule:
    supported = metadata["supported_answer_types"]
    answer_type = supported[0] if supported else "expression"
    engine, canonicalization = _fallback_answer_engine(subject_id, answer_type)
    parameter_spec = _fallback_parameter_spec(subject_id, problem_type)
    symbol_spec = _fallback_symbol_spec(subject_id, problem_type)
    source_formula_ids = metadata["source_formula_ids"]
    primary_formula_id = (
        source_formula_ids[0] if len(source_formula_ids) == 1 else None
    )

    semantic_structure = metadata["semantic_structure"] or [
        f"{problem_type} 유형의 수학 객체를 제시한다.",
        "문제에서 요구한 연산 또는 판정을 수행하도록 한다.",
    ]

    return GenerationRule.model_validate(
        {
            "rule_id": f"{subject_id}.{problem_type}.v1",
            "rule_version": "1.0.0",
            "status": "draft_auto",
            "executable": False,
            "manual_review_required": True,
            "subject_id": subject_id,
            "problem_type": problem_type,
            "source_concept_ids": metadata["source_concept_ids"],
            "source_formula_ids": source_formula_ids,
            "primary_formula_id": primary_formula_id,
            "supported_answer_types": supported,
            "parameter_spec": parameter_spec,
            "symbol_spec": symbol_spec,
            "constraints": metadata["constraints"],
            "construction": {
                "operation": problem_type,
                "required_objects": list(parameter_spec),
                "semantic_structure": semantic_structure,
                "text_templates": [
                    "다음 조건을 이용하여 "
                    f"'{problem_type.replace('_', ' ')}' 문제를 해결하시오."
                ],
                "latex_templates": [],
                "builder_expression": None,
            },
            "answer_spec": {
                "answer_type": answer_type,
                "engine": engine,
                "expression": None,
                "latex_expression": None,
                "canonicalization": canonicalization,
            },
            "validation": {
                "validators": metadata["validators"],
                "all_required": True,
                "max_generation_attempts": 100,
            },
            "difficulty": {
                "min": metadata["difficulty_min"],
                "max": metadata["difficulty_max"],
                "factors": dict(DEFAULT_DIFFICULTY_FACTORS),
            },
            "notes": AUTO_NOTE,
        }
    )


def _refresh_existing_rule(
    existing: GenerationRule,
    metadata: dict[str, Any],
) -> GenerationRule:
    # TODO[LA-D004] _refresh_existing_rule 구현
    # 1. 새 linear_algebra_diversity_profiles.apply_policy() 연결 지점.
    # 2. 기존 보정 후 정책을 적용하되 기존 JSON을 참조하는 순환만 남기지 않는다.
    # 3. 명시적 opt-in, 불변 입력, 멱등성을 보장한다.
    # 4. 원본 검수 정보는 이력으로 보존하고 확장한 생성 범위의 검수 완료를 자동 주장하지 않는다.
    raise NotImplementedError("TODO[LA-D004]: _refresh_existing_rule")


def build_rules(
    concept_groups: dict[tuple[str, str], list[Concept]],
    existing_rules: dict[tuple[str, str], GenerationRule],
    *,
    rule_overrides: dict[tuple[str, str], GenerationRule] | None = None,
) -> dict[str, list[GenerationRule]]:
    # TODO[LA-D005] build_rules 구현
    # 1. 정책 적용은 subject_id=linear_algebra로 한정한다.
    # 2. 기존 ID·공식·정답식·검증기·사용자 제약·검수 메모의 보존 여부를 비교 보고한다.
    # 3. 다른 네 과목은 의미상 동일해야 한다.
    raise NotImplementedError("TODO[LA-D005]: build_rules")


def _build_catalog(subject_id: str, rules: list[GenerationRule]) -> GenerationRuleCatalog:
    return GenerationRuleCatalog(
        schema_version="1.1.0",
        object_type="generation_rule_catalog",
        subject_id=subject_id,
        rule_count=len(rules),
        rules=rules,
    )


def _build_manifest(by_subject: dict[str, list[GenerationRule]]) -> dict[str, Any]:
    subjects: dict[str, Any] = {}
    all_rules: list[GenerationRule] = []

    for subject_id in sorted(by_subject):
        rules = by_subject[subject_id]
        all_rules.extend(rules)
        status_counts = Counter(rule.status for rule in rules)

        subjects[subject_id] = {
            "rule_count": len(rules),
            "status_counts": dict(status_counts),
            "executable_count": sum(bool(rule.executable) for rule in rules),
            "manual_review_required_count": sum(
                bool(rule.manual_review_required) for rule in rules
            ),
        }

    total_status_counts = Counter(rule.status for rule in all_rules)

    return {
        "total_subject_problem_pairs": len(all_rules),
        "subjects": subjects,
        "status_counts": dict(total_status_counts),
    }


def _write_outputs(
    output_dir: Path,
    by_subject: dict[str, list[GenerationRule]],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    for subject_id in sorted(by_subject):
        catalog = _build_catalog(subject_id, by_subject[subject_id])
        target = output_dir / f"{subject_id}.json"
        _atomic_write_text(target,
            catalog.model_dump_json(indent=2, exclude_unset=True),
        )

    # --subject 실행 시에도 기존 다른 과목을 manifest에서 지우지 않는다.
    manifest_rules = dict(by_subject)
    for path in sorted(output_dir.glob("*.json")):
        if path.name == "manifest.json" or path.stem in manifest_rules:
            continue
        with path.open("r", encoding="utf-8") as file:
            catalog = GenerationRuleCatalog.model_validate(json.load(file))
        manifest_rules[catalog.subject_id] = list(catalog.rules)

    manifest = _build_manifest(manifest_rules)
    _atomic_write_text(output_dir / "manifest.json",
        json.dumps(manifest, ensure_ascii=False, indent=2),
    )


def _atomic_write_text(target: Path, content: str) -> None:
    """내용이 달라졌을 때만 임시 파일을 완성한 뒤 대상 파일을 교체한다.

    각 JSON 파일의 쓰기는 원자적으로 처리한다. 여러 과목 파일 전체에 대한
    트랜잭션은 아니므로 실행 중 실패했다면 동일 명령으로 다시 동기화한다.
    """
    if target.exists() and target.read_text(encoding="utf-8") == content:
        return
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=target.parent,
            prefix=f".{target.name}.", suffix=".tmp", delete=False,
        ) as file:
            temporary = file.name
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, target)
    finally:
        if temporary is not None and os.path.exists(temporary):
            os.unlink(temporary)


def _load_rule_overrides(paths: list[Path]) -> dict[tuple[str, str], GenerationRule]:
    """과목별로 보완한 Rule catalog을 읽는다.

    --rule-overrides로 지정한 JSON은 GenerationRuleCatalog 형식이어야 한다.
    rules에는 교체할 유형만 담아도 된다. 파라미터·조건·문장·정답식·Validator는
    해당 Rule 전체를 사용하므로 일부 필드만 적는 patch 파일은 허용하지 않는다.
    이 입력 자체가 검수 완료를 의미하지 않으며 draft_auto는 비실행 상태를 유지한다.
    """
    overrides: dict[tuple[str, str], GenerationRule] = {}
    for path in paths:
        catalog = GenerationRuleCatalog.model_validate_json(
            _resolve_path(path).read_text(encoding="utf-8")
        )
        if catalog.rule_count != len(catalog.rules):
            raise GenerationRuleBuildError(f"보완 파일의 rule_count 불일치: {path}")
        for rule in catalog.rules:
            key = (rule.subject_id, rule.problem_type)
            if key in overrides:
                raise GenerationRuleBuildError(f"보완 파일에 중복 Rule이 있습니다: {key}")
            overrides[key] = rule
    return overrides


def _compare_with_existing(
    output_rules: dict[str, list[GenerationRule]],
    existing_rules: dict[tuple[str, str], GenerationRule],
) -> tuple[list[str], list[str], list[str]]:
    generated = {
        (rule.subject_id, rule.problem_type): rule
        for rules in output_rules.values()
        for rule in rules
    }

    missing = sorted(
        f"{subject}/{problem_type}"
        for subject, problem_type in generated.keys() - existing_rules.keys()
    )
    stale = sorted(
        f"{subject}/{problem_type}"
        for subject, problem_type in existing_rules.keys() - generated.keys()
    )

    changed: list[str] = []
    for key in sorted(generated.keys() & existing_rules.keys()):
        if generated[key].model_dump(mode="json") != existing_rules[key].model_dump(mode="json"):
            changed.append(f"{key[0]}/{key[1]}")

    return missing, stale, changed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Concept JSON에서 GenerationRule catalog을 동기화/생성합니다. "
            "기존 수학 설계를 보존하고 과목별 보완 Rule을 반영합니다."
        )
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
        help="GenerationRule catalog 저장 디렉터리",
    )
    parser.add_argument(
        "--subject",
        type=str,
        default=None,
        help="특정 subject_id만 처리",
    )
    parser.add_argument(
        "--problem-type",
        action="append", default=[],
        help="처리할 문제 유형. 여러 번 지정 가능하며 --subject와 함께 사용합니다.",
    )
    parser.add_argument(
        "--rule-overrides", type=Path, action="append", default=[],
        help="전체 Rule 정의가 들어 있는 보완 catalog JSON. 여러 번 지정 가능합니다.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="파일을 쓰지 않고 현재 catalog와 동기화 결과 차이만 검사",
    )
    return parser.parse_args()


def main() -> int:
    # TODO[LA-D006] main 구현
    # 1. 재생성 가능한 Python 정책을 명시적으로 선택하는 CLI와 dry-run 차이를 제공한다.
    # 2. 후보는 별도 output-dir에 쓰며, 후보 카탈로그·manifest·정책 버전·seed·원본 hash를 기록한다.
    # 3. JSON 수동 편집을 요구하지 않는다.
    raise NotImplementedError("TODO[LA-D006]: main")


if __name__ == "__main__":
    raise SystemExit(main())
