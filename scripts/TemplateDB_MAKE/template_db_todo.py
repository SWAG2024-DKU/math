"""선형대수 Template ZIP을 확인하고 기존 PostgreSQL Importer에 연결할 준비를 한다.

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
    """ZIP에서 출제 가능한 선형대수 Template만 읽는다."""
    records = []
    seen = set()
    with ZipFile(archive) as z:
        for path in sorted(z.namelist()):
            if not path.endswith('.json'):
                continue
            value = json.loads(z.read(path))
            if value.get('object_type') != 'problem_template':
                continue
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
    """TODO: 선형대수 Template를 프로젝트의 기존 PostgreSQL 테이블에 적재한다.

    TODO 1. 각 원본을 ProblemTemplate.model_validate()로 검사하고
        classification.answer_type과 answer_spec.answer_type의 일치도 확인한다.
        app.problems.template_importer.validate_answer_type()을 재사용할 수 있다.
    TODO 2. 기존 app.db.connection.get_connection()과
        app.problems.template_repository의 조회·삽입·개념 연결·감사 함수를 재사용한다.
        기존 scripts/problems/import_problem_templates.py는 전체 과목을 순회하므로
        이번에는 records의 선형대수 62개만 대상으로 연결한다.
    TODO 3. ZIP 내부 경로는 실제 프로젝트 경로가 아니다. DB source_path를
        어떤 상대 경로로 기록할지 정하고 재실행 시 동일 경로를 유지한다.
        기존 build_db_record()의 normalize_source_path()를 그대로 쓰려면
        임시 파일을 프로젝트 루트 아래에 둬야 한다.
    TODO 4. (template_id, template_version)이 이미 있으면 content_hash를 비교한다.
        같으면 건너뛰고, 다르면 공개된 Template를 덮어쓰지 말고 오류로 종료한다.
        병렬 적재 가능성이 있다면 SELECT ... FOR UPDATE 또는 충돌 처리로 보호한다.
    TODO 5. 한 트랜잭션에서 Template와 kb.concepts 외래 키 연결을 저장한다.
        참조 Concept가 없으면 롤백하고, 결과를 template_import_audit에 기록한다.
    TODO 6. 적재·건너뜀·오류 건수와 출처 경로를 출력한다.
    """
    raise NotImplementedError('기존 PostgreSQL Template Importer 연결 작업이 필요합니다.')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--templates', required=True, type=Path)
    args = parser.parse_args()
    records = read_templates(args.templates)
    print(json.dumps({'ready_templates': len(records),
                      'problem_types': len({r.payload['classification']['problem_type'] for r in records}),
                      'subject': 'linear_algebra'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
