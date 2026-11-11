"""Offline ProblemInstance generation for configured subject templates.

Generate validated payloads without writing to the database. Draft templates
may be exercised for review; callers must only publish eligible results.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, field
from fractions import Fraction
import math
import re
from numbers import Integral, Real
from typing import Any

import numpy as np
import sympy as sp
from jinja2 import Environment, StrictUndefined, TemplateSyntaxError, UndefinedError

from app.schemas.problem_template import ProblemTemplate
from scripts.problems.common import constraint_evaluator, math_validators, parameter_sampler


class ProblemGenerationError(RuntimeError):
    """A template cannot produce a verified instance."""


@dataclass(frozen=True, slots=True)
class GenerationAttempt:
    attempt: int
    seed: int
    passed: bool
    stage: str
    message: str | None = None


@dataclass(frozen=True, slots=True)
class GenerationResult:
    instance: dict[str, Any]
    seed: int
    attempts: list[GenerationAttempt] = field(default_factory=list)


def validate_template_preconditions(template: ProblemTemplate) -> None:
    if template.taxonomy.subject_id not in ENABLED_SUBJECT_IDS:
        raise ProblemGenerationError(f"Inactive subject: {template.taxonomy.subject_id}")
    if template.generation_rule_status == "draft_auto":
        raise ProblemGenerationError("미구현 draft_auto Rule은 실행할 수 없습니다.")
    if not template.executable or template.status == "deprecated":
        raise ProblemGenerationError(f"Non-executable template: {template.template_id}")
    if not template.problem_builder.text_templates_ko:
        raise ProblemGenerationError("Missing problem text template")
    if template.answer_spec.engine not in {"sympy", "python"} or not template.answer_spec.cas_template:
        raise ProblemGenerationError("Missing supported answer expression")
    if not template.validation.validators or not all(v.required for v in template.validation.validators):
        raise ProblemGenerationError("At least one required validator is needed")
    if not template.validation.all_required_must_pass:
        raise ProblemGenerationError("All required validators must pass")
    missing = set(template.problem_builder.required_objects) - (set(template.parameters) | set(template.symbols))
    if missing:
        raise ProblemGenerationError(f"Undeclared required objects: {sorted(missing)}")
    for validator in template.validation.validators:
        try:
            math_validators.get_validator(validator.name, template.answer_spec.answer_type)
        except ValueError as exc:
            raise ProblemGenerationError(str(exc)) from exc


def prepare_linear_algebra_context(template: ProblemTemplate) -> dict[str, Any]:
    """Bind the existing sampler, constraint engine, and math validator APIs."""
    sample = parameter_sampler.sample_parameters
    if template.classification.problem_type == "eigenvector_calculation":
        # A general 3x3 symmetric integer matrix can have algebraic eigenvalues
        # whose exact eigenvectors are extremely expensive to simplify. Apply
        # the already-supported integer-spectrum generator to this type alone.
        # Keep the Template and Rule objects immutable; other types still use
        # the original sampler without any parameter changes.
        def sample_eigenvector_parameters(parameter_specs: Mapping[str, Any], *, seed: int) -> dict[str, Any]:
            A = parameter_specs.get("A")
            lam = parameter_specs.get("lambda_val")
            if A is None or lam is None or A.type != "matrix" or (
                lam.derived is None or "A" not in lam.derived.depends_on
            ):
                raise parameter_sampler.ParameterSamplingError(
                    "eigenvector_calculation에는 A 및 A에서 파생되는 lambda_val이 필요합니다."
                )
            if A.generator not in (None, "small_integer_spectrum_symmetric"):
                raise parameter_sampler.ParameterSamplingError(
                    f"고유벡터 A의 기존 generator를 덮어쓸 수 없습니다: {A.generator}"
                )
            specs = dict(parameter_specs)
            specs["A"] = A.model_copy(update={"generator": "small_integer_spectrum_symmetric"})
            return parameter_sampler.sample_parameters(specs, seed=seed)

        sample = sample_eigenvector_parameters
    return {
        "sample": sample,
        "constraints": constraint_evaluator.evaluate_constraints,
        "answer": math_validators.compute_expected_answer,
        "validate": math_validators.run_math_validators,
    }


def prepare_common_subject_context(template: ProblemTemplate) -> dict[str, Any]:
    """추가 과목은 확장된 공통 엔진을 사용한다. 개별 Rule 계약은 실행 전에 검사한다."""
    return {
        "sample": parameter_sampler.sample_parameters,
        "constraints": constraint_evaluator.evaluate_constraints,
        "answer": math_validators.compute_expected_answer,
        "validate": math_validators.run_math_validators,
    }


SUBJECT_CONTEXT_BUILDERS: dict[str, Callable[[ProblemTemplate], dict[str, Any]]] = {
    "linear_algebra": prepare_linear_algebra_context,
    "calculus_1": prepare_common_subject_context,
    "calculus_2": prepare_common_subject_context,
    "engineering_mathematics": prepare_common_subject_context,
    "probability_statistics": prepare_common_subject_context,
}
ENABLED_SUBJECT_IDS: frozenset[str] = frozenset(SUBJECT_CONTEXT_BUILDERS)


def prepare_subject_context(template: ProblemTemplate) -> dict[str, Any]:
    subject = template.taxonomy.subject_id
    if subject not in SUBJECT_CONTEXT_BUILDERS:
        raise ProblemGenerationError(f"Inactive subject: {subject}")
    return SUBJECT_CONTEXT_BUILDERS[subject](template)


def _symbolic_values(template: ProblemTemplate, values: Mapping[str, Any]) -> dict[str, Any]:
    """symbol_spec는 무작위로 뽑지 않고 수식에서 사용할 기호로 만든다."""
    symbols: dict[str, Any] = {}
    for name, spec in template.symbols.items():
        if name in values:
            raise ProblemGenerationError(f"중복 파라미터/기호: {name}")
        assumptions = {k: v for k, v in spec.assumptions.items() if isinstance(v, bool)}
        dimension = spec.dimension
        if isinstance(dimension, str):
            match = re.fullmatch(r"([A-Za-z_]\w*)\.(rows|cols)", dimension)
            if match is None or match.group(1) not in values:
                raise ProblemGenerationError(f"기호 {name}의 미지원 차원 참조: {dimension}")
            matrix = values[match.group(1)]
            dimension = getattr(matrix, match.group(2))
        if dimension is not None:
            if isinstance(dimension, bool) or not isinstance(dimension, (Integral, sp.Integer)) or not 1 <= dimension <= 8:
                raise ProblemGenerationError(f"기호 {name}의 벡터 차원은 1~8이어야 합니다.")
            symbols[name] = sp.Matrix([
                sp.Symbol(f"{name}_{index}", **assumptions)
                for index in range(1, int(dimension) + 1)
            ])
        else:
            symbols[name] = sp.Symbol(name, **assumptions)
    return symbols


def _render(pattern: str, template: ProblemTemplate, values: Mapping[str, Any], *, latex: bool) -> str:
    symbols = {
        name: sp.Symbol(name, **{key: flag for key, flag in spec.assumptions.items() if isinstance(flag, bool)})
        for name, spec in template.symbols.items()
    }
    symbols.update(values)
    def display_value(value):
        if template.taxonomy.subject_id != "linear_algebra" and isinstance(value, Mapping) and {'term','index','start'} <= value.keys():
            term=sp.latex(value['term']) if latex else str(value['term'])
            return f"a_{value['index']} = {term} ({value['index']} ≥ {value['start']})"
        # 추가 과목은 숫자를 유지해 {{ a+b }}, {{ a*b }}를 산술식으로 렌더링한다.
        # 선형대수의 기존 문장 출력은 동일하게 유지한다.
        if template.taxonomy.subject_id != "linear_algebra" and isinstance(value, (int, float, sp.Number)):
            return value
        return sp.latex(value) if latex else str(value)
    display = {name: display_value(value) for name, value in symbols.items()}
    rendered = Environment(undefined=StrictUndefined, autoescape=False).from_string(pattern).render(display)
    if not rendered.strip() or "{{" in rendered or "{%" in rendered:
        raise ValueError("Unresolved placeholder in problem statement")
    return rendered


def render_problem_statement(template: ProblemTemplate, values: Mapping[str, Any]) -> str:
    return _render(template.problem_builder.text_templates_ko[0], template, values, latex=False)


def render_problem_latex(template: ProblemTemplate, values: Mapping[str, Any]) -> str | None:
    patterns = template.problem_builder.latex_templates
    return _render(patterns[0], template, values, latex=True) if patterns else None


def _json_value(value: Any) -> Any:
    """Preserve exact rational values as strings in JSON payloads."""
    if isinstance(value, sp.MatrixBase):
        return [[_json_value(value[row, col]) for col in range(value.cols)] for row in range(value.rows)]
    if isinstance(value, np.ndarray):
        return _json_value(value.tolist())
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if value is sp.true or value is sp.false or isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, sp.Rational):
        return int(value) if value.q == 1 else str(value)
    if isinstance(value, Fraction):
        return int(value) if value.denominator == 1 else str(value)
    if isinstance(value, np.generic):
        return _json_value(value.item())
    if isinstance(value, (str, bool, int, float)) or value is None:
        return value
    if isinstance(value, sp.Basic):
        return str(value)
    raise TypeError(f"Unsupported JSON value: {type(value).__name__}")


def _answer_fraction_grade(
    value: Any, path: str = "answer", *, max_fraction_part: int = 99,
) -> tuple[str | None, int]:
    """정확한 유리수 답만 허용하고 난이도를 매긴다.

    0: 정수/분류, 1: 한 자리/한 자리, 2: 한 자리/두 자리,
    3: 두 자리/두 자리. 무리수·소수 및 상한 초과 시 위치를 반환한다.
    """
    def rational_grade(numerator: int, denominator: int) -> tuple[str | None, int]:
        if denominator == 1:
            return None, 0
        if abs(numerator) > max_fraction_part or denominator > max_fraction_part:
            return path, 0
        if abs(numerator) <= 9 and denominator <= 9:
            return None, 1
        if abs(numerator) <= 9:
            return None, 2
        return None, 3

    def children(items: Any) -> tuple[str | None, int]:
        worst = 0
        for child_path, item in items:
            bad, grade = _answer_fraction_grade(
                item, child_path, max_fraction_part=max_fraction_part
            )
            if bad is not None:
                return bad, 0
            worst = max(worst, grade)
        return None, worst

    if value is sp.true or value is sp.false or isinstance(value, (bool, np.bool_)):
        return None, 0
    if isinstance(value, sp.MatrixBase):
        return children(
            (f"{path}[{row},{col}]", value[row, col])
            for row in range(value.rows) for col in range(value.cols)
        )
    if isinstance(value, np.ndarray):
        return _answer_fraction_grade(value.tolist(), path, max_fraction_part=max_fraction_part)
    if isinstance(value, np.generic):
        return _answer_fraction_grade(value.item(), path, max_fraction_part=max_fraction_part)
    if isinstance(value, Mapping):
        def mapping_entries() -> Any:
            for key, item in value.items():
                if not isinstance(key, str):
                    yield f"{path}.key", key
                yield f"{path}[{key!s}]", item
        return children(mapping_entries())
    if isinstance(value, (list, tuple, set, frozenset, sp.Tuple, sp.FiniteSet)):
        return children((f"{path}[{index}]", item) for index, item in enumerate(value))
    if isinstance(value, Fraction):
        return rational_grade(value.numerator, value.denominator)
    if isinstance(value, sp.Rational):
        return rational_grade(int(value.p), int(value.q))
    if isinstance(value, sp.Float):
        numeric = float(value)
        return (None, 0) if math.isfinite(numeric) and numeric.is_integer() else (path, 0)
    if isinstance(value, sp.Expr):
        if value.is_number:
            return path, 0  # 무리수·복소수 등은 작은 기약분수로 표시할 수 없다.
        # 1/x처럼 문자식이 분모에 있으면 분자·분모 자릿수를 평가할 수 없다.
        _, denominator = sp.fraction(value)
        if denominator != 1 and not denominator.is_Integer:
            return path, 0
        return children((f"{path}.arg{index}", part) for index, part in enumerate(value.args))
    if isinstance(value, sp.Basic):
        return children((f"{path}.arg{index}", part) for index, part in enumerate(value.args))
    if isinstance(value, Integral):
        return None, 0
    if isinstance(value, Real):
        numeric = float(value)
        return (None, 0) if math.isfinite(numeric) and numeric.is_integer() else (path, 0)
    if isinstance(value, str):
        if "/" not in value:
            return None, 0
        if not re.fullmatch(r"[+-]?\d+\s*/\s*[+-]?\d+", value.strip()):
            return path, 0
        try:
            fraction = Fraction(value.replace(" ", ""))
        except (ValueError, ZeroDivisionError):
            return path, 0
        return rational_grade(fraction.numerator, fraction.denominator)
    if value is None:
        return None, 0
    return path, 0


def _bind_subject_symbols(values: Mapping[str, Any], symbols: Mapping[str, Any]) -> dict[str, Any]:
    """샘플러와 symbol_spec가 같은 이름의 다른 Symbol을 만들면 조용히 미분하지 않는다."""
    def bind(value):
        if isinstance(value, (sp.Basic, sp.MatrixBase)):
            replacements = {}
            for symbol in value.free_symbols:
                declared = symbols.get(symbol.name)
                if declared is not None:
                    if not isinstance(declared, sp.Symbol):
                        raise ProblemGenerationError(f"스칼라 변수/벡터 기호 충돌: {symbol.name}")
                    if symbol.assumptions0 != declared.assumptions0:
                        raise ProblemGenerationError(f"샘플러와 symbol_spec의 가정 불일치: {symbol.name}")
                    replacements[symbol] = declared
            return value.xreplace(replacements)
        if isinstance(value, Mapping): return {key: bind(item) for key, item in value.items()}
        if isinstance(value, tuple): return tuple(bind(item) for item in value)
        if isinstance(value, list): return [bind(item) for item in value]
        return value
    return {key: bind(value) for key, value in values.items()}


def _subject_answer_grade(template, answer, *, integer_answers_only, max_fraction_part):
    """선형대수는 기존 정책, 추가 과목은 유리수 계수의 크기만 검사한다.

    sin(x), 1/x, sqrt(2), exp(-t), pi 등은 해당 과목의 정상적인 답이다.
    숫자 또는 식의 기약분수 계수는 여전히 분자/분모 상한을 적용한다.
    """
    if template.taxonomy.subject_id == "linear_algebra":
        return _answer_fraction_grade(answer, max_fraction_part=max_fraction_part)
    def grade(value, path="answer"):
        if isinstance(value, sp.Rational):
            return _answer_fraction_grade(value, path, max_fraction_part=max_fraction_part)
        if isinstance(value, (sp.Basic, sp.MatrixBase)):
            return combine((item, path+'.coefficient') for item in value.atoms(sp.Rational))
        if isinstance(value, Mapping): return combine((item, path+'.'+str(key)) for key,item in value.items())
        if isinstance(value, (list,tuple)): return combine((item,path+'[]') for item in value)
        return _answer_fraction_grade(value, path, max_fraction_part=max_fraction_part)
    def combine(items):
        worst=0
        for item,path in items:
            bad,result=grade(item,path)
            if bad is not None: return bad,0
            worst=max(worst,result)
        return None,worst
    return grade(answer)


def build_instance_payload(
    template: ProblemTemplate,
    values: Mapping[str, Any],
    statement: str,
    statement_latex: str | None,
    expected_answer: Any,
    validation_trace: Mapping[str, Any],
    *,
    seed: int,
) -> dict[str, Any]:
    payload = {
        "subject_id": template.taxonomy.subject_id,
        "template_id": template.template_id,
        "template_version": template.template_version,
        "generation_rule_id": template.generation_rule_id,
        "generation_rule_version": template.generation_rule_version,
        "problem_type": template.classification.problem_type,
        "answer_type": template.answer_spec.answer_type,
        "template_status": template.status,
        "review_status": template.metadata.review_status,
        "publishable": False,  # Role 5 promotes only after multi-seed and human review.
        "statement": statement,
        "statement_latex": statement_latex,
        "parameters": _json_value(values),
        "expected_answer": _json_value(expected_answer),
    }
    if template.storage_policy.save_seed:
        payload["seed"] = seed
    if template.storage_policy.save_validation_trace:
        payload["validation_trace"] = _json_value(validation_trace)
    if template.storage_policy.save_template_snapshot:
        payload["template_snapshot"] = template.model_dump(mode="json")
    return payload


def _failed_constraints(template: ProblemTemplate, report: Any) -> list[Any]:
    selected = [
        constraint for constraint in template.constraints
        if not hasattr(constraint.expression, "scope")
        or constraint.expression.scope in {"generation", "both"}
    ]
    return [result for constraint, result in zip(selected, report.results) if constraint.required and not result.passed]


def generate_problem_instance(
    template: ProblemTemplate, *, seed: int, max_attempts: int | None = None,
    integer_answers_only: bool = False, max_fraction_part: int = 99,
) -> GenerationResult:
    validate_template_preconditions(template)
    context = prepare_subject_context(template)
    limit = max_attempts if max_attempts is not None else template.validation.generation_max_attempts
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("max_attempts must be a positive integer")
    if isinstance(max_fraction_part, bool) or not isinstance(max_fraction_part, int) or max_fraction_part < 1:
        raise ValueError("max_fraction_part must be a positive integer")
    attempts: list[GenerationAttempt] = []
    fallback: GenerationResult | None = None
    # 두 자리/두 자리 답을 확보한 뒤에는 작은 분수를 최대 8개 seed만 더 찾는다.
    fallback_deadline = limit
    for index in range(limit):
        if fallback is not None and index >= fallback_deadline:
            break
        current_seed = seed + index
        number = index + 1
        try:
            values = context["sample"](template.parameters, seed=current_seed)
        except parameter_sampler.ParameterSamplingError as exc:
            attempts.append(GenerationAttempt(number, current_seed, False, "sampling", str(exc)))
            continue

        constraint_values = values
        if template.taxonomy.subject_id != "linear_algebra":
            symbols = _symbolic_values(template, values)
            values = _bind_subject_symbols(values, symbols)
            constraint_values = {**values, **symbols}
        generation = context["constraints"](template.constraints, constraint_values, scope="generation")
        if not generation.passed:
            failed = _failed_constraints(template, generation)
            message = "; ".join(item.message or item.constraint_id or "Constraint failed" for item in failed)
            attempts.append(GenerationAttempt(number, current_seed, False, "constraints", message))
            if any(item.on_failure in {"reject", "error"} for item in failed):
                raise ProblemGenerationError(f"{template.template_id}: {message}")
            continue

        try:
            statement = render_problem_statement(template, values)
            latex = render_problem_latex(template, values)
            calculation_values = {**values, **_symbolic_values(template, values)}
            answer = context["answer"](template.answer_spec, calculation_values)
            bad_location, answer_grade = _subject_answer_grade(
                template, answer, integer_answers_only=integer_answers_only, max_fraction_part=max_fraction_part
            )
            if bad_location is not None or (integer_answers_only and answer_grade > 0):
                attempts.append(GenerationAttempt(
                    number, current_seed, False, "answer_policy",
                    f"최종 정답이 허용 범위를 벗어남: {bad_location or 'answer'}",
                ))
                continue
            validation_constraints = context["constraints"](template.constraints, constraint_values, scope="validation")
            if not validation_constraints.passed:
                raise ValueError("Validation-scope constraints failed")
            report = context["validate"](
                answer, calculation_values, template.validation.validators,
                all_required_must_pass=template.validation.all_required_must_pass,
                answer_type=template.answer_spec.answer_type,
                required_checks=template.answer_spec.required_checks,
                problem_type=template.classification.problem_type,
            )
        except (ValueError, TypeError, UndefinedError, TemplateSyntaxError) as exc:
            attempts.append(GenerationAttempt(number, current_seed, False, "construction", str(exc)))
            continue
        if not report.passed:
            message = "; ".join(f"{item.name}: {item.message}" for item in report.results if not item.passed)
            attempts.append(GenerationAttempt(number, current_seed, False, "validation", message))
            continue

        attempts.append(GenerationAttempt(number, current_seed, True, "validated"))
        trace = {
            "constraints": [asdict(item) for item in generation.results],
            "validation_constraints": [asdict(item) for item in validation_constraints.results],
            "validators": [asdict(item) for item in report.results],
            "attempts": [asdict(item) for item in attempts],
        }
        payload = build_instance_payload(template, values, statement, latex, answer, trace, seed=current_seed)
        candidate = GenerationResult(payload, current_seed, attempts.copy())
        if template.taxonomy.subject_id != "linear_algebra" or answer_grade <= 2:  # 신규 과목은 상한 이내 첫 검증 결과를 사용한다.
            return candidate
        if fallback is None:
            fallback = candidate
            fallback_deadline = min(limit, number + 8)

    if fallback is not None:
        if "validation_trace" in fallback.instance:
            fallback.instance["validation_trace"]["attempts"] = [asdict(item) for item in attempts]
        return GenerationResult(fallback.instance, fallback.seed, attempts)

    summary = "; ".join(f"{item.stage}: {item.message}" for item in attempts[-3:])
    raise ProblemGenerationError(f"{template.template_id}: {limit} attempts failed. {summary}")


def generate_problem_instances(
    templates: list[ProblemTemplate], *, seed_start: int, instances_per_template: int,
) -> list[GenerationResult]:
    """Generate for review; abort on failure and never write to the database."""
    if isinstance(instances_per_template, bool) or instances_per_template < 1:
        raise ValueError("instances_per_template must be positive")
    results: list[GenerationResult] = []
    next_seed = seed_start
    for template in templates:
        validate_template_preconditions(template)
        for _ in range(instances_per_template):
            result = generate_problem_instance(template, seed=next_seed)
            results.append(result)
            next_seed = result.seed + 1
    return results
