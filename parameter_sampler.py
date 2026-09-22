"""여러 과목에서 공유하는 파라미터 샘플러 골격.

배치 생성 코드에서 사용하는 파일이다.
저장 위치: scripts/problems/parameter_sampler.py

현재 활성화한 함수 틀:
- 정수·유리수·실수
- 벡터·행렬
- 행렬 크기 의존관계
- 다른 값으로부터 계산되는 파생 파라미터

공통 함수와 선형대수 함수만 주석 없이 선언한다. 실제 계산 로직은 TODO 상태다.
미적분 1·2, 공업수학, 확률통계 함수 틀은 파일 아래에 주석으로 보관한다.
공통 함수는 특정 과목에 고정하지 않고 다른 과목에서도 재사용한다.
과목별 연결과 활성 목록은 problem_instance_generator.py에서 관리한다.
Constraint 만족 여부는 constraint_evaluator.py가 담당한다.
"""

from __future__ import annotations

from collections.abc import Mapping
from random import Random
from typing import Any

from sympy import Matrix

from app.schemas.generation_rule import ParameterSpec, RangeSpec, ShapeSpec

import ast


class ParameterSamplingError(RuntimeError):
    """파라미터를 생성할 수 없을 때 사용하는 예외."""


def _random_index(n: int, *, rng: Random) -> int:
    if isinstance(n, bool) or not isinstance(n, int):
        raise ParameterSamplingError(
            f"random_index의 n은 정수여야 합니다: {n!r}"
        )

    if n < 1:
        raise ParameterSamplingError(
            "random_index의 n은 1 이상이어야 합니다."
        )

    return rng.randrange(n)


