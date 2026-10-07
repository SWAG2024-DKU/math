"""Fail-closed mathematical validation for common answers and linear algebra.

Inputs are Python/SymPy objects, not executable CAS strings. A failed or
undecidable check never passes. See docs/math_validation.md for the contract.
"""
from __future__ import annotations

import ast
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any
import math
import numbers

import numpy as np
import sympy as sp

from app.problems.validator_policy import validate_validator_mapping, validate_curated_mapping
from app.schemas.problem_template import AnswerTemplateSpec, ValidatorTemplate


@dataclass(frozen=True)
class ValidationResult:
    name: str
    passed: bool
    message: str = ''

    def __bool__(self):
        return self.passed

    @property
    def validator(self):
        """기존 ProblemInstance 생성기 계약과의 호환 이름."""
        return self.name


@dataclass(frozen=True)
class ValidationReport:
    results: tuple[ValidationResult, ...]

    @property
    def passed(self):
        return bool(self.results) and all(r.passed for r in self.results)

    def __bool__(self):
        return self.passed


def scalar(value):
    # sympify(str) uses eval; deliberately do not parse user text here.
    if isinstance(value, (bool, np.bool_)) or value is sp.true or value is sp.false:
        raise ValueError('Boolean is not a scalar answer')
    if isinstance(value, sp.Expr):
        result = value
    elif isinstance(value, numbers.Number):
        result = sp.sympify(value)
    else:
        raise ValueError('Expected a number or a parsed SymPy expression')
    if result.has(sp.nan, sp.zoo, sp.oo, -sp.oo):
        raise ValueError('Non-finite answer')
    return result


def matrix(value):
    if isinstance(value, sp.MatrixBase):
        result = value
    elif isinstance(value, (list, tuple, np.ndarray)):
        # Validate elements before Matrix has an opportunity to parse strings.
        arr = np.asarray(value, dtype=object)
        if arr.ndim not in (1, 2):
            raise ValueError('Expected one or two dimensions')
        for item in arr.flat:
            scalar(item)
        result = sp.Matrix(value.tolist() if isinstance(value, np.ndarray) else value)
    else:
        raise ValueError('Expected a matrix')
    for item in result:
        scalar(item)
    return result


def vector(value):
    result = matrix(value)
    if result.cols != 1 and result.rows != 1:
        raise ValueError('Expected a vector')
    return result.T if result.rows == 1 else result


def equal(a, b, config=None):
    config = config or {}
    if isinstance(a, sp.MatrixBase) or isinstance(b, sp.MatrixBase):
        a, b = matrix(a), matrix(b)
        return a.shape == b.shape and all(equal(x, y, config) for x, y in zip(a, b))
    a, b = scalar(a), scalar(b)
    # Exact structural equality is common for CAS results that are recomputed
    # from the same input. Check it before simplify(): comparing different
    # algebraic roots with simplify can trigger expensive minimal-polynomial
    # factorization (notably during eigenvalue matching).
    if a == b:
        return True
    if config.get('numeric', False):
        tolerances = (float(config.get('atol', 1e-9)), float(config.get('rtol', 1e-9)))
        if not all(math.isfinite(t) and t >= 0 for t in tolerances):
            raise ValueError('Tolerances must be finite and nonnegative')
    if sp.simplify(a - b) == 0:
        return True
    if config.get('numeric', False) and not (a.free_symbols or b.free_symbols):
        atol, rtol = float(config.get('atol', 1e-9)), float(config.get('rtol', 1e-9))
        if not all(math.isfinite(t) and t >= 0 for t in (atol, rtol)):
            raise ValueError('Tolerances must be finite and nonnegative')
        x, y = complex(a.evalf()), complex(b.evalf())
        return bool(np.isfinite(x) and np.isfinite(y) and abs(x-y) <= atol + rtol*abs(y))
    return False


def boolean(value):
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if value is sp.true:
        return True
    if value is sp.false:
        return False
    raise ValueError('Expected a Boolean, not a number or string')


def columns(values, dimension):
    if isinstance(values, sp.MatrixBase):
        out = matrix(values)
    else:
        if not isinstance(values, (list, tuple)):
            raise ValueError('Expected a list of vectors')
        out = sp.Matrix.hstack(*(vector(v) for v in values)) if values else sp.zeros(dimension, 0)
    if out.rows != dimension:
        raise ValueError('Wrong ambient dimension')
    return out


def basis_matches(answer, target):
    # Target columns need not themselves be independent; answer columns must be.
    answer = columns(answer, target.rows)
    return (answer.cols == answer.rank() == target.rank()
            and answer.row_join(target).rank() == target.rank())


def square(A):
    if A.rows != A.cols:
        raise ValueError('A square matrix is required')
    return A


def real_symmetric(A):
    square(A)
    if not all(x.is_real is True for x in A) or not equal(A.T, A):
        raise ValueError('A real symmetric matrix is required')
    return A


def pair(value):
    if not isinstance(value, (tuple, list)) or len(value) != 2:
        raise ValueError('Expected a pair')
    return matrix(value[0]), matrix(value[1])


