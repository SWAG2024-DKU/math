"""오프라인 문제 생성용 공통·선형대수 파라미터 샘플러.

저장 위치: scripts/problems/parameter_sampler.py
- 정수·유리수·실수, 벡터, 일반/정사각/대칭/대각행렬을 생성한다.
- 공통 Random(seed)으로 의존관계·파생값 선택까지 재현한다.
- 생성값과 파생값의 선언 타입·범위·step·choices·exclude를 검증한다.
- allowed_families는 생성 가능한 행렬 형태의 선택 목록이다.
- matrix/vector의 min/max, choices, exclude, step은 원소에 적용한다.
  대각행렬의 구조적 0도 원소 조건을 만족해야 한다.
- rational: step이 있으면 min 기준 격자에서, 없으면 denominator(기본 10)의
  정수배 격자에서 균등 선택한다. 모든 유리수에 대한 균등분포를 뜻하지 않는다.
  denominator는 ParameterSpec의 추가 필드로 지정할 수 있다.
- real: step이 없으면 연속 균등 난수(float), 있으면 min 기준 격자에서 선택한다.
- 파생식의 정수 나눗셈은 정확한 SymPy 유리수이다. float 입력은 근삿값이다.
- 가역성/rank 등 Rule의 수학적 Constraint는 별도 Evaluator에서 검사한다.
  실패 시 여기서 재샘플링하지 않고 ParameterSamplingError를 발생시킨다.
- 다른 과목 전용 함수는 파일 아래 주석 상태로 유지한다.
"""

from __future__ import annotations

from collections.abc import Mapping
from random import Random
from typing import Any

from fractions import Fraction
from numbers import Integral
import math

import sympy as sp
from sympy import Matrix

from app.schemas.generation_rule import ParameterSpec, RangeSpec, ShapeSpec

import ast


class ParameterSamplingError(RuntimeError):
    """파라미터를 생성할 수 없을 때 사용하는 예외."""


_MATRIX_GENERATORS = frozenset({
    "regression_design_matrix",
    "orthogonal_integer_norm_columns",
    "small_integer_spectrum_symmetric",
    "elementary_matrix",
    "small_svd_matrix",
    "rank_one_pseudoinverse_matrix",
    "centered_pca_matrix",
    "defective_jordan_matrix",
})
_VECTOR_GENERATORS = frozenset({"small_gaussian_vector", "complex_real_inner_partner"})


def _random_index(n: int, *, rng: Random) -> int:
    if isinstance(n, bool) or not isinstance(n, (Integral, sp.Integer)):
        raise ParameterSamplingError(
            f"random_index의 n은 정수여야 합니다: {n!r}"
        )

    if n < 1:
        raise ParameterSamplingError(
            "random_index의 n은 1 이상이어야 합니다."
        )

    return rng.randrange(int(n))


def _random_distinct_index(
    n: int,
    target_row: int,
    *,
    rng: Random,
) -> int:
    if isinstance(n, bool) or not isinstance(n, (Integral, sp.Integer)):
        raise ParameterSamplingError(
            f"random_distinct_index의 n은 정수여야 합니다: {n!r}"
        )

    if n < 2:
        raise ParameterSamplingError(
            "서로 다른 두 행을 선택하려면 n은 2 이상이어야 합니다."
        )

    if (
        isinstance(target_row, bool)
        or not isinstance(target_row, (Integral, sp.Integer))
        or not 0 <= target_row < n
    ):
        raise ParameterSamplingError(
            f"target_row가 범위를 벗어났습니다: {target_row!r}"
        )

    candidates = [
        index
        for index in range(int(n))
        if index != target_row
    ]

    return rng.choice(candidates)


DERIVED_FUNCTION_REGISTRY = {
    "random_index": _random_index,
    "random_distinct_index": _random_distinct_index,
}


