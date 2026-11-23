"""선형대수 Instance 전체 독립 재검증. 기본은 읽기 전용, --write는 검증 이력만 저장한다.

한국어 구현 설명:
1. UUID 키셋 페이지로 pending/rejected/confirmed 모두 순회한다.
2. PostgreSQL 읽기 스냅샷으로 대상 내용을 고정한다.
3. Windows에서도 spawn 자식 프로세스로 건별 제한 시간을 보장한다.
4. 저장 직전 Instance와 Template를 잠그고 검증한 내용이 바뀌지 않았는지 비교한다.
5. 실패/미지원도 이력으로 남긴다. 사람 승인 및 confirmed 승격은 수행하지 않는다.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import math
import multiprocessing as mp
from pathlib import Path
import time
from uuid import UUID, uuid4
from zipfile import ZipFile

from scripts.problems.common.independent_instance_validator import VALIDATOR_VERSION, digest, validate_payload


def failure(message, verdict='failed'):
    return {'validator_version': VALIDATOR_VERSION, 'result': verdict,
            'report': {'checks': [{'name': 'batch_or_storage_validation', 'passed': False, 'message': message}]}}


def _worker(connection, payload):
    try:
        connection.send(validate_payload(payload))
    except BaseException as exc:
        connection.send(failure(f'worker: {type(exc).__name__}: {exc}', 'unsupported'))
    finally:
        connection.close()



def validate_with_timeout(payload, seconds=30, *, worker=_worker):
    """별도 spawn 프로세스에서 검증하고 시간 제한을 적용한다."""

    if (
        isinstance(seconds, bool)
        or not isinstance(seconds, (int, float))
        or not math.isfinite(seconds)
        or seconds <= 0
    ):
        return failure("검증 제한 시간은 양수여야 합니다")

    ctx = mp.get_context("spawn")
    parent_conn, child_conn = ctx.Pipe(duplex=False)
    process = None

    try:
        process = ctx.Process(
            target=worker,
            args=(child_conn, payload),
        )
        process.daemon = True
        process.start()

        # 부모는 수신 쪽만 사용한다.
        child_conn.close()

        # 설정된 시간 동안 결과를 기다린다.
        if not parent_conn.poll(seconds):
            if process.is_alive():
                process.terminate()
                process.join(timeout=1)

                if process.is_alive():
                    process.kill()
                    process.join()

                return failure(
                    f"독립 검증 제한 시간 {seconds}초 초과",
                    "timeout",
                )

            return failure(
                "검증 프로세스가 결과 없이 종료됨",
                "failed",
            )

        try:
            result = parent_conn.recv()
        except (EOFError, OSError) as exc:
            return failure(
                f"검증 결과 수신 실패: {type(exc).__name__}",
                "failed",
            )

        if not isinstance(result, dict):
            return failure("검증 결과 형식 오류", "failed")

        if result.get("result") not in {
            "passed", "failed", "unsupported", "timeout"
        }:
            return failure("알 수 없는 검증 결과", "failed")

        if not isinstance(result.get("report"), dict):
            return failure("검증 보고서 형식 오류", "failed")

        return result

    except (OSError, ValueError, RuntimeError, TypeError) as exc:
        return failure(
            f"검증 프로세스 실행 실패: {type(exc).__name__}: {exc}",
            "failed",
        )

    finally:
        parent_conn.close()
        child_conn.close()

        if process is not None:
            if process.pid is not None:
                if process.is_alive():
                    process.terminate()
                process.join()
                process.close()


def connection():
    from app.db.connection import get_connection
    return get_connection()


def storage_check(row):
    """DB 중복 컬럼과 payload, Template 해시를 비교한다. 원본 파일 해시는 재계산하지 않는다."""
    p = row['payload']
    for field in ('template_id', 'template_version', 'subject_id', 'problem_type', 'seed', 'statement', 'expected_answer'):
        if row[field] != p[field]: raise ValueError('DB/payload 불일치: ' + field)
    if isinstance(p['seed'], bool) or not isinstance(p['seed'], int): raise ValueError('seed 정수 필요')
    if row['template_content_hash'] != digest(p['template_snapshot']): raise ValueError('snapshot 해시 불일치')
    if row['current_template_hash'] != row['template_content_hash']: raise ValueError('현재 Template 해시 불일치')
    if row['problem_hash'] != digest([p['template_id'], p['statement'], p['expected_answer']]): raise ValueError('문제 내용 해시 불일치')
    if len(row['source_sha256']) != 64 or any(c not in '0123456789abcdef' for c in row['source_sha256']): raise ValueError('원본 해시 형식 오류')


SELECT = '''SELECT pi.*, pt.content_hash AS current_template_hash
FROM problem.problem_instances pi LEFT JOIN problem.problem_templates pt
ON pt.template_id=pi.template_id AND pt.template_version=pi.template_version'''


def iterate_rows(conn, batch_size, after_id=None, limit=None):
    """같은 읽기 트랜잭션 안에서 페이지 순회한다. NULL after_id는 처음부터 검사한다."""
    count = 0
    while limit is None or count < limit:
        size = batch_size if limit is None else min(batch_size, limit-count)
        rows = conn.execute(SELECT + ''' WHERE pi.subject_id='linear_algebra'
            AND (%s::uuid IS NULL OR pi.instance_id > %s::uuid)
            ORDER BY pi.instance_id LIMIT %s''', (after_id, after_id, size)).fetchall()
        if not rows: return
        for row in rows:
            yield row
            count += 1; after_id = row['instance_id']


def save_result(conn, row, result):
    """기존 상태와 사람 검수는 변경하지 않고 별도 검증 이력만 원자적으로 추가한다."""
    from psycopg.types.json import Jsonb
    with conn.transaction():
        # Template를 먼저 잠그는 기존 적재/확정 경로의 잠금 순서를 따른다.
        template = conn.execute('''SELECT content_hash FROM problem.problem_templates
            WHERE template_id=%s AND template_version=%s FOR SHARE''',
            (row['template_id'], row['template_version'])).fetchone()
        current = conn.execute('''SELECT * FROM problem.problem_instances
            WHERE instance_id=%s FOR UPDATE''', (row['instance_id'],)).fetchone()
        if current is None: raise ValueError('검증 중 Instance가 삭제됨')
        for key in ('payload','statement','expected_answer','template_id','template_version','seed',
                    'subject_id','problem_type','template_content_hash','source_sha256','problem_hash'):
            if current[key] != row[key]: raise ValueError('검증 중 내용 변경: '+key)
        if (template['content_hash'] if template else None) != row['current_template_hash']:
            raise ValueError('검증 중 Template 변경')
        conn.execute('''INSERT INTO problem.instance_validation_runs
            (run_id,instance_id,validator_version,source_sha256,template_content_hash,result,report,checked_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,clock_timestamp())''',
            (uuid4(),row['instance_id'],VALIDATOR_VERSION,row['source_sha256'],
             row['template_content_hash'],result['result'],Jsonb(result['report'])))


def positive(value):
    number = int(value)
    if number <= 0: raise argparse.ArgumentTypeError('양의 정수가 필요합니다.')
    return number




def main(argv=None):
    """Preview ZIP을 읽기 전용으로 독립 검증하고 보고서를 작성한다."""
    from zipfile import BadZipFile

    from scripts.problems.common.independent_instance_validator import (
        SUPPORTED_TYPES,
    )

    parser = argparse.ArgumentParser(
        description="선형대수 Preview ZIP 독립 검증 (DB 쓰기 없음)"
    )
    parser.add_argument(
        "--preview-zip",
        type=Path,
        required=True,
        help="검증할 Preview ZIP 파일",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "data/reports/linear_algebra/"
            "independent_validation_report.json"
        ),
        help="검증 결과 JSON 보고서 경로",
    )
    parser.add_argument(
        "--seconds",
        type=positive,
        default=30,
        help="문제당 최대 검증 시간(초)",
    )

    args = parser.parse_args(argv)

    if not args.preview_zip.is_file():
        parser.error("Preview ZIP 파일을 찾을 수 없습니다")

    if args.output.suffix.lower() != ".json":
        parser.error("보고서 파일은 .json이어야 합니다")

    if args.preview_zip.resolve() == args.output.resolve():
        parser.error("원본 ZIP을 보고서로 덮어쓸 수 없습니다")

    statuses = ("passed", "failed", "unsupported", "timeout")

    def empty_counts():
        return {status: 0 for status in statuses}

    totals = Counter()
    by_unit = {}
    by_type = {}
    details = []
    observed_types = set()

    def add_result(source, unit, kind, result):
        verdict = result.get("result", "failed")

        if verdict not in statuses:
            verdict = "failed"
            result = failure("잘못된 검증 결과 상태")

        totals[verdict] += 1

        if unit not in by_unit:
            by_unit[unit] = empty_counts()

        if kind not in by_type:
            by_type[kind] = empty_counts()

        by_unit[unit][verdict] += 1
        by_type[kind][verdict] += 1

        details.append({
            "source": source,
            "unit_id": unit,
            "problem_type": kind,
            "result": verdict,
            "report": result.get("report", {}),
        })

    try:
        with ZipFile(args.preview_zip, "r") as archive:
            # ZIP 내부의 Preview 문제 파일만 선택한다.
            sources = sorted(
                (
                    info for info in archive.infolist()
                    if not info.is_dir()
                    and Path(info.filename).name.startswith("start_")
                    and info.filename.endswith(".json")
                ),
                key=lambda info: info.filename,
            )

            if not sources:
                parser.error(
                    "ZIP 안에 start_*.json 문제 파일이 없습니다"
                )

            for info in sources:
                source = info.filename
                unit = "unknown"
                kind = "unknown"

                # ZIP 압축 해제 크기 상한
                max_size = 10 * 1024 * 1024

                if info.file_size > max_size:
                    add_result(
                        source,
                        unit,
                        kind,
                        failure("문제 JSON 크기 제한 초과"),
                    )
                    continue

                try:
                    with archive.open(info) as stream:
                        data = stream.read(max_size + 1)

                    if len(data) > max_size:
                        raise ValueError(
                            "문제 파일 크기 제한 초과"
                        )

                    payload = json.loads(
                        data.decode("utf-8")
                    )

                    if not isinstance(payload, dict):
                        raise ValueError(
                            "문제 JSON의 최상위는 객체여야 합니다"
                        )

                    kind_value = payload.get("problem_type")

                    if isinstance(kind_value, str):
                        kind = kind_value
                        observed_types.add(kind)

                    snapshot = payload.get("template_snapshot")

                    if isinstance(snapshot, dict):
                        taxonomy = snapshot.get("taxonomy")

                        if isinstance(taxonomy, dict):
                            unit_value = taxonomy.get("unit_id")

                            if (
                                isinstance(unit_value, str)
                                and unit_value
                            ):
                                unit = unit_value

                    # 각 문제에 독립 검증과 시간 제한 적용
                    result = validate_with_timeout(
                        payload,
                        seconds=args.seconds,
                    )

                except (
                    ValueError,
                    UnicodeError,
                    OSError,
                    EOFError,
                    RuntimeError,
                    TypeError,
                    BadZipFile,
                ) as exc:
                    result = failure(
                        "문제 파일 처리 실패: "
                        f"{type(exc).__name__}: {exc}"
                    )

                add_result(
                    source,
                    unit,
                    kind,
                    result,
                )

    except (OSError, ValueError, BadZipFile) as exc:
        parser.error(
            "ZIP 파일을 읽을 수 없습니다: "
            f"{type(exc).__name__}: {exc}"
        )

    # 지원하는 문제 유형 중 ZIP에 없는 유형 집계
    missing_types = sorted(
        set(SUPPORTED_TYPES) - observed_types
    )

    # 계약에 정의되지 않은 문제 유형 집계
    unexpected_types = sorted(
        observed_types - set(SUPPORTED_TYPES)
    )

    total = sum(totals.values())

    all_passed = (
        total > 0
        and totals["passed"] == total
        and not missing_types
        and not unexpected_types
    )

    report = {
        "validator_version": VALIDATOR_VERSION,
        "checked_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "source_zip": str(args.preview_zip),
        "status": (
            "passed" if all_passed else "failed"
        ),
        "total": total,
        "counts": empty_counts(),
        "by_unit": dict(sorted(by_unit.items())),
        "by_type": dict(sorted(by_type.items())),
        "missing_types": missing_types,
        "unexpected_types": unexpected_types,
        "details": details,
        "database_write": False,
    }

    for status in statuses:
        report["counts"][status] = totals[status]

    # DB가 아닌 별도 JSON 보고서만 생성
    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    args.output.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "status": report["status"],
                "total": report["total"],
                "counts": report["counts"],
                "missing_types": missing_types,
                "unexpected_types": unexpected_types,
                "output": str(args.output),
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    return 0 if all_passed else 2




if __name__ == '__main__':
    mp.freeze_support()
    raise SystemExit(main())
