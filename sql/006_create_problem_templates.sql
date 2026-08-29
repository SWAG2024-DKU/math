CREATE TABLE IF NOT EXISTS problem.problem_templates (
    template_id VARCHAR(500) NOT NULL,
    template_version VARCHAR(30) NOT NULL,

    schema_version VARCHAR(30) NOT NULL,

    status VARCHAR(30) NOT NULL,
    executable BOOLEAN NOT NULL DEFAULT FALSE,

    generation_rule_id VARCHAR(500),
    generation_rule_version VARCHAR(30),
    generation_rule_status VARCHAR(30),

    subject_id VARCHAR(100) NOT NULL,
    unit_id VARCHAR(200) NOT NULL,

    problem_type VARCHAR(200) NOT NULL,
    answer_type VARCHAR(100) NOT NULL,

    difficulty_base INTEGER NOT NULL,
    difficulty_min INTEGER NOT NULL,
    difficulty_max INTEGER NOT NULL,

    generation_strategy VARCHAR(100) NOT NULL,
    language VARCHAR(30) NOT NULL DEFAULT 'ko-KR',

    source_path TEXT NOT NULL,

    content_hash CHAR(64) NOT NULL,

    payload JSONB NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (
        template_id,
        template_version
    ),

    CONSTRAINT problem_templates_status_check
        CHECK (
            status IN (
                'draft',
                'ready',
                'deprecated'
            )
        ),

    CONSTRAINT problem_templates_difficulty_check
        CHECK (
            difficulty_min <= difficulty_base
            AND difficulty_base <= difficulty_max
        ),

    CONSTRAINT problem_templates_payload_check
        CHECK (
            jsonb_typeof(payload) = 'object'
        )
);


CREATE INDEX IF NOT EXISTS idx_problem_templates_subject
ON problem.problem_templates(subject_id);

CREATE INDEX IF NOT EXISTS idx_problem_templates_unit
ON problem.problem_templates(unit_id);

CREATE INDEX IF NOT EXISTS idx_problem_templates_problem_type
ON problem.problem_templates(problem_type);

CREATE INDEX IF NOT EXISTS idx_problem_templates_answer_type
ON problem.problem_templates(answer_type);

CREATE INDEX IF NOT EXISTS idx_problem_templates_status
ON problem.problem_templates(status);

CREATE INDEX IF NOT EXISTS idx_problem_templates_ready
ON problem.problem_templates(
    subject_id,
    unit_id,
    problem_type
)
WHERE
    status = 'ready'
    AND executable = TRUE;
