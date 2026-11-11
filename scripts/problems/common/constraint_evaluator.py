"""여러 과목에서 공유하는 문제 생성 조건 Evaluator.

배치 생성 코드에서 사용하는 파일이다.

역할
----
- 샘플링된 파라미터가 GenerationRule / ProblemTemplate의 Constraint를 만족하는지 검사한다.
- 문자열 Constraint와 구조화 Constraint를 모두 지원한다.
- Python eval()을 사용하지 않고 AST 화이트리스트 방식으로 허용된 수학 표현만 실행한다.
- 공통 비교·논리 연산과 선형대수 조건을 실제로 계산한다.
- 정답 자체의 정확성 검증은 math_validators.py가 담당한다.

현재 지원하는 대표 표현
-------------------------
- det(A) != 0
- A.det() != 0
- rank(A) == 3
- A.rank() == A.cols
- A.cols == B.rows
- source_row < n
- is_square(A)
- is_symmetric(A)
- is_invertible(A)
- is_full_rank(A)
- is_linearly_independent(V)
- is_orthogonal(Q)
- is_positive_definite(A)
- is_positive_semidefinite(A)
- is_diagonal(A)
- is_diagonalizable(A)
- is_diagonalizable(A, field="complex")
- supports_lu_without_pivoting(A)
- b.dot(b) > 0
- and / or / not

지원하지 않는 표현은 조용히 통과시키지 않고 ConstraintEvaluationError를 발생시킨다.
미확정 기호는 필요한 성질이 증명될 때만 허용한다. 대각화 검사는 수치 행렬만 받는다.
정확한 분수는 1/10처럼 작성한다. 소수 리터럴과 외부 float는 근삿값으로 유지한다.
구조화 대각화의 field는 rule.args=[{"field": "complex"}]로 지정한다.
operator="diagonal"은 대각행렬 검사이다. 대각화 의미의 구형 Rule은
operator="diagonalizable"로 명시적으로 수정해야 한다.
"""

from __future__ import annotations

import ast
from itertools import combinations
from numbers import Integral
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from functools import wraps
from typing import Any

import sympy as sp

from app.schemas.generation_rule import (ConstraintSpec,
                                         StructuredConstraintSpec)
from app.schemas.problem_template import ConstraintTemplate

ConstraintLike = ConstraintSpec | ConstraintTemplate


class ConstraintEvaluationError(RuntimeError):
    """Constraint 자체를 해석하거나 실행할 수 없을 때 사용하는 예외."""


@dataclass(frozen=True, slots=True)
class ConstraintResult:
    """단일 Constraint 평가 결과."""

    passed: bool
    constraint_id: str | None = None
    on_failure: str = "resample"
    message: str | None = None
    observed: Any = None


@dataclass(frozen=True, slots=True)
class ConstraintReport:
    """한 번 생성한 파라미터 세트의 전체 조건 검사 결과."""

    passed: bool
    results: list[ConstraintResult] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Public evaluation API
# ---------------------------------------------------------------------------


def evaluate_constraints(
    constraints: Sequence[ConstraintLike],
    values: Mapping[str, Any],
    *,
    scope: str = "generation",
) -> ConstraintReport:
    """현재 scope에 해당하는 Constraint를 모두 평가한다.

    규칙
    ----
    - 구조화 Constraint는 expression.scope가 generation / validation / both인지 확인한다.
    - 기존 문자열 Constraint에는 scope 정보가 없으므로 generation 조건으로 취급한다.
    - required=True 조건이 하나라도 실패하면 전체 report.passed=False가 된다.
    - 지원하지 않거나 해석할 수 없는 필수 조건을 임의로 통과시키지 않는다.
    - 구조화 Constraint의 on_failure 값은 결과에 그대로 보존한다.
    """

    if scope not in {"generation", "validation", "both"}:
        raise ValueError(
            "scope는 'generation', 'validation', 'both' 중 하나여야 합니다."
        )

    results: list[ConstraintResult] = []
    overall_passed = True

    for constraint in constraints:
        expression = getattr(constraint, "expression", None)

        if isinstance(expression, StructuredConstraintSpec):
            constraint_scope = expression.scope
        else:
            # Legacy 문자열 Constraint에는 scope 필드가 없었다.
            constraint_scope = "generation"

        if scope != "both" and constraint_scope not in {scope, "both"}:
            continue

        result = evaluate_constraint(
            constraint,
            values,
        )
        results.append(result)

        required = bool(
            getattr(
                constraint,
                "required",
                True,
            )
        )

        if required and not result.passed:
            overall_passed = False

    return ConstraintReport(
        passed=overall_passed,
        results=results,
    )


def evaluate_constraint(
    constraint: ConstraintLike,
    values: Mapping[str, Any],
) -> ConstraintResult:
    """구조화 Constraint와 기존 문자열 Constraint를 구분해 실행한다."""

    expression = getattr(
        constraint,
        "expression",
        None,
    )

    if expression is None:
        raise ConstraintEvaluationError(
            "Constraint expression이 없습니다."
        )

    description = getattr(
        constraint,
        "description",
        None,
    )

    if isinstance(
        expression,
        StructuredConstraintSpec,
    ):
        result = evaluate_structured_constraint(
            expression,
            values,
        )

        message = (
            description
            or expression.description
            or result.message
        )

        return ConstraintResult(
            passed=result.passed,
            constraint_id=expression.constraint_id,
            on_failure=expression.on_failure,
            message=message,
            observed=result.observed,
        )

    if isinstance(expression, str):
        result = evaluate_string_constraint(
            expression,
            values,
        )

        return ConstraintResult(
            passed=result.passed,
            constraint_id=None,
            on_failure="resample",
            message=description or result.message,
            observed=result.observed,
        )

    raise ConstraintEvaluationError(
        "Constraint expression은 문자열 또는 "
        "StructuredConstraintSpec이어야 합니다. "
        f"현재 타입={type(expression).__name__}"
    )


def evaluate_structured_constraint(
    constraint: StructuredConstraintSpec,
    values: Mapping[str, Any],
) -> ConstraintResult:
    """구조화된 left/operator/right 또는 args 조건을 검사한다."""

    rule = constraint.rule

    try:
        passed, observed = _evaluate_structured_rule(
            rule,
            values,
        )
    except ConstraintEvaluationError:
        raise
    except Exception as exc:
        raise ConstraintEvaluationError(
            f"구조화 Constraint 실행 중 오류가 발생했습니다: "
            f"{constraint.constraint_id}"
        ) from exc

    return ConstraintResult(
        passed=passed,
        constraint_id=constraint.constraint_id,
        on_failure=constraint.on_failure,
        message=constraint.description,
        observed=observed,
    )


def evaluate_string_constraint(expression: str, values: Mapping[str, Any]) -> ConstraintResult:
    """문자열 조건을 평가하고 실행 오류를 통일한다."""
    try:
        return _evaluate_string_constraint_impl(expression, values)
    except ConstraintEvaluationError:
        raise
    except Exception as exc:
        raise ConstraintEvaluationError(
            f"표현 실행에 실패했습니다: {expression!r} ({type(exc).__name__})"
        ) from exc


def _evaluate_string_constraint_impl(
    expression: str,
    values: Mapping[str, Any],
) -> ConstraintResult:
    """기존 문자열 조건을 제한된 문법으로 안전하게 검사한다.

    Python eval()은 사용하지 않는다.
    AST를 파싱한 뒤 허용된 노드와 함수만 직접 실행한다.
    """

    expression = expression.strip()

    if not expression:
        raise ConstraintEvaluationError(
            "빈 Constraint expression입니다."
        )

    # 일부 과거 데이터의 자연어형 비교 연산을 하위 호환으로 처리한다.
    textual = _split_textual_comparison(
        expression
    )

    if textual is not None:
        left_text, operator, right_text = textual

        left = resolve_operand(
            left_text,
            values,
        )
        right = resolve_operand(
            right_text,
            values,
        )

        passed = _compare_values(
            left,
            operator,
            right,
        )

        return ConstraintResult(
            passed=passed,
            message=expression,
            observed={
                "left": left,
                "operator": operator,
                "right": right,
            },
        )

    try:
        parsed = ast.parse(
            expression,
            mode="eval",
        )
    except SyntaxError as exc:
        raise ConstraintEvaluationError(
            f"지원하지 않는 Constraint 문법입니다: {expression}"
        ) from exc

    result = _eval_ast_node(
        parsed.body,
        values,
    )

    passed = _to_bool(
        result,
        context=expression,
    )

    return ConstraintResult(
        passed=passed,
        message=expression,
        observed=result,
    )


def resolve_operand(operand: Any, values: Mapping[str, Any]) -> Any:
    """피연산자를 해석하고 실행 오류를 통일한다."""
    try:
        return _resolve_operand_impl(operand, values)
    except ConstraintEvaluationError:
        raise
    except Exception as exc:
        raise ConstraintEvaluationError(
            f"표현 실행에 실패했습니다: {operand!r} ({type(exc).__name__})"
        ) from exc


