UPSERT_CONCEPT_SQL = """
INSERT INTO kb.concepts (
    concept_id,
    subject_id,
    chapter_id,
    section_id,
    name_ko,
    name_en,
    raw_markdown,
    content,
    schema_version
)
VALUES (
    %(concept_id)s,
    %(subject_id)s,
    %(chapter_id)s,
    %(section_id)s,
    %(name_ko)s,
    %(name_en)s,
    %(raw_markdown)s,
    %(content)s,
    %(schema_version)s
)
ON CONFLICT (concept_id)
DO UPDATE SET
    subject_id = EXCLUDED.subject_id,
    chapter_id = EXCLUDED.chapter_id,
    section_id = EXCLUDED.section_id,
    name_ko = EXCLUDED.name_ko,
    name_en = EXCLUDED.name_en,

    raw_markdown = CASE
        WHEN EXCLUDED.raw_markdown <> ''
        THEN EXCLUDED.raw_markdown
        ELSE kb.concepts.raw_markdown
    END,

    content = EXCLUDED.content,
    schema_version = EXCLUDED.schema_version,

    content_version = CASE
        WHEN kb.concepts.content IS DISTINCT FROM EXCLUDED.content
        THEN kb.concepts.content_version + 1
        ELSE kb.concepts.content_version
    END,

    updated_at = NOW()

RETURNING
    concept_id,
    content_version;
"""


COUNT_CONCEPTS_SQL = """
SELECT COUNT(*) AS concept_count
FROM kb.concepts;
"""


COUNT_CONCEPTS_BY_SUBJECT_SQL = """
SELECT
    subject_id,
    COUNT(*) AS concept_count
FROM kb.concepts
GROUP BY subject_id
ORDER BY subject_id;
"""