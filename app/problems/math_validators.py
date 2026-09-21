"""Fail-closed mathematical validation for common answers and linear algebra.

Inputs are Python/SymPy objects, not executable CAS strings. A failed or
undecidable check never passes. See docs/math_validation.md for the contract.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import math
import numbers

import numpy as np
import sympy as sp

from app.problems.validator_policy import validate_validator_mapping, validate_curated_mapping


@dataclass(frozen=True)
class ValidationResult:
    name: str
    passed: bool
    message: str = ''

    def __bool__(self):
        return self.passed


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
        # Deliberately conservative: identical residuals or swapped sides.
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
    remaining = list(targets)
    for value in values:
        for i, target in enumerate(remaining):
            if equal(value,target,config):
                remaining.pop(i)
                break
        else:
            return False
    return not remaining


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
