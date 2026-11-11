"""기존 선형대수의 수계산 정답/오답 검증을 유지하는 회귀 검사."""
import sympy as s
import pytest
from scripts.problems.common import math_validators as m
from app.problems.validator_policy import RULE_VALIDATORS
M=s.Matrix
I=s.eye(2)
D=s.diag(2,3)
v=M([1,2])
t=s.Symbol('t',real=True)
x,y=s.symbols('x y',real=True)
CASES = {
'algebraic_expansion_verification': ({'A':M([[0,1],[0,0]]),'B':M([[0,0],[1,0]])}, I, s.zeros(2)),
'basis_verification': ({'V':I,'n':2}, True, False),
'block_matrix_determinant': ({'B':D,'C':M([[4]])}, 24, 6),
'change_of_basis_calculation': ({'B':D,'C':2*I}, s.diag(1,s.Rational(3,2)), I),
'column_space_basis': ({'A':M([[1,2],[2,4]])}, [M([2,4])], [M([1,0])]),
'consistency_check': ({'Aug':M([[1,1,1],[2,2,3]])}, '해 없음', '해 존재'),
'cramer_rule_solution': ({'A':D,'b':M([2,6])}, v, M([1,1])),
'determinant_by_ero': ({'A':D}, 6, 5),
'determinant_cofactor_expansion': ({'A':D}, 6, 5),
'eigenvalue_calculation': ({'A':D}, [3,2], [2,2]),
'eigenvector_calculation': ({'A':D,'lambda_val':2}, [M([7,0])], [M([0,0])]),
'elementary_inverse_calculation': ({'E':M([[1,1],[0,1]])}, M([[1,-1],[0,1]]), I),
'elementary_matrix_construction': ({'n':2,'target_row':0,'source_row':1,'c':3}, M([[1,3],[0,1]]), I),
'equation_to_matrix': ({'A':I,'b':v}, M([[1,0,1],[0,1,2]]), I),
'equivalence_theorem_check': ({'A':D}, True, False),
'ero_application': ({'A':D,'target_row':0,'source_row':1,'c':2}, M([[2,6],[0,3]]), D),
'free_variable_identification': ({'A':M([[1,2,0],[0,0,1]])}, [1], [0]),
'geometric_area_volume_calculation': ({'A':s.diag(-2,3)}, 6, -6),
'gram_schmidt_orthogonalization': ({'V':M([[1,1],[0,1]])}, [-I[:,0], I[:,1]], [2*I[:,0], I[:,1]]),
'inverse_calculation': ({'A':D}, s.diag(s.Rational(1,2),s.Rational(1,3)), D),
'invertibility_determination': ({'A':D}, '가역', '비가역'),
'kernel_image_calculation': ({'A':M([[1,2],[2,4]])}, ([M([-2,1])],[M([2,4])]), ([M([0,0])],[M([1,2])])),
'least_squares_calculation': ({'A':M([[1],[1]]),'b':M([1,3])}, M([2]), M([1])),
'left_null_space_basis': ({'A':M([[1,0],[2,0],[3,0]])}, [M([-2,1,0]),M([-3,0,1])], [M([-2,1,0])]),
'linear_independence_test': ({'V':M([[1,2],[2,4]])}, False, True),
'linear_regression_calculation': ({'X':M([[1,0],[1,1],[1,2]]),'y':M([1,3,5])}, M([1,2]), M([2,1])),
'linear_transformation_verification': ({'A':I,'b':M([1,0])}, False, True),
'lu_factorization': ({'A':M([[1,2],[3,7]])}, M([[1,0,1,2],[3,1,0,1]]), I.row_join(I)),
'matrix_diagonalization': ({'A':D}, (M([[0,4],[5,0]]),s.diag(3,2)), (s.zeros(2),D)),
'matrix_multiplication': ({'A':M([[1,2],[0,1]]),'B':M([[1,0],[3,1]])}, M([[7,2],[3,1]]), M([[1,2],[3,7]])),
'matrix_power_calculation': ({'A':D,'k':3}, s.diag(8,27), D),
'matrix_rank_property': ({'m':3,'n':2}, 2, 3),
'matrix_to_vector_equation': ({'A':I,'b':v,'x':M([x,y])}, s.Eq(M([x,y]),v,evaluate=False), s.Eq(M([x,y]),2*v,evaluate=False)),
'norm_distance_calculation': ({'u':M([0,0]),'v':M([3,4])}, 5, 25),
'null_space_basis': ({'A':M([[1,2]])}, [M([-4,2])], [M([0,0])]),
'orthogonal_complement_calculation': ({'W':M([[1],[2]])}, [M([-2,1])], [M([1,2])]),
'orthogonal_diagonalization_calculation': ({'A':D}, (M([[0,-1],[1,0]]),s.diag(3,2)), (2*I,D)),
'orthogonal_projection_calculation': ({'a':M([3,4]),'b':M([2,0])}, M([3,0]), M([0,4])),
'orthonormal_verification': ({'Q':M([[1,0],[0,1],[0,0]])}, True, False),
'parametric_solution_extraction': ({'A':M([[1,1]]),'b':M([1])}, s.FiniteSet((1-2*t,2*t)), M([1,0])),
'positive_definite_test': ({'A':s.diag(1,-1)}, False, True),
'qr_factorization_calculation': ({'A':M([[2,0],[0,3],[0,0]])}, (M([[-1,0],[0,1],[0,0]]),s.diag(-2,3)), (M([[2,0],[0,1],[0,0]]),s.diag(1,3))),
'quadratic_form_transformation': ({'A':D}, 3*x*x+2*y*y, 2*x*x+2*y*y),
'rank_calculation': ({'A':M([[1,2],[2,4]])}, 1, 2),
'rank_nullity_calculation': ({'A':M([[1,2,3],[2,4,6]])}, 2, 1),
'ref_identification': ({'A':M([[0,1],[1,0]])}, False, True),
'row_space_basis': ({'A':M([[1,2],[2,4]])}, [M([[3,6]])], [M([1,0])]),
'rref_calculation': ({'A':M([[1,2],[2,4]])}, M([[1,2],[0,0]]), I),
'singular_matrix_identification': ({'A':M([[1,2],[2,4]])}, True, False),
'solve_by_lu': ({'A':D,'b':M([2,6])}, v, M([2,1])),
'span_membership_test': ({'V':M([[1],[2]]),'b':M([2,4])}, True, False),
'spectral_decomposition_calculation': ({'A':D}, [(3,s.diag(0,1)),(2,s.diag(1,0))], [(2,I)]),
'standard_matrix_derivation': ({'images':M([[1,2],[3,4]])}, M([[1,2],[3,4]]), I),
'subspace_verification': ({'A':I,'b':M([1,0])}, False, True),
'symmetry_classification': ({'A':M([[1,2],[2,3]])}, True, False),
'transpose_algebra': ({'A':M([[1,2],[0,1]]),'B':M([[1,0],[3,1]])}, M([[7,3],[2,1]]), I),
}

