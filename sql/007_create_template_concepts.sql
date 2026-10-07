CREATE TABLE IF NOT EXISTS problem.template_concepts (
    template_id VARCHAR(500) NOT NULL,
    template_version VARCHAR(30) NOT NULL,

    concept_id VARCHAR(200) NOT NULL,

    PRIMARY KEY (
        template_id,
        template_version,
        concept_id
    ),

    FOREIGN KEY (
        template_id,
        template_version
    )
    REFERENCES problem.problem_templates (
        template_id,
        template_version
    )
    ON DELETE CASCADE,

    FOREIGN KEY (
        concept_id
    )
    REFERENCES kb.concepts (
        concept_id
    )
    ON DELETE RESTRICT
);


-- concept → template 역방향 조회용.
-- PK가 (template_id, template_version, concept_id)라 concept_id가 선두가 아니어서
-- 이 인덱스가 없으면 kb.concepts 삭제 시 ON DELETE RESTRICT 검사와
-- "이 개념을 쓰는 템플릿" 조회가 전수 스캔이 된다.
CREATE INDEX IF NOT EXISTS idx_template_concepts_concept_id
ON problem.template_concepts (concept_id);
