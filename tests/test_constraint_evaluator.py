import sympy as sp

from constraint_evaluator import (ConstraintEvaluationError,
                                  evaluate_string_constraint,
                                  is_diagonalizable, is_full_rank,
                                  is_invertible, is_linearly_independent,
                                  is_orthogonal, is_positive_definite,
                                  is_square, is_symmetric,
                                  supports_lu_without_pivoting)


def test_det_nonzero_true():
    a = sp.Matrix([[1, 2], [3, 4]])

    result = evaluate_string_constraint(
        "det(A) != 0",
        {"A": a},
    )

    assert result.passed is True


def test_det_nonzero_false():
    a = sp.Matrix([[1, 2], [2, 4]])

    result = evaluate_string_constraint(
        "det(A) != 0",
        {"A": a},
    )

    assert result.passed is False


def test_dimension_match():
    a = sp.Matrix([[1, 2], [3, 4]])
    b = sp.Matrix([[1, 2, 3], [4, 5, 6]])

    result = evaluate_string_constraint(
        "A.cols == B.rows",
        {
            "A": a,
            "B": b,
        },
    )

    assert result.passed is True


def test_rank_method_expression():
    v = sp.Matrix([[1, 0], [0, 1], [1, 1]])

    result = evaluate_string_constraint(
        "V.rank() == V.cols",
        {"V": v},
    )

    assert result.passed is True


def test_numeric_index_condition():
    result = evaluate_string_constraint(
        "source_row < n",
        {
            "source_row": 0,
            "n": 3,
        },
    )

    assert result.passed is True


def test_symmetric_true():
    a = sp.Matrix([[1, 2], [2, 3]])

    assert is_symmetric(a) is True


def test_symmetric_false():
    a = sp.Matrix([[1, 2], [3, 4]])

    assert is_symmetric(a) is False


def test_square():
    a = sp.Matrix([[1, 2], [3, 4]])
    b = sp.Matrix([[1, 2, 3], [4, 5, 6]])

    assert is_square(a) is True
    assert is_square(b) is False


def test_invertible():
    a = sp.Matrix([[1, 2], [3, 4]])
    b = sp.Matrix([[1, 2], [2, 4]])

    assert is_invertible(a) is True
    assert is_invertible(b) is False


def test_full_rank():
    a = sp.Matrix([[1, 0], [0, 1], [1, 1]])

    assert is_full_rank(a) is True


def test_linearly_independent():
    vectors = [
        sp.Matrix([1, 0, 0]),
        sp.Matrix([0, 1, 0]),
        sp.Matrix([0, 0, 1]),
    ]

    assert is_linearly_independent(vectors) is True


def test_orthogonal():
    q = sp.eye(3)

    assert is_orthogonal(q) is True


def test_positive_definite():
    a = sp.Matrix([[2, 0], [0, 3]])

    assert is_positive_definite(a) is True


def test_diagonalizable():
    a = sp.Matrix([[1, 0], [0, 2]])

    assert is_diagonalizable(a) is True


def test_lu_without_pivoting():
    a = sp.Matrix([[2, 1], [1, 3]])

    assert supports_lu_without_pivoting(a) is True


def test_dot_product_constraint():
    b = sp.Matrix([1, 2])

    result = evaluate_string_constraint(
        "b.dot(b) > 0",
        {"b": b},
    )

    assert result.passed is True


def test_unknown_variable_raises():
    try:
        evaluate_string_constraint(
            "det(Z) != 0",
            {},
        )
    except ConstraintEvaluationError:
        pass
    else:
        raise AssertionError(
            "미선언 변수는 ConstraintEvaluationError를 발생시켜야 합니다."
        )
