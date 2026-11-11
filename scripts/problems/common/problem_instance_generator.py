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
    # TODO[LA-D027] prepare_linear_algebra_context 구현
    # 1. 확장 입력의 symbol/derived 파라미터를 정확한 SymPy 수로 유지한다.
    # 2. 고유값·차원 등 의존 파라미터를 이전 고정 범위와 불일치하게 만들지 않는다.
    raise NotImplementedError("TODO[LA-D027]: prepare_linear_algebra_context")


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
    # TODO[LA-D028] _json_value 구현
    # 1. 유리수 입력/정답의 분자·분모가 float로 손실되지 않고 저장 후 독립 parse로 동일하게 복원되는지 왕복 테스트한다.
    raise NotImplementedError("TODO[LA-D028]: _json_value")


def _answer_fraction_grade(
    value: Any, path: str = "answer", *, max_fraction_part: int = 99,
) -> tuple[str | None, int]:
    # TODO[LA-D029] _answer_fraction_grade 구현
    # 1. 현재 최대 분수 부분 99 및 무리수/복소수 제한 때문에 생성 후 탈락하는 비율을 측정한다.
    # 2. 수학적 정당성 실패와 표시/난도 제한을 구분하며, 제한을 무작정 제거하지 않는다.
    # 3. 복소/근호 정답은 유형별 명시적 지원이 있는 경우에만 확장한다.
    raise NotImplementedError("TODO[LA-D029]: _answer_fraction_grade")


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
    # TODO[LA-D030] generate_problem_instance 구현
    # 1. 후보 정책별 재시도/제약 실패/정답 난도 탈락/시간 초과를 집계한다.
    # 2. 정책 혼합 후 최종 통과 표본의 분포가 한 구조로 수렴하는 편향을 측정한다.
    # 3. 검수 전 결과는 publishable=False로 유지한다.
    raise NotImplementedError("TODO[LA-D030]: generate_problem_instance")


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