def reference_answer(problem_type, parameters):
    """Independent, explicitly coded references; never eval rule expressions."""
    p = parameters
    A = matrix(p['A']) if 'A' in p else None
    V = matrix(p['V']) if 'V' in p else None
    b = vector(p['b']) if 'b' in p else None
    if problem_type == 'algebraic_expansion_verification':
        return (A + matrix(p['B'])) ** 2
    if problem_type == 'basis_verification':
        return V.rows == V.cols == p['n'] and V.rank() == p['n']
    if problem_type == 'block_matrix_determinant':
        return sp.diag(matrix(p['B']), matrix(p['C'])).det()
    if problem_type == 'change_of_basis_calculation':
        B, C = square(matrix(p['B'])), square(matrix(p['C']))
        if B.det() == 0 or C.det() == 0:
            raise ValueError('Both bases must be invertible')
        return C.inv()*B
    if problem_type == 'consistency_check':
        aug = matrix(p['Aug'])
        if aug.cols < 2:
            raise ValueError('Expected an augmented matrix')
        return '해 존재' if aug[:, :-1].rank() == aug.rank() else '해 없음'
    if problem_type in {'determinant_by_ero', 'determinant_cofactor_expansion'}:
        return square(A).det()
    if problem_type in {'elementary_matrix_construction', 'ero_application'}:
        M = sp.eye(p['n']) if problem_type == 'elementary_matrix_construction' else A
        i, j, c = p['target_row'], p['source_row'], scalar(p['c'])
        if not (isinstance(i, int) and isinstance(j, int) and 0 <= i < M.rows and 0 <= j < M.rows and i != j and c != 0):
            raise ValueError('Invalid row operation')
        return M.elementary_row_op(op='n->n+km', row1=i, row2=j, k=c)
    if problem_type in {'inverse_calculation', 'elementary_inverse_calculation'}:
        return square(A if A is not None else matrix(p['E'])).inv()
    if problem_type == 'equation_to_matrix':
        return A.row_join(b)
    if problem_type == 'equivalence_theorem_check':
        return square(A).det() != 0
    if problem_type == 'invertibility_determination':
        return '가역' if square(A).det() != 0 else '비가역'
    if problem_type == 'geometric_area_volume_calculation':
        return abs(square(A).det())
    if problem_type == 'linear_independence_test':
        return V.rank() == V.cols
    if problem_type in {'linear_transformation_verification', 'subspace_verification'}:
        if A.rows != b.rows:
            raise ValueError('Incompatible A and b')
        return equal(b, sp.zeros(b.rows, 1))
    if problem_type == 'matrix_multiplication':
        return A * matrix(p['B'])
    if problem_type == 'matrix_power_calculation':
        k = scalar(p['k'])
        if k.is_integer is not True:
            raise ValueError('Integer power required')
        return square(A)**k
    if problem_type == 'matrix_rank_property':
        m, n = scalar(p['m']), scalar(p['n'])
        if any(x.is_integer is not True or x.is_positive is not True for x in (m,n)):
            raise ValueError('Positive integer dimensions required')
        return min(m, n)
    if problem_type == 'matrix_to_vector_equation':
        x = vector(p['x'])
        return sp.Eq(A*x, b, evaluate=False)
    if problem_type == 'norm_distance_calculation':
        return (vector(p['u'])-vector(p['v'])).norm()
    if problem_type == 'orthonormal_verification':
        Q = matrix(p['Q'])
        return equal(Q.H*Q, sp.eye(Q.cols))
    if problem_type == 'positive_definite_test':
        A = real_symmetric(A)
        return all(A[:k, :k].det() > 0 for k in range(1, A.rows+1))
    if problem_type == 'rank_calculation':
        return sp.Integer(A.rank())
    if problem_type == 'rank_nullity_calculation':
        return sp.Integer(A.cols-A.rank())
    if problem_type == 'ref_identification':
        return bool(A.is_echelon)
    if problem_type == 'rref_calculation':
        return A.rref()[0]
    if problem_type == 'singular_matrix_identification':
        return square(A).det() == 0
    if problem_type == 'span_membership_test':
        return V.rank() == V.row_join(b).rank()
    if problem_type == 'standard_matrix_derivation':
        return matrix(p['images'])
    if problem_type == 'symmetry_classification':
        return equal(square(A).T, A)
    if problem_type == 'transpose_algebra':
        return (A*matrix(p['B'])).T
    raise ValueError(f'No unique reference for {problem_type}')


def domain_check(answer, expected, p, c):
    domain = c.get('domain')
    if not isinstance(domain, sp.Set):
        raise ValueError('config.domain must be a SymPy Set')
    value = scalar(answer)
    symbol = c.get('symbol')
    if symbol is None:
        return domain.contains(value) is sp.true
    if not isinstance(symbol, sp.Symbol) or value.free_symbols - {symbol}:
        raise ValueError('A univariate expression and explicit symbol are required')
    if domain.is_subset(sp.S.Reals) is not True:
        raise ValueError('Expression domain checking currently supports real domains')
    actual = sp.calculus.util.continuous_domain(value, symbol, sp.S.Reals)
    return domain.is_subset(actual) is True


