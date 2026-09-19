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
- is_diagonalizable(A)
- supports_lu_without_pivoting(A)
- b.dot(b) > 0
- and / or / not

지원하지 않는 표현은 조용히 통과시키지 않고 ConstraintEvaluationError를 발생시킨다.
"""

from __future__ import annotations

import ast
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
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


def evaluate_string_constraint(
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


def resolve_operand(
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


def is_symmetric(matrix: Any) -> bool:
    """실수 정사각행렬이며 A == A.T인지 검사한다."""

    matrix = _as_matrix(matrix)

    if not is_square(matrix):
        return False

    for element in matrix:
        if element.is_real is False:
            return False

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

    return matrix.rank() == min(
        matrix.rows,
        matrix.cols,
    )


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

    return matrix.rank() == matrix.cols


def is_orthogonal(matrix: Any) -> bool:
    """실수 정사각행렬이며 A.T * A == I인지 검사한다."""

    matrix = _as_matrix(matrix)

    if not is_square(matrix):
        return False

    for element in matrix:
        if element.is_real is False:
            return False

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

    try:
        result = matrix.is_diagonalizable(
            reals_only=reals_only
        )
    except TypeError:
        # 사용 중인 SymPy 버전에서 reals_only 인자를 지원하지 않는 경우
        result = matrix.is_diagonalizable()

    return bool(result)


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

        resolved = [
            _evaluate_condition_operand(
                operand,
                values,
            )
            for operand in operands
        ]

        if normalized == "and":
            result = all(
                resolved
            )
        else:
            result = any(
                resolved
            )

        return result, {
            "operator": operator,
            "args": operands,
            "resolved": resolved,
        }

    left_value = resolve_operand(
        left,
        values,
    )

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
        # 현재 linear_algebra GenerationRule에서
        # type=diagonalizable 조건의 operator가 "diagonal"로 저장되어 있다.
        "diagonal": is_diagonalizable,
        "lu_without_pivoting": supports_lu_without_pivoting,
        "supports_lu_without_pivoting": supports_lu_without_pivoting,
    }

    if normalized in property_predicates:
        actual = bool(
            property_predicates[
                normalized
            ](
                left_value
            )
        )

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
        resolved = [
            _to_bool(
                _eval_ast_node(
                    item,
                    values,
                ),
                context="boolean operand",
            )
            for item in node.values
        ]

        if isinstance(
            node.op,
            ast.And,
        ):
            return all(
                resolved
            )

        if isinstance(
            node.op,
            ast.Or,
        ):
            return any(
                resolved
            )

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

    if node.keywords:
        raise ConstraintEvaluationError(
            "Constraint 함수 호출에서는 keyword argument를 지원하지 않습니다."
        )

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

        if name not in functions:
            raise ConstraintEvaluationError(
                f"허용되지 않은 함수입니다: {name}"
            )

        try:
            return functions[
                name
            ](
                *args
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
            return _as_matrix(
                owner
            ).rank()

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


def _is_zero(
    value: Any,
) -> bool | None:
    """값이 정확히 0인지 True / False / None으로 판정한다."""

    try:
        simplified = sp.simplify(
            value
        )
    except Exception:
        simplified = value

    if simplified == 0:
        return True

    is_zero = getattr(
        simplified,
        "is_zero",
        None,
    )

    if is_zero is True:
        return True

    if is_zero is False:
        return False

    equals_method = getattr(
        simplified,
        "equals",
        None,
    )

    if callable(
        equals_method
    ):
        try:
            equals_zero = equals_method(
                0
            )
        except Exception:
            equals_zero = None

        if equals_zero is True:
            return True

        if equals_zero is False:
            return False

    if isinstance(
        simplified,
        (
            int,
            float,
            complex,
        ),
    ):
        return simplified == 0

    return None


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


def _function_rank(
    value: Any,
) -> int:
    return int(
        _as_matrix(
            value
        ).rank()
    )


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
# 아래 과목별 함수는 설계용 주석이다.
# 현재 Python 함수로 정의하지 않고, 해당 과목 구현·검증 후 별도 연결한다.
# ---------------------------------------------------------------------------


# [미적분 1: calculus_1 / 비활성]
# def is_defined_on_domain(expression: Any, variable: Any, domain: Any) -> bool:
#     """분모·로그·근호 등 정의 조건을 지정된 정의역 전체에서 검사한다."""
#     raise NotImplementedError
#
# def is_continuous_on_interval(expression: Any, variable: Any, interval: Any) -> bool:
#     """구간 내부와 포함된 끝점의 연속성을 검사한다."""
#     raise NotImplementedError
#
# def is_series_convergent(term: Any, index: Any, start: Any) -> bool:
#     """적용 가능한 수렴 판정법을 사용하고 판정 불능은 예외로 처리한다."""
#     raise NotImplementedError


# [미적분 2: calculus_2 / 비활성]
# def is_valid_integration_region(region: Any, variables: Sequence[Any]) -> bool:
#     """경계식·변수 순서·좌표계와 영역의 유효성을 검사한다."""
#     raise NotImplementedError
#
# def has_regular_parameterization(parameterization: Any, domain: Any) -> bool:
#     """곡선·곡면의 미분 또는 Jacobian이 필요한 지점에서 퇴화하지 않는지 검사한다."""
#     raise NotImplementedError


# [공업수학: engineering_mathematics / 비활성]
# def has_valid_ode_conditions(equation: Any, conditions: Mapping[str, Any]) -> bool:
#     """차수·초기/경계조건·특이점을 확인하고 적용 정리의 가정을 검사한다."""
#     raise NotImplementedError
#
# def is_transform_admissible(expression: Any, config: Mapping[str, Any]) -> bool:
#     """지정한 라플라스·푸리에 변환의 존재 조건과 수렴 영역을 검사한다."""
#     raise NotImplementedError
#
# def is_analytic_on_domain(expression: Any, variable: Any, domain: Any) -> bool:
#     """특이점과 필요한 정칙성 조건을 정의역에서 검사한다."""
#     raise NotImplementedError


# [확률통계: probability_statistics / 비활성]
# def is_valid_probability_distribution(
#     distribution: Any,
#     config: Mapping[str, Any],
# ) -> bool:
#     """모수 범위·비음수성·전체 확률 1 조건을 검사한다."""
#     raise NotImplementedError
#
# def satisfies_statistical_assumptions(
#     data: Any,
#     config: Mapping[str, Any],
# ) -> bool:
#     """표본 크기·자유도·분산 등 계산 조건과 명시된 가정을 확인한다.
#
#     표본만 보고 독립성·정규성이 증명되었다고 판단하지 않는다.
#     """
#     raise NotImplementedError
