"""선형대수 Template ZIP을 검증하고 --insert 지정 시 PostgreSQL에 적재한다.

프로젝트의 sql/005_create_problem_schema.sql 및 006~008 마이그레이션이
problem.problem_templates, problem.template_concepts와 적재 이력을 정의한다.
Template용 테이블은 추가로 생성하지 않는다.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile


@dataclass(frozen=True)
class TemplateRecord:
    template_id: str
    version: str
    sha256: str
    source: str
    payload: dict


def content_hash(value: dict) -> str:
    """기존 template_importer와 같은 규칙으로 정규화된 SHA-256을 계산한다."""
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def read_templates(archive: Path) -> list[TemplateRecord]:
    """DB 연결 없이 ZIP의 선형대수 Template 스키마와 답 유형을 검사한다."""
    from app.problems.template_importer import validate_answer_type
    from app.schemas.problem_template import ProblemTemplate

    records = []
    seen = set()
    with ZipFile(archive) as z:
        for path in sorted(z.namelist()):
            if not path.endswith('.json'):
                continue
            value = json.loads(z.read(path))
            if not isinstance(value, dict):
                raise ValueError(f'JSON 객체가 아닌 파일: {path}')
            if value.get('object_type') != 'problem_template':
                continue
            # 읽기 전용 실행에서도 필수 필드와 두 answer_type의 일치를 검사한다.
            try:
                template = ProblemTemplate.model_validate(value)
                validate_answer_type(template)
            except ValueError as exc:
                raise ValueError(f'Template 검증 실패: {path}\n{exc}') from exc
            if value.get('taxonomy', {}).get('subject_id') != 'linear_algebra':
                raise ValueError(f'다른 과목 Template: {path}')
            if value.get('status') != 'ready' or value.get('executable') is not True:
                raise ValueError(f'출제 대상이 아닌 Template: {path}')
            key = (value['template_id'], value['template_version'])
            if key in seen:
                raise ValueError(f'Template ID/버전 중복: {key}')
            seen.add(key)
            records.append(TemplateRecord(*key, content_hash(value), path, value))
    if not records:
        raise ValueError('선형대수 Template가 없습니다.')
    return records


def import_template_records(records: list[TemplateRecord]) -> None:
    """전달받은 선형대수 Template 전체를 검증하고 한 트랜잭션으로 적재한다.

    같은 ID/버전의 내용이 다르거나 Concept 연결에 실패하면 전체를 롤백한다.
    기존 audit 스키마는 오류 action을 허용하지 않아 실패는 출력 후 재발생시킨다.
    """
    from pathlib import PurePosixPath, PureWindowsPath

    from app.db.connection import get_connection
    from app.problems.template_importer import build_db_record, validate_answer_type
    from app.problems.template_repository import (
        find_existing_template,
        insert_template,
        insert_template_concept,
        insert_import_audit,
    )
    from app.schemas.problem_template import ProblemTemplate

    prepared = []
    seen = set()
    results = []
    current_source = None

    try:
        # DB에 쓰기 전에 전체 입력을 검사한다. ZIP을 거치지 않은 호출도 검증한다.
        for item in records:
            current_source = item.source
            raw = item.payload
            template = ProblemTemplate.model_validate(raw)
            validate_answer_type(template)
            if (raw.get('object_type') != 'problem_template'
                    or template.taxonomy.subject_id != 'linear_algebra'
                    or template.status != 'ready'
                    or template.executable is not True):
                raise ValueError('출제 가능한 선형대수 Template만 적재할 수 있습니다.')

            key = (template.template_id, template.template_version)
            if key != (item.template_id, item.version):
                raise ValueError('TemplateRecord와 원본의 ID/버전이 다릅니다.')
            if key in seen:
                raise ValueError(f'Template ID/버전 중복: {key}')
            seen.add(key)
            if content_hash(raw) != item.sha256:
                raise ValueError('TemplateRecord와 원본의 해시가 다릅니다.')

            # ZIP 출처는 고정된 가상 상대 경로로 기록하며 실제 파일은 만들지 않는다.
            # build_db_record는 경로 문자열만 처리하므로 임시 파일이 필요 없다.
            source = PurePosixPath(item.source.replace('\\', '/'))
            if (source.is_absolute() or PureWindowsPath(item.source).drive
                    or '..' in source.parts or source.suffix != '.json'):
                raise ValueError(f'잘못된 ZIP 내부 경로: {item.source}')
            path = Path('data/problem_templates/_zip_imports/linear_algebra').joinpath(
                *source.parts
            )
            record = build_db_record(path, raw, template, Path('.'))
            prepared.append((record, template))

        if prepared:
            current_source = None
            with get_connection() as conn:
                with conn.transaction():
                    # 아직 없는 행도 보호하려고 조회 전 쓰기 잠금을 잡는다.
                    # 다른 적재 작업의 INSERT/UPDATE는 이 트랜잭션 종료까지 대기한다.
                    with conn.cursor() as cur:
                        cur.execute(
                            'LOCK TABLE problem.problem_templates '
                            'IN SHARE ROW EXCLUSIVE MODE'
                        )

                    for record, template in prepared:
                        current_source = record['source_path']
                        existing = find_existing_template(
                            conn, template.template_id, template.template_version
                        )
                        if existing is None:
                            insert_template(conn, record)
                            # 존재하지 않는 Concept는 FK 오류를 내고 전체 적재를 취소한다.
                            for concept_id in dict.fromkeys(template.taxonomy.concept_ids):
                                insert_template_concept(
                                    conn, template.template_id,
                                    template.template_version, concept_id,
                                )
                            action = 'inserted'
                            reason = 'New template inserted'
                        elif existing['content_hash'] == record['content_hash']:
                            action = 'skipped'
                            reason = 'Same template already exists'
                        else:
                            raise RuntimeError(
                                '같은 ID/버전의 Template 내용이 다릅니다: '
                                f'{template.template_id} / {template.template_version}'
                            )

                        # 성공 이력도 Template 및 Concept 연결과 함께 커밋한다.
                        insert_import_audit(conn, {
                            'template_id': template.template_id,
                            'template_version': template.template_version,
                            'selected_path': record['source_path'],
                            'rejected_path': None,
                            'action': action,
                            'reason': reason,
                        })
                        results.append({'action': action, 'source_path': current_source})
                    current_source = None
    except Exception as exc:
        # 중간에 성공했던 INSERT도 롤백되므로 완료 건수로 집계하지 않는다.
        print(json.dumps({
            'inserted': 0, 'skipped': 0, 'errors': 1,
            'source_path': current_source, 'error': str(exc),
        }, ensure_ascii=False, indent=2))
        raise

    # 커밋이 끝난 뒤에만 최종 결과를 출력한다.
    print(json.dumps({
        'inserted': sum(row['action'] == 'inserted' for row in results),
        'skipped': sum(row['action'] == 'skipped' for row in results),
        'errors': 0, 'sources': results,
    }, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--templates', required=True, type=Path)
    parser.add_argument(
        '--insert', action='store_true',
        help='검증 후 DB에 적재합니다. 생략하면 DB 연결 없이 검증만 합니다.',
    )
    args = parser.parse_args()
    records = read_templates(args.templates)
    print(json.dumps({'ready_templates': len(records),
                      'problem_types': len({r.payload['classification']['problem_type'] for r in records}),
                      'subject': 'linear_algebra'}, ensure_ascii=False, indent=2))
    # 명시적으로 --insert를 지정했을 때만 DB 저장 함수를 호출한다.
    if args.insert:
        import_template_records(records)


if __name__ == '__main__':
    main()
