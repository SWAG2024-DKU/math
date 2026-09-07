from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.generation_rule import StructuredConstraintSpec, SymbolSpec


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
    # C의 기존 문자열 Constraint를 그대로 허용하면서,
    # GenerationRule 1.1의 구조화 Constraint도 손실 없이 받는다.
    expression: str | StructuredConstraintSpec
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
    """정답 동치 판정 방식."""

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

    # GenerationRule 1.1의 대표 공식. 기존 C 템플릿에는 없으므로 optional이다.
    primary_formula_id: str | None = None

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

    # C 버전에서 추가된 실제 복잡도 제한 필드들을 보존한다.
    maximum_answer_complexity: int | None = None
    maximum_denominator: int | None = None
    allow_decimal_answer: bool | None = None


class StoragePolicySpec(StrictModel):
    save_failed_generations: bool = True
    save_validation_trace: bool = True
    save_seed: bool = True
    save_template_snapshot: bool = True


class DistractorRule(StrictModel):
    """오답 선택지 생성 규칙."""

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
    """GenerationRule과 Concept 메타데이터를 합친 문제 생성용 최종 설계도.

    이 모델은 C의 기존 ProblemTemplate 데이터와 DB 검증을 깨지 않으면서
    GenerationRule 1.1의 symbols / structured constraints /
    primary_formula_id를 추가로 수용한다.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    # 새로 생성되는 Template의 기본 버전. 기존 JSON은 명시된 1.0.0을 유지한다.
    schema_version: str = "1.1.0"
    object_type: Literal["problem_template"] = "problem_template"

    template_id: str
    template_version: str = "1.0.0"

    # C에서 사용하던 생명주기를 그대로 보존한다.
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

    # C의 기존 데이터는 parameter 구조가 완전히 고정되지 않았으므로
    # dict를 유지한다. GenerationRule의 ParameterSpec.model_dump() 결과도
    # 이 필드에 손실 없이 저장된다.
    parameters: dict[str, dict[str, Any]] = Field(default_factory=dict)

    # GenerationRule 1.1의 샘플링하지 않는 수학 기호 선언.
    symbols: dict[str, SymbolSpec] = Field(default_factory=dict)

    # C에서 이미 존재하던 파생 파라미터 표현을 하위호환 목적으로 유지한다.
    parameter_dependencies: list[dict[str, Any]] = Field(default_factory=list)

    constraints: list[ConstraintTemplate] = Field(default_factory=list)

    problem_builder: ProblemBuilderSpec
    answer_spec: AnswerTemplateSpec
    solution_spec: SolutionSpec
    validation: ValidationTemplateSpec

    # C에서 추가된 기능을 그대로 보존한다.
    distractor_rules: list[DistractorRule] = Field(default_factory=list)

    quality_rules: QualityRulesSpec = Field(default_factory=QualityRulesSpec)
    storage_policy: StoragePolicySpec = Field(default_factory=StoragePolicySpec)
    metadata: TemplateMetadata = Field(default_factory=TemplateMetadata)

    @model_validator(mode="after")
    def validate_ready_template(self) -> "ProblemTemplate":
        # 새 symbols와 기존 parameters 사이 이름 충돌은 막는다.
        overlap = sorted(set(self.parameters) & set(self.symbols))
        if overlap:
            raise ValueError(
                "같은 이름을 parameters와 symbols에 중복 선언할 수 없습니다: "
                + ", ".join(overlap)
            )

        primary_formula_id = self.solution_spec.primary_formula_id
        if (
            primary_formula_id is not None
            and primary_formula_id not in self.taxonomy.formula_ids
        ):
            raise ValueError(
                "solution_spec.primary_formula_id는 taxonomy.formula_ids에 "
                "포함되어야 합니다."
            )

        if self.status == "ready":
            if not self.executable:
                raise ValueError("ready Template은 executable=True여야 합니다.")
            if not self.problem_builder.text_templates_ko:
                raise ValueError("ready Template에는 문제 문장 Template이 필요합니다.")
            if (
                self.answer_spec.engine != "none"
                and self.answer_spec.cas_template is None
            ):
                raise ValueError("ready Template에는 정답 계산식이 필요합니다.")
        return self