@pytest.mark.parametrize('kind', CASES)
def test_linear_algebra_correct_wrong(kind):
    p, good, bad = CASES[kind]
    for name in RULE_VALIDATORS[kind]:
        expected=m.reference_answer(kind,p) if name in {'scalar_equality_check','boolean_equality','choice_equality','matrix_equivalence','symbolic_noncommutative_expansion','equation_equivalence'} else None
        assert m._check(name,good,expected,p,{},kind), kind
        assert not m._check(name,bad,expected,p,{},kind), kind

@pytest.mark.parametrize('kind,p',[
 ('svd_calculation',{'A':D}),
 ('compact_svd_approximation',{'A':D,'k':1}),
 ('pseudoinverse_calculation',{'A':D}),
 ('pca_calculation',{'A':M([[2,0],[-2,0],[0,1],[0,-1]])}),
 ('complex_inner_product_calculation',{'u':M([s.I,1]),'v':M([1,s.I])}),
 ('jordan_canonical_form_calculation',{'A':M([[2,1],[0,2]])}),
])
def test_advanced_linear_algebra(kind,p):
    answer = {'svd_calculation': lambda: m._advanced_svd(p['A']), 'compact_svd_approximation': lambda: m._compact_svd_rank_one(p['A']), 'pseudoinverse_calculation': lambda: p['A'].pinv(), 'pca_calculation': lambda: m._pca_projection(p['A']), 'complex_inner_product_calculation': lambda: (p['u'].H*p['v'])[0], 'jordan_canonical_form_calculation': lambda: m._jordan_defective_pair(p['A'])}[kind]()
    for name in RULE_VALIDATORS[kind]:
        assert m._check(name,answer,answer,p,{},kind)
