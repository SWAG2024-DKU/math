from __future__ import annotations

import os
from typing import Any

import numpy as np
from pgvector.psycopg import register_vector

from app.db.connection import get_connection
from app.kb.embedder import ConceptEmbedder


DEFAULT_EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "intfloat/multilingual-e5-base",
)


class VectorSearcher:
    """
    PostgreSQL + pgvector 기반 Concept Chunk Vector Search.

    처리 흐름
    ---------
    query
      -> E5 query embedding 생성
      -> pgvector cosine similarity 검색
      -> Top-K chunk 반환
    """

    def __init__(
        self,
        *,
        model_name: str = DEFAULT_EMBEDDING_MODEL,
        embedder: ConceptEmbedder | None = None,
    ) -> None:

        self.model_name = model_name

        # 외부에서 Embedder를 주입할 수도 있고,
        # 없으면 여기서 생성
        self.embedder = (
            embedder
            if embedder is not None
            else ConceptEmbedder(
                model_name=model_name
            )
        )

    # =====================================================
    # Query Embedding
    # =====================================================

    def embed_query(
        self,
        query: str,
    ) -> np.ndarray:

        query = query.strip()

        if not query:
            raise ValueError(
                "검색어(query)는 비어 있을 수 없습니다."
            )

        embedding = self.embedder.embed_query(
            query
        )

        embedding = np.asarray(
            embedding,
            dtype=np.float32,
        )

        if embedding.ndim != 1:
            raise ValueError(
                "Query embedding은 "
                "1차원 벡터여야 합니다. "
                f"shape={embedding.shape}"
            )

        if embedding.shape[0] != 768:
            raise ValueError(
                "Embedding 차원이 올바르지 않습니다. "
                f"현재={embedding.shape[0]}, "
                "예상=768"
            )

        return embedding

    # =====================================================
    # Vector Search
    # =====================================================

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        subject_id: str | None = None,
        chunk_type: str | None = None,
        min_similarity: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        검색어와 의미적으로 유사한 Concept Chunk 검색.

        Parameters
        ----------
        query:
            사용자 검색 문장.

        top_k:
            반환할 최대 검색 결과 수.

        subject_id:
            특정 과목으로 검색 범위를 제한.
            예: "linear_algebra"

        chunk_type:
            특정 Chunk 유형으로 제한.
            예: "definition", "formula"

        min_similarity:
            최소 cosine similarity.
            예: 0.70

        Returns
        -------
        list[dict]
            유사도가 높은 순서대로 검색 결과 반환.
        """

        if top_k < 1:
            raise ValueError(
                "top_k는 1 이상이어야 합니다."
            )

        if (
            min_similarity is not None
            and not -1.0 <= min_similarity <= 1.0
        ):
            raise ValueError(
                "min_similarity는 "
                "-1.0 이상 1.0 이하이어야 합니다."
            )

        query_embedding = self.embed_query(
            query
        )

        # -------------------------------------------------
        # WHERE 조건 동적 구성
        # -------------------------------------------------

        conditions = [
            "embedding_model = %(embedding_model)s"
        ]

        params: dict[str, Any] = {
            "embedding_model": self.model_name,
            "query_embedding": query_embedding,
            "top_k": top_k,
        }

        if subject_id is not None:
            conditions.append(
                "subject_id = %(subject_id)s"
            )
            params["subject_id"] = subject_id

        if chunk_type is not None:
            conditions.append(
                "chunk_type = %(chunk_type)s"
            )
            params["chunk_type"] = chunk_type

        where_clause = " AND ".join(
            conditions
        )

        # -------------------------------------------------
        # cosine similarity
        #
        # <=> = cosine distance
        #
        # similarity = 1 - distance
        # -------------------------------------------------

        similarity_expression = (
            "1 - "
            "(embedding <=> %(query_embedding)s)"
        )

        sql = f"""
            SELECT
                chunk_id,
                concept_id,
                subject_id,
                chapter_id,
                chunk_index,
                chunk_type,
                heading,
                content_text,
                token_count,
                content_hash,
                source_content_version,
                embedding_model,
                metadata,
                {similarity_expression}
                    AS similarity
            FROM kb.concept_chunks
            WHERE {where_clause}
        """

        # 최소 similarity가 지정된 경우
        if min_similarity is not None:
            sql += f"""
                AND {similarity_expression}
                    >= %(min_similarity)s
            """

            params[
                "min_similarity"
            ] = min_similarity

        sql += """
            ORDER BY
                embedding <=> %(query_embedding)s
            LIMIT %(top_k)s
        """

        # -------------------------------------------------
        # DB 검색
        # -------------------------------------------------

        connection = get_connection()

        try:
            register_vector(connection)

            rows = connection.execute(
                sql,
                params,
            ).fetchall()

        finally:
            connection.close()

        # -------------------------------------------------
        # 결과 정리
        #
        # get_connection()이 dict row를 반환한다는
        # 현재 프로젝트 설정 기준
        # -------------------------------------------------

        results: list[dict[str, Any]] = []

        for rank, row in enumerate(
            rows,
            start=1,
        ):

            result = {
                "rank": rank,
                "chunk_id": row["chunk_id"],
                "concept_id": row[
                    "concept_id"
                ],
                "subject_id": row[
                    "subject_id"
                ],
                "chapter_id": row[
                    "chapter_id"
                ],
                "chunk_index": row[
                    "chunk_index"
                ],
                "chunk_type": row[
                    "chunk_type"
                ],
                "heading": row["heading"],
                "content_text": row[
                    "content_text"
                ],
                "token_count": row[
                    "token_count"
                ],
                "content_hash": row[
                    "content_hash"
                ],
                "source_content_version": row[
                    "source_content_version"
                ],
                "embedding_model": row[
                    "embedding_model"
                ],
                "metadata": row[
                    "metadata"
                ],
                "similarity": float(
                    row["similarity"]
                ),
            }

            results.append(result)

        return results