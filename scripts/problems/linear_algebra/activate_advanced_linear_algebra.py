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
    # TODO[LA-D020] upgrade 구현
    # 1. 현재 parameter_spec 전체 교체, constraints 초기화, status/notes 강제 설정이 검수 정보를 지울 수 있다.
    # 2. 최초 활성화와 다양성 갱신을 분리하고 기존 사용자 수정/검수 이력을 보존한다.
    # 3. ADVANCED 설정은 새 Python 정책과 중복 정의하지 않는다.
    raise NotImplementedError("TODO[LA-D020]: upgrade")


def main() -> None:
    # TODO[LA-D021] main 구현
    # 1. 이미 검수된 카탈로그에 활성화 스크립트를 재실행할 때 무엇이 바뀌는지 dry-run/백업/변경 보고를 제공한다.
    # 2. 신규 후보에 자동 승인 플래그를 부여하지 않는다.
    raise NotImplementedError("TODO[LA-D021]: main")


if __name__ == '__main__':
    main()
