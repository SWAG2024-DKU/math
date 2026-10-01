-- Preview pending 적재 및 confirmed 조회를 위한 PostgreSQL 마이그레이션 초안.
-- TODO: 실제 DB 스키마·권한과 비교하고 검토한 후에만 실행한다.
-- Template DB는 기존 sql/005_create_problem_schema.sql 및 006~008을 사용한다.

CREATE SCHEMA IF NOT EXISTS problem;

CREATE TABLE IF NOT EXISTS problem.problem_instances (
    instance_id UUID PRIMARY KEY,                 -- TODO: Python 적재 코드에서 UUID를 생성한다.
    template_id VARCHAR(500) NOT NULL,
    template_version VARCHAR(30) NOT NULL,
    template_content_hash CHAR(64) NOT NULL,
    subject_id VARCHAR(100) NOT NULL CHECK (subject_id = 'linear_algebra'),
    problem_type VARCHAR(200) NOT NULL,
    seed BIGINT NOT NULL,
    statement TEXT NOT NULL CHECK (length(trim(statement)) > 0),
    expected_answer JSONB NOT NULL,
    payload JSONB NOT NULL CHECK (jsonb_typeof(payload) = 'object'),
    problem_hash CHAR(64) NOT NULL,
    source_path TEXT NOT NULL,
    source_sha256 CHAR(64) NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'rejected', 'confirmed')),
    human_reviewer_id TEXT,
    human_review_decision TEXT CHECK (human_review_decision IN ('approved', 'rejected')),
    human_reviewed_at TIMESTAMPTZ,
    confirmed_at TIMESTAMPTZ,
    confirmed_validator_version TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (template_id, template_version)
        REFERENCES problem.problem_templates(template_id, template_version)
        ON DELETE RESTRICT,
    UNIQUE (template_id, template_version, seed),
    UNIQUE (template_id, template_version, problem_hash),
    CHECK (status <> 'confirmed' OR
        (human_reviewer_id IS NOT NULL AND human_review_decision IS NOT DISTINCT FROM 'approved'
         AND human_reviewed_at IS NOT NULL
         AND confirmed_at IS NOT NULL AND confirmed_validator_version IS NOT NULL))
);

CREATE INDEX IF NOT EXISTS idx_problem_instances_pending
    ON problem.problem_instances (subject_id, problem_type)
    WHERE status = 'pending';

CREATE TABLE IF NOT EXISTS problem.instance_validation_runs (
    run_id UUID PRIMARY KEY,                      -- TODO: Python 검증 이력 코드에서 UUID를 생성한다.
    instance_id UUID NOT NULL REFERENCES problem.problem_instances(instance_id)
        ON DELETE RESTRICT,
    validator_version TEXT NOT NULL,
    source_sha256 CHAR(64) NOT NULL,
    template_content_hash CHAR(64) NOT NULL,
    result TEXT NOT NULL CHECK (result IN ('passed', 'failed', 'unsupported')),
    report JSONB NOT NULL CHECK (jsonb_typeof(report) = 'object'),
    checked_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_instance_validation_latest
    ON problem.instance_validation_runs (instance_id, checked_at DESC, run_id DESC);

-- Confirmed_Instance는 같은 원본 행에 대한 VIEW이다.
-- 별도 복제 테이블의 내용이 원본과 어긋나는 상황을 막는다.
-- 공개용 VIEW이므로 expected_answer와 payload(JSONB 안의 정답 포함)는 제외한다.
CREATE OR REPLACE VIEW problem.confirmed_instances AS
SELECT pi.instance_id, pi.template_id, pi.template_version,
       pi.subject_id, pi.problem_type, pi.statement, pi.confirmed_at
FROM problem.problem_instances AS pi
JOIN problem.problem_templates AS pt
  ON pt.template_id = pi.template_id
 AND pt.template_version = pi.template_version
JOIN LATERAL (
    SELECT vr.validator_version, vr.source_sha256,
           vr.template_content_hash, vr.result
    FROM problem.instance_validation_runs AS vr
    WHERE vr.instance_id = pi.instance_id
    ORDER BY vr.checked_at DESC, vr.run_id DESC
    LIMIT 1
) AS latest ON true
WHERE pi.status = 'confirmed'
  AND pi.subject_id = 'linear_algebra'
  AND pi.human_reviewer_id IS NOT NULL
  AND pi.human_review_decision = 'approved'
  AND pi.human_reviewed_at IS NOT NULL
  AND pi.confirmed_validator_version = latest.validator_version
  AND latest.result = 'passed'
  AND latest.source_sha256 = pi.source_sha256
  AND latest.template_content_hash = pi.template_content_hash
  AND pi.template_content_hash = pt.content_hash
  AND pt.status IN ('ready', 'active')
  AND pt.executable = TRUE;

-- TODO: 서비스 API 계정은 confirmed_instances만 조회할 수 있도록 권한을 제한한다.
--       정답이 있는 problem_instances 원본 테이블을 일반 문제 조회에 노출하지 않는다.
-- TODO: instance_db_todo.py에 pending -> confirmed 원자적 승격을 구현한다.
