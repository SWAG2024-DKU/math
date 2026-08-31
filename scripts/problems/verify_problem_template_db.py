from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.connection import get_connection


TEMPLATE_DIR = PROJECT_ROOT / "data" / "problem_templates"

EXPECTED_JSON_FILES = 3389
EXPECTED_TEMPLATE_FILES = 3383
EXPECTED_DUPLICATE_GROUPS = 56
EXPECTED_UNIQUE_TEMPLATES = 3327
EXPECTED_READY = 56
EXPECTED_DRAFT = 3271
EXPECTED_EXECUTABLE_READY = 56

STATUS_RANK = {
    "deprecated": 0,
    "draft": 1,
    "ready": 2,
}

RULE_STATUS_RANK = {
    None: 0,
    "draft_auto": 1,
    "reviewed": 2,
    "curated": 3,
}


@dataclass(frozen=True)
class SourceCandidate:
    path: Path
    data: dict[str, Any]


@dataclass
class SourceScanResult:
    json_file_count: int
    template_file_count: int
    duplicate_group_count: int
    unique_template_count: int
    ready_count: int
    draft_count: int
    winners: dict[tuple[str, str], SourceCandidate]


class VerificationError(RuntimeError):
    pass


def canonical_hash(payload: dict[str, Any]) -> str:
    """DB payload와 content_hash를 비교할 때 사용하는 canonical SHA-256."""
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def template_rank(data: dict[str, Any]) -> tuple[int, int, int]:
    """중복 Template winner 선정을 위한 독립 검증용 우선순위."""
    return (
        STATUS_RANK.get(data.get("status"), -1),
        int(bool(data.get("executable", False))),
        RULE_STATUS_RANK.get(data.get("generation_rule_status"), 0),
    )


def select_winner(candidates: list[SourceCandidate]) -> SourceCandidate:
    if not candidates:
        raise VerificationError("빈 candidate 목록입니다.")

    ordered = sorted(
        candidates,
        key=lambda item: template_rank(item.data),
        reverse=True,
    )

    if len(ordered) == 1:
        return ordered[0]

    first_rank = template_rank(ordered[0].data)
    second_rank = template_rank(ordered[1].data)

    if first_rank == second_rank:
        paths = ", ".join(str(item.path) for item in ordered[:2])
        raise VerificationError(
            "자동으로 결정할 수 없는 동일 우선순위 template 충돌이 있습니다: "
            + paths
        )

    return ordered[0]


def scan_source_templates() -> SourceScanResult:
    """
    B Importer의 함수를 재사용하지 않고 raw 파일을 독립적으로 스캔한다.
    C 검증이 importer와 같은 버그를 공유하지 않도록 하기 위함이다.
    """
    files = sorted(TEMPLATE_DIR.rglob("*.json"))

    groups: dict[tuple[str, str], list[SourceCandidate]] = defaultdict(list)
    template_file_count = 0

    for path in files:
        with path.open("r", encoding="utf-8") as file:
            raw = json.load(file)

        if raw.get("object_type") != "problem_template":
            continue

        template_file_count += 1

        template_id = raw.get("template_id")
        template_version = raw.get("template_version", "1.0.0")

        if not template_id:
            raise VerificationError(f"template_id가 없는 파일: {path}")

        groups[(template_id, template_version)].append(
            SourceCandidate(path=path, data=raw)
        )

    duplicate_group_count = sum(
        1 for candidates in groups.values() if len(candidates) > 1
    )

    winners: dict[tuple[str, str], SourceCandidate] = {}
    for key, candidates in groups.items():
        winners[key] = select_winner(candidates)

    statuses = Counter(
        candidate.data.get("status")
        for candidate in winners.values()
    )

    return SourceScanResult(
        json_file_count=len(files),
        template_file_count=template_file_count,
        duplicate_group_count=duplicate_group_count,
        unique_template_count=len(winners),
        ready_count=statuses.get("ready", 0),
        draft_count=statuses.get("draft", 0),
        winners=winners,
    )


def require_equal(name: str, actual: int, expected: int) -> None:
    if actual != expected:
        raise VerificationError(
            f"{name} 불일치: expected={expected}, actual={actual}"
        )
    print(f"[OK] {name}: {actual}")


