from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from pgvector.psycopg import register_vector


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.db.connection import get_connection
from app.kb.embedder import ConceptEmbedder


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")

    model_name = os.getenv(
        "EMBEDDING_MODEL",
        "intfloat/multilingual-e5-base",
    )

    query = "행렬의 고유값과 고유벡터"

    print("=" * 70)
    print(f"검색어: {query}")
    print(f"Embedding Model: {model_name}")
    print("=" * 70)

    # ---------------------------------------------------------
    # Query embedding 생성
    # ---------------------------------------------------------

    embedder = ConceptEmbedder(
        model_name=model_name
    )

    query_embedding = embedder.embed_query(
        query
    )

    # ---------------------------------------------------------
    # DB 연결
    # ---------------------------------------------------------

    connection = get_connection()

    try:
        # pgvector 타입 등록
        register_vector(connection)

        # -----------------------------------------------------
        # Vector Search
        #
        # <=> : cosine distance
        #
        # cosine similarity
        # = 1 - cosine distance
        # -----------------------------------------------------

        rows = connection.execute(
            """
            SELECT
                concept_id,
                subject_id,
                chapter_id,
                chunk_index,
                chunk_type,
                heading,
                content_text,
                1 - (embedding <=> %s) AS similarity
            FROM kb.concept_chunks
            WHERE embedding_model = %s
            ORDER BY embedding <=> %s
            LIMIT 5
            """,
            (
                query_embedding,
                model_name,
                query_embedding,
            ),
        ).fetchall()

        # -----------------------------------------------------
        # 검색 결과 없음
        # -----------------------------------------------------

        if not rows:
            print()
            print("검색 결과가 없습니다.")
            return

        # -----------------------------------------------------
        # 검색 결과 출력
        #
        # get_connection()의 row_factory 때문에
        # row가 dict 형태이므로
        # row["column_name"] 방식으로 접근
        # -----------------------------------------------------

        print()
        print(f"검색 결과: {len(rows)}개")

        for rank, row in enumerate(
            rows,
            start=1,
        ):
            concept_id = row["concept_id"]
            subject_id = row["subject_id"]
            chapter_id = row["chapter_id"]
            chunk_index = row["chunk_index"]
            chunk_type = row["chunk_type"]
            heading = row["heading"]
            content_text = row["content_text"]

            similarity = float(
                row["similarity"]
            )

            print()
            print("=" * 70)
            print(f"[{rank}]")
            print(f"concept_id : {concept_id}")
            print(f"subject_id : {subject_id}")
            print(f"chapter_id : {chapter_id}")
            print(f"chunk_index: {chunk_index}")
            print(f"chunk_type : {chunk_type}")
            print(f"heading    : {heading}")
            print(f"similarity : {similarity:.4f}")
            print("-" * 70)
            print(content_text[:500])

        print()
        print("=" * 70)
        print("Vector Search 테스트 완료")
        print("=" * 70)

    finally:
        connection.close()


if __name__ == "__main__":
    main()