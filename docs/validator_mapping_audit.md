# 선형대수 Validator 매핑 검수

문제 문장과 정답식을 기준으로 curated 56개를 검수했습니다. 샘플러, 공식, 상태 승격의 검수 완료를 뜻하지 않습니다.

| Rule | 기존 | 수정 |
| --- | --- | --- |
| `algebraic_expansion_verification` | symbolic_noncommutative_expansion | symbolic_noncommutative_expansion |
| `basis_verification` | rank_matrix_check | boolean_equality |
| `block_matrix_determinant` | determinant_check | scalar_equality_check |
| `change_of_basis_calculation` | matrix_inverse_check | matrix_equivalence |
| `column_space_basis` | span_equivalence_check | basis_equivalence |
| `consistency_check` | consistency_theorem_check | choice_equality |
| `cramer_rule_solution` | cramer_solution_check | linear_system_check |
| `determinant_by_ero` | determinant_check | scalar_equality_check |
| `determinant_cofactor_expansion` | determinant_check | scalar_equality_check |
| `eigenvalue_calculation` | characteristic_polynomial_check | eigenvalue_check |
| `eigenvector_calculation` | matrix_multiplication_zero_check | basis_equivalence |
| `elementary_inverse_calculation` | matrix_equivalence | matrix_equivalence |
| `elementary_matrix_construction` | matrix_equivalence | matrix_equivalence |
| `equation_to_matrix` | symbolic_equivalence | matrix_equivalence |
| `equivalence_theorem_check` | logical_equivalence_check | boolean_equality |
| `ero_application` | matrix_equivalence | matrix_equivalence |
| `free_variable_identification` | null_space_check | index_set_check |
| `geometric_area_volume_calculation` | absolute_value_check | scalar_equality_check |
| `gram_schmidt_orthogonalization` | pairwise_orthogonality_check | gram_schmidt_check |
| `inverse_calculation` | matrix_inverse_check | matrix_equivalence |
| `invertibility_determination` | logical_equivalence_check | choice_equality |
| `kernel_image_calculation` | rank_nullity_check | kernel_image_check |
| `least_squares_calculation` | normal_equation_residual_check | least_squares_check |
| `left_null_space_basis` | matrix_multiplication_zero_check | basis_equivalence |
| `linear_independence_test` | rank_matrix_check | boolean_equality |
| `linear_regression_calculation` | regression_residual_check | least_squares_check |
| `linear_transformation_verification` | superposition_check | boolean_equality |
| `lu_factorization` | matrix_multiplication_check, lower_triangular_check | lu_factorization_check |
| `matrix_diagonalization` | matrix_equivalence | diagonalization_check |
| `matrix_multiplication` | matrix_equivalence | matrix_equivalence |
| `matrix_power_calculation` | matrix_equivalence | matrix_equivalence |
| `matrix_rank_property` | rank_computation_check | scalar_equality_check |
| `matrix_to_vector_equation` | symbolic_equivalence | equation_equivalence |
| `norm_distance_calculation` | scalar_equality_check | scalar_equality_check |
| `null_space_basis` | matrix_multiplication_zero_check | basis_equivalence |
| `orthogonal_complement_calculation` | dot_product_zero_check | basis_equivalence |
| `orthogonal_diagonalization_calculation` | orthogonal_matrix_check | orthogonal_diagonalization_check |
| `orthogonal_projection_calculation` | idempotent_symmetric_check | projection_check |
| `orthonormal_verification` | matrix_product_identity_check | boolean_equality |
| `parametric_solution_extraction` | linear_combination_equivalence, null_space_check | parametric_solution_check |
| `positive_definite_test` | eigenvalue_sign_check | boolean_equality |
| `qr_factorization_calculation` | qr_product_check | qr_factorization_check |
| `quadratic_form_transformation` | quadratic_form_equivalence | quadratic_form_check |
| `rank_calculation` | rank_computation_check | scalar_equality_check |
| `rank_nullity_calculation` | dimension_equality_check | scalar_equality_check |
| `ref_identification` | ref_form_check | boolean_equality |
| `row_space_basis` | span_equivalence_check | basis_equivalence |
| `rref_calculation` | rref_form_check | matrix_equivalence |
| `singular_matrix_identification` | zero_row_detection | boolean_equality |
| `solve_by_lu` | matrix_multiplication_check | linear_system_check |
| `span_membership_test` | consistency_theorem_check | boolean_equality |
| `spectral_decomposition_calculation` | matrix_equivalence | spectral_decomposition_check |
| `standard_matrix_derivation` | matrix_multiplication_check | matrix_equivalence |
| `subspace_verification` | subspace_axiom_check | boolean_equality |
| `symmetry_classification` | matrix_equivalence | boolean_equality |
| `transpose_algebra` | matrix_equivalence | matrix_equivalence |
