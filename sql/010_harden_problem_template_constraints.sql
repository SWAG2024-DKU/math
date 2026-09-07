-- 010_harden_problem_template_constraints.sql
--
-- Existing data should be verified before applying this migration.
-- This migration hardens problem.problem_templates so invalid direct SQL INSERTs
-- are rejected even when application/Pydantic validation is bypassed.

CREATE TABLE IF NOT EXISTS problem.allowed_answer_types (
    answer_type VARCHAR(100) PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Freeze the answer types already present in the verified 3,327-row dataset.
-- A new answer type must be explicitly registered here before it can be used.
INSERT INTO problem.allowed_answer_types (answer_type)
SELECT DISTINCT answer_type
FROM problem.problem_templates
WHERE answer_type IS NOT NULL
  AND BTRIM(answer_type) <> ''
ON CONFLICT (answer_type) DO NOTHING;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'problem_templates_ready_requires_executable'
          AND conrelid = 'problem.problem_templates'::regclass
    ) THEN
        ALTER TABLE problem.problem_templates
        ADD CONSTRAINT problem_templates_ready_requires_executable
        CHECK (
            status <> 'ready'
            OR executable = TRUE
        )
        NOT VALID;
    END IF;
END
$$;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'problem_templates_positive_difficulty'
          AND conrelid = 'problem.problem_templates'::regclass
    ) THEN
        ALTER TABLE problem.problem_templates
        ADD CONSTRAINT problem_templates_positive_difficulty
        CHECK (
            difficulty_min >= 1
            AND difficulty_base >= 1
            AND difficulty_max >= 1
        )
        NOT VALID;
    END IF;
END
$$;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'problem_templates_generation_strategy_check'
          AND conrelid = 'problem.problem_templates'::regclass
    ) THEN
        ALTER TABLE problem.problem_templates
        ADD CONSTRAINT problem_templates_generation_strategy_check
        CHECK (
            generation_strategy IN (
                'forward_generation',
                'reverse_generation'
            )
        )
        NOT VALID;
    END IF;
END
$$;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'problem_templates_generation_rule_status_check'
          AND conrelid = 'problem.problem_templates'::regclass
    ) THEN
        ALTER TABLE problem.problem_templates
        ADD CONSTRAINT problem_templates_generation_rule_status_check
        CHECK (
            generation_rule_status IS NULL
            OR generation_rule_status IN (
                'draft_auto',
                'reviewed',
                'curated'
            )
        )
        NOT VALID;
    END IF;
END
$$;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'problem_templates_nonempty_identifiers'
          AND conrelid = 'problem.problem_templates'::regclass
    ) THEN
        ALTER TABLE problem.problem_templates
        ADD CONSTRAINT problem_templates_nonempty_identifiers
        CHECK (
            BTRIM(template_id) <> ''
            AND BTRIM(template_version) <> ''
            AND BTRIM(schema_version) <> ''
            AND BTRIM(subject_id) <> ''
            AND BTRIM(unit_id) <> ''
            AND BTRIM(problem_type) <> ''
            AND BTRIM(answer_type) <> ''
            AND BTRIM(generation_strategy) <> ''
            AND BTRIM(language) <> ''
            AND BTRIM(source_path) <> ''
        )
        NOT VALID;
    END IF;
END
$$;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'problem_templates_content_hash_format'
          AND conrelid = 'problem.problem_templates'::regclass
    ) THEN
        ALTER TABLE problem.problem_templates
        ADD CONSTRAINT problem_templates_content_hash_format
        CHECK (
            content_hash ~ '^[0-9a-f]{64}$'
        )
        NOT VALID;
    END IF;
END
$$;


