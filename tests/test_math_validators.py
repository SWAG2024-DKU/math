import numpy as np
import pytest
import sympy as s
from app.problems.math_validators import validate_answer, validate_rule_answer
from app.problems.generation_rule_registry import get_rule, list_rules
from app.problems.validator_policy import RULE_VALIDATORS, validate_validator_mapping

M = s.Matrix
I = s.eye(2)
D = s.diag(2,3)
v = M([1,2])
t = s.Symbol('t', real=True)
x,y = s.symbols('x y', real=True)

def check(kind,answer,p):
    return validate_rule_answer(get_rule('linear_algebra',kind),answer,p)

# Hand-computed examples, including alternate bases and decompositions.
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

@pytest.mark.parametrize('kind',CASES)
def test_curated_correct_and_wrong(kind):
    p,good,bad = CASES[kind]
    result = check(kind,good,p)
    assert result.passed, result
    assert not check(kind,bad,p).passed


def test_full_curated_coverage():
    curated = [r for r in list_rules() if r.status!='draft_auto']
    assert len(curated) == 56
    assert set(CASES) == set(RULE_VALIDATORS) == {r.problem_type for r in curated}

@pytest.mark.parametrize('value',[1,0,'True','False',[],None])
def test_boolean_is_strict(value):
    assert not validate_answer(value,True,answer_type='boolean',validators=['boolean_equality'])

@pytest.mark.parametrize('value',[float('nan'),float('inf'),s.zoo,s.oo,True,'__import__("os")'])
def test_bad_scalar(value):
    assert not validate_answer(value,value,answer_type='scalar',validators=['scalar_equality_check'])


def test_exact_and_numeric():
    assert validate_answer(s.Rational(1,2),.5,answer_type='scalar',validators=['scalar_equality_check'])
    assert not validate_answer(.5000001,.5,answer_type='scalar',validators=['scalar_equality_check'])
    assert validate_answer(.5000001,.5,answer_type='scalar',validators=['numeric_equality'],config={'numeric_equality':{'atol':1e-6}})
    assert not validate_answer(1,2,answer_type='scalar',validators=['numeric_equality'],config={'numeric_equality':{'atol':float('inf')}})


def test_noncommutative():
    A,B=s.symbols('A B',commutative=False)
    expected=A*A+A*B+B*A+B*B
    assert validate_answer((A+B)**2,expected,answer_type='expression',validators=['symbolic_noncommutative_expansion'])
    assert not validate_answer(A*A+2*A*B+B*B,expected,answer_type='expression',validators=['symbolic_noncommutative_expansion'])


def test_sets_and_domain():
    assert validate_answer(s.Interval(0,1),s.Interval(0,1),answer_type='interval',validators=['set_equivalence'])
    assert not validate_answer(s.Interval.open(0,1),s.Interval(0,1),answer_type='interval',validators=['set_equivalence'])
    assert not validate_answer(1/x,answer_type='expression',validators=['domain_check'],config={'domain_check':{'domain':s.S.Reals,'symbol':x}})
    assert validate_answer(1/x,answer_type='expression',validators=['domain_check'],config={'domain_check':{'domain':s.Interval.open(0,s.oo),'symbol':x}})
    assert not validate_answer(s.I,answer_type='scalar',validators=['domain_check'],config={'domain_check':{'domain':s.S.Reals}})


def test_shape_and_numpy():
    assert validate_answer(np.array([[1,2]]),M([[1,2]]),answer_type='matrix',validators=['matrix_equivalence'])
    assert not validate_answer(np.array([[1,2]]),M([1,2]),answer_type='matrix',validators=['matrix_equivalence'])
    assert validate_answer(np.array([1,2]),M([1,2]),answer_type='vector',validators=['vector_equivalence'])


def test_fail_closed():
    assert not validate_answer(1,1,answer_type='scalar',validators=[])
    assert not validate_answer(1,1,answer_type='scalar',validators=['unknown'])
    assert not validate_answer(True,True,answer_type='boolean',validators=['matrix_equivalence'])
    assert not check('eigenvector_calculation',[],{'A':I,'lambda_val':9})
    assert not check('orthogonal_projection_calculation',v,{'a':v,'b':s.zeros(2,1)})
    assert not check('matrix_multiplication',I,{})