def _resolve_operand_impl(
    operand: Any,
    values: Mapping[str, Any],
) -> Any:
    """A.cols, det(A), A.rank(), b.dot(b) 등의 표현을 실제 값으로 바꾼다."""

    if not isinstance(operand, str):
        return operand

    expression = operand.strip()

    if not expression:
        raise ConstraintEvaluationError(
            "빈 operand는 사용할 수 없습니다."
        )

    try:
        parsed = ast.parse(
            expression,
            mode="eval",
        )
    except SyntaxError as exc:
        raise ConstraintEvaluationError(
            f"지원하지 않는 operand 문법입니다: {operand}"
        ) from exc

    return _eval_ast_node(
        parsed.body,
        values,
    )


# ---------------------------------------------------------------------------
# Linear algebra predicates
# ---------------------------------------------------------------------------


def is_square(matrix: Any) -> bool:
    """정사각행렬인지 검사한다."""

    matrix = _as_matrix(matrix)

    return matrix.rows == matrix.cols


def is_diagonal(matrix: Any) -> bool:
    """정사각행렬의 비대각 원소가 모두 0인지 검사한다."""
    matrix = _as_matrix(matrix)
    if not is_square(matrix):
        return False
    unknown = False
    for row in range(matrix.rows):
        for col in range(matrix.cols):
            if row == col:
                continue
            zero = _is_zero(matrix[row, col])
            if zero is False:
                return False
            unknown |= zero is None
    if unknown:
        raise ConstraintEvaluationError("대각행렬 여부를 확정할 수 없습니다.")
    return True


def is_symmetric(matrix: Any) -> bool:
    """실수 정사각행렬이며 A == A.T인지 검사한다."""

    matrix = _as_matrix(matrix)

    if not is_square(matrix):
        return False

    for element in matrix:
        if element.is_real is False:
            return False
        if element.is_real is not True:
            raise ConstraintEvaluationError("실수 행렬인지 확정할 수 없습니다.")

    difference = matrix - matrix.T

    for value in difference:
        zero = _is_zero(value)

        if zero is False:
            return False

        if zero is None:
            raise ConstraintEvaluationError(
                "대칭 여부를 확정할 수 없는 행렬 원소가 있습니다."
            )

    return True


def is_invertible(matrix: Any) -> bool:
    """정사각행렬이며 det(A) != 0인지 검사한다."""

    matrix = _as_matrix(matrix)

    if not is_square(matrix):
        return False

    determinant = sp.simplify(
        matrix.det()
    )
    zero = _is_zero(
        determinant
    )

    if zero is True:
        return False

    if zero is False:
        return True

    raise ConstraintEvaluationError(
        "행렬식이 0인지 확정할 수 없어 가역성을 판정할 수 없습니다."
    )


def is_full_rank(matrix: Any) -> bool:
    """rank(A) == min(A.rows, A.cols)인지 검사한다."""

    matrix = _as_matrix(matrix)

    return _has_rank_at_least(matrix, min(matrix.rows, matrix.cols))


def is_linearly_independent(
    vectors: Any,
) -> bool:
    """벡터를 열로 쌓아 rank가 벡터 개수와 같은지 검사한다.

    Matrix가 직접 들어오면 각 column을 하나의 벡터로 본다.
    """

    if isinstance(
        vectors,
        sp.MatrixBase,
    ):
        matrix = vectors

    elif isinstance(
        vectors,
        Sequence,
    ) and not isinstance(
        vectors,
        (str, bytes),
    ):
        columns: list[sp.MatrixBase] = []

        for vector in vectors:
            column = _as_column_vector(
                vector
            )
            columns.append(column)

        if not columns:
            return True

        dimension = columns[0].rows

        if any(
            column.rows != dimension
            for column in columns
        ):
            raise ConstraintEvaluationError(
                "선형독립성을 검사할 벡터들의 차원이 서로 다릅니다."
            )

        matrix = sp.Matrix.hstack(
            *columns
        )

    else:
        raise ConstraintEvaluationError(
            "선형독립성 검사는 Matrix 또는 벡터 Sequence가 필요합니다."
        )

    return _has_rank_at_least(matrix, matrix.cols)


def is_orthogonal(matrix: Any) -> bool:
    """실수 정사각행렬이며 A.T * A == I인지 검사한다."""

    matrix = _as_matrix(matrix)

    if not is_square(matrix):
        return False

    for element in matrix:
        if element.is_real is False:
            return False
        if element.is_real is not True:
            raise ConstraintEvaluationError("실수 행렬인지 확정할 수 없습니다.")

    product = matrix.T * matrix
    identity = sp.eye(
        matrix.cols
    )

    return _matrix_equal(
        product,
        identity,
    )


def is_positive_definite(
    matrix: Any,
) -> bool:
    """실수 대칭행렬의 양의 정부호 여부를 Sylvester 기준으로 검사한다."""

    matrix = _as_matrix(matrix)

    if not is_symmetric(matrix):
        return False

    # 실수 대칭행렬에서 모든 leading principal minor > 0 이면
    # 양의 정부호라는 Sylvester criterion을 사용한다.
    for size in range(
        1,
        matrix.rows + 1,
    ):
        minor = matrix[
            :size,
            :size,
        ].det()

        relation = _compare_ordered(
            sp.simplify(minor),
            ">",
            sp.Integer(0),
        )

        if relation is False:
            return False

    return True


def is_positive_semidefinite(
    matrix: Any,
) -> bool:
    """실수 대칭행렬의 양의 반정부호 여부를 검사한다."""

    matrix = _as_matrix(matrix)

    if not is_symmetric(matrix):
        return False

    property_value = getattr(
        matrix,
        "is_positive_semidefinite",
        None,
    )

    if property_value is True:
        return True

    if property_value is False:
        return False

    # SymPy가 직접 결정하지 못하는 경우 실수 대칭행렬의 고윳값을 확인한다.
    eigenvalues = matrix.eigenvals()

    for eigenvalue in eigenvalues:
        result = _compare_ordered(
            sp.simplify(eigenvalue),
            ">=",
            sp.Integer(0),
        )

        if result is False:
            return False

    return True


def _diagonalization_options(config: Any) -> dict[str, str]:
    """임의 keyword나 **kwargs를 허용하지 않고 field만 검사한다."""
    if not isinstance(config, Mapping) or set(config) != {"field"}:
        raise ConstraintEvaluationError("대각화 설정은 field 하나만 포함해야 합니다.")
    value = config["field"]
    if not isinstance(value, str) or value.strip().lower() not in {"real", "complex", "r", "rr", "c", "cc"}:
        raise ConstraintEvaluationError("field는 'real' 또는 'complex'여야 합니다.")
    return {"field": value.strip().lower()}


def is_diagonalizable(
    matrix: Any,
    *,
    field: str = "real",
) -> bool:
    """지정된 수 체계에서 대각화 가능한지 검사한다."""

    matrix = _as_matrix(matrix)

    if not is_square(matrix):
        return False

    normalized_field = field.strip().lower()

    if normalized_field in {
        "real",
        "r",
        "rr",
    }:
        reals_only = True

    elif normalized_field in {
        "complex",
        "c",
        "cc",
    }:
        reals_only = False

    else:
        raise ConstraintEvaluationError(
            "field는 'real' 또는 'complex'여야 합니다."
        )

    if matrix.free_symbols:
        raise ConstraintEvaluationError("대각화 검사는 실제 값이 대입된 행렬이 필요합니다.")
    try:
        result = matrix.is_diagonalizable(reals_only=reals_only)
    except Exception as exc:
        raise ConstraintEvaluationError("지정한 수 체계에서 대각화 여부를 계산할 수 없습니다.") from exc
    return _to_bool(result, context="diagonalizable")


def supports_lu_without_pivoting(
    matrix: Any,
) -> bool:
    """행 교환 없이 표준 LU 분해를 적용할 수 있는지 검사한다.

    현재 생성 파이프라인의 유일해 문제를 기준으로
    모든 leading principal minor가 0이 아닌 정사각행렬을 허용한다.
    """

    matrix = _as_matrix(matrix)

    if not is_square(matrix):
        return False

    for size in range(
        1,
        matrix.rows + 1,
    ):
        leading_minor = sp.simplify(
            matrix[
                :size,
                :size,
            ].det()
        )

        zero = _is_zero(
            leading_minor
        )

        if zero is True:
            return False

        if zero is None:
            raise ConstraintEvaluationError(
                "LU pivot 조건을 확정할 수 없는 leading principal minor가 있습니다."
            )

    return True


# ---------------------------------------------------------------------------
# Structured rule evaluator
# ---------------------------------------------------------------------------


