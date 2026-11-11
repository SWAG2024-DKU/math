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
    # TODO[LA-D037] validate_with_timeout 구현
    # 1. 확대된 유리수/행렬 구조에서도 제한 시간과 Windows spawn을 보장한다.
    # 2. timeout을 unsupported 또는 성공으로 숨기지 않는다.
    raise NotImplementedError("TODO[LA-D037]: validate_with_timeout")


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
    # TODO[LA-D038] main 구현
    # 1. 후보 Preview ZIP 전체에 독립 검증을 실행한다.
    # 2. 단원·유형별 passed/failed/unsupported/timeout 및 누락된 유형을 집계한다.
    # 3. 이번 워크플로에서는 DB --write를 사용하지 않고 별도 보고서에만 기록한다.
    raise NotImplementedError("TODO[LA-D038]: main")


if __name__ == '__main__':
    mp.freeze_support()
    raise SystemExit(main())
