"""Static answer contracts. No CAS import is needed to validate a catalog."""
from __future__ import annotations

ALLOWED_VALIDATORS = {
    'scalar': {'scalar_equality_check', 'numeric_equality', 'domain_check'},
    'expression': {'symbolic_equivalence', 'symbolic_noncommutative_expansion', 'quadratic_form_check', 'domain_check'},
    'equation': {'equation_equivalence'},
    'boolean': {'boolean_equality'},
    'single_choice': {'choice_equality'},
    'multiple_choice': {'choice_equality'},
    'matrix': {'matrix_equivalence', 'dimension_valid', 'lu_factorization_check'},
    'vector': {'vector_equivalence', 'linear_system_check', 'least_squares_check', 'projection_check'},
    'vector_list': {'basis_equivalence', 'kernel_image_check', 'gram_schmidt_check'},
    'vector_expression': {'index_set_check', 'parametric_solution_check'},
    'scalar_list': {'eigenvalue_check'},
    'matrix_pair': {'diagonalization_check', 'orthogonal_diagonalization_check', 'qr_factorization_check'},
    'matrix_list': {'spectral_decomposition_check'},
    'set': {'set_equivalence'},
    'interval': {'set_equivalence'},
}

# Explicitly reviewed against each curated rule's question and answer expression.
RULE_VALIDATORS = {
    'algebraic_expansion_verification': ('symbolic_noncommutative_expansion',),
    'basis_verification': ('boolean_equality',),
    'block_matrix_determinant': ('scalar_equality_check',),
    'change_of_basis_calculation': ('matrix_equivalence',),
    'column_space_basis': ('basis_equivalence',),
    'consistency_check': ('choice_equality',),
    'cramer_rule_solution': ('linear_system_check',),
    'determinant_by_ero': ('scalar_equality_check',),
    'determinant_cofactor_expansion': ('scalar_equality_check',),
    'eigenvalue_calculation': ('eigenvalue_check',),
    'eigenvector_calculation': ('basis_equivalence',),
    'elementary_inverse_calculation': ('matrix_equivalence',),
    'elementary_matrix_construction': ('matrix_equivalence',),
    'equation_to_matrix': ('matrix_equivalence',),
    'equivalence_theorem_check': ('boolean_equality',),
    'ero_application': ('matrix_equivalence',),
    'free_variable_identification': ('index_set_check',),
    'geometric_area_volume_calculation': ('scalar_equality_check',),
    'gram_schmidt_orthogonalization': ('gram_schmidt_check',),
    'inverse_calculation': ('matrix_equivalence',),
    'invertibility_determination': ('choice_equality',),
    'kernel_image_calculation': ('kernel_image_check',),
    'least_squares_calculation': ('least_squares_check',),
    'left_null_space_basis': ('basis_equivalence',),
    'linear_independence_test': ('boolean_equality',),
    'linear_regression_calculation': ('least_squares_check',),
    'linear_transformation_verification': ('boolean_equality',),
    'lu_factorization': ('lu_factorization_check',),
    'matrix_diagonalization': ('diagonalization_check',),
    'matrix_multiplication': ('matrix_equivalence',),
    'matrix_power_calculation': ('matrix_equivalence',),
    'matrix_rank_property': ('scalar_equality_check',),
    'matrix_to_vector_equation': ('equation_equivalence',),
    'norm_distance_calculation': ('scalar_equality_check',),
    'null_space_basis': ('basis_equivalence',),
    'orthogonal_complement_calculation': ('basis_equivalence',),
    'orthogonal_diagonalization_calculation': ('orthogonal_diagonalization_check',),
    'orthogonal_projection_calculation': ('projection_check',),
    'orthonormal_verification': ('boolean_equality',),
    'parametric_solution_extraction': ('parametric_solution_check',),
    'positive_definite_test': ('boolean_equality',),
    'qr_factorization_calculation': ('qr_factorization_check',),
    'quadratic_form_transformation': ('quadratic_form_check',),
    'rank_calculation': ('scalar_equality_check',),
    'rank_nullity_calculation': ('scalar_equality_check',),
    'ref_identification': ('boolean_equality',),
    'row_space_basis': ('basis_equivalence',),
    'rref_calculation': ('matrix_equivalence',),
    'singular_matrix_identification': ('boolean_equality',),
    'solve_by_lu': ('linear_system_check',),
    'span_membership_test': ('boolean_equality',),
    'spectral_decomposition_calculation': ('spectral_decomposition_check',),
    'standard_matrix_derivation': ('matrix_equivalence',),
    'subspace_verification': ('boolean_equality',),
    'symmetry_classification': ('boolean_equality',),
    'transpose_algebra': ('matrix_equivalence',),
}


def validate_validator_mapping(answer_type: str, names, *, require_nonempty=True):
    names = tuple(names)
    if require_nonempty and not names:
        raise ValueError('At least one validator is required')
    invalid = set(names) - ALLOWED_VALIDATORS.get(answer_type, set())
    if invalid:
        raise ValueError(f'Validators not allowed for {answer_type}: {sorted(invalid)}')


def validate_curated_mapping(rule):
    validate_validator_mapping(rule.answer_spec.answer_type, rule.validation.validators)
    if rule.subject_id == 'linear_algebra' and rule.problem_type in RULE_VALIDATORS:
        if tuple(rule.validation.validators) != RULE_VALIDATORS[rule.problem_type]:
            raise ValueError(f'Unreviewed validator mapping: {rule.problem_type}')