def _evaluate_structured_rule(
    rule: Any,
    values: Mapping[str, Any],
) -> tuple[bool, Any]:
    """ConstraintRuleSpec 또는 같은 구조의 dict를 실행한다."""

    if isinstance(
        rule,
        Mapping,
    ):
        left = rule.get(
            "left"
        )
        operator = rule.get(
            "operator"
        )
        right = rule.get(
            "right"
        )
        args = list(
            rule.get(
                "args",
                [],
            )
            or []
        )

    else:
        left = getattr(
            rule,
            "left",
            None,
        )
        operator = getattr(
            rule,
            "operator",
            None,
        )
        right = getattr(
            rule,
            "right",
            None,
        )
        args = list(
            getattr(
                rule,
                "args",
                [],
            )
            or []
        )

    if not isinstance(
        operator,
        str,
    ) or not operator.strip():
        raise ConstraintEvaluationError(
            "Structured Constraint rule에 operator가 없습니다."
        )

    normalized = _normalize_operator(
        operator
    )

    # 논리 연산
    if normalized in {
        "and",
        "or",
        "not",
    }:
        operands = args

        if not operands:
            operands = [
                item
                for item in (
                    left,
                    right,
                )
                if item is not None
            ]

        if normalized == "not":
            if len(operands) != 1:
                raise ConstraintEvaluationError(
                    "'not' 연산자는 조건 하나만 받아야 합니다."
                )

            value = _evaluate_condition_operand(
                operands[0],
                values,
            )

            result = not value

            return result, {
                "operator": operator,
                "args": operands,
                "resolved": [
                    value
                ],
            }

        if not operands:
            raise ConstraintEvaluationError(
                f"'{normalized}' 연산자에 조건이 없습니다."
            )

        # 실제로 평가한 값만 기록한다. 뒤의 조건은 실행하지 않을 수 있다.
        resolved = []
        result = normalized == "and"
        for operand in operands:
            value = _evaluate_condition_operand(operand, values)
            resolved.append(value)
            result = value
            if (normalized == "and" and not value) or (normalized == "or" and value):
                break

        return result, {
            "operator": operator,
            "args": operands,
            "resolved": resolved,
        }

    left_value = resolve_operand(
        left,
        values,
    )

    # 새 과목의 다중 인자 조건. left가 첫 인자이며 args가 나머지 인자다.
    # 예: {left:'f', operator:'is_defined_on_domain', args:['x','D'], right:true}
    if normalized in NEW_PREDICATES:
        arguments = [left_value, *[resolve_operand(arg, values) for arg in args]]
        actual = _decide(NEW_PREDICATES[normalized](*arguments), normalized)
        expected = True if right is None else _to_bool(resolve_operand(right, values), context='predicate right')
        return actual == expected, {'operator': operator, 'actual': actual, 'expected': expected}

    # 선형대수 property 연산자
    property_predicates = {
        "square": is_square,
        "is_square": is_square,
        "symmetric": is_symmetric,
        "is_symmetric": is_symmetric,
        "invertible": is_invertible,
        "is_invertible": is_invertible,
        "full_rank": is_full_rank,
        "is_full_rank": is_full_rank,
        "linearly_independent": is_linearly_independent,
        "is_linearly_independent": is_linearly_independent,
        "orthogonal": is_orthogonal,
        "is_orthogonal": is_orthogonal,
        "positive_definite": is_positive_definite,
        "is_positive_definite": is_positive_definite,
        "positive_semidefinite": is_positive_semidefinite,
        "positive_semi_definite": is_positive_semidefinite,
        "is_positive_semidefinite": is_positive_semidefinite,
        "is_positive_semi_definite": is_positive_semidefinite,
        "diagonalizable": is_diagonalizable,
        "is_diagonalizable": is_diagonalizable,
        # 구형 Rule에서 대각화 의미로 diagonal을 썼다면 해당 Rule을
        # diagonalizable로 변경해야 한다. 여기서는 의미를 추측하지 않는다.
        "diagonal": is_diagonal,
        "is_diagonal": is_diagonal,
        "lu_without_pivoting": supports_lu_without_pivoting,
        "supports_lu_without_pivoting": supports_lu_without_pivoting,
    }

    if normalized in property_predicates:
        options = {}
        if args:
            # Schema 변경 없이 수 체계를 전달한다.
            # rule: {left: "A", operator: "diagonalizable",
            #        args: [{field: "complex"}]}
            if normalized not in {"diagonalizable", "is_diagonalizable"} or len(args) != 1:
                raise ConstraintEvaluationError("이 property에는 args 설정을 사용할 수 없습니다.")
            options = _diagonalization_options(args[0])
        actual = property_predicates[normalized](left_value, **options)

        expected = (
            True
            if right is None
            else _to_bool(
                resolve_operand(
                    right,
                    values,
                ),
                context=(
                    f"structured right operand: "
                    f"{right}"
                ),
            )
        )

        return actual == expected, {
            "left": left_value,
            "operator": operator,
            "actual": actual,
            "expected": expected,
        }

    right_value = resolve_operand(
        right,
        values,
    )

    passed = _compare_values(
        left_value,
        normalized,
        right_value,
    )

    return passed, {
        "left": left_value,
        "operator": operator,
        "right": right_value,
    }


def _evaluate_condition_operand(
    operand: Any,
    values: Mapping[str, Any],
) -> bool:
    """논리 연산의 하위 조건 하나를 Boolean으로 평가한다."""

    if isinstance(
        operand,
        Mapping,
    ) and "operator" in operand:
        result, _ = _evaluate_structured_rule(
            operand,
            values,
        )
        return result

    if hasattr(
        operand,
        "operator",
    ):
        result, _ = _evaluate_structured_rule(
            operand,
            values,
        )
        return result

    if isinstance(
        operand,
        str,
    ):
        # 비교식 또는 논리식이면 전체 Constraint로 평가한다.
        try:
            parsed = ast.parse(
                operand,
                mode="eval",
            )
        except SyntaxError:
            parsed = None

        if parsed is not None and isinstance(
            parsed.body,
            (
                ast.Compare,
                ast.BoolOp,
                ast.UnaryOp,
                ast.Call,
            ),
        ):
            try:
                return evaluate_string_constraint(
                    operand,
                    values,
                ).passed
            except ConstraintEvaluationError:
                # 단순 이름/함수 결과인 경우 아래 resolve_operand 경로로 처리한다.
                pass

    resolved = resolve_operand(
        operand,
        values,
    )

    return _to_bool(
        resolved,
        context=str(
            operand
        ),
    )


# ---------------------------------------------------------------------------
# Safe AST evaluator
# ---------------------------------------------------------------------------


