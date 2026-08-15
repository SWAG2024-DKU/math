from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.schemas.concept import Concept, ConceptCatalog


@dataclass(frozen=True, slots=True)
class ProblemTypeInfo:
    """
    Concept에서 추출한 하나의 문제 유형과 그 출처 정보.

    Problem Type 자체뿐 아니라 다음 단계인 Generation Rule 조회와
    ProblemTemplate 조립에 필요한 최소 메타데이터를 함께 보존한다.
    """

    language: str

    subject_id: str
    subject_name_ko: str

    unit_id: str
    unit_name_ko: str

    concept_id: str
    concept_name_ko: str

    problem_type: str

    formula_ids: tuple[str, ...]
    tags: tuple[str, ...]

    supported_answer_types: tuple[str, ...]
    difficulty_min: int
    difficulty_max: int
    recommended_validators: tuple[str, ...]
    generation_notes: str | None

    def to_dict(self) -> dict[str, Any]:
        """JSON 직렬화 등에 사용할 수 있는 dict 형태로 변환한다."""
        return asdict(self)


def _ensure_unique_problem_types(concept: Concept) -> None:
    """
    하나의 Concept 안에 같은 problem_type이 중복 선언되었는지 확인한다.

    현재 Concept Pydantic Schema는 supported_problem_types 내부 중복까지는
    검사하지 않으므로 추출 단계에서 중복 생성을 방지한다.
    """

    problem_types = concept.generation_profile.supported_problem_types

    if len(problem_types) != len(set(problem_types)):
        duplicated = sorted(
            {
                problem_type
                for problem_type in problem_types
                if problem_types.count(problem_type) > 1
            }
        )
        raise ValueError(
            f"{concept.concept_id}: supported_problem_types에 중복이 있습니다: "
            f"{', '.join(duplicated)}"
        )


def extract_from_concept(
    catalog: ConceptCatalog,
    concept: Concept,
) -> list[ProblemTypeInfo]:
    """
    Concept 하나에서 활성화된 Problem Type을 추출한다.

    generation_profile.enabled가 False이면 빈 목록을 반환한다.
    Problem Type 하나당 ProblemTypeInfo 하나를 생성한다.
    """

    profile = concept.generation_profile

    if not profile.enabled:
        return []

    _ensure_unique_problem_types(concept)

    formula_ids = tuple(
        formula.formula_id
        for formula in concept.formulas
    )
    tags = tuple(concept.tags)
    supported_answer_types = tuple(profile.supported_answer_types)
    recommended_validators = tuple(profile.recommended_validators)

    return [
        ProblemTypeInfo(
            language=catalog.language,
            subject_id=catalog.subject.subject_id,
            subject_name_ko=catalog.subject.name_ko,
            unit_id=catalog.unit.unit_id,
            unit_name_ko=catalog.unit.name_ko,
            concept_id=concept.concept_id,
            concept_name_ko=concept.name_ko,
            problem_type=problem_type,
            formula_ids=formula_ids,
            tags=tags,
            supported_answer_types=supported_answer_types,
            difficulty_min=profile.difficulty_range.min,
            difficulty_max=profile.difficulty_range.max,
            recommended_validators=recommended_validators,
            generation_notes=profile.generation_notes,
        )
        for problem_type in profile.supported_problem_types
    ]


def extract_from_catalog(
    catalog: ConceptCatalog,
) -> list[ProblemTypeInfo]:
    """ConceptCatalog 안의 모든 Concept에서 Problem Type을 추출한다."""

    problem_types: list[ProblemTypeInfo] = []

    for concept in catalog.concepts:
        problem_types.extend(
            extract_from_concept(
                catalog=catalog,
                concept=concept,
            )
        )

    return problem_types


def load_catalog(path: str | Path) -> ConceptCatalog:
    """
    Concept JSON 파일을 읽고 기존 ConceptCatalog Pydantic 모델로 검증한다.

    JSON 문법 오류나 Pydantic 검증 오류는 파일 경로를 포함한 예외로
    다시 전달해 어느 Concept 파일에서 문제가 발생했는지 알 수 있게 한다.
    """

    catalog_path = Path(path)

    if not catalog_path.is_file():
        raise FileNotFoundError(
            f"Concept JSON 파일을 찾을 수 없습니다: {catalog_path}"
        )

    try:
        raw = json.loads(
            catalog_path.read_text(encoding="utf-8")
        )
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"유효하지 않은 JSON 파일입니다: {catalog_path}"
        ) from exc

    try:
        return ConceptCatalog.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(
            f"ConceptCatalog 검증에 실패했습니다: {catalog_path}\n{exc}"
        ) from exc


def extract_from_file(
    path: str | Path,
) -> list[ProblemTypeInfo]:
    """Concept JSON 파일 하나에서 모든 Problem Type을 추출한다."""

    return extract_from_catalog(
        load_catalog(path)
    )


def extract_from_directory(
    directory: str | Path,
    *,
    recursive: bool = True,
) -> list[ProblemTypeInfo]:
    """
    디렉터리 안의 Concept JSON 파일들을 순회하며 Problem Type을 추출한다.

    기본적으로 하위 과목 디렉터리까지 재귀 탐색한다. 따라서
    data/concepts/linear_algebra뿐 아니라 data/concepts 전체를 넘겨도 된다.
    파일 순서는 실행할 때마다 동일하도록 경로명 기준으로 정렬한다.
    """

    concepts_dir = Path(directory)

    if not concepts_dir.is_dir():
        raise NotADirectoryError(
            f"Concept 디렉터리를 찾을 수 없습니다: {concepts_dir}"
        )

    pattern = "**/*.json" if recursive else "*.json"
    concept_files = sorted(concepts_dir.glob(pattern))

    problem_types: list[ProblemTypeInfo] = []

    for concept_file in concept_files:
        problem_types.extend(
            extract_from_file(concept_file)
        )

    return problem_types