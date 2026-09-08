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
    generation_strategy: Literal[
        "forward_generation",
        "reverse_generation",
    ] = "forward_generation"
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


class EquivalenceSpec(StrictModel):
    """정답 동치 판정 방식. 상수 재명명·대수적 변형을 어디까지 같다고 볼지."""

    method: str | None = None
    tolerance: float | None = None
    allow_algebraic_rearrangement: bool | None = None
    allow_constant_renaming: bool | None = None


class AnswerTemplateSpec(StrictModel):
    answer_type: str
    engine: Literal["sympy", "numpy", "python", "none"]
    cas_template: str | None = None
    latex_template: str | None = None
    canonicalization: CanonicalizationSpec
    equivalence: EquivalenceSpec | None = None
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

    # answer_complexity_check가 실제로 쓸 임계값. 없으면 검사기가 기준을 못 잡는다.
    maximum_answer_complexity: int | None = None
    maximum_denominator: int | None = None
    allow_decimal_answer: bool | None = None


class StoragePolicySpec(StrictModel):
    save_failed_generations: bool = True
    save_validation_trace: bool = True
    save_seed: bool = True
    save_template_snapshot: bool = True


class DistractorRule(StrictModel):
    """오답 선택지 생성 규칙. misconception_id는 개념 카탈로그에 등록된 것이어야 한다."""

    rule_id: str
    misconception_id: str
    transformation: str
    validator: str | None = None


class TemplateMetadata(StrictModel):
    created_by: str = "template_builder.py"
    review_status: Literal["not_reviewed", "reviewed"] = "not_reviewed"
    reviewed_by: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
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
    # 데이터 구조 설계 10.3의 6단계 생명주기.
    # "ready"는 template_builder.py가 실제로 찍어내는 값이고 기존 템플릿 56개가
    # 쓰고 있어 함께 허용한다. 데이터 이관이 끝나면 뺀다.
    status: Literal[
        "draft",
        "schema_validated",
        "math_validated",
        "human_reviewed",
        "active",
        "deprecated",
        "ready",
    ] = "draft"

    generation_rule_id: str
    generation_rule_version: str
    generation_rule_status: Literal["curated", "draft_auto", "reviewed"]
    executable: bool

    taxonomy: TaxonomySpec
    classification: ClassificationSpec

    # GenerationRule의 parameter_spec을 손실 없이 넘기기 위해 유연한 dict로 둔다.
    parameters: dict[str, dict[str, Any]] = Field(default_factory=dict)

    # 샘플링된 파라미터로 계산되는 파생 값. 현재 데이터는 전부 빈 배열이라
    # 항목 구조가 확정되지 않았다 — 확정되면 전용 모델로 조인다.
    parameter_dependencies: list[dict[str, Any]] = Field(default_factory=list)

    constraints: list[ConstraintTemplate] = Field(default_factory=list)

    problem_builder: ProblemBuilderSpec
    answer_spec: AnswerTemplateSpec
    solution_spec: SolutionSpec
    validation: ValidationTemplateSpec

    distractor_rules: list[DistractorRule] = Field(default_factory=list)

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
