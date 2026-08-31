from __future__ import annotations

from typing import Any

from psycopg.types.json import Jsonb


def find_existing_template(
    conn,
    template_id: str,
    template_version: str,
):
    with conn.cursor() as cur:

        cur.execute(
            """
            SELECT
                content_hash
            FROM problem.problem_templates
            WHERE
                template_id = %s
                AND template_version = %s
            """,
            (
                template_id,
                template_version,
            ),
        )

        return cur.fetchone()

def insert_template(
    conn,
    record: dict[str, Any],
):
    with conn.cursor() as cur:

        cur.execute(
            """
            INSERT INTO problem.problem_templates (
                template_id,
                template_version,
                schema_version,

                status,
                executable,

                generation_rule_id,
                generation_rule_version,
                generation_rule_status,

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
                %(template_version)s,
                %(schema_version)s,

                %(status)s,
                %(executable)s,

                %(generation_rule_id)s,
                %(generation_rule_version)s,
                %(generation_rule_status)s,

                %(subject_id)s,
                %(unit_id)s,

                %(problem_type)s,
                %(answer_type)s,

                %(difficulty_base)s,
                %(difficulty_min)s,
                %(difficulty_max)s,

                %(generation_strategy)s,
                %(language)s,

                %(source_path)s,
                %(content_hash)s,
                %(payload)s
            )
            """,
            {
                **record,
                "payload": Jsonb(
                    record["payload"]
                ),
            },
        )

def insert_template_concept(
    conn,
    template_id: str,
    template_version: str,
    concept_id: str,
):
    with conn.cursor() as cur:

        cur.execute(
            """
            INSERT INTO problem.template_concepts (
                template_id,
                template_version,
                concept_id
            )
            VALUES (%s, %s, %s)
            """,
            (
                template_id,
                template_version,
                concept_id,
            ),
        )

def insert_import_audit(
    conn,
    audit_record: dict[str, Any],
):
    with conn.cursor() as cur:

        cur.execute(
            """
            INSERT INTO problem.template_import_audit (
                template_id,
                template_version,
                selected_path,
                rejected_path,
                action,
                reason
            )
            VALUES (
                %(template_id)s,
                %(template_version)s,
                %(selected_path)s,
                %(rejected_path)s,
                %(action)s,
                %(reason)s
            )
            """,
            audit_record,
        )