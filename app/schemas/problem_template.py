from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class DifficultySpec(StrictModel):
    base: int = Field(ge=1)
    min: int = Field(ge=1)
    max: int = Field(ge=1)
    factors: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_range(self) -> "DifficultySpec":
        if self.min > self.max:
            raise ValueError("difficulty.min은 max보다 클 수 없습니다.")
        if not self.min <= self.base <= self.max:
            raise ValueError("difficulty.base는 min~max 범위 안이어야 합니다.")
        return self


class TaxonomySpec(StrictModel):
    subject_id: str
    subject_name_ko: str
    unit_id: str
    unit_name_ko: str
    concept_ids: list[str] = Field(min_length=1)
    formula_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class ClassificationSpec(StrictModel):
    problem_type: str
    answer_type: str
    difficulty: DifficultySpec
    generation_strategy: Literal["forward_generation"] = "forward_generation"
    language: str = "ko-KR"


class ConstraintTemplate(StrictModel):
    type: str
    expression: str
    required: bool = True
    description: str | None = None


class ProblemBuilderSpec(StrictModel):
    operation: str
    required_objects: list[str] = Field(default_factory=list)
    semantic_structure: list[str] = Field(default_factory=list)
    text_templates_ko: list[str] = Field(default_factory=list)
    latex_templates: list[str] = Field(default_factory=list)
    cas_template: str | None = None
    render_engine: Literal["jinja2"] = "jinja2"


class CanonicalizationSpec(StrictModel):
    method: str | None = None
    exact_value_preferred: bool = True


class AnswerTemplateSpec(StrictModel):
    answer_type: str
    engine: Literal["sympy", "numpy", "python", "none"]
    cas_template: str | None = None
    latex_template: str | None = None
    canonicalization: CanonicalizationSpec
    required_checks: list[str] = Field(default_factory=list)


class SolutionStep(StrictModel):
    step: int = Field(ge=1)
    action: str
    formula_id: str | None = None
    cas_expression: str | None = None


class ExplanationPolicy(StrictModel):
    use_verified_answer_only: bool = True
    use_knowledge_base: bool = True
    allow_llm_calculation: bool = False


class SolutionSpec(StrictModel):
    solution_strategy: Literal["engine_then_explanation"] = "engine_then_explanation"
    solution_plan: list[SolutionStep] = Field(default_factory=list)
    explanation_policy: ExplanationPolicy = Field(default_factory=ExplanationPolicy)


class ValidatorTemplate(StrictModel):
    name: str
    required: bool = True
    config: dict[str, Any] = Field(default_factory=dict)


class ValidationTemplateSpec(StrictModel):
    validators: list[ValidatorTemplate] = Field(default_factory=list)
    generation_max_attempts: int = Field(default=100, ge=1)
    all_required_must_pass: bool = True


class QualityRulesSpec(StrictModel):
    duplicate_check: bool = True
    answer_complexity_check: bool = True
    ambiguity_check: bool = True
    minimum_distinct_parameter_sets: int = Field(default=20, ge=1)


class StoragePolicySpec(StrictModel):
    save_failed_generations: bool = True
    save_validation_trace: bool = True
    save_seed: bool = True
    save_template_snapshot: bool = True


class TemplateMetadata(StrictModel):
    created_by: str = "template_builder.py"
    review_status: Literal["not_reviewed", "reviewed"] = "not_reviewed"
    notes: str | None = None


class ProblemTemplate(BaseModel):
    """GenerationRule과 Concept 메타데이터를 합친 문제 생성용 최종 설계도."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    schema_version: str = "1.0.0"
    object_type: Literal["problem_template"] = "problem_template"

    template_id: str
    template_version: str = "1.0.0"
    status: Literal["draft", "ready", "deprecated"] = "draft"

    generation_rule_id: str
    generation_rule_version: str
    generation_rule_status: Literal["curated", "draft_auto", "reviewed"]
    executable: bool

    taxonomy: TaxonomySpec
    classification: ClassificationSpec

    # GenerationRule의 parameter_spec을 손실 없이 넘기기 위해 유연한 dict로 둔다.
    parameters: dict[str, dict[str, Any]] = Field(default_factory=dict)
    constraints: list[ConstraintTemplate] = Field(default_factory=list)

    problem_builder: ProblemBuilderSpec
    answer_spec: AnswerTemplateSpec
    solution_spec: SolutionSpec
    validation: ValidationTemplateSpec

    quality_rules: QualityRulesSpec = Field(default_factory=QualityRulesSpec)
    storage_policy: StoragePolicySpec = Field(default_factory=StoragePolicySpec)
    metadata: TemplateMetadata = Field(default_factory=TemplateMetadata)

    @model_validator(mode="after")
    def validate_ready_template(self) -> "ProblemTemplate":
        if self.status == "ready":
            if not self.executable:
                raise ValueError("ready Template은 executable=True여야 합니다.")
            if not self.problem_builder.text_templates_ko:
                raise ValueError("ready Template에는 문제 문장 Template이 필요합니다.")
            if self.answer_spec.engine != "none" and self.answer_spec.cas_template is None:
                raise ValueError("ready Template에는 정답 계산식이 필요합니다.")
        return self
