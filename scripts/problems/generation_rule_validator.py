from __future__ import annotations

"""GenerationRule 정적 의미 검증기.

이 모듈은 GenerationRule JSON/Pydantic 객체를 실제로 실행하지 않고 다음을
검사한다.

- Rule 식별자와 상태 플래그의 일관성
- parameter_spec과 required_objects/Jinja 변수의 일치
- builder/answer expression의 구문 및 미선언 변수
- Constraint의 저장 형식과 파라미터 참조
- 실행 Rule에 필요한 행렬 크기/파생 파라미터/수학적 전제조건
- ProblemType과 Validator 조합의 명백한 불일치

프로젝트 배치 생성 경로에서는 ``ensure_generation_rule_valid``를 import해서
사용할 수 있고, 단독 실행 시 ``data/generation_rules`` 전체를 검사한다.
수식을 평가하지 않으므로 이 파일 자체는 eval/exec/sympify를 사용하지 않는다.
"""

import argparse
import ast
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Mapping, Sequence

from pydantic import ValidationError


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RULE_DIR = PROJECT_ROOT / "data" / "generation_rules"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.schemas.generation_rule import GenerationRule

SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}
VALID_STATUSES = {
    "draft_auto",
    "reviewed",
    "curated",
}

# 이 상태에서 executable=True인 Rule만 배포 후보로 보고 실행 계약을 엄격히
# 검사한다. draft_auto는 문제를 숨기지 않되 검토 목록인 warning으로 남긴다.
STRICT_EXECUTION_STATUSES = {"reviewed", "curated"}

IDENTIFIER_RE = re.compile(r"[A-Za-z_]\w*")
JINJA_EXPRESSION_RE = re.compile(r"{{\s*(.*?)\s*}}", re.DOTALL)

# 식 평가기가 제공해야 하는 안전한 전역 이름이다. 이 검증기는 실행하지 않고
# 미선언 변수와 helper 함수 호출을 구분하기 위해서만 사용한다.
BUILTIN_EXPRESSION_NAMES = {
    "Abs",
    "Derivative",
    "E",
    "Eq",
    "False",
    "I",
    "Integer",
    "Integral",
    "Matrix",
    "Max",
    "Min",
    "None",
    "Rational",
    "S",
    "Sum",
    "True",
    "all",
    "any",
    "cos",
    "det",
    "diff",
    "eye",
    "exp",
    "factorial",
    "integrate",
    "len",
    "limit",
    "list",
    "linsolve",
    "log",
    "max",
    "min",
    "oo",
    "pi",
    "set",
    "sin",
    "sorted",
    "sqrt",
    "summation",
    "tuple",
}

# 샘플링 파라미터가 아니라 수식의 독립변수/인덱스일 수 있는 이름이다.
# 조용히 무시하지 않고 implicit_symbol warning으로 남긴다.
COMMON_SYMBOL_NAMES = {
    "i",
    "j",
    "k",
    "m",
    "n",
    "r",
    "s",
    "t",
    "u",
    "v",
    "w",
    "x",
    "y",
    "z",
    "phi",
    "rho",
    "theta",
}

SYMPY_BINDING_CALLS = {
    "Derivative",
    "Integral",
    "Sum",
    "diff",
    "integrate",
    "limit",
    "summation",
}

SHAPE_KEYS = {
    "shape",
    "rows",
    "cols",
    "rows_min",
    "rows_max",
    "cols_min",
    "cols_max",
    "dimension",
    "dimension_min",
    "dimension_max",
    "length",
    "length_min",
    "length_max",
    "size",
    "size_min",
    "size_max",
}


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    code: str
    message: str
    rule_id: str = "<unknown>"
    field: str | None = None
    source_path: str | None = None
    rule_status: str | None = None


