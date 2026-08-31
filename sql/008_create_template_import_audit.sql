CREATE TABLE IF NOT EXISTS problem.template_import_audit (
    audit_id BIGSERIAL PRIMARY KEY,

    template_id VARCHAR(500),
    template_version VARCHAR(30),

    selected_path TEXT,
    rejected_path TEXT,

    action VARCHAR(50) NOT NULL,

    reason TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT template_import_audit_action_check
        CHECK (
            action IN (
                'inserted',
                'skipped',
                'duplicate_resolved'
            )
        )
);
