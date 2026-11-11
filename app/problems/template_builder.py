from __future__ import annotations

from typing import Iterable

from app.problems.problem_type_extractor import ProblemTypeInfo
from app.problems.validator_policy import ALLOWED_VALIDATORS, validate_curated_mapping
from app.schemas.generation_rule import GenerationRule
from app.schemas.problem_template import ProblemTemplate


def _unique(items: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))


def _difficulty_range(
    problem_type: ProblemTypeInfo,
    rule: GenerationRule,
) -> tuple[int, int, int]:
    """Concept 범위와 Rule 범위의 교집합을 Template 난이도로 사용한다."""

    minimum = max(problem_type.difficulty_min, rule.difficulty.min)
    maximum = min(problem_type.difficulty_max, rule.difficulty.max)

    if minimum > maximum:
        raise ValueError(
            "난이도 범위가 서로 겹치지 않습니다: "
            f"{problem_type.concept_id} / {problem_type.problem_type} "
            f"(concept={problem_type.difficulty_min}~{problem_type.difficulty_max}, "
            f"rule={rule.difficulty.min}~{rule.difficulty.max})"
        )

    base = (minimum + maximum) // 2
    return minimum, maximum, base


def _validate_pair(
    problem_type: ProblemTypeInfo,
    rule: GenerationRule,
) -> None:
    if problem_type.subject_id != rule.subject_id:
        raise ValueError(
            "subject_id 불일치: "
            f"{problem_type.subject_id} != {rule.subject_id}"
        )

    if problem_type.problem_type != rule.problem_type:
        raise ValueError(
            "problem_type 불일치: "
            f"{problem_type.problem_type} != {rule.problem_type}"
        )

    if (
        rule.source_concept_ids
        and problem_type.concept_id not in rule.source_concept_ids
    ):
        raise ValueError(
            "Generation Rule의 source_concept_ids에 Concept가 없습니다: "
            f"{problem_type.concept_id} / {rule.rule_id}"
        )



def _resolve_answer_type(
    problem_type: ProblemTypeInfo,
    rule: GenerationRule,
) -> tuple[str, bool]:
    """
    Rule이 여러 Concept에서 재사용될 때 Concept별 지원 answer_type을 맞춘다.

    curated/reviewed Rule은 불일치를 오류로 처리하고, draft_auto Rule은
    해당 Concept이 지원하는 answer_type 중 Rule catalog에도 존재하는 값을
    선택한다. 두 번째 반환값은 Rule 원래 answer_type에서 변경되었는지 여부다.
    """

    rule_answer_type = rule.answer_spec.answer_type
    supported = tuple(problem_type.supported_answer_types)

    if not supported or rule_answer_type in supported:
        return rule_answer_type, False

    if rule.status != "draft_auto":
        raise ValueError(
            "Rule answer_type이 Concept에서 지원되지 않습니다: "
            f"{rule_answer_type} not in {supported}"
        )

    for answer_type in rule.supported_answer_types:
        if answer_type in supported:
            return answer_type, True

    return supported[0], True


def _resolve_primary_formula_id(
    problem_type: ProblemTypeInfo,
    rule: GenerationRule,
) -> str | None:
    """현재 Concept에 실제로 속하는 대표 공식만 선택한다."""

    formula_ids = _unique(problem_type.formula_ids)
    primary_formula_id = rule.primary_formula_id

    if primary_formula_id is not None:
        if primary_formula_id not in formula_ids:
            raise ValueError(
                "Generation Rule의 primary_formula_id가 현재 Concept에 없습니다: "
                f"{primary_formula_id} / {problem_type.concept_id}"
            )
        return primary_formula_id

    # 공식이 정확히 하나일 때만 자동 선택한다. 여러 개라면 임의로 첫 번째
    # 공식을 고르지 않고 None으로 남겨 후속 검토 대상으로 만든다.
    return formula_ids[0] if len(formula_ids) == 1 else None


def _dump_model(value: object) -> object:
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return model_dump(mode="python", exclude_unset=True)
    return value


def build_template(
    problem_type: ProblemTypeInfo,
    rule: GenerationRule,
) -> ProblemTemplate:
    # TODO[LA-D025] build_template 구현
    # 1. 새 파라미터 옵션이 Rule에서 Template로 손실 없이 전달되는지 확인한다.
    # 2. 기존 검수 정보는 보존하되 확장된 후보 생성 범위가 기존 reviewed/ready/publishable 판정을 무조건 상속하지 않도록 버전/검수 범위를 구분한다.
    # 3. 보고서 필드를 임의로 strict schema에 삽입하지 않는다.
    raise NotImplementedError("TODO[LA-D025]: build_template")
