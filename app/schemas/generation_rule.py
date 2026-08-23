from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class FlexibleModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class ConstraintSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    expression: str
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
    supported_answer_types: list[str] = Field(default_factory=list)

    parameter_spec: dict[str, FlexibleModel] = Field(default_factory=dict)
    constraints: list[ConstraintSpec] = Field(default_factory=list)

    construction: ConstructionSpec
    answer_spec: AnswerSpec
    validation: ValidationSpec
    difficulty: DifficultySpec

    notes: str | None = None


class GenerationRuleCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str
    object_type: Literal["generation_rule_catalog"]
    subject_id: str
    rule_count: int
    rules: list[GenerationRule]