class GenerationRuleValidationError(ValueError):
    """차단 수준의 GenerationRule 오류가 발견됐을 때 발생한다."""

    def __init__(self, issues: Sequence[ValidationIssue]) -> None:
        self.issues = tuple(issues)
        lines = [
            f"{issue.rule_id}: [{issue.code}] {issue.message}"
            for issue in self.issues[:10]
        ]
        if len(self.issues) > 10:
            lines.append(f"... 외 {len(self.issues) - 10}개")
        super().__init__("GenerationRule 검증 실패\n" + "\n".join(lines))


def _to_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return dict(model_dump(mode="python"))
    raise TypeError(
        "GenerationRule은 Mapping 또는 model_dump()를 제공하는 객체여야 합니다."
    )


def _is_nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _expression_texts(constraints: Sequence[Any]) -> list[str]:
    result: list[str] = []
    for constraint in constraints:
        if not isinstance(constraint, Mapping):
            continue
        expression = constraint.get("expression")
        if isinstance(expression, str):
            result.append(expression)
        elif isinstance(expression, Mapping):
            result.append(json.dumps(expression, ensure_ascii=False, sort_keys=True))
    return result


def _condition_contains(constraints: Sequence[Any], *tokens: str) -> bool:
    haystack = " ".join(_expression_texts(constraints)).lower()
    return all(
        re.search(
            rf"(?<![A-Za-z0-9_]){re.escape(token.lower())}(?![A-Za-z0-9_])",
            haystack,
        )
        is not None
        for token in tokens
    )


def _has_shape_spec(spec: Mapping[str, Any]) -> bool:
    return any(key in spec and spec[key] is not None for key in SHAPE_KEYS)


def _jinja_roots(template: str) -> set[str]:
    roots: set[str] = set()
    for expression in JINJA_EXPRESSION_RE.findall(template):
        match = IDENTIFIER_RE.search(expression)
        if match:
            roots.add(match.group(0))
    return roots


def _bound_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
    return names


def _binding_target_names(node: ast.AST) -> set[str]:
    """SymPy 연산자의 변수 인자에서 묶이는 이름을 추출한다."""

    if isinstance(node, ast.Name):
        return {node.id}
    if isinstance(node, (ast.Tuple, ast.List)) and node.elts:
        first = node.elts[0]
        return {first.id} if isinstance(first, ast.Name) else set()
    return set()


def _sympy_bound_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        if node.func.id not in SYMPY_BINDING_CALLS:
            continue

        variable_args = node.args[1:]
        if node.func.id == "limit":
            variable_args = node.args[1:2]
        for argument in variable_args:
            names.update(_binding_target_names(argument))
    return names


def _loaded_names(tree: ast.AST) -> set[str]:
    return {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }


def _direct_call_names(tree: ast.AST) -> set[str]:
    return {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }


def _analyze_python_expression(
    expression: str,
    *,
    parameters: set[str],
    strict_execution: bool,
    rule_id: str,
    field: str,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        issues.append(
            ValidationIssue(
                "error" if strict_execution else "warning",
                "invalid_expression_syntax",
                f"Python expression 구문을 해석할 수 없습니다: {exc.msg}",
                rule_id,
                field,
            )
        )
        return issues

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            issues.append(
                ValidationIssue(
                    "error",
                    "dunder_access_forbidden",
                    f"허용할 수 없는 특수 속성 접근입니다: {node.attr}",
                    rule_id,
                    field,
                )
            )

    bound = _bound_names(tree) | _sympy_bound_names(tree)
    loaded = _loaded_names(tree)
    direct_calls = _direct_call_names(tree)
    unknown = loaded - bound - parameters - BUILTIN_EXPRESSION_NAMES

    for name in sorted(unknown):
        if name in direct_calls:
            issues.append(
                ValidationIssue(
                    "warning",
                    "external_helper_required",
                    f"'{name}' helper가 안전한 실행 환경에 등록되어 있어야 합니다.",
                    rule_id,
                    field,
                )
            )
        elif name in COMMON_SYMBOL_NAMES:
            issues.append(
                ValidationIssue(
                    "warning",
                    "implicit_symbol",
                    f"'{name}'은 수학 기호로 보입니다. 실행 환경에서 Symbol로 "
                    "등록되는지 확인해야 합니다.",
                    rule_id,
                    field,
                )
            )
        else:
            issues.append(
                ValidationIssue(
                    "error" if strict_execution else "warning",
                    "undeclared_expression_name",
                    f"식에서 사용한 '{name}'이 parameter_spec에 선언되지 않았습니다.",
                    rule_id,
                    field,
                )
            )

    return issues


def _structured_constraint_names(value: Any) -> set[str]:
    names: set[str] = set()
    if isinstance(value, Mapping):
        # 기존 v1 포맷은 최상위 metadata와 실제 식인 rule을 함께 담는다.
        # constraint_id/operator/description 같은 문자열은 변수 참조가 아니므로
        # 실제 피연산자 필드만 검사한다.
        if isinstance(value.get("rule"), Mapping):
            names.update(_structured_constraint_names(value["rule"]))
        else:
            operand_keys = {
                "args",
                "expression",
                "left",
                "operand",
                "operands",
                "right",
                "source",
                "value",
            }
            for key, child in value.items():
                if key in operand_keys:
                    names.update(_structured_constraint_names(child))
    elif isinstance(value, list):
        for child in value:
            names.update(_structured_constraint_names(child))
    elif isinstance(value, str):
        try:
            tree = ast.parse(value, mode="eval")
        except SyntaxError:
            return names
        loaded = _loaded_names(tree)
        bound = _bound_names(tree) | _sympy_bound_names(tree)
        names.update(loaded - bound - BUILTIN_EXPRESSION_NAMES)
    return names


def _validate_constraint(
    constraint: Any,
    *,
    index: int,
    declared_names: set[str],
    strict_execution: bool,
    rule_id: str,
) -> list[ValidationIssue]:
    field = f"constraints[{index}]"
    issues: list[ValidationIssue] = []

    if not isinstance(constraint, Mapping):
        return [
            ValidationIssue(
                "error",
                "invalid_constraint_type",
                "Constraint는 JSON object여야 합니다.",
                rule_id,
                field,
            )
        ]

    expression = constraint.get("expression")
    if expression is None:
        return [
            ValidationIssue(
                "error",
                "missing_constraint_expression",
                "Constraint expression이 없습니다.",
                rule_id,
                field,
            )
        ]

    structured: Any = None
    if isinstance(expression, Mapping):
        structured = expression
    elif isinstance(expression, str):
        stripped = expression.strip()
        if not stripped:
            issues.append(
                ValidationIssue(
                    "error",
                    "empty_constraint_expression",
                    "Constraint expression이 비어 있습니다.",
                    rule_id,
                    field,
                )
            )
            return issues

        try:
            decoded = json.loads(stripped)
        except json.JSONDecodeError:
            decoded = None

        if isinstance(decoded, Mapping):
            structured = decoded
            issues.append(
                ValidationIssue(
                    "warning",
                    "constraint_double_encoded",
                    "구조화 Constraint가 JSON 문자열로 이중 저장되어 있습니다.",
                    rule_id,
                    f"{field}.expression",
                )
            )
        else:
            try:
                ast.parse(stripped, mode="eval")
            except SyntaxError:
                severity = "error" if strict_execution else "warning"
                issues.append(
                    ValidationIssue(
                        severity,
                        "non_executable_constraint",
                        "Constraint가 설명용 문자열이며 실행 가능한 식/객체가 아닙니다.",
                        rule_id,
                        f"{field}.expression",
                    )
                )
            else:
                issues.extend(
                    _analyze_python_expression(
                        stripped,
                        parameters=declared_names,
                        strict_execution=strict_execution,
                        rule_id=rule_id,
                        field=f"{field}.expression",
                    )
                )
    else:
        issues.append(
            ValidationIssue(
                "error",
                "invalid_constraint_expression_type",
                "Constraint expression은 문자열 또는 object여야 합니다.",
                rule_id,
                f"{field}.expression",
            )
        )

    if structured is not None:
        unknown = _structured_constraint_names(structured) - declared_names
        for name in sorted(unknown):
            # constraint_id, operator 이름처럼 식별자로 우연히 해석되는 문자열은
            # rule.left/right 내부에 있을 때만 실제 참조가 된다. 명백한 미선언
            # 참조만 경고하고 실행 단계의 evaluator가 최종 판정하도록 한다.
            if name in {"generation", "resample"}:
                continue
            issues.append(
                ValidationIssue(
                    "error" if strict_execution else "warning",
                    "unknown_constraint_reference",
                    f"구조화 Constraint가 미선언 이름 '{name}'을 참조할 수 있습니다.",
                    rule_id,
                    f"{field}.expression",
                )
            )

    return issues


def _validate_operation_requirements(
    rule: Mapping[str, Any],
    *,
    parameters: Mapping[str, Any],
    constraints: Sequence[Any],
    strict_execution: bool,
    rule_id: str,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    construction = _mapping(rule.get("construction"))
    operation = str(construction.get("operation") or rule.get("problem_type") or "")
    executable = bool(rule.get("executable"))
    if not executable:
        return issues

    def add(code: str, message: str, field: str = "constraints") -> None:
        severity = "error" if strict_execution else "warning"
        issues.append(ValidationIssue(severity, code, message, rule_id, field))

    if operation == "matrix_multiplication":
        b_spec = _mapping(parameters.get("B"))
        b_shape = _mapping(b_spec.get("shape"))
        linked_by_shape = (
            b_shape.get("rows") == "A.cols"
            and "A" in _list(b_spec.get("depends_on"))
        )
        linked_by_constraint = _condition_contains(
            constraints,
            "A.cols",
            "B.rows",
        )
        if not linked_by_shape and not linked_by_constraint:
            add(
                "matrix_dimensions_not_linked",
                "행렬곱을 위해 A.cols == B.rows 관계를 구조화해야 합니다.",
            )

    if operation == "eigenvector_calculation":
        lambda_spec = _mapping(parameters.get("lambda_val"))
        is_derived = lambda_spec.get("type") == "derived" or any(
            lambda_spec.get(key) is not None
            for key in ("derived", "derived_from", "expression", "source")
        )
        has_relation = _condition_contains(constraints, "lambda_val", "A")
        if not is_derived and not has_relation:
            add(
                "eigenvalue_not_derived",
                "lambda_val은 무작위 정수가 아니라 A의 고윳값에서 파생되어야 합니다.",
                "parameter_spec.lambda_val",
            )

    if operation == "elementary_matrix_construction":
        n_spec = _mapping(parameters.get("n"))
        for name in ("target_row", "source_row"):
            row_spec = _mapping(parameters.get(name))
            row_max = row_spec.get("max")
            n_min = n_spec.get("min")
            has_bound = _condition_contains(constraints, name, "n")
            if (
                isinstance(row_max, (int, float))
                and isinstance(n_min, (int, float))
                and row_max >= n_min
                and not has_bound
            ):
                add(
                    "row_index_not_bounded_by_n",
                    f"{name} < n 의존조건이 없어 범위를 벗어난 행 인덱스가 생성될 수 있습니다.",
                    f"parameter_spec.{name}",
                )

    rank_required = {
        "least_squares_calculation": "A",
        "linear_regression_calculation": "X",
        "gram_schmidt_orthogonalization": "V",
    }
    if operation in rank_required:
        name = rank_required[operation]
        if not _condition_contains(constraints, "rank", name):
            add(
                "full_rank_condition_missing",
                f"{operation} 실행에 필요한 {name}의 full-rank 조건이 없습니다.",
            )

    symmetric_required = {
        "orthogonal_diagonalization_calculation",
        "positive_definite_test",
        "spectral_decomposition_calculation",
    }
    if operation in symmetric_required and not (
        _condition_contains(constraints, "symmetric")
        or _condition_contains(constraints, ".T")
        or _mapping(parameters.get("A")).get("generator") == "symmetric_matrix"
    ):
        add(
            "symmetric_matrix_condition_missing",
            f"{operation}에 필요한 실수 대칭행렬 생성 조건이 없습니다.",
        )

    if operation == "matrix_diagonalization" and not _condition_contains(
        constraints, "diagonal"
    ):
        add(
            "diagonalizable_condition_missing",
            "대각화 문제에 A가 대각화 가능하다는 생성 조건이 없습니다.",
        )

    if operation == "lu_factorization" and not (
        _condition_contains(constraints, "pivot")
        or _condition_contains(constraints, "minor")
        or _mapping(parameters.get("A")).get("generator") == "lu_factorable_matrix"
    ):
        add(
            "lu_generation_condition_missing",
            "행 교환 없는 LU 분해가 가능하다는 생성 조건이 없습니다.",
        )

    suspicious_validators = {
        ("orthogonal_projection_calculation", "idempotent_symmetric_check"):
            "벡터 사영 답안에 투영행렬의 멱등·대칭 검사가 연결되어 있습니다.",
        ("singular_matrix_identification", "zero_row_detection"):
            "영행 존재는 특이행렬과 동치가 아닙니다. det/rank 검증이 필요합니다.",
        ("symmetry_classification", "matrix_equivalence"):
            "대칭 여부의 Boolean 답안에는 boolean/logical 검증기가 적절합니다.",
        ("standard_matrix_derivation", "matrix_multiplication_check"):
            "표준행렬 답안에는 matrix_equivalence 검증기가 더 적절합니다.",
    }
    validators = _list(_mapping(rule.get("validation")).get("validators"))
    validator_names = {
        str(item.get("name")) if isinstance(item, Mapping) else str(item)
        for item in validators
    }
    for (problem_type, validator), message in suspicious_validators.items():
        if operation == problem_type and validator in validator_names:
            add("validator_semantic_mismatch", message, "validation.validators")

    return issues


def validate_generation_rule(rule: Mapping[str, Any] | Any) -> list[ValidationIssue]:
    """GenerationRule 하나를 정적으로 검사하고 모든 이슈를 반환한다."""

    raw_data = _to_dict(rule)
    rule_id = str(raw_data.get("rule_id") or "<unknown>")
    raw_status = raw_data.get("status")
    issues: list[ValidationIssue] = []

    def add(severity: str, code: str, message: str, field: str | None = None) -> None:
        issues.append(ValidationIssue(severity, code, message, rule_id, field))

    try:
        validated_rule = GenerationRule.model_validate(raw_data)
    except ValidationError as exc:
        for error in exc.errors(include_url=False):
            field = ".".join(str(part) for part in error.get("loc", ())) or None
            add(
                "error",
                "schema_validation_error",
                str(error.get("msg") or "GenerationRule Schema 검증 실패"),
                field,
            )
        status_text = str(raw_status) if raw_status is not None else None
        return sorted(
            (replace(issue, rule_status=status_text) for issue in issues),
            key=lambda item: (
                SEVERITY_ORDER.get(item.severity, 99),
                item.code,
                item.field or "",
            ),
        )

    data = validated_rule.model_dump(mode="python")
    status = validated_rule.status
    executable = bool(data.get("executable"))
    manual_review = bool(data.get("manual_review_required"))
    strict_execution = bool(executable and status in STRICT_EXECUTION_STATUSES)
    runtime_severity = "error" if strict_execution else "warning"

    if status == "draft_auto" and not manual_review:
        add(
            "warning",
            "draft_without_manual_review",
            "draft_auto Rule은 manual_review_required=True가 안전합니다.",
            "manual_review_required",
        )

    if executable and manual_review:
        add(
            "info",
            "executable_pending_review",
            "기계적으로 실행 가능하지만 수동 검토가 남아 있습니다.",
            "executable",
        )

    parameters = _mapping(data.get("parameter_spec"))
    symbols = _mapping(data.get("symbol_spec"))
    constraints = _list(data.get("constraints"))
    construction = _mapping(data.get("construction"))
    answer_spec = _mapping(data.get("answer_spec"))
    validation = _mapping(data.get("validation"))

    if not parameters and not symbols:
        add(
            "warning",
            "no_declared_inputs",
            "샘플링 파라미터와 수학 기호가 모두 비어 있습니다.",
            "parameter_spec",
        )

    declared_names = set(parameters) | set(symbols)

    required_objects = {
        str(item) for item in _list(construction.get("required_objects"))
    }
    missing_objects = sorted(required_objects - declared_names)
    if missing_objects:
        add(
            runtime_severity,
            "required_object_not_declared",
            "required_objects에 있지만 parameter_spec/symbol_spec에 없는 이름: "
            + ", ".join(missing_objects),
            "construction.required_objects",
        )

    templates = [
        item
        for key in ("text_templates", "latex_templates")
        for item in _list(construction.get(key))
        if isinstance(item, str)
    ]
    placeholder_names = set().union(*(_jinja_roots(item) for item in templates)) if templates else set()
    missing_placeholders = sorted(placeholder_names - declared_names)
    if missing_placeholders:
        add(
            runtime_severity,
            "template_variable_not_declared",
            "Jinja Template에서 사용했지만 선언되지 않은 이름: "
            + ", ".join(missing_placeholders),
            "construction.text_templates",
        )

    builder_expression = construction.get("builder_expression")
    answer_expression = answer_spec.get("expression")
    validators = _list(validation.get("validators"))

    if executable:
        if not _is_nonempty_text(builder_expression):
            add(
                runtime_severity,
                "executable_without_builder_expression",
                "executable=True인데 builder_expression이 없습니다. operation "
                "handler로 생성한다면 실행 레지스트리 검사가 필요합니다.",
                "construction.builder_expression",
            )
        if not _is_nonempty_text(answer_expression):
            add(
                runtime_severity,
                "executable_without_answer_expression",
                "executable=True인데 answer_spec.expression이 없습니다.",
                "answer_spec.expression",
            )
        if not templates:
            add(
                runtime_severity,
                "executable_without_template",
                "executable=True인데 문제 문장/LaTeX Template이 없습니다.",
                "construction.text_templates",
            )
        if not validators:
            add(
                runtime_severity,
                "executable_without_validator",
                "executable=True인데 Validator가 없습니다.",
                "validation.validators",
            )

    for field, expression in (
        ("construction.builder_expression", builder_expression),
        ("answer_spec.expression", answer_expression),
    ):
        if _is_nonempty_text(expression):
            issues.extend(
                _analyze_python_expression(
                    expression,
                    parameters=declared_names,
                    strict_execution=strict_execution,
                    rule_id=rule_id,
                    field=field,
                )
            )

    for name, raw_spec in parameters.items():
        spec = _mapping(raw_spec)
        derived = _mapping(spec.get("derived"))
        expression = derived.get("expression")
        if _is_nonempty_text(expression):
            issues.extend(
                _analyze_python_expression(
                    expression,
                    parameters=declared_names,
                    strict_execution=strict_execution,
                    rule_id=rule_id,
                    field=f"parameter_spec.{name}.derived.expression",
                )
            )

    for index, constraint in enumerate(constraints):
        issues.extend(
            _validate_constraint(
                constraint,
                index=index,
                declared_names=declared_names,
                strict_execution=strict_execution,
                rule_id=rule_id,
            )
        )

    for name, raw_spec in parameters.items():
        spec = _mapping(raw_spec)
        parameter_type = spec.get("type")
        if executable and parameter_type in {"matrix", "vector"} and not _has_shape_spec(spec):
            add(
                "warning",
                "parameter_shape_unspecified",
                f"실행 Rule의 {parameter_type} 파라미터 '{name}'에 크기 규칙이 없습니다.",
                f"parameter_spec.{name}",
            )

    source_formula_ids = [
        item for item in _list(data.get("source_formula_ids")) if item
    ]
    if executable and len(source_formula_ids) > 1 and not data.get("primary_formula_id"):
        add(
            "warning",
            "primary_formula_missing",
            "공식이 여러 개인데 primary_formula_id가 없어 첫 공식이 잘못 선택될 수 있습니다.",
            "primary_formula_id",
        )

    issues.extend(
        _validate_operation_requirements(
            data,
            parameters=parameters,
            constraints=constraints,
            strict_execution=strict_execution,
            rule_id=rule_id,
        )
    )

    status_text = str(status)
    return sorted(
        (replace(issue, rule_status=status_text) for issue in issues),
        key=lambda item: (
            SEVERITY_ORDER.get(item.severity, 99),
            item.code,
            item.field or "",
        ),
    )


def ensure_generation_rule_valid(
    rule: Mapping[str, Any] | Any,
    *,
    fail_on_warnings: bool = False,
) -> list[ValidationIssue]:
    """Rule을 검사하고 차단 이슈가 있으면 예외를 발생시킨다."""

    issues = validate_generation_rule(rule)
    blocking = [
        issue
        for issue in issues
        if issue.severity == "error"
        or (fail_on_warnings and issue.severity == "warning")
    ]
    if blocking:
        raise GenerationRuleValidationError(blocking)
    return issues


def _resolve_input_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def _catalog_files(paths: Sequence[Path]) -> list[Path]:
    files: list[Path] = []
    for raw_path in paths:
        path = _resolve_input_path(raw_path)
        if path.is_dir():
            files.extend(
                child
                for child in sorted(path.glob("*.json"))
                if child.name != "manifest.json"
            )
        elif path.is_file():
            if path.name != "manifest.json":
                files.append(path)
        else:
            raise FileNotFoundError(f"GenerationRule 경로가 없습니다: {path}")
    return list(dict.fromkeys(files))


def validate_catalog_files(
    paths: Sequence[Path],
    *,
    subject_filter: str | None = None,
    status_filter: set[str] | None = None,
) -> list[ValidationIssue]:
    """하나 이상의 catalog 파일을 검사하며 전역 중복도 확인한다."""

    issues: list[ValidationIssue] = []
    seen_rule_ids: dict[str, str] = {}
    seen_problem_types: dict[tuple[str, str], str] = {}

    for path in _catalog_files(paths):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            issues.append(
                ValidationIssue(
                    "error",
                    "catalog_read_error",
                    str(exc),
                    source_path=str(path),
                )
            )
            continue

        if not isinstance(raw, Mapping):
            issues.append(
                ValidationIssue(
                    "error",
                    "invalid_catalog_type",
                    "Catalog 최상위 값은 JSON object여야 합니다.",
                    source_path=str(path),
                )
            )
            continue

        rules = raw.get("rules")
        if not isinstance(rules, list):
            issues.append(
                ValidationIssue(
                    "error",
                    "rules_array_missing",
                    "Catalog에 rules 배열이 없습니다.",
                    source_path=str(path),
                )
            )
            continue

        rule_count = raw.get("rule_count")
        if rule_count != len(rules):
            issues.append(
                ValidationIssue(
                    "error",
                    "rule_count_mismatch",
                    f"rule_count={rule_count!r}, 실제 rules={len(rules)}",
                    source_path=str(path),
                )
            )

        for raw_rule in rules:
            if not isinstance(raw_rule, Mapping):
                issues.append(
                    ValidationIssue(
                        "error",
                        "invalid_rule_type",
                        "rules 항목은 JSON object여야 합니다.",
                        source_path=str(path),
                    )
                )
                continue

            subject_id = str(raw_rule.get("subject_id") or "")
            if subject_filter and subject_id != subject_filter:
                continue
            if status_filter and raw_rule.get("status") not in status_filter:
                continue

            rule_id = str(raw_rule.get("rule_id") or "<unknown>")
            problem_type = str(raw_rule.get("problem_type") or "")

            previous = seen_rule_ids.get(rule_id)
            if previous is not None:
                issues.append(
                    ValidationIssue(
                        "error",
                        "duplicate_rule_id",
                        f"같은 rule_id가 중복됐습니다. 최초 위치: {previous}",
                        rule_id,
                        "rule_id",
                        str(path),
                    )
                )
            else:
                seen_rule_ids[rule_id] = str(path)

            pair = (subject_id, problem_type)
            previous = seen_problem_types.get(pair)
            if previous is not None:
                issues.append(
                    ValidationIssue(
                        "error",
                        "duplicate_subject_problem_type",
                        "같은 subject_id/problem_type Rule이 중복됐습니다. "
                        f"최초 위치: {previous}",
                        rule_id,
                        "problem_type",
                        str(path),
                    )
                )
            else:
                seen_problem_types[pair] = str(path)

            issues.extend(
                replace(issue, source_path=str(path))
                for issue in validate_generation_rule(raw_rule)
            )

    return sorted(
        issues,
        key=lambda item: (
            SEVERITY_ORDER.get(item.severity, 99),
            item.source_path or "",
            item.rule_id,
            item.code,
        ),
    )


def _print_text_report(issues: Sequence[ValidationIssue]) -> None:
    for issue in issues:
        location = issue.rule_id
        if issue.field:
            location += f"::{issue.field}"
        print(
            f"[{issue.severity.upper():7}] "
            f"[{issue.code}] {location} - {issue.message}"
        )

    counts = Counter(issue.severity for issue in issues)
    print()
    print("=== GenerationRule 정적 검증 결과 ===")
    print(f"errors:   {counts.get('error', 0)}")
    print(f"warnings: {counts.get('warning', 0)}")
    print(f"info:     {counts.get('info', 0)}")

    by_status: Counter[tuple[str, str]] = Counter(
        ((issue.rule_status or "catalog"), issue.severity) for issue in issues
    )
    if by_status:
        print()
        print("--- status별 issue 수 ---")
        for status in sorted({status for status, _ in by_status}):
            print(
                f"{status:16} "
                f"errors={by_status[(status, 'error')]:4}  "
                f"warnings={by_status[(status, 'warning')]:4}  "
                f"info={by_status[(status, 'info')]:4}"
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="GenerationRule catalog의 구조와 실행 전제조건을 정적으로 검사합니다."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="검사할 catalog 파일 또는 디렉터리. 기본값: data/generation_rules",
    )
    parser.add_argument(
        "--subject",
        default=None,
        help="특정 subject_id만 검사합니다.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="warning도 실패(exit code 1)로 처리합니다.",
    )
    parser.add_argument(
        "--status",
        action="append",
        choices=tuple(sorted(VALID_STATUSES)),
        default=None,
        help="특정 status만 검사합니다. 여러 번 지정할 수 있습니다.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        dest="output_format",
        help="출력 형식",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = args.paths or [DEFAULT_RULE_DIR]

    try:
        issues = validate_catalog_files(
            paths,
            subject_filter=args.subject,
            status_filter=set(args.status) if args.status else None,
        )
    except (OSError, ValueError) as exc:
        print(f"[FAIL] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    if args.output_format == "json":
        print(
            json.dumps(
                {
                    "issues": [asdict(issue) for issue in issues],
                    "summary": dict(Counter(issue.severity for issue in issues)),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        _print_text_report(issues)

    has_errors = any(issue.severity == "error" for issue in issues)
    has_warnings = any(issue.severity == "warning" for issue in issues)
    return 1 if has_errors or (args.strict and has_warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
