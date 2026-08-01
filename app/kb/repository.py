from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from app.db.queries import (
    COUNT_CONCEPTS_BY_SUBJECT_SQL,
    COUNT_CONCEPTS_SQL,
    UPSERT_CONCEPT_SQL,
)


ConceptRecord = dict[str, Any]


def upsert_concepts(
    connection: psycopg.Connection,
    records: Iterable[ConceptRecord],
) -> int:
    """
    Concept 레코드를 kb.concepts에 저장한다.

    concept_id가 이미 존재하면 기존 데이터를 갱신한다.
    반환값은 처리한 Concept 개수다.
    """

    processed_count = 0

    with connection.cursor() as cursor:
        for record in records:
            parameters = dict(record)

            # Python dict를 PostgreSQL JSONB로 변환
            parameters["content"] = Jsonb(record["content"])

            cursor.execute(
                UPSERT_CONCEPT_SQL,
                parameters,
            )

            result = cursor.fetchone()

            if result is None:
                raise RuntimeError(
                    f"Concept 저장 결과가 없습니다: "
                    f"{record['concept_id']}"
                )

            processed_count += 1

    return processed_count


def count_concepts(
    connection: psycopg.Connection,
) -> int:
    """kb.concepts 전체 행 수를 반환한다."""

    with connection.cursor() as cursor:
        cursor.execute(COUNT_CONCEPTS_SQL)
        result = cursor.fetchone()

    if result is None:
        return 0

    return int(result["concept_count"])


def count_concepts_by_subject(
    connection: psycopg.Connection,
) -> list[dict[str, Any]]:
    """과목별 Concept 개수를 반환한다."""

    with connection.cursor() as cursor:
        cursor.execute(COUNT_CONCEPTS_BY_SUBJECT_SQL)
        rows = cursor.fetchall()

    return list(rows)