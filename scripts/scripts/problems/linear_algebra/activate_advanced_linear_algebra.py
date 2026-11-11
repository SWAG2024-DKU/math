"""Upgrade exactly six opt-in linear algebra drafts to executable rules.

Run from project root after reviewing the six typed implementations. Re-running
is idempotent; every other Rule remains semantically identical.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


ADVANCED = {
    'compact_svd_approximation': {
        'formula': 'truncated_svd_formula',
        'parameters': {'A': ('matrix', {'rows': 2, 'cols': 2}, 'small_svd_matrix')},
        'expression': 'compact_svd_rank_one(A)',
        'validator': 'compact_svd_optimality_check',
        'text': '행렬 A = {{ A }}에 대해 Frobenius 노름을 최소화하는 rank 1 근사행렬을 구하시오.',
    },
    'complex_inner_product_calculation': {
        'formula': 'complex_inner_product',
        'parameters': {
            'u': ('vector', {'dimension': 2}, 'small_gaussian_vector'),
            'v': ('vector', {'dimension': 2}, 'complex_real_inner_partner'),
        },
        'expression': 'complex_inner_product(u, v)',
        'validator': 'complex_inner_product_check',
        'text': '첫째 인자를 켤레로 취하는 복소 내적 u^H v를 구하시오. u = {{ u }}, v = {{ v }}',
    },
    'jordan_canonical_form_calculation': {
        'formula': 'jordan_decomposition_formula',
        'parameters': {'A': ('matrix', {'rows': 2, 'cols': 2}, 'defective_jordan_matrix')},
        'expression': 'jordan_defective_pair(A)',
        'validator': 'jordan_similarity_check',
        'text': 'A = P J P^(-1)을 만족하는 가역행렬 P와 조르당 표준형 J를 구하시오. A = {{ A }}',
    },
    'pca_calculation': {
        'formula': 'covariance_matrix_formula',
        'parameters': {'A': ('matrix', {'rows': 4, 'cols': 2}, 'centered_pca_matrix')},
        'expression': 'pca_projection(A)',
        'validator': 'pca_projection_check',
        'text': '행이 관측값인 중심화 데이터 A = {{ A }}에 대해 최대 분산의 1차원 주성분 공간으로 직교 투영하는 2x2 행렬을 구하시오.',
    },
    'pseudoinverse_calculation': {
        'formula': 'pseudoinverse_formula',
        'parameters': {'A': ('matrix', {'rows': 2, 'cols': 2}, 'rank_one_pseudoinverse_matrix')},
        'expression': 'moore_penrose_pinv(A)',
        'validator': 'moore_penrose_conditions_check',
        'text': 'rank 1 행렬 A = {{ A }}의 무어-펜로즈 의사역행렬 A^+를 구하시오.',
    },
    'svd_calculation': {
        'formula': 'svd_formula',
        'parameters': {'A': ('matrix', {'rows': 2, 'cols': 2}, 'small_svd_matrix')},
        'expression': 'advanced_svd(A)',
        'validator': 'svd_reconstruction_check',
        'text': 'A = U Σ V^H이고 특이값이 내림차순인 특이값 분해 (U, Σ, V)를 구하시오. A = {{ A }}',
    },
}


def upgrade(catalog: dict) -> dict:
    if catalog.get('subject_id') != 'linear_algebra':
        raise ValueError('Only linear_algebra catalogs are supported')
    encountered = set()
    for rule in catalog['rules']:
        kind = rule['problem_type']
        if kind not in ADVANCED:
            continue
        if kind in encountered:
            raise ValueError(f'Duplicate problem_type: {kind}')
        encountered.add(kind)
        item = ADVANCED[kind]
        rule['parameter_spec'] = {
            name: {
                'type': typ,
                'shape': dims,
                'generator': generator,
                'element_type': 'integer',
                'element_min': -5,
                'element_max': 5,
                **({'depends_on': ['u']} if kind == 'complex_inner_product_calculation' and name == 'v' else {}),
            }
            for name, (typ, dims, generator) in item['parameters'].items()
        }
        rule['symbol_spec'] = {}
        rule['constraints'] = []  # restricted generators and independent validators enforce the invariants
        rule['construction']['required_objects'] = list(item['parameters'])
        rule['construction']['text_templates'] = [item['text']]
        rule['construction']['builder_expression'] = item['expression']
        if item['formula'] not in rule['source_formula_ids']:
            raise ValueError(f"{kind}: expected formula {item['formula']} missing")
        rule['primary_formula_id'] = item['formula']
        rule['answer_spec']['engine'] = 'sympy'
        rule['answer_spec']['expression'] = item['expression']
        rule['answer_spec']['canonicalization'] = 'simplify'
        rule['validation']['validators'] = [item['validator']]
        rule['status'] = 'curated'
        rule['executable'] = True
        rule['manual_review_required'] = False
        rule['notes'] = '선형대수 고급 유형: 제한된 정수 입력, 정답 계산, 입력값 기반 독립 검증.'
    if encountered != set(ADVANCED):
        raise ValueError(f'Missing problem types: {sorted(set(ADVANCED)-encountered)}')
    return catalog


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=Path('data/generation_rules/linear_algebra.json'))
    parser.add_argument('--output', type=Path, default=Path('data/generation_rules/linear_algebra.json'))
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding='utf-8'))
    upgrade(data)
    if args.output == args.input and args.output.exists():
        backup = args.output.with_suffix('.json.before-advanced-ready.bak')
        if not backup.exists():
            backup.write_bytes(args.output.read_bytes())
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Six advanced linear algebra rules upgraded:', ', '.join(ADVANCED))


if __name__ == '__main__':
    main()
