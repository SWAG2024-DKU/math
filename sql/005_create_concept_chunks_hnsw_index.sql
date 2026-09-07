CREATE INDEX IF NOT EXISTS idx_concept_chunks_embedding_hnsw
ON kb.concept_chunks
USING hnsw (embedding vector_cosine_ops);