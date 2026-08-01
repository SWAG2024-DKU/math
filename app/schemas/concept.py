from __future__ import annotations

from collections import Counter
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)


# 공백만 있는 문자열을 허용하지 않는다.
NonEmptyStr = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
    ),
]

# application_conditions.rule.value에서 사용하는 자료형
RuleScalar = bool | int | float | NonEmptyStr
RuleValue = RuleScalar | list[RuleScalar]


class StrictModel(BaseModel):
    """정의되지 않은 필드와 잘못된 자료형을 허용하지 않는 기본 모델."""

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        str_strip_whitespace=True,
    )


class DifficultyRange(StrictModel):
    min: int = Field(ge=1)
    max: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_range(self) -> "DifficultyRange":
        if self.min > self.max:
            raise ValueError(
                "difficulty_range.min은 max보다 클 수 없습니다."
            )
        return self


class SubjectInfo(StrictModel):
    subject_id: NonEmptyStr
    name_ko: NonEmptyStr


class UnitInfo(StrictModel):
    unit_id: NonEmptyStr
    name_ko: NonEmptyStr
    order: int = Field(ge=1)
    description: NonEmptyStr


class SourceInfo(StrictModel):
    source_type: Literal["markdown"]
    source_file: list[NonEmptyStr] = Field(min_length=1)
    converted_fields: list[NonEmptyStr] = Field(min_length=1)

    @field_validator("source_file", mode="before")
    @classmethod
    def normalize_source_file(cls, value):
        """
        source_file이 문자열 하나면 문자열 배열로 변환한다.

        입력:
        "chapter01.md"

        내부 변환:
        ["chapter01.md"]
        """
        if isinstance(value, str):
            return [value]

        return value


class Conventions(StrictModel):
    """
    과목별 표기 및 계산 규칙.

    미적분학에는 독립변수와 종속함수가 있지만,
    선형대수나 확률통계에서는 사용하지 않을 수도 있으므로
    두 필드는 선택사항으로 둔다.
    """

    model_config = ConfigDict(
        extra="allow",
        strict=True,
        str_strip_whitespace=True,
    )

    independent_variable: NonEmptyStr | None = None
    dependent_function: NonEmptyStr | None = None

    formula_display: NonEmptyStr
    formula_computation: NonEmptyStr
    difficulty_scale: DifficultyRange


class Formula(StrictModel):
    formula_id: NonEmptyStr
    name_ko: NonEmptyStr
    role: NonEmptyStr
    latex: NonEmptyStr

    # CAS 표현이 적절하지 않은 개념도 있으므로 null 허용
    cas: NonEmptyStr | None = None


class ConditionRule(StrictModel):
    property: NonEmptyStr
    operator: NonEmptyStr

    # 현재 기준 파일에는 bool, int, str, list가 모두 등장한다.
    value: RuleValue


class ApplicationCondition(StrictModel):
    condition_id: NonEmptyStr
    description: NonEmptyStr
    rule: ConditionRule


class ConceptProperty(StrictModel):
    property_id: NonEmptyStr
    description: NonEmptyStr


class Prerequisite(StrictModel):
    concept_id: NonEmptyStr
    name_ko: NonEmptyStr
    importance: Literal[
        "required",
        "recommended",
        "optional",
    ]


class LearningObjective(StrictModel):
    objective_id: NonEmptyStr
    verb: NonEmptyStr
    description: NonEmptyStr


class Misconception(StrictModel):
    misconception_id: NonEmptyStr
    title: NonEmptyStr
    description: NonEmptyStr
    diagnosis_tag: NonEmptyStr
    feedback: NonEmptyStr


class GenerationProfile(StrictModel):
    enabled: bool

    supported_problem_types: list[NonEmptyStr] = Field(
        default_factory=list
    )

    supported_answer_types: list[NonEmptyStr] = Field(
        default_factory=list
    )

    difficulty_range: DifficultyRange

    recommended_validators: list[NonEmptyStr] = Field(
        default_factory=list
    )

    generation_notes: NonEmptyStr | None = None


def ensure_unique(
    items: list[BaseModel],
    attribute: str,
    label: str,
) -> None:
    """Pydantic 객체 목록에서 지정한 ID의 중복을 검사한다."""

    values = [
        getattr(item, attribute)
        for item in items
    ]

    duplicated = [
        value
        for value, count in Counter(values).items()
        if count > 1
    ]

    if duplicated:
        raise ValueError(
            f"{label} 중복: {', '.join(map(str, duplicated))}"
        )


class Concept(StrictModel):
    concept_id: NonEmptyStr
    order: int = Field(ge=1)

    name_ko: NonEmptyStr
    definition: NonEmptyStr

    formulas: list[Formula] = Field(default_factory=list)

    application_conditions: list[ApplicationCondition] = Field(
        default_factory=list
    )

    properties: list[ConceptProperty] = Field(
        default_factory=list
    )

    prerequisites: list[Prerequisite] = Field(
        default_factory=list
    )

    related_concepts: list[NonEmptyStr] = Field(
        default_factory=list
    )

    learning_objectives: list[LearningObjective] = Field(
        default_factory=list
    )

    misconceptions: list[Misconception] = Field(
        default_factory=list
    )

    generation_profile: GenerationProfile

    tags: list[NonEmptyStr] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_nested_ids(self) -> "Concept":
        ensure_unique(
            self.formulas,
            "formula_id",
            "formula_id",
        )

        ensure_unique(
            self.application_conditions,
            "condition_id",
            "condition_id",
        )

        ensure_unique(
            self.properties,
            "property_id",
            "property_id",
        )

        ensure_unique(
            self.learning_objectives,
            "objective_id",
            "objective_id",
        )

        ensure_unique(
            self.misconceptions,
            "misconception_id",
            "misconception_id",
        )

        if len(self.related_concepts) != len(
            set(self.related_concepts)
        ):
            raise ValueError(
                "related_concepts에 중복 ID가 있습니다."
            )

        if len(self.tags) != len(set(self.tags)):
            raise ValueError(
                "tags에 중복 값이 있습니다."
            )

        return self


class ConceptCatalog(StrictModel):
    schema_version: str = Field(
        pattern=r"^\d+\.\d+\.\d+$"
    )

    catalog_type: Literal["concept_catalog"]
    language: NonEmptyStr

    subject: SubjectInfo
    unit: UnitInfo
    source: SourceInfo
    conventions: Conventions

    concepts: list[Concept] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_catalog(self) -> "ConceptCatalog":
        # 같은 파일 안에서 Concept ID 중복 검사
        ensure_unique(
            self.concepts,
            "concept_id",
            "concept_id",
        )

        # 같은 단원 안에서 순서 중복 검사
        ensure_unique(
            self.concepts,
            "order",
            "concept order",
        )

        # Concept의 난이도 범위가 카탈로그 범위 안에 있는지 검사
        catalog_range = self.conventions.difficulty_scale

        for concept in self.concepts:
            concept_range = (
                concept
                .generation_profile
                .difficulty_range
            )

            if (
                concept_range.min < catalog_range.min
                or concept_range.max > catalog_range.max
            ):
                raise ValueError(
                    f"{concept.concept_id}: "
                    "generation_profile의 난이도 범위가 "
                    "카탈로그 difficulty_scale을 벗어났습니다."
                )

        return self