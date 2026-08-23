from __future__ import annotations

from typing import Iterable

from app.problems.problem_type_extractor import ProblemTypeInfo
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


def build_template(
    problem_type: ProblemTypeInfo,
    rule: GenerationRule,
) -> ProblemTemplate:
    """ProblemTypeInfo + GenerationRule을 하나의 ProblemTemplate로 조립한다."""

    _validate_pair(problem_type, rule)

    difficulty_min, difficulty_max, difficulty_base = _difficulty_range(
        problem_type,
        rule,
    )
    answer_type, answer_type_changed = _resolve_answer_type(
        problem_type,
        rule,
    )

    is_ready = (
        rule.status in {"curated", "reviewed"}
        and rule.executable
        and not rule.manual_review_required
    )

    template_status = "ready" if is_ready else "draft"
    review_status = "reviewed" if rule.status == "reviewed" else "not_reviewed"

    validator_names = _unique(
        [
            *rule.validation.validators,
            *problem_type.recommended_validators,
        ]
    )

    formula_ids = _unique(problem_type.formula_ids)
    first_formula_id = formula_ids[0] if formula_ids else None

    parameter_dict = {
        name: spec.model_dump(mode="python")
        for name, spec in rule.parameter_spec.items()
    }

    effective_answer_expression = (
        None if answer_type_changed else rule.answer_spec.expression
    )
    effective_latex_expression = (
        None if answer_type_changed else rule.answer_spec.latex_expression
    )

    notes = (
        f"Generation Rule '{rule.rule_id}'에서 생성. "
        f"rule_status={rule.status}, executable={rule.executable}, "
        f"manual_review_required={rule.manual_review_required}."
    )
    if answer_type_changed:
        notes += (
            " 공유 draft_auto Rule의 answer_type을 현재 Concept의 "
            f"지원 타입 '{answer_type}'에 맞게 조정했으며, 정답식은 검토 전까지 비워둠."
        )
    if rule.notes:
        notes += f" {rule.notes}"
    if problem_type.generation_notes:
        notes += f" Concept generation_notes: {problem_type.generation_notes}"

    return ProblemTemplate(
        template_id=(
            f"{problem_type.subject_id}."
            f"{problem_type.unit_id}."
            f"{problem_type.concept_id}."
            f"{problem_type.problem_type}.v1"
        ),
        status=template_status,
        generation_rule_id=rule.rule_id,
        generation_rule_version=rule.rule_version,
        generation_rule_status=rule.status,
        executable=bool(rule.executable and is_ready),
        taxonomy={
            "subject_id": problem_type.subject_id,
            "subject_name_ko": problem_type.subject_name_ko,
            "unit_id": problem_type.unit_id,
            "unit_name_ko": problem_type.unit_name_ko,
            "concept_ids": [problem_type.concept_id],
            "formula_ids": formula_ids,
            "tags": _unique(problem_type.tags),
        },
        classification={
            "problem_type": problem_type.problem_type,
            "answer_type": answer_type,
            "difficulty": {
                "base": difficulty_base,
                "min": difficulty_min,
                "max": difficulty_max,
                "factors": rule.difficulty.factors,
            },
            "generation_strategy": "forward_generation",
            "language": problem_type.language,
        },
        parameters=parameter_dict,
        constraints=[
            {
                "type": constraint.type,
                "expression": constraint.expression,
                "required": constraint.required,
                "description": constraint.description,
            }
            for constraint in rule.constraints
        ],
        problem_builder={
            "operation": rule.construction.operation,
            "required_objects": rule.construction.required_objects,
            "semantic_structure": rule.construction.semantic_structure,
            "text_templates_ko": rule.construction.text_templates,
            "latex_templates": rule.construction.latex_templates,
            "cas_template": rule.construction.builder_expression,
            "render_engine": "jinja2",
        },
        answer_spec={
            "answer_type": answer_type,
            "engine": rule.answer_spec.engine,
            "cas_template": effective_answer_expression,
            "latex_template": effective_latex_expression,
            "canonicalization": {
                "method": rule.answer_spec.canonicalization,
                "exact_value_preferred": True,
            },
            "required_checks": validator_names,
        },
        solution_spec={
            "solution_strategy": "engine_then_explanation",
            "solution_plan": [
                {
                    "step": 1,
                    "action": (
                        "Generation Rule의 계산식을 사용하여 정답을 계산하고 "
                        "Validator로 결과를 검증한다."
                    ),
                    "formula_id": first_formula_id,
                    "cas_expression": effective_answer_expression,
                }
            ],
            "explanation_policy": {
                "use_verified_answer_only": True,
                "use_knowledge_base": True,
                "allow_llm_calculation": False,
            },
        },
        validation={
            "validators": [
                {
                    "name": name,
                    "required": True,
                    "config": {},
                }
                for name in validator_names
            ],
            "generation_max_attempts": rule.validation.max_generation_attempts,
            "all_required_must_pass": rule.validation.all_required,
        },
        metadata={
            "created_by": "template_builder.py",
            "review_status": review_status,
            "notes": notes,
        },
    )