def _eval_ast_node(
    node: ast.AST,
    values: Mapping[str, Any],
) -> Any:
    """허용된 AST 노드만 재귀적으로 실행한다."""

    if isinstance(
        node,
        ast.Constant,
    ):
        # bool은 int의 하위 타입이므로 정확히 int인 리터럴만 변환한다.
        # 소수 리터럴(0.1 등)은 근삿값으로 유지한다. 정확한 값은 1/10 사용.
        if type(node.value) is int:
            return sp.Integer(node.value)
        return node.value

    if isinstance(
        node,
        ast.Name,
    ):
        if node.id in values:
            return values[
                node.id
            ]

        constants = {
            "True": True,
            "False": False,
            "None": None,
            "pi": sp.pi,
            "E": sp.E,
            "I": sp.I,
            "oo": sp.oo,
        }

        if node.id in constants:
            return constants[
                node.id
            ]

        raise ConstraintEvaluationError(
            f"선언되지 않은 변수입니다: {node.id}"
        )

    if isinstance(
        node,
        ast.List,
    ):
        return [
            _eval_ast_node(
                element,
                values,
            )
            for element in node.elts
        ]

    if isinstance(node, ast.Dict):
        if any(key is None for key in node.keys):
            raise ConstraintEvaluationError('dict 확장은 허용하지 않습니다.')
        return {_eval_ast_node(key, values): _eval_ast_node(value, values)
                for key, value in zip(node.keys, node.values)}

    if isinstance(
        node,
        ast.Tuple,
    ):
        return tuple(
            _eval_ast_node(
                element,
                values,
            )
            for element in node.elts
        )

    if isinstance(
        node,
        ast.Attribute,
    ):
        base = _eval_ast_node(
            node.value,
            values,
        )

        if node.attr in {
            "rows",
            "cols",
            "shape",
            "T",
        }:
            matrix = _as_matrix(
                base
            )

            if node.attr == "rows":
                return matrix.rows

            if node.attr == "cols":
                return matrix.cols

            if node.attr == "shape":
                return matrix.shape

            return matrix.T

        raise ConstraintEvaluationError(
            f"허용되지 않은 attribute입니다: {node.attr}"
        )

    if isinstance(
        node,
        ast.Subscript,
    ):
        base = _eval_ast_node(
            node.value,
            values,
        )
        index = _eval_ast_node(
            node.slice,
            values,
        )

        try:
            return base[
                index
            ]
        except Exception as exc:
            raise ConstraintEvaluationError(
                "첨자 접근에 실패했습니다."
            ) from exc

    if isinstance(
        node,
        ast.Slice,
    ):
        lower = (
            _eval_ast_node(
                node.lower,
                values,
            )
            if node.lower is not None
            else None
        )
        upper = (
            _eval_ast_node(
                node.upper,
                values,
            )
            if node.upper is not None
            else None
        )
        step = (
            _eval_ast_node(
                node.step,
                values,
            )
            if node.step is not None
            else None
        )
        return slice(
            lower,
            upper,
            step,
        )

    if isinstance(
        node,
        ast.Call,
    ):
        return _eval_call(
            node,
            values,
        )

    if isinstance(
        node,
        ast.BinOp,
    ):
        left = _eval_ast_node(
            node.left,
            values,
        )
        right = _eval_ast_node(
            node.right,
            values,
        )

        if isinstance(
            node.op,
            ast.Add,
        ):
            return left + right

        if isinstance(
            node.op,
            ast.Sub,
        ):
            return left - right

        if isinstance(
            node.op,
            ast.Mult,
        ):
            return left * right

        if isinstance(
            node.op,
            ast.MatMult,
        ):
            return left @ right

        if isinstance(
            node.op,
            ast.Div,
        ):
            if right == 0:
                raise ConstraintEvaluationError("0으로 나눌 수 없습니다.")
            if isinstance(left, (Integral, sp.Integer)) and isinstance(right, (Integral, sp.Integer)):
                return sp.Integer(left) / sp.Integer(right)
            return left / right

        if isinstance(
            node.op,
            ast.FloorDiv,
        ):
            return left // right

        if isinstance(
            node.op,
            ast.Mod,
        ):
            return left % right

        if isinstance(
            node.op,
            ast.Pow,
        ):
            return left ** right

        raise ConstraintEvaluationError(
            "허용되지 않은 이항 연산입니다."
        )

    if isinstance(
        node,
        ast.UnaryOp,
    ):
        value = _eval_ast_node(
            node.operand,
            values,
        )

        if isinstance(
            node.op,
            ast.USub,
        ):
            return -value

        if isinstance(
            node.op,
            ast.UAdd,
        ):
            return +value

        if isinstance(
            node.op,
            ast.Not,
        ):
            return not _to_bool(
                value,
                context="not operand",
            )

        raise ConstraintEvaluationError(
            "허용되지 않은 단항 연산입니다."
        )

    if isinstance(
        node,
        ast.BoolOp,
    ):
        if isinstance(node.op, ast.And):
            for item in node.values:
                if not _to_bool(_eval_ast_node(item, values), context="and operand"):
                    return False
            return True

        if isinstance(node.op, ast.Or):
            for item in node.values:
                if _to_bool(_eval_ast_node(item, values), context="or operand"):
                    return True
            return False

        raise ConstraintEvaluationError(
            "허용되지 않은 논리 연산입니다."
        )

    if isinstance(
        node,
        ast.Compare,
    ):
        left = _eval_ast_node(
            node.left,
            values,
        )

        for operator_node, comparator_node in zip(
            node.ops,
            node.comparators,
            strict=True,
        ):
            right = _eval_ast_node(
                comparator_node,
                values,
            )
            operator = _comparison_operator_from_ast(
                operator_node
            )

            if not _compare_values(
                left,
                operator,
                right,
            ):
                return False

            left = right

        return True

    raise ConstraintEvaluationError(
        "허용되지 않은 Constraint 표현입니다: "
        f"{node.__class__.__name__}"
    )


def _eval_call(
    node: ast.Call,
    values: Mapping[str, Any],
) -> Any:
    """화이트리스트에 등록된 함수/메서드 호출만 실행한다."""

    options = {}
    if node.keywords:
        if not isinstance(node.func, ast.Name) or node.func.id != "is_diagonalizable":
            raise ConstraintEvaluationError("키워드 인자는 is_diagonalizable의 field만 허용합니다.")
        if len(node.keywords) != 1 or node.keywords[0].arg != "field":
            raise ConstraintEvaluationError("허용된 키워드는 field 하나입니다.")
        options = _diagonalization_options({
            "field": _eval_ast_node(node.keywords[0].value, values)
        })

    args = [
        _eval_ast_node(
            argument,
            values,
        )
        for argument in node.args
    ]

    # det(A), rank(A), is_symmetric(A) 같은 함수 호출
    if isinstance(
        node.func,
        ast.Name,
    ):
        name = node.func.id

        functions = {
            "det": _function_det,
            "rank": _function_rank,
            "transpose": _function_transpose,
            "rows": _function_rows,
            "cols": _function_cols,
            "shape": _function_shape,
            "is_square": is_square,
            "is_diagonal": is_diagonal,
            "is_symmetric": is_symmetric,
            "is_invertible": is_invertible,
            "is_full_rank": is_full_rank,
            "is_linearly_independent": is_linearly_independent,
            "is_orthogonal": is_orthogonal,
            "is_positive_definite": is_positive_definite,
            "is_positive_semidefinite": is_positive_semidefinite,
            "is_positive_semi_definite": is_positive_semidefinite,
            "is_diagonalizable": is_diagonalizable,
            "supports_lu_without_pivoting": supports_lu_without_pivoting,
            "len": len,
            "abs": abs,
            "min": min,
            "max": max,
        }
        functions.update(NEW_PREDICATES)
        functions.update({'Interval': sp.Interval, 'sin': sp.sin, 'cos': sp.cos,
                          'exp': sp.exp, 'log': sp.log, 'sqrt': sp.sqrt})

        if name not in functions:
            raise ConstraintEvaluationError(
                f"허용되지 않은 함수입니다: {name}"
            )

        try:
            return functions[
                name
            ](
                *args, **options
            )
        except ConstraintEvaluationError:
            raise
        except Exception as exc:
            raise ConstraintEvaluationError(
                f"함수 실행에 실패했습니다: {name}"
            ) from exc

    # A.rank(), A.det(), b.dot(b) 같은 제한된 메서드 호출
    if isinstance(
        node.func,
        ast.Attribute,
    ):
        owner = _eval_ast_node(
            node.func.value,
            values,
        )
        method = node.func.attr

        if method == "rank":
            _require_no_args(
                method,
                args,
            )
            return _function_rank(owner)

        if method == "det":
            _require_no_args(
                method,
                args,
            )
            matrix = _as_matrix(
                owner
            )

            if not is_square(
                matrix
            ):
                raise ConstraintEvaluationError(
                    "det() 메서드는 정사각행렬에만 사용할 수 있습니다."
                )

            return sp.simplify(
                matrix.det()
            )

        if method == "trace":
            _require_no_args(
                method,
                args,
            )
            return _as_matrix(
                owner
            ).trace()

        if method == "transpose":
            _require_no_args(
                method,
                args,
            )
            return _as_matrix(
                owner
            ).T

        if method == "norm":
            _require_no_args(
                method,
                args,
            )
            return _as_matrix(
                owner
            ).norm()

        if method == "dot":
            if len(
                args
            ) != 1:
                raise ConstraintEvaluationError(
                    "dot()은 인자 하나를 받아야 합니다."
                )

            left = _as_column_vector(
                owner
            )
            right = _as_column_vector(
                args[0]
            )

            if left.rows != right.rows:
                raise ConstraintEvaluationError(
                    "dot()에 사용한 두 벡터의 차원이 다릅니다."
                )

            return sp.simplify(
                left.dot(
                    right
                )
            )

        raise ConstraintEvaluationError(
            f"허용되지 않은 메서드입니다: {method}"
        )

    raise ConstraintEvaluationError(
        "허용되지 않은 함수 호출 형식입니다."
    )


# ---------------------------------------------------------------------------
# Comparison helpers
# ---------------------------------------------------------------------------


def _compare_values(
    left: Any,
    operator: str,
    right: Any,
) -> bool:
    """허용된 비교 연산을 실제 값에 적용한다."""

    normalized = _normalize_operator(
        operator
    )

    if normalized == "equals":
        return _values_equal(
            left,
            right,
        )

    if normalized == "not_equals":
        return not _values_equal(
            left,
            right,
        )

    if normalized in {
        "less_than",
        "less_than_or_equal",
        "greater_than",
        "greater_than_or_equal",
    }:
        symbol = {
            "less_than": "<",
            "less_than_or_equal": "<=",
            "greater_than": ">",
            "greater_than_or_equal": ">=",
        }[
            normalized
        ]

        return _compare_ordered(
            left,
            symbol,
            right,
        )

    if normalized == "in":
        try:
            return left in right
        except TypeError as exc:
            raise ConstraintEvaluationError(
                "'in' 오른쪽 값은 포함 검사가 가능한 객체여야 합니다."
            ) from exc

    if normalized == "not_in":
        try:
            return left not in right
        except TypeError as exc:
            raise ConstraintEvaluationError(
                "'not_in' 오른쪽 값은 포함 검사가 가능한 객체여야 합니다."
            ) from exc

    raise ConstraintEvaluationError(
        f"지원하지 않는 비교 연산자입니다: {operator}"
    )


