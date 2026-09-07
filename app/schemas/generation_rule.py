from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FlexibleModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class RangeSpec(BaseModel):
    """행렬 크기처럼 양의 정수 범위로 표현되는 값."""

    model_config = ConfigDict(extra="forbid")

    min: int = Field(ge=1)
    max: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_order(self) -> "RangeSpec":
        if self.min > self.max:
            raise ValueError("RangeSpec.min은 max보다 클 수 없습니다.")
        return self


DimensionValue = int | str | RangeSpec


class ShapeSpec(BaseModel):
    """행렬·벡터·데이터의 크기와 다른 파라미터와의 크기 관계.

    정수는 고정 크기, 문자열은 ``A.cols`` 또는 ``n`` 같은 참조,
    RangeSpec은 생성 가능한 범위를 뜻한다.
    """

    model_config = ConfigDict(extra="forbid")

    rows: DimensionValue | None = None
    cols: DimensionValue | None = None
    dimension: DimensionValue | None = None
    length: DimensionValue | None = None
    size: DimensionValue | None = None

    @model_validator(mode="after")
    def validate_shape(self) -> "ShapeSpec":
        values = (self.rows, self.cols, self.dimension, self.length, self.size)
        if not any(value is not None for value in values):
            raise ValueError("shape에는 하나 이상의 크기 필드가 필요합니다.")

        for value in values:
            if isinstance(value, int) and value < 1:
                raise ValueError("shape의 고정 크기는 1 이상이어야 합니다.")

        if self.rows is not None or self.cols is not None:
            if self.dimension is not None or self.length is not None:
                raise ValueError(
                    "행렬 rows/cols와 벡터 dimension/length는 함께 사용할 수 없습니다."
                )
        return self


class DerivedParameterSpec(BaseModel):
    """다른 파라미터로부터 계산되는 파생값."""

    model_config = ConfigDict(extra="forbid")

    depends_on: list[str] = Field(min_length=1)
    expression: str = Field(min_length=1)
    engine: Literal["sympy", "numpy", "python", "registry"] = "sympy"
    selection: str | None = None


class ParameterSpec(BaseModel):
    """GenerationRule 파라미터 정의.

    기존 JSON의 평면형 크기 필드를 유지하면서 ``shape``와 ``derived``를
    추가한다. 아직 알려지지 않은 샘플러 옵션도 보존할 수 있도록 extra를
    허용한다.
    """

    model_config = ConfigDict(extra="allow")

    type: str = Field(min_length=1)
    description: str | None = None
    required: bool = True

    min: int | float | None = None
    max: int | float | None = None
    exclude: list[Any] = Field(default_factory=list)
    choices: list[Any] = Field(default_factory=list)
    step: int | float | None = None
    distribution: str | None = None

    allowed_families: list[str] = Field(default_factory=list)
    element_type: str | None = None
    element_min: int | float | None = None
    element_max: int | float | None = None

    # 기존 v1 JSON과의 하위 호환 필드다. 신규 Rule은 shape 사용을 권장한다.
    rows_min: int | None = Field(default=None, ge=1)
    rows_max: int | None = Field(default=None, ge=1)
    cols_min: int | None = Field(default=None, ge=1)
    cols_max: int | None = Field(default=None, ge=1)
    dimension_min: int | None = Field(default=None, ge=1)
    dimension_max: int | None = Field(default=None, ge=1)
    size_min: int | None = Field(default=None, ge=1)
    size_max: int | None = Field(default=None, ge=1)

    shape: ShapeSpec | None = None
    depends_on: list[str] = Field(default_factory=list)
    derived: DerivedParameterSpec | None = None
    generator: str | None = None

    @model_validator(mode="after")
    def validate_ranges_and_derivation(self) -> "ParameterSpec":
        range_pairs = (
            ("min", self.min, "max", self.max),
            ("element_min", self.element_min, "element_max", self.element_max),
            ("rows_min", self.rows_min, "rows_max", self.rows_max),
            ("cols_min", self.cols_min, "cols_max", self.cols_max),
            (
                "dimension_min",
                self.dimension_min,
                "dimension_max",
                self.dimension_max,
            ),
            ("size_min", self.size_min, "size_max", self.size_max),
        )
        for min_name, minimum, max_name, maximum in range_pairs:
            if minimum is not None and maximum is not None and minimum > maximum:
                raise ValueError(f"{min_name}은 {max_name}보다 클 수 없습니다.")

        if self.type == "derived" and self.derived is None:
            raise ValueError("type='derived' 파라미터에는 derived 설정이 필요합니다.")
        return self


class SymbolSpec(BaseModel):
    """샘플링하지 않는 수학 기호의 선언."""

    model_config = ConfigDict(extra="forbid")

    role: Literal[
        "independent_variable",
        "bound_variable",
        "unknown",
        "constant",
        "index",
    ]
    assumptions: dict[str, bool | int | str] = Field(default_factory=dict)
    dimension: int | str | None = None
    description: str | None = None


class ConstraintRuleSpec(BaseModel):
    """Evaluator가 실행할 수 있는 단일 구조화 조건."""

    model_config = ConfigDict(extra="forbid")

    left: Any = None
    operator: str = Field(min_length=1)
    right: Any = None
    args: list[Any] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_operands(self) -> "ConstraintRuleSpec":
        if self.left is None and not self.args:
            raise ValueError("Constraint rule에는 left 또는 args가 필요합니다.")
        return self


