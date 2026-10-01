"""Avoid expensive algebraic eigenvalues in the eigenvector preview rule.

Project-root usage:
    python -m scripts.problems.limit_eigenvector_spectrum
    python -m scripts.problems.build_problem_templates --subject linear_algebra --overwrite

Only ``linear_algebra.eigenvector_calculation.v1`` changes. A backup is made
once beside the catalog. The sampler already implements the selected generator.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path

RULE_ID = 'linear_algebra.eigenvector_calculation.v1'
GENERATOR = 'small_integer_spectrum_symmetric'
DEFAULT_CATALOG = Path('data/generation_rules/linear_algebra.json')


def patch_catalog(catalog: dict) -> bool:
    if catalog.get('subject_id') != 'linear_algebra':
        raise ValueError('선형대수 Catalog가 아닙니다.')
    matches = [rule for rule in catalog['rules'] if rule.get('rule_id') == RULE_ID]
    if len(matches) != 1:
        raise ValueError(f'{RULE_ID} Rule은 정확히 한 개여야 합니다: {len(matches)}개')
    rule = matches[0]
    if rule.get('problem_type') != 'eigenvector_calculation':
        raise ValueError('대상 Rule의 problem_type이 예상과 다릅니다.')
    A = rule['parameter_spec']['A']
    shape = A.get('shape') or {}
    if (A.get('type') != 'matrix' or
            'symmetric' not in A.get('allowed_families', []) or
            shape.get('cols') != 'A.rows'):
        raise ValueError('A의 정사각 대칭행렬 계약이 예상과 다릅니다. 최신 Rule을 확인하세요.')
    if A.get('generator') == GENERATOR:
        return False
    if A.get('generator') is not None:
        raise ValueError(f"기존 generator {A['generator']!r}를 덮어쓰지 않습니다.")
    A['generator'] = GENERATOR
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, default=DEFAULT_CATALOG)
    args = parser.parse_args()
    path = args.catalog
    original = path.read_bytes()
    catalog = json.loads(original.decode('utf-8-sig'))
    if not patch_catalog(catalog):
        print('[UNCHANGED] 이미 전용 generator가 설정되어 있습니다.')
        return 0
    backup = path.with_name(path.name + '.before-eigenvector-spectrum.bak')
    if not backup.exists():
        shutil.copy2(path, backup)
    content = json.dumps(catalog, ensure_ascii=False, indent=2) + '\n'
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', newline='\n',
                                         dir=path.parent, prefix=path.name + '.',
                                         suffix='.tmp', delete=False) as temp:
            temp_name = temp.name
            temp.write(content)
        os.replace(temp_name, path)
    finally:
        if temp_name is not None and os.path.exists(temp_name):
            os.unlink(temp_name)
    print(f'[UPDATED] {RULE_ID}: A.generator={GENERATOR}')
    print(f'[BACKUP] {backup}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
