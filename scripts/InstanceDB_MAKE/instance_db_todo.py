"""Preview Instance의 pending 적재와 검증 이후 confirmed 승격을 준비한다.

Template DB 파트의 Python 파일을 import하지 않는다. 두 파트는
기존 Template의 (ID, 버전, 정규화된 SHA-256) 규칙만 공유한다.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile


@dataclass(frozen=True)
class PendingInstance:
    template_id: str
    template_version: str
    template_hash: str
    problem_hash: str
    source_path: str
    source_hash: str
    seed: int
    payload: dict


def _hash(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def read_template_hashes(template_zip: Path) -> dict[tuple[str, str], str]:
    """Template DB 코드를 가져오지 않고 ZIP에서 참조용 해시를 읽는다."""
    hashes = {}
    with ZipFile(template_zip) as z:
        for path in sorted(z.namelist()):
            if not path.endswith('.json'):
                continue
            value = json.loads(z.read(path))
            if value.get('object_type') != 'problem_template':
                continue
            if value.get('status') != 'ready' or value.get('taxonomy', {}).get('subject_id') != 'linear_algebra':
                raise ValueError(f'출제 대상이 아닌 Template: {path}')
            key = (value['template_id'], value['template_version'])
            if key in hashes:
                raise ValueError(f'Template ID/버전 중복: {key}')
            hashes[key] = _hash(value)
    return hashes


def read_previews(preview_zip: Path, template_hashes: dict[tuple[str, str], str]) -> list[PendingInstance]:
    """원본 Template 일치 여부를 확인하고 DB 쓰기 없이 pending 후보를 만든다."""
    records = []
    keys = set()
    with ZipFile(preview_zip) as z:
        for path in sorted(z.namelist()):
            if not Path(path).name.startswith('start_') or not path.endswith('.json'):
                continue
            source_bytes = z.read(path)
            value = json.loads(source_bytes)
            key = (value['template_id'], value['template_version'])
            expected = template_hashes.get(key)
            if expected is None or _hash(value.get('template_snapshot')) != expected:
                raise ValueError(f'Template snapshot/버전 불일치: {path}')
            if value.get('subject_id') != 'linear_algebra' or value.get('publishable') is not False:
                raise ValueError(f'Preview의 과목 또는 공개 상태 오류: {path}')
            seed = value.get('seed')
            if isinstance(seed, bool) or not isinstance(seed, int):
                raise ValueError(f'seed가 없습니다: {path}')
            identity = (*key, seed)
            if identity in keys:
                raise ValueError(f'동일 Template/seed 중복: {identity}')
            keys.add(identity)
            problem_hash = _hash([key[0], value['statement'], value['expected_answer']])
            records.append(PendingInstance(*key, expected, problem_hash, path,
                                           hashlib.sha256(source_bytes).hexdigest(), seed, value))
    if not records:
        raise ValueError('Preview Instance가 없습니다.')
    return records


def insert_pending_instances(records: list[PendingInstance]) -> None:
    """TODO: Preview를 문제 공개 전 상태인 pending으로만 저장한다.

    TODO 1. 프로젝트의 005~008 SQL 적용 여부를 확인하고 Instance용 009 초안을
        실제 PostgreSQL 스키마와 대조한 뒤 적용한다. 모든 Template ID·버전·해시가
        problem.problem_templates에 존재하고 content_hash가 일치하는지 검사한다.
    TODO 2. 기존 app.db.connection.get_connection()의 psycopg 연결을 재사용한다.
        단일 트랜잭션에서 status='pending', seed, 원본 SHA-256, Template 해시,
        문제 문장·정답·전체 payload를 저장한다. JSONB는 psycopg Jsonb로 전달한다.
    TODO 3. 생성기의 validation_trace는 독립적인 수학 검증 결과로 취급하지 않는다.
        저장된 결과가 모두 성공해도 검증 이력은 별도 단계에서 기록한다.
    TODO 4. 같은 Template에서 서로 다른 seed가 동일한 문제를 만든 경우
        (problem_hash 중복), 건너뛸지 출처 별칭으로 보관할지 정책을 정한다.
        동일한 ID/seed인데 payload가 다르면 덮어쓰지 말고 중단한다.
    TODO 5. 재실행 시 해시와 전체 payload가 같을 때만 중복 적재를 건너뛴다.
        저장·건너뜀·실패 건수와 원본 경로를 보고한다.
    """
    raise NotImplementedError('pending Instance의 PostgreSQL 저장 구현이 필요합니다.')


def record_independent_validation(instance_id: str, result: dict) -> None:
    """TODO: 독립 검증의 버전·판정·검증 근거를 기록한다.

    TODO 1. preview_revalidator.py 결과를 원본 SHA-256 및 Template 해시에 묶는다.
        passed 외에 failed와 unsupported도 이력으로 남긴다.
    TODO 2. 검증 이력 기록만으로 confirmed 상태를 부여하지 않는다.
        최신 검증이 실패하면 과거 통과 이력으로 공개되지 않도록 한다.
    """
    raise NotImplementedError('Instance 독립 검증 이력 저장 구현이 필요합니다.')


def confirm_instance(instance_id: str, reviewer_id: str) -> None:
    """TODO: 최신 독립 검증과 사람 검수를 통과한 Instance만 확정한다.

    TODO 1. 한 트랜잭션에서 대상 Instance와 Template를 SELECT ... FOR UPDATE 한다.
    TODO 2. 최신 독립 검증이 passed이고 원본 SHA-256, Template 해시,
        Validator 버전이 현재 대상과 일치하는지 확인한다.
    TODO 3. 실제 검수자의 ID와 문제 문장·정답 형식·유일성 검수 결정을 기록한다.
        이름 없는 자동 승격과 Preview의 validation_trace만을 근거로 한 승격은 막는다.
    TODO 4. 조건 충족 시에만 confirmed, 검수 시각, 승격 시각과 검증기 버전을
        원자적으로 기록한다. 공개 조회는 confirmed_instances VIEW를 사용한다.
    """
    raise NotImplementedError('사람 검수 후 confirmed 승격 구현이 필요합니다.')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--templates', type=Path, required=True)
    parser.add_argument('--previews', type=Path, required=True)
    args = parser.parse_args()
    # 읽기 전용 후보 계산이다. 여기서는 DB 연결이나 저장을 수행하지 않는다.
    records = read_previews(args.previews, read_template_hashes(args.templates))
    per_type = Counter(x.payload['problem_type'] for x in records)
    print(json.dumps({'pending_candidates': len(records), 'types': len(per_type),
                      'count_per_type': dict(sorted(per_type.items())),
                      'distinct_problem_hashes': len({x.problem_hash for x in records})},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
