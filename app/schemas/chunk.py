from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


ChunkType = Literal[
    "definition",
    "formula",
    "condition",
    "property",
    "learning",
    "misconception",
    "generation",
]


class StrictModel(BaseModel):
    """정의되지 않은 필드를 허용하지 않는 기본 모델임."""

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        str_strip_whitespace=True,
    )


class ConceptChunk(StrictModel):
    """Concept에서 분할한 검색·Embedding용 Chunk임."""

    chunk_schema_version: str = "1.0.0"

    concept_id: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    chapter_id: str = Field(min_length=1)

    concept_name_ko: str = Field(min_length=1)

    chunk_index: int = Field(ge=0)
    chunk_type: ChunkType

    heading: str = Field(min_length=1)
    content_text: str = Field(min_length=1)

    token_count: int = Field(ge=1)
    content_hash: str = Field(
        min_length=64,
        max_length=64,
    )

    source_content_version: int = Field(ge=1)

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class ChunkCollection(StrictModel):
    """Concept 하나에서 생성된 Chunk 묶음임."""

    chunk_schema_version: str = "1.0.0"

    concept_id: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    chapter_id: str = Field(min_length=1)
    concept_name_ko: str = Field(min_length=1)

    embedding_model: str = Field(min_length=1)
    max_tokens: int = Field(ge=1)

    chunks: list[ConceptChunk] = Field(
        min_length=1
    )