def verify_source() -> SourceScanResult:
    print("[1/2] Source files verification")

    result = scan_source_templates()

    require_equal("JSON file count", result.json_file_count, EXPECTED_JSON_FILES)
    require_equal(
        "ProblemTemplate file count",
        result.template_file_count,
        EXPECTED_TEMPLATE_FILES,
    )
    require_equal(
        "duplicate group count",
        result.duplicate_group_count,
        EXPECTED_DUPLICATE_GROUPS,
    )
    require_equal(
        "unique template count",
        result.unique_template_count,
        EXPECTED_UNIQUE_TEMPLATES,
    )
    require_equal("ready source count", result.ready_count, EXPECTED_READY)
    require_equal("draft source count", result.draft_count, EXPECTED_DRAFT)

    print()
    return result


def require_table(conn, table_name: str) -> None:
    row = conn.execute(
        "SELECT to_regclass(%s) AS table_name",
        (table_name,),
    ).fetchone()

    if row["table_name"] is None:
        raise VerificationError(f"필수 DB table이 없습니다: {table_name}")


def scalar_count(conn, sql: str, params: tuple[Any, ...] = ()) -> int:
    row = conn.execute(sql, params).fetchone()
    return int(row["count"])


def get_status_counts(conn) -> dict[str, int]:
    rows = conn.execute(
        """
        SELECT status, COUNT(*) AS count
        FROM problem.problem_templates
        GROUP BY status
        """
    ).fetchall()

    return {row["status"]: int(row["count"]) for row in rows}


def count_hash_mismatches(conn) -> tuple[int, list[str]]:
    rows = conn.execute(
        """
        SELECT
            template_id,
            template_version,
            content_hash,
            payload
        FROM problem.problem_templates
        """
    ).fetchall()

    mismatches: list[str] = []

    for row in rows:
        payload = row["payload"]
        calculated = canonical_hash(payload)

        if calculated != row["content_hash"]:
            mismatches.append(
                f"{row['template_id']}@{row['template_version']}"
            )

    return len(mismatches), mismatches[:10]


def count_key_set_mismatches(
    conn,
    source_result: SourceScanResult,
) -> tuple[int, list[str]]:
    rows = conn.execute(
        """
        SELECT template_id, template_version
        FROM problem.problem_templates
        """
    ).fetchall()

    db_keys = {
        (row["template_id"], row["template_version"])
        for row in rows
    }
    source_keys = set(source_result.winners)

    only_source = sorted(source_keys - db_keys)
    only_db = sorted(db_keys - source_keys)

    samples = [
        f"source_only={template_id}@{version}"
        for template_id, version in only_source[:5]
    ]
    samples.extend(
        f"db_only={template_id}@{version}"
        for template_id, version in only_db[:5]
    )

    return len(only_source) + len(only_db), samples


def count_source_path_mismatches(
    conn,
    source_result: SourceScanResult,
) -> tuple[int, list[str]]:
    rows = conn.execute(
        """
        SELECT
            template_id,
            template_version,
            source_path
        FROM problem.problem_templates
        """
    ).fetchall()

    mismatches: list[str] = []

    for row in rows:
        key = (row["template_id"], row["template_version"])
        winner = source_result.winners.get(key)

        if winner is None:
            continue

        expected = str(winner.path.relative_to(PROJECT_ROOT)).replace("\\", "/")
        actual = str(row["source_path"]).replace("\\", "/")

        if expected != actual:
            mismatches.append(
                f"{row['template_id']}@{row['template_version']}: "
                f"expected={expected}, actual={actual}"
            )

    return len(mismatches), mismatches[:10]


