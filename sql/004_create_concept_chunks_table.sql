CREATE TABLE IF NOT EXISTS kb.concept_chunks (
    chunk_id BIGSERIAL PRIMARY KEY,

    concept_id VARCHAR(200) NOT NULL
        REFERENCES kb.concepts(concept_id)
        ON DELETE CASCADE,

    subject_id VARCHAR(50) NOT NULL,
    chapter_id VARCHAR(150) NOT NULL,

    chunk_index INTEGER NOT NULL,
    chunk_type VARCHAR(30) NOT NULL,

    heading TEXT NOT NULL,
    content_text TEXT NOT NULL,

    token_count INTEGER NOT NULL,

    content_hash CHAR(64) NOT NULL,

    source_content_version INTEGER NOT NULL,

    embedding_model VARCHAR(200) NOT NULL,

    embedding VECTOR(768) NOT NULL,

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT concept_chunks_unique
        UNIQUE (
            concept_id,
            chunk_index,
            embedding_model
        ),

    CONSTRAINT concept_chunks_token_count_check
        CHECK (token_count >= 1)
);

CREATE INDEX IF NOT EXISTS idx_concept_chunks_concept_id
ON kb.concept_chunks (concept_id);

CREATE INDEX IF NOT EXISTS idx_concept_chunks_subject_id
ON kb.concept_chunks (subject_id);

CREATE INDEX IF NOT EXISTS idx_concept_chunks_chapter_id
ON kb.concept_chunks (chapter_id);

CREATE INDEX IF NOT EXISTS idx_concept_chunks_chunk_type
ON kb.concept_chunks (chunk_type);

CREATE INDEX IF NOT EXISTS idx_concept_chunks_embedding_model
ON kb.concept_chunks (embedding_model);