def _evaluate_safe_expression(
    expression: str,
    context: Mapping[str, Any],
    rng: Random,
    *,
    allow_registry: bool,
) -> Any:
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ParameterSamplingError(
            f"파생식 문법이 올바르지 않습니다: {expression}"
        ) from exc

    def evaluate(node: ast.AST) -> Any:
        if isinstance(node, ast.Expression):
            return evaluate(node.body)

        if isinstance(node, ast.Name):
            if node.id in context:
                return context[node.id]

            raise ParameterSamplingError(
                f"파생식에서 사용할 수 없는 이름입니다: {node.id}"
            )

        if isinstance(node, ast.Constant):
            return sp.Integer(node.value) if type(node.value) is int else node.value

        if isinstance(node, ast.List):
            return [
                evaluate(element)
                for element in node.elts
            ]

        if isinstance(node, ast.Tuple):
            return tuple(
                evaluate(element)
                for element in node.elts
            )

        if isinstance(node, ast.UnaryOp):
            value = evaluate(node.operand)

            if isinstance(node.op, ast.USub):
                return -value

            if isinstance(node.op, ast.UAdd):
                return +value

            raise ParameterSamplingError(
                "지원하지 않는 단항 연산입니다."
            )

        if isinstance(node, ast.BinOp):
            left = evaluate(node.left)
            right = evaluate(node.right)

            if isinstance(node.op, ast.Add):
                return left + right

            if isinstance(node.op, ast.Sub):
                return left - right

            if isinstance(node.op, ast.Mult):
                return left * right

            if isinstance(node.op, ast.Div):
                if right == 0:
                    raise ParameterSamplingError("파생식에서 0으로 나눌 수 없습니다.")
                if isinstance(left, (Integral, sp.Integer)) and isinstance(right, (Integral, sp.Integer)):
                    return sp.Rational(int(left), int(right))
                return left / right

            if isinstance(node.op, ast.Pow):
                return left ** right

            raise ParameterSamplingError(
                "지원하지 않는 이항 연산입니다."
            )

        if isinstance(node, ast.Attribute):
            value = evaluate(node.value)

            if node.attr in {"rows", "cols"}:
                if not hasattr(value, node.attr):
                    raise ParameterSamplingError(
                        f"'{node.attr}' 속성을 사용할 수 없습니다."
                    )

                return getattr(value, node.attr)

            raise ParameterSamplingError(
                f"허용되지 않은 속성 접근입니다: {node.attr}"
            )

        if isinstance(node, ast.Call):
            args = [
                evaluate(arg)
                for arg in node.args
            ]

            if node.keywords:
                raise ParameterSamplingError(
                    "파생식의 keyword argument는 지원하지 않습니다."
                )

            # list(...)
            if isinstance(node.func, ast.Name):
                function_name = node.func.id

                if function_name == "list":
                    if len(args) != 1:
                        raise ParameterSamplingError(
                            "list()는 인자 하나만 허용합니다."
                        )

                    return list(args[0])

                if (
                    allow_registry
                    and function_name in DERIVED_FUNCTION_REGISTRY
                ):
                    function = DERIVED_FUNCTION_REGISTRY[
                        function_name
                    ]

                    return function(
                        *args,
                        rng=rng,
                    )

                raise ParameterSamplingError(
                    f"허용되지 않은 파생 함수입니다: "
                    f"{function_name}"
                )

            # A.eigenvals(), result.keys()
            if isinstance(node.func, ast.Attribute):
                target = evaluate(node.func.value)
                method_name = node.func.attr

                if method_name == "eigenvals":
                    if args:
                        raise ParameterSamplingError(
                            "eigenvals() 인자는 지원하지 않습니다."
                        )

                    if not hasattr(target, "eigenvals"):
                        raise ParameterSamplingError(
                            "eigenvals()를 사용할 수 없는 객체입니다."
                        )

                    return target.eigenvals()

                if method_name == "keys":
                    if args:
                        raise ParameterSamplingError(
                            "keys() 인자는 지원하지 않습니다."
                        )

                    if not isinstance(target, Mapping):
                        raise ParameterSamplingError(
                            "keys()는 Mapping 객체에만 사용할 수 있습니다."
                        )

                    return target.keys()

                raise ParameterSamplingError(
                    f"허용되지 않은 메서드입니다: "
                    f"{method_name}"
                )

        if isinstance(node, ast.Subscript):
            target = evaluate(node.value)
            index = evaluate(node.slice)

            try:
                return target[index]
            except (IndexError, KeyError, TypeError) as exc:
                raise ParameterSamplingError(
                    "파생식의 인덱스 접근에 실패했습니다."
                ) from exc

        raise ParameterSamplingError(
            "지원하지 않는 파생식 구문입니다: "
            f"{type(node).__name__}"
        )

    return evaluate(tree)


def sample_parameters(
    parameter_specs: Mapping[str, ParameterSpec],
    *,
    seed: int,
) -> dict[str, Any]:
    """GenerationRule의 파라미터를 의존 순서에 맞게 한 번 생성한다."""

    rng = Random(seed)

    order = resolve_parameter_order(
        parameter_specs
    )

    generated: dict[str, Any] = {}

    for name in order:
        spec = parameter_specs[name]

        try:
            if spec.derived is not None or spec.type == "derived":
                value = evaluate_derived_parameter(
                    name,
                    spec,
                    generated,
                    rng,
                )
            else:
                value = sample_parameter(
                    name,
                    spec,
                    generated,
                    rng,
                )

        except ParameterSamplingError:
            raise

        except Exception as exc:
            raise ParameterSamplingError(
                f"파라미터 '{name}' 생성 중 "
                f"예상하지 못한 오류가 발생했습니다."
            ) from exc

        generated[name] = value

    return generated


def resolve_parameter_order(
    parameter_specs: Mapping[str, ParameterSpec],
) -> list[str]:
    """의존관계를 위상 정렬하여 파라미터 생성 순서를 반환한다.

    검사 항목:
    - 선언되지 않은 파라미터 의존
    - 자기 자신에 대한 의존
    - 순환 의존관계

    반환 순서는 가능한 한 parameter_specs의 기존 선언 순서를 유지한다.
    """

    parameter_names = list(parameter_specs.keys())
    known_names = set(parameter_names)

    # parameter -> 그 parameter가 의존하는 parameter 집합
    dependencies: dict[str, set[str]] = {}

    for name, spec in parameter_specs.items():
        deps = set(spec.depends_on)

        # derived 파라미터의 의존관계도 함께 반영한다.
        if spec.derived is not None:
            deps.update(spec.derived.depends_on)

        if spec.shape is not None:
            shape_values = (
                spec.shape.rows,
                spec.shape.cols,
                spec.shape.dimension,
                spec.shape.length,
                spec.shape.size,
            )

            for value in shape_values:
                if not isinstance(value, str):
                    continue

                referenced_name = value.split(".", 1)[0]

                # A.cols = A.rows 같은 자기 내부 참조는
                # parameter dependency가 아니다.
                if referenced_name != name:
                    deps.add(referenced_name)

        # 선언되지 않은 dependency 검사
        unknown = deps - known_names
        if unknown:
            unknown_text = ", ".join(sorted(unknown))
            raise ParameterSamplingError(
                f"파라미터 '{name}'이 선언되지 않은 파라미터에 의존합니다: "
                f"{unknown_text}"
            )

        # 자기 자신을 dependency로 지정한 경우
        if name in deps:
            raise ParameterSamplingError(
                f"파라미터 '{name}'이 자기 자신에 의존합니다."
            )

        dependencies[name] = deps

    result: list[str] = []
    resolved: set[str] = set()

    while len(result) < len(parameter_names):
        progressed = False

        # 기존 JSON의 선언 순서를 최대한 보존한다.
        for name in parameter_names:
            if name in resolved:
                continue

            if dependencies[name].issubset(resolved):
                result.append(name)
                resolved.add(name)
                progressed = True

        # 한 바퀴 돌았는데 아무 것도 해결되지 않았다면 cycle이다.
        if not progressed:
            unresolved = [
                name
                for name in parameter_names
                if name not in resolved
            ]

            details = ", ".join(
                f"{name} -> {sorted(dependencies[name] - resolved)}"
                for name in unresolved
            )

            raise ParameterSamplingError(
                "파라미터 의존관계에 순환이 있거나 해결할 수 없는 "
                f"의존관계가 있습니다: {details}"
            )

    return result