def _check(name, answer, expected, p, c, problem_type):
    # The six advanced types have independent checks against sampled input,
    # rather than comparing a computed answer with itself.
    if name == 'complex_inner_product_check':
        u, v = vector(p['u']), vector(p['v'])
        return u.shape == v.shape and equal(scalar(answer), (u.H*v)[0], c)
    if name == 'jordan_similarity_check':
        A = square(matrix(p['A']))
        P, J = pair(answer)
        if A.shape != (2, 2) or P.shape != A.shape or J.shape != A.shape or P.det() == 0:
            return False
        lam = A.trace()/2
        canonical = sp.Matrix([[lam, 1], [0, lam]])
        return J == canonical and equal(A*P, P*J, c) and A.charpoly().as_expr() == J.charpoly().as_expr()
    if name == 'svd_reconstruction_check':
        A = matrix(p['A'])
        if not isinstance(answer, (tuple, list)) or len(answer) != 3:
            return False
        U, S, V = (matrix(part) for part in answer)
        if A.shape != (2, 2) or any(M.shape != A.shape for M in (U, S, V)):
            return False
        singular = [S[i, i] for i in range(2)]
        return (S.is_diagonal() is True
                and all(x.is_real is True and x.is_nonnegative is True for x in singular)
                and singular[0] >= singular[1]
                and equal(U.H*U, sp.eye(2), c) and equal(V.H*V, sp.eye(2), c)
                and equal(U*S*V.H, A, c))
    if name == 'compact_svd_optimality_check':
        A, B = matrix(p['A']), matrix(answer)
        if A.shape != (2, 2) or B.shape != A.shape or B.rank() > 1:
            return False
        # For the restricted 2x2 generated matrices with distinct singular
        # values, the optimal rank-one Frobenius residual equals sigma_2^2.
        eigen = (A.H*A).eigenvals()
        values = sorted((sp.sqrt(v) for v, multiplicity in eigen.items() for _ in range(multiplicity)), reverse=True)
        if len(values) != 2 or values[0] <= values[1]:
            return False
        residual = A-B
        return equal((residual.H*residual).trace(), values[1]**2, c)
    if name == 'moore_penrose_conditions_check':
        A, B = matrix(p['A']), matrix(answer)
        return (B.shape == (A.cols, A.rows) and equal(A*B*A, A, c)
                and equal(B*A*B, B, c) and equal((A*B).H, A*B, c)
                and equal((B*A).H, B*A, c))
    if name == 'pca_projection_check':
        A, P = matrix(p['A']), matrix(answer)
        if A.rows < 2 or A.cols != 2 or P.shape != (2, 2) or any(sum(A[:, j]) != 0 for j in range(A.cols)):
            return False
        C = A.T*A/(A.rows-1)
        eig = C.eigenvals()
        if len(eig) != 2:
            return False
        largest = max(eig)
        return (P.rank() == 1 and equal(P.H, P, c) and equal(P*P, P, c)
                and equal(C*P, largest*P, c) and equal((C*P).trace(), largest, c))
    if name in {'scalar_equality_check', 'symbolic_equivalence', 'numeric_equality', 'symbolic_noncommutative_expansion'}:
        if name == 'numeric_equality':
            c = {**c, 'numeric': True}
        return equal(answer, expected, c)
    if name == 'matrix_equivalence':
        return equal(matrix(answer), matrix(expected), c)
    if name == 'vector_equivalence':
        return equal(vector(answer), vector(expected), c)
    if name == 'boolean_equality':
        return boolean(answer) == boolean(expected)
    if name == 'choice_equality':
        if isinstance(answer, str) and isinstance(expected, str):
            return answer == expected
        if isinstance(answer, (list, tuple)) and isinstance(expected, (list, tuple)):
            return all(isinstance(v, str) for v in (*answer, *expected)) and set(answer) == set(expected)
        return False
    if name == 'dimension_valid':
        return matrix(answer).shape == matrix(expected).shape
    if name == 'domain_check':
        return domain_check(answer, expected, p, c)
    if name == 'set_equivalence':
        if not isinstance(answer, sp.Set) or not isinstance(expected, sp.Set):
            return False
        return answer == expected or sp.SymmetricDifference(answer, expected) == sp.EmptySet
    if name == 'equation_equivalence':
        if not isinstance(answer, sp.Equality) or not isinstance(expected, sp.Equality):
            return False
        if problem_type == 'matrix_to_vector_equation':
            # 저장된 expected를 다시 비교하는 대신 입력 행렬의 열벡터들로 재구성한다.
            A, b, x = matrix(p['A']), vector(p['b']), vector(p['x'])
            if A.rows != b.rows or A.cols != x.rows:
                return False
            linear_combination = sp.zeros(A.rows, 1)
            for index in range(A.cols):
                linear_combination += A[:, index] * x[index, 0]
            lhs, rhs = answer.lhs-answer.rhs, linear_combination-b
        else:
            # 다른 equation 유형은 별도의 독립 검증기를 붙이기 전까지 기존 계약 유지.
            lhs, rhs = answer.lhs-answer.rhs, expected.lhs-expected.rhs
        return equal(lhs, rhs, c) or equal(lhs, -rhs, c)
    if name == 'index_set_check':
        A = matrix(p['A'])
        values = list(answer)
        values = [scalar(x) for x in values]
        return (all(x.is_integer is True for x in values) and len(set(values)) == len(values)
                and set(values) == set(range(A.cols))-set(A.rref()[1]))
    if name == 'basis_equivalence':
        A = matrix(p['W'] if problem_type == 'orthogonal_complement_calculation' else p['A'])
        if problem_type == 'column_space_basis':
            target = A
        elif problem_type == 'row_space_basis':
            target = A.T
        elif problem_type in {'left_null_space_basis', 'orthogonal_complement_calculation'}:
            target = columns(A.H.nullspace(), A.rows)
        elif problem_type == 'null_space_basis':
            target = columns(A.nullspace(), A.cols)
        elif problem_type == 'eigenvector_calculation':
            N = square(A)-scalar(p['lambda_val'])*sp.eye(A.rows)
            if N.det() != 0:
                raise ValueError('lambda_val is not an eigenvalue')
            target = columns(N.nullspace(), A.cols)
        else:
            target = matrix(expected)
        return basis_matches(answer, target)
    if name == 'kernel_image_check':
        A = matrix(p['A'])
        if not isinstance(answer, (tuple, list)) or len(answer) != 2:
            return False
        return basis_matches(answer[0], columns(A.nullspace(), A.cols)) and basis_matches(answer[1], A)
    if name == 'eigenvalue_check':
        A = square(matrix(p['A']))
        values = [scalar(v) for v in answer]
        targets = list(A.eigenvals())  # Catalog asks for DISTINCT eigenvalues.
        return len(values) == len(targets) and _matching(values, targets, c)
    if name == 'linear_system_check':
        A, b = square(matrix(p['A'])), vector(p['b'])
        if A.det() == 0:
            raise ValueError('This rule requires a nonsingular matrix')
        return equal(A*vector(answer), b, c)
    if name == 'least_squares_check':
        regression = problem_type == 'linear_regression_calculation'
        A, b = matrix(p['X' if regression else 'A']), vector(p['y' if regression else 'b'])
        if A.rank() != A.cols:
            raise ValueError('This rule requires full column rank')
        residual = A.H*(A*vector(answer)-b)
        return equal(residual, sp.zeros(A.cols, 1), c)
    if name == 'projection_check':
        a, b, v = vector(p['a']), vector(p['b']), vector(answer)
        if (b.H*b)[0] == 0:
            raise ValueError('Projection direction is zero')
        return v.shape == b.shape and b.row_join(v).rank() == 1 and equal((b.H*(a-v))[0], 0, c)
    if name == 'gram_schmidt_check':
        V = matrix(p['V'])
        Q = columns(answer, V.rows)
        if V.rank() != V.cols:
            raise ValueError('Gram-Schmidt input must have independent columns')
        return (Q.shape == V.shape and equal(Q.H*Q, sp.eye(Q.cols), c)
                and all(basis_matches(Q[:, :i], V[:, :i]) for i in range(1, V.cols+1)))
    if name == 'lu_factorization_check':
        A, block = square(matrix(p['A'])), matrix(answer)
        n = A.rows
        if block.shape != (n, 2*n):
            return False
        L, U = block[:, :n], block[:, n:]
        return bool(L.is_lower and U.is_upper and all(equal(L[i,i],1,c) for i in range(n)) and equal(L*U,A,c))
    if name in {'diagonalization_check', 'orthogonal_diagonalization_check'}:
        A = square(matrix(p['A']))
        P, D = pair(answer)
        if P.shape != A.shape or D.shape != A.shape or not D.is_diagonal() or P.det() == 0:
            return False
        if name == 'orthogonal_diagonalization_check':
            real_symmetric(A)
            if not all(x.is_real is True for x in P) or not equal(P.T*P, sp.eye(A.rows), c):
                return False
        return equal(A*P, P*D, c)
    if name == 'qr_factorization_check':
        A = matrix(p['A'])
        Q, R = pair(answer)
        if A.rank() != A.cols:
            raise ValueError('This rule requires full column rank')
        return (Q.shape == A.shape and R.shape == (A.cols,A.cols) and bool(R.is_upper)
                and equal(Q.H*Q, sp.eye(A.cols), c) and equal(Q*R,A,c))
    if name == 'parametric_solution_check':
        A, b = matrix(p['A']), vector(p['b'])
        if answer is sp.EmptySet:
            return A.rank() != A.row_join(b).rank()
        if isinstance(answer, sp.FiniteSet):
            if len(answer) != 1:
                return False
            answer = list(answer)[0]
        x = vector(list(answer) if isinstance(answer, sp.Tuple) else answer)
        if x.rows != A.cols:
            return False
        params = sorted(x.free_symbols - A.free_symbols - b.free_symbols, key=str)
        J = x.jacobian(params) if params else sp.zeros(A.cols,0)
        if any(v.is_integer is True or v.is_positive is True or v.is_negative is True or v.is_nonzero is True for v in params):
            return False  # Restricted parameters do not describe the full affine space.
        if J.free_symbols & set(params):
            return False  # Require affine, unconstrained parameterization.
        offset = x.subs(dict.fromkeys(params,0))
        return (equal(x,offset+J*sp.Matrix(params)) if params else equal(x,offset)) and equal(A*x,b,c) and J.rank() == A.cols-A.rank()
    if name == 'quadratic_form_check':
        A = real_symmetric(matrix(p['A']))
        expr = scalar(answer)
        variables = c.get('variables', sorted(expr.free_symbols, key=str))
        if len(variables) > A.rows or not all(isinstance(v,sp.Symbol) for v in variables):
            return False
        if expr == 0:
            return A == sp.zeros(A.rows)
        poly = sp.Poly(expr, *variables)
        if any(sum(m) != 2 or sum(v != 0 for v in m) != 1 for m, _ in poly.terms()):
            return False
        coefficients = [poly.coeff_monomial(v**2) for v in variables] + [sp.Integer(0)]*(A.rows-len(variables))
        eigenvalues = [v for v,m in A.eigenvals().items() for _ in range(m)]
        return _matching(coefficients, eigenvalues, c)
    if name == 'spectral_decomposition_check':
        A = real_symmetric(matrix(p['A']))
        terms = [(scalar(lam), matrix(P)) for lam,P in answer]
        total, identity = sp.zeros(A.rows), sp.zeros(A.rows)
        for i,(lam,P) in enumerate(terms):
            if not all(x.is_real is True for x in P) or P.shape != A.shape or P.rank() == 0 or not equal(P.T,P,c) or not equal(P*P,P,c):
                return False
            if not equal(A*P,lam*P,c) or any(not equal(P*Q,sp.zeros(A.rows),c) for _,Q in terms[:i]):
                return False
            total += lam*P
            identity += P
        return equal(total,A,c) and equal(identity,sp.eye(A.rows),c)
    raise ValueError(f'Unimplemented validator: {name}')