def _random_distinct_index(
    n: int,
    target_row: int,
    *,
    rng: Random,
) -> int:
    if isinstance(n, bool) or not isinstance(n, int):
        raise ParameterSamplingError(
            f"random_distinct_index의 n은 정수여야 합니다: {n!r}"
        )

    if n < 2:
        raise ParameterSamplingError(
            "서로 다른 두 행을 선택하려면 n은 2 이상이어야 합니다."
        )

    if (
        isinstance(target_row, bool)
        or not isinstance(target_row, int)
        or not 0 <= target_row < n
    ):
        raise ParameterSamplingError(
            f"target_row가 범위를 벗어났습니다: {target_row!r}"
        )

    candidates = [
        index
        for index in range(n)
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
            return node.value

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

    if spec.generator is not None:
        raise ParameterSamplingError(
            f"파라미터 '{name}'의 generator "
            f"'{spec.generator}'는 아직 구현되지 않았습니다."
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

        return sample_matrix(
            spec,
            shape,
            rng,
        )

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
        if isinstance(value, bool) or not isinstance(value, int):
            raise ParameterSamplingError(
                f"파라미터 '{name}'의 {field_name} 크기는 정수여야 합니다: "
                f"{value!r}"
            )

        if value < 1:
            raise ParameterSamplingError(
                f"파라미터 '{name}'의 {field_name} 크기는 1 이상이어야 합니다: "
                f"{value}"
            )

        return value

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
        if isinstance(value, int):
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
        for field_name in (
            "rows",
            "cols",
            "dimension",
            "length",
            "size",
        ):
            value = getattr(shape, field_name)

            if value is not None:
                resolved[field_name] = resolve_value(
                    field_name,
                    value,
                )

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


def sample_scalar(spec: ParameterSpec, rng: Random) -> Any:
    """범위·선택지·제외값을 반영해 스칼라 값을 생성한다.

    현재 지원:
    - integer
    - choices가 명시된 파라미터

    아직 실제 Rule에서 사용하지 않는 rational/real은
    명시적으로 미지원 처리한다.
    """

    if spec.distribution not in (None, "uniform"):
        raise ParameterSamplingError(
            f"지원하지 않는 distribution입니다: {spec.distribution}"
        )

    # choices가 명시되어 있으면 범위보다 우선한다.
    if spec.choices:
        candidates = [
            value
            for value in spec.choices
            if value not in spec.exclude
        ]

        if not candidates:
            raise ParameterSamplingError(
                "choices에서 exclude를 제외한 생성 가능한 값이 없습니다."
            )

        return rng.choice(candidates)

    if spec.type == "integer":
        if spec.min is None or spec.max is None:
            raise ParameterSamplingError(
                "integer 파라미터에는 min과 max가 필요합니다."
            )

        if isinstance(spec.min, bool) or not isinstance(spec.min, int):
            raise ParameterSamplingError(
                "integer 파라미터의 min은 정수여야 합니다."
            )

        if isinstance(spec.max, bool) or not isinstance(spec.max, int):
            raise ParameterSamplingError(
                "integer 파라미터의 max는 정수여야 합니다."
            )

        step = spec.step if spec.step is not None else 1

        if isinstance(step, bool) or not isinstance(step, int):
            raise ParameterSamplingError(
                "integer 파라미터의 step은 정수여야 합니다."
            )

        if step <= 0:
            raise ParameterSamplingError(
                "integer 파라미터의 step은 1 이상이어야 합니다."
            )

        candidates = [
            value
            for value in range(spec.min, spec.max + 1, step)
            if value not in spec.exclude
        ]

        if not candidates:
            raise ParameterSamplingError(
                "범위와 exclude 조건을 만족하는 정수가 없습니다."
            )

        return rng.choice(candidates)

    if spec.type in {"real", "rational"}:
        raise ParameterSamplingError(
            f"'{spec.type}' scalar sampling은 아직 구현되지 않았습니다."
        )

    raise ParameterSamplingError(
        f"sample_scalar()가 지원하지 않는 타입입니다: {spec.type}"
    )


def sample_vector(
    spec: ParameterSpec,
    shape: Mapping[str, int],
    rng: Random,
) -> Any:
    """차원과 원소 범위에 맞는 SymPy 열벡터를 생성한다."""

    dimension = shape.get("dimension")

    if dimension is None:
        dimension = shape.get("length")

    if dimension is None:
        raise ParameterSamplingError(
            "vector 파라미터에는 dimension 또는 length가 필요합니다."
        )

    if dimension < 1:
        raise ParameterSamplingError(
            "vector의 차원은 1 이상이어야 합니다."
        )

    element_type = spec.element_type or "integer"

    element_min = (
        spec.element_min
        if spec.element_min is not None
        else spec.min
    )

    element_max = (
        spec.element_max
        if spec.element_max is not None
        else spec.max
    )

    element_spec = spec.model_copy(
        update={
            "type": element_type,
            "min": element_min,
            "max": element_max,
            "shape": None,
            "depends_on": [],
            "derived": None,
        }
    )

    values = [
        sample_scalar(element_spec, rng)
        for _ in range(dimension)
    ]

    return Matrix(values)


def sample_matrix(
    spec: ParameterSpec,
    shape: Mapping[str, int],
    rng: Random,
) -> Any:
    """행·열과 원소 범위에 맞는 SymPy 행렬을 생성한다."""

    rows = shape.get("rows")
    cols = shape.get("cols")

    if rows is None or cols is None:
        raise ParameterSamplingError(
            "matrix 파라미터에는 rows와 cols가 모두 필요합니다."
        )

    if rows < 1 or cols < 1:
        raise ParameterSamplingError(
            "matrix의 rows와 cols는 1 이상이어야 합니다."
        )

    element_type = spec.element_type or "integer"

    element_min = (
        spec.element_min
        if spec.element_min is not None
        else spec.min
    )

    element_max = (
        spec.element_max
        if spec.element_max is not None
        else spec.max
    )

    element_spec = spec.model_copy(
        update={
            "type": element_type,
            "min": element_min,
            "max": element_max,
            "shape": None,
            "depends_on": [],
            "derived": None,
        }
    )

    values = [
        sample_scalar(element_spec, rng)
        for _ in range(rows * cols)
    ]

    return Matrix(rows, cols, values)


def evaluate_derived_parameter(
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