def sample_parameter(
    name: str,
    spec: ParameterSpec,
    generated: Mapping[str, Any],
    rng: Random,
) -> Any:
    """파라미터 타입에 맞는 생성 함수를 선택한다."""

    if spec.derived is not None or spec.type == "derived":
        raise ParameterSamplingError(
            f"파생 파라미터 '{name}'은 "
            "evaluate_derived_parameter()로 생성해야 합니다."
        )

    if spec.generator is not None and spec.generator not in (
        _MATRIX_GENERATORS if spec.type == "matrix" else _VECTOR_GENERATORS if spec.type == "vector" else ()
    ):
        raise ParameterSamplingError(
            f"파라미터 '{name}'의 generator "
            f"'{spec.generator}'는 아직 구현되지 않았습니다."
        )
    if spec.generator is not None and spec.type not in {"matrix", "vector"}:
        raise ParameterSamplingError(
            f"{spec.generator}에는 행렬 또는 벡터 타입이 필요합니다."
        )

    if spec.type in {
        "integer",
        "real",
        "rational",
        "choice",
    }:
        return sample_scalar(spec, rng)

    if spec.type == "vector":
        shape = resolve_shape(
            name,
            spec.shape,
            spec,
            generated,
            rng,
        )

        if spec.generator == "complex_real_inner_partner":
            if shape.get("dimension") != 2 or "u" not in generated:
                raise ParameterSamplingError("complex_real_inner_partner에는 길이 2인 u가 필요합니다.")
            u = Matrix(generated["u"])
            if u.shape != (2, 1):
                raise ParameterSamplingError("u는 길이 2인 열벡터여야 합니다.")
            orthogonal = Matrix([-sp.conjugate(u[1]), sp.conjugate(u[0])])
            return rng.choice((-1, 1)) * u + orthogonal
        return sample_vector(
            spec,
            shape,
            rng,
        )

    if spec.type == "matrix":
        shape = resolve_shape(
            name,
            spec.shape,
            spec,
            generated,
            rng,
        )

        matrix = sample_matrix(
            spec,
            shape,
            rng,
        )
        if spec.generator == "regression_design_matrix":
            if matrix.cols < 2:
                raise ParameterSamplingError("회귀 설계행렬에는 절편 열과 설명변수 열이 필요합니다.")
            _validate_scalar(1, _element_spec(spec))
            for row in range(matrix.rows):
                matrix[row, 0] = 1
        return matrix

    raise ParameterSamplingError(
        f"파라미터 '{name}'의 타입 "
        f"'{spec.type}'은 아직 지원하지 않습니다."
    )