def _values_equal(
    left: Any,
    right: Any,
) -> bool:
    """스칼라와 행렬의 수학적 동치 여부를 안전하게 판정한다."""

    if isinstance(
        left,
        sp.MatrixBase,
    ) or isinstance(
        right,
        sp.MatrixBase,
    ):
        try:
            left_matrix = _as_matrix(
                left
            )
            right_matrix = _as_matrix(
                right
            )
        except ConstraintEvaluationError:
            return False

        return _matrix_equal(
            left_matrix,
            right_matrix,
        )

    try:
        difference = sp.simplify(
            left - right
        )
    except Exception:
        difference = None

    if difference is not None:
        zero = _is_zero(
            difference
        )

        if zero is True:
            return True

        if zero is False:
            return False
        raise ConstraintEvaluationError("동등 여부를 확정할 수 없는 값입니다.")

    try:
        result = left == right
    except Exception as exc:
        raise ConstraintEvaluationError(
            "동등 비교를 수행할 수 없습니다."
        ) from exc

    return _to_bool(
        result,
        context=f"{left!r} == {right!r}",
    )


def _compare_ordered(
    left: Any,
    operator: str,
    right: Any,
) -> bool:
    """<, <=, >, >= 결과를 확정 가능한 Boolean으로 변환한다."""

    try:
        if operator == "<":
            result = left < right
        elif operator == "<=":
            result = left <= right
        elif operator == ">":
            result = left > right
        elif operator == ">=":
            result = left >= right
        else:
            raise ConstraintEvaluationError(
                f"지원하지 않는 순서 비교 연산자입니다: {operator}"
            )
    except TypeError as exc:
        raise ConstraintEvaluationError(
            f"순서 비교를 수행할 수 없습니다: "
            f"{left!r} {operator} {right!r}"
        ) from exc

    return _to_bool(
        result,
        context=f"{left!r} {operator} {right!r}",
    )


def _normalize_operator(
    operator: str,
) -> str:
    """여러 표기의 operator를 내부 표기로 통일한다."""

    normalized = operator.strip().lower().replace(
        "-",
        "_",
    ).replace(
        " ",
        "_",
    )

    aliases = {
        "==": "equals",
        "eq": "equals",
        "equal": "equals",
        "equals": "equals",
        "!=": "not_equals",
        "ne": "not_equals",
        "not_equal": "not_equals",
        "not_equals": "not_equals",
        "<": "less_than",
        "lt": "less_than",
        "less_than": "less_than",
        "<=": "less_than_or_equal",
        "le": "less_than_or_equal",
        "less_equal": "less_than_or_equal",
        "less_than_or_equal": "less_than_or_equal",
        ">": "greater_than",
        "gt": "greater_than",
        "greater_than": "greater_than",
        ">=": "greater_than_or_equal",
        "ge": "greater_than_or_equal",
        "greater_equal": "greater_than_or_equal",
        "greater_than_or_equal": "greater_than_or_equal",
        "&&": "and",
        "and": "and",
        "||": "or",
        "or": "or",
        "!": "not",
        "not": "not",
        "in": "in",
        "not_in": "not_in",
    }

    return aliases.get(
        normalized,
        normalized,
    )


def _comparison_operator_from_ast(
    operator: ast.cmpop,
) -> str:
    if isinstance(
        operator,
        ast.Eq,
    ):
        return "equals"

    if isinstance(
        operator,
        ast.NotEq,
    ):
        return "not_equals"

    if isinstance(
        operator,
        ast.Lt,
    ):
        return "less_than"

    if isinstance(
        operator,
        ast.LtE,
    ):
        return "less_than_or_equal"

    if isinstance(
        operator,
        ast.Gt,
    ):
        return "greater_than"

    if isinstance(
        operator,
        ast.GtE,
    ):
        return "greater_than_or_equal"

    if isinstance(
        operator,
        ast.In,
    ):
        return "in"

    if isinstance(
        operator,
        ast.NotIn,
    ):
        return "not_in"

    raise ConstraintEvaluationError(
        "허용되지 않은 비교 연산입니다."
    )


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def _as_matrix(
    value: Any,
) -> sp.MatrixBase:
    """입력값을 SymPy Matrix로 통일한다."""

    if isinstance(
        value,
        sp.MatrixBase,
    ):
        return value

    if hasattr(
        value,
        "tolist",
    ):
        value = value.tolist()

    if isinstance(
        value,
        (
            list,
            tuple,
        ),
    ):
        try:
            return sp.Matrix(
                value
            )
        except Exception as exc:
            raise ConstraintEvaluationError(
                f"행렬로 변환할 수 없습니다: {value!r}"
            ) from exc

    raise ConstraintEvaluationError(
        f"행렬 값이 아닙니다: {type(value).__name__}"
    )


def _as_column_vector(
    value: Any,
) -> sp.MatrixBase:
    """입력값을 SymPy 열벡터로 통일한다."""

    matrix = _as_matrix(
        value
    )

    if matrix.cols == 1:
        return matrix

    if matrix.rows == 1:
        return matrix.T

    raise ConstraintEvaluationError(
        "벡터로 사용할 값은 한 개의 행 또는 한 개의 열이어야 합니다."
    )


def _matrix_equal(
    left: sp.MatrixBase,
    right: sp.MatrixBase,
) -> bool:
    """두 행렬을 원소별 simplify로 비교한다."""

    if left.shape != right.shape:
        return False

    difference = left - right

    for value in difference:
        zero = _is_zero(
            value
        )

        if zero is False:
            return False

        if zero is None:
            raise ConstraintEvaluationError(
                "행렬 원소의 동치 여부를 확정할 수 없습니다."
            )

    return True


def _is_zero(value: Any) -> bool | None:
    """모든 허용된 값에서 0/비영임이 확정될 때만 bool을 반환한다.

    자유 기호의 equals(0)==False는 '항등적으로 0이 아님'이므로
    특정 샘플의 비영 증거로 사용하지 않는다.
    """
    try:
        simplified = sp.simplify(value)
    except Exception:
        return None
    if simplified.has(sp.nan, sp.zoo, sp.oo, -sp.oo):
        return None
    if simplified == 0 or simplified.is_zero is True:
        return True
    if simplified.is_zero is False:
        return False
    if simplified.free_symbols:
        return None
    try:
        result = simplified.equals(0)
    except Exception:
        return None
    return result if result is True or result is False else None


def _to_bool(
    value: Any,
    *,
    context: str,
) -> bool:
    """Python/SymPy Boolean만 명확하게 True/False로 변환한다."""

    if value is True or value == sp.S.true:
        return True

    if value is False or value == sp.S.false:
        return False

    if isinstance(
        value,
        bool,
    ):
        return value

    raise ConstraintEvaluationError(
        f"조건 결과를 True/False로 확정할 수 없습니다: "
        f"{context} -> {value!r}"
    )


def _split_textual_comparison(
    expression: str,
) -> tuple[str, str, str] | None:
    """'left equals right', 'left not equals right' 형태를 분리한다."""

    lowered = expression.lower()

    marker = " not equals "

    index = lowered.find(
        marker
    )

    if index >= 0:
        return (
            expression[
                :index
            ].strip(),
            "not_equals",
            expression[
                index + len(
                    marker
                ):
            ].strip(),
        )

    marker = " equals "

    index = lowered.find(
        marker
    )

    if index >= 0:
        return (
            expression[
                :index
            ].strip(),
            "equals",
            expression[
                index + len(
                    marker
                ):
            ].strip(),
        )

    return None


def _require_no_args(
    function_name: str,
    args: Sequence[Any],
) -> None:
    if args:
        raise ConstraintEvaluationError(
            f"{function_name}()은 인자를 받지 않습니다."
        )


def _function_det(
    value: Any,
) -> Any:
    matrix = _as_matrix(
        value
    )

    if not is_square(
        matrix
    ):
        raise ConstraintEvaluationError(
            "det()는 정사각행렬에만 사용할 수 있습니다."
        )

    return sp.simplify(
        matrix.det()
    )