def _matching(values, targets, config):
    # Match structurally identical exact expressions first. The former greedy
    # loop called simplify(value - target) on the first pair even when the
    # matching expression appeared later in the target list; algebraic root
    # comparisons can become extremely expensive.
    unmatched_values = []
    remaining_targets = list(targets)
    for value in values:
        for i, target in enumerate(remaining_targets):
            if value == target:
                remaining_targets.pop(i)
                break
        else:
            unmatched_values.append(value)

    if not unmatched_values:
        return not remaining_targets
    if len(unmatched_values) != len(remaining_targets):
        return False

    # Preserve general mathematical equivalence checks for pairs that do not
    # have identical SymPy representations.
    for value in unmatched_values:
        for i, target in enumerate(remaining_targets):
            if equal(value, target, config):
                remaining_targets.pop(i)
                break
        else:
            return False
    return not remaining_targets


def validate_answer(answer, expected=None, *, answer_type, validators, parameters=None,
                    config=None, problem_type=None):
    """Run all named checks. Unknown/type-incompatible checks are failures.

    config is a dictionary keyed by validator name. Every returned check is
    required; callers must use report.passed, never just the first result.
    """
    names = tuple(validators)
    try:
        validate_validator_mapping(answer_type, names)
    except ValueError as exc:
        return ValidationReport((ValidationResult('validator_mapping',False,str(exc)),))
    results = []
    for name in names:
        try:
            passed = bool(_check(name,answer,expected,parameters or {},(config or {}).get(name,{}),problem_type))
            results.append(ValidationResult(name,passed,'' if passed else 'Mathematical check failed'))
        except Exception as exc:
            results.append(ValidationResult(name,False,f'{type(exc).__name__}: {exc}'))
    return ValidationReport(tuple(results))


def validate_rule_answer(rule, answer, parameters, *, config=None):
    """Entry point for the future instance generator; no rule expression eval."""
    try:
        if rule.subject_id != 'linear_algebra' or rule.status == 'draft_auto':
            raise ValueError('Only reviewed-mapping linear algebra rules are supported')
        validate_curated_mapping(rule)
        # Generation rules here describe sampled, concrete matrices. Rank and
        # determinant with unspecified symbols can assume generic nonzero pivots.
        for key, value in parameters.items():
            if key == 'x':  # Explicit unknowns for matrix_to_vector_equation only.
                continue
            parsed = matrix(value) if isinstance(value, (sp.MatrixBase,list,tuple,np.ndarray)) else scalar(value)
            if parsed.free_symbols:
                raise ValueError(f'Concrete sampled parameter required: {key}')
        names = tuple(rule.validation.validators)
        generic = {'scalar_equality_check','boolean_equality','choice_equality','matrix_equivalence',
                   'symbolic_noncommutative_expansion','equation_equivalence'}
        expected = reference_answer(rule.problem_type,parameters) if set(names) & generic else None
    except Exception as exc:
        return ValidationReport((ValidationResult('rule_context',False,f'{type(exc).__name__}: {exc}'),))
    return validate_answer(answer,expected,answer_type=rule.answer_spec.answer_type,
                           validators=names,parameters=parameters,config=config,problem_type=rule.problem_type)


# ---------------------------------------------------------------------------
# ProblemInstance 생성기 호환 API와 안전한 정답 계산기
# ---------------------------------------------------------------------------

MathValidationError = ValueError
MathValidationResult = ValidationResult
MathValidationReport = ValidationReport
ValidatorFunction = Callable[[Any, Mapping[str, Any], Mapping[str, Any]], ValidationResult]

VALIDATOR_REGISTRY: dict[str, ValidatorFunction] = {}
VALIDATOR_ANSWER_TYPES: dict[str, set[str]] = {}


def _parameter_values(values: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if not key.startswith('__')}


def _validator_adapter(name: str) -> ValidatorFunction:
    def adapter(answer, values, config):
        parameters = _parameter_values(values)
        problem_type = config.get('problem_type') or values.get('__problem_type__')
        expected = values.get('__reference_answer__')
        generic = {
            'scalar_equality_check', 'boolean_equality', 'choice_equality',
            'matrix_equivalence', 'vector_equivalence',
            'symbolic_equivalence', 'symbolic_noncommutative_expansion',
            'equation_equivalence', 'numeric_equality',
        }
        try:
            if expected is None and name in generic:
                if not isinstance(problem_type, str):
                    raise ValueError(
                        f'{name}에는 problem_type 또는 __reference_answer__가 필요합니다.'
                    )
                expected = reference_answer(problem_type, parameters)
            passed = bool(_check(
                name, answer, expected, parameters, dict(config), problem_type
            ))
            return ValidationResult(name, passed, '' if passed else 'Mathematical check failed')
        except Exception as exc:
            return ValidationResult(name, False, f'{type(exc).__name__}: {exc}')
    return adapter


