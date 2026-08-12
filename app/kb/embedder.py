from __future__ import annotations

from sentence_transformers import SentenceTransformer


class ConceptEmbedder:
    def __init__(
        self,
        model_name: str = "intfloat/multilingual-e5-base",
    ) -> None:
        self.model_name = model_name

        print(
            f"Embedding model 불러오는 중: "
            f"{self.model_name}"
        )

        self.model = SentenceTransformer(
            self.model_name
        )

    def embed_passages(
        self,
        texts: list[str],
        batch_size: int = 32,
    ):
        if not texts:
            return []

        passage_texts = [
            f"passage: {text}"
            for text in texts
        ]

        embeddings = self.model.encode(
            passage_texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
        )

        return embeddings

    def embed_query(
        self,
        query: str,
    ):
        embedding = self.model.encode(
            [f"query: {query}"],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        return embedding[0]