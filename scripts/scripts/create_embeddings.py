from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.kb.embedder import ConceptEmbedder


CHUNKS_DIR = PROJECT_ROOT / "data" / "chunks"
EMBEDDINGS_DIR = PROJECT_ROOT / "data" / "embeddings"


def load_chunk_files() -> list[Path]:
    return sorted(
        CHUNKS_DIR.rglob("*_chunks.json")
    )


def get_embedding_path(
    *,
    chunk_file: Path,
    subject_id: str,
    concept_id: str,
) -> Path:

    subject_dir = (
        EMBEDDINGS_DIR / subject_id
    )

    subject_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_concept_id = (
        concept_id
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
    )

    return (
        subject_dir
        / f"{safe_concept_id}_embeddings.npz"
    )


def main() -> None:

    load_dotenv(
        PROJECT_ROOT / ".env"
    )

    model_name = os.getenv(
        "EMBEDDING_MODEL",
        "intfloat/multilingual-e5-base",
    )

    chunk_files = load_chunk_files()

    if not chunk_files:
        raise FileNotFoundError(
            f"Chunk 파일을 찾을 수 없습니다: "
            f"{CHUNKS_DIR}"
        )

    print("=" * 70)
    print("전체 Embedding 생성")
    print(f"Model: {model_name}")
    print(
        f"Chunk JSON 파일: "
        f"{len(chunk_files)}개"
    )
    print("=" * 70)

    embedder = ConceptEmbedder(
        model_name=model_name
    )

    total_chunks = 0
    total_embeddings = 0

    for file_number, chunk_file in enumerate(
        chunk_files,
        start=1,
    ):

        document = json.loads(
            chunk_file.read_text(
                encoding="utf-8"
            )
        )

        concept_id = document[
            "concept_id"
        ]

        subject_id = document[
            "subject_id"
        ]

        chunks = document.get(
            "chunks",
            [],
        )

        if not chunks:
            print(
                f"[SKIP] {concept_id}: "
                "Chunk 없음"
            )
            continue

        texts = [
            chunk["content_text"]
            for chunk in chunks
        ]

        embeddings = (
            embedder.embed_passages(
                texts
            )
        )

        # 기본 검증
        if len(embeddings) != len(chunks):
            raise ValueError(
                f"{concept_id}: "
                "Chunk와 Embedding 개수가 다릅니다. "
                f"{len(chunks)} != "
                f"{len(embeddings)}"
            )

        if (
            embeddings.ndim != 2
            or embeddings.shape[1] != 768
        ):
            raise ValueError(
                f"{concept_id}: "
                "Embedding shape 오류: "
                f"{embeddings.shape}"
            )

        output_path = get_embedding_path(
            chunk_file=chunk_file,
            subject_id=subject_id,
            concept_id=concept_id,
        )

        # 벡터 + Chunk 식별정보 저장
        np.savez_compressed(
            output_path,

            embeddings=embeddings.astype(
                np.float32
            ),

            concept_id=np.array(
                concept_id
            ),

            subject_id=np.array(
                subject_id
            ),

            embedding_model=np.array(
                model_name
            ),

            chunk_indexes=np.array(
                [
                    chunk["chunk_index"]
                    for chunk in chunks
                ],
                dtype=np.int32,
            ),

            content_hashes=np.array(
                [
                    chunk["content_hash"]
                    for chunk in chunks
                ]
            ),
        )

        total_chunks += len(chunks)
        total_embeddings += len(
            embeddings
        )

        print(
            f"[{file_number}/"
            f"{len(chunk_files)}] "
            f"{concept_id} "
            f"→ Chunk {len(chunks)} "
            f"→ Embedding "
            f"{len(embeddings)} "
            f"→ 저장 완료"
        )

    print()
    print("=" * 70)
    print("Embedding 생성 완료")
    print(
        f"처리 Concept 파일: "
        f"{len(chunk_files)}"
    )
    print(
        f"처리 Chunk: "
        f"{total_chunks}"
    )
    print(
        f"생성 Embedding: "
        f"{total_embeddings}"
    )
    print(
        f"저장 위치: "
        f"{EMBEDDINGS_DIR}"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()