-- Keep relational columns and duplicated values inside payload in lock-step.
-- IS NOT DISTINCT FROM is used so a missing JSON key is rejected for NOT NULL
-- relational columns instead of slipping through SQL CHECK's NULL semantics.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'problem_templates_payload_relational_consistency'
          AND conrelid = 'problem.problem_templates'::regclass
    ) THEN
        ALTER TABLE problem.problem_templates
        ADD CONSTRAINT problem_templates_payload_relational_consistency
        CHECK (
            to_jsonb(template_id::text)
                IS NOT DISTINCT FROM payload -> 'template_id'
            AND to_jsonb(template_version::text)
                IS NOT DISTINCT FROM payload -> 'template_version'
            AND to_jsonb(schema_version::text)
                IS NOT DISTINCT FROM payload -> 'schema_version'
            AND to_jsonb(status::text)
                IS NOT DISTINCT FROM payload -> 'status'
            AND to_jsonb(executable)
                IS NOT DISTINCT FROM payload -> 'executable'

            AND to_jsonb(subject_id::text)
                IS NOT DISTINCT FROM payload #> '{taxonomy,subject_id}'
            AND to_jsonb(unit_id::text)
                IS NOT DISTINCT FROM payload #> '{taxonomy,unit_id}'

            AND to_jsonb(problem_type::text)
                IS NOT DISTINCT FROM payload #> '{classification,problem_type}'
            AND to_jsonb(answer_type::text)
                IS NOT DISTINCT FROM payload #> '{classification,answer_type}'
            AND to_jsonb(difficulty_base)
                IS NOT DISTINCT FROM payload #> '{classification,difficulty,base}'
            AND to_jsonb(difficulty_min)
                IS NOT DISTINCT FROM payload #> '{classification,difficulty,min}'
            AND to_jsonb(difficulty_max)
                IS NOT DISTINCT FROM payload #> '{classification,difficulty,max}'
            AND to_jsonb(generation_strategy::text)
                IS NOT DISTINCT FROM payload #> '{classification,generation_strategy}'
            AND to_jsonb(language::text)
                IS NOT DISTINCT FROM payload #> '{classification,language}'

            AND COALESCE(
                    to_jsonb(generation_rule_id::text),
                    'null'::jsonb
                )
                IS NOT DISTINCT FROM COALESCE(
                    payload -> 'generation_rule_id',
                    'null'::jsonb
                )
            AND COALESCE(
                    to_jsonb(generation_rule_version::text),
                    'null'::jsonb
                )
                IS NOT DISTINCT FROM COALESCE(
                    payload -> 'generation_rule_version',
                    'null'::jsonb
                )
            AND COALESCE(
                    to_jsonb(generation_rule_status::text),
                    'null'::jsonb
                )
                IS NOT DISTINCT FROM COALESCE(
                    payload -> 'generation_rule_status',
                    'null'::jsonb
                )
        )
        NOT VALID;
    END IF;
END
$$;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'problem_templates_answer_type_fk'
          AND conrelid = 'problem.problem_templates'::regclass
    ) THEN
        ALTER TABLE problem.problem_templates
        ADD CONSTRAINT problem_templates_answer_type_fk
        FOREIGN KEY (answer_type)
        REFERENCES problem.allowed_answer_types(answer_type)
        NOT VALID;
    END IF;
END
$$;


-- Validate every pre-existing row. If any legacy data violates the stronger
-- contract, this migration stops here instead of silently accepting it.
ALTER TABLE problem.problem_templates
    VALIDATE CONSTRAINT problem_templates_ready_requires_executable;

ALTER TABLE problem.problem_templates
    VALIDATE CONSTRAINT problem_templates_positive_difficulty;

ALTER TABLE problem.problem_templates
    VALIDATE CONSTRAINT problem_templates_generation_strategy_check;

ALTER TABLE problem.problem_templates
    VALIDATE CONSTRAINT problem_templates_generation_rule_status_check;

ALTER TABLE problem.problem_templates
    VALIDATE CONSTRAINT problem_templates_nonempty_identifiers;

ALTER TABLE problem.problem_templates
    VALIDATE CONSTRAINT problem_templates_content_hash_format;

ALTER TABLE problem.problem_templates
    VALIDATE CONSTRAINT problem_templates_payload_relational_consistency;

ALTER TABLE problem.problem_templates
    VALIDATE CONSTRAINT problem_templates_answer_type_fk;