def resolve_shape(
    name: str,
    shape: ShapeSpec | None,
    spec: ParameterSpec,
    generated: Mapping[str, Any],
    rng: Random,
) -> dict[str, int]:
    """행렬 또는 벡터의 실제 크기를 결정한다.

    지원:
    - 고정 크기
    - RangeSpec 범위
    - 다른 파라미터의 크기 참조: A.rows, A.cols, u.dimension
    - 직접 값 참조: n
    - 같은 파라미터 내부 참조: A.cols = A.rows
    - 기존 rows_min/rows_max 등의 legacy 필드
    """

    resolved: dict[str, int] = {}

    def validate_dimension(field_name: str, value: Any) -> int:
        if isinstance(value, bool) or not isinstance(value, (Integral, sp.Integer)):
            raise ParameterSamplingError(
                f"파라미터 '{name}'의 {field_name} 크기는 정수여야 합니다: "
                f"{value!r}"
            )

        if value < 1:
            raise ParameterSamplingError(
                f"파라미터 '{name}'의 {field_name} 크기는 1 이상이어야 합니다: "
                f"{value}"
            )

        return int(value)

    def get_object_dimension(
        reference_name: str,
        value: Any,
        attribute: str,
    ) -> int:
        if attribute == "rows":
            if not hasattr(value, "rows"):
                raise ParameterSamplingError(
                    f"'{reference_name}'에는 rows 속성이 없습니다."
                )
            return validate_dimension(attribute, value.rows)

        if attribute == "cols":
            if not hasattr(value, "cols"):
                raise ParameterSamplingError(
                    f"'{reference_name}'에는 cols 속성이 없습니다."
                )
            return validate_dimension(attribute, value.cols)

        if attribute in {"dimension", "length"}:
            # SymPy 열벡터
            if hasattr(value, "rows") and hasattr(value, "cols"):
                if value.cols == 1:
                    return validate_dimension(attribute, value.rows)

                if value.rows == 1:
                    return validate_dimension(attribute, value.cols)

                raise ParameterSamplingError(
                    f"'{reference_name}'은 벡터가 아니므로 "
                    f"{attribute}을 참조할 수 없습니다."
                )

            try:
                return validate_dimension(attribute, len(value))
            except TypeError as exc:
                raise ParameterSamplingError(
                    f"'{reference_name}'의 {attribute}을 결정할 수 없습니다."
                ) from exc

        if attribute == "size":
            try:
                return validate_dimension(attribute, len(value))
            except TypeError as exc:
                raise ParameterSamplingError(
                    f"'{reference_name}'의 size를 결정할 수 없습니다."
                ) from exc

        raise ParameterSamplingError(
            f"지원하지 않는 크기 속성입니다: {attribute}"
        )

    def resolve_value(field_name: str, value: Any) -> int:
        # 1. 고정 크기
        if isinstance(value, (Integral, sp.Integer)):
            return validate_dimension(field_name, value)

        # 2. 범위
        if isinstance(value, RangeSpec):
            sampled = rng.randint(value.min, value.max)
            return validate_dimension(field_name, sampled)

        # 3. 참조
        if isinstance(value, str):
            # n 같은 직접 파라미터 참조
            if "." not in value:
                if value not in generated:
                    raise ParameterSamplingError(
                        f"파라미터 '{name}'의 {field_name}에서 "
                        f"아직 생성되지 않은 값 '{value}'을 참조합니다."
                    )

                return validate_dimension(
                    field_name,
                    generated[value],
                )

            reference_name, attribute = value.split(".", 1)

            # A.cols = A.rows 같은 자기 내부 shape 참조
            if reference_name == name:
                if attribute not in resolved:
                    raise ParameterSamplingError(
                        f"파라미터 '{name}'의 {field_name}에서 "
                        f"아직 결정되지 않은 자기 크기 "
                        f"'{value}'을 참조합니다."
                    )

                return validate_dimension(
                    field_name,
                    resolved[attribute],
                )

            # B.rows = A.cols 같은 다른 파라미터 참조
            if reference_name not in generated:
                raise ParameterSamplingError(
                    f"파라미터 '{name}'의 {field_name}에서 "
                    f"아직 생성되지 않은 파라미터 "
                    f"'{reference_name}'을 참조합니다."
                )

            return get_object_dimension(
                reference_name,
                generated[reference_name],
                attribute,
            )

        raise ParameterSamplingError(
            f"파라미터 '{name}'의 {field_name}에 "
            f"지원하지 않는 shape 값이 있습니다: {value!r}"
        )

    # 신규 shape 구조
    if shape is not None:
        pending = {key: getattr(shape, key) for key in
                   ("rows", "cols", "dimension", "length", "size")
                   if getattr(shape, key) is not None}
        while pending:
            progressed = False
            for field_name, value in list(pending.items()):
                if isinstance(value, str) and value.startswith(name + "."):
                    attribute = value.split(".", 1)[1]
                    if attribute not in resolved:
                        if attribute not in pending:
                            raise ParameterSamplingError(f"미선언 자기 크기 참조: {value}")
                        continue
                resolved[field_name] = resolve_value(field_name, value)
                del pending[field_name]
                progressed = True
            if not progressed:
                raise ParameterSamplingError(f"자기 크기 참조가 순환합니다: {name}")
        return resolved

    # legacy matrix shape
    if spec.type == "matrix":
        if spec.rows_min is not None or spec.rows_max is not None:
            minimum = spec.rows_min or spec.rows_max
            maximum = spec.rows_max or spec.rows_min

            resolved["rows"] = rng.randint(minimum, maximum)

        if spec.cols_min is not None or spec.cols_max is not None:
            minimum = spec.cols_min or spec.cols_max
            maximum = spec.cols_max or spec.cols_min

            resolved["cols"] = rng.randint(minimum, maximum)

    # legacy vector shape
    elif spec.type == "vector":
        if (
            spec.dimension_min is not None
            or spec.dimension_max is not None
        ):
            minimum = spec.dimension_min or spec.dimension_max
            maximum = spec.dimension_max or spec.dimension_min

            resolved["dimension"] = rng.randint(
                minimum,
                maximum,
            )

    # legacy size
    if spec.size_min is not None or spec.size_max is not None:
        minimum = spec.size_min or spec.size_max
        maximum = spec.size_max or spec.size_min

        resolved["size"] = rng.randint(minimum, maximum)

    if not resolved:
        raise ParameterSamplingError(
            f"파라미터 '{name}'에 크기 규칙이 없습니다."
        )

    for field_name, value in resolved.items():
        validate_dimension(field_name, value)

    return resolved


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (Integral, sp.Integer)):
        raise ParameterSamplingError(f"{label}은 정수여야 합니다: {value!r}")
    return int(value)


def _number(value: Any) -> sp.Expr:
    """문자열 파싱 없이 유한한 실수만 정규화한다."""
    if isinstance(value, bool):
        raise ParameterSamplingError("Boolean은 숫자 파라미터로 사용할 수 없습니다.")
    if isinstance(value, (Integral, sp.Integer)):
        result = sp.Integer(int(value))
    elif isinstance(value, Fraction):
        result = sp.Rational(value.numerator, value.denominator)
    elif isinstance(value, float):
        if not math.isfinite(value):
            raise ParameterSamplingError("유한한 숫자가 필요합니다.")
        result = sp.Rational(str(value))
    elif isinstance(value, sp.Expr):
        result = value
    else:
        raise ParameterSamplingError(f"숫자가 아닌 값입니다: {value!r}")
    if result.is_number is not True or result.is_real is not True or result.is_finite is not True:
        raise ParameterSamplingError(f"확정된 유한 실수가 필요합니다: {value!r}")
    return result


def _equal(left: Any, right: Any) -> bool:
    try:
        return sp.simplify(_number(left) - _number(right)) == 0
    except ParameterSamplingError:
        return left == right


def _normalize_scalar(value: Any, kind: str) -> Any:
    if kind == "integer":
        return _integer(value, "integer 값")
    if kind in {"rational", "real"}:
        number = _number(value)
        if kind == "rational":
            if number.is_Rational is not True:
                raise ParameterSamplingError(f"유리수가 아닌 값입니다: {value!r}")
            return number
        return value
    if kind in {"choice", "derived"}:
        return value
    raise ParameterSamplingError(f"지원하지 않는 scalar 타입입니다: {kind}")


def _validate_scalar(value: Any, spec: ParameterSpec, *, check_choices: bool = True,
                     check_exclude: bool = True) -> Any:
    value = _normalize_scalar(value, spec.type)
    if spec.min is not None or spec.max is not None or spec.step is not None:
        number = _number(value)
        lower = _number(spec.min) if spec.min is not None else None
        upper = _number(spec.max) if spec.max is not None else None
        if lower is not None and upper is not None and lower > upper:
            raise ParameterSamplingError("min이 max보다 큽니다.")
        if lower is not None and number < lower:
            raise ParameterSamplingError(f"생성값 {value!r}이 min보다 작습니다.")
        if upper is not None and number > upper:
            raise ParameterSamplingError(f"생성값 {value!r}이 max보다 큽니다.")
        if spec.step is not None:
            step = _number(spec.step)
            if step <= 0 or lower is None:
                raise ParameterSamplingError("step은 양수이며 기준 min이 필요합니다.")
            if sp.simplify((number - lower) / step).is_integer is not True:
                raise ParameterSamplingError(f"생성값 {value!r}이 step 격자에 없습니다.")
    if check_exclude and any(_equal(value, excluded) for excluded in spec.exclude):
        raise ParameterSamplingError(f"제외값이 생성되었습니다: {value!r}")
    if check_choices and spec.choices and not any(_equal(value, choice) for choice in spec.choices):
        raise ParameterSamplingError(f"생성값이 choices에 없습니다: {value!r}")
    return value


def _grid_sample(start: sp.Expr, step: sp.Expr, count: int,
                 exclude: list[Any], rng: Random) -> sp.Expr:
    """큰 후보 리스트 없이 제외된 격자 인덱스를 건너뛴다."""
    blocked = set()
    for value in exclude:
        try:
            index = sp.simplify((_number(value) - start) / step)
        except ParameterSamplingError:
            continue
        if index.is_integer is True and 0 <= index < count:
            blocked.add(int(index))
    available = count - len(blocked)
    if available <= 0:
        raise ParameterSamplingError("조건을 만족하는 생성 후보가 없습니다.")
    index = rng.randrange(available)
    for forbidden in sorted(blocked):
        if forbidden <= index:
            index += 1
    return start + index * step


def sample_scalar(spec: ParameterSpec, rng: Random) -> Any:
    """타입과 모든 제약을 만족하는 scalar를 생성한다.

    choices의 잘못된 타입/범위는 설정 오류로 처리한다. exclude만 후보에서 제거한다.
    유리수는 고정 분모 격자(기본 10) 또는 명시적 step 격자를 사용한다.
    """
    if spec.distribution not in (None, "uniform"):
        raise ParameterSamplingError(f"지원하지 않는 distribution: {spec.distribution}")
    if spec.type not in {"integer", "real", "rational", "choice"}:
        raise ParameterSamplingError(f"지원하지 않는 scalar 타입: {spec.type}")
    if spec.type == "integer":
        for label in ("min", "max", "step"):
            if getattr(spec, label) is not None:
                _integer(getattr(spec, label), label)
    if spec.choices:
        candidates = []
        for candidate in spec.choices:
            candidate = _validate_scalar(candidate, spec, check_choices=False, check_exclude=False)
            if not any(_equal(candidate, excluded) for excluded in spec.exclude):
                candidates.append(candidate)
        if not candidates:
            raise ParameterSamplingError("choices에서 exclude를 제외한 값이 없습니다.")
        return rng.choice(candidates)
    if spec.type == "choice":
        raise ParameterSamplingError("choice 타입에는 choices가 필요합니다.")
    if spec.min is None or spec.max is None:
        raise ParameterSamplingError("min과 max가 필요합니다.")
    lower, upper = _number(spec.min), _number(spec.max)
    if lower > upper:
        raise ParameterSamplingError("min이 max보다 큽니다.")
    if spec.type == "real" and spec.step is None:
        lo, hi = float(lower), float(upper)
        if not math.isfinite(lo) or not math.isfinite(hi) or not math.isfinite(hi - lo):
            raise ParameterSamplingError("float로 샘플링할 수 없는 real 범위입니다.")
        # 연속 실수에 대한 유한한 exclude 재선택이다. Rule Constraint 재시도가 아니다.
        for _ in range(128):
            value = rng.uniform(lo, hi)
            if not any(_equal(value, excluded) for excluded in spec.exclude):
                return _validate_scalar(value, spec)
        raise ParameterSamplingError("real 범위에서 제외값을 피할 수 없습니다.")
    start = lower
    if spec.step is not None:
        step = _number(spec.step)
        if step <= 0:
            raise ParameterSamplingError("step은 양수여야 합니다.")
    elif spec.type == "integer":
        step = sp.Integer(1)
    else:
        denominator = _integer(getattr(spec, "denominator", 10), "denominator")
        if denominator < 1:
            raise ParameterSamplingError("denominator는 1 이상이어야 합니다.")
        step = sp.Rational(1, denominator)
        start = sp.ceiling(lower * denominator) / denominator
    count = int(sp.floor((upper - start) / step)) + 1
    value = _grid_sample(start, step, count, spec.exclude, rng)
    if spec.type == "integer":
        value = int(value)
    elif spec.type == "real":
        # 격자값은 정확한 Rational로 반환하여 float 반올림으로 step을 깨지 않는다.
        pass
    return _validate_scalar(value, spec)