def register_validator(
    name: str,
    function: ValidatorFunction,
    *,
    allowed_answer_types: set[str],
) -> None:
    """Validator 함수와 허용 답 유형을 Registry에 등록한다."""
    if not isinstance(name, str) or not name or not callable(function):
        raise ValueError('Validator 이름과 호출 가능한 함수가 필요합니다.')
    if not allowed_answer_types or any(not isinstance(v, str) for v in allowed_answer_types):
        raise ValueError('허용 답 유형을 하나 이상 지정해야 합니다.')
    if name in VALIDATOR_REGISTRY:
        raise ValueError(f'중복 Validator: {name}')
    VALIDATOR_REGISTRY[name] = function
    VALIDATOR_ANSWER_TYPES[name] = set(allowed_answer_types)


def get_validator(name: str, answer_type: str) -> ValidatorFunction:
    """답 유형에 사용할 수 있는 등록 Validator를 반환한다."""
    if name not in VALIDATOR_REGISTRY:
        raise ValueError(f'미등록 Validator: {name}')
    if answer_type not in VALIDATOR_ANSWER_TYPES[name]:
        raise ValueError(f'{name}은 answer_type={answer_type!r}에 사용할 수 없습니다.')
    return VALIDATOR_REGISTRY[name]


def _install_policy_validators() -> None:
    from app.problems.validator_policy import ALLOWED_VALIDATORS

    by_name: dict[str, set[str]] = {}
    for answer_type, names in ALLOWED_VALIDATORS.items():
        for name in names:
            by_name.setdefault(name, set()).add(answer_type)
    for name, answer_types in by_name.items():
        register_validator(
            name,
            _validator_adapter(name),
            allowed_answer_types=answer_types,
        )


def _ensure_finite(value: Any, *, allow_symbols: bool = True) -> None:
    if isinstance(value, (str, bool, np.bool_)) or value is sp.true or value is sp.false:
        return
    if isinstance(value, Mapping):
        for item in value.values():
            _ensure_finite(item, allow_symbols=allow_symbols)
        return
    if isinstance(value, (list, tuple, sp.Tuple, sp.FiniteSet, sp.MatrixBase, np.ndarray)):
        for item in value:
            _ensure_finite(item, allow_symbols=allow_symbols)
        return
    if value is sp.EmptySet:
        return
    if isinstance(value, sp.Equality):
        _ensure_finite(value.lhs, allow_symbols=allow_symbols)
        _ensure_finite(value.rhs, allow_symbols=allow_symbols)
        return
    result = scalar(value)
    if result.has(sp.nan, sp.zoo, sp.oo, -sp.oo):
        raise ValueError('NaN 또는 무한대 결과는 허용하지 않습니다.')
    if result.free_symbols:
        if not allow_symbols:
            raise ValueError('샘플 값이 대입되지 않은 기호가 있습니다.')
        return
    if result.is_finite is not True:
        raise ValueError('결과의 유한성을 확정할 수 없습니다.')


def canonicalize_answer(
    answer: Any,
    *,
    method: str | None = None,
    config: Mapping[str, Any] | None = None,
) -> Any:
    """스칼라·벡터·행렬·해집합을 비교 가능한 표준 형태로 바꾼다."""
    if config:
        raise ValueError('canonicalize_answer의 추가 config는 아직 지원하지 않습니다.')
    allowed = {None, 'none', 'simplify', 'expand', 'factor', 'cancel', 'together', 'sorted', 'sort'}
    if method not in allowed:
        raise ValueError(f'미지원 canonicalization: {method}')
    _ensure_finite(answer)
    if method in {'sorted', 'sort'}:
        if not isinstance(answer, (list, tuple, sp.Tuple, sp.FiniteSet)):
            raise ValueError('정렬 canonicalization은 목록에만 사용할 수 있습니다.')
        return tuple(sorted(answer, key=sp.default_sort_key))
    operation = {
        'simplify': sp.simplify,
        'expand': sp.expand,
        'factor': sp.factor,
        'cancel': sp.cancel,
        'together': sp.together,
    }.get(method)

    def visit(value):
        if isinstance(value, sp.MatrixBase):
            return value.applyfunc(visit)
        if isinstance(value, list):
            return [visit(item) for item in value]
        if isinstance(value, tuple):
            return tuple(visit(item) for item in value)
        if isinstance(value, Mapping):
            return {key: visit(item) for key, item in value.items()}
        if isinstance(value, sp.FiniteSet):
            return sp.FiniteSet(*(visit(item) for item in value))
        if isinstance(value, sp.Equality):
            return sp.Eq(visit(value.lhs), visit(value.rhs), evaluate=False)
        if isinstance(value, (str, bool, np.bool_)) or value is sp.true or value is sp.false:
            return value
        return operation(value) if operation else value

    return visit(answer)


def are_symbolically_equivalent(left: Any, right: Any) -> bool:
    if isinstance(left, sp.Equality) or isinstance(right, sp.Equality):
        if not isinstance(left, sp.Equality) or not isinstance(right, sp.Equality):
            return False
        lhs = left.lhs - left.rhs
        rhs = right.lhs - right.rhs
        return equal(lhs, rhs) or equal(lhs, -rhs)
    if isinstance(left, sp.Set) or isinstance(right, sp.Set):
        return isinstance(left, sp.Set) and isinstance(right, sp.Set) and (
            left == right or sp.SymmetricDifference(left, right) == sp.EmptySet
        )
    return equal(left, right)


def are_numerically_equivalent(
    left: Any,
    right: Any,
    *,
    absolute_tolerance: float = 1e-9,
    relative_tolerance: float = 1e-9,
) -> bool:
    return equal(left, right, {
        'numeric': True,
        'atol': absolute_tolerance,
        'rtol': relative_tolerance,
    })


def are_vectors_equivalent(
    left: Any,
    right: Any,
    *,
    allow_nonzero_scalar_multiple: bool = False,
) -> bool:
    a, b = vector(left), vector(right)
    if a.shape != b.shape:
        return False
    if not allow_nonzero_scalar_multiple:
        return equal(a, b)
    if a == sp.zeros(a.rows, 1) or b == sp.zeros(b.rows, 1):
        return False
    pivot = next((index for index, item in enumerate(b) if item != 0), None)
    if pivot is None:
        return False
    ratio = sp.simplify(a[pivot] / b[pivot])
    return ratio != 0 and equal(a, ratio * b)


def are_matrices_equivalent(left: Any, right: Any) -> bool:
    return equal(matrix(left), matrix(right))


