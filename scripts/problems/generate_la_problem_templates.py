from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path
from typing import Any


# -----------------------------------------------------------------------------
# Problem-type blueprints
# -----------------------------------------------------------------------------
# concept catalog만으로는 문제 본문, 파라미터, 정답 계산식을 완전히 복원할 수 없다.
# 따라서 supported_problem_types를 실제 ProblemTemplate로 바꾸기 위한 최소 규칙을
# problem_type별 blueprint로 둔다.


def p(
    type_: str,
    description: str,
    *,
    min_: int | float | None = None,
    max_: int | float | None = None,
    exclude: list[Any] | None = None,
    choices: list[Any] | None = None,
    step: int | float | None = None,
) -> dict[str, Any]:
    return {
        "type": type_,
        "required": True,
        "min": min_,
        "max": max_,
        "exclude": exclude or [],
        "choices": choices or [],
        "step": step,
        "distribution": "uniform",
        "description": description,
    }


BLUEPRINTS: dict[str, dict[str, Any]] = {
    "equation_to_matrix": {
        "answer_type": "matrix",
        "parameters": {
            "A": p("matrix", "연립일차방정식의 계수행렬. 2x2 또는 3x3의 작은 정수 행렬을 권장한다.", min_=-5, max_=5),
            "b": p("vector", "연립일차방정식의 상수벡터. A의 행 수와 같은 길이를 가져야 한다.", min_=-9, max_=9),
        },
        "text": "다음 연립일차방정식 A x = b에 대응하는 첨가행렬 [A | b]를 구하시오.\nA = {{ A }}, b = {{ b }}",
        "latex": r"A={{ A }},\quad \mathbf{b}={{ b }}\;\Rightarrow\;[A\mid\mathbf{b}]",
        "builder_cas": "Matrix.hstack(A, b)",
        "answer_cas": "Matrix.hstack(A, b)",
        "answer_latex": r"\left[A\mid \mathbf{b}\right]",
        "solution_strategy": "formula_substitution",
        "validators": ["symbolic_equivalence"],
    },
    "matrix_to_vector_equation": {
        "answer_type": "equation",
        "parameters": {
            "A": p("matrix", "벡터 방정식의 열벡터들을 담는 계수행렬.", min_=-5, max_=5),
            "b": p("vector", "우변 벡터. A의 행 수와 같은 길이를 가져야 한다.", min_=-9, max_=9),
        },
        "text": "주어진 A와 b에 대하여 A x = b를 A의 열벡터들의 선형결합 형태인 벡터 방정식으로 나타내시오.\nA = {{ A }}, b = {{ b }}",
        "latex": r"A={{ A }},\quad \mathbf{b}={{ b }}",
        "builder_cas": "Eq(A*x, b)",
        "answer_cas": "Eq(A*x, b)",
        "answer_latex": r"x_1\mathbf{a}_1+\cdots+x_n\mathbf{a}_n=\mathbf{b}",
        "solution_strategy": "rule_based_steps",
        "validators": ["symbolic_equivalence"],
    },
    "ero_application": {
        "answer_type": "matrix",
        "parameters": {
            "A": p("matrix", "기본행연산을 적용할 행렬.", min_=-6, max_=6),
            "target_row": p("integer", "변경할 행의 0-based 인덱스.", min_=0, max_=2),
            "source_row": p("integer", "더해 줄 행의 0-based 인덱스.", min_=0, max_=2),
            "c": p("integer", "R_target + c R_source에 사용할 0이 아닌 정수.", min_=-4, max_=4, exclude=[0]),
        },
        "constraints": [
            ("different_rows", "target_row", "not_equals", "source_row", "서로 다른 두 행을 사용한다."),
        ],
        "text": "행렬 A에 기본행연산 R_{{ target_row }} + ({{ c }})R_{{ source_row }} -> R_{{ target_row }} 를 적용한 결과를 구하시오.\nA = {{ A }}",
        "latex": r"R_{{ target_row }}+({{ c }})R_{{ source_row }}\to R_{{ target_row }}",
        "builder_cas": "A.elementary_row_op(op='n->n+km', row1=target_row, row2=source_row, k=c)",
        "answer_cas": "A.elementary_row_op(op='n->n+km', row1=target_row, row2=source_row, k=c)",
        "answer_latex": r"\operatorname{ERO}(A)",
        "solution_strategy": "rule_based_steps",
        "validators": ["matrix_equivalence"],
    },
    "ref_identification": {
        "answer_type": "boolean",
        "parameters": {"A": p("matrix", "REF 여부를 판정할 행렬.", min_=-5, max_=5)},
        "text": "다음 행렬 A가 행사다리꼴(REF)인지 판정하시오.\nA = {{ A }}",
        "latex": r"A={{ A }}\text{ 가 REF인가?}",
        "builder_cas": "is_ref(A)",
        "answer_cas": "is_ref(A)",
        "answer_latex": r"\mathrm{True}\;\text{or}\;\mathrm{False}",
        "solution_strategy": "rule_based_steps",
        "validators": ["ref_form_check"],
    },
    "rref_calculation": {
        "answer_type": "matrix",
        "parameters": {"A": p("matrix", "RREF를 구할 행렬.", min_=-6, max_=6)},
        "text": "다음 행렬 A의 기약행사다리꼴(RREF)을 구하시오.\nA = {{ A }}",
        "latex": r"\operatorname{RREF}({{ A }})",
        "builder_cas": "A.rref()[0]",
        "answer_cas": "A.rref()[0]",
        "answer_latex": r"\operatorname{RREF}(A)",
        "solution_strategy": "rule_based_steps",
        "validators": ["rref_form_check"],
    },
    "consistency_check": {
        "answer_type": "single_choice",
        "parameters": {"Aug": p("matrix", "연립방정식의 첨가행렬 [A|b].", min_=-6, max_=6)},
        "text": "다음 첨가행렬이 나타내는 연립일차방정식의 해 존재 여부를 판정하시오. (해 없음 / 해 존재)\n[A|b] = {{ Aug }}",
        "latex": r"[A\mid\mathbf b]={{ Aug }}",
        "builder_cas": "is_consistent_augmented(Aug)",
        "answer_cas": "'해 존재' if is_consistent_augmented(Aug) else '해 없음'",
        "answer_latex": r"\text{해 존재 여부}",
        "solution_strategy": "rule_based_steps",
        "validators": ["consistency_theorem_check"],
    },
    "rank_calculation": {
        "answer_type": "scalar",
        "parameters": {"A": p("matrix", "랭크를 계산할 행렬.", min_=-6, max_=6)},
        "text": "다음 행렬 A의 랭크(rank)를 구하시오.\nA = {{ A }}",
        "latex": r"\operatorname{rank}({{ A }})",
        "builder_cas": "A.rank()",
        "answer_cas": "A.rank()",
        "answer_latex": r"\operatorname{rank}(A)",
        "solution_strategy": "rule_based_steps",
        "validators": ["rank_computation_check"],
    },
    "matrix_rank_property": {
        "answer_type": "scalar",
        "parameters": {
            "m": p("integer", "행렬의 행 개수.", min_=1, max_=6),
            "n": p("integer", "행렬의 열 개수.", min_=1, max_=6),
        },
        "text": "m={{ m }}, n={{ n }}일 때 m x n 행렬이 가질 수 있는 최대 랭크를 구하시오.",
        "latex": r"\max\operatorname{rank}(A),\quad A\in\mathbb{R}^{ {{ m }}\times {{ n }} }",
        "builder_cas": "Min(m, n)",
        "answer_cas": "Min(m, n)",
        "answer_latex": r"\min(m,n)",
        "solution_strategy": "formula_substitution",
        "validators": ["rank_computation_check"],
    },
    "free_variable_identification": {
        "answer_type": "vector_expression",
        "parameters": {"A": p("matrix", "자유변수를 식별할 계수행렬.", min_=-5, max_=5)},
        "text": "행렬 A의 RREF를 기준으로 자유변수에 해당하는 열의 인덱스를 구하시오.\nA = {{ A }}",
        "latex": r"A={{ A }}",
        "builder_cas": "free_variable_indices(A)",
        "answer_cas": "free_variable_indices(A)",
        "answer_latex": r"\{j\mid j\text{ is a non-pivot column}\}",
        "solution_strategy": "rule_based_steps",
        "validators": ["null_space_check"],
    },
    "parametric_solution_extraction": {
        "answer_type": "vector_expression",
        "parameters": {
            "A": p("matrix", "일관된 연립방정식의 계수행렬.", min_=-5, max_=5),
            "b": p("vector", "우변 벡터.", min_=-8, max_=8),
        },
        "text": "연립방정식 A x = b의 해를 벡터 매개변수형으로 나타내시오.\nA = {{ A }}, b = {{ b }}",
        "latex": r"A\mathbf{x}=\mathbf b,\quad A={{ A }},\;\mathbf b={{ b }}",
        "builder_cas": "linsolve((A, b))",
        "answer_cas": "linsolve((A, b))",
        "answer_latex": r"\mathbf{x}=\mathbf{x}_p+t_1\mathbf v_1+\cdots+t_k\mathbf v_k",
        "solution_strategy": "symbolic_derivation",
        "validators": ["linear_combination_equivalence", "null_space_check"],
    },
    "matrix_multiplication": {
        "answer_type": "matrix",
        "parameters": {
            "A": p("matrix", "왼쪽 행렬. A의 열 수와 B의 행 수가 일치해야 한다.", min_=-5, max_=5),
            "B": p("matrix", "오른쪽 행렬. A의 열 수와 B의 행 수가 일치해야 한다.", min_=-5, max_=5),
        },
        "text": "다음 두 행렬의 곱 AB를 구하시오.\nA = {{ A }}, B = {{ B }}",
        "latex": r"{{ A }}{{ B }}",
        "builder_cas": "A*B",
        "answer_cas": "A*B",
        "answer_latex": r"AB",
        "solution_strategy": "formula_substitution",
        "validators": ["matrix_equivalence"],
    },
    "algebraic_expansion_verification": {
        "answer_type": "expression",
        "parameters": {
            "A": p("matrix", "정사각행렬 A.", min_=-4, max_=4),
            "B": p("matrix", "A와 같은 크기의 정사각행렬 B.", min_=-4, max_=4),
        },
        "text": "행렬 곱셈의 비교환성을 고려하여 (A+B)^2를 전개하시오.",
        "latex": r"(A+B)^2",
        "builder_cas": "A*A + A*B + B*A + B*B",
        "answer_cas": "A*A + A*B + B*A + B*B",
        "answer_latex": r"A^2+AB+BA+B^2",
        "solution_strategy": "symbolic_derivation",
        "validators": ["symbolic_noncommutative_expansion"],
    },
    "transpose_algebra": {
        "answer_type": "matrix",
        "parameters": {
            "A": p("matrix", "행렬 A.", min_=-5, max_=5),
            "B": p("matrix", "곱 AB가 정의되도록 크기를 맞춘 행렬 B.", min_=-5, max_=5),
        },
        "text": "주어진 A, B에 대하여 (AB)^T를 계산하시오.\nA = {{ A }}, B = {{ B }}",
        "latex": r"(AB)^T",
        "builder_cas": "(A*B).T",
        "answer_cas": "B.T*A.T",
        "answer_latex": r"B^T A^T",
        "solution_strategy": "formula_substitution",
        "validators": ["matrix_equivalence"],
    },
    "symmetry_classification": {
        "answer_type": "boolean",
        "parameters": {"A": p("matrix", "대칭 여부를 판정할 정사각행렬.", min_=-5, max_=5)},
        "text": "다음 행렬 A가 대칭행렬인지 판정하시오.\nA = {{ A }}",
        "latex": r"A^T=A\;?",
        "builder_cas": "A.T == A",
        "answer_cas": "A.T == A",
        "answer_latex": r"A^T=A",
        "solution_strategy": "rule_based_steps",
        "validators": ["matrix_equivalence"],
    },
    "inverse_calculation": {
        "answer_type": "matrix",
        "parameters": {"A": p("matrix", "역행렬이 존재하는 정사각행렬.", min_=-5, max_=5)},
        "text": "가우스-조르당 소거법을 이용하여 다음 행렬 A의 역행렬을 구하시오.\nA = {{ A }}",
        "latex": r"A^{-1},\quad A={{ A }}",
        "builder_cas": "A.inv()",
        "answer_cas": "A.inv()",
        "answer_latex": r"A^{-1}",
        "solution_strategy": "rule_based_steps",
        "constraints": [("nonsingular", "det(A)", "not_equals", 0, "역행렬이 존재하도록 det(A) != 0을 만족해야 한다.")],
        "validators": ["matrix_inverse_check"],
    },
    "singular_matrix_identification": {
        "answer_type": "boolean",
        "parameters": {"A": p("matrix", "특이 여부를 판정할 정사각행렬.", min_=-5, max_=5)},
        "text": "다음 행렬 A가 특이행렬(singular matrix)인지 판정하시오.\nA = {{ A }}",
        "latex": r"\det(A)=0\;?",
        "builder_cas": "A.det() == 0",
        "answer_cas": "A.det() == 0",
        "answer_latex": r"\det(A)=0",
        "solution_strategy": "rule_based_steps",
        "validators": ["zero_row_detection"],
    },
    "equivalence_theorem_check": {
        "answer_type": "boolean",
        "parameters": {"A": p("matrix", "IMT 조건을 확인할 정사각행렬.", min_=-5, max_=5)},
        "text": "정사각행렬 A에 대해 가역행렬 정리(IMT)의 동치 조건들이 참인지 판정하시오.\nA = {{ A }}",
        "latex": r"A\text{ invertible}\iff\operatorname{rank}(A)=n\iff\det(A)\ne0",
        "builder_cas": "A.det() != 0",
        "answer_cas": "A.det() != 0",
        "answer_latex": r"\mathrm{True}\;\text{or}\;\mathrm{False}",
        "solution_strategy": "rule_based_steps",
        "validators": ["logical_equivalence_check"],
    },
    "invertibility_determination": {
        "answer_type": "multiple_choice",
        "parameters": {"A": p("matrix", "가역성을 판정할 정사각행렬.", min_=-5, max_=5)},
        "text": "다음 행렬 A의 가역성에 대한 옳은 선택지를 고르시오.\nA = {{ A }}",
        "latex": r"A={{ A }}",
        "builder_cas": "'가역' if A.det() != 0 else '비가역'",
        "answer_cas": "'가역' if A.det() != 0 else '비가역'",
        "answer_latex": r"\text{가역 또는 비가역}",
        "solution_strategy": "rule_based_steps",
        "context_templates": ["선택지: 가역 / 비가역"],
        "validators": ["logical_equivalence_check"],
    },
    "elementary_matrix_construction": {
        "answer_type": "matrix",
        "parameters": {
            "n": p("integer", "기본행렬의 차원.", min_=2, max_=4),
            "target_row": p("integer", "변경할 행의 0-based 인덱스.", min_=0, max_=3),
            "source_row": p("integer", "더해 줄 행의 0-based 인덱스.", min_=0, max_=3),
            "c": p("integer", "행 가산 계수.", min_=-4, max_=4, exclude=[0]),
        },
        "constraints": [("different_rows", "target_row", "not_equals", "source_row", "서로 다른 행을 사용한다.")],
        "text": "n={{ n }}일 때 행연산 R_{{ target_row }} + ({{ c }})R_{{ source_row }} -> R_{{ target_row }} 에 대응하는 기본행렬 E를 구하시오.",
        "latex": r"R_{{ target_row }}+({{ c }})R_{{ source_row }}\to R_{{ target_row }}",
        "builder_cas": "eye(n).elementary_row_op(op='n->n+km', row1=target_row, row2=source_row, k=c)",
        "answer_cas": "eye(n).elementary_row_op(op='n->n+km', row1=target_row, row2=source_row, k=c)",
        "answer_latex": r"E",
        "solution_strategy": "rule_based_steps",
        "validators": ["matrix_equivalence"],
    },
    "elementary_inverse_calculation": {
        "answer_type": "matrix",
        "parameters": {"E": p("matrix", "역행렬을 구할 기본행렬.", min_=-4, max_=4)},
        "text": "다음 기본행렬 E의 역행렬 E^{-1}을 구하시오.\nE = {{ E }}",
        "latex": r"E^{-1},\quad E={{ E }}",
        "builder_cas": "E.inv()",
        "answer_cas": "E.inv()",
        "answer_latex": r"E^{-1}",
        "solution_strategy": "rule_based_steps",
        "validators": ["matrix_equivalence"],
    },
    "lu_factorization": {
        "answer_type": "matrix",
        "parameters": {"A": p("matrix", "행 교환 없이 LU 분해가 가능한 정사각행렬.", min_=-5, max_=5)},
        "text": "다음 행렬 A를 A=LU 형태로 분해하시오. 정답은 [L | U] 형태의 블록 행렬로 제출하시오.\nA = {{ A }}",
        "latex": r"A=LU,\quad A={{ A }}",
        "builder_cas": "Matrix.hstack(A.LUdecomposition()[0], A.LUdecomposition()[1])",
        "answer_cas": "Matrix.hstack(A.LUdecomposition()[0], A.LUdecomposition()[1])",
        "answer_latex": r"[L\mid U]",
        "solution_strategy": "rule_based_steps",
        "validators": ["matrix_multiplication_check", "lower_triangular_check"],
    },
    "solve_by_lu": {
        "answer_type": "vector",
        "parameters": {
            "A": p("matrix", "LU 분해 가능한 정사각행렬.", min_=-5, max_=5),
            "b": p("vector", "우변 벡터.", min_=-8, max_=8),
        },
        "text": "LU 분해와 전진/후진대입을 사용하여 A x = b의 해 x를 구하시오.\nA = {{ A }}, b = {{ b }}",
        "latex": r"A\mathbf{x}=\mathbf b",
        "builder_cas": "A.LUsolve(b)",
        "answer_cas": "A.LUsolve(b)",
        "answer_latex": r"\mathbf{x}",
        "solution_strategy": "rule_based_steps",
        "constraints": [("nonsingular", "det(A)", "not_equals", 0, "유일해가 존재하도록 det(A) != 0을 만족해야 한다.")],
        "validators": ["matrix_multiplication_check"],
    },
}



