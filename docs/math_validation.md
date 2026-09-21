# 정답·수학 검증 구현 — 긴급한 문제 4번 / 9번

## 적용 범위

업로드한 `math-emergency-JM.zip`이 기준입니다. Notion의 진행 보고와 실제 코드가 다릅니다. 업로드본에는 네 실행 엔진이나 새 Schema 변경이 없으므로 다른 담당자의 미구현 모듈을 대신 만들지 않았습니다.

- `app/problems/math_validators.py`: 공통 비교, 수치 허용오차, 정의역 및 선형대수 검증.
- `app/problems/validator_policy.py`: 답 유형별 허용 검증기와 curated 56개별 승인 매핑.
- `app/schemas/generation_rule.py`: curated/reviewed 규칙 로드 시 매핑 검사.
- `app/problems/template_builder.py`: Concept 추천 검증기의 무조건 병합 제거. Rule의 검증기가 기준입니다. draft는 해당 답 유형에 허용되는 구현된 검증기만 전달하며, 이 처리는 수학적 승인이나 상태 승격이 아닙니다.
- `data/generation_rules/linear_algebra.json`: curated 56개 매핑 검수·수정. draft 500개 Rule 원본은 변경하지 않았습니다.
- `data/problem_templates/linear_algebra/` 및 manifest: Builder로 62개 재생성. 다른 과목의 기존 생성 파일은 수정하지 않았습니다.
- `environment.yml`: SymPy 의존성 추가.
- `tests/test_math_validators.py`: DB나 API 없이 실행하는 91개 회귀 테스트.
- `docs/validator_mapping_audit.md`: 전체 56개 매핑 변경표.

## 적용 및 실행

변경 파일 ZIP의 내용을 프로젝트 루트에 같은 경로로 반영하십시오. 전체 ZIP은 반영이 끝난 프로젝트입니다. 별도 커밋·푸시·PR은 생성하지 않았습니다.

```bash
python -m pip install "sympy>=1.13,<2" numpy pydantic pytest
python -m pytest tests/test_math_validators.py -q
python -m scripts.problems.validate_generation_rules
python -m scripts.problems.build_problem_templates --subject linear_algebra --overwrite
```

검증 환경: Python 3.12 / SymPy 1.14.0 / NumPy 2.3.5 / Pydantic 2.13.5. 프로젝트의 Python 3.13 환경 자체에서는 실행하지 않았습니다.

## 생성 파이프라인 연결

```python
from sympy import Matrix
from app.problems.generation_rule_registry import get_rule
from app.problems.math_validators import validate_rule_answer

rule = get_rule("linear_algebra", "orthogonal_projection_calculation")
report = validate_rule_answer(
    rule,
    answer=Matrix([3, 0]),
    parameters={"a": Matrix([3, 4]), "b": Matrix([2, 0])},
)
if not report.passed:
    # 생성 실패 기록 / 재생성 처리는 호출자의 책임입니다.
    for result in report.results:
        print(result.name, result.message)
```

`validate_rule_answer(rule, answer, parameters, config=None)`는 독립적으로 코딩한 기준값 또는 문제의 수학적 관계로 검증합니다. Rule의 정답 문자열을 다시 eval해서 자기 자신과 비교하지 않습니다. 반환된 `ValidationReport.passed`를 확인하십시오. 빈 검사 목록, 미구현 검증기, 답 유형 불일치, 누락 파라미터, 예외는 실패로 반환됩니다. 개별 검증 결과는 `name`, `passed`, `message`를 갖습니다. 모든 검사는 필수이며 부분 통과로 정답을 인정하지 않습니다.

Rule에는 구체적으로 샘플링된 숫자·행렬·벡터를 전달합니다. 자유 기호가 포함된 파라미터는 미지의 피벗을 0이 아니라고 가정하는 오판정을 막기 위해 거부합니다. `matrix_to_vector_equation`의 `x`만 명시적 미지수 벡터로 전달합니다. 미선언 x를 생성하는 작업은 8번 담당 범위입니다.

## 공통 검증 API

```python
import sympy as sp
from app.problems.math_validators import validate_answer

report = validate_answer(
    0.3333333333, sp.Rational(1, 3),
    answer_type="scalar", validators=["numeric_equality"],
    config={"numeric_equality": {"atol": 1e-9, "rtol": 1e-9}},
)
```

- 기본값은 정확 비교입니다. 근사 비교는 `numeric_equality` 또는 해당 검사 설정의 `numeric=True`로 명시적으로 요청합니다. 비교식은 `abs(actual-expected) <= atol + rtol*abs(expected)`입니다. NaN, 무한대, 음수/비유한 허용오차를 거부합니다.
- 문자열 수식 파싱은 이 모듈에서 하지 않습니다. 숫자, SymPy 객체, 숫자 리스트, NumPy 배열을 전달합니다. 문자열은 선택지에만 사용합니다. 기존 CAS 문자열의 계산은 생성 엔진의 책임이며 사용자 입력을 eval/sympify 문자열로 실행하면 안 됩니다.
- Boolean은 실제 bool/SymPy Boolean만 허용하며 0/1 및 'True' 문자열은 거부합니다.
- 행렬은 모양과 모든 원소를 비교합니다. 벡터 비교는 행/열 표현을 같은 열벡터로 정규화합니다.
- `set_equivalence`는 SymPy Set/Interval을 받으며 열린/닫힌 끝점을 구분합니다.
- `equation_equivalence`는 보수적으로 같은 잔차 또는 양변을 바꾼 식만 인정합니다. 임의 비선형 방정식의 해집합 동치 판정기는 아닙니다.
- 검증 결과가 불확실하거나 지원되지 않는 경우 정답으로 승인하지 않습니다.

