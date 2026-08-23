from __future__ import annotations

from app.schemas.generation_rule import GenerationRule


LINEAR_ALGEBRA_RULES: dict[str, GenerationRule] = {
    "matrix_multiplication": GenerationRule(
        rule_id="linear_algebra.matrix_multiplication.v1",
        subject_id="linear_algebra",
        problem_type="matrix_multiplication",
        supported_answer_types=["matrix"],
        parameter_spec={
            "A": {
                "type": "matrix",
                "description": "2x2~3x3 정수 행렬",
                "rows_min": 2,
                "rows_max": 3,
                "cols_min": 2,
                "cols_max": 3,
                "element_type": "integer",
                "element_min": -5,
                "element_max": 5,
            },
            "B": {
                "type": "matrix",
                "description": "A와 곱셈 가능한 정수 행렬",
                "rows_min": 2,
                "rows_max": 3,
                "cols_min": 2,
                "cols_max": 3,
                "element_type": "integer",
                "element_min": -5,
                "element_max": 5,
            },
        },
        constraints=[
            {
                "type": "dimension_match",
                "expression": "A.cols == B.rows",
                "required": True,
                "description": "행렬 곱 AB가 정의되어야 한다.",
            }
        ],
        construction={
            "operation": "matrix_multiplication",
            "required_objects": ["A", "B"],
            "semantic_structure": [
                "두 행렬 A와 B를 제시한다.",
                "행렬의 곱 AB를 계산하도록 요구한다.",
            ],
            "text_templates": [
                "다음 두 행렬 A와 B에 대하여 AB를 구하여라.",
                "주어진 행렬 A, B의 곱 AB를 계산하여라.",
            ],
        },
        answer_spec={
            "answer_type": "matrix",
            "engine": "sympy",
            "expression": "A * B",
            "canonicalization": "simplify",
        },
        validation={
            "validators": ["dimension_valid", "matrix_equivalence"],
            "all_required": True,
            "max_generation_attempts": 100,
        },
        difficulty={
            "min": 1,
            "max": 4,
            "factors": {
                "matrix_size": {
                    "easy": "2x2",
                    "medium": "2x3_or_3x2",
                    "hard": "3x3",
                },
                "element_range": {
                    "easy": [-3, 3],
                    "medium": [-5, 5],
                    "hard": [-10, 10],
                },
                "negative_values": {"easy": False, "hard": True},
            },
        },
    ),
}
