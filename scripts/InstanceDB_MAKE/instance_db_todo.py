"""Preview Instance를 pending으로 적재하고 독립 검증/사람 승인 후 확정한다.
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
            if not isinstance(value, dict):
                raise ValueError(f'Template은 JSON 객체여야 합니다: {path}')
            if value.get('object_type') != 'problem_template':
                continue
            if value.get('status') != 'ready' or value.get('taxonomy', {}).get('subject_id') != 'linear_algebra':
                raise ValueError(f'출제 대상이 아닌 Template: {path}')
            try:
                _check_template_snapshot(value)
            except ValueError as exc:
                raise ValueError(f'잘못된 Template: {path}: {exc}') from exc
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
            try:
                _validate_payload_structure(value)
            except ValueError as exc:
                raise ValueError(f'잘못된 Preview: {path}: {exc}') from exc
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
            record = PendingInstance(*key, expected, problem_hash, path,
                                     hashlib.sha256(source_bytes).hexdigest(), seed, value)
            _check_record(record)
            records.append(record)
    if not records:
        raise ValueError('Preview Instance가 없습니다.')
    return records


def _db_connection():
    """DB 의존성은 쓰기 단계에서만 로드한다. 직접 실행도 지원한다."""
    import sys
    project_root = str(Path(__file__).resolve().parents[2])
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from app.db.connection import get_connection
    return get_connection()


def _jsonb(value: object):
    from psycopg.types.json import Jsonb
    return Jsonb(value)


def _check_schema(conn) -> None:
    """마이그레이션은 자동 적용하지 않고 필요한 관계의 존재를 확인한다."""
    for name in (
        'kb.concepts', 'problem.problem_templates', 'problem.template_concepts',
        'problem.template_import_audit', 'problem.problem_instances',
        'problem.instance_validation_runs', 'problem.confirmed_instances',
    ):
        row = conn.execute('SELECT to_regclass(%s) AS relation', (name,)).fetchone()
        if row['relation'] is None:
            raise RuntimeError(f'DB 관계가 없습니다: {name}. 005~009 SQL을 확인하세요.')


def _check_digest(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(
        char not in '0123456789abcdef' for char in value
    ):
        raise ValueError(f'{name}: 소문자 SHA-256 해시가 필요합니다.')
    return value


def _template_schema():
    """프로젝트의 기존 Pydantic Template 스키마만 로드한다."""
    import sys
    project_root = str(Path(__file__).resolve().parents[2])
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from app.schemas.problem_template import ProblemTemplate
    return ProblemTemplate


def _check_template_snapshot(value: object):
    if not isinstance(value, dict):
        raise ValueError('template_snapshot은 완전한 Template JSON 객체여야 합니다.')
    required = {'schema_version', 'object_type', 'template_id', 'template_version',
                'status', 'executable', 'generation_rule_id', 'generation_rule_version',
                'generation_rule_status', 'taxonomy', 'classification', 'parameters',
                'problem_builder', 'answer_spec', 'solution_spec', 'validation'}
    missing = required - value.keys()
    if missing:
        raise ValueError(f'Template 필수 필드 누락: {sorted(missing)}')
    template = _template_schema().model_validate(value)
    if template.taxonomy.subject_id != 'linear_algebra' or template.status != 'ready' or not template.executable:
        raise ValueError('선형대수 ready/executable Template만 허용합니다.')
    if template.classification.answer_type != template.answer_spec.answer_type:
        raise ValueError('Template 내부 answer_type이 일치하지 않습니다.')
    return template


def _check_math_text(value: str, *, symbolic: bool = False, equation: bool = False,
                     solution_set: bool = False) -> None:
    """직렬화된 수식의 문법/구조만 확인한다. 계산하거나 문자열을 실행하지 않는다."""
    import ast
    import math
    if not value.strip() or len(value) > 20000:
        raise ValueError('비어 있거나 너무 긴 수학 표현입니다.')
    try:
        tree = ast.parse(value, mode='eval')
    except (SyntaxError, RecursionError) as exc:
        raise ValueError('수학 표현의 문법이 잘못됐습니다.') from exc
    nodes = list(ast.walk(tree))
    if len(nodes) > 4000:
        raise ValueError('수학 표현이 너무 복잡합니다.')
    allowed_calls = {'sqrt': (1,), 'Rational': (2,)}
    if equation:
        allowed_calls.update({'Eq': (2,), 'Matrix': (1,)})
        if not (isinstance(tree.body, ast.Call) and isinstance(tree.body.func, ast.Name)
                and tree.body.func.id == 'Eq' and len(tree.body.args) == 2):
            raise ValueError('equation 정답은 Eq(좌변, 우변) 형식이어야 합니다.')
    containers = (ast.List, ast.Tuple, ast.Set) if solution_set or equation else ()
    if solution_set and value == 'EmptySet':
        return
    if solution_set and not (isinstance(tree.body, ast.Set) and
                             all(isinstance(item, ast.Tuple) for item in tree.body.elts)):
        raise ValueError('기호 벡터 해집합은 {(성분, ...)} 또는 EmptySet 형식이어야 합니다.')
    function_names = {id(node.func) for node in nodes if isinstance(node, ast.Call)}
    allowed_nodes = (ast.Expression, ast.Constant, ast.Name, ast.Load, ast.BinOp,
                     ast.UnaryOp, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow,
                     ast.UAdd, ast.USub, ast.Call) + containers
    for node in nodes:
        if not isinstance(node, allowed_nodes):
            raise ValueError('허용되지 않은 수학 표현 구조입니다.')
        if isinstance(node, ast.Constant) and type(node.value) not in (int, float):
            raise ValueError('수식에는 숫자 상수만 허용합니다.')
        if isinstance(node, ast.Constant) and type(node.value) is float and not math.isfinite(node.value):
            raise ValueError('수식에 비유한 수치가 있습니다.')
        if isinstance(node, ast.Call):
            if (not isinstance(node.func, ast.Name) or node.func.id not in allowed_calls
                    or len(node.args) not in allowed_calls[node.func.id] or node.keywords):
                raise ValueError('허용되지 않은 수식 함수/인자입니다.')
        if isinstance(node, ast.Name):
            if id(node) in function_names or node.id == 'I':
                continue
            if not symbolic or node.id.startswith('_'):
                raise ValueError(f'허용되지 않은 수학 기호: {node.id}')


def _check_scalar_structure(value: object) -> None:
    import math
    if type(value) is int:
        return
    if type(value) is float and math.isfinite(value):
        return
    if isinstance(value, str):
        _check_math_text(value)
        return
    raise ValueError('수치 정답/원소는 유한한 숫자 또는 수치식 문자열이어야 합니다.')


def _check_matrix_structure(value: object) -> tuple[int, int]:
    if not isinstance(value, list) or not value or not all(isinstance(row, list) and row for row in value):
        raise ValueError('행렬은 비어 있지 않은 2차원 배열이어야 합니다.')
    columns = len(value[0])
    if any(len(row) != columns for row in value):
        raise ValueError('행렬의 행 길이가 다릅니다.')
    for row in value:
        for item in row:
            _check_scalar_structure(item)
    return len(value), columns


def _check_vector_structure(value: object) -> None:
    if not isinstance(value, list) or not value:
        raise ValueError('벡터는 비어 있지 않은 배열이어야 합니다.')
    if any(isinstance(item, list) for item in value):
        rows, columns = _check_matrix_structure(value)
        if rows != 1 and columns != 1:
            raise ValueError('벡터는 한 행 또는 한 열이어야 합니다.')
    else:
        for item in value:
            _check_scalar_structure(item)


def _check_answer_structure(answer: object, answer_type: str, problem_type: str) -> None:
    if answer is None:
        raise ValueError('expected_answer는 null일 수 없습니다.')
    if answer_type == 'boolean':
        if type(answer) is not bool:
            raise ValueError('boolean 정답은 true/false여야 합니다.')
    elif answer_type in {'single_choice', 'multiple_choice'}:
        # 현재 선형대수 Preview는 두 유형 모두 문자열로 직렬화한다.
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError('선택형 정답은 비어 있지 않은 문자열이어야 합니다.')
    elif answer_type == 'scalar':
        _check_scalar_structure(answer)
    elif answer_type == 'matrix':
        _check_matrix_structure(answer)
    elif answer_type == 'vector':
        _check_vector_structure(answer)
    elif answer_type in {'scalar_list', 'vector_list'}:
        if not isinstance(answer, list):
            raise ValueError(f'{answer_type} 정답은 배열이어야 합니다.')
        if problem_type == 'kernel_image_calculation':
            if len(answer) != 2 or not all(isinstance(part, list) for part in answer):
                raise ValueError('핵/상 정답은 두 기저 목록이어야 합니다.')
            for basis in answer:
                for item in basis:
                    _check_vector_structure(item)
        else:
            check = _check_scalar_structure if answer_type == 'scalar_list' else _check_vector_structure
            for item in answer:
                check(item)
    elif answer_type in {'matrix_pair', 'matrix_tuple'}:
        count = 2 if answer_type == 'matrix_pair' else 3
        if not isinstance(answer, list) or len(answer) != count:
            raise ValueError(f'{answer_type} 정답에는 행렬 {count}개가 필요합니다.')
        for item in answer:
            _check_matrix_structure(item)
    elif answer_type == 'matrix_list':
        if not isinstance(answer, list) or not answer:
            raise ValueError('matrix_list 정답은 비어 있지 않은 배열이어야 합니다.')
        for item in answer:
            if problem_type == 'spectral_decomposition_calculation':
                if not isinstance(item, list) or len(item) != 2:
                    raise ValueError('스펙트럼 분해 정답은 [고유값, 투영행렬] 목록이어야 합니다.')
                _check_scalar_structure(item[0])
                _check_matrix_structure(item[1])
            else:
                _check_matrix_structure(item)
    elif answer_type == 'equation':
        if not isinstance(answer, str):
            raise ValueError('equation 정답은 수식 문자열이어야 합니다.')
        _check_math_text(answer, symbolic=True, equation=True)
    elif answer_type in {'expression', 'vector_expression'}:
        if isinstance(answer, str):
            _check_math_text(answer, symbolic=True, solution_set=answer_type == 'vector_expression')
        elif isinstance(answer, list):
            if answer_type == 'expression':
                _check_matrix_structure(answer)
            elif answer:
                _check_vector_structure(answer)
        else:
            if answer_type == 'vector_expression':
                raise ValueError('vector_expression 정답은 배열 또는 해집합 문자열이어야 합니다.')
            _check_scalar_structure(answer)
    else:
        raise ValueError(f'지원하지 않는 정답 유형: {answer_type}')


def _validate_payload_structure(value: object) -> None:
    if not isinstance(value, dict):
        raise ValueError('payload는 JSON 객체여야 합니다.')
    required = {'subject_id', 'template_id', 'template_version', 'generation_rule_id',
                'generation_rule_version', 'problem_type', 'answer_type', 'template_status',
                'publishable', 'statement', 'seed', 'parameters', 'expected_answer', 'template_snapshot'}
    missing = required - value.keys()
    if missing:
        raise ValueError(f'Instance 필수 필드 누락: {sorted(missing)}')
    if type(value['seed']) is not int or not -(2 ** 63) <= value['seed'] < 2 ** 63:
        raise ValueError('seed는 bool이 아닌 BIGINT 범위의 정수여야 합니다.')
    if value['publishable'] is not False:
        raise ValueError('비공개 Preview만 허용합니다.')
    if not isinstance(value['statement'], str) or not value['statement'].strip():
        raise ValueError('문제 문장이 없습니다.')
    json.dumps(value, allow_nan=False)
    template = _check_template_snapshot(value['template_snapshot'])
    matches = {'subject_id': template.taxonomy.subject_id, 'template_id': template.template_id,
               'template_version': template.template_version, 'generation_rule_id': template.generation_rule_id,
               'generation_rule_version': template.generation_rule_version,
               'problem_type': template.classification.problem_type,
               'answer_type': template.answer_spec.answer_type, 'template_status': template.status}
    for name, expected in matches.items():
        if value[name] != expected:
            raise ValueError(f'Instance의 {name}이 Template snapshot과 다릅니다.')
    parameters = value['parameters']
    if not isinstance(parameters, dict):
        raise ValueError('parameters는 JSON 객체여야 합니다.')
    required_parameters = {name for name, spec in template.parameters.items() if spec.required}
    required_parameters.update(set(template.problem_builder.required_objects) - set(template.symbols))
    missing = required_parameters - parameters.keys()
    unknown = parameters.keys() - template.parameters.keys()
    if missing or unknown:
        raise ValueError(f'parameters 누락={sorted(missing)}, 미선언={sorted(unknown)}')
    for name, item in parameters.items():
        kind = template.parameters[name].type
        try:
            if kind == 'matrix':
                _check_matrix_structure(item)
            elif kind == 'vector':
                _check_vector_structure(item)
            elif kind == 'integer':
                if type(item) is not int:
                    raise ValueError('정수여야 합니다.')
            elif kind in {'rational', 'real', 'derived'}:
                _check_scalar_structure(item)
            elif kind == 'choice':
                choices = template.parameters[name].choices
                if item is None or (choices and item not in choices):
                    raise ValueError('선택지에 없는 값입니다.')
            else:
                raise ValueError(f'지원하지 않는 파라미터 타입: {kind}')
        except ValueError as exc:
            raise ValueError(f'parameters.{name}: {exc}') from exc
    _check_answer_structure(value['expected_answer'], template.answer_spec.answer_type,
                            template.classification.problem_type)


def _check_record(record: PendingInstance) -> None:
    value = record.payload
    _validate_payload_structure(value)
    if not isinstance(value, dict):
        raise ValueError('payload는 JSON 객체여야 합니다.')
    if (value.get('template_id'), value.get('template_version'), value.get('seed')) != (
        record.template_id, record.template_version, record.seed
    ):
        raise ValueError('payload의 Template/seed가 레코드와 다릅니다.')
    if isinstance(record.seed, bool) or not isinstance(record.seed, int) or not (
        -(2 ** 63) <= record.seed < 2 ** 63
    ):
        raise ValueError('seed는 PostgreSQL BIGINT 범위의 정수여야 합니다.')
    if value.get('subject_id') != 'linear_algebra' or value.get('publishable') is not False:
        raise ValueError('선형대수 비공개 Preview만 적재할 수 있습니다.')
    if not isinstance(value.get('statement'), str) or not value['statement'].strip():
        raise ValueError('문제 문장이 없습니다.')
    if not isinstance(value.get('problem_type'), str) or not value['problem_type'].strip():
        raise ValueError('problem_type이 없습니다.')
    if 'expected_answer' not in value:
        raise ValueError('expected_answer가 없습니다.')
    _check_digest(record.source_hash, 'source_sha256')
    _check_digest(record.template_hash, 'template_content_hash')
    _check_digest(record.problem_hash, 'problem_hash')
    if _hash(value.get('template_snapshot')) != record.template_hash:
        raise ValueError('Template snapshot 해시가 다릅니다.')
    if _hash([record.template_id, value['statement'], value['expected_answer']]) != record.problem_hash:
        raise ValueError('문제 해시가 다릅니다.')
    # 원본 바이트 해시는 read_previews()에서 계산된다. JSON 재직렬화 해시와 다르다.
    json.dumps(value, allow_nan=False)


def insert_pending_instances(records: list[PendingInstance]) -> dict:
    """한 트랜잭션으로 pending 적재. 다른 seed의 동일 문제는 skip한다.
    같은 ID/버전/seed는 모든 해시와 payload가 동일할 때만 skip한다.
    오류 발생 시 전체 배치를 롤백하고 실패 경로를 예외에 포함한다.
    반환값/출력의 inserted는 커밋이 끝난 실제 저장 건수다.
    """
    from uuid import uuid4
    summary = {'inserted': 0, 'skipped': 0, 'failed': 0, 'records': []}
    current_path = None
    try:
        with _db_connection() as conn:
            _check_schema(conn)
            # 정렬된 잠금 순서로 동시에 여러 배치를 적재할 때의 교착을 줄인다.
            templates = {}
            for key in sorted({(x.template_id, x.template_version) for x in records}):
                templates[key] = conn.execute(
                    '''SELECT content_hash, subject_id, status, executable
                       FROM problem.problem_templates
                       WHERE template_id = %s AND template_version = %s FOR SHARE''', key,
                ).fetchone()
            for record in records:
                current_path = record.source_path
                _check_record(record)
                template = templates[(record.template_id, record.template_version)]
                if template is None or template['content_hash'] != record.template_hash:
                    raise ValueError('DB Template가 없거나 content_hash가 다릅니다.')
                if template['subject_id'] != 'linear_algebra' or template['status'] not in (
                    'ready', 'active'
                ) or template['executable'] is not True:
                    raise ValueError('DB Template가 출제 가능한 상태가 아닙니다.')
                value = record.payload
                # UNIQUE 두 가지를 함께 처리하고 충돌 행을 다시 읽어 정책을 판단한다.
                inserted = conn.execute(
                    '''INSERT INTO problem.problem_instances
                       (instance_id, template_id, template_version, template_content_hash,
                        subject_id, problem_type, seed, statement, expected_answer, payload,
                        problem_hash, source_path, source_sha256, status)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')
                       ON CONFLICT DO NOTHING RETURNING instance_id''',
                    (uuid4(), record.template_id, record.template_version, record.template_hash,
                     value['subject_id'], value['problem_type'], record.seed, value['statement'],
                     _jsonb(value['expected_answer']), _jsonb(value), record.problem_hash,
                     record.source_path, record.source_hash),
                ).fetchone()
                if inserted:
                    summary['inserted'] += 1
                    summary['records'].append({'source_path': current_path, 'action': 'inserted',
                                               'instance_id': str(inserted['instance_id'])})
                    continue
                conflicts = conn.execute(
                    '''SELECT instance_id, seed, template_content_hash, problem_hash,
                              source_sha256, payload, statement, expected_answer, problem_type
                       FROM problem.problem_instances
                       WHERE template_id = %s AND template_version = %s
                         AND (seed = %s OR problem_hash = %s) FOR UPDATE''',
                    (record.template_id, record.template_version, record.seed, record.problem_hash),
                ).fetchall()
                same_seed = next((x for x in conflicts if x['seed'] == record.seed), None)
                if same_seed is not None:
                    if not (
                        same_seed['template_content_hash'] == record.template_hash
                        and same_seed['problem_hash'] == record.problem_hash
                        and same_seed['source_sha256'] == record.source_hash
                        and same_seed['payload'] == value
                        and same_seed['statement'] == value['statement']
                        and same_seed['expected_answer'] == value['expected_answer']
                        and same_seed['problem_type'] == value['problem_type']
                    ):
                        raise ValueError('같은 Template/seed의 내용이 다릅니다. 덮어쓰지 않습니다.')
                    existing = same_seed
                    reason = 'identical_seed'
                else:
                    existing = next((x for x in conflicts if x['problem_hash'] == record.problem_hash), None)
                    if existing is None or not (
                        existing['template_content_hash'] == record.template_hash
                        and existing['statement'] == value['statement']
                        and existing['expected_answer'] == value['expected_answer']
                        and existing['problem_type'] == value['problem_type']
                    ):
                        raise ValueError('동일 문제 해시의 내용이 다릅니다.')
                    reason = 'duplicate_problem'
                summary['skipped'] += 1
                summary['records'].append({'source_path': current_path, 'action': 'skipped',
                                           'reason': reason, 'instance_id': str(existing['instance_id'])})
    except Exception as exc:
        failure = {'inserted': 0, 'skipped': summary['skipped'], 'failed': 1,
                   'rolled_back': True, 'source_path': current_path, 'error': str(exc)}
        print(json.dumps(failure, ensure_ascii=False))
        raise RuntimeError(f'Instance 적재 실패 (전체 롤백): {current_path}: {exc}') from exc
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def record_independent_validation(instance_id: str, result: dict) -> None:
    """독립 검증 결과를 저장한다. 생성 시 validation_trace는 전달하지 않는다.
    result 계약: validator_version, result(passed/failed/unsupported),
    source_sha256, template_content_hash, report(JSON 객체).
    해시는 validator가 실제로 검사한 원본에서 가져와야 한다.
    """
    from uuid import UUID, uuid4
    identity = UUID(instance_id)
    if not isinstance(result, dict):
        raise ValueError('독립 검증 결과는 JSON 객체여야 합니다.')
    version = result.get('validator_version')
    if not isinstance(version, str) or not version.strip():
        raise ValueError('validator_version이 필요합니다.')
    verdict = result.get('result')
    if verdict not in ('passed', 'failed', 'unsupported'):
        raise ValueError('검증 판정은 passed/failed/unsupported여야 합니다.')
    source_hash = _check_digest(result.get('source_sha256'), 'source_sha256')
    template_hash = _check_digest(result.get('template_content_hash'), 'template_content_hash')
    report = result.get('report')
    if not isinstance(report, dict) or not report:
        raise ValueError('독립 검증 근거를 담은 report 객체가 필요합니다.')
    json.dumps(report, allow_nan=False)
    with _db_connection() as conn:
        _check_schema(conn)
        instance = conn.execute(
            '''SELECT source_sha256, template_content_hash FROM problem.problem_instances
               WHERE instance_id = %s FOR UPDATE''', (identity,),
        ).fetchone()
        if instance is None:
            raise ValueError(f'Instance가 없습니다: {instance_id}')
        if instance['source_sha256'] != source_hash or instance['template_content_hash'] != template_hash:
            raise ValueError('독립 검증 대상 해시가 저장된 Instance와 다릅니다.')
        # confirm_instance와 동일한 Instance 잠금을 사용한다. 잠금 이후의 실제 시각을
        # 기록해 먼저 시작했지만 나중에 저장된 실패가 과거 결과로 정렬되지 않게 한다.
        conn.execute(
            '''INSERT INTO problem.instance_validation_runs
               (run_id, instance_id, validator_version, source_sha256,
                template_content_hash, result, report, checked_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, clock_timestamp())''',
            (uuid4(), identity, version, source_hash, template_hash, verdict, _jsonb(report)),
        )
        # confirmed 상태의 최신 결과가 바뀌어도 VIEW에서 즉시 공개 대상이 걸러진다.
        # 이 함수는 사람 검수 결정이나 confirmed 상태를 자동 부여하지 않는다.


def confirm_instance(
    instance_id: str, reviewer_id: str, *, validator_version: str,
    human_review_decision: str,
) -> None:
    """명시적 사람 승인 + 현재 검증기 버전의 최신 passed일 때만 원자적으로 확정.
    호출자는 문제 문장/정답 형식/유일성을 검수한 뒤 approved를 전달한다.
    validator_version은 현재 사용하는 독립 검증기의 버전을 전달한다.
    """
    from uuid import UUID
    identity = UUID(instance_id)
    if not isinstance(reviewer_id, str) or not reviewer_id.strip():
        raise ValueError('실제 검수자의 reviewer_id가 필요합니다.')
    if human_review_decision != 'approved':
        raise ValueError('사람 검수 approved 결정이 있어야 확정할 수 있습니다.')
    if not isinstance(validator_version, str) or not validator_version.strip():
        raise ValueError('현재 validator_version이 필요합니다.')
    with _db_connection() as conn:
        _check_schema(conn)
        reference = conn.execute(
            '''SELECT template_id, template_version FROM problem.problem_instances
               WHERE instance_id = %s''', (identity,),
        ).fetchone()
        if reference is None:
            raise ValueError(f'Instance가 없습니다: {instance_id}')
        template = conn.execute(
            '''SELECT content_hash, subject_id, status, executable FROM problem.problem_templates
               WHERE template_id = %s AND template_version = %s FOR UPDATE''',
            (reference['template_id'], reference['template_version']),
        ).fetchone()
        instance = conn.execute(
            'SELECT * FROM problem.problem_instances WHERE instance_id = %s FOR UPDATE',
            (identity,),
        ).fetchone()
        if instance is None or (instance['template_id'], instance['template_version']) != (
            reference['template_id'], reference['template_version']
        ):
            raise ValueError('승격 도중 Instance의 Template 참조가 변경됐습니다.')
        if template is None or not (
            template['subject_id'] == instance['subject_id'] == 'linear_algebra'
            and template['status'] in ('ready', 'active') and template['executable'] is True
            and template['content_hash'] == instance['template_content_hash']
        ):
            raise ValueError('현재 Template 상태 또는 해시가 출제 조건과 다릅니다.')
        if instance['status'] not in ('pending', 'confirmed'):
            raise ValueError('rejected Instance는 확정할 수 없습니다.')
        latest = conn.execute(
            '''SELECT validator_version, result, source_sha256, template_content_hash
               FROM problem.instance_validation_runs WHERE instance_id = %s
               ORDER BY checked_at DESC, run_id DESC LIMIT 1 FOR UPDATE''', (identity,),
        ).fetchone()
        if latest is None or not (
            latest['result'] == 'passed' and latest['validator_version'] == validator_version
            and latest['source_sha256'] == instance['source_sha256']
            and latest['template_content_hash'] == instance['template_content_hash']
        ):
            raise ValueError('최신 독립 검증의 판정/해시/검증기 버전이 확정 조건과 다릅니다.')
        conn.execute(
            '''UPDATE problem.problem_instances SET status = 'confirmed',
               human_reviewer_id = %s, human_review_decision = 'approved',
               human_reviewed_at = clock_timestamp(), confirmed_at = clock_timestamp(),
               confirmed_validator_version = %s WHERE instance_id = %s''',
            (reviewer_id.strip(), validator_version, identity),
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--templates', type=Path, required=True)
    parser.add_argument('--previews', type=Path, required=True)
    parser.add_argument('--insert', action='store_true',
                        help='후보 확인 후 DB에 pending으로 적재 (기본은 읽기 전용)')
    args = parser.parse_args()
    # 기본 실행은 읽기 전용이며 --insert를 명시할 때만 DB에 저장한다.
    records = read_previews(args.previews, read_template_hashes(args.templates))
    per_type = Counter(x.payload['problem_type'] for x in records)
    print(json.dumps({'pending_candidates': len(records), 'types': len(per_type),
                      'count_per_type': dict(sorted(per_type.items())),
                      'distinct_problem_hashes': len({x.problem_hash for x in records})},
                     ensure_ascii=False, indent=2))
    if args.insert:
        insert_pending_instances(records)


if __name__ == '__main__':
    main()
