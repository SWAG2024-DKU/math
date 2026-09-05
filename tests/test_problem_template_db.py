from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pytest
from psycopg.errors import CheckViolation, ForeignKeyViolation, UniqueViolation
from psycopg.types.json import Jsonb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_PROBLEMS_DIR = PROJECT_ROOT / "scripts" / "problems"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SCRIPTS_PROBLEMS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_PROBLEMS_DIR))

from app.db.connection import get_connection
import verify_problem_template_db as verifier


@pytest.fixture
def db_conn():
    """
    테스트 중 생성한 데이터가 실제 DB에 남지 않도록 마지막에 rollback한다.
    실패를 기대하는 SQL은 nested transaction(savepoint)으로 감싼다.
    """
    conn = get_connection()

    try:
        yield conn
    finally:
        conn.rollback()
        conn.close()


def assert_required_tables(conn) -> None:
    for table_name in (
        "problem.problem_templates",
        "problem.template_concepts",
        "problem.template_import_audit",
        "kb.concepts",
    ):
        row = conn.execute(
            "SELECT to_regclass(%s) AS table_name",
            (table_name,),
        ).fetchone()
        assert row["table_name"] is not None, f"missing table: {table_name}"


def insert_test_template(
    conn,
    *,
    template_id: str,
    status: str = "draft",
    executable: bool = False,
    difficulty_min: int = 1,
    difficulty_base: int = 1,
    difficulty_max: int = 2,
) -> None:
    payload = {
        "template_id": template_id,
        "template_version": "1.0.0",
        "schema_version": "1.0.0",
        "status": status,
        "taxonomy": {
            "subject_id": "test_subject",
            "unit_id": "test_unit",
            "concept_ids": [],
        },
        "classification": {
            "problem_type": "test_problem",
            "answer_type": "scalar",
        },
    }

    conn.execute(
        """
        INSERT INTO problem.problem_templates (
            template_id,
            template_version,
            schema_version,
            status,
            executable,
            subject_id,
            unit_id,
            problem_type,
            answer_type,
            difficulty_base,
            difficulty_min,
            difficulty_max,
            generation_strategy,
            language,
            source_path,
            content_hash,
            payload
        )
        VALUES (
            %(template_id)s,
            '1.0.0',
            '1.0.0',
            %(status)s,
            %(executable)s,
            'test_subject',
            'test_unit',
            'test_problem',
            'scalar',
            %(difficulty_base)s,
            %(difficulty_min)s,
            %(difficulty_max)s,
            'forward_generation',
            'ko-KR',
            'tests/generated_test_template.json',
            %(content_hash)s,
            %(payload)s
        )
        """,
        {
            "template_id": template_id,
            "status": status,
            "executable": executable,
            "difficulty_base": difficulty_base,
            "difficulty_min": difficulty_min,
            "difficulty_max": difficulty_max,
            "content_hash": verifier.canonical_hash(payload),
            "payload": Jsonb(payload),
        },
    )


def test_source_template_counts_are_reproducible():
    result = verifier.scan_source_templates()

    assert result.json_file_count == verifier.EXPECTED_JSON_FILES
    assert result.template_file_count == verifier.EXPECTED_TEMPLATE_FILES
    assert result.duplicate_group_count == verifier.EXPECTED_DUPLICATE_GROUPS
    assert result.unique_template_count == verifier.EXPECTED_UNIQUE_TEMPLATES
    assert result.ready_count == verifier.EXPECTED_READY
    assert result.draft_count == verifier.EXPECTED_DRAFT


def test_source_duplicate_resolution_has_no_ties():
    # scan_source_templates() 내부에서 동률 충돌이 있으면 VerificationError가 발생한다.
    result = verifier.scan_source_templates()
    assert len(result.winners) == verifier.EXPECTED_UNIQUE_TEMPLATES


def test_problem_template_db_counts(db_conn):
    assert_required_tables(db_conn)

    row = db_conn.execute(
        "SELECT COUNT(*) AS count FROM problem.problem_templates"
    ).fetchone()
    assert row["count"] == verifier.EXPECTED_UNIQUE_TEMPLATES

    rows = db_conn.execute(
        """
        SELECT status, COUNT(*) AS count
        FROM problem.problem_templates
        GROUP BY status
        """
    ).fetchall()
    counts = {row["status"]: row["count"] for row in rows}

    assert counts.get("ready", 0) == verifier.EXPECTED_READY
    assert counts.get("draft", 0) == verifier.EXPECTED_DRAFT


def test_all_ready_templates_are_executable(db_conn):
    assert_required_tables(db_conn)

    row = db_conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM problem.problem_templates
        WHERE status = 'ready'
          AND executable = FALSE
        """
    ).fetchone()

    assert row["count"] == 0


def test_no_duplicate_template_keys(db_conn):
    assert_required_tables(db_conn)

    row = db_conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM (
            SELECT template_id, template_version
            FROM problem.problem_templates
            GROUP BY template_id, template_version
            HAVING COUNT(*) > 1
        ) AS duplicated
        """
    ).fetchone()

    assert row["count"] == 0


