from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.connection import get_connection

COUNT_QUERIES = {
    "ready_non_executable": """
        SELECT COUNT(*) AS n
        FROM problem.problem_templates
        WHERE status = 'ready'
          AND executable = FALSE
    """,
    "non_positive_difficulty": """
        SELECT COUNT(*) AS n
        FROM problem.problem_templates
        WHERE NOT (
            difficulty_min BETWEEN 1 AND 2147483647
            AND difficulty_base BETWEEN 1 AND 2147483647
            AND difficulty_max BETWEEN 1 AND 2147483647
        )
    """,
    "invalid_generation_strategy": """
        SELECT COUNT(*) AS n
        FROM problem.problem_templates
        WHERE generation_strategy NOT IN (
            'forward_generation',
            'reverse_generation'
        )
    """,
    "invalid_generation_rule_status": """
        SELECT COUNT(*) AS n
        FROM problem.problem_templates
        WHERE generation_rule_status IS NOT NULL
          AND generation_rule_status NOT IN (
              'draft_auto',
              'reviewed',
              'curated'
          )
    """,
    "empty_identifier": """
        SELECT COUNT(*) AS n
        FROM problem.problem_templates
        WHERE BTRIM(template_id) = ''
           OR BTRIM(template_version) = ''
           OR BTRIM(schema_version) = ''
           OR BTRIM(subject_id) = ''
           OR BTRIM(unit_id) = ''
           OR BTRIM(problem_type) = ''
           OR BTRIM(answer_type) = ''
           OR BTRIM(generation_strategy) = ''
           OR BTRIM(language) = ''
           OR BTRIM(source_path) = ''
    """,
    "invalid_content_hash": """
        SELECT COUNT(*) AS n
        FROM problem.problem_templates
        WHERE content_hash !~ '^[0-9a-f]{64}$'
    """,
    "payload_relational_mismatch": """
        SELECT COUNT(*) AS n
        FROM problem.problem_templates
        WHERE NOT (
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
    """,
}


def main() -> int:
    conn = get_connection()
    failures: dict[str, int] = {}

    try:
        print("=" * 68)
        print("ProblemTemplate DB hardening preflight")
        print("=" * 68)

        for name, sql in COUNT_QUERIES.items():
            n = conn.execute(sql).fetchone()["n"]
            failures[name] = n
            marker = "OK" if n == 0 else "FAIL"
            print(f"[{marker:4}] {name}: {n}")

        print()
        print("Current answer_type vocabulary:")
        rows = conn.execute(
            """
            SELECT answer_type, COUNT(*) AS n
            FROM problem.problem_templates
            GROUP BY answer_type
            ORDER BY answer_type
            """
        ).fetchall()
        for row in rows:
            print(f"  - {row['answer_type']}: {row['n']}")

        bad = {name: n for name, n in failures.items() if n != 0}
        print()
        if bad:
            print("PRECHECK FAILED - 010 migration을 아직 적용하지 마세요.")
            for name, n in bad.items():
                print(f"  {name}: {n}")
            return 1

        print("PRECHECK PASSED - 010 migration을 적용해도 됩니다.")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
