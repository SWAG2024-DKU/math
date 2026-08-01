from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.db.connection import get_connection
from app.kb.repository import (
    count_concepts,
    count_concepts_by_subject,
    upsert_concepts,
)
from app.schemas.concept import ConceptCatalog


CONCEPTS_DIR = PROJECT_ROOT / "data" / "concepts"
MARKDOWN_DIR = PROJECT_ROOT / "data" / "markdown"


def load_catalog(file_path: Path) -> ConceptCatalog:
    """JSON 파일을 읽고 Pydantic 검증을 다시 수행한다."""

    raw_text = file_path.read_text(
        encoding="utf-8-sig"
    )

    raw_data = json.loads(raw_text)

    return ConceptCatalog.model_validate(raw_data)


def build_markdown_index(
    subject_id: str,
) -> dict[str, Path]:
    """
    해당 과목 Markdown 파일명을 소문자 기준으로 색인한다.
    """

    subject_directory = MARKDOWN_DIR / subject_id

    if not subject_directory.exists():
        return {}

    return {
        path.name.lower(): path
        for path in subject_directory.rglob("*.md")
    }


def read_source_markdown(
    catalog: ConceptCatalog,
) -> tuple[str, list[str]]:
    """
    catalog.source.source_file에 기록된 Markdown을 찾아 읽는다.

    반환:
        Markdown 원문
        찾지 못한 파일명 목록
    """

    subject_id = catalog.subject.subject_id
    markdown_index = build_markdown_index(
        subject_id
    )

    markdown_parts: list[str] = []
    missing_files: list[str] = []

    for source_name in catalog.source.source_file:
        matched_path = markdown_index.get(
            source_name.lower()
        )

        if matched_path is None:
            missing_files.append(source_name)
            continue

        markdown_text = matched_path.read_text(
            encoding="utf-8-sig"
        )

        markdown_parts.append(
            "\n".join(
                [
                    f"<!-- source: {matched_path.name} -->",
                    markdown_text,
                ]
            )
        )

    return "\n\n".join(markdown_parts), missing_files


def build_content(
    catalog: ConceptCatalog,
    concept: Any,
) -> dict[str, Any]:
    """
    DB의 content JSONB에 저장할 구조를 만든다.

    Concept 필드를 최상위에 유지하여
    나중에 Chunk 생성 시 content["definition"],
    content["formulas"]처럼 바로 접근할 수 있게 한다.
    """

    concept_data = concept.model_dump(
        mode="json"
    )

    return {
        "schema_version": catalog.schema_version,
        "catalog_type": catalog.catalog_type,
        "language": catalog.language,
        "subject": catalog.subject.model_dump(
            mode="json"
        ),
        "unit": catalog.unit.model_dump(
            mode="json"
        ),
        "source": catalog.source.model_dump(
            mode="json"
        ),
        "conventions": (
            catalog.conventions.model_dump(
                mode="json"
            )
        ),
        **concept_data,
    }


def catalog_to_records(
    catalog: ConceptCatalog,
    raw_markdown: str,
) -> list[dict[str, Any]]:
    """
    ConceptCatalog의 concepts 배열을
    DB 저장용 레코드 목록으로 변환한다.
    """

    records: list[dict[str, Any]] = []

    for concept in catalog.concepts:
        records.append(
            {
                "concept_id": concept.concept_id,

                "subject_id": (
                    catalog.subject.subject_id
                ),

                # 현재 JSON의 unit_id를
                # DB chapter_id로 사용
                "chapter_id": catalog.unit.unit_id,

                # 현재 JSON에는 section_id가 없으므로 NULL
                "section_id": None,

                "name_ko": concept.name_ko,

                # 현재 Schema에는 영문명이 없으므로 NULL
                "name_en": None,

                # 원본 Markdown을 찾지 못한 경우 빈 문자열
                "raw_markdown": raw_markdown,

                "content": build_content(
                    catalog,
                    concept,
                ),

                "schema_version": (
                    catalog.schema_version
                ),
            }
        )

    return records


def collect_records() -> tuple[
    list[dict[str, Any]],
    list[str],
]:
    """data/concepts 아래 모든 JSON을 DB 레코드로 변환한다."""

    json_files = sorted(
        CONCEPTS_DIR.rglob("*.json")
    )

    if not json_files:
        raise RuntimeError(
            f"JSON 파일이 없습니다: {CONCEPTS_DIR}"
        )

    all_records: list[dict[str, Any]] = []
    warnings: list[str] = []

    seen_concept_ids: dict[str, Path] = {}

    for file_path in json_files:
        relative_path = file_path.relative_to(
            PROJECT_ROOT
        )

        try:
            catalog = load_catalog(file_path)
        except json.JSONDecodeError as error:
            raise RuntimeError(
                f"{relative_path}: JSON 문법 오류 "
                f"{error.lineno}행 {error.colno}열"
            ) from error
        except ValidationError as error:
            raise RuntimeError(
                f"{relative_path}: Pydantic 검증 실패\n"
                f"{error}"
            ) from error

        raw_markdown, missing_files = (
            read_source_markdown(catalog)
        )

        for missing_file in missing_files:
            warnings.append(
                f"{relative_path}: "
                f"Markdown 원본을 찾지 못함 - "
                f"{missing_file}"
            )

        records = catalog_to_records(
            catalog,
            raw_markdown,
        )

        for record in records:
            concept_id = record["concept_id"]

            previous_file = seen_concept_ids.get(
                concept_id
            )

            if previous_file is not None:
                raise RuntimeError(
                    "concept_id 중복 발견: "
                    f"{concept_id}\n"
                    f"기존 파일: {previous_file}\n"
                    f"중복 파일: {relative_path}"
                )

            seen_concept_ids[concept_id] = (
                relative_path
            )

        all_records.extend(records)

        print(
            f"[준비] {relative_path} "
            f"({len(records)}개 Concept)"
        )

    return all_records, warnings


def main() -> None:
    print("Concept JSON을 읽는 중...")
    print()

    records, warnings = collect_records()

    print()
    print(
        f"DB 저장 대상 Concept: {len(records)}개"
    )

    connection = get_connection()


    try:
        with connection:
            processed_count = upsert_concepts(
                connection,
                records,
            )

            total_count = count_concepts(
                connection
            )

            subject_counts = count_concepts_by_subject(
                connection
            )

    finally:
        if not connection.closed:
            connection.close()

    print()
    print("=" * 60)
    print(
        f"저장 또는 갱신 완료: "
        f"{processed_count}개"
    )
    print(
        f"kb.concepts 전체 행 수: "
        f"{total_count}개"
    )

    print()
    print("[과목별 저장 현황]")

    for row in subject_counts:
        print(
            f"  {row['subject_id']}: "
            f"{row['concept_count']}개"
        )

    if warnings:
        print()
        print("[Markdown 연결 경고]")

        for warning in warnings:
            print(f"  - {warning}")

        print()
        print(
            "경고가 있어도 Concept JSON과 JSONB는 "
            "정상 저장되었습니다."
        )


if __name__ == "__main__":
    main()