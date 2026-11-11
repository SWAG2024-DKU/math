"""Static answer contracts. No CAS import is needed to validate a catalog."""
from __future__ import annotations

ALLOWED_VALIDATORS = {
    'scalar': {'scalar_equality_check', 'numeric_equality', 'domain_check', 'complex_inner_product_check'},
    'expression': {'symbolic_equivalence', 'symbolic_noncommutative_expansion', 'quadratic_form_check', 'domain_check'},
    'equation': {'equation_equivalence'},
    'boolean': {'boolean_equality'},
    'single_choice': {'choice_equality'},
    'multiple_choice': {'choice_equality'},
    'matrix': {'matrix_equivalence', 'dimension_valid', 'lu_factorization_check',
               'compact_svd_optimality_check', 'moore_penrose_conditions_check', 'pca_projection_check'},
    'vector': {'vector_equivalence', 'linear_system_check', 'least_squares_check', 'projection_check'},
    'vector_list': {'basis_equivalence', 'kernel_image_check', 'gram_schmidt_check'},
    'vector_expression': {'index_set_check', 'parametric_solution_check'},
    'scalar_list': {'eigenvalue_check'},
    'matrix_pair': {'diagonalization_check', 'orthogonal_diagonalization_check', 'qr_factorization_check', 'jordan_similarity_check'},
    'matrix_tuple': {'svd_reconstruction_check'},
    'matrix_list': {'spectral_decomposition_check'},
    'set': {'set_equivalence'},
    'interval': {'set_equivalence'},
}

# 새 과목의 구현된 검사만 허용한다. 개별 Rule 매핑은 검수 후 JSON에 명시한다.
NEW_VALIDATOR_ANSWER_TYPES = {
    'derivative_check': {'scalar', 'expression'},
    'antiderivative_check': {'expression'},
    'definite_integral_check': {'scalar'},
    'limit_check': {'scalar'},
    'series_sum_check': {'scalar'},
    'multiple_integral_check': {'scalar'},
    'gradient_check': {'vector_expression'},
    'divergence_check': {'expression', 'scalar'},
    'curl_check': {'vector_expression'},
    'ode_solution_check': {'equation', 'expression'},
    'laplace_transform_check': {'expression'},
    'fourier_transform_check': {'expression'},
    'expectation_check': {'scalar'},
    'variance_check': {'scalar'},
    'probability_mass_check': {'scalar'},
    'sample_statistic_check': {'scalar'},
}
ALLOWED_VALIDATORS.setdefault('classification',set())
NEW_VALIDATOR_ANSWER_TYPES['calculus_relation_check']={'scalar','expression','equation','boolean','classification'}
NEW_VALIDATOR_ANSWER_TYPES['calculus_remaining_check']={'scalar','expression','equation','boolean','classification','set','interval','numerical_approximation'}
ALLOWED_VALIDATORS.setdefault('numerical_approximation',set())
NEW_VALIDATOR_ANSWER_TYPES['calculus_2_check']={'scalar','expression','equation','boolean','classification','set','interval','vector','numerical_approximation'}
NEW_VALIDATOR_ANSWER_TYPES['probability_statistics_check']={'scalar','boolean','interval','single_choice'}
ALLOWED_VALIDATORS.setdefault('string',set())
NEW_VALIDATOR_ANSWER_TYPES['engineering_mathematics_check']={'scalar','scalar_list','expression','boolean','vector','vector_list','matrix','string'}
for _name, _types in NEW_VALIDATOR_ANSWER_TYPES.items():
    for _type in _types:
        ALLOWED_VALIDATORS[_type].add(_name)

# Explicitly reviewed against each curated rule's question and answer expression.
RULE_VALIDATORS = {
    'compact_svd_approximation': ('compact_svd_optimality_check',),
    'complex_inner_product_calculation': ('complex_inner_product_check',),
    'jordan_canonical_form_calculation': ('jordan_similarity_check',),
    'pca_calculation': ('pca_projection_check',),
    'pseudoinverse_calculation': ('moore_penrose_conditions_check',),
    'svd_calculation': ('svd_reconstruction_check',),
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