def _has_rank_at_least(matrix: sp.MatrixBase, size: int) -> bool:
    """非零 minor를 증거로 rank 하한을 판정한다. 미확정은 예외로 처리한다.

    수치 행렬은 SymPy rank를 사용하고, 작은 기호 행렬에만 minor를 조사한다.
    """
    if matrix.has(sp.nan, sp.zoo, sp.oo, -sp.oo):
        raise ConstraintEvaluationError("랭크 검사에는 유한한 원소가 필요합니다.")
    if size == 0:
        return True
    if size > min(matrix.rows, matrix.cols):
        return False
    if not matrix.free_symbols:
        return int(matrix.rank()) >= size
    unknown = False
    for rows in combinations(range(matrix.rows), size):
        for cols in combinations(range(matrix.cols), size):
            zero = _is_zero(matrix.extract(rows, cols).det())
            if zero is False:
                return True
            unknown |= zero is None
    if unknown:
        raise ConstraintEvaluationError("기호의 값/가정이 부족해 랭크를 확정할 수 없습니다.")
    return False


def _function_rank(value: Any) -> int:
    matrix = _as_matrix(value)
    for size in range(min(matrix.rows, matrix.cols), 0, -1):
        if _has_rank_at_least(matrix, size):
            return size
    # 빈 행렬도 유한성 검사를 거친다.
    _has_rank_at_least(matrix, 0)
    return 0


def _function_transpose(
    value: Any,
) -> sp.MatrixBase:
    return _as_matrix(
        value
    ).T


def _function_rows(
    value: Any,
) -> int:
    return int(
        _as_matrix(
            value
        ).rows
    )


def _function_cols(
    value: Any,
) -> int:
    return int(
        _as_matrix(
            value
        ).cols
    )


def _function_shape(
    value: Any,
) -> tuple[int, int]:
    return tuple(
        _as_matrix(
            value
        ).shape
    )


# ---------------------------------------------------------------------------
# 과목별 조건 검사: 구간/영역 전체를 판정하며 임의의 몇 점만 검사하지 않는다.
# ---------------------------------------------------------------------------


def _decide(value: Any, label: str) -> bool:
    if value is True or value is sp.true:
        return True
    if value is False or value is sp.false:
        return False
    raise ConstraintEvaluationError(f'{label}: 정확한 참/거짓을 판정하지 못했습니다.')


def _subset(left: sp.Set, right: sp.Set, label: str) -> bool:
    result = left.is_subset(right)
    if result is not None:
        return _decide(result, label)
    # SymPy가 열린 구간의 합집합 포함관계에 None을 반환하는 경우에도
    # 차집합이 비었는지 정확히 계산할 수 있다. 표본점 검사는 사용하지 않는다.
    difference = left - right
    return _decide(difference.is_empty, label)


