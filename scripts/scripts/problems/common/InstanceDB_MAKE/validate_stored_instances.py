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
    """재시도 횟수가 아닌 실제 경과 시간 제한. 종료된 worker를 반드시 회수한다."""
    context = mp.get_context('spawn')
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(target=worker, args=(sender, payload))
    start = time.monotonic()
    try:
        process.start(); sender.close()
        if receiver.poll(seconds):
            try:
                result = receiver.recv()
            except EOFError:
                result = failure('worker가 결과 없이 종료됨', 'unsupported')
        else:
            result = failure(f'제한 시간 {seconds}초 초과', 'unsupported')
            result['report']['timeout'] = True
        result['report']['elapsed_seconds'] = round(time.monotonic() - start, 3)
        return result
    finally:
        sender.close(); receiver.close()
        if process.pid is not None:
            if process.is_alive(): process.terminate()
            process.join(2)
            if process.is_alive(): process.kill(); process.join()
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='검증 이력 저장; 자동 확정 없음')
    parser.add_argument('--limit', type=positive)
    parser.add_argument('--batch-size', type=positive, default=100)
    parser.add_argument('--timeout-seconds', type=positive, default=30)
    parser.add_argument('--after-id', type=UUID)
    parser.add_argument('--report-dir', type=Path, default=Path('data/instance_validation_reports'))
    parser.add_argument('--preview-zip', type=Path, help='DB 대신 Preview ZIP을 읽는 사전 테스트')
    args = parser.parse_args(argv)
    if args.preview_zip and (args.write or args.after_id): parser.error('ZIP 모드에서는 --write/--after-id를 사용할 수 없습니다.')
    folder = args.report_dir / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:8])
    folder.mkdir(parents=True)
    counts = Counter(); last_id = None; read_conn = write_conn = archive = None
    summary = {'validator_version':VALIDATOR_VERSION,'write':args.write,'completed':False}
    try:
        if args.preview_zip:
            archive = ZipFile(args.preview_zip)
            names = sorted(n for n in archive.namelist() if Path(n).name.startswith('start_') and n.endswith('.json'))
            if not names: raise ValueError('Preview JSON 없음')
            if args.limit: names = names[:args.limit]
            rows = ({'instance_id':n,'payload':json.loads(archive.read(n))} for n in names)
        else:
            read_conn = connection()
            read_conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            if args.write:
                write_conn = connection(); write_conn.autocommit = True
            rows = iterate_rows(read_conn,args.batch_size,args.after_id,args.limit)
        with (folder/'results.jsonl').open('w',encoding='utf-8') as output:
            for row in rows:
                try:
                    if not args.preview_zip: storage_check(row)
                    result = validate_with_timeout(row['payload'],args.timeout_seconds)
                except (ValueError,KeyError,TypeError) as exc:
                    result = failure(f'{type(exc).__name__}: {exc}')
                result['report']['payload_sha256'] = digest(row['payload'])
                if not args.preview_zip:
                    result['report']['source_hash_note'] = '원본 파일 바이트는 DB에 없으므로 source_sha256는 메타데이터 비교만 수행'
                saved = False
                if args.write:
                    try: save_result(write_conn,row,result); saved=True; counts['saved']+=1
                    except Exception as exc:
                        counts['write_errors']+=1
                        result['write_error']=f'{type(exc).__name__}: {exc}'
                counts[result['result']]+=1
                if result['report'].get('timeout'): counts['timeouts']+=1
                last_id = str(row['instance_id'])
                item = {'instance_id':last_id,'problem_type':row['payload'].get('problem_type'),'saved':saved,**result}
                output.write(json.dumps(item,ensure_ascii=False)+'\n');output.flush()
                print(f"[{result['result'].upper()}] {item['problem_type']} | {last_id}",flush=True)
                # DB 저장 실패 시 멈춰서 재개 커서가 실패 레코드를 건너뛰지 않게 한다.
                if args.write and not saved:
                    summary['failed_write_id']=last_id
                    last_id = summary.get('last_successfully_saved_id')
                    raise RuntimeError('검증 이력 저장 실패. results.jsonl의 write_error를 확인하세요.')
                if saved: summary['last_successfully_saved_id']=last_id
        summary['completed']=True
    except Exception as exc:
        summary['error']=f'{type(exc).__name__}: {exc}'
    finally:
        if archive: archive.close()
        if write_conn: write_conn.close()
        if read_conn: read_conn.close()
        summary.update(counts=dict(counts),last_processed_id=last_id,report_dir=str(folder))
        (folder/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)
    return 0 if summary['completed'] and not counts['failed'] and not counts['unsupported'] else 1


if __name__ == '__main__':
    mp.freeze_support()
    raise SystemExit(main())