class StructuredConstraintSpec(BaseModel):
    """문자열로 이중 저장하지 않는 실행 가능한 Constraint 형식."""

    model_config = ConfigDict(extra="forbid")

    constraint_id: str = Field(min_length=1)
    scope: Literal["generation", "validation", "both"] = "generation"
    description: str | None = None
    rule: ConstraintRuleSpec
    on_failure: Literal["resample", "reject", "error"] = "resample"


class ConstraintSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    expression: str | StructuredConstraintSpec
    required: bool = True
    description: str | None = None


class ConstructionSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation: str
    required_objects: list[str] = Field(default_factory=list)
    semantic_structure: list[str] = Field(default_factory=list)
    text_templates: list[str] = Field(default_factory=list)
    latex_templates: list[str] = Field(default_factory=list)
    builder_expression: str | None = None


class AnswerSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer_type: str
    engine: Literal["sympy", "numpy", "python", "none"] = "sympy"
    expression: str | None = None
    latex_expression: str | None = None
    canonicalization: str | None = None


class ValidationSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    validators: list[str] = Field(default_factory=list)
    all_required: bool = True
    max_generation_attempts: int = 100


class DifficultySpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min: int
    max: int
    factors: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_order(self) -> "DifficultySpec":
        if self.min > self.max:
            raise ValueError("difficulty.min은 max보다 클 수 없습니다.")
        return self


REFERENCE_RE = re.compile(r"^([A-Za-z_]\w*)(?:\.[A-Za-z_]\w*)*$")


def _shape_references(shape: ShapeSpec | None) -> set[str]:
    if shape is None:
        return set()

    references: set[str] = set()
    for value in (shape.rows, shape.cols, shape.dimension, shape.length, shape.size):
        if isinstance(value, str):
            match = REFERENCE_RE.fullmatch(value.strip())
            if match:
                references.add(match.group(1))
    return references


class GenerationRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_id: str
    rule_version: str = "1.0.0"

    status: Literal["curated", "draft_auto", "reviewed"] = "draft_auto"
    executable: bool = False
    manual_review_required: bool = True

    subject_id: str
    problem_type: str

    source_concept_ids: list[str] = Field(default_factory=list)
    source_formula_ids: list[str] = Field(default_factory=list)
    primary_formula_id: str | None = None
    supported_answer_types: list[str] = Field(default_factory=list)

    parameter_spec: dict[str, ParameterSpec] = Field(default_factory=dict)
    symbol_spec: dict[str, SymbolSpec] = Field(default_factory=dict)
    constraints: list[ConstraintSpec] = Field(default_factory=list)

    construction: ConstructionSpec
    answer_spec: AnswerSpec
    validation: ValidationSpec
    difficulty: DifficultySpec

    notes: str | None = None

    @model_validator(mode="after")
    def validate_internal_references(self) -> "GenerationRule":
        parameter_names = set(self.parameter_spec)
        symbol_names = set(self.symbol_spec)
        known_names = parameter_names | symbol_names

        overlap = sorted(parameter_names & symbol_names)
        if overlap:
            raise ValueError(
                "같은 이름을 parameter_spec과 symbol_spec에 중복 선언할 수 없습니다: "
                + ", ".join(overlap)
            )

        missing_required = sorted(
            set(self.construction.required_objects) - known_names
        )
        if missing_required:
            raise ValueError(
                "construction.required_objects의 미선언 이름: "
                + ", ".join(missing_required)
            )

        dependency_graph: dict[str, set[str]] = {}
        for name, spec in self.parameter_spec.items():
            dependencies = set(spec.depends_on)
            if spec.derived is not None:
                dependencies.update(spec.derived.depends_on)

            unknown = sorted(dependencies - known_names)
            if unknown:
                raise ValueError(
                    f"parameter_spec.{name}의 미선언 의존 대상: "
                    + ", ".join(unknown)
                )
            if name in dependencies:
                raise ValueError(f"parameter_spec.{name}은 자기 자신에 의존할 수 없습니다.")

            unknown_shape_refs = sorted(_shape_references(spec.shape) - known_names)
            if unknown_shape_refs:
                raise ValueError(
                    f"parameter_spec.{name}.shape의 미선언 참조: "
                    + ", ".join(unknown_shape_refs)
                )
            dependency_graph[name] = dependencies & parameter_names

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(name: str) -> None:
            if name in visited:
                return
            if name in visiting:
                raise ValueError(f"파라미터 의존관계에 순환이 있습니다: {name}")
            visiting.add(name)
            for dependency in dependency_graph.get(name, set()):
                visit(dependency)
            visiting.remove(name)
            visited.add(name)

        for parameter_name in dependency_graph:
            visit(parameter_name)

        if (
            self.primary_formula_id is not None
            and self.primary_formula_id not in self.source_formula_ids
        ):
            raise ValueError(
                "primary_formula_id는 source_formula_ids에 포함되어야 합니다."
            )
        return self


class GenerationRuleCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str
    object_type: Literal["generation_rule_catalog"]
    subject_id: str
    rule_count: int
    rules: list[GenerationRule]

    @model_validator(mode="after")
    def validate_catalog(self) -> "GenerationRuleCatalog":
        if self.rule_count != len(self.rules):
            raise ValueError(
                f"rule_count={self.rule_count}, 실제 rules={len(self.rules)}"
            )

        wrong_subjects = sorted(
            rule.rule_id
            for rule in self.rules
            if rule.subject_id != self.subject_id
        )
        if wrong_subjects:
            raise ValueError(
                "Catalog subject_id와 다른 Rule이 있습니다: "
                + ", ".join(wrong_subjects[:10])
            )

        rule_ids = [rule.rule_id for rule in self.rules]
        if len(rule_ids) != len(set(rule_ids)):
            raise ValueError("Catalog 안에 중복 rule_id가 있습니다.")
        return self