def _element_spec(spec: ParameterSpec) -> ParameterSpec:
    return spec.model_copy(update={
        "type": spec.element_type or "integer",
        "min": spec.element_min if spec.element_min is not None else spec.min,
        "max": spec.element_max if spec.element_max is not None else spec.max,
        "shape": None, "depends_on": [], "derived": None,
        "allowed_families": [], "generator": None,
    })


def sample_vector(spec: ParameterSpec, shape: Mapping[str, int], rng: Random) -> Any:
    if spec.allowed_families:
        raise ParameterSamplingError("vector의 allowed_families는 아직 지원하지 않습니다.")
    dimension = _integer(shape.get("dimension", shape.get("length")), "vector 차원")
    if dimension < 1:
        raise ParameterSamplingError("vector 차원은 1 이상이어야 합니다.")
    if spec.generator == "small_gaussian_vector":
        if dimension != 2:
            raise ParameterSamplingError("small_gaussian_vector는 길이 2만 지원합니다.")
        # 복소 성분이 실제로 등장하며, seed마다 독립적으로 변한다.
        return Matrix([rng.choice((-2, -1, 1, 2)) + rng.choice((-1, 1)) * sp.I,
                       rng.choice((-2, -1, 1, 2)) + rng.choice((-1, 1)) * sp.I])
    element = _element_spec(spec)
    return Matrix([sample_scalar(element, rng) for _ in range(dimension)])


_MATRIX_FAMILIES = {
    "general": "general", "matrix": "general", "general_matrix": "general",
    "square": "square", "square_matrix": "square",
    "symmetric": "symmetric", "symmetric_matrix": "symmetric",
    "diagonal": "diagonal", "diagonal_matrix": "diagonal",
}


def _families(spec: ParameterSpec) -> list[str]:
    result = []
    for family in spec.allowed_families or ["general"]:
        if family not in _MATRIX_FAMILIES:
            raise ParameterSamplingError(f"미지원 행렬 family입니다: {family}")
        result.append(_MATRIX_FAMILIES[family])
    return result


def sample_matrix(spec: ParameterSpec, shape: Mapping[str, int], rng: Random) -> Any:
    rows, cols = _integer(shape.get("rows"), "rows"), _integer(shape.get("cols"), "cols")
    if rows < 1 or cols < 1:
        raise ParameterSamplingError("행렬 크기는 1 이상이어야 합니다.")
    # 선형대수에서 답의 계산 난이도를 제어하는 명시적 generator.
    # 일반 행렬을 대량 생성한 뒤 정답만 거르는 방식은 사용하지 않는다.
    special = {
        "orthogonal_integer_norm_columns": _easy_orthogonal_columns,
        "small_integer_spectrum_symmetric": _small_integer_spectrum_symmetric,
        "elementary_matrix": _elementary_matrix,
        "small_svd_matrix": _small_svd_matrix,
        "rank_one_pseudoinverse_matrix": _rank_one_pseudoinverse_matrix,
        "centered_pca_matrix": _centered_pca_matrix,
        "defective_jordan_matrix": _defective_jordan_matrix,
    }
    if spec.generator in special:
        result = special[spec.generator](rows, cols, rng)
        element = _element_spec(spec)
        for entry in result:
            _validate_scalar(entry, element)
        if spec.allowed_families:
            families = _families(spec)
            if not any(
                family == "general"
                or (family == "square" and rows == cols)
                or (family == "symmetric" and result == result.T)
                or (family == "diagonal" and result.is_diagonal() is True)
                for family in families
            ):
                raise ParameterSamplingError("전용 generator가 allowed_families와 충돌합니다.")
        return result
    families = [family for family in _families(spec) if family == "general" or rows == cols]
    if not families:
        raise ParameterSamplingError("지정한 행렬 family에는 정사각형 크기가 필요합니다.")
    family = families[0] if len(families) == 1 else rng.choice(families)
    element = _element_spec(spec)
    if family in {"general", "square"}:
        return Matrix(rows, cols, [sample_scalar(element, rng) for _ in range(rows * cols)])
    result = sp.zeros(rows, cols)
    if family == "symmetric":
        for row in range(rows):
            for col in range(row, cols):
                result[row, col] = result[col, row] = sample_scalar(element, rng)
    else:
        if rows > 1:
            # 구조상 필요한 0이 금지된 설정은 조용히 무시하지 않는다.
            _validate_scalar(0, element)
        for row in range(rows):
            result[row, row] = sample_scalar(element, rng)
    return result


def _small_svd_matrix(rows: int, cols: int, rng: Random) -> Any:
    """서로 다른 양의 정수 특이값을 가진 2x2 부호 있는 순열행렬."""
    if (rows, cols) != (2, 2):
        raise ParameterSamplingError("small_svd_matrix는 2x2만 지원합니다.")
    large, small = rng.sample((1, 2, 3, 4), 2)
    if rng.choice((True, False)):
        return Matrix([[rng.choice((-1, 1)) * large, 0],
                       [0, rng.choice((-1, 1)) * small]])
    return Matrix([[0, rng.choice((-1, 1)) * large],
                   [rng.choice((-1, 1)) * small, 0]])


