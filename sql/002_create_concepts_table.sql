CREATE TABLE IF NOT EXISTS kb.concepts (
    concept_id VARCHAR(200) PRIMARY KEY,

    subject_id VARCHAR(50) NOT NULL,
    chapter_id VARCHAR(150) NOT NULL,
    section_id VARCHAR(150),

    name_ko VARCHAR(300) NOT NULL,
    name_en VARCHAR(300),

    raw_markdown TEXT NOT NULL DEFAULT '',

    content JSONB NOT NULL,

    schema_version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    content_version INTEGER NOT NULL DEFAULT 1,

    status VARCHAR(20) NOT NULL DEFAULT 'draft',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT concepts_status_check
        CHECK (
            status IN (
                'draft',
                'reviewed',
                'published',
                'deprecated'
            )
        ),

    CONSTRAINT concepts_content_type_check
        CHECK (
            jsonb_typeof(content) = 'object'
        ),

    CONSTRAINT concepts_content_version_check
        CHECK (
            content_version >= 1
        )
);


CREATE INDEX IF NOT EXISTS idx_concepts_subject_id
ON kb.concepts (subject_id);


CREATE INDEX IF NOT EXISTS idx_concepts_chapter_id
ON kb.concepts (chapter_id);


CREATE INDEX IF NOT EXISTS idx_concepts_subject_chapter
ON kb.concepts (subject_id, chapter_id);


CREATE INDEX IF NOT EXISTS idx_concepts_status
ON kb.concepts (status);


CREATE INDEX IF NOT EXISTS idx_concepts_content_gin
ON kb.concepts
USING GIN (content);