def test_no_dangling_relationships(db_conn):
    assert_required_tables(db_conn)

    dangling_concepts = db_conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM problem.template_concepts tc
        LEFT JOIN kb.concepts c
          ON tc.concept_id = c.concept_id
        WHERE c.concept_id IS NULL
        """
    ).fetchone()["count"]

    dangling_templates = db_conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM problem.template_concepts tc
        LEFT JOIN problem.problem_templates pt
          ON tc.template_id = pt.template_id
         AND tc.template_version = pt.template_version
        WHERE pt.template_id IS NULL
        """
    ).fetchone()["count"]

    assert dangling_concepts == 0
    assert dangling_templates == 0


def test_template_concept_links_match_payload(db_conn):
    assert_required_tables(db_conn)

    row = db_conn.execute(
        """
        WITH payload_links AS (
            SELECT
                pt.template_id,
                pt.template_version,
                jsonb_array_elements_text(
                    pt.payload #> '{taxonomy,concept_ids}'
                ) AS concept_id
            FROM problem.problem_templates pt
        ),
        db_links AS (
            SELECT
                template_id,
                template_version,
                concept_id
            FROM problem.template_concepts
        ),
        differences AS (
            (SELECT * FROM payload_links EXCEPT SELECT * FROM db_links)
            UNION ALL
            (SELECT * FROM db_links EXCEPT SELECT * FROM payload_links)
        )
        SELECT COUNT(*) AS count
        FROM differences
        """
    ).fetchone()

    assert row["count"] == 0


def test_relational_columns_match_payload(db_conn):
    assert_required_tables(db_conn)

    row = db_conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM problem.problem_templates
        WHERE subject_id
                IS DISTINCT FROM payload #>> '{taxonomy,subject_id}'
           OR unit_id
                IS DISTINCT FROM payload #>> '{taxonomy,unit_id}'
           OR problem_type
                IS DISTINCT FROM payload #>> '{classification,problem_type}'
           OR answer_type
                IS DISTINCT FROM payload #>> '{classification,answer_type}'
           OR status
                IS DISTINCT FROM payload ->> 'status'
           OR template_id
                IS DISTINCT FROM payload ->> 'template_id'
           OR template_version
                IS DISTINCT FROM payload ->> 'template_version'
        """
    ).fetchone()

    assert row["count"] == 0


def test_content_hash_matches_payload(db_conn):
    assert_required_tables(db_conn)

    mismatch_count, samples = verifier.count_hash_mismatches(db_conn)

    assert mismatch_count == 0, samples


def test_source_and_db_template_keys_match(db_conn):
    assert_required_tables(db_conn)

    source_result = verifier.scan_source_templates()
    mismatch_count, samples = verifier.count_key_set_mismatches(
        db_conn,
        source_result,
    )

    assert mismatch_count == 0, samples


def test_duplicate_audit_has_56_distinct_resolutions(db_conn):
    assert_required_tables(db_conn)

    row = db_conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM (
            SELECT DISTINCT
                template_id,
                template_version,
                selected_path,
                rejected_path,
                action
            FROM problem.template_import_audit
            WHERE action = 'duplicate_resolved'
        ) AS distinct_audits
        """
    ).fetchone()

    assert row["count"] == verifier.EXPECTED_DUPLICATE_GROUPS


def test_invalid_status_is_rejected(db_conn):
    assert_required_tables(db_conn)

    template_id = "test.invalid.status." + uuid.uuid4().hex

    with pytest.raises(CheckViolation):
        with db_conn.transaction():
            insert_test_template(
                db_conn,
                template_id=template_id,
                status="invalid_status",
            )


def test_invalid_difficulty_is_rejected(db_conn):
    assert_required_tables(db_conn)

    template_id = "test.invalid.difficulty." + uuid.uuid4().hex

    with pytest.raises(CheckViolation):
        with db_conn.transaction():
            insert_test_template(
                db_conn,
                template_id=template_id,
                difficulty_min=5,
                difficulty_base=2,
                difficulty_max=3,
            )


def test_unknown_concept_is_rejected(db_conn):
    assert_required_tables(db_conn)

    template_id = "test.unknown.concept." + uuid.uuid4().hex
    insert_test_template(db_conn, template_id=template_id)

    with pytest.raises(ForeignKeyViolation):
        with db_conn.transaction():
            db_conn.execute(
                """
                INSERT INTO problem.template_concepts (
                    template_id,
                    template_version,
                    concept_id
                )
                VALUES (%s, '1.0.0', %s)
                """,
                (
                    template_id,
                    "concept_that_does_not_exist_" + uuid.uuid4().hex,
                ),
            )


def test_duplicate_primary_key_is_rejected(db_conn):
    assert_required_tables(db_conn)

    template_id = "test.duplicate.pk." + uuid.uuid4().hex
    insert_test_template(db_conn, template_id=template_id)

    with pytest.raises(UniqueViolation):
        with db_conn.transaction():
            insert_test_template(
                db_conn,
                template_id=template_id,
            )