def verify_db(source_result: SourceScanResult) -> None:
    print("[2/2] PostgreSQL verification")

    conn = get_connection()

    try:
        required_tables = [
            "problem.problem_templates",
            "problem.template_concepts",
            "problem.template_import_audit",
            "kb.concepts",
        ]
        for table_name in required_tables:
            require_table(conn, table_name)
        print("[OK] required tables exist")

        template_count = scalar_count(
            conn,
            "SELECT COUNT(*) AS count FROM problem.problem_templates",
        )
        require_equal(
            "DB template count",
            template_count,
            EXPECTED_UNIQUE_TEMPLATES,
        )

        status_counts = get_status_counts(conn)
        require_equal(
            "DB ready count",
            status_counts.get("ready", 0),
            EXPECTED_READY,
        )
        require_equal(
            "DB draft count",
            status_counts.get("draft", 0),
            EXPECTED_DRAFT,
        )

        executable_ready = scalar_count(
            conn,
            """
            SELECT COUNT(*) AS count
            FROM problem.problem_templates
            WHERE status = 'ready'
              AND executable = TRUE
            """,
        )
        require_equal(
            "executable ready count",
            executable_ready,
            EXPECTED_EXECUTABLE_READY,
        )

        invalid_ready = scalar_count(
            conn,
            """
            SELECT COUNT(*) AS count
            FROM problem.problem_templates
            WHERE status = 'ready'
              AND executable = FALSE
            """,
        )
        require_equal("ready but non-executable", invalid_ready, 0)

        duplicate_keys = scalar_count(
            conn,
            """
            SELECT COUNT(*) AS count
            FROM (
                SELECT template_id, template_version
                FROM problem.problem_templates
                GROUP BY template_id, template_version
                HAVING COUNT(*) > 1
            ) AS duplicated
            """,
        )
        require_equal("duplicate DB template keys", duplicate_keys, 0)

        dangling_concepts = scalar_count(
            conn,
            """
            SELECT COUNT(*) AS count
            FROM problem.template_concepts tc
            LEFT JOIN kb.concepts c
              ON tc.concept_id = c.concept_id
            WHERE c.concept_id IS NULL
            """,
        )
        require_equal("dangling concept references", dangling_concepts, 0)

        dangling_templates = scalar_count(
            conn,
            """
            SELECT COUNT(*) AS count
            FROM problem.template_concepts tc
            LEFT JOIN problem.problem_templates pt
              ON tc.template_id = pt.template_id
             AND tc.template_version = pt.template_version
            WHERE pt.template_id IS NULL
            """,
        )
        require_equal("dangling template references", dangling_templates, 0)

        invalid_payloads = scalar_count(
            conn,
            """
            SELECT COUNT(*) AS count
            FROM problem.problem_templates
            WHERE jsonb_typeof(payload) IS DISTINCT FROM 'object'
            """,
        )
        require_equal("invalid JSON payloads", invalid_payloads, 0)

        column_payload_mismatches = scalar_count(
            conn,
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
            """,
        )
        require_equal(
            "relational column/payload mismatches",
            column_payload_mismatches,
            0,
        )

        link_mismatches = scalar_count(
            conn,
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
            """,
        )
        require_equal(
            "template_concepts/payload link mismatches",
            link_mismatches,
            0,
        )

        hash_mismatch_count, hash_samples = count_hash_mismatches(conn)
        if hash_mismatch_count:
            raise VerificationError(
                "content_hash mismatch가 있습니다: "
                + "; ".join(hash_samples)
            )
        print("[OK] content_hash mismatches: 0")

        key_mismatch_count, key_samples = count_key_set_mismatches(
            conn,
            source_result,
        )
        if key_mismatch_count:
            raise VerificationError(
                "source/DB template key mismatch가 있습니다: "
                + "; ".join(key_samples)
            )
        print("[OK] source/DB template key mismatches: 0")

        source_path_mismatch_count, path_samples = count_source_path_mismatches(
            conn,
            source_result,
        )
        if source_path_mismatch_count:
            raise VerificationError(
                "source_path mismatch가 있습니다: "
                + "; ".join(path_samples)
            )
        print("[OK] source_path mismatches: 0")

        distinct_duplicate_audits = scalar_count(
            conn,
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
            """,
        )
        require_equal(
            "distinct duplicate audit count",
            distinct_duplicate_audits,
            EXPECTED_DUPLICATE_GROUPS,
        )

        total_duplicate_audits = scalar_count(
            conn,
            """
            SELECT COUNT(*) AS count
            FROM problem.template_import_audit
            WHERE action = 'duplicate_resolved'
            """,
        )
        if total_duplicate_audits > distinct_duplicate_audits:
            print(
                "[WARN] duplicate audit rows are repeated across import runs: "
                f"total={total_duplicate_audits}, "
                f"distinct={distinct_duplicate_audits}"
            )
        else:
            print(
                f"[OK] total duplicate audit count: "
                f"{total_duplicate_audits}"
            )

        print()
    finally:
        conn.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ProblemTemplate source/DB integrity verifier"
    )
    parser.add_argument(
        "--source-only",
        action="store_true",
        help="DB 연결 없이 data/problem_templates 파일만 검사합니다.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    print("=" * 64)
    print("ProblemTemplate DB Verification")
    print("=" * 64)
    print()

    try:
        source_result = verify_source()

        if not args.source_only:
            verify_db(source_result)

    except (VerificationError, OSError, json.JSONDecodeError) as exc:
        print()
        print(f"[FAIL] {exc}")
        return 1
    except Exception as exc:
        print()
        print(
            "[FAIL] 예상하지 못한 오류가 발생했습니다: "
            f"{type(exc).__name__}: {exc}"
        )
        return 1

    print("=" * 64)
    if args.source_only:
        print("ProblemTemplate SOURCE verification PASSED")
    else:
        print("ProblemTemplate DB verification PASSED")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
