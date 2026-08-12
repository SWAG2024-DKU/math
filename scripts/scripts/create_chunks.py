from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.db.connection import get_connection
from app.kb.chunker import (
    ChunkSource,
    ConceptChunker,
)


load_dotenv(PROJECT_ROOT / ".env")


CHUNKS_DIR = PROJECT_ROOT / "data" / "chunks"


def load_concepts(
    concept_id: str | None = None,
    subject_id: str | None = None,
) -> list[dict[str, Any]]:
    """DB에서 Chunk 생성 대상 Concept를 조회함."""

    where_conditions: list[str] = []
    parameters: dict[str, Any] = {}

    if concept_id:
        where_conditions.append(
            "concept_id = %(concept_id)s"
        )
        parameters["concept_id"] = concept_id

    if subject_id:
        where_conditions.append(
            "subject_id = %(subject_id)s"
        )
        parameters["subject_id"] = subject_id

    where_sql = ""

    if where_conditions:
        where_sql = (
            "WHERE "
            + " AND ".join(where_conditions)
        )

    query = f"""
    SELECT
        concept_id,
        subject_id,
        chapter_id,
        name_ko,
        content_version,
        content
    FROM kb.concepts
    {where_sql}
    ORDER BY
        subject_id,
        chapter_id,
        concept_id;
    """

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                query,
                parameters,
            )

            rows = cursor.fetchall()

    finally:
        connection.close()

    return list(rows)


def save_chunk_collection(
    collection,
) -> Path:
    """ChunkCollection을 과목별 JSON 파일로 저장함."""

    output_directory = (
        CHUNKS_DIR
        / collection.subject_id
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_concept_id = (
        collection.concept_id
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
    )

    output_path = (
        output_directory
        / f"{safe_concept_id}_chunks.json"
    )

    output_path.write_text(
        json.dumps(
            collection.model_dump(
                mode="json"
            ),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return output_path


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "kb.concepts의 JSONB 데이터를 "
            "의미 단위 Chunk로 분할함."
        )
    )

    parser.add_argument(
        "--concept-id",
        type=str,
        default=None,
        help="Concept 하나만 Chunk로 분할함.",
    )

    parser.add_argument(
        "--subject",
        type=str,
        default=None,
        help="특정 과목만 Chunk로 분할함.",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="전체 Concept를 Chunk로 분할함.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    if not any(
        [
            args.concept_id,
            args.subject,
            args.all,
        ]
    ):
        print(
            "검수 안전을 위해 대상을 지정해야 함."
        )
        print()
        print(
            "예시:"
        )
        print(
            "python scripts\\create_chunks.py "
            "--concept-id calculus.limit_definition"
        )
        raise SystemExit(1)

    model_name = os.getenv(
        "EMBEDDING_MODEL",
        "intfloat/multilingual-e5-base",
    )

    max_tokens = int(
        os.getenv(
            "CHUNK_MAX_TOKENS",
            "420",
        )
    )

    chunker = ConceptChunker(
        model_name=model_name,
        max_tokens=max_tokens,
    )

    concepts = load_concepts(
        concept_id=args.concept_id,
        subject_id=args.subject,
    )

    if not concepts:
        print("Chunk 생성 대상 Concept가 없음.")
        raise SystemExit(1)

    total_chunk_count = 0

    print()
    print(
        f"Chunk 생성 대상 Concept: "
        f"{len(concepts)}개"
    )
    print()

    for row in concepts:
        source = ChunkSource(
            concept_id=row["concept_id"],
            subject_id=row["subject_id"],
            chapter_id=row["chapter_id"],
            concept_name_ko=row["name_ko"],
            content_version=(
                row["content_version"]
            ),
            content=row["content"],
        )

        collection = chunker.create_chunks(
            source
        )

        output_path = save_chunk_collection(
            collection
        )

        total_chunk_count += len(
            collection.chunks
        )

        maximum_tokens = max(
            chunk.token_count
            for chunk in collection.chunks
        )

        print(
            f"[완료] {source.concept_id}"
            f" → {len(collection.chunks)}개 Chunk"
            f" / 최대 {maximum_tokens} tokens"
        )
        print(
            f"       {output_path}"
        )

    print()
    print("=" * 60)
    print(
        f"처리한 Concept: {len(concepts)}개"
    )
    print(
        f"생성한 Chunk: {total_chunk_count}개"
    )


if __name__ == "__main__":
    main()