from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from pgvector.psycopg import register_vector
from psycopg.types.json import Jsonb


# =========================================================
# 프로젝트 경로
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.db.connection import get_connection


CHUNKS_DIR = PROJECT_ROOT / "data" / "chunks"
EMBEDDINGS_DIR = PROJECT_ROOT / "data" / "embeddings"


# =========================================================
# 파일 탐색
# =========================================================

def find_embedding_files() -> list[Path]:
    return sorted(
        EMBEDDINGS_DIR.rglob("*_embeddings.npz")
    )


def find_chunk_file(
    subject_id: str,
    concept_id: str,
) -> Path:

    chunk_file = (
        CHUNKS_DIR
        / subject_id
        / f"{concept_id}_chunks.json"
    )

    if not chunk_file.exists():
        raise FileNotFoundError(
            f"Chunk 파일을 찾을 수 없습니다.\n"
            f"{chunk_file}"
        )

    return chunk_file


# =========================================================
# NPZ 읽기
# =========================================================

def load_embedding_file(
    embedding_file: Path,
):
    data = np.load(
        embedding_file,
        allow_pickle=False,
    )

    embeddings = data["embeddings"]

    concept_id = str(
        data["concept_id"].item()
    )

    subject_id = str(
        data["subject_id"].item()
    )

    embedding_model = str(
        data["embedding_model"].item()
    )

    chunk_indexes = data[
        "chunk_indexes"
    ].astype(int)

    content_hashes = [
        str(value)
        for value in data[
            "content_hashes"
        ]
    ]

    return {
        "embeddings": embeddings,
        "concept_id": concept_id,
        "subject_id": subject_id,
        "embedding_model": embedding_model,
        "chunk_indexes": chunk_indexes,
        "content_hashes": content_hashes,
    }


# =========================================================
# Embedding 파일 ↔ Chunk JSON 검증
# =========================================================

def validate_files(
    *,
    document: dict,
    embedding_data: dict,
) -> None:

    chunks = document["chunks"]

    embeddings = embedding_data[
        "embeddings"
    ]

    concept_id = embedding_data[
        "concept_id"
    ]

    # Concept ID 확인
    if document["concept_id"] != concept_id:
        raise ValueError(
            f"{concept_id}: concept_id 불일치"
        )

    # Chunk 개수 확인
    if len(chunks) != len(embeddings):
        raise ValueError(
            f"{concept_id}: "
            f"Chunk {len(chunks)}개 / "
            f"Embedding {len(embeddings)}개"
        )

    # Embedding 차원 확인
    if (
        embeddings.ndim != 2
        or embeddings.shape[1] != 768
    ):
        raise ValueError(
            f"{concept_id}: "
            f"Embedding shape 오류 "
            f"{embeddings.shape}"
        )

    chunk_indexes = embedding_data[
        "chunk_indexes"
    ]

    content_hashes = embedding_data[
        "content_hashes"
    ]

    for position, chunk in enumerate(chunks):

        # chunk_index 확인
        if (
            chunk["chunk_index"]
            != int(
                chunk_indexes[position]
            )
        ):
            raise ValueError(
                f"{concept_id}: "
                f"chunk_index 불일치 "
                f"(position={position})"
            )

        # content_hash 확인
        if (
            chunk["content_hash"]
            != content_hashes[position]
        ):
            raise ValueError(
                f"{concept_id}: "
                f"content_hash 불일치 "
                f"(chunk_index="
                f"{chunk['chunk_index']})"
            )


# =========================================================
# DB 저장
# =========================================================

def save_concept_embeddings(
    *,
    connection,
    document: dict,
    embedding_data: dict,
) -> int:

    concept_id = embedding_data[
        "concept_id"
    ]

    embedding_model = embedding_data[
        "embedding_model"
    ]

    embeddings = embedding_data[
        "embeddings"
    ]

    chunks = document["chunks"]

    # -----------------------------------------------------
    # 같은 Concept + 같은 embedding model 기존 데이터 삭제
    # -----------------------------------------------------

    connection.execute(
        """
        DELETE FROM kb.concept_chunks
        WHERE concept_id = %s
          AND embedding_model = %s
        """,
        (
            concept_id,
            embedding_model,
        ),
    )

    # -----------------------------------------------------
    # INSERT
    # -----------------------------------------------------

    sql = """
        INSERT INTO kb.concept_chunks (
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
            embedding,
            metadata
        )
        VALUES (
            %(concept_id)s,
            %(subject_id)s,
            %(chapter_id)s,
            %(chunk_index)s,
            %(chunk_type)s,
            %(heading)s,
            %(content_text)s,
            %(token_count)s,
            %(content_hash)s,
            %(source_content_version)s,
            %(embedding_model)s,
            %(embedding)s,
            %(metadata)s
        )
    """

    inserted_count = 0

    for chunk, embedding in zip(
        chunks,
        embeddings,
        strict=True,
    ):

        connection.execute(
            sql,
            {
                "concept_id":
                    chunk["concept_id"],

                "subject_id":
                    chunk["subject_id"],

                "chapter_id":
                    chunk["chapter_id"],

                "chunk_index":
                    chunk["chunk_index"],

                "chunk_type":
                    chunk["chunk_type"],

                "heading":
                    chunk["heading"],

                "content_text":
                    chunk["content_text"],

                "token_count":
                    chunk["token_count"],

                "content_hash":
                    chunk["content_hash"],

                "source_content_version":
                    chunk[
                        "source_content_version"
                    ],

                "embedding_model":
                    embedding_model,

                # NumPy float32 벡터를
                # pgvector가 처리
                "embedding":
                    embedding.astype(
                        np.float32
                    ),

                "metadata":
                    Jsonb(
                        chunk.get(
                            "metadata",
                            {},
                        )
                    ),
            },
        )

        inserted_count += 1

    return inserted_count


# =========================================================
# Main
# =========================================================

def main() -> None:

    embedding_files = (
        find_embedding_files()
    )

    if not embedding_files:
        raise FileNotFoundError(
            "Embedding 파일을 찾을 수 없습니다.\n"
            f"{EMBEDDINGS_DIR}"
        )

    print("=" * 70)
    print("Vector DB 저장 시작")
    print(
        f"Embedding 파일 수: "
        f"{len(embedding_files)}"
    )
    print("=" * 70)

    connection = get_connection()

    try:

        # PostgreSQL vector 타입 등록
        register_vector(connection)

        total_inserted = 0

        for file_number, embedding_file in enumerate(
            embedding_files,
            start=1,
        ):

            # ---------------------------------------------
            # Embedding 읽기
            # ---------------------------------------------

            embedding_data = (
                load_embedding_file(
                    embedding_file
                )
            )

            concept_id = embedding_data[
                "concept_id"
            ]

            subject_id = embedding_data[
                "subject_id"
            ]

            # ---------------------------------------------
            # 대응하는 Chunk JSON
            # ---------------------------------------------

            chunk_file = find_chunk_file(
                subject_id,
                concept_id,
            )

            document = json.loads(
                chunk_file.read_text(
                    encoding="utf-8"
                )
            )

            # ---------------------------------------------
            # Chunk / Embedding 무결성 검증
            # ---------------------------------------------

            validate_files(
                document=document,
                embedding_data=embedding_data,
            )

            # ---------------------------------------------
            # Concept 단위 Transaction
            # ---------------------------------------------

            with connection.transaction():

                inserted = (
                    save_concept_embeddings(
                        connection=connection,
                        document=document,
                        embedding_data=embedding_data,
                    )
                )

            total_inserted += inserted

            print(
                f"[{file_number}/"
                f"{len(embedding_files)}] "
                f"{concept_id} "
                f"→ {inserted}개 저장"
            )

        print()
        print("=" * 70)
        print("Vector DB 저장 완료")
        print(
            f"Embedding 파일: "
            f"{len(embedding_files)}"
        )
        print(
            f"저장된 Chunk: "
            f"{total_inserted}"
        )
        print("=" * 70)

    finally:
        connection.close()


if __name__ == "__main__":
    main()