def test_basis_completeness_and_zero_space():
    assert not check('null_space_basis',[M([1,0])],{'A':s.zeros(2)})
    assert not check('null_space_basis',[M([1,0]),M([2,0])],{'A':s.zeros(2)})
    assert check('null_space_basis',[],{'A':I})
    assert not check('null_space_basis',[s.zeros(2,1)],{'A':I})
    assert check('eigenvalue_calculation',[2],{'A':2*I})
    assert not check('eigenvalue_calculation',[2,2],{'A':2*I})


def test_factorization_conditions():
    assert not check('lu_factorization',I.row_join(M([[0,1],[1,0]])),{'A':M([[0,1],[1,0]])})
    assert not check('matrix_diagonalization',(I,M([[1,1],[0,1]])),{'A':M([[1,1],[0,1]])})
    assert not check('spectral_decomposition_calculation',[(2,s.diag(1,0))],{'A':s.diag(2,0)})
    assert not check('gram_schmidt_orthogonalization',[I[:,1],I[:,0]],{'V':I})


def test_rule_schema_rejects_semantic_mismatch():
    from app.schemas.generation_rule import GenerationRule
    r=get_rule('linear_algebra','change_of_basis_calculation').model_dump()
    r['validation']['validators']=['lu_factorization_check']
    with pytest.raises(ValueError):
        GenerationRule.model_validate(r)


def test_builder_does_not_append_recommendations():
    from app.problems.problem_type_extractor import extract_from_directory
    from app.problems.template_builder import build_template
    items=extract_from_directory('data/concepts')
    count=0
    for item in items:
        rule=get_rule(item.subject_id,item.problem_type)
        template=build_template(item,rule)
        names=[v.name for v in template.validation.validators]
        validate_validator_mapping(template.classification.answer_type,names,require_nonempty=False)
        if rule.status!='draft_auto':
            assert names==list(RULE_VALIDATORS[rule.problem_type])
        count+=1
    assert count==3327

@pytest.mark.parametrize('kind,answer,p',[
    ('positive_definite_test',True,{'A':M([[1,2],[0,1]])}),
    ('singular_matrix_identification',False,{'A':s.diag(x,1)}),
    ('inverse_calculation',I,{'A':s.zeros(2)}),
    ('least_squares_calculation',v,{'A':s.zeros(2),'b':v}),
    ('elementary_matrix_construction',I,{'n':2,'target_row':2,'source_row':0,'c':1}),
    ('matrix_to_vector_equation',s.Eq(x,y,evaluate=False),{'A':I,'b':v}),
    ('parametric_solution_extraction',M([1-s.exp(t),s.exp(t)]),{'A':M([[1,1]]),'b':M([1])}),
    ('parametric_solution_extraction',M([1-s.Symbol('k',integer=True),s.Symbol('k',integer=True)]),{'A':M([[1,1]]),'b':M([1])}),
    ('quadratic_form_transformation',2*x*x+3*y*y+x,{'A':D}),
    ('spectral_decomposition_calculation',[],{'A':s.zeros(2)}),
])
def test_invalid_context_or_incomplete_answer(kind,answer,p):
    assert not check(kind,answer,p)


def test_zero_eigenvalue_projection_required():
    assert check('spectral_decomposition_calculation',[(2,s.diag(1,0)),(0,s.diag(0,1))],{'A':s.diag(2,0)})


def test_unknown_and_invalid_config_cannot_pass():
    assert not validate_answer(1,1,answer_type='scalar',validators=['numeric_equality'],config={'numeric_equality':{'atol':-1}})
    assert not validate_answer(1,1,answer_type='scalar',validators=['scalar_equality_check','domain_check'])


def test_domain_hole_is_not_hidden_by_equivalence():
    expr=s.Mul(x**2-1,s.Pow(x-1,-1,evaluate=False),evaluate=False)
    report=validate_answer(expr,x+1,answer_type='expression',validators=['symbolic_equivalence','domain_check'],config={'domain_check':{'domain':s.S.Reals,'symbol':x}})
    assert report.results[0].passed
    assert not report.passed