def _rank_one_pseudoinverse_matrix(rows: int, cols: int, rng: Random) -> Any:
    if (rows, cols) != (2, 2):
        raise ParameterSamplingError("rank_one_pseudoinverse_matrix는 2x2만 지원합니다.")
    a, b = rng.sample((1, 2, 3), 2)
    a, b = rng.choice((-1, 1)) * a, rng.choice((-1, 1)) * b
    return Matrix([[a, 0], [b, 0]]) if rng.choice((True, False)) else Matrix([[0, a], [0, b]])


def _centered_pca_matrix(rows: int, cols: int, rng: Random) -> Any:
    if (rows, cols) != (4, 2):
        raise ParameterSamplingError("centered_pca_matrix는 4x2만 지원합니다.")
    a, b = rng.sample((1, 2, 3), 2)
    # Both coordinate axes and 45-degree axes occur. Distinct scales avoid
    # ambiguous leading principal components.
    directions = ((1, 0), (0, 1)) if rng.choice((True, False)) else ((1, 1), (1, -1))
    u, v = directions
    samples = [[a * u[0], a * u[1]], [-a * u[0], -a * u[1]],
               [b * v[0], b * v[1]], [-b * v[0], -b * v[1]]]
    rng.shuffle(samples)
    return Matrix(samples)


def _defective_jordan_matrix(rows: int, cols: int, rng: Random) -> Any:
    if (rows, cols) != (2, 2):
        raise ParameterSamplingError("defective_jordan_matrix는 2x2만 지원합니다.")
    lam = rng.randrange(-3, 4)
    c = rng.choice((-3, -2, -1, 1, 2, 3))
    return Matrix([[lam, c], [0, lam]])


def _easy_orthogonal_columns(rows: int, cols: int, rng: Random) -> Any:
    """작은 정수 성분과 길이 1 또는 5인 직교 열벡터를 만든다."""
    if (rows, cols) != (3, 2):
        raise ParameterSamplingError("orthogonal_integer_norm_columns는 3x2만 지원합니다.")
    candidates = (
        ((1, 0, 0), (0, 1, 0)),
        ((3, 4, 0), (4, -3, 0)),
        ((3, 4, 0), (0, 0, 1)),
    )
    base = rng.choice(candidates)
    permutation = rng.sample(range(3), 3)
    columns = []
    for column in base:
        sign = rng.choice((-1, 1))
        columns.append(Matrix([sign * column[index] for index in permutation]))
    if rng.randrange(2):
        columns.reverse()
    return Matrix.hstack(*columns)


def _small_integer_spectrum_symmetric(rows: int, cols: int, rng: Random) -> Any:
    """2x2 대칭 블록의 고윳값이 d±b인 작은 정수 행렬."""
    if rows != cols or rows not in (2, 3):
        raise ParameterSamplingError("small_integer_spectrum_symmetric는 2x2/3x3만 지원합니다.")
    diagonal = rng.randint(-2, 2)
    off_diagonal = rng.choice((-2, -1, 1, 2))
    result = sp.zeros(rows)
    result[0, 0] = result[1, 1] = diagonal
    result[0, 1] = result[1, 0] = off_diagonal
    if rows == 3:
        result[2, 2] = rng.randint(-3, 3)
    permutation = rng.sample(range(rows), rows)
    return result.extract(permutation, permutation)


def _elementary_matrix(rows: int, cols: int, rng: Random) -> Any:
    """한 번의 기본행연산에 대응하는 진짜 기본행렬."""
    if rows != cols or rows < 2:
        raise ParameterSamplingError("elementary_matrix는 2차 이상 정사각행렬만 지원합니다.")
    result = sp.eye(rows)
    first, second = rng.sample(range(rows), 2)
    if rng.randrange(2):
        result.row_swap(first, second)
    else:
        result[first, second] = rng.choice((-3, -2, -1, 1, 2, 3))
    return result


def evaluate_derived_parameter(
    name: str,
    spec: ParameterSpec,
    generated: Mapping[str, Any],
    rng: Random,
) -> Any:
    """파생값을 계산한 뒤 선언한 타입·범위·선택지·제외값을 검증한다."""
    try:
        value = _evaluate_derived_parameter_impl(name, spec, generated, rng)
        if spec.type in {"matrix", "vector"}:
            if not isinstance(value, sp.MatrixBase):
                raise ParameterSamplingError(f"{name}: Matrix 결과가 필요합니다.")
            if spec.type == "vector" and value.cols != 1:
                raise ParameterSamplingError(f"{name}: 열벡터 결과가 필요합니다.")
            element = _element_spec(spec)
            for item in value:
                _validate_scalar(item, element)
            if spec.type == "matrix":
                valid_family = {
                    "general": True,
                    "square": value.rows == value.cols,
                    "symmetric": value.rows == value.cols and value == value.T,
                    "diagonal": value.rows == value.cols and value.is_diagonal() is True,
                }
                if not any(valid_family[family] for family in _families(spec)):
                    raise ParameterSamplingError(f"{name}: 파생 행렬이 allowed_families를 만족하지 않습니다.")
            elif spec.allowed_families:
                raise ParameterSamplingError("vector의 allowed_families는 미지원입니다.")
            return value
        # type='derived'는 반환 타입을 특정하지 않는다. 구체 타입 검증이 필요하면
        # type='integer' 등과 derived 설정을 함께 사용한다.
        return _validate_scalar(value, spec)
    except ParameterSamplingError:
        raise
    except Exception as exc:
        raise ParameterSamplingError(f"파생 파라미터 {name!r} 실행에 실패했습니다.") from exc