def _orthogonal_diagonalize(A):
    A = real_symmetric(matrix(A))
    columns_out, eigenvalues = [], []
    for eigenvalue, _, basis in A.eigenvects():
        orthonormal = sp.GramSchmidt(basis, True)
        columns_out.extend(orthonormal)
        eigenvalues.extend([eigenvalue] * len(orthonormal))
    if len(columns_out) != A.rows:
        raise ValueError('완전한 고유기저를 얻지 못했습니다.')
    return sp.Matrix.hstack(*columns_out), sp.diag(*eigenvalues)


def _spectral_decomposition(A):
    A = real_symmetric(matrix(A))
    Q, D = _orthogonal_diagonalize(A)
    projectors: dict[Any, sp.MatrixBase] = {}
    for column in range(Q.cols):
        eigenvalue = D[column, column]
        projector = Q[:, column] * Q[:, column].H
        projectors[eigenvalue] = projectors.get(eigenvalue, sp.zeros(A.rows)) + projector
    return list(projectors.items())


def _gram_schmidt(V):
    V = matrix(V)
    if V.rank() != V.cols:
        raise ValueError('Gram-Schmidt 입력은 선형독립이어야 합니다.')
    return sp.GramSchmidt([V[:, column] for column in range(V.cols)], True)


def _is_consistent(A, b):
    A, b = matrix(A), vector(b)
    if A.rows != b.rows:
        raise ValueError('연립방정식의 차원이 맞지 않습니다.')
    return A.rank() == A.row_join(b).rank()


def _is_consistent_augmented(augmented):
    augmented = matrix(augmented)
    if augmented.cols < 2:
        raise ValueError('첨가행렬에는 계수 열과 상수 열이 필요합니다.')
    return _is_consistent(augmented[:, :-1], augmented[:, -1])


def _principal_axis_quadratic_form(A):
    A = real_symmetric(matrix(A))
    _, diagonal = _orthogonal_diagonalize(A)
    variables = sp.symbols(f'y1:{A.rows + 1}', real=True)
    return sum(diagonal[index, index] * variables[index] ** 2 for index in range(A.rows))


def _safe_equation(left, right):
    return sp.Eq(left, right, evaluate=False)


def _advanced_svd(A):
    """Exact SVD for the small signed-permutation matrix generator."""
    A = matrix(A)
    if A.shape != (2, 2) or (A.H*A).is_diagonal() is not True:
        raise ValueError('Only the 2x2 signed-permutation SVD family is supported')
    lengths = [(sp.sqrt((A.H*A)[i, i]), i) for i in range(2)]
    lengths.sort(key=lambda item: int(item[0]), reverse=True)
    if lengths[0][0] <= lengths[1][0] or lengths[1][0] <= 0:
        raise ValueError('Distinct positive singular values are required')
    V = sp.eye(2)[:, [item[1] for item in lengths]]
    S = sp.diag(*(item[0] for item in lengths))
    U = A*V*S.inv()
    return U, S, V


def _compact_svd_rank_one(A):
    U, S, V = _advanced_svd(A)
    return U[:, :1] * S[0, 0] * V[:, :1].H


def _jordan_defective_pair(A):
    A = matrix(A)
    if A.shape != (2, 2) or A[1, 0] != 0 or A[0, 0] != A[1, 1] or A[0, 1] == 0:
        raise ValueError('Expected a defective 2x2 Jordan family')
    P = sp.diag(A[0, 1], 1)
    J = sp.Matrix([[A[0, 0], 1], [0, A[0, 0]]])
    return P, J


def _pca_covariance(A):
    A = matrix(A)
    if A.rows < 2 or any(sum(A[:, j]) != 0 for j in range(A.cols)):
        raise ValueError('Expected mean-centered samples')
    return A.T*A/(A.rows-1)


def _pca_projection(A):
    C = _pca_covariance(A)
    eigenspaces = C.eigenvects()
    if len(eigenspaces) != 2:
        raise ValueError('A unique leading principal component is required')
    largest, _, vectors = max(eigenspaces, key=lambda item: item[0])
    v = vectors[0]
    return v*v.H/(v.H*v)[0]


_CALC_FUNCTIONS = {
    'complex_inner_product': lambda u, v: (vector(u).H*vector(v))[0],
    'jordan_defective_pair': _jordan_defective_pair,
    'advanced_svd': _advanced_svd,
    'compact_svd_rank_one': _compact_svd_rank_one,
    'pca_projection': _pca_projection,
    'moore_penrose_pinv': lambda A: matrix(A).pinv(),
    'eye': sp.eye,
    'zeros': sp.zeros,
    'ones': sp.ones,
    'diag': sp.diag,
    'Matrix': lambda value: matrix(value),
    'Abs': sp.Abs,
    'abs': sp.Abs,
    'sqrt': sp.sqrt,
    'Rational': sp.Rational,
    'Integer': sp.Integer,
    'Min': sp.Min,
    'Max': sp.Max,
    'min': min,
    'max': max,
    'len': len,
    'list': list,
    'tuple': tuple,
    'sum': sum,
    'all': lambda items: all(boolean(item) for item in items),
    'any': lambda items: any(boolean(item) for item in items),
    'Eq': _safe_equation,
    'simplify': sp.simplify,
    'expand': sp.expand,
    'factor': sp.factor,
    'linsolve': sp.linsolve,
    'gram_schmidt': _gram_schmidt,
    'diagonalize_pair': lambda A: matrix(A).diagonalize(),
    'orthogonal_diagonalize_pair': _orthogonal_diagonalize,
    'spectral_decomposition': _spectral_decomposition,
    'is_consistent': _is_consistent,
    'is_consistent_augmented': _is_consistent_augmented,
    'free_variable_indices': lambda A: [
        index for index in range(matrix(A).cols)
        if index not in matrix(A).rref()[1]
    ],
    'is_ref': lambda A: bool(matrix(A).is_echelon),
    'is_zero_vector': lambda value: vector(value) == sp.zeros(vector(value).rows, 1),
    'is_subspace_solution_set': lambda A, b: (
        matrix(A).rows == vector(b).rows
        and vector(b) == sp.zeros(vector(b).rows, 1)
    ),
    'principal_axis_quadratic_form': _principal_axis_quadratic_form,
}

_MATRIX_METHODS = {
    'det': set(), 'rank': set(), 'inv': set(), 'rref': set(),
    'nullspace': set(), 'columnspace': set(), 'rowspace': set(),
    'eigenvals': set(), 'eigenvects': set(), 'LUsolve': set(),
    'LUdecomposition': set(), 'QRdecomposition': set(),
    'diagonalize': set(), 'dot': set(), 'norm': set(), 'trace': set(),
    'transpose': set(), 'conjugate': set(),
    'elementary_row_op': {'op', 'row', 'row1', 'row2', 'k'},
}


