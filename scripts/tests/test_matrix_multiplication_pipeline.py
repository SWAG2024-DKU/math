"""실제 선형대수 행렬 곱셈 Template으로 생성 파이프라인을 검증한다.

프로젝트 루트에서 실행:
    python -m pytest -q scripts/tests/test_matrix_multiplication_pipeline.py
"""

from pathlib import Path

import sympy as sp
import pytest

from app.schemas.problem_template import ProblemTemplate
from scripts.problems.problem_instance_generator import generate_problem_instance


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_PATH = (
    PROJECT_ROOT
    / "data"
    / "problem_templates"
    / "linear_algebra"
    / "la_01_matrix_algebra"
    / "la.matrix.multiplication__matrix_multiplication.json"
)


def test_matrix_multiplication_pipeline_across_seeds() -> None:
    assert TEMPLATE_PATH.is_file(), f"Template 파일을 찾을 수 없습니다: {TEMPLATE_PATH}"
    template = ProblemTemplate.model_validate_json(
        TEMPLATE_PATH.read_text(encoding="utf-8")
    )

    assert template.taxonomy.subject_id == "linear_algebra"
    assert template.classification.problem_type == "matrix_multiplication"
    a_shape = template.parameters["A"].shape
    b_shape = template.parameters["B"].shape
    assert a_shape is not None and a_shape.rows is not None and a_shape.cols is not None
    assert b_shape is not None and b_shape.rows == "A.cols"
    assert "A" in template.parameters["B"].depends_on

    seeds = range(17, 37)  # 20개 시작 seed
    failures: list[str] = []
    attempts_total = 0

    for seed in seeds:
        try:
            result = generate_problem_instance(template, seed=seed)
            instance = result.instance
            attempts_total += len(result.attempts)

            a = sp.Matrix(instance["parameters"]["A"])
            b = sp.Matrix(instance["parameters"]["B"])
            answer = sp.Matrix(instance["expected_answer"])

            assert a.cols == b.rows, f"A.cols={a.cols}, B.rows={b.rows}"
            assert answer == a * b, f"계산 정답 불일치: A={a}, B={b}, answer={answer}"
            assert instance["statement"].strip(), "문제 문장이 비어 있습니다."
            assert result.attempts[-1].passed, "마지막 생성 시도가 통과로 기록되지 않았습니다."
            assert result.attempts[-1].stage == "validated", result.attempts[-1].stage
            assert instance["publishable"] is False, "검수 전 Instance가 출제 가능 상태입니다."

            trace = instance.get("validation_trace")
            assert trace is not None, "validation_trace가 결과에 없습니다."
            failed_validators = [item for item in trace["validators"] if not item["passed"]]
            assert not failed_validators, f"실패 Validator: {failed_validators}"

        except Exception as exc:  # 각 seed의 실패를 모두 모아 출력한다.
            failures.append(f"seed={seed}: {type(exc).__name__}: {exc}")

    total = len(range(17, 37))
    succeeded = total - len(failures)
    failure_rate = len(failures) / total
    print(
        f"\n행렬 곱셈 다중 seed 결과: 성공 {succeeded}/{total}, "
        f"실패 {len(failures)}/{total} ({failure_rate:.1%}), "
        f"총 시도 {attempts_total}"
    )
    if failures:
        pytest.fail("\n".join(failures))