# -----------------------------------------------------------------------------
# Additional blueprints for la_02 ~ la_05
# -----------------------------------------------------------------------------
BLUEPRINTS.update(
{'subspace_verification': {'answer_type': 'boolean',
                           'parameters': {'A': {'type': 'matrix',
                                                'required': True,
                                                'min': -5,
                                                'max': 5,
                                                'exclude': [],
                                                'choices': [],
                                                'step': None,
                                                'distribution': 'uniform',
                                                'description': '동차 선형 제약 Ax=0을 정의하는 행렬.'},
                                          'b': {'type': 'vector',
                                                'required': True,
                                                'min': -5,
                                                'max': 5,
                                                'exclude': [],
                                                'choices': [],
                                                'step': None,
                                                'distribution': 'uniform',
                                                'description': '집합을 Ax=b 형태로 제시할 때의 상수벡터.'}},
                           'text': '집합 H = {x | A x = b}가 R^n의 부분공간인지 판정하시오.\nA = {{ A }}, b = {{ b }}',
                           'latex': 'H=\\{\\mathbf{x}\\mid A\\mathbf{x}=\\mathbf{b}\\}',
                           'builder_cas': 'is_subspace_solution_set(A, b)',
                           'answer_cas': 'is_subspace_solution_set(A, b)',
                           'answer_latex': '\\mathrm{True}\\;\\text{or}\\;\\mathrm{False}',
                           'solution_strategy': 'rule_based_steps',
                           'validators': ['subspace_axiom_check']},
 'span_membership_test': {'answer_type': 'boolean',
                          'parameters': {'V': {'type': 'matrix',
                                               'required': True,
                                               'min': -5,
                                               'max': 5,
                                               'exclude': [],
                                               'choices': [],
                                               'step': None,
                                               'distribution': 'uniform',
                                               'description': '생성 벡터들을 열벡터로 갖는 행렬.'},
                                         'b': {'type': 'vector',
                                               'required': True,
                                               'min': -7,
                                               'max': 7,
                                               'exclude': [],
                                               'choices': [],
                                               'step': None,
                                               'distribution': 'uniform',
                                               'description': 'Span 포함 여부를 검사할 대상 벡터.'}},
                          'text': '벡터 b가 V의 열벡터들이 생성하는 Span에 속하는지 판정하시오.\nV = {{ V }}, b = {{ b }}',
                          'latex': '\\mathbf b\\in\\operatorname{Span}(V)\\;?',
                          'builder_cas': 'is_consistent(V, b)',
                          'answer_cas': 'is_consistent(V, b)',
                          'answer_latex': '\\mathrm{True}\\;\\text{or}\\;\\mathrm{False}',
                          'solution_strategy': 'rule_based_steps',
                          'validators': ['consistency_theorem_check']},
 'linear_independence_test': {'answer_type': 'boolean',
                              'parameters': {'V': {'type': 'matrix',
                                                   'required': True,
                                                   'min': -5,
                                                   'max': 5,
                                                   'exclude': [],
                                                   'choices': [],
                                                   'step': None,
                                                   'distribution': 'uniform',
                                                   'description': '검사할 벡터들을 열벡터로 갖는 행렬.'}},
                              'text': '행렬 V의 열벡터들이 선형독립인지 판정하시오.\nV = {{ V }}',
                              'latex': '\\operatorname{rank}(V)=\\text{number of columns}\\;?',
                              'builder_cas': 'V.rank() == V.cols',
                              'answer_cas': 'V.rank() == V.cols',
                              'answer_latex': '\\mathrm{True}\\;\\text{or}\\;\\mathrm{False}',
                              'solution_strategy': 'rule_based_steps',
                              'validators': ['rank_matrix_check']},
 'basis_verification': {'answer_type': 'boolean',
                        'parameters': {'V': {'type': 'matrix',
                                             'required': True,
                                             'min': -5,
                                             'max': 5,
                                             'exclude': [],
                                             'choices': [],
                                             'step': None,
                                             'distribution': 'uniform',
                                             'description': '후보 기저 벡터들을 열벡터로 갖는 행렬.'},
                                       'n': {'type': 'integer',
                                             'required': True,
                                             'min': 1,
                                             'max': 5,
                                             'exclude': [],
                                             'choices': [],
                                             'step': None,
                                             'distribution': 'uniform',
                                             'description': '목표 공간 R^n의 차원.'}},
                        'text': 'V의 열벡터들이 R^{{ n }}의 기저인지 판정하시오.\nV = {{ V }}',
                        'latex': '\\operatorname{Basis}(\\mathbb{R}^{ {{ n }} })\\;?',
                        'builder_cas': 'V.rows == n and V.cols == n and V.rank() == n',
                        'answer_cas': 'V.rows == n and V.cols == n and V.rank() == n',
                        'answer_latex': '\\mathrm{True}\\;\\text{or}\\;\\mathrm{False}',
                        'solution_strategy': 'rule_based_steps',
                        'validators': ['rank_matrix_check']},
 'column_space_basis': {'answer_type': 'vector_list',
                        'parameters': {'A': {'type': 'matrix',
                                             'required': True,
                                             'min': -5,
                                             'max': 5,
                                             'exclude': [],
                                             'choices': [],
                                             'step': None,
                                             'distribution': 'uniform',
                                             'description': '열공간의 기저를 구할 행렬.'}},
                        'text': '행렬 A의 열공간 C(A)의 기저를 구하시오.\nA = {{ A }}',
                        'latex': '\\operatorname{Basis}(C(A))',
                        'builder_cas': 'A.columnspace()',
                        'answer_cas': 'A.columnspace()',
                        'answer_latex': '\\operatorname{Basis}(C(A))',
                        'solution_strategy': 'rule_based_steps',
                        'validators': ['span_equivalence_check']},
 'row_space_basis': {'answer_type': 'vector_list',
                     'parameters': {'A': {'type': 'matrix',
                                          'required': True,
                                          'min': -5,
                                          'max': 5,
                                          'exclude': [],
                                          'choices': [],
                                          'step': None,
                                          'distribution': 'uniform',
                                          'description': '행공간의 기저를 구할 행렬.'}},
                     'text': '행렬 A의 행공간 Row(A)의 기저를 구하시오.\nA = {{ A }}',
                     'latex': '\\operatorname{Basis}(\\operatorname{Row}(A))',
                     'builder_cas': 'A.rowspace()',
                     'answer_cas': 'A.rowspace()',
                     'answer_latex': '\\operatorname{Basis}(\\operatorname{Row}(A))',
                     'solution_strategy': 'rule_based_steps',
                     'validators': ['span_equivalence_check']},
 'null_space_basis': {'answer_type': 'vector_list',
                      'parameters': {'A': {'type': 'matrix',
                                           'required': True,
                                           'min': -5,
                                           'max': 5,
                                           'exclude': [],
                                           'choices': [],
                                           'step': None,
                                           'distribution': 'uniform',
                                           'description': '영공간의 기저를 구할 행렬.'}},
                      'text': '행렬 A의 영공간 N(A)의 기저를 구하시오.\nA = {{ A }}',
                      'latex': '\\operatorname{Basis}(N(A))',
                      'builder_cas': 'A.nullspace()',
                      'answer_cas': 'A.nullspace()',
                      'answer_latex': '\\operatorname{Basis}(N(A))',
                      'solution_strategy': 'rule_based_steps',
                      'validators': ['matrix_multiplication_zero_check']},
 'left_null_space_basis': {'answer_type': 'vector_list',
                           'parameters': {'A': {'type': 'matrix',
                                                'required': True,
                                                'min': -5,
                                                'max': 5,
                                                'exclude': [],
                                                'choices': [],
                                                'step': None,
                                                'distribution': 'uniform',
                                                'description': '좌영공간의 기저를 구할 행렬.'}},
                           'text': '행렬 A의 좌영공간 N(A^T)의 기저를 구하시오.\nA = {{ A }}',
                           'latex': '\\operatorname{Basis}(N(A^T))',
                           'builder_cas': 'A.T.nullspace()',
                           'answer_cas': 'A.T.nullspace()',
                           'answer_latex': '\\operatorname{Basis}(N(A^T))',
                           'solution_strategy': 'rule_based_steps',
                           'validators': ['matrix_multiplication_zero_check']},
 'rank_nullity_calculation': {'answer_type': 'scalar',
                              'parameters': {'A': {'type': 'matrix',
                                                   'required': True,
                                                   'min': -5,
                                                   'max': 5,
                                                   'exclude': [],
                                                   'choices': [],
                                                   'step': None,
                                                   'distribution': 'uniform',
                                                   'description': 'nullity를 계산할 행렬.'}},
                              'text': '행렬 A에 대해 nullity(A)를 구하시오.\nA = {{ A }}',
                              'latex': '\\operatorname{nullity}(A)=n-\\operatorname{rank}(A)',
                              'builder_cas': 'A.cols - A.rank()',
                              'answer_cas': 'A.cols - A.rank()',
                              'answer_latex': 'n-\\operatorname{rank}(A)',
                              'solution_strategy': 'formula_substitution',
                              'validators': ['dimension_equality_check']},
 'change_of_basis_calculation': {'answer_type': 'matrix',
                                 'parameters': {'B': {'type': 'matrix',
                                                      'required': True,
                                                      'min': -4,
                                                      'max': 4,
                                                      'exclude': [],
                                                      'choices': [],
                                                      'step': None,
                                                      'distribution': 'uniform',
                                                      'description': '기존 기저를 열벡터로 갖는 가역행렬.'},
                                                'C': {'type': 'matrix',
                                                      'required': True,
                                                      'min': -4,
                                                      'max': 4,
                                                      'exclude': [],
                                                      'choices': [],
                                                      'step': None,
                                                      'distribution': 'uniform',
                                                      'description': '새 기저를 열벡터로 갖는 가역행렬.'}},
                                 'constraints': [('basis_B_invertible',
                                                  'det(B)',
                                                  'not_equals',
                                                  0,
                                                  'B는 기저 행렬이므로 가역이어야 한다.'),
                                                 ('basis_C_invertible',
                                                  'det(C)',
                                                  'not_equals',
                                                  0,
                                                  'C는 기저 행렬이므로 가역이어야 한다.')],
                                 'text': '기저 B에서 기저 C로 좌표를 변환하는 전이행렬 P_(C<-B)를 구하시오.\nB = {{ B }}, C = {{ C }}',
                                 'latex': 'P_{C\\leftarrow B}=C^{-1}B',
                                 'builder_cas': 'C.inv()*B',
                                 'answer_cas': 'C.inv()*B',
                                 'answer_latex': 'C^{-1}B',
                                 'solution_strategy': 'formula_substitution',
                                 'validators': ['matrix_inverse_check']},
 'linear_transformation_verification': {'answer_type': 'boolean',
                                        'parameters': {'A': {'type': 'matrix',
                                                             'required': True,
                                                             'min': -5,
                                                             'max': 5,
                                                             'exclude': [],
                                                             'choices': [],
                                                             'step': None,
                                                             'distribution': 'uniform',
                                                             'description': '선형 부분을 나타내는 행렬.'},
                                                       'b': {'type': 'vector',
                                                             'required': True,
                                                             'min': -3,
                                                             'max': 3,
                                                             'exclude': [],
                                                             'choices': [],
                                                             'step': None,
                                                             'distribution': 'uniform',
                                                             'description': '아핀 평행이동 항. b=0일 때만 T(x)=Ax+b가 선형.'}},
                                        'text': '변환 T(x)=Ax+b가 선형변환인지 판정하시오.\nA = {{ A }}, b = {{ b }}',
                                        'latex': 'T(\\mathbf{x})=A\\mathbf{x}+\\mathbf{b}',
                                        'builder_cas': 'is_zero_vector(b)',
                                        'answer_cas': 'is_zero_vector(b)',
                                        'answer_latex': 'T(\\mathbf 0)=\\mathbf 0',
                                        'solution_strategy': 'rule_based_steps',
                                        'validators': ['superposition_check']},
 'standard_matrix_derivation': {'answer_type': 'matrix',
                                'parameters': {'images': {'type': 'matrix',
                                                          'required': True,
                                                          'min': -5,
                                                          'max': 5,
                                                          'exclude': [],
                                                          'choices': [],
                                                          'step': None,
                                                          'distribution': 'uniform',
                                                          'description': '표준기저 e_i의 상 T(e_i)를 열벡터로 모은 행렬.'}},
                                'text': '표준기저벡터들의 상이 열벡터로 주어졌을 때 선형변환 T의 표준행렬을 구하시오.\n[T(e1) ... T(en)] = {{ images }}',
                                'latex': 'A=[T(\\mathbf e_1)\\ \\cdots\\ T(\\mathbf e_n)]',
                                'builder_cas': 'images',
                                'answer_cas': 'images',
                                'answer_latex': '[T(\\mathbf e_1)\\ \\cdots\\ T(\\mathbf e_n)]',
                                'solution_strategy': 'formula_substitution',
                                'validators': ['matrix_multiplication_check']},
 'kernel_image_calculation': {'answer_type': 'vector_list',
                              'parameters': {'A': {'type': 'matrix',
                                                   'required': True,
                                                   'min': -5,
                                                   'max': 5,
                                                   'exclude': [],
                                                   'choices': [],
                                                   'step': None,
                                                   'distribution': 'uniform',
                                                   'description': '선형변환 T(x)=Ax의 표준행렬.'}},
                              'text': 'T(x)=Ax에 대해 Ker(T)의 기저와 Im(T)의 기저를 구하시오.\nA = {{ A }}',
                              'latex': '\\operatorname{Ker}(T)=N(A),\\quad \\operatorname{Im}(T)=C(A)',
                              'builder_cas': '(A.nullspace(), A.columnspace())',
                              'answer_cas': '(A.nullspace(), A.columnspace())',
                              'answer_latex': '\\big(\\operatorname{Basis}N(A),\\operatorname{Basis}C(A)\\big)',
                              'solution_strategy': 'rule_based_steps',
                              'validators': ['rank_nullity_check']},
 'determinant_cofactor_expansion': {'answer_type': 'scalar',
                                    'parameters': {'A': {'type': 'matrix',
                                                         'required': True,
                                                         'min': -5,
                                                         'max': 5,
                                                         'exclude': [],
                                                         'choices': [],
                                                         'step': None,
                                                         'distribution': 'uniform',
                                                         'description': '여인수 전개로 행렬식을 구할 정사각행렬.'}},
                                    'text': '여인수 전개를 이용하여 det(A)를 구하시오.\nA = {{ A }}',
                                    'latex': '\\det(A)',
                                    'builder_cas': 'A.det()',
                                    'answer_cas': 'A.det()',
                                    'answer_latex': '\\det(A)',
                                    'solution_strategy': 'symbolic_derivation',
                                    'validators': ['determinant_check']},
 'determinant_by_ero': {'answer_type': 'scalar',
                        'parameters': {'A': {'type': 'matrix',
                                             'required': True,
                                             'min': -5,
                                             'max': 5,
                                             'exclude': [],
                                             'choices': [],
                                             'step': None,
                                             'distribution': 'uniform',
                                             'description': '기본행연산을 이용해 행렬식을 구할 정사각행렬.'}},
                        'text': '기본행연산과 행렬식의 변화 규칙을 이용하여 det(A)를 구하시오.\nA = {{ A }}',
                        'latex': '\\det(A)',
                        'builder_cas': 'A.det()',
                        'answer_cas': 'A.det()',
                        'answer_latex': '\\det(A)',
                        'solution_strategy': 'rule_based_steps',
                        'validators': ['determinant_check']},
 'block_matrix_determinant': {'answer_type': 'scalar',
                              'parameters': {'B': {'type': 'matrix',
                                                   'required': True,
                                                   'min': -4,
                                                   'max': 4,
                                                   'exclude': [],
                                                   'choices': [],
                                                   'step': None,
                                                   'distribution': 'uniform',
                                                   'description': '블록 대각행렬의 첫 번째 정사각 블록.'},
                                             'C': {'type': 'matrix',
                                                   'required': True,
                                                   'min': -4,
                                                   'max': 4,
                                                   'exclude': [],
                                                   'choices': [],
                                                   'step': None,
                                                   'distribution': 'uniform',
                                                   'description': '블록 대각행렬의 두 번째 정사각 블록.'}},
                              'text': '블록 대각행렬 A = diag(B,C)의 행렬식을 구하시오.\nB = {{ B }}, C = {{ C }}',
                              'latex': '\\det\\begin{bmatrix}B&0\\\\0&C\\end{bmatrix}',
                              'builder_cas': 'B.det()*C.det()',
                              'answer_cas': 'B.det()*C.det()',
                              'answer_latex': '\\det(B)\\det(C)',
                              'solution_strategy': 'formula_substitution',
                              'validators': ['determinant_check']},
 'cramer_rule_solution': {'answer_type': 'vector',
                          'parameters': {'A': {'type': 'matrix',
                                               'required': True,
                                               'min': -5,
                                               'max': 5,
                                               'exclude': [],
                                               'choices': [],
                                               'step': None,
                                               'distribution': 'uniform',
                                               'description': 'Cramer 법칙을 적용할 가역 정사각행렬.'},
                                         'b': {'type': 'vector',
                                               'required': True,
                                               'min': -8,
                                               'max': 8,
                                               'exclude': [],
                                               'choices': [],
                                               'step': None,
                                               'distribution': 'uniform',
                                               'description': '우변 벡터.'}},
                          'constraints': [('cramer_nonsingular',
                                           'det(A)',
                                           'not_equals',
                                           0,
                                           'Cramer 법칙 적용을 위해 A는 가역이어야 한다.')],
                          'text': 'Cramer 법칙을 이용하여 A x = b의 해 x를 구하시오.\nA = {{ A }}, b = {{ b }}',
                          'latex': 'x_i=\\frac{\\det(A_i)}{\\det(A)}',
                          'builder_cas': 'A.LUsolve(b)',
                          'answer_cas': 'A.LUsolve(b)',
                          'answer_latex': '\\mathbf x',
                          'solution_strategy': 'formula_substitution',
                          'validators': ['cramer_solution_check']},
 'geometric_area_volume_calculation': {'answer_type': 'scalar',
                                       'parameters': {'A': {'type': 'matrix',
                                                            'required': True,
                                                            'min': -5,
                                                            'max': 5,
                                                            'exclude': [],
                                                            'choices': [],
                                                            'step': None,
                                                            'distribution': 'uniform',
                                                            'description': '열벡터들이 평행사변형/평행육면체를 생성하는 정사각행렬.'}},
                                       'text': 'A의 열벡터들이 생성하는 평행사변형 또는 평행육면체의 넓이/부피를 구하시오.\nA = {{ A }}',
                                       'latex': '|\\det(A)|',
                                       'builder_cas': 'Abs(A.det())',
                                       'answer_cas': 'Abs(A.det())',
                                       'answer_latex': '|\\det(A)|',
                                       'solution_strategy': 'formula_substitution',
                                       'validators': ['absolute_value_check']},
 'norm_distance_calculation': {'answer_type': 'scalar',
                               'parameters': {'u': {'type': 'vector',
                                                    'required': True,
                                                    'min': -6,
                                                    'max': 6,
                                                    'exclude': [],
                                                    'choices': [],
                                                    'step': None,
                                                    'distribution': 'uniform',
                                                    'description': '첫 번째 벡터.'},
                                              'v': {'type': 'vector',
                                                    'required': True,
                                                    'min': -6,
                                                    'max': 6,
                                                    'exclude': [],
                                                    'choices': [],
                                                    'step': None,
                                                    'distribution': 'uniform',
                                                    'description': '두 번째 벡터. u와 같은 차원.'}},
                               'text': '두 벡터 u, v 사이의 유클리드 거리를 구하시오.\nu = {{ u }}, v = {{ v }}',
                               'latex': '\\|\\mathbf u-\\mathbf v\\|',
                               'builder_cas': '(u-v).norm()',
                               'answer_cas': '(u-v).norm()',
                               'answer_latex': '\\|\\mathbf u-\\mathbf v\\|',
                               'solution_strategy': 'formula_substitution',
                               'validators': ['scalar_equality_check']},
 'orthogonal_complement_calculation': {'answer_type': 'vector_list',
                                       'parameters': {'W': {'type': 'matrix',
                                                            'required': True,
                                                            'min': -5,
                                                            'max': 5,
                                                            'exclude': [],
                                                            'choices': [],
                                                            'step': None,
                                                            'distribution': 'uniform',
                                                            'description': '부분공간 W의 기저 벡터들을 열벡터로 갖는 행렬.'}},
                                       'text': 'W의 열벡터들이 생성하는 부분공간의 직교 여공간 W^perp의 기저를 구하시오.\nW = {{ W }}',
                                       'latex': 'W^\\perp=N(W^T)',
                                       'builder_cas': 'W.T.nullspace()',
                                       'answer_cas': 'W.T.nullspace()',
                                       'answer_latex': '\\operatorname{Basis}(W^\\perp)',
                                       'solution_strategy': 'rule_based_steps',
                                       'validators': ['dot_product_zero_check']},
 'orthonormal_verification': {'answer_type': 'boolean',
                              'parameters': {'Q': {'type': 'matrix',
                                                   'required': True,
                                                   'min': -3,
                                                   'max': 3,
                                                   'exclude': [],
                                                   'choices': [],
                                                   'step': None,
                                                   'distribution': 'uniform',
                                                   'description': '열벡터 집합의 정규직교성을 검사할 행렬.'}},
                              'text': 'Q의 열벡터들이 정규직교집합인지 판정하시오.\nQ = {{ Q }}',
                              'latex': 'Q^TQ=I\\;?',
                              'builder_cas': 'Q.T*Q == eye(Q.cols)',
                              'answer_cas': 'Q.T*Q == eye(Q.cols)',
                              'answer_latex': 'Q^TQ=I',
                              'solution_strategy': 'rule_based_steps',
                              'validators': ['matrix_product_identity_check']},
 'orthogonal_projection_calculation': {'answer_type': 'vector',
                                       'parameters': {'a': {'type': 'vector',
                                                            'required': True,
                                                            'min': -6,
                                                            'max': 6,
                                                            'exclude': [],
                                                            'choices': [],
                                                            'step': None,
                                                            'distribution': 'uniform',
                                                            'description': '사영할 벡터.'},
                                                      'b': {'type': 'vector',
                                                            'required': True,
                                                            'min': -6,
                                                            'max': 6,
                                                            'exclude': [],
                                                            'choices': [],
                                                            'step': None,
                                                            'distribution': 'uniform',
                                                            'description': '사영 대상 방향을 나타내는 0이 아닌 벡터.'}},
                                       'constraints': [('projection_nonzero_basis',
                                                        'b.dot(b)',
                                                        'greater_than',
                                                        0,
                                                        '사영 방향 벡터 b는 영벡터가 아니어야 한다.')],
                                       'text': '벡터 a를 벡터 b가 생성하는 직선 위로 직교사영한 proj_b(a)를 구하시오.\n'
                                               'a = {{ a }}, b = {{ b }}',
                                       'latex': '\\operatorname{proj}_{\\mathbf b}(\\mathbf a)=\\frac{\\mathbf '
                                                'a\\cdot\\mathbf b}{\\mathbf b\\cdot\\mathbf b}\\mathbf b',
                                       'builder_cas': '(a.dot(b)/b.dot(b))*b',
                                       'answer_cas': '(a.dot(b)/b.dot(b))*b',
                                       'answer_latex': '\\frac{\\mathbf a\\cdot\\mathbf b}{\\mathbf b\\cdot\\mathbf '
                                                       'b}\\mathbf b',
                                       'solution_strategy': 'formula_substitution',
                                       'validators': ['idempotent_symmetric_check']},
 'gram_schmidt_orthogonalization': {'answer_type': 'vector_list',
                                    'parameters': {'V': {'type': 'matrix',
                                                         'required': True,
                                                         'min': -4,
                                                         'max': 4,
                                                         'exclude': [],
                                                         'choices': [],
                                                         'step': None,
                                                         'distribution': 'uniform',
                                                         'description': '선형독립인 벡터들을 열벡터로 갖는 행렬.'}},
                                    'text': 'V의 열벡터들에 Gram-Schmidt 과정을 적용하여 정규직교 기저를 구하시오.\nV = {{ V }}',
                                    'latex': '\\operatorname{GramSchmidt}(V)',
                                    'builder_cas': 'gram_schmidt(V)',
                                    'answer_cas': 'gram_schmidt(V)',
                                    'answer_latex': '\\{\\mathbf q_1,\\ldots,\\mathbf q_k\\}',
                                    'solution_strategy': 'rule_based_steps',
                                    'validators': ['pairwise_orthogonality_check']},
 'qr_factorization_calculation': {'answer_type': 'matrix_pair',
                                  'parameters': {'A': {'type': 'matrix',
                                                       'required': True,
                                                       'min': -4,
                                                       'max': 4,
                                                       'exclude': [],
                                                       'choices': [],
                                                       'step': None,
                                                       'distribution': 'uniform',
                                                       'description': '열들이 선형독립인 QR 분해 대상 행렬.'}},
                                  'text': '행렬 A를 A=QR 형태로 QR 분해하시오.\nA = {{ A }}',
                                  'latex': 'A=QR',
                                  'builder_cas': 'A.QRdecomposition()',
                                  'answer_cas': 'A.QRdecomposition()',
                                  'answer_latex': '(Q,R)',
                                  'solution_strategy': 'rule_based_steps',
                                  'validators': ['qr_product_check']},
 'least_squares_calculation': {'answer_type': 'vector',
                               'parameters': {'A': {'type': 'matrix',
                                                    'required': True,
                                                    'min': -5,
                                                    'max': 5,
                                                    'exclude': [],
                                                    'choices': [],
                                                    'step': None,
                                                    'distribution': 'uniform',
                                                    'description': '과결정계의 설계행렬. 열랭크가 가득 차도록 생성한다.'},
                                              'b': {'type': 'vector',
                                                    'required': True,
                                                    'min': -8,
                                                    'max': 8,
                                                    'exclude': [],
                                                    'choices': [],
                                                    'step': None,
                                                    'distribution': 'uniform',
                                                    'description': '관측 벡터. A의 행 수와 같은 길이.'}},
                               'text': '과결정계 A x ≈ b의 최소제곱해 x_hat을 구하시오.\nA = {{ A }}, b = {{ b }}',
                               'latex': '\\hat{\\mathbf x}=(A^TA)^{-1}A^T\\mathbf b',
                               'builder_cas': '(A.T*A).inv()*A.T*b',
                               'answer_cas': '(A.T*A).inv()*A.T*b',
                               'answer_latex': '(A^TA)^{-1}A^T\\mathbf b',
                               'solution_strategy': 'formula_substitution',
                               'validators': ['normal_equation_residual_check']},
 'linear_regression_calculation': {'answer_type': 'vector',
                                   'parameters': {'X': {'type': 'matrix',
                                                        'required': True,
                                                        'min': -5,
                                                        'max': 5,
                                                        'exclude': [],
                                                        'choices': [],
                                                        'step': None,
                                                        'distribution': 'uniform',
                                                        'description': '첫 열이 1인 선형회귀 설계행렬.'},
                                                  'y': {'type': 'vector',
                                                        'required': True,
                                                        'min': -10,
                                                        'max': 10,
                                                        'exclude': [],
                                                        'choices': [],
                                                        'step': None,
                                                        'distribution': 'uniform',
                                                        'description': '반응변수 관측값.'}},
                                   'text': '설계행렬 X와 관측벡터 y에 대한 최소제곱 회귀계수 beta_hat을 구하시오.\nX = {{ X }}, y = {{ y }}',
                                   'latex': '\\hat{\\boldsymbol\\beta}=(X^TX)^{-1}X^T\\mathbf y',
                                   'builder_cas': '(X.T*X).inv()*X.T*y',
                                   'answer_cas': '(X.T*X).inv()*X.T*y',
                                   'answer_latex': '(X^TX)^{-1}X^T\\mathbf y',
                                   'solution_strategy': 'formula_substitution',
                                   'validators': ['regression_residual_check']},
 'eigenvalue_calculation': {'answer_type': 'scalar_list',
                            'parameters': {'A': {'type': 'matrix',
                                                 'required': True,
                                                 'min': -5,
                                                 'max': 5,
                                                 'exclude': [],
                                                 'choices': [],
                                                 'step': None,
                                                 'distribution': 'uniform',
                                                 'description': '고윳값을 계산할 정사각행렬.'}},
                            'text': '행렬 A의 고윳값들을 구하시오.\nA = {{ A }}',
                            'latex': '\\det(A-\\lambda I)=0',
                            'builder_cas': 'list(A.eigenvals().keys())',
                            'answer_cas': 'list(A.eigenvals().keys())',
                            'answer_latex': '\\{\\lambda_1,\\ldots,\\lambda_k\\}',
                            'solution_strategy': 'symbolic_derivation',
                            'validators': ['characteristic_polynomial_check']},
 'eigenvector_calculation': {'answer_type': 'vector_list',
                             'parameters': {'A': {'type': 'matrix',
                                                  'required': True,
                                                  'min': -5,
                                                  'max': 5,
                                                  'exclude': [],
                                                  'choices': [],
                                                  'step': None,
                                                  'distribution': 'uniform',
                                                  'description': '고유벡터를 계산할 정사각행렬.'},
                                            'lambda_val': {'type': 'integer',
                                                           'required': True,
                                                           'min': -8,
                                                           'max': 8,
                                                           'exclude': [],
                                                           'choices': [],
                                                           'step': None,
                                                           'distribution': 'uniform',
                                                           'description': 'A의 고윳값 중 하나.'}},
                             'text': '행렬 A의 고윳값 lambda={{ lambda_val }}에 대응하는 고유공간의 기저를 구하시오.\nA = {{ A }}',
                             'latex': 'N(A-\\lambda I)',
                             'builder_cas': '(A-lambda_val*eye(A.rows)).nullspace()',
                             'answer_cas': '(A-lambda_val*eye(A.rows)).nullspace()',
                             'answer_latex': '\\operatorname{Basis}(E_\\lambda)',
                             'solution_strategy': 'rule_based_steps',
                             'validators': ['matrix_multiplication_zero_check']},
 'matrix_diagonalization': {'answer_type': 'matrix_pair',
                            'parameters': {'A': {'type': 'matrix',
                                                 'required': True,
                                                 'min': -4,
                                                 'max': 4,
                                                 'exclude': [],
                                                 'choices': [],
                                                 'step': None,
                                                 'distribution': 'uniform',
                                                 'description': '대각화 가능한 정사각행렬.'}},
                            'text': '행렬 A를 A=PDP^{-1} 형태로 대각화하고 P와 D를 구하시오.\nA = {{ A }}',
                            'latex': 'A=PDP^{-1}',
                            'builder_cas': 'diagonalize_pair(A)',
                            'answer_cas': 'diagonalize_pair(A)',
                            'answer_latex': '(P,D)',
                            'solution_strategy': 'rule_based_steps',
                            'validators': ['matrix_equivalence']},
 'matrix_power_calculation': {'answer_type': 'matrix',
                              'parameters': {'A': {'type': 'matrix',
                                                   'required': True,
                                                   'min': -4,
                                                   'max': 4,
                                                   'exclude': [],
                                                   'choices': [],
                                                   'step': None,
                                                   'distribution': 'uniform',
                                                   'description': '거듭제곱을 계산할 대각화 가능한 정사각행렬.'},
                                             'k': {'type': 'integer',
                                                   'required': True,
                                                   'min': 2,
                                                   'max': 10,
                                                   'exclude': [],
                                                   'choices': [],
                                                   'step': None,
                                                   'distribution': 'uniform',
                                                   'description': '양의 정수 지수.'}},
                              'text': '대각화를 활용하여 A^{{ k }}를 구하시오.\nA = {{ A }}',
                              'latex': 'A^k=PD^kP^{-1}',
                              'builder_cas': 'A**k',
                              'answer_cas': 'A**k',
                              'answer_latex': 'A^k',
                              'solution_strategy': 'formula_substitution',
                              'validators': ['matrix_equivalence']},
 'orthogonal_diagonalization_calculation': {'answer_type': 'matrix_pair',
                                            'parameters': {'A': {'type': 'matrix',
                                                                 'required': True,
                                                                 'min': -4,
                                                                 'max': 4,
                                                                 'exclude': [],
                                                                 'choices': [],
                                                                 'step': None,
                                                                 'distribution': 'uniform',
                                                                 'description': '실수 대칭행렬.'}},
                                            'text': '실수 대칭행렬 A를 A=QDQ^T 형태로 직교대각화하고 Q와 D를 구하시오.\nA = {{ A }}',
                                            'latex': 'A=QDQ^T',
                                            'builder_cas': 'orthogonal_diagonalize_pair(A)',
                                            'answer_cas': 'orthogonal_diagonalize_pair(A)',
                                            'answer_latex': '(Q,D)',
                                            'solution_strategy': 'rule_based_steps',
                                            'validators': ['orthogonal_matrix_check']},
 'spectral_decomposition_calculation': {'answer_type': 'matrix_list',
                                        'parameters': {'A': {'type': 'matrix',
                                                             'required': True,
                                                             'min': -4,
                                                             'max': 4,
                                                             'exclude': [],
                                                             'choices': [],
                                                             'step': None,
                                                             'distribution': 'uniform',
                                                             'description': '스펙트럼 분해할 실수 대칭행렬.'}},
                                        'text': '실수 대칭행렬 A의 스펙트럼 분해 A = sum(lambda_i P_i)를 구하시오.\nA = {{ A }}',
                                        'latex': 'A=\\sum_i\\lambda_iP_i',
                                        'builder_cas': 'spectral_decomposition(A)',
                                        'answer_cas': 'spectral_decomposition(A)',
                                        'answer_latex': '\\{(\\lambda_i,P_i)\\}',
                                        'solution_strategy': 'symbolic_derivation',
                                        'validators': ['matrix_equivalence']},
 'quadratic_form_transformation': {'answer_type': 'expression',
                                   'parameters': {'A': {'type': 'matrix',
                                                        'required': True,
                                                        'min': -4,
                                                        'max': 4,
                                                        'exclude': [],
                                                        'choices': [],
                                                        'step': None,
                                                        'distribution': 'uniform',
                                                        'description': '이차형식 x^T A x를 정의하는 실수 대칭행렬.'}},
                                   'text': '대칭행렬 A가 정의하는 이차형식 x^T A x를 주축 좌표계에서 대각형식으로 나타내시오.\nA = {{ A }}',
                                   'latex': '\\mathbf x^TA\\mathbf x=\\mathbf y^TD\\mathbf y',
                                   'builder_cas': 'principal_axis_quadratic_form(A)',
                                   'answer_cas': 'principal_axis_quadratic_form(A)',
                                   'answer_latex': '\\sum_i\\lambda_i y_i^2',
                                   'solution_strategy': 'symbolic_derivation',
                                   'validators': ['quadratic_form_equivalence']},
 'positive_definite_test': {'answer_type': 'boolean',
                            'parameters': {'A': {'type': 'matrix',
                                                 'required': True,
                                                 'min': -4,
                                                 'max': 4,
                                                 'exclude': [],
                                                 'choices': [],
                                                 'step': None,
                                                 'distribution': 'uniform',
                                                 'description': '양의 정부호 여부를 판정할 실수 대칭행렬.'}},
                            'text': '실수 대칭행렬 A가 양의 정부호(positive definite)인지 판정하시오.\nA = {{ A }}',
                            'latex': '\\lambda_i(A)>0\\;\\forall i\\;?',
                            'builder_cas': 'all(ev > 0 for ev in A.eigenvals().keys())',
                            'answer_cas': 'all(ev > 0 for ev in A.eigenvals().keys())',
                            'answer_latex': '\\mathrm{True}\\;\\text{or}\\;\\mathrm{False}',
                            'solution_strategy': 'rule_based_steps',
                            'validators': ['eigenvalue_sign_check']}}
)

# problem_type별 answer_type의 순서를 명시적으로 고정한다.
# concept의 supported_answer_types가 1개이면 그 값을 사용하고,
# 여러 개인 경우 이 매핑과 서로 일치하는지 검사한다.
ANSWER_TYPE_BY_PROBLEM_TYPE = {
    key: value["answer_type"] for key, value in BLUEPRINTS.items()
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def dump_json(data: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def slug(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z_.-]+", "_", value).strip("_")


def unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def choose_answer_type(concept: dict[str, Any], problem_type: str) -> str:
    supported = concept["generation_profile"].get("supported_answer_types", [])
    blueprint_answer = ANSWER_TYPE_BY_PROBLEM_TYPE.get(problem_type)

    if blueprint_answer is None:
        return supported[0] if supported else "expression"

    if blueprint_answer not in supported:
        raise ValueError(
            f"{concept['concept_id']} / {problem_type}: blueprint answer_type "
            f"'{blueprint_answer}' is not in supported_answer_types={supported}"
        )
    return blueprint_answer


def make_constraints(raw_constraints: list[tuple[Any, ...]]) -> list[dict[str, Any]]:
    result = []
    for constraint_id, left, operator, right, description in raw_constraints:
        result.append(
            {
                "constraint_id": constraint_id,
                "scope": "generation",
                "description": description,
                "rule": {"left": left, "operator": operator, "right": right},
                "on_failure": "resample",
            }
        )
    return result


def build_distractors(concept: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for misconception in concept.get("misconceptions", []):
        result.append(
            {
                "rule_id": f"from_{slug(misconception['misconception_id'])}",
                "misconception_id": misconception["misconception_id"],
                "transformation": f"apply_misconception:{misconception.get('diagnosis_tag', misconception['misconception_id'])}",
                "validator": "not_equivalent_to_correct_answer",
            }
        )
    return result


def build_template(
    catalog: dict[str, Any],
    concept: dict[str, Any],
    problem_type: str,
    *,
    strict: bool = True,
) -> dict[str, Any]:
    bp = BLUEPRINTS.get(problem_type)
    if bp is None:
        if strict:
            raise KeyError(f"No blueprint registered for problem_type='{problem_type}'")
        bp = {
            "answer_type": concept["generation_profile"].get("supported_answer_types", ["expression"])[0],
            "parameters": {},
            "text": f"TODO: {concept['name_ko']} / {problem_type} 문제 본문을 정의하세요.",
            "latex": "",
            "builder_cas": "",
            "answer_cas": "",
            "answer_latex": "",
            "solution_strategy": "llm_explanation",
        }

    answer_type = choose_answer_type(concept, problem_type)
    # ProblemTemplate_프레임.json의 구조를 코드 내부에서 직접 구성한다.
    # 따라서 별도의 frame JSON 파일은 실행 시 필요하지 않다.
    result: dict[str, Any] = {}

    subject = catalog["subject"]
    unit = catalog["unit"]
    gp = concept["generation_profile"]
    difficulty = gp.get("difficulty_range", {"min": 1, "max": 5})
    dmin, dmax = difficulty["min"], difficulty["max"]
    dbase = (dmin + dmax) // 2

    formula_ids = [f["formula_id"] for f in concept.get("formulas", [])]
    recommended_validators = gp.get("recommended_validators", [])
    # 개념 단위 추천 validator보다 문제 유형별 blueprint validator를 우선한다.
    # blueprint에 지정이 없을 때만 catalog의 recommended_validators를 fallback으로 쓴다.
    validators = unique(bp.get("validators", recommended_validators) + bp.get("extra_validators", []))

    result["schema_version"] = "1.0.0"
    result["object_type"] = "problem_template"
    result["template_id"] = f"{subject['subject_id']}.{unit['unit_id']}.{concept['concept_id']}.{problem_type}.v1"
    result["template_version"] = "1.0.0"
    result["status"] = "draft"

    result["taxonomy"] = {
        "subject_id": subject["subject_id"],
        "subject_name_ko": subject["name_ko"],
        "unit_id": unit["unit_id"],
        "unit_name_ko": unit["name_ko"],
        "concept_ids": [concept["concept_id"]],
        "formula_ids": formula_ids,
        "tags": concept.get("tags", []),
    }

    result["classification"] = {
        "problem_type": problem_type,
        "answer_type": answer_type,
        "difficulty": {"base": dbase, "min": dmin, "max": dmax},
        "generation_strategy": bp.get("generation_strategy", "forward_generation"),
        "language": catalog.get("language", "ko-KR"),
    }

    result["parameters"] = copy.deepcopy(bp.get("parameters", {}))
    result["parameter_dependencies"] = copy.deepcopy(bp.get("parameter_dependencies", []))
    result["constraints"] = make_constraints(bp.get("constraints", []))

    result["problem_builder"] = {
        "text_templates_ko": [bp["text"]],
        "latex_templates": [bp.get("latex", "")],
        "cas_template": bp.get("builder_cas", ""),
        "context_templates": bp.get("context_templates", []),
        "render_engine": "jinja2",
    }

    result["answer_spec"] = {
        "answer_type": answer_type,
        "cas_template": bp.get("answer_cas", ""),
        "latex_template": bp.get("answer_latex", ""),
        "canonicalization": {
            "method": bp.get("canonicalization", "simplify"),
            "exact_value_preferred": True,
        },
        "equivalence": {
            "method": bp.get("equivalence", "symbolic_equivalence"),
            "tolerance": None,
        },
        "required_checks": validators,
    }

    primary_formula = formula_ids[0] if formula_ids else ""
    result["solution_spec"] = {
        "solution_strategy": bp.get("solution_strategy", "rule_based_steps"),
        "solution_plan": [
            {
                "step": 1,
                "action": concept.get("learning_objectives", [{}])[0].get(
                    "description", f"{concept['name_ko']}의 정의와 성질을 적용한다."
                ),
                "formula_id": primary_formula,
                "cas_expression": bp.get("answer_cas", ""),
            }
        ],
        "explanation_policy": {
            "use_verified_answer_only": True,
            "use_knowledge_base": True,
            "allow_llm_calculation": False,
        },
    }

    result["validation"] = {
        "validators": [
            {"name": validator, "required": True, "config": {}}
            for validator in validators
        ],
        "generation_max_attempts": 100,
        "all_required_must_pass": True,
    }

    result["distractor_rules"] = build_distractors(concept)

    result["quality_rules"] = {
        "duplicate_check": True,
        "answer_complexity_check": True,
        "ambiguity_check": True,
        "maximum_answer_complexity": None,
        "maximum_denominator": 12,
        "allow_decimal_answer": False,
        "minimum_distinct_parameter_sets": 20,
    }

    result["storage_policy"] = {
        "save_failed_generations": True,
        "save_validation_trace": True,
        "save_seed": True,
        "save_template_snapshot": True,
    }

    result["metadata"] = {
        "created_at": None,
        "updated_at": None,
        "created_by": "concept_catalog_converter.py",
        "reviewed_by": None,
        "review_status": "not_reviewed",
        "notes": (
            f"Auto-generated from concept '{concept['concept_id']}' "
            f"({concept['name_ko']}) and problem_type '{problem_type}'. "
            "행렬 크기/가역성/REF 형태처럼 sampler 단계에서 보장해야 하는 조건은 "
            "실제 문제 생성 엔진 구현 시 추가 검증이 필요하다."
        ),
    }

    return result


def validate_catalog_coverage(catalog: dict[str, Any]) -> list[str]:
    missing = []
    for concept in catalog.get("concepts", []):
        gp = concept.get("generation_profile", {})
        if not gp.get("enabled", False):
            continue
        for problem_type in gp.get("supported_problem_types", []):
            if problem_type not in BLUEPRINTS:
                missing.append(f"{concept['concept_id']}::{problem_type}")
    return missing


def generate_catalog(
    catalog_path: Path,
    output_dir: Path,
    *,
    strict: bool = True,
) -> list[Path]:
    catalog = load_json(catalog_path)

    missing = validate_catalog_coverage(catalog)
    if missing and strict:
        raise RuntimeError("Missing blueprints:\n  - " + "\n  - ".join(missing))

    unit_output_dir = output_dir / catalog["unit"]["unit_id"]
    written: list[Path] = []
    manifest: list[dict[str, str]] = []

    for concept in catalog.get("concepts", []):
        gp = concept.get("generation_profile", {})
        if not gp.get("enabled", False):
            continue

        for problem_type in gp.get("supported_problem_types", []):
            data = build_template(
                catalog,
                concept,
                problem_type,
                strict=strict,
            )

            filename = f"{concept['order']:02d}_{slug(concept['concept_id'])}__{slug(problem_type)}.json"
            path = unit_output_dir / filename
            dump_json(data, path)
            written.append(path)
            manifest.append(
                {
                    "template_id": data["template_id"],
                    "concept_id": concept["concept_id"],
                    "problem_type": problem_type,
                    "file": filename,
                }
            )

    dump_json(
        {
            "subject_id": catalog["subject"]["subject_id"],
            "unit_id": catalog["unit"]["unit_id"],
            "template_count": len(written),
            "templates": manifest,
        },
        unit_output_dir / "manifest.json",
    )

    return written


def find_catalog_files(input_path: Path, max_unit: int | None = None) -> list[Path]:
    if input_path.is_file():
        return [input_path]

    if not input_path.is_dir():
        raise FileNotFoundError(f"Input path does not exist: {input_path}")

    files = sorted(input_path.glob("la_*.json"))

    if max_unit is not None:
        filtered: list[Path] = []
        for path in files:
            match = re.match(r"la_(\d+)_", path.name)
            if match and int(match.group(1)) <= max_unit:
                filtered.append(path)
        files = filtered

    return files


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert linear-algebra concept catalog JSON files into ProblemTemplate JSON files."
    )
    parser.add_argument(
        "input",
        type=Path,
        help="One concept catalog JSON file or a directory containing la_*.json files.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("generated_problem_templates"),
        help="Root output directory. Each unit is written to its own subdirectory.",
    )
    parser.add_argument(
        "--max-unit",
        type=int,
        default=None,
        help="When input is a directory, only process la_01 through la_N.",
    )
    parser.add_argument(
        "--allow-missing-blueprints",
        action="store_true",
        help="Generate TODO draft templates instead of failing for unknown problem types.",
    )
    args = parser.parse_args()

    catalog_files = find_catalog_files(args.input, args.max_unit)
    if not catalog_files:
        raise RuntimeError(f"No catalog JSON files found: {args.input}")

    total_written: list[Path] = []

    for catalog_path in catalog_files:
        written = generate_catalog(
            catalog_path,
            args.output,
            strict=not args.allow_missing_blueprints,
        )
        total_written.extend(written)
        print(f"[OK] {catalog_path.name}: {len(written)} templates")

    print()
    print(f"Generated {len(total_written)} templates in total: {args.output.resolve()}")


if __name__ == "__main__":
    main()