def _evaluate_expression(expression: str, values: Mapping[str, Any]) -> Any:
    try:
        tree = ast.parse(expression, mode='eval')
    except SyntaxError as exc:
        raise ValueError('정답 계산식 문법 오류') from exc

    def evaluate(node, environment):
        if isinstance(node, ast.Constant):
            if type(node.value) is int:
                return sp.Integer(node.value)
            if isinstance(node.value, (float, str, bool)) or node.value is None:
                return node.value
            raise ValueError('미지원 상수 타입')
        if isinstance(node, ast.Name):
            if node.id in environment:
                value = environment[node.id]
                if callable(value):
                    raise ValueError('파라미터로 전달된 호출 객체는 사용할 수 없습니다.')
                return value
            constants = {'I': sp.I, 'pi': sp.pi, 'E': sp.E, 'True': True, 'False': False}
            if node.id in constants:
                return constants[node.id]
            raise ValueError(f'미선언 계산식 변수: {node.id}')
        if isinstance(node, (ast.List, ast.Tuple)):
            output = [evaluate(item, environment) for item in node.elts]
            return output if isinstance(node, ast.List) else tuple(output)
        if isinstance(node, ast.Dict):
            if any(key is None for key in node.keys):
                raise ValueError('dict 확장은 허용하지 않습니다.')
            return {
                evaluate(key, environment): evaluate(value, environment)
                for key, value in zip(node.keys, node.values)
            }
        if isinstance(node, ast.UnaryOp):
            value = evaluate(node.operand, environment)
            if isinstance(node.op, ast.Not):
                return not boolean(value)
            if isinstance(node.op, ast.USub):
                return -value
            if isinstance(node.op, ast.UAdd):
                return +value
        if isinstance(node, ast.BinOp):
            left = evaluate(node.left, environment)
            right = evaluate(node.right, environment)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, (ast.Mult, ast.MatMult)):
                return left * right
            if isinstance(node.op, ast.Div):
                if right == 0:
                    raise ValueError('계산식의 0 나눗셈')
                if isinstance(left, (int, sp.Integer)) and isinstance(right, (int, sp.Integer)):
                    return sp.Rational(left, right)
                return left / right
            if isinstance(node.op, ast.Pow):
                return left ** right
        if isinstance(node, ast.BoolOp):
            items = (boolean(evaluate(item, environment)) for item in node.values)
            if isinstance(node.op, ast.And):
                return all(items)
            if isinstance(node.op, ast.Or):
                return any(items)
        if isinstance(node, ast.IfExp):
            branch = node.body if boolean(evaluate(node.test, environment)) else node.orelse
            return evaluate(branch, environment)
        if isinstance(node, ast.Compare):
            left = evaluate(node.left, environment)
            for operator, comparator in zip(node.ops, node.comparators):
                right = evaluate(comparator, environment)
                if isinstance(operator, ast.Eq):
                    result = left == right if isinstance(left, (str, bool)) else are_symbolically_equivalent(left, right)
                elif isinstance(operator, ast.NotEq):
                    result = not (left == right if isinstance(left, (str, bool)) else are_symbolically_equivalent(left, right))
                elif isinstance(operator, ast.Lt):
                    result = left < right
                elif isinstance(operator, ast.LtE):
                    result = left <= right
                elif isinstance(operator, ast.Gt):
                    result = left > right
                elif isinstance(operator, ast.GtE):
                    result = left >= right
                else:
                    raise ValueError('미지원 비교식')
                if not boolean(result):
                    return False
                left = right
            return True
        if isinstance(node, ast.Attribute):
            target = evaluate(node.value, environment)
            if isinstance(target, sp.MatrixBase) and node.attr in {'rows', 'cols', 'T', 'H', 'shape'}:
                return getattr(target, node.attr)
            raise ValueError(f'미지원 속성: {node.attr}')
        if isinstance(node, ast.Slice):
            values_out = [
                evaluate(item, environment) if item is not None else None
                for item in (node.lower, node.upper, node.step)
            ]
            return slice(*values_out)
        if isinstance(node, ast.Subscript):
            return evaluate(node.value, environment)[evaluate(node.slice, environment)]
        if isinstance(node, (ast.GeneratorExp, ast.ListComp)):
            if len(node.generators) != 1:
                raise ValueError('단일 comprehension만 지원합니다.')
            generator = node.generators[0]
            if generator.is_async or not isinstance(generator.target, ast.Name):
                raise ValueError('미지원 comprehension 대상')
            output = []
            for item in evaluate(generator.iter, environment):
                local = dict(environment)
                local[generator.target.id] = item
                if all(boolean(evaluate(test, local)) for test in generator.ifs):
                    output.append(evaluate(node.elt, local))
            return output
        if isinstance(node, ast.Call):
            if any(keyword.arg is None for keyword in node.keywords):
                raise ValueError('**kwargs는 허용하지 않습니다.')
            args = [evaluate(item, environment) for item in node.args]
            kwargs = {keyword.arg: evaluate(keyword.value, environment) for keyword in node.keywords}
            if isinstance(node.func, ast.Name):
                name = node.func.id
                if name not in _CALC_FUNCTIONS or kwargs:
                    raise ValueError(f'미지원 계산 함수 또는 keyword: {name}')

                def reject_string(value):
                    if isinstance(value, str):
                        raise ValueError('수학 함수의 문자열 인자는 허용하지 않습니다.')
                    if isinstance(value, (list, tuple)):
                        for child in value:
                            reject_string(child)

                if name in {
                    'Rational', 'Integer', 'sqrt', 'Abs', 'abs', 'Min', 'Max',
                    'simplify', 'expand', 'factor', 'diag', 'eye', 'zeros',
                    'ones', 'linsolve', 'Eq',
                }:
                    for item in args:
                        reject_string(item)
                return _CALC_FUNCTIONS[name](*args)
            if isinstance(node.func, ast.Attribute):
                if (
                    isinstance(node.func.value, ast.Name)
                    and node.func.value.id == 'Matrix'
                    and node.func.attr in {'hstack', 'vstack'}
                ):
                    if kwargs:
                        raise ValueError('Matrix stack keyword는 허용하지 않습니다.')
                    return getattr(sp.Matrix, node.func.attr)(*(matrix(item) for item in args))
                target = evaluate(node.func.value, environment)
                method = node.func.attr
                if method == 'keys' and isinstance(target, Mapping) and not args and not kwargs:
                    return list(target.keys())
                if (
                    not isinstance(target, sp.MatrixBase)
                    or method not in _MATRIX_METHODS
                    or set(kwargs) - _MATRIX_METHODS[method]
                ):
                    raise ValueError(f'미지원 계산 메서드: {method}')
                for index, item in enumerate(args):
                    if isinstance(item, str) and not (method == 'elementary_row_op' and index == 0):
                        raise ValueError('행렬 메서드의 수학 인자에 문자열을 사용할 수 없습니다.')
                for key, item in kwargs.items():
                    if isinstance(item, str) and not (method == 'elementary_row_op' and key == 'op'):
                        raise ValueError('행렬 메서드의 수학 keyword에 문자열을 사용할 수 없습니다.')
                return getattr(target, method)(*args, **kwargs)
        raise ValueError(f'미지원 AST 구문: {type(node).__name__}')

    return evaluate(tree.body, dict(values))


