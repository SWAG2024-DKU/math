/*
TODO: 이 파일은 Preview의 pending 적재와 confirmed 조회를 위한 마이그레이션 초안이다.
TODO 1. 실제 PostgreSQL의 problem 스키마와 애플리케이션 계정 권한을 확인한다.
TODO 2. 기존 sql/005_create_problem_schema.sql 및 006~008 마이그레이션이
        적용되어 있는지 확인한다. Template 테이블은 여기서 다시 만들지 않는다.
TODO 3. 기존에 같은 이름의 테이블이나 VIEW가 있다면 구조를 대조한다.
        CREATE TABLE IF NOT EXISTS는 기존 테이블의 구조를 갱신하지 않는다.
*/

CREATE SCHEMA IF NOT EXISTS problem;

/*
TODO: Python의 insert_pending_instances()를 구현할 때 이 테이블에만 먼저 적재한다.
TODO 1. instance_id는 적재 코드에서 UUID를 만들어 전달한다.
TODO 2. Template ID·버전이 실제 DB에 존재하고 template_content_hash가
        problem.problem_templates.content_hash와 일치하는지 적재 전에 확인한다.
TODO 3. 같은 Template·seed가 재등장하면 payload와 해시까지 비교한다.
        내용이 다르면 덮어쓰지 않고 오류로 처리한다.
TODO 4. Preview 원본의 validation_trace만으로 confirmed로 승격하지 않는다.
*/
CREATE TABLE IF NOT EXISTS problem.problem_instances (
    instance_id UUID PRIMARY KEY,
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

/*
TODO: record_independent_validation()에서 독립 재검증 실행마다 이력을 남긴다.
TODO 1. run_id는 검증 이력 저장 코드에서 UUID를 만들어 전달한다.
TODO 2. passed·failed·unsupported를 모두 기록하고 검증기 버전,
        원본 SHA-256, Template 해시 및 검사 근거를 함께 저장한다.
TODO 3. 새 검증 이력이 생겨도 이 테이블만 수정해서 자동으로 confirmed로
        바꾸지 않는다. 공개 판단에는 가장 최근 이력만 사용한다.
*/
CREATE TABLE IF NOT EXISTS problem.instance_validation_runs (
    run_id UUID PRIMARY KEY,
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

/*
TODO: confirm_instance()에서 검증과 사람 검수를 확인한 뒤 트랜잭션으로 승격한다.
TODO 1. 최신 독립 검증이 passed이고 원본 해시·Template 해시·검증기 버전이
        현재 Instance와 일치하는지 다시 확인한다.
TODO 2. 검수 담당자와 approved 결정을 기록하고 상태를 confirmed로 변경한다.
TODO 3. 서비스 문제 조회는 아래 VIEW를 사용한다. 원본을 복제한 별도 테이블을
        만들지 않으며, 정답이 든 expected_answer와 payload를 반환하지 않는다.
TODO 4. 최신 검증이 실패하거나 Template가 출제 불가능해지면 조회 대상에서 제외한다.
*/
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

/*
TODO: 실제 DB 권한 설정 및 애플리케이션 연결 코드를 완성한다.
TODO 1. 서비스의 일반 문제 조회 계정에 confirmed_instances SELECT만 부여하고,
        정답을 포함한 problem_instances 원본과 instance_validation_runs에 대한
        일반 사용자 접근은 막는다. 채점용 접근은 별도 권한으로 설계한다.
TODO 2. instance_db_todo.py의 pending -> confirmed 승격을 원자적 트랜잭션으로 구현한다.
TODO 3. 별도 테스트 DB에서 신규 적용·재실행·롤백·권한을 확인한 후 적용한다.
*/
