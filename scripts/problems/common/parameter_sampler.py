"""오프라인 문제 생성용 공통·선형대수 파라미터 샘플러.

저장 위치: scripts/parameter_sampler.py
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
- 다른 과목의 지원 타입과 설정 예시는 파일 아래 NEW_TYPE_SAMPLERS를 참고한다.
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

                if function_name in SYMBOLIC_DERIVED_FUNCTIONS:
                    return SYMBOLIC_DERIVED_FUNCTIONS[function_name](*args)

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
    # TODO[LA-D007] sample_parameters 구현
    # 1. 정책과 같은 seed로 결과가 재현되는지, 파라미터 순서·depends_on·derived 평가가 유지되는지 검증한다.
    # 2. 생성 실패/재시도 원인을 기록할 연결 지점을 마련한다.
    raise NotImplementedError("TODO[LA-D007]: sample_parameters")


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
    # TODO[LA-D008] sample_parameter 구현
    # 1. 복소 내적 등 특수 분기에서 하드코딩한 후보와 분수 지원을 확인한다.
    # 2. 유형별 수학 조건을 지키면서 확대하고 모든 과목에 전역 적용하지 않는다.
    raise NotImplementedError("TODO[LA-D008]: sample_parameter")


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
    # TODO[LA-D009] sample_scalar 구현
    # 1. 고정 분모 10 격자 외에 opt-in 유리수 정책을 구현한다.
    # 2. 기약분수 중복·분모 부호·0분모·exclude·step·choices를 처리하고, 분자/분모 균등과 값 균등의 차이를 명시한다.
    # 3. legacy 모드의 seed 결과는 보존한다.
    raise NotImplementedError("TODO[LA-D009]: sample_scalar")


def _element_spec(spec: ParameterSpec) -> ParameterSpec:
    # TODO[LA-D010] _element_spec 구현
    # 1. 행렬·벡터의 element_* 유리수 옵션과 가중치가 스칼라 설정으로 올바르게 전달되도록 한다.
    # 2. 외부 객체용 옵션을 스칼라에 잘못 적용하거나 기존 사용자 설정을 잃지 않는다.
    raise NotImplementedError("TODO[LA-D010]: _element_spec")


def sample_vector(spec: ParameterSpec, shape: Mapping[str, int], rng: Random) -> Any:
    # TODO[LA-D011] sample_vector 구현
    # 1. 실수 벡터/복소 벡터에서 계수 분포와 구조를 다양화한다.
    # 2. 차원, 0벡터 금지, 복소 내적 조건을 지킨다.
    raise NotImplementedError("TODO[LA-D011]: sample_vector")


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
    # TODO[LA-D012] sample_matrix 구현
    # 1. 숫자 범위뿐 아니라 성긴/조밀/비대각 구조를 유형별로 선택한다.
    # 2. SVD·대각화·양의 정부호 등의 전제조건은 생성 과정에서 보장한다.
    # 3. 특수 생성기 호출에 spec/정책을 전달하는 인터페이스도 기존 호출과 호환되게 확장한다.
    raise NotImplementedError("TODO[LA-D012]: sample_matrix")


def _small_svd_matrix(rows: int, cols: int, rng: Random) -> Any:
    # TODO[LA-D013] _small_svd_matrix 구현
    # 1. 대각/반대각 형태만 생성하는 제한을 확장한다.
    # 2. 합리적인 유리 직교변환과 분리된 특이값으로 조밀한 행렬도 생성한다.
    # 3. 최적 rank-1 근사의 비유일성·계산량·원소 범위를 확인한다.
    raise NotImplementedError("TODO[LA-D013]: _small_svd_matrix")


def _rank_one_pseudoinverse_matrix(rows: int, cols: int, rng: Random) -> Any:
    # TODO[LA-D014] _rank_one_pseudoinverse_matrix 구현
    # 1. 한 열 또는 한 행만 0이 아닌 제한을 넘어 A=u*v.T 형태로 조밀한 rank-1 예제를 생성한다.
    # 2. u,v 비영 조건과 정확한 유리수 계산을 검증한다.
    raise NotImplementedError("TODO[LA-D014]: _rank_one_pseudoinverse_matrix")


def _centered_pca_matrix(rows: int, cols: int, rng: Random) -> Any:
    # TODO[LA-D015] _centered_pca_matrix 구현
    # 1. 축 방향/45도 방향 고정 조합을 확장한다.
    # 2. 표본 중심화, 열 차원, 유일한 최대 고유값 및 주성분 부호 동치를 유지한다.
    raise NotImplementedError("TODO[LA-D015]: _centered_pca_matrix")


def _defective_jordan_matrix(rows: int, cols: int, rng: Random) -> Any:
    # TODO[LA-D016] _defective_jordan_matrix 구현
    # 1. 표준 Jordan 블록 외에 가역변환 P*J*P.inv()로 다양한 표현을 만든다.
    # 2. 결함 행렬 조건과 기하적 중복도, 정확한 계수, 연산량을 확인한다.
    raise NotImplementedError("TODO[LA-D016]: _defective_jordan_matrix")


def _easy_orthogonal_columns(rows: int, cols: int, rng: Random) -> Any:
    # TODO[LA-D017] _easy_orthogonal_columns 구현
    # 1. 세 기본 조합의 부호·순열 반복을 확장한다.
    # 2. 정수/유리 직교 열벡터를 구성하고 full column rank·직교성·노름과 QR/Gram-Schmidt의 정답 난도 조건을 유지한다.
    raise NotImplementedError("TODO[LA-D017]: _easy_orthogonal_columns")


def _small_integer_spectrum_symmetric(rows: int, cols: int, rng: Random) -> Any:
    # TODO[LA-D018] _small_integer_spectrum_symmetric 구현
    # 1. 고정 2x2 대칭 블록·작은 정수 스펙트럼 제한을 opt-in 정책으로 확장한다.
    # 2. 유리 직교 유사변환으로 대칭성을 유지하고 고유값 간격·중복도·검증기 지원 차원을 관리한다.
    raise NotImplementedError("TODO[LA-D018]: _small_integer_spectrum_symmetric")


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
        if spec.type in {'expression', 'function', 'univariate_function',
                         'multivariate_function', 'transform_function', 'complex_function'}:
            if not isinstance(value, sp.Expr) or value.has(sp.nan, sp.oo, -sp.oo, sp.zoo):
                raise ParameterSamplingError(f'{name}: 유한한 SymPy 수식이 필요합니다.')
            return value
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

    if spec.type in {'expression', 'function', 'univariate_function',
                     'multivariate_function', 'transform_function', 'complex_function'}:
        defaults = ('x',)
        if spec.type == 'multivariate_function':
            defaults = ('x','y')
        elif spec.type == 'complex_function':
            defaults = ('z',)
        elif spec.type == 'transform_function':
            defaults = ('t',)
        for variable in _variables(spec, defaults, complex_variable=spec.type == 'complex_function'):
            if str(variable) in context:
                raise ParameterSamplingError('기호 이름과 파라미터 이름이 충돌합니다.')
            context[str(variable)] = variable

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


# ---------------------------------------------------------------------------
# 미적분·공업수학·확률통계용 샘플러
# ParameterSpec.extra 필드로 설정을 전달하며 새 Schema 파일은 필요하지 않다.
# ---------------------------------------------------------------------------


def _option(spec: ParameterSpec, name: str, default: Any = None) -> Any:
    return getattr(spec, name, default)


def _symbol(value: Any, *, integer: bool = False, complex_variable: bool = False) -> sp.Symbol:
    if isinstance(value, sp.Symbol):
        if integer and value.is_integer is not True:
            raise ParameterSamplingError('수열 인덱스에는 정수 기호가 필요합니다.')
        if not integer and not complex_variable and value.is_real is not True:
            raise ParameterSamplingError('실수 함수에는 real=True 기호가 필요합니다.')
        return value
    if not isinstance(value, str) or not value.isidentifier() or value.startswith('_'):
        raise ParameterSamplingError('변수 이름은 유효한 공개 식별자여야 합니다.')
    if integer:
        return sp.Symbol(value, integer=True, positive=True)
    if complex_variable:
        return sp.Symbol(value)
    return sp.Symbol(value, real=True)


def _variables(spec: ParameterSpec, default: tuple[str, ...], *, complex_variable: bool = False) -> tuple[sp.Symbol, ...]:
    names = _option(spec, 'variables', None)
    if names is None:
        names = [_option(spec, 'variable', default[0])] if len(default) == 1 else list(default)
    if not isinstance(names, (list, tuple)) or not 1 <= len(names) <= 3:
        raise ParameterSamplingError('variables는 서로 다른 변수 1~3개의 목록이어야 합니다.')
    variables = tuple(_symbol(name, complex_variable=complex_variable) for name in names)
    if len(set(variables)) != len(variables):
        raise ParameterSamplingError('변수 이름이 중복됩니다.')
    return variables


def _family(spec: ParameterSpec, rng: Random, allowed: set[str], default: str) -> str:
    selected = _option(spec, 'family', None)
    if spec.generator is not None:
        if selected is not None and selected != spec.generator:
            raise ParameterSamplingError('family와 generator가 서로 다릅니다.')
        selected = spec.generator
    candidates = list(spec.allowed_families) or [selected or default]
    if selected is not None:
        if selected not in candidates:
            raise ParameterSamplingError('family가 allowed_families에 없습니다.')
        candidates = [selected]
    unknown = set(candidates) - allowed
    if unknown:
        raise ParameterSamplingError(f'미지원 함수/분포족: {sorted(unknown)}')
    return rng.choice(candidates)


def _coefficient_spec(spec: ParameterSpec) -> ParameterSpec:
    # TODO[LA-D019] _coefficient_spec 구현
    # 1. 계수 옵션 전달 방식의 참고 지점.
    # 2. 선형대수는 주로 matrix/vector 원소를 사용하므로 이 함수만 바꾸면 해결된다고 가정하지 않는다.
    # 3. 미적분 등 다른 과목의 기본값은 보존한다.
    raise NotImplementedError("TODO[LA-D019]: _coefficient_spec")


def _coeff(spec: ParameterSpec, rng: Random, *, nonzero: bool = False) -> Any:
    scalar = _coefficient_spec(spec)
    if nonzero:
        scalar = scalar.model_copy(update={'exclude': [*scalar.exclude, 0]})
    return sample_scalar(scalar, rng)


def _degree(spec: ParameterSpec, rng: Random) -> int:
    fixed = _option(spec, 'degree', None)
    lower = _integer(fixed if fixed is not None else _option(spec, 'degree_min', 1), 'degree_min')
    upper = _integer(fixed if fixed is not None else _option(spec, 'degree_max', 3), 'degree_max')
    if not 0 <= lower <= upper <= 8:
        raise ParameterSamplingError('다항식 차수는 0~8의 범위여야 합니다.')
    return rng.randint(lower, upper)


def _generated_function(spec: ParameterSpec, rng: Random, variables: tuple[sp.Symbol, ...], family: str) -> sp.Expr:
    x = variables[0]
    if family == 'polynomial':
        degree = _degree(spec, rng)
        # 상수항은 한 번만 생성하여 다변수에서도 계수 범위를 보존한다.
        result = _coeff(spec, rng, nonzero=degree == 0)
        for variable in variables:
            for power in range(1, degree + 1):
                result += _coeff(spec, rng, nonzero=power == degree) * variable**power
        return sp.expand(result)
    if len(variables) != 1:
        raise ParameterSamplingError('다변수 자동 함수족은 polynomial만 지원합니다.')
    a = _coeff(spec, rng, nonzero=True)
    b = _coeff(spec, rng)
    if family == 'rational':
        return (a*x + b)/(x + _coeff(spec, rng))
    if family == 'exponential':
        return a*sp.exp(_coeff(spec, rng, nonzero=True)*x) + b
    if family == 'logarithmic':
        return a*sp.log(x + b)
    if family == 'trigonometric':
        return a*rng.choice([sp.sin, sp.cos])(_coeff(spec, rng, nonzero=True)*x) + b
    if family == 'gaussian':
        return a*sp.exp(-rng.randint(1, 3)*x**2)
    raise ParameterSamplingError(f'미지원 함수족: {family}')


def sample_univariate_function(spec: ParameterSpec, generated: Mapping[str, Any], rng: Random) -> Any:
    """작은 일변수 SymPy 식을 반환한다. 정의역은 Rule의 별도 interval로 선언한다.

    variable='x', degree_min/max, min/max(계수 범위), allowed_families를 사용한다.
    표현식 문자열을 eval/sympify로 실행하지 않는다.
    """
    variables = _variables(spec, ('x',))
    if len(variables) != 1:
        raise ParameterSamplingError('일변수 함수에는 변수 하나가 필요합니다.')
    family = _family(spec, rng, {'polynomial','rational','exponential','logarithmic','trigonometric'}, 'polynomial')
    return _generated_function(spec, rng, variables, family)


def _reference(value: Any, generated: Mapping[str, Any]) -> Any:
    if isinstance(value, str):
        if value not in generated:
            raise ParameterSamplingError(f'선언하고 먼저 생성해야 할 참조: {value}')
        return generated[value]
    return value


def sample_interval(spec: ParameterSpec, generated: Mapping[str, Any], rng: Random) -> sp.Interval:
    """lower/upper로 고정값 또는 파라미터 이름을 지정한다. 없으면 두 끝점을 뽑는다."""
    if spec.generator is not None or spec.allowed_families:
        raise ParameterSamplingError('interval에는 generator/allowed_families를 사용하지 않습니다.')
    lower, upper = _option(spec, 'lower'), _option(spec, 'upper')
    if (lower is None) != (upper is None):
        raise ParameterSamplingError('lower와 upper는 함께 지정해야 합니다.')
    if lower is None:
        scalar = _coefficient_spec(spec)
        a = sample_scalar(scalar, rng)
        second = scalar.model_copy(update={'exclude': [*scalar.exclude, a]})
        b = sample_scalar(second, rng)
        lower, upper = sorted((a, b))
    else:
        lower = _number(_reference(lower, generated))
        upper = _number(_reference(upper, generated))
    if not lower < upper:
        raise ParameterSamplingError('구간은 lower < upper여야 합니다.')
    left_open = _option(spec, 'left_open', False)
    right_open = _option(spec, 'right_open', False)
    if type(left_open) is not bool or type(right_open) is not bool:
        raise ParameterSamplingError('구간의 개폐 설정은 bool이어야 합니다.')
    return sp.Interval(lower, upper, left_open=left_open, right_open=right_open)


def sample_sequence(spec: ParameterSpec, generated: Mapping[str, Any], rng: Random) -> dict[str, Any]:
    """일반항·인덱스·시작점·분류를 반환한다. geometric/p_series/arithmetic 지원."""
    n = _symbol(_option(spec, 'index', 'n'), integer=True)
    start = _integer(_reference(_option(spec, 'start', 1), generated), 'start')
    if start < 1:
        raise ParameterSamplingError('수열의 start는 1 이상이어야 합니다.')
    family = _family(spec, rng, {'geometric','p_series','arithmetic'}, 'geometric')
    a = _coeff(spec, rng, nonzero=True)
    if family == 'geometric':
        ratio = _option(spec, 'ratio', None)
        ratio = sp.Rational(rng.choice([-3,-2,-1,1,2,3]), 4) if ratio is None else _number(_reference(ratio, generated))
        term = a*ratio**(n-start)
    elif family == 'p_series':
        p = _integer(_reference(_option(spec, 'power', 2), generated), 'power')
        term = a/n**p
    else:
        term = a + _coeff(spec, rng)*(n-start)
    return {'term': term, 'index': n, 'start': start, 'family': family}


def sample_multivariate_function(spec: ParameterSpec, generated: Mapping[str, Any], rng: Random) -> sp.Expr:
    variables = _variables(spec, ('x','y'))
    if len(variables) < 2:
        raise ParameterSamplingError('다변수 함수에는 2~3개 변수가 필요합니다.')
    family = _family(spec, rng, {'polynomial'}, 'polynomial')
    return _generated_function(spec, rng, variables, family)


def sample_integration_region(spec: ParameterSpec, generated: Mapping[str, Any], rng: Random) -> dict[str, Any]:
    """직교좌표의 직사각형/직육면체 또는 2차원 삼각형 영역.

    box: variables=['x','y'], bounds=[[0,2],[0,3]] (숫자/참조 이름).
    triangle: extent=2 -> 0<=x<=2, 0<=y<=2-x. bounds 순서는 바깥 변수부터다.
    """
    variables = _variables(spec, ('x','y'))
    family = _family(spec, rng, {'box','triangle'}, 'box')
    if _option(spec, 'coordinate_system', 'cartesian') != 'cartesian':
        raise ParameterSamplingError('현재 영역 샘플러는 직교좌표만 지원합니다.')
    if family == 'triangle':
        if len(variables) != 2:
            raise ParameterSamplingError('triangle에는 변수 2개가 필요합니다.')
        extent = _number(_reference(_option(spec, 'extent', rng.randint(1, 4)), generated))
        if extent <= 0:
            raise ParameterSamplingError('extent는 양수여야 합니다.')
        x,y = variables
        bounds = ((x, sp.Integer(0), extent), (y, sp.Integer(0), extent-x))
    else:
        raw = _option(spec, 'bounds', None)
        if raw is None:
            raw = [[0, rng.randint(1,4)] for _ in variables]
        if not isinstance(raw, (list,tuple)) or len(raw) != len(variables):
            raise ParameterSamplingError('bounds 수와 변수 수가 다릅니다.')
        bounds = []
        for variable, pair in zip(variables, raw):
            if not isinstance(pair,(list,tuple)) or len(pair) != 2:
                raise ParameterSamplingError('각 경계에는 lower/upper가 필요합니다.')
            lower,upper = (_number(_reference(v,generated)) for v in pair)
            if not lower < upper:
                raise ParameterSamplingError('적분 영역의 lower < upper 조건이 필요합니다.')
            bounds.append((variable,lower,upper))
        bounds = tuple(bounds)
    return {'variables': variables, 'bounds': bounds, 'coordinate_system': 'cartesian', 'family': family}


def sample_vector_field(spec: ParameterSpec, generated: Mapping[str, Any], rng: Random) -> sp.Matrix:
    variables = _variables(spec, ('x','y','z'))
    family = _family(spec, rng, {'polynomial'}, 'polynomial')
    return Matrix([_generated_function(spec,rng,variables,family) for _ in variables])


def sample_differential_equation(spec: ParameterSpec, generated: Mapping[str, Any], rng: Random) -> dict[str, Any]:
    """상수계수 선형 1/2차 ODE와 같은 점에서의 초기조건을 생성한다.

    반환값: equation(Eq), variable, function, order, initial_conditions(list).
    ODE 시스템·PDE·경계값 문제를 임의로 추측하지 않는다.
    """
    family = _family(spec, rng, {'linear_constant'}, 'linear_constant')
    variables = _variables(spec, ('t',))
    if len(variables) != 1:
        raise ParameterSamplingError('ODE에는 독립변수 하나가 필요합니다.')
    t = variables[0]
    order = _integer(_option(spec, 'order', 1), 'order')
    if order not in (1,2):
        raise ParameterSamplingError('ODE 자동 생성 차수는 1 또는 2입니다.')
    name = _option(spec, 'function_name', 'y')
    if not isinstance(name,str) or not name.isidentifier() or name.startswith('_'):
        raise ParameterSamplingError('미지함수 이름이 올바르지 않습니다.')
    y = sp.Function(name)(t)
    lhs = sp.diff(y,t,order)
    for k in range(order):
        lhs += _coeff(spec,rng)*sp.diff(y,t,k)
    point = _number(_reference(_option(spec,'initial_point',0),generated))
    conditions = [{'order':k, 'point':point, 'value':_coeff(spec,rng)} for k in range(order)]
    return {'equation':sp.Eq(lhs,_coeff(spec,rng)), 'variable':t, 'function':y,
            'order':order, 'initial_conditions':conditions, 'family':family}


def sample_transform_function(spec: ParameterSpec, generated: Mapping[str, Any], rng: Random) -> sp.Expr:
    variables = _variables(spec, ('t',))
    if len(variables) != 1:
        raise ParameterSamplingError('변환 함수에는 변수 하나가 필요합니다.')
    family = _family(spec,rng,{'polynomial','exponential','trigonometric','gaussian'},'exponential')
    return _generated_function(spec,rng,variables,family)


def sample_complex_function(spec: ParameterSpec, generated: Mapping[str, Any], rng: Random) -> sp.Expr:
    variables = _variables(spec, ('z',), complex_variable=True)
    if len(variables) != 1:
        raise ParameterSamplingError('복소함수에는 변수 하나가 필요합니다.')
    family = _family(spec,rng,{'polynomial','rational','exponential','trigonometric'},'polynomial')
    return _generated_function(spec,rng,variables,family)


def sample_probability_distribution(spec: ParameterSpec, generated: Mapping[str, Any], rng: Random) -> dict[str, Any]:
    """분포족과 모수를 반환한다. sampling distribution 옵션과 문제의 분포족은 별개다.

    family='binomial', parameters={'n':5,'p':'p'}처럼 참조 이름을 사용할 수 있다.
    모수 검사는 constraint_evaluator.is_valid_probability_distribution이 담당한다.
    """
    family = _family(spec,rng,{'bernoulli','binomial','poisson','normal','uniform','exponential'},'binomial')
    raw = _option(spec,'parameters',{})
    if not isinstance(raw, Mapping):
        raise ParameterSamplingError('분포의 parameters는 객체여야 합니다.')
    defaults = {'bernoulli':{'p':sp.Rational(rng.randint(1,9),10)},
                'binomial':{'n':rng.randint(2,8),'p':sp.Rational(rng.randint(1,9),10)},
                'poisson':{'rate':rng.randint(1,4)},
                'normal':{'mu':rng.randint(-3,3),'sigma':rng.randint(1,3)},
                'uniform':{'lower':0,'upper':rng.randint(1,5)},
                'exponential':{'rate':rng.randint(1,4)}}[family]
    if set(raw)-set(defaults):
        raise ParameterSamplingError(f'해당 분포의 미지원 모수: {set(raw)-set(defaults)}')
    parameters = {key:_number(_reference(raw.get(key,value),generated)) for key,value in defaults.items()}
    p = parameters.get('p')
    if p is not None and not 0 <= p <= 1:
        raise ParameterSamplingError('확률 p는 0~1이어야 합니다.')
    if family=='binomial' and (parameters['n'].is_Integer is not True or parameters['n']<0):
        raise ParameterSamplingError('이항분포 n은 음이 아닌 정수여야 합니다.')
    for key in ('sigma','rate'):
        if key in parameters and parameters[key]<=0:
            raise ParameterSamplingError(f'{key}는 양수여야 합니다.')
    if family=='uniform' and not parameters['lower']<parameters['upper']:
        raise ParameterSamplingError('균등분포 lower < upper 조건이 필요합니다.')
    return {'family':family,'parameters':parameters}


def sample_statistical_dataset(spec: ParameterSpec, generated: Mapping[str, Any], rng: Random) -> Any:
    """numeric_data를 list 또는 행 단위 list로 반환한다.

    shape.size로 표본 수, variable_count로 열 수를 지정한다(최대 10000 x 20).
    data_family='uniform'은 원소 조건을 적용하고 'normal'은 실수 정규표본을 만든다.
    표본 자체에 독립성/정규성의 증명이 포함된 것으로 취급하지 않는다.
    """
    if spec.generator is not None or spec.allowed_families:
        raise ParameterSamplingError('numeric_data에는 data_family를 사용하세요.')
    shape = resolve_shape('dataset',spec.shape,spec,generated,rng)
    size = shape.get('size',shape.get('length'))
    columns = _integer(_option(spec,'variable_count',1),'variable_count')
    if size is None or not 1<=size<=10000 or not 1<=columns<=20:
        raise ParameterSamplingError('표본 수 1~10000, 열 수 1~20을 명시해야 합니다.')
    family = _option(spec,'data_family','uniform')
    element = _element_spec(spec)
    if family=='uniform':
        rows = [[sample_scalar(element,rng) for _ in range(columns)] for _ in range(size)]
    elif family=='normal':
        if spec.element_type not in (None,'real'):
            raise ParameterSamplingError('정규표본의 element_type은 real이어야 합니다.')
        mu = float(_number(_reference(_option(spec,'mu',0),generated)))
        sigma = float(_number(_reference(_option(spec,'sigma',1),generated)))
        if not math.isfinite(mu) or not math.isfinite(sigma) or sigma<=0:
            raise ParameterSamplingError('유한한 평균과 양의 표준편차가 필요합니다.')
        element = element.model_copy(update={'type':'real'})
        rows = [[_validate_scalar(rng.gauss(mu,sigma),element) for _ in range(columns)] for _ in range(size)]
    else:
        raise ParameterSamplingError(f'미지원 표본 생성 방식: {family}')
    if columns==1:
        return [row[0] for row in rows]
    return rows


NEW_TYPE_SAMPLERS = {
    'expression':sample_univariate_function, 'function':sample_univariate_function,
    'univariate_function':sample_univariate_function, 'interval':sample_interval,
    'sequence':sample_sequence, 'series':sample_sequence,
    'multivariate_function':sample_multivariate_function,
    'integration_region':sample_integration_region, 'vector_field':sample_vector_field,
    'differential_equation':sample_differential_equation,
    'transform_function':sample_transform_function, 'complex_function':sample_complex_function,
    'probability_distribution':sample_probability_distribution,
    'numeric_data':sample_statistical_dataset, 'statistical_dataset':sample_statistical_dataset,
}

# eval 없이 사용할 수 있는 파생 수식 함수. 기존 선형대수 함수 계약은 유지한다.
SYMBOLIC_DERIVED_FUNCTIONS = {
    'sin':sp.sin, 'cos':sp.cos, 'exp':sp.exp, 'log':sp.log, 'sqrt':sp.sqrt,
    'Abs':sp.Abs, 'diff':sp.diff,
}