def _predicate_guard(function):
    """直接 API에서도 미지원 SymPy 계산의 예외를 동일한 오류 타입으로 제공한다."""
    @wraps(function)
    def guarded(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except ConstraintEvaluationError:
            raise
        except Exception as exc:
            raise ConstraintEvaluationError(f'{function.__name__} 판정 불능: {type(exc).__name__}: {exc}') from exc
    return guarded


def _math_expression(value: Any) -> sp.Expr:
    if isinstance(value, bool) or isinstance(value,str):
        raise ConstraintEvaluationError('파싱된 수식 또는 수치가 필요합니다. 문자열 수식을 실행하지 않습니다.')
    if isinstance(value,(Integral,float)):
        value = sp.sympify(value)
    if not isinstance(value,sp.Expr) or value.has(sp.nan,sp.zoo,sp.oo,-sp.oo):
        raise ConstraintEvaluationError('유한한 SymPy 수식이 필요합니다.')
    return value


def _real_number(value: Any) -> sp.Expr:
    value = _math_expression(value)
    if value.free_symbols or value.is_real is not True or value.is_finite is not True:
        raise ConstraintEvaluationError('유한한 실수 상수가 필요합니다.')
    return value


def _real_context(expression: Any, variable: Any, domain: Any) -> tuple[sp.Expr,sp.Symbol,sp.Set]:
    expr = _math_expression(expression)
    if not isinstance(variable,sp.Symbol) or variable.is_real is not True:
        raise ConstraintEvaluationError('real=True인 독립변수가 필요합니다.')
    if expr.free_symbols - {variable}:
        raise ConstraintEvaluationError('아직 대입되지 않은 다른 변수가 있습니다.')
    if not isinstance(domain,sp.Set):
        raise ConstraintEvaluationError('정의역에는 SymPy Set/Interval이 필요합니다.')
    if not _decide(domain.is_subset(sp.S.Reals),'실수 정의역'):
        raise ConstraintEvaluationError('정의역은 실수 집합이어야 합니다.')
    return expr,variable,domain


def _condition_set(condition: Any, variable: sp.Symbol) -> sp.Set:
    if condition is sp.true or condition is True:
        return sp.S.Reals
    if condition is sp.false or condition is False:
        return sp.S.EmptySet
    try:
        result = condition.as_set()
    except (AttributeError,NotImplementedError) as exc:
        raise ConstraintEvaluationError('부등식의 해집합을 판정할 수 없습니다.') from exc
    if result.has(sp.ConditionSet):
        raise ConstraintEvaluationError('조건의 해집합이 미확정입니다.')
    return result


def is_defined_on_domain(expression: Any, variable: Any, domain: Any) -> bool:
    """실수 다항식·유리식·exp/sin/cos/log/Abs·유리수 거듭제곱의 정의역 검사.

    SymPy의 주값 거듭제곱을 따른다. 미지원 특수함수는 예외이며 실수 세제곱근을
    별도 함수족으로 간주하지 않는다. 이미 약분된 식의 제거 가능한 구멍은 원래
    분모를 복원할 수 없으므로 Rule에 원래 분모의 조건을 별도로 보존해야 한다.
    """
    expr,x,domain = _real_context(expression,variable,domain)
    def allowed(node: sp.Expr) -> sp.Set:
        if node==x or (not node.free_symbols and node.is_real is True):
            return sp.S.Reals
        if node.is_Add or node.is_Mul:
            return sp.Intersection(*(allowed(a) for a in node.args))
        if node.is_Pow:
            base,power = node.args
            valid = allowed(base)
            if power.is_Integer:
                if power<0:
                    valid = valid-sp.solveset(base,x,domain=sp.S.Reals)
                return valid
            if power.is_Rational:
                condition = base>0 if power<0 else base>=0
                return sp.Intersection(valid,_condition_set(condition,x))
            raise ConstraintEvaluationError('정의역 검사는 정수/유리수 거듭제곱만 지원합니다.')
        if node.func in {sp.exp,sp.sin,sp.cos,sp.Abs}:
            return allowed(node.args[0])
        if node.func==sp.log:
            return sp.Intersection(allowed(node.args[0]),_condition_set(node.args[0]>0,x))
        if node.func==sp.tan:
            return allowed(node.args[0])-sp.solveset(sp.cos(node.args[0]),x,domain=sp.S.Reals)
        if isinstance(node,sp.Piecewise):
            valid = sp.S.EmptySet
            remaining = domain
            for branch,condition in node.args:
                active = sp.Intersection(remaining,_condition_set(condition,x))
                valid = sp.Union(valid,sp.Intersection(active,allowed(branch)))
                remaining = remaining-active
            return valid
        raise ConstraintEvaluationError(f'정의역 검사의 미지원 함수: {node.func}')
    valid = allowed(expr)
    return _subset(domain,valid,'정의역 포함 관계')


def is_continuous_on_interval(expression: Any, variable: Any, interval: Any) -> bool:
    """끝점의 개폐를 포함한 실제 구간 전체의 연속성을 검사한다."""
    from sympy.calculus.util import continuous_domain
    expr,x,domain = _real_context(expression,variable,interval)
    if not isinstance(domain,sp.Interval):
        raise ConstraintEvaluationError('연속성 검사에는 Interval이 필요합니다.')
    if not is_defined_on_domain(expr,x,domain):
        return False
    try:
        continuous = continuous_domain(expr,x,sp.S.Reals)
    except (NotImplementedError,ValueError) as exc:
        raise ConstraintEvaluationError('해당 함수의 연속성을 판정할 수 없습니다.') from exc
    return _subset(domain,continuous,'연속 구간 포함 관계')


def is_series_convergent(term: Any, index: Any = None, start: Any = None) -> bool:
    """무한급수의 수렴 여부. sequence 샘플러의 dict 또는 일반항을 받는다."""
    if isinstance(term,Mapping):
        if index is not None or start is not None:
            raise ConstraintEvaluationError('수열 객체와 별도 index/start를 중복 지정하지 마세요.')
        index,start,term = term.get('index'),term.get('start'),term.get('term')
    if not isinstance(index,sp.Symbol) or index.is_integer is not True:
        raise ConstraintEvaluationError('급수의 정수 인덱스가 필요합니다.')
    start = _real_number(1 if start is None else start)
    if start.is_Integer is not True or start<1:
        raise ConstraintEvaluationError('급수 start는 양의 정수여야 합니다.')
    term = _math_expression(term)
    if term.free_symbols-{index}:
        raise ConstraintEvaluationError('급수에 미대입 변수가 있습니다.')
    # 수렴 판정법은 유한 개의 앞 항을 무시할 수 있다. 앞 항의 0 나눗셈을
    # 수렴으로 오판하지 않도록 양의 정수 인덱스에 있는 특이점을 먼저 검사한다.
    initial = term.subs(index,start)
    if initial.has(sp.nan,sp.zoo,sp.oo,-sp.oo):
        return False
    singularities = sp.singularities(term,index)
    if singularities is not sp.S.EmptySet:
        if not isinstance(singularities,sp.FiniteSet):
            raise ConstraintEvaluationError('급수의 특이점이 무한집합이어서 판정할 수 없습니다.')
        for pole in singularities:
            if pole.is_integer is None:
                raise ConstraintEvaluationError('급수 특이점의 정수 여부가 미확정입니다.')
            if pole.is_integer is True and _decide(pole>=start,'급수 특이점 위치'):
                return False
    try:
        return _decide(sp.Sum(term,(index,start,sp.oo)).is_convergent(),'급수 수렴')
    except (NotImplementedError,ValueError) as exc:
        raise ConstraintEvaluationError('수렴 판정 불능입니다.') from exc


def is_valid_integration_region(region: Any, variables: Any = None) -> bool:
    """직교좌표 box/triangle 영역의 모든 경계와 변수 순서를 검사한다.

    bounds는 바깥 변수부터다. 적분 계산에 사용할 때는 bounds를 역순으로 전달한다.
    임의의 곡선 경계·극좌표 영역은 지원하지 않으며 오류로 남긴다.
    """
    if not isinstance(region,Mapping) or region.get('coordinate_system')!='cartesian':
        raise ConstraintEvaluationError('직교좌표 영역 객체가 필요합니다.')
    stored = region.get('variables')
    if not isinstance(stored,(list,tuple)) or not 1<=len(stored)<=3 or len(set(stored))!=len(stored):
        raise ConstraintEvaluationError('서로 다른 1~3개 변수가 필요합니다.')
    if any(not isinstance(v,sp.Symbol) or v.is_real is not True for v in stored):
        raise ConstraintEvaluationError('영역 변수는 실수 Symbol이어야 합니다.')
    if variables is not None and tuple(variables)!=tuple(stored):
        return False
    bounds = region.get('bounds')
    if not isinstance(bounds,(list,tuple)) or len(bounds)!=len(stored):
        return False
    for variable,bound in zip(stored,bounds):
        if not isinstance(bound,(list,tuple)) or len(bound)!=3 or bound[0]!=variable:
            return False
    if region.get('family')=='box':
        return all(_decide(_real_number(lo)<_real_number(hi),'영역 경계') for _,lo,hi in bounds)
    if region.get('family')=='triangle' and len(stored)==2:
        x,y = stored
        _,lo,extent = bounds[0]
        _,inner_lo,inner_hi = bounds[1]
        return (_real_number(lo)==0 and _real_number(inner_lo)==0
                and _decide(_real_number(extent)>0,'삼각형 크기')
                and sp.expand(_math_expression(inner_hi)-(extent-x))==0)
    raise ConstraintEvaluationError('영역 검사는 box/triangle만 지원합니다.')


def has_regular_parameterization(parameterization: Any, domain: Any) -> bool:
    """곡선 속도가 전체 구간에서 0이 아닌지 검사한다. 곡면은 affine만 지원한다."""
    if not isinstance(parameterization,Mapping):
        raise ConstraintEvaluationError('components, variables가 있는 매개화 객체가 필요합니다.')
    variables = parameterization.get('variables')
    components = parameterization.get('components')
    if not isinstance(variables,(list,tuple)) or len(variables) not in (1,2):
        raise ConstraintEvaluationError('매개변수는 1개 또는 2개여야 합니다.')
    if len(set(variables))!=len(variables) or any(not isinstance(v,sp.Symbol) or v.is_real is not True for v in variables):
        raise ConstraintEvaluationError('서로 다른 실수 매개변수가 필요합니다.')
    curve = sp.Matrix(components)
    if curve.cols!=1 or curve.rows not in (2,3):
        raise ConstraintEvaluationError('매개화에는 2/3차원 열벡터가 필요합니다.')
    if any(_math_expression(c).free_symbols-set(variables) for c in curve):
        raise ConstraintEvaluationError('매개화에 미대입 변수가 있습니다.')
    if len(variables)==1:
        t=variables[0]
        if not all(is_defined_on_domain(c,t,domain) for c in curve):
            return False
        velocity=curve.diff(t)
        if not all(is_continuous_on_interval(c,t,domain) for c in velocity):
            return False
        squared=sp.expand(velocity.dot(velocity))
        return _subset(domain,_condition_set(squared>0,t),'정칙 곡선')
    if not is_valid_integration_region(domain,variables):
        return False
    if curve.rows!=3:
        raise ConstraintEvaluationError('곡면은 3차원 성분이 필요합니다.')
    cross=curve.diff(variables[0]).cross(curve.diff(variables[1]))
    if any(c.free_symbols for c in cross):
        raise ConstraintEvaluationError('변수에 따라 변하는 곡면 Jacobian은 아직 지원하지 않습니다.')
    # 각 성분이 일차식인지 확인하여 비선형 매개화의 특이점을 숨기지 않는다.
    if any(sp.Poly(c,*variables).total_degree()>1 for c in curve):
        raise ConstraintEvaluationError('곡면 검사는 affine 매개화만 지원합니다.')
    return _decide(cross.dot(cross)>0,'정칙 곡면')


def has_valid_ode_conditions(equation: Any, conditions: Any = None) -> bool:
    """상수계수 선형 ODE의 동일 점 초기조건(0~order-1)을 검사한다.

    이는 생성 조건 검사이며 해의 정확성을 검증하지 않는다. 경계값 문제는
    별도의 존재/유일성 검사가 필요하므로 여기서 통과시키지 않는다.
    """
    if not isinstance(equation,Mapping):
        raise ConstraintEvaluationError('equation/variable/function/order를 담은 ODE 객체가 필요합니다.')
    t,y,order = equation.get('variable'),equation.get('function'),equation.get('order')
    if not isinstance(t,sp.Symbol) or t.is_real is not True or not isinstance(order,(Integral,sp.Integer)) or isinstance(order,bool) or order not in (1,2):
        raise ConstraintEvaluationError('실수 변수와 1/2차 ODE가 필요합니다.')
    if not isinstance(y,sp.Function) or y.args!=(t,):
        raise ConstraintEvaluationError('미지함수는 지정 변수의 함수여야 합니다.')
    eq=equation.get('equation')
    if not isinstance(eq,sp.Equality):
        raise ConstraintEvaluationError('ODE에는 Eq 객체가 필요합니다.')
    residual=sp.expand(eq.lhs-eq.rhs)
    jets=[y,*[sp.diff(y,t,k) for k in range(1,int(order)+1)]]
    if residual.atoms(sp.Derivative)-set(jets[1:]):
        return False
    placeholders=sp.symbols(f'j0:{int(order)+1}')
    try:
        polynomial=sp.Poly(residual.xreplace(dict(zip(jets,placeholders))),*placeholders)
    except sp.PolynomialError as exc:
        raise ConstraintEvaluationError('선형 ODE 형태가 아닙니다.') from exc
    if polynomial.total_degree()>1:
        return False
    lead=_real_number(polynomial.coeff_monomial(placeholders[-1]))
    if lead==0:
        return False
    for placeholder in placeholders:
        _real_number(polynomial.coeff_monomial(placeholder))
    forcing=polynomial.coeff_monomial(1)
    initial=equation.get('initial_conditions') if conditions is None else conditions
    if not isinstance(initial,(list,tuple)) or len(initial)!=order:
        return False
    seen=set();point=None
    for condition in initial:
        if not isinstance(condition,Mapping) or set(condition)!={'order','point','value'}:
            raise ConstraintEvaluationError('초기조건에는 order/point/value만 필요합니다.')
        k=condition['order']
        if isinstance(k,bool) or not isinstance(k,(Integral,sp.Integer)) or not 0<=k<order or k in seen:
            return False
        seen.add(k)
        p=_real_number(condition['point']);_real_number(condition['value'])
        if point is not None and p!=point:
            raise ConstraintEvaluationError('서로 다른 점의 조건은 경계값 문제이므로 지원하지 않습니다.')
        point=p
    if not is_defined_on_domain(forcing,t,sp.FiniteSet(point)):
        return False
    from sympy.calculus.util import continuous_domain
    continuous = continuous_domain(forcing,t,sp.S.Reals)
    return _decide(continuous.interior.contains(point),'초기점 근방의 연속성')


def is_transform_admissible(expression: Any, config: Any) -> bool:
    """Laplace: polynomial/exp/sin/cos 및 유한 합·곱. Fourier: polynomial*Gaussian.

    변환값을 계산하지 않고 충분조건을 확인한다. 일반 분포 변환이나 불명확한
    성장률은 통과시키지 않는다. config={'transform':'laplace','variable':t}.
    """
    if not isinstance(config,Mapping) or set(config)-{'transform','variable'}:
        raise ConstraintEvaluationError('변환 설정에는 transform/variable을 사용하세요.')
    t=config.get('variable');kind=config.get('transform')
    domain=sp.Interval(0,sp.oo) if kind=='laplace' else sp.S.Reals
    expr,t,_ = _real_context(expression,t,domain)
    if not is_defined_on_domain(expr,t,domain):
        return False
    if kind=='laplace':
        def exponential_order(node):
            if node.is_polynomial(t):return True
            if node.is_Add or node.is_Mul:return all(exponential_order(a) for a in node.args)
            if node.func in (sp.exp,sp.sin,sp.cos):
                polynomial = sp.Poly(node.args[0],t)
                if polynomial.degree()<=1:
                    return True
                if node.func==sp.exp and polynomial.degree()==2:
                    return _real_number(polynomial.coeff_monomial(t**2))<0
                return False
            return False
        if not exponential_order(expr):
            raise ConstraintEvaluationError('이 함수의 Laplace 존재 조건은 지원하지 않습니다.')
        return True
    if kind=='fourier':
        factors=sp.Mul.make_args(expr);gaussians=[a for a in factors if a.func==sp.exp]
        if len(gaussians)!=1:
            raise ConstraintEvaluationError('Fourier 존재 검사는 polynomial*Gaussian만 지원합니다.')
        exponent=gaussians[0].args[0]
        polynomial=sp.Poly(exponent,t)
        if polynomial.degree()!=2 or _real_number(polynomial.coeff_monomial(t**2))>=0:
            return False
        return _decide((expr/gaussians[0]).is_polynomial(t),'Fourier의 다항식 계수')
    raise ConstraintEvaluationError(f'미지원 변환: {kind}')


def is_analytic_on_domain(expression: Any, variable: Any, domain: Any) -> bool:
    """다항식/유리식/exp/sin/cos의 복소 전평면 또는 원판에서의 정칙성 검사."""
    expr=_math_expression(expression)
    if not isinstance(variable,sp.Symbol) or expr.free_symbols-{variable}:
        raise ConstraintEvaluationError('복소 독립변수와 대입된 계수가 필요합니다.')
    numerator,denominator=sp.fraction(sp.together(expr))
    def entire(node):
        if node.is_polynomial(variable):return True
        if node.is_Add or node.is_Mul:return all(entire(a) for a in node.args)
        if node.func in (sp.exp,sp.sin,sp.cos):return entire(node.args[0])
        return False
    if not entire(numerator) or not denominator.is_polynomial(variable):
        raise ConstraintEvaluationError('분기/특수함수의 정칙성 검사는 지원하지 않습니다.')
    poles=sp.solveset(denominator,variable,domain=sp.S.Complexes)
    if not isinstance(poles,sp.FiniteSet):
        if poles is not sp.S.EmptySet:
            raise ConstraintEvaluationError('분모의 복소 영점을 확정할 수 없습니다.')
    if domain==sp.S.Complexes:return poles is sp.S.EmptySet
    if not isinstance(domain,Mapping) or set(domain)-{'center','radius','closed'}:
        raise ConstraintEvaluationError('정칙성 정의역은 Complexes 또는 center/radius/closed 원판입니다.')
    center=_math_expression(domain.get('center',0));radius=_real_number(domain.get('radius'))
    if center.free_symbols or center.is_finite is not True or radius<=0 or type(domain.get('closed',False)) is not bool:
        raise ConstraintEvaluationError('유한한 중심·양의 반지름·bool closed가 필요합니다.')
    if poles is sp.S.EmptySet:return True
    for pole in poles:
        distance=sp.Abs(pole-center)
        if _decide(distance<=radius if domain.get('closed',False) else distance<radius,'극점 위치'):
            return False
    return True


def is_valid_probability_distribution(distribution: Any, config: Any = None) -> bool:
    """6개 표준 분포의 모수 또는 유한 이산 PMF의 비음수성과 합 1을 검사한다."""
    if config not in (None,{}):
        raise ConstraintEvaluationError('표준 분포 검사에는 별도 config가 필요하지 않습니다.')
    if not isinstance(distribution,Mapping):
        raise ConstraintEvaluationError('분포 객체가 필요합니다.')
    family=distribution.get('family');p=distribution.get('parameters')
    if family=='finite_discrete':
        masses=distribution.get('probabilities');outcomes=distribution.get('outcomes')
        if not isinstance(masses,(list,tuple)) or not masses or not isinstance(outcomes,(list,tuple)) or len(masses)!=len(outcomes) or len(set(outcomes))!=len(outcomes):
            return False
        masses=[_real_number(v) for v in masses]
        return all(_decide(v>=0,'확률 비음수성') for v in masses) and sp.Add(*masses)==1
    keys={'bernoulli':{'p'},'binomial':{'n','p'},'poisson':{'rate'},'normal':{'mu','sigma'},'uniform':{'lower','upper'},'exponential':{'rate'}}
    if family not in keys:
        raise ConstraintEvaluationError(f'미지원 분포: {family}')
    if not isinstance(p,Mapping) or set(p)!=keys[family]:return False
    p={k:_real_number(v) for k,v in p.items()}
    if family in ('bernoulli','binomial'):
        valid=_decide(0<=p['p']<=1,'확률 모수')
        if family=='binomial':valid=valid and p['n'].is_Integer is True and p['n']>=0
        return bool(valid)
    if family in ('poisson','exponential'):return _decide(p['rate']>0,'분포 rate')
    if family=='normal':return _decide(p['sigma']>0,'표준편차')
    return _decide(p['lower']<p['upper'],'균등분포 경계')


def satisfies_statistical_assumptions(data: Any, config: Any) -> bool:
    """관측값으로 확인 가능한 조건만 검사한다. 정규성·독립성은 표본으로 증명하지 않는다.

    지원 설정: min_samples, min_df, nonzero_variance, integer_values, paired.
    정규성/독립성을 요구하는 알 수 없는 설정은 예외로 남긴다.
    """
    allowed={'min_samples','min_df','nonzero_variance','integer_values','paired'}
    if not isinstance(config,Mapping) or set(config)-allowed:
        raise ConstraintEvaluationError('지원하지 않는 통계 가정입니다. 정규성/독립성을 임의로 판정하지 않습니다.')
    if not isinstance(data,(list,tuple)) or not data:return False
    paired=config.get('paired',False)
    for key in ('nonzero_variance','integer_values','paired'):
        if key in config and type(config[key]) is not bool:
            raise ConstraintEvaluationError(f'{key}는 bool이어야 합니다.')
    min_samples=config.get('min_samples',2);min_df=config.get('min_df',0)
    if any(isinstance(v,bool) or not isinstance(v,(Integral,sp.Integer)) or v<0 for v in (min_samples,min_df)):
        raise ConstraintEvaluationError('min_samples/min_df는 음이 아닌 정수여야 합니다.')
    if len(data)<min_samples or len(data)-1<min_df:return False
    rows=[]
    for value in data:
        row=list(value) if isinstance(value,(list,tuple)) else [value]
        rows.append([_real_number(v) for v in row])
    width=len(rows[0])
    if width==0 or any(len(row)!=width for row in rows):return False
    if paired:
        if width!=2:return False
        columns=[[row[0]-row[1] for row in rows]]
    else:columns=list(zip(*rows))
    if config.get('integer_values',False) and any(v.is_Integer is not True for row in rows for v in row):return False
    if config.get('nonzero_variance',False):
        for column in columns:
            mean=sp.Add(*column)/len(column)
            variance=sp.Add(*[(v-mean)**2 for v in column])
            if not _decide(variance>0,'표본 분산'):return False
    return True


NEW_PREDICATES = {
    'is_defined_on_domain':is_defined_on_domain,
    'is_continuous_on_interval':is_continuous_on_interval,
    'is_series_convergent':is_series_convergent,
    'is_valid_integration_region':is_valid_integration_region,
    'has_regular_parameterization':has_regular_parameterization,
    'has_valid_ode_conditions':has_valid_ode_conditions,
    'is_transform_admissible':is_transform_admissible,
    'is_analytic_on_domain':is_analytic_on_domain,
    'is_valid_probability_distribution':is_valid_probability_distribution,
    'satisfies_statistical_assumptions':satisfies_statistical_assumptions,
}