def _evaluate_derived_parameter_impl(
    name: str,
    spec: ParameterSpec,
    generated: Mapping[str, Any],
    rng: Random,
) -> Any:
    """다른 파라미터로부터 파생되는 값을 안전하게 계산한다."""

    derived = spec.derived

    if derived is None:
        raise ParameterSamplingError(
            f"파라미터 '{name}'에 derived 설정이 없습니다."
        )

    missing = [
        dependency
        for dependency in derived.depends_on
        if dependency not in generated
    ]

    if missing:
        raise ParameterSamplingError(
            f"파라미터 '{name}' 계산에 필요한 값이 "
            f"아직 생성되지 않았습니다: {', '.join(missing)}"
        )

    context = {
        dependency: generated[dependency]
        for dependency in derived.depends_on
    }

    if derived.engine == "registry":
        result = _evaluate_safe_expression(
            derived.expression,
            context,
            rng,
            allow_registry=True,
        )

    elif derived.engine == "sympy":
        result = _evaluate_safe_expression(
            derived.expression,
            context,
            rng,
            allow_registry=False,
        )

    elif derived.engine in {"python", "numpy"}:
        raise ParameterSamplingError(
            f"derived engine '{derived.engine}'은 "
            "아직 안전한 실행기가 구현되지 않았습니다."
        )

    else:
        raise ParameterSamplingError(
            f"지원하지 않는 derived engine입니다: "
            f"{derived.engine}"
        )

    if derived.selection is None:
        return result

    try:
        candidates = list(result)
    except TypeError as exc:
        raise ParameterSamplingError(
            f"파라미터 '{name}'의 selection을 적용할 수 없습니다."
        ) from exc

    if not candidates:
        raise ParameterSamplingError(
            f"파라미터 '{name}'의 파생 결과가 비어 있습니다."
        )

    if derived.selection == "first":
        return candidates[0]

    if derived.selection == "random":
        return rng.choice(candidates)

    raise ParameterSamplingError(
        f"지원하지 않는 selection입니다: "
        f"{derived.selection}"
    )


# 아래 과목별 함수는 설계용 주석이다. 현재 Python 함수로 정의되지 않는다.
# 구현·검증 후 호출 분기와 Registry에 연결하고 해당 과목을 활성화한다.


# [미적분 1: calculus_1 / 비활성]
# def sample_univariate_function(spec: ParameterSpec, generated: Mapping[str, Any], rng: Random) -> Any:
#     """TODO: 함수족·계수 범위에 맞는 일변수 식과 독립변수를 생성한다.
#
#     정의역을 함께 보존하고 분모·로그·근호 조건은 Evaluator로 전달한다.
#     """
#     raise NotImplementedError
#
# def sample_interval(spec: ParameterSpec, generated: Mapping[str, Any], rng: Random) -> Any:
#     """TODO: 양 끝점과 개폐 여부를 가진 구간을 생성한다."""
#     raise NotImplementedError
#
# def sample_sequence(spec: ParameterSpec, generated: Mapping[str, Any], rng: Random) -> Any:
#     """TODO: 수열·급수의 일반항, 정수 인덱스, 시작점을 생성한다."""
#     raise NotImplementedError
#


# [미적분 2: calculus_2 / 비활성]
# def sample_multivariate_function(spec: ParameterSpec, generated: Mapping[str, Any], rng: Random) -> Any:
#     """TODO: 변수 수·계수·정의역에 맞는 다변수 함수를 생성한다."""
#     raise NotImplementedError
#
# def sample_integration_region(spec: ParameterSpec, generated: Mapping[str, Any], rng: Random) -> Any:
#     """TODO: 좌표계·변수 순서·경계식을 가진 적분 영역을 생성한다."""
#     raise NotImplementedError
#
# def sample_vector_field(spec: ParameterSpec, generated: Mapping[str, Any], rng: Random) -> Any:
#     """TODO: 공간 차원에 맞는 벡터장과 성분 함수를 생성한다."""
#     raise NotImplementedError
#


# [공업수학: engineering_mathematics / 비활성]
# def sample_differential_equation(spec: ParameterSpec, generated: Mapping[str, Any], rng: Random) -> Any:
#     """TODO: 차수·계수·미지함수·초기/경계조건을 가진방정식을 생성한다.
#
#     행렬형 연립방정식에는 기존 행렬·벡터 샘플러를 재사용한다.
#     """
#     raise NotImplementedError
#
# def sample_transform_function(spec: ParameterSpec, generated: Mapping[str, Any], rng: Random) -> Any:
#     """TODO: 라플라스·푸리에 변환용 함수와 변환 정의·정의역을 생성한다."""
#     raise NotImplementedError
#
# def sample_complex_function(spec: ParameterSpec, generated: Mapping[str, Any], rng: Random) -> Any:
#     """TODO: 복소변수 함수와 정의역·분기 정보를 생성한다."""
#     raise NotImplementedError
#


# [확률통계: probability_statistics / 비활성]
# def sample_probability_distribution(spec: ParameterSpec, generated: Mapping[str, Any], rng: Random) -> Any:
#     """TODO: 문제에 등장하는 분포족·모수·표본공간을 생성한다.
#
#     ParameterSpec.distribution의 샘플링 방식과 문제의 확률분포를 구분한다.
#     """
#     raise NotImplementedError
#
# def sample_statistical_dataset(spec: ParameterSpec, generated: Mapping[str, Any], rng: Random) -> Any:
#     """TODO: 표본 크기·변수 수·생성 가정에 맞는 numeric_data를 생성한다.
#
#     공통 RNG로 seed 재현성을 유지하고 모수와 표본 통계량을 구분한다.
#     """
#     raise NotImplementedError
#
