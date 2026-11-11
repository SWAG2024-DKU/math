"""Avoid expensive algebraic eigenvalues in the eigenvector preview rule.

Project-root usage:
    python -m scripts.problems.linear_algebra.limit_eigenvector_spectrum
    python -m scripts.problems.common.build_problem_templates --subject linear_algebra --overwrite

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
    # TODO[LA-D023] patch_catalog 구현
    # 1. 기존 안전 모드의 작은 정수 스펙트럼 제한은 유지한다.
    # 2. 확장 정책에서는 새로운 generator를 충돌로 오판하거나 다시 고정하지 않도록 버전/모드에 따른 동작을 명시한다.
    raise NotImplementedError("TODO[LA-D023]: patch_catalog")


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
