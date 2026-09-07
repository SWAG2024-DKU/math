from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
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
    specs = {
        name: copy.deepcopy(PARAMETER_LIBRARY[name])
        for name in _fallback_parameter_names(subject_id, problem_type)
    }

    text = problem_type.lower()
    if "A" in specs and any(
        keyword in text for keyword in SQUARE_MATRIX_KEYWORDS
    ):
        specs["A"]["shape"] = {
            "rows": {"min": 2, "max": 4},
            "cols": "A.rows",
        }

    if "A" in specs and "B" in specs and "matrix_multiplication" in text:
        specs["B"]["shape"] = {
            "rows": "A.cols",
            "cols": {"min": 2, "max": 4},
        }
        specs["B"]["depends_on"] = ["A"]

    if "A" in specs and problem_type == "eigenvector_calculation":
        specs["lambda_val"] = {
            "type": "derived",
            "description": "A의 고윳값 중 하나",
            "depends_on": ["A"],
            "derived": {
                "depends_on": ["A"],
                "expression": "choose_eigenvalue(A)",
                "engine": "registry",
                "selection": "uniform",
            },
        }

    return specs


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
        shape = parameters["A"].setdefault("shape", {})
        if shape.get("rows") is not None:
            shape["cols"] = "A.rows"

    if "A" in parameters and "B" in parameters and "matrix_multiplication" in text:
        shape = parameters["B"].setdefault("shape", {})
        shape["rows"] = "A.cols"
        parameters["B"]["depends_on"] = _unique(
            [*parameters["B"].get("depends_on", []), "A"]
        )

    if "u" in parameters and "v" in parameters:
        parameters["v"]["shape"] = {"dimension": "u.dimension"}
        parameters["v"]["depends_on"] = _unique(
            [*parameters["v"].get("depends_on", []), "u"]
        )


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
    """
    Concept에서 기계적으로 유도되는 필드만 최신화한다.

    parameter_spec, executable expression, curated construction 등 사람이 검토하거나
    실행 엔진과 연결한 정보는 보존한다.
    """

    # curated/reviewed Rule의 수학 설계는 보존하고, 이중 인코딩만 정규화한다.
    if existing.status != "draft_auto":
        return _normalize_legacy_constraint_encoding(existing)

    data = existing.model_dump(mode="python", exclude_unset=True)

    data["source_concept_ids"] = metadata["source_concept_ids"]
    data["source_formula_ids"] = metadata["source_formula_ids"]
    data["supported_answer_types"] = metadata["supported_answer_types"]
    data["difficulty"]["min"] = metadata["difficulty_min"]
    data["difficulty"]["max"] = metadata["difficulty_max"]

    if existing.status == "draft_auto":
        source_formula_ids = metadata["source_formula_ids"]
        current_primary = data.get("primary_formula_id")
        if current_primary not in source_formula_ids:
            data["primary_formula_id"] = (
                source_formula_ids[0] if len(source_formula_ids) == 1 else None
            )

        _migrate_draft_structure(
            data,
            subject_id=existing.subject_id,
            problem_type=existing.problem_type,
        )
        data["constraints"] = metadata["constraints"]
        data["construction"]["semantic_structure"] = (
            metadata["semantic_structure"]
            or data["construction"]["semantic_structure"]
        )
        data["validation"]["validators"] = metadata["validators"]

        supported = metadata["supported_answer_types"]
        current_answer_type = data["answer_spec"]["answer_type"]
        if supported and current_answer_type not in supported:
            data["answer_spec"]["answer_type"] = supported[0]
            data["answer_spec"]["expression"] = None
            data["answer_spec"]["latex_expression"] = None
            data["executable"] = False
            data["manual_review_required"] = True

    return GenerationRule.model_validate(data)


def build_rules(
    concept_groups: dict[tuple[str, str], list[Concept]],
    existing_rules: dict[tuple[str, str], GenerationRule],
) -> dict[str, list[GenerationRule]]:
    by_subject: dict[str, list[GenerationRule]] = defaultdict(list)

    for (subject_id, problem_type), concepts in sorted(concept_groups.items()):
        metadata = _aggregate_metadata(concepts)
        existing = existing_rules.get((subject_id, problem_type))

        if existing is None:
            rule = _new_draft_rule(subject_id, problem_type, metadata)
        else:
            rule = _refresh_existing_rule(existing, metadata)

        by_subject[subject_id].append(rule)

    for rules in by_subject.values():
        rules.sort(key=lambda rule: rule.problem_type)

    return dict(by_subject)


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
        target.write_text(
            catalog.model_dump_json(indent=2, exclude_unset=True),
            encoding="utf-8",
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
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


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
            "기존 curated/reviewed Rule은 보존하고, draft_auto의 기계적 메타데이터만 갱신합니다."
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
        "--check",
        action="store_true",
        help="파일을 쓰지 않고 현재 catalog와 동기화 결과 차이만 검사",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    concept_dir = _resolve_path(args.concept_dir)
    output_dir = _resolve_path(args.output_dir)

    concept_groups = _load_concept_groups(
        concept_dir,
        subject_filter=args.subject,
    )
    if not concept_groups:
        raise SystemExit("생성 대상 Generation Rule이 없습니다.")

    existing_rules = _load_existing_rules(output_dir)
    if args.subject:
        existing_rules = {
            key: rule
            for key, rule in existing_rules.items()
            if key[0] == args.subject
        }

    by_subject = build_rules(concept_groups, existing_rules)

    new_count = sum(
        1
        for rules in by_subject.values()
        for rule in rules
        if (rule.subject_id, rule.problem_type) not in existing_rules
    )

    print("=== GenerationRule 생성/동기화 ===")
    print(f"대상 subject/problem_type: {sum(map(len, by_subject.values()))}")
    print(f"기존 Rule 재사용/동기화: {sum(map(len, by_subject.values())) - new_count}")
    print(f"신규 draft_auto 생성: {new_count}")

    if args.check:
        missing, stale, changed = _compare_with_existing(
            by_subject,
            existing_rules,
        )
        print(f"현재 catalog에 없는 Rule: {len(missing)}")
        print(f"Concept에서 더 이상 사용하지 않는 Rule: {len(stale)}")
        print(f"Concept 메타데이터와 달라진 Rule: {len(changed)}")

        for label, values in (
            ("NEW", missing),
            ("STALE", stale),
            ("CHANGED", changed),
        ):
            for value in values[:20]:
                print(f"[{label}] {value}")
            if len(values) > 20:
                print(f"[{label}] ... 외 {len(values) - 20}개")

        return 1 if (missing or stale or changed) else 0

    _write_outputs(output_dir, by_subject)
    print(f"출력 디렉터리: {output_dir}")
    print("GenerationRule catalog 생성/동기화 완료")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