## 정의역 검사

```python
x = sp.Symbol("x", real=True)
report = validate_answer(
    1/x, answer_type="expression", validators=["domain_check"],
    config={"domain_check": {"symbol": x, "domain": sp.Interval.open(0, sp.oo)}},
)
```

스칼라는 주어진 집합의 원소인지 검사합니다. 단일 변수 실수식은 `continuous_domain`이 반환하는 연속 정의역에 요청 구간이 포함되는지 검사합니다. 이는 보수적인 검사이며 일반 불연속 함수 전체의 정의역 판정은 지원하지 않습니다. 정의역을 지정하지 않았을 때 동치성 검사만으로 정의역까지 보장하지 않습니다. 약분으로 소실된 제외점은 복원할 수 없으므로 원식을 보존하고 필요한 `domain_check`를 별도로 실행하십시오. 다변수·복소식 정의역은 지원하지 않습니다.

## 수학적 검수 기준

| 대상 | 판정 기준 |
| --- | --- |
| 특이행렬 판정 | 정사각행렬의 det(A)=0. 영행 유무로 대체하지 않음 |
| 대칭성·기저·독립성 등 | 파라미터에서 판정값을 독립 계산하고 Boolean으로 비교 |
| 사영 벡터 | 방향 벡터가 0이 아니며, 답이 그 span에 있고 잔차가 직교 |
| 기저 | 정답 벡터들이 독립이고 목표 공간과 span 및 차원이 일치 |
| 고유공간 | 실제 고윳값인지 확인 후 해당 영공간의 완전한 기저인지 검사 |
| 고윳값 | 현 Rule의 `list(A.eigenvals().keys())` 계약에 따라 서로 다른 고윳값 전체. 중복/누락 거부 |
| 커널·이미지 | `(kernel_basis, image_basis)` 두 기저를 각각 검사 |
| Gram–Schmidt | 단위 길이·상호 직교·각 접두 벡터 집합의 span 보존. 부호 차이 허용 |
| LU | 제출 형식 `[L|U]`, L 단위 하삼각, U 상삼각, LU=A. 행 교환을 누락한 답 거부 |
| 대각화 | P 가역, D 대각, AP=PD. 고유벡터 순서와 배율 차이 허용 |
| 직교대각화 | 실수 대칭 A, 실수 Q, Q^TQ=I, AQ=QD |
| QR | full-column-rank A, thin Q, 상삼각 R, Q^HQ=I, QR=A |
| 최소제곱·회귀 | 열 full rank 전제 확인 후 정상방정식 잔차 0 |
| 매개변수해 | Ax=b, affine 표현 및 영공간 전체를 생성하는 방향. 제한된 정수/양수 파라미터 거부 |
| 주축 이차형식 | 순수 제곱항만 허용하고 계수의 중복도를 포함한 집합이 고윳값과 일치 |
| 스펙트럼 분해 | `(lambda, P)` 목록. 실수 대칭 멱등 P, 상호 직교, AP=lambda P, 합 P=I, 합 lambda P=A |

행렬의 rank, 기저 및 상삼각 여부는 정확 산술 기준입니다. 근사 기저와 수치적으로 불안정한 행렬의 rank 판정은 이 구현의 지원 범위가 아닙니다. 수치 허용오차가 모든 구조 판정을 근사 판정으로 바꾸지는 않습니다.

## 남은 통합 작업 및 범위 밖 항목

- 파라미터 생성, Constraint 실행, ProblemInstance 생성, Rule 설정 전달(14번), seed 반복 생성 및 ready 승격은 각각 담당자의 작업입니다. 이 구현은 그 기능이 완료되었다고 가정하지 않습니다.
- 업로드본 Builder의 기존 `ready` 판정은 유지했습니다. 재생성 결과의 ready 56개는 기존 메타데이터 분류이며 실제 모든 인스턴스 검증/사람 검수 완료를 뜻하지 않습니다. 6번 담당자가 실행 결과에 따른 승격을 연결해야 합니다.
- 기존에 배포/DB에 적재된 Template은 자동 갱신되지 않습니다. 수정된 원본 Rule로 재생성하고 기존 적재 절차로 반영해야 합니다.
- 미적분의 미분/적분 전용 검증기는 Notion의 최신 공통·선형대수 우선 범위에 따라 이번에 구현하지 않았습니다.
- 기존 데이터의 `vector_expression`(인덱스 목록), `vector_list`(kernel/image 쌍), `matrix_list`(스펙트럼 쌍 목록)라는 넓은 타입 이름은 호환성을 위해 유지하며, 전용 검사기가 실제 구조를 검사합니다.
- `all_required=False`에 의한 일부 검사만 통과하는 기능은 제공하지 않습니다. 핵심 정답 검증을 우회하지 않도록 모든 요청 검사가 성공해야 합니다.

SymPy API 참고: https://docs.sympy.org/latest/modules/matrices/matrices.html