def compute_expected_answer(
    answer_spec: AnswerTemplateSpec,
    values: Mapping[str, Any],
) -> Any:
    """허용 목록 기반 AST 해석기로 Template의 정답을 계산한다."""
    if answer_spec.engine not in {'sympy', 'python'}:
        raise ValueError(
            f'현재 활성 선형대수 정답 엔진은 sympy/python뿐입니다: {answer_spec.engine}'
        )
    expression = answer_spec.cas_template
    if not isinstance(expression, str) or not expression.strip():
        raise ValueError('answer_spec.cas_template이 필요합니다.')
    validate_validator_mapping(
        answer_spec.answer_type,
        answer_spec.required_checks,
        require_nonempty=False,
    )
    result = _evaluate_expression(expression, values)
    symbolic = answer_spec.answer_type in {'expression', 'equation', 'vector_expression'}
    _ensure_finite(result, allow_symbols=symbolic)
    return canonicalize_answer(
        result,
        method=answer_spec.canonicalization.method,
    )


def run_math_validators(
    expected_answer: Any,
    values: Mapping[str, Any],
    validators: Sequence[ValidatorTemplate],
    *,
    all_required_must_pass: bool = True,
    answer_type: str | None = None,
    required_checks: Sequence[str] = (),
    problem_type: str | None = None,
) -> ValidationReport:
    """ProblemTemplate의 Validator 설정을 fail-closed 방식으로 실행한다."""
    kind = answer_type or values.get('__answer_type__')
    selected_problem_type = problem_type or values.get('__problem_type__')
    if not isinstance(kind, str) or not kind:
        return ValidationReport((ValidationResult(
            'validator_mapping', False, 'answer_type을 명시해야 합니다.'
        ),))
    if not validators or not any(item.required for item in validators):
        return ValidationReport((ValidationResult(
            'validator_mapping', False, '필수 Validator가 하나 이상 필요합니다.'
        ),))
    if not all_required_must_pass:
        return ValidationReport((ValidationResult(
            'validator_mapping', False,
            '현재 수학 검증 정책은 모든 필수 Validator 통과만 허용합니다.'
        ),))
    names = tuple(item.name for item in validators)
    required_names = {item.name for item in validators if item.required}
    if any(not item.required for item in validators):
        return ValidationReport((ValidationResult(
            'validator_mapping', False, '선택 Validator는 현재 지원하지 않습니다.'
        ),))
    if set(required_checks) - required_names:
        missing = sorted(set(required_checks) - required_names)
        return ValidationReport((ValidationResult(
            'validator_mapping', False,
            f'필수 검증이 실행 목록에 없습니다: {missing}'
        ),))
    configs = {item.name: dict(item.config) for item in validators}
    parameters = _parameter_values(values)
    generic = {
        'scalar_equality_check', 'boolean_equality', 'choice_equality',
        'matrix_equivalence', 'vector_equivalence',
        'symbolic_equivalence', 'symbolic_noncommutative_expansion',
        'equation_equivalence', 'numeric_equality',
    }
    reference = values.get('__reference_answer__')
    try:
        if reference is None and set(names) & generic:
            if not isinstance(selected_problem_type, str):
                raise ValueError('일반 동치 Validator에는 problem_type이 필요합니다.')
            reference = reference_answer(selected_problem_type, parameters)
    except Exception as exc:
        return ValidationReport((ValidationResult(
            'rule_context', False, f'{type(exc).__name__}: {exc}'
        ),))
    return validate_answer(
        expected_answer,
        reference,
        answer_type=kind,
        validators=names,
        parameters=parameters,
        config=configs,
        problem_type=selected_problem_type,
    )


def validate_by_substitution(answer, values, config) -> ValidationResult:
    passed = _check('linear_system_check', answer, None, values, config, 'solve_by_lu')
    return ValidationResult('validate_by_substitution', bool(passed))


def validate_inverse(answer, values, config) -> ValidationResult:
    A = square(matrix(values['A']))
    passed = equal(matrix(answer) * A, sp.eye(A.rows), config) and equal(
        A * matrix(answer), sp.eye(A.rows), config
    )
    return ValidationResult('validate_inverse', bool(passed))


def validate_eigenpair(answer, values, config) -> ValidationResult:
    A = square(matrix(values['A']))
    if isinstance(answer, Mapping):
        eigenvalue = scalar(answer['eigenvalue'])
        eigenvector = vector(answer['eigenvector'])
    elif isinstance(answer, (list, tuple)) and len(answer) == 2:
        eigenvalue, eigenvector = scalar(answer[0]), vector(answer[1])
    else:
        eigenvalue = scalar(values['lambda_val'])
        eigenvector = vector(answer)
    passed = (
        eigenvector != sp.zeros(eigenvector.rows, 1)
        and eigenvector.rows == A.cols
        and equal(A * eigenvector, eigenvalue * eigenvector, config)
    )
    return ValidationResult('validate_eigenpair', bool(passed))


def validate_projection(answer, values, config) -> ValidationResult:
    passed = _check(
        'projection_check', answer, None, values, config,
        'orthogonal_projection_calculation',
    )
    return ValidationResult('validate_projection', bool(passed))


def validate_matrix_factorization(answer, values, config) -> ValidationResult:
    kind = config.get('kind')
    mapping = {
        'lu': ('lu_factorization_check', 'lu_factorization'),
        'qr': ('qr_factorization_check', 'qr_factorization_calculation'),
        'diagonalization': ('diagonalization_check', 'matrix_diagonalization'),
        'orthogonal_diagonalization': (
            'orthogonal_diagonalization_check',
            'orthogonal_diagonalization_calculation',
        ),
        'spectral': ('spectral_decomposition_check', 'spectral_decomposition_calculation'),
    }
    if kind not in mapping:
        raise ValueError('분해 kind를 명시해야 합니다.')
    validator_name, problem_type = mapping[kind]
    passed = _check(validator_name, answer, None, values, config, problem_type)
    return ValidationResult('validate_matrix_factorization', bool(passed))


_install_policy_validators()
