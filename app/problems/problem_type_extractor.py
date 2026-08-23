from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.concept import ConceptCatalog


class ProblemTypeInfo(BaseModel):
    """Concept JSON에서 추출한 Problem Type 메타데이터."""

    model_config = ConfigDict(extra="forbid")

    # Taxonomy
    subject_id: str
    subject_name_ko: str
    unit_id: str
    unit_name_ko: str
    concept_id: str
    concept_name_ko: str

    # Problem classification
    problem_type: str
    language: str = "ko-KR"

    # Concept / generation metadata
    formula_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    supported_answer_types: list[str] = Field(default_factory=list)

    difficulty_min: int | None = None
    difficulty_max: int | None = None

    recommended_validators: list[str] = Field(default_factory=list)
    generation_notes: str | None = None

    source_file: str | None = None


def extract_from_concept(
    catalog: ConceptCatalog,
    concept,
    *,
    source_file: str | None = None,
) -> list[ProblemTypeInfo]:
    """
    Concept 하나에서 generation_profile.enabled=True인
    supported_problem_types를 ProblemTypeInfo로 변환한다.
    """

    profile = getattr(concept, "generation_profile", None)

    if profile is None or not getattr(profile, "enabled", False):
        return []

    problem_types = list(
        getattr(profile, "supported_problem_types", []) or []
    )

    if not problem_types:
        return []

    # ------------------------------------------------------------------
    # Taxonomy
    # ------------------------------------------------------------------
    subject = getattr(catalog, "subject", None)
    unit = getattr(catalog, "unit", None)

    subject_id = getattr(subject, "subject_id", None)
    subject_name_ko = getattr(subject, "name_ko", None)

    unit_id = getattr(unit, "unit_id", None)
    unit_name_ko = getattr(unit, "name_ko", None)

    concept_id = getattr(concept, "concept_id", None)
    concept_name_ko = (
        getattr(concept, "name_ko", None)
        or getattr(concept, "concept_name_ko", None)
        or concept_id
    )

    if not subject_id:
        raise ValueError(f"subject_id가 없습니다: {source_file}")

    if not subject_name_ko:
        subject_name_ko = subject_id

    if not unit_id:
        raise ValueError(f"unit_id가 없습니다: {source_file}")

    if not unit_name_ko:
        unit_name_ko = unit_id

    if not concept_id:
        raise ValueError(f"concept_id가 없습니다: {source_file}")

    # ------------------------------------------------------------------
    # Generation metadata
    # ------------------------------------------------------------------
    difficulty_range = getattr(profile, "difficulty_range", None)

    difficulty_min = (
        getattr(difficulty_range, "min", None)
        if difficulty_range is not None
        else None
    )

    difficulty_max = (
        getattr(difficulty_range, "max", None)
        if difficulty_range is not None
        else None
    )

    formulas = list(getattr(concept, "formulas", []) or [])

    formula_ids = [
        getattr(formula, "formula_id")
        for formula in formulas
        if getattr(formula, "formula_id", None)
    ]

    tags = list(getattr(concept, "tags", []) or [])

    supported_answer_types = list(
        getattr(profile, "supported_answer_types", []) or []
    )

    recommended_validators = list(
        getattr(profile, "recommended_validators", []) or []
    )

    generation_notes = getattr(
        profile,
        "generation_notes",
        None,
    )

    language = getattr(catalog, "language", None) or "ko-KR"

    return [
        ProblemTypeInfo(
            subject_id=subject_id,
            subject_name_ko=subject_name_ko,
            unit_id=unit_id,
            unit_name_ko=unit_name_ko,
            concept_id=concept_id,
            concept_name_ko=concept_name_ko,
            problem_type=problem_type,
            language=language,
            formula_ids=formula_ids,
            tags=tags,
            supported_answer_types=supported_answer_types,
            difficulty_min=difficulty_min,
            difficulty_max=difficulty_max,
            recommended_validators=recommended_validators,
            generation_notes=generation_notes,
            source_file=source_file,
        )
        for problem_type in problem_types
    ]


def extract_from_catalog(
    catalog: ConceptCatalog,
    *,
    source_file: str | None = None,
) -> list[ProblemTypeInfo]:
    """ConceptCatalog 안의 모든 Concept에서 Problem Type을 추출한다."""

    results: list[ProblemTypeInfo] = []

    for concept in list(getattr(catalog, "concepts", []) or []):
        results.extend(
            extract_from_concept(
                catalog,
                concept,
                source_file=source_file,
            )
        )

    return results


def extract_from_file(
    file_path: str | Path,
) -> list[ProblemTypeInfo]:
    """Concept JSON 파일 하나를 Pydantic 검증 후 Problem Type으로 변환한다."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {path}")

    if not path.is_file():
        raise ValueError(f"파일 경로가 아닙니다: {path}")

    if path.suffix.lower() != ".json":
        raise ValueError(f"JSON 파일이 아닙니다: {path}")

    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    catalog = ConceptCatalog.model_validate(raw)

    return extract_from_catalog(
        catalog,
        source_file=str(path),
    )


def _iter_json_files(
    directory: Path,
    *,
    recursive: bool,
) -> Iterable[Path]:
    if recursive:
        yield from sorted(directory.rglob("*.json"))
    else:
        yield from sorted(directory.glob("*.json"))


def extract_from_directory(
    directory: str | Path,
    *,
    recursive: bool = True,
) -> list[ProblemTypeInfo]:
    """
    디렉터리 안의 Concept JSON 전체에서 Problem Type을 추출한다.

    예:
        extract_from_directory("data/concepts/linear_algebra")
        extract_from_directory("data/concepts")
    """

    path = Path(directory)

    if not path.exists():
        raise FileNotFoundError(
            f"디렉터리를 찾을 수 없습니다: {path}"
        )

    if not path.is_dir():
        raise ValueError(
            f"디렉터리 경로가 아닙니다: {path}"
        )

    results: list[ProblemTypeInfo] = []

    for json_file in _iter_json_files(
        path,
        recursive=recursive,
    ):
        results.extend(
            extract_from_file(json_file)
        )

    return results


def unique_problem_types(
    items: Iterable[ProblemTypeInfo],
) -> list[str]:
    """중복 제거한 Problem Type 문자열 목록을 정렬해 반환한다."""

    return sorted(
        {
            item.problem_type
            for item in items
        }
    )