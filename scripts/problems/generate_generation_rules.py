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
    """열 가지 curated 선형대수 Rule의 실행 가능한 전제조건을 채운다.

    같은 JSON에 여러 번 실행해도 항목을 중복 추가하지 않는다. 기존 정답식,
    검증기 및 사용자가 작성한 Constraint는 보존한다.
    """

    if data.get("subject_id") != "linear_algebra":
        return

    problem_type = data.get("problem_type")
    parameters = data.get("parameter_spec", {})
    constraints = data.setdefault("constraints", [])

    def spec(name: str, expected_type: str) -> dict[str, Any]:
        value = parameters.get(name)
        if not isinstance(value, dict) or value.get("type") != expected_type:
            raise GenerationRuleBuildError(
                f"linear_algebra/{problem_type}: {name}은 "
                f"{expected_type} 파라미터여야 합니다."
            )
        return value

    def shape(name: str, expected_type: str, **dimensions: Any) -> dict[str, Any]:
        value = spec(name, expected_type)
        current = value.setdefault("shape", {})
        if not isinstance(current, dict):
            raise GenerationRuleBuildError(
                f"linear_algebra/{problem_type}: {name}.shape는 객체여야 합니다."
            )
        for field, dimension in dimensions.items():
            current.setdefault(field, dimension)
        return value

    def dependent_shape(name: str, expected_type: str, dependency: str, **dimensions: Any) -> None:
        value = shape(name, expected_type, **dimensions)
        value["depends_on"] = _unique([*value.get("depends_on", []), dependency])

    def require(expression: str | dict[str, Any], label: str) -> None:
        if any(c.get("expression") == expression for c in constraints if isinstance(c, dict)):
            return
        constraints.append({
            "type": "generation_precondition",
            "expression": expression,
            "required": True,
            "description": label,
        })

    def property_constraint(name: str, operator: str, label: str) -> None:
        require({
            "constraint_id": f"migration.{problem_type}.{name}.{operator}",
            "scope": "generation",
            "description": label,
            "rule": {"left": name, "operator": operator},
            "on_failure": "resample",
        }, label)

    square = {"rows": {"min": 2, "max": 3}, "cols": "A.rows"}

    if problem_type == "elementary_matrix_construction":
        spec("n", "integer")
        for name in ("source_row", "target_row"):
            spec(name, "integer")
            require(f"{name} < n", f"{name}은 n보다 작아야 한다.")
        # 서로 다른 행이라는 기존 조건을 삭제하지 않는다.

    elif problem_type == "lu_factorization":
        shape("A", "matrix", **square)
        property_constraint("A", "lu_without_pivoting", "A는 행 교환 없이 LU 분해 가능")

    elif problem_type == "gram_schmidt_orthogonalization":
        shape("V", "matrix", rows=3, cols=2)
        require("rank(V) == V.cols", "V의 열벡터가 선형독립")

    elif problem_type == "least_squares_calculation":
        shape("A", "matrix", rows={"min": 3, "max": 4}, cols=2)
        dependent_shape("b", "vector", "A", dimension="A.rows")
        require("rank(A) == A.cols", "A는 full column rank")

    elif problem_type == "linear_regression_calculation":
        design = shape("X", "matrix", rows={"min": 3, "max": 4}, cols=2)
        design["generator"] = "regression_design_matrix"
        dependent_shape("y", "vector", "X", dimension="X.rows")
        require("rank(X) == X.cols", "X는 full column rank")
        # 전용 샘플러가 첫 열을 1로 고정하고 나머지 열은 무작위로 채운다.

    elif problem_type == "eigenvector_calculation":
        matrix = shape("A", "matrix", **square)
        matrix["allowed_families"] = ["symmetric"]
        value = spec("lambda_val", "integer") if parameters.get("lambda_val", {}).get("type") == "integer" else spec("lambda_val", "derived")
        value["type"] = "derived"
        for field in ("min", "max", "step", "choices", "exclude", "distribution"):
            value.pop(field, None)
        value["depends_on"] = _unique([*value.get("depends_on", []), "A"])
        value["derived"] = {
            "depends_on": ["A"],
            "expression": "list(A.eigenvals().keys())",
            "engine": "sympy",
            "selection": "random",
        }

    elif problem_type == "matrix_diagonalization":
        shape("A", "matrix", **square)
        property_constraint("A", "diagonalizable", "A는 실수 범위에서 대각화 가능")

    elif problem_type in {
        "orthogonal_diagonalization_calculation",
        "spectral_decomposition_calculation",
        "positive_definite_test",
    }:
        matrix = shape("A", "matrix", **square)
        matrix["allowed_families"] = ["symmetric"]
        property_constraint("A", "symmetric", "A는 실수 대칭행렬")


def _migrate_linear_algebra_curated_shapes(data: dict[str, Any]) -> None:
    """curated 선형대수 Rule의 행렬·벡터 크기 관계를 완성한다.

    기존에 사람이 검수해 넣은 shape 필드는 보존하고 누락 필드만 채운다.
    다른 파라미터를 참조하는 경우 depends_on도 함께 추가한다. 같은 입력에
    여러 번 실행해도 결과가 바뀌지 않는 반복 가능한 마이그레이션이다.
    """

    if data.get("subject_id") != "linear_algebra" or data.get("status") != "curated":
        return

    problem_type = data.get("problem_type")
    parameters = data.get("parameter_spec", {})
    ranged = {"min": 2, "max": 3}

    # (parameter name, shape, explicit dependencies)
    mappings: dict[str, list[tuple[str, dict[str, Any], list[str]]]] = {
        "algebraic_expansion_verification": [
            ("A", {"rows": ranged, "cols": "A.rows"}, []),
            ("B", {"rows": "A.rows", "cols": "A.cols"}, ["A"]),
        ],
        "basis_verification": [("V", {"rows": "n", "cols": "n"}, ["n"])],
        "block_matrix_determinant": [
            ("B", {"rows": ranged, "cols": "B.rows"}, []),
            ("C", {"rows": ranged, "cols": "C.rows"}, []),
        ],
        "change_of_basis_calculation": [
            ("B", {"rows": ranged, "cols": "B.rows"}, []),
            ("C", {"rows": "B.rows", "cols": "B.cols"}, ["B"]),
        ],
        "column_space_basis": [("A", {"rows": 3, "cols": 3}, [])],
        "consistency_check": [("Aug", {"rows": 2, "cols": 3}, [])],
        "cramer_rule_solution": [
            ("A", {"rows": ranged, "cols": "A.rows"}, []),
            ("b", {"dimension": "A.rows"}, ["A"]),
        ],
        "determinant_by_ero": [("A", {"rows": ranged, "cols": "A.rows"}, [])],
        "determinant_cofactor_expansion": [("A", {"rows": ranged, "cols": "A.rows"}, [])],
        "eigenvalue_calculation": [("A", {"rows": ranged, "cols": "A.rows"}, [])],
        "eigenvector_calculation": [("A", {"rows": ranged, "cols": "A.rows"}, [])],
        "elementary_inverse_calculation": [("E", {"rows": 3, "cols": 3}, [])],
        "equation_to_matrix": [
            ("A", {"rows": 2, "cols": 2}, []),
            ("b", {"dimension": "A.rows"}, ["A"]),
        ],
        "equivalence_theorem_check": [("A", {"rows": ranged, "cols": "A.rows"}, [])],
        "ero_application": [("A", {"rows": 3, "cols": 3}, [])],
        "free_variable_identification": [("A", {"rows": 2, "cols": 3}, [])],
        "geometric_area_volume_calculation": [("A", {"rows": ranged, "cols": "A.rows"}, [])],
        "gram_schmidt_orthogonalization": [("V", {"rows": 3, "cols": 2}, [])],
        "inverse_calculation": [("A", {"rows": ranged, "cols": "A.rows"}, [])],
        "invertibility_determination": [("A", {"rows": ranged, "cols": "A.rows"}, [])],
        "kernel_image_calculation": [("A", {"rows": 3, "cols": 3}, [])],
        "least_squares_calculation": [
            ("A", {"rows": {"min": 3, "max": 4}, "cols": 2}, []),
            ("b", {"dimension": "A.rows"}, ["A"]),
        ],
        "left_null_space_basis": [("A", {"rows": 3, "cols": 2}, [])],
        "linear_independence_test": [("V", {"rows": 3, "cols": 2}, [])],
        "linear_regression_calculation": [
            ("X", {"rows": {"min": 3, "max": 4}, "cols": 2}, []),
            ("y", {"dimension": "X.rows"}, ["X"]),
        ],
        "linear_transformation_verification": [
            ("A", {"rows": 2, "cols": 2}, []),
            ("b", {"dimension": "A.rows"}, ["A"]),
        ],
        "lu_factorization": [("A", {"rows": ranged, "cols": "A.rows"}, [])],
        "matrix_diagonalization": [("A", {"rows": ranged, "cols": "A.rows"}, [])],
        "matrix_multiplication": [
            ("A", {"rows": ranged, "cols": ranged}, []),
            ("B", {"rows": "A.cols", "cols": ranged}, ["A"]),
        ],
        "matrix_power_calculation": [("A", {"rows": ranged, "cols": "A.rows"}, [])],
        "matrix_to_vector_equation": [
            ("A", {"rows": 2, "cols": 2}, []),
            ("b", {"dimension": "A.rows"}, ["A"]),
        ],
        "norm_distance_calculation": [
            ("u", {"dimension": ranged}, []),
            ("v", {"dimension": "u.dimension"}, ["u"]),
        ],
        "null_space_basis": [("A", {"rows": 2, "cols": 3}, [])],
        "orthogonal_complement_calculation": [("W", {"rows": 3, "cols": 2}, [])],
        "orthogonal_diagonalization_calculation": [("A", {"rows": ranged, "cols": "A.rows"}, [])],
        "orthogonal_projection_calculation": [
            ("a", {"dimension": ranged}, []),
            ("b", {"dimension": "a.dimension"}, ["a"]),
        ],
        "orthonormal_verification": [("Q", {"rows": 3, "cols": 2}, [])],
        "parametric_solution_extraction": [
            ("A", {"rows": 2, "cols": 3}, []),
            ("b", {"dimension": "A.rows"}, ["A"]),
        ],
        "positive_definite_test": [("A", {"rows": ranged, "cols": "A.rows"}, [])],
        "qr_factorization_calculation": [("A", {"rows": 3, "cols": 2}, [])],
        "quadratic_form_transformation": [("A", {"rows": ranged, "cols": "A.rows"}, [])],
        "rank_calculation": [("A", {"rows": ranged, "cols": ranged}, [])],
        "rank_nullity_calculation": [("A", {"rows": 2, "cols": 3}, [])],
        "ref_identification": [("A", {"rows": 3, "cols": 4}, [])],
        "row_space_basis": [("A", {"rows": 2, "cols": 3}, [])],
        "rref_calculation": [("A", {"rows": 3, "cols": 4}, [])],
        "singular_matrix_identification": [("A", {"rows": ranged, "cols": "A.rows"}, [])],
        "solve_by_lu": [
            ("A", {"rows": ranged, "cols": "A.rows"}, []),
            ("b", {"dimension": "A.rows"}, ["A"]),
        ],
        "span_membership_test": [
            ("V", {"rows": 3, "cols": 2}, []),
            ("b", {"dimension": "V.rows"}, ["V"]),
        ],
        "spectral_decomposition_calculation": [("A", {"rows": ranged, "cols": "A.rows"}, [])],
        "standard_matrix_derivation": [("images", {"rows": 3, "cols": 2}, [])],
        "subspace_verification": [
            ("A", {"rows": 2, "cols": 3}, []),
            ("b", {"dimension": "A.rows"}, ["A"]),
        ],
        "symmetry_classification": [("A", {"rows": ranged, "cols": "A.rows"}, [])],
        "transpose_algebra": [
            ("A", {"rows": 2, "cols": 3}, []),
            ("B", {"rows": "A.cols", "cols": 2}, ["A"]),
        ],
    }

    # 스칼라 파라미터만 사용하는 두 유형은 shape 마이그레이션 대상이 아니다.
    no_shape_required = {"elementary_matrix_construction", "matrix_rank_property"}
    entries = mappings.get(problem_type)
    if entries is None:
        if problem_type in no_shape_required:
            return
        raise GenerationRuleBuildError(
            f"linear_algebra/{problem_type}: curated shape 매핑이 없습니다."
        )

    for name, dimensions, dependencies in entries:
        spec = parameters.get(name)
        if not isinstance(spec, dict) or spec.get("type") not in {"matrix", "vector"}:
            raise GenerationRuleBuildError(
                f"linear_algebra/{problem_type}: {name}은 matrix/vector 파라미터여야 합니다."
            )
        current = spec.setdefault("shape", {})
        if not isinstance(current, dict):
            raise GenerationRuleBuildError(
                f"linear_algebra/{problem_type}: {name}.shape는 객체여야 합니다."
            )
        for field, value in dimensions.items():
            current.setdefault(field, copy.deepcopy(value))
        if dependencies:
            spec["depends_on"] = _unique([*spec.get("depends_on", []), *dependencies])

    missing = [
        name
        for name, spec in parameters.items()
        if isinstance(spec, dict)
        and spec.get("type") in {"matrix", "vector"}
        and not spec.get("shape")
    ]
    if missing:
        raise GenerationRuleBuildError(
            f"linear_algebra/{problem_type}: 크기 규칙 누락: {', '.join(missing)}"
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

    # curated/reviewed Rule의 수학 설계를 보존하면서, 선형대수 행렬 곱셈의
    # 누락된 크기 관계만 채운다. Validator 매핑 등 다른 검수 정보는 유지한다.
    if existing.status != "draft_auto":
        data = _normalize_legacy_constraint_encoding(existing).model_dump(
            mode="python", exclude_unset=True
        )
        _ensure_linear_algebra_matrix_multiplication_shape(data)
        _migrate_linear_algebra_runtime_requirements(data)
        _migrate_linear_algebra_curated_shapes(data)
        return GenerationRule.model_validate(data)

    data = existing.model_dump(mode="python", exclude_unset=True)

    # 기존 초안도 매번 동일한 상태로 정규화한다. 예전 executable=True 값이
    # answer_type 변경 여부와 관계없이 다음 동기화 결과에 남지 않도록 한다.
    # curated/reviewed는 위 분기에서 반환하므로 이 초기화 대상이 아니다.
    data["executable"] = False
    data["manual_review_required"] = True

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
        _ensure_linear_algebra_matrix_multiplication_shape(data)
        data["constraints"] = metadata["constraints"]
        _migrate_linear_algebra_runtime_requirements(data)
        _migrate_linear_algebra_curated_shapes(data)
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
