# 미적분 1: 남은 144개 유형 적용 결과

업로드한 최신 프로젝트를 기준으로 144개 실행 계약을 추가했습니다. 기존 57개 Rule 내용은 동일합니다. 총 201개 Rule / 202개 Template이 실행 가능합니다.

## 검증 결과

- 실제 Template 연결: 전체 Rule의 seed 17~21 실행 통과(Template 중복 연결 포함 총 1,010건).
- Preview 저장: 실제 저장/중복 제거 함수로 202개 Template × 10개 = 2,020개 파일 확인. 검사 환경에서 생성의 시간 제한은 Linux signal로 적용했습니다.
- 실제 CLI의 별도 프로세스/시간 제한 경로: 202개 Template × 1개 = 202개 성공, 실패·제외·시간 초과·파일 오류 0.
- 관련 테스트 1,232개 통과(오답 거부, 수작업 기준값, 조건 경계, 반복 적용, 기존 기능 포함).
- 선형대수 Rule JSON 동일. 62개 Template 및 seed 17 생성 결과가 업로드한 기존 코드와 동일.
- 정적 검사: 누락 0, 오류 0, 경고 1. domain_range_identification은 두 Concept에 연결되어 하나의 primary_formula_id를 고정하지 않았습니다. 대표 공식/해설 연결은 수동 확인이 필요합니다.

## 구현 범위와 남은 검수

질문에 명시한 함수족만 지원합니다. 각 학습 유형의 모든 가능한 함수/문제를 처리하는 일반 풀이 엔진은 아닙니다. 그래프는 식·구간 등 객관적으로 비교할 답을, 증명/방법 문제는 명시된 판정·설정 답을 검사합니다. 자유로운 그림과 서술 증명/풀이 방법의 정당성은 검증하지 않습니다. 예를 들어 curve_sketching은 오목 구간, integral_inequality_proof는 주어진 전제와 결론의 판정을 생성합니다.

curated는 실행 계약 정리를 나타냅니다. 사람 검수 완료를 뜻하지 않습니다. Template은 draft/not_reviewed, Instance는 publishable=False를 유지합니다.

| 새 유형 | 답 유형 | 생성 질문 | 지원 범위 |
|---|---|---|---|
| absolute_conditional_classification | classification | 급수 ∑(-1)^(n-1)/n^{{ a }} (n≥1)를 절대수렴/조건수렴/발산으로 분류하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| accumulation_function_derivative | expression | F(x)=∫₀ˣ ({{ a }}t²+{{ b }})dt의 도함수를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| alternating_series_error_estimation | numerical_approximation | 교대급수 ∑(-1)^(n-1)/n을 n={{ N }}까지 합했다. 교대급수 오차정리의 상한을 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| alternating_series_test_application | boolean | 급수 ∑(-1)^(n-1)/n^{{ a }} (n≥1)는 교대급수 정리의 감소·0극한 조건을 만족하는가? | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| arc_length_calculation | scalar | 곡선 y={{ a }}x, 0≤x≤{{ b }}의 호의 길이를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| arc_length_setup | expression | 곡선 y={{ a }}x, 0≤x≤{{ b }}의 호의 길이를 구할 때 적분할 피적분함수를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| area_between_polar_curves | scalar | {{ a }}≤r≤({{ a }}+{{ b }}), 0≤θ≤π/2인 극좌표 영역의 넓이를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| area_limit_estimation | scalar | [0,1]에서 f(x)={{ a }}x²의 오른쪽 끝점 리만합의 분할 수를 무한히 늘릴 때 넓이의 극한값을 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| axis_distance_calculation | expression | 점 (x,y)에서 직선 x={{ c }}까지의 거리를 x의 식으로 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| cancellation_verification | boolean | f(x)={{ a }}x+{{ b }}, g(x)=(x-{{ c }})/{{ a }}이다. f(g(x))=x가 모든 실수 x에서 성립하는가? | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| cardiac_output_calculation | numerical_approximation | 주입량 A={{ a }}이고 시간 0,1,2의 농도는 {{ b }},{{ a }},{{ b }}이다. 사다리꼴 적분으로 A/∫농도 dt를 근사하시오. 단위는 일관된 단위계다. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| change_of_base | scalar | log_({{ a }}+1)((({{ a }}+1))^{{ b }}) 값을 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| closed_interval_extrema_calculation | scalar | f(x)={{ a }}x²+{{ b }}x+{{ c }}의 [0,1]에서 최댓값을 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| comparison_series_construction | boolean | 1/(n²+{{ a }})≤1/n² (n≥1)이고 우변의 급수가 수렴한다. 이 비교 대상은 좌변 급수의 수렴 증명에 유효한가? | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| comparison_theorem_application | boolean | x≥1에서 f(x)=1/x^{{ a }}이다. ∫₁^∞ f가 수렴하는지 참/거짓으로 답하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| composition_continuity_check | boolean | h(x)=sqrt({{ a }}x+{{ c }})가 x=0의 열린 근방에서 실수 함수로 연속인가? | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| concavity_interval_identification | interval | f(x)={{ a }}(x-{{ c }})³가 f''(x)>0인 최대 열린 구간을 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| conic_element_calculation | expression | 타원 x²/({{ a }}²+{{ b }}²)+y²/{{ b }}²=1의 초점과 중심 사이 거리 c를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| conic_type_classification | classification | x²/{{ a }}²+{{ k }}y²/{{ b }}²=1의 이차곡선을 타원/쌍곡선 중에서 답하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| continuity_algebra_application | boolean | f(x)=1/(x-{{ c }})+{{ a }}x는 x=0에서 연속인가? | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| critical_number_calculation | set | f(x)={{ a }}(x-{{ c }})²+{{ b }}의 임계수 집합을 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| cross_section_area_construction | expression | x축에 수직인 단면이 한 변 {{ a }}x+{{ b }}인 정사각형이다. 단면 넓이 A(x)를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| curve_sketching | interval | f(x)={{ a }}(x-{{ c }})³+{{ b }}의 그래프를 분석하시오. 스케치의 핵심인 아래로 오목한 구간(f''<0)만 답하시오. | 곡선 분석의 오목 구간 답만 검사; 완전한 그림/모든 특징은 사람 검수 |
| cylindrical_shell_volume_calculation | scalar | 0≤x≤1에서 y={{ a }}x 아래 영역을 y축 둘레로 회전한다. 원통껍질법으로 부피를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| derivative_from_definition | expression | f(x)={{ a }}x²+{{ b }}x이다. 차분몫의 극한 정의로 f'(x)를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| differentiability_continuity_reasoning | boolean | f(x)=\|x-{{ c }}\|는 x={{ c }}에서 연속이지만 미분 불가능하다는 명제는 참인가? | 절댓값 반례의 명제 판정; 서술 논증은 검사하지 않음 |
| direct_comparison_test_application | boolean | ∑1/(n^{{ a }}+n), n≥1을 ∑1/n^{{ a }}와 직접 비교할 때, 수렴을 결론낼 수 있는가? | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| discontinuity_classification | classification | x≠{{ c }}에서 f(x)=((x-{{ c }})²)/(x-{{ c }}), f({{ c }})={{ a }}이다. x={{ c }}의 불연속을 제거 가능 또는 점프 또는 무한으로 분류하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| displacement_and_distance_calculation | scalar | 0≤t≤2에서 속도 v(t)={{ a }}(t-1)이다. 변위가 아니라 총 이동 거리를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| divergence_test_application | boolean | 급수 ∑( {{ a }}+1/n )에 일반항의 극한을 이용한 발산판정법으로 발산을 결론낼 수 있는가? | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| domain_by_family | interval | 유리함수 f(x)={{ a }}/(x-{{ c }})의 실수 정의역을 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| domain_of_combination | interval | f(x)=sqrt(x-{{ c }}), g(x)=x-{{ c }}-{{ a }}이다. f/g의 실수 정의역을 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| domain_range_identification | interval | f(x)=arctan({{ a }}x)의 실수 정의역을 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| domain_segment_identification | scalar | f(x)={{ a }}x (x<{{ c }}), f(x)={{ b }}x (x≥{{ c }})이다. x={{ c }}+{{ k }}에는 몇 번째 식을 쓰는가? 1 또는 2로 답하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| economic_optimization | scalar | 0≤q≤{{ a }}에서 이익 P(q)={{ a }}q-q²이다. 이익을 최대화하는 생산량 q를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| error_propagation_estimation | expression | f(x)=x², 측정값 x={{ a }}, dx=1/{{ N }}이다. 미분을 이용한 df의 추정값을 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| evt_condition_check | boolean | f(x)=1/(x-{{ c }})에 대해 [-1,1]에서 최대·최소 정리를 적용할 연속성 가정을 만족하는가? | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| exponent_law_application | expression | {{ a }}^(x+{{ b }}) / {{ a }}^x 를 간단히 하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| extrema_classification | classification | f(x)=({{ k }})*{{ a }}(x-{{ c }})²+{{ b }}의 x={{ c }}는 극대 또는 극소 중 무엇인가? | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| first_derivative_test_classification | classification | f(x)=({{ k }})*{{ a }}(x-{{ c }})²의 x={{ c }}에서 일계도함수 판정 결과를 극대/극소로 답하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| function_decomposition | expression | h(x)=({{ a }}x+{{ b }})²를 f(u)=u²와 g(x)로 분해하시오. g(x)만 답하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| function_family_classification | classification | f(x)={{ a }}x^{{ b }}+{{ c }}를 다항함수 또는 유리함수(다항함수 제외)로 분류하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| general_to_standard_form_conversion | equation | x²-2*{{ c }}x+y²-2*{{ b }}y+{{ c }}²+{{ b }}²={{ a }}²의 표준형을 좌변=우변 방정식으로 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| geometric_sequence_limit_classification | classification | 수열 a_n=(({{ k }})*{{ a }})^n의 극한 거동을 1/진동/발산(+∞)/발산(진동) 중에서 답하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| graph_identification | expression | f(x)=({{ a }}+1)^x의 그래프가 지나는 x=0에서의 y 좌표를 구하시오. | 지수 그래프의 절편 식별; 이미지 선택은 미지원 |
| graph_sketch_rule | expression | y={{ k }}x²의 그래프를 오른쪽 {{ c }}만큼 이동할 때, 스케치의 기준이 되는 y의 식을 구하시오. | 스케치를 나타내는 함수식만 검사; 실제 그림은 사람 검수 |
| growth_rate_comparison | scalar | x→+∞에서 x^{{ a }}/exp({{ b }}x)의 극한을 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| heaviside_modeling | expression | x<{{ c }}일 때 0, x≥{{ c }}일 때 {{ a }}인 계단함수를 Piecewise 식으로 나타내시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| horizontal_asymptote_identification | scalar | f(x)=({{ a }}x+{{ c }})/({{ b }}x+1)의 수평점근선 y=L에서 L을 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| horizontal_tangent_point_calculation | set | y={{ a }}(x-{{ c }})²+{{ b }}의 수평접선이 생기는 x 좌표들의 집합을 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| horizontal_vertical_tangent_identification | set | X(t)=t², Y(t)={{ a }}t인 곡선의 수직접선이 생기는 t 값들의 집합을 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| hydrostatic_force_calculation | scalar | 수면에서 깊이 0≤h≤{{ b }}에 너비 {{ a }}인 직사각형 판이 있다. 유체의 비중량을 1로 놓고 정수압 힘을 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| hyperbolic_identity_application | expression | cosh²({{ a }}x)-sinh²({{ a }}x)를 간단히 하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| implicit_differentiation | expression | 곡선 x²+{{ a }}y²={{ b }}에서 y≠0이다. dy/dx를 x,y로 나타내시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| implicit_second_derivative | expression | 곡선 x²+{{ a }}y²={{ b }}에서 y≠0이다. d²y/dx²를 x,y로 나타내시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| improper_integral_evaluation | scalar | p={{ a }}+1일 때 ∫₁^∞ x^(-p)dx를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| improper_integral_type_classification | classification | ∫₁^∞ x^(-{{ a }})dx의 이상적분 유형을 제1종 또는 제2종으로 분류하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| increasing_decreasing_interval_identification | interval | f(x)={{ a }}(x-{{ c }})²+{{ b }}가 감소하는 최대 열린 구간을 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| indeterminate_form_classification | classification | x→0에서 (exp({{ a }}x)-1)/sin({{ b }}x)의 부정형을 0 나누기 0 또는 무한대 나누기 무한대로 분류하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| infinite_limit_identification | boolean | f(x)=({{ k }})*{{ a }}/x²의 x→0 극한이 +∞인가? 참/거짓으로 답하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| inflection_point_calculation | set | f(x)={{ a }}(x-{{ c }})³+{{ b }}의 변곡점 x 좌표들의 집합을 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| inner_outer_identification | expression | h(x)=sin(({{ a }}x+{{ b }})²)에서 최외곽 함수를 sin(u)로 선택한다. 안쪽 함수 u(x)를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| integrability_check | boolean | f(x)=1/(x-{{ c }})는 [-1,1]에서 유계인 보통의 리만 적분 가능한 함수인가? | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| integral_inequality_proof | boolean | 0≤x≤1에서 f(x)={{ a }}x, g(x)={{ b }}이다. f≤g의 점별 조건과 ∫f≤∫g가 모두 성립하는지 참/거짓으로 판정하시오. 서술 증명은 별도 제출이다. | 적분 비교의 전제 및 결론 판정만 자동 검사; 서술 증명의 정당성은 사람 검수 |
| integral_property_application | scalar | ∫₀¹ f={{ a }}, ∫₀¹ g={{ b }}이다. ∫₀¹ (2f-3g)를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| integral_test_application | classification | 급수 ∑1/n^{{ a }} (n≥1)에 적분판정법을 적용한 수렴/발산 결과를 답하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| intersection_point_calculation | scalar | y={{ a }}x와 y={{ b }}의 교점 x 좌표를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| inverse_function_derivation | expression | 실수 전체에서 f(x)={{ a }}x+{{ b }}이다. 역함수 f^(-1)(x)를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| inverse_function_derivative_rule_application | expression | f(x)={{ a }}x+{{ b }}의 역함수의 도함수를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| inverse_hyperbolic_derivative_calculation | expression | f(x)=asinh({{ a }}x)의 도함수를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| inverse_trig_derivative_calculation | expression | f(x)=arctan({{ a }}x)의 도함수를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| inverse_trig_evaluation | scalar | 주값 arctan({{ k }})를 사용하여 {{ a }}*arctan({{ k }})를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| ivt_condition_check | boolean | f(x)=x²-{{ a }}가 [0,{{ b }}]에서 연속이다. 끝점의 함수값만으로 중간값정리가 이 구간의 영점 존재를 보장하는가(끝점 영점 포함)? | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| limit_at_infinity_calculation | scalar | x→+∞에서 ({{ a }}x²+{{ c }})/({{ b }}x²+1)의 극한을 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| limit_comparison_test_application | classification | 급수 ∑({{ a }}n+1)/n³를 ∑1/n²와 극한 비교하여 수렴/발산을 답하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| limit_law_precondition_check | boolean | x→0에서 f(x)={{ a }}x+1, g(x)=x+{{ c }}이다. 분모 극한이 0이 아닌 경우에 쓰는 몫의 극한 법칙을 바로 적용할 수 있는가? | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| limit_numeric_estimation | scalar | f(x)={{ a }}x+{{ b }}이다. x=1-1/{{ N }}와 x=1+1/{{ N }}의 함수값 평균을 극한 추정값으로 사용하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| log_law_application | expression | x>0일 때 log(x^{{ a }})+log(x^{{ b }})를 자연로그 하나로 합치시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| midpoint_rule_estimation | scalar | [0,1]에서 f(x)={{ a }}x²를 {{ N }}등분한 중점 공식 근사값을 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| monotonic_interval_identification | interval | f(x)={{ a }}(x-{{ c }})²가 증가하는 최대 열린 구간을 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| monotonic_theorem_application | boolean | a_n={{ a }}-{{ b }}/n (n≥1)에 단조·유계 수열 정리의 가정을 모두 적용할 수 있는가? | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| monotonicity_boundedness_classification | classification | a_n={{ a }}-{{ b }}/n (n≥1)의 단조성과 유계성을 증가·유계 또는 감소·유계 중에서 답하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| monotonicity_from_base | boolean | 함수 f(x)=({{ a }}+1)^({{ k }}x)는 실수 전체에서 증가하는가? 참/거짓으로 답하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| motion_reconstruction | expression | 가속도 s''(x)={{ a }}, s'(0)={{ b }}, s(0)={{ c }}이다. 위치 함수 s(x)를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| mvt_bound_estimation | scalar | [0,1]에서 \|f'(x)\|≤{{ a }}이다. 평균값정리로 얻는 \|f(1)-f(0)\|의 상한을 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| mvt_point_calculation | scalar | f(x)={{ a }}x²+{{ b }}의 [0,2]에서 평균값정리를 만족하는 c∈(0,2)를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| natural_vs_common_log | expression | log는 자연로그를 뜻한다. log(exp({{ a }})) / log(10^{{ b }})를 정확한 식으로 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| numeric_integration_from_data | numerical_approximation | 시간 0,1,2의 농도 측정값이 각각 {{ a }},{{ b }},{{ a }}이다. 간격 1의 사다리꼴 공식으로 농도 적분을 근사하시오. | 표본 사다리꼴 공식의 정확한 유리수 표현; 측정 오차는 별도 |
| one_to_one_check | boolean | 실수 전체에서 f(x)={{ a }}x^{{ b }}는 일대일 함수인가? | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| optimization_formulation | expression | 둘레가 2*{{ a }}인 직사각형의 한 변을 x라 할 때, 넓이를 x의 함수로 세우시오(0<x<{{ a }}). | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| optimization_solving | scalar | 두 변의 합이 {{ a }}인 직사각형의 넓이를 최대화하는 한 변의 길이를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| p_series_classification | classification | p={{ a }}일 때 p급수 ∑1/n^p (n≥1)의 수렴/발산을 답하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| pappus_applicability_check | boolean | 반지름 {{ a }}인 원판의 중심과 회전축 사이 거리가 {{ b }}이다. 축이 원판과 만나지 않아 파푸스 부피 정리를 직접 적용할 수 있는가? | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| pappus_theorem_application | scalar | 반지름 {{ a }}인 원판을 원판 중심에서 ({{ a }}+{{ b }})만큼 떨어진 같은 평면의 축 둘레로 회전한다. 부피를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| parameter_elimination | equation | X(t)={{ a }}t, Y(t)={{ b }}t+{{ c }}에서 t를 제거한 y,x 방정식을 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| parametric_arc_length_calculation | scalar | X(t)={{ a }}t, Y(t)={{ b }}t, 0≤t≤1의 곡선 길이를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| parametric_area_calculation | scalar | X(t)={{ a }}t, Y(t)={{ b }}t², 0≤t≤1에서 곡선과 X축 사이 넓이를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| parametric_curve_sketching | equation | 곡선 X(t)=t, Y(t)={{ a }}t²+{{ b }}의 t를 제거하여 평면 그래프 방정식을 y,x로 나타내시오. | 매개변수 스케치의 직교좌표 방정식; 진행 방향/그림은 별도 검수 |
| parametric_second_derivative_calculation | scalar | X(t)={{ a }}t, Y(t)={{ b }}t²의 d²Y/dX²를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| parametric_surface_area_calculation | scalar | X(t)={{ a }}t, Y(t)={{ b }}t, 0≤t≤1을 X축 둘레로 회전한 곡면 넓이를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| parametric_tangent_slope_calculation | scalar | X(t)={{ a }}t, Y(t)={{ b }}t²이다. t={{ k }}에서 dY/dX를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| partial_fraction_decomposition | expression | 1/(x(x+{{ a }}))의 부분분수 분해를 구하시오. x=0,-{{ a }}는 제외한다. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| piecewise_evaluation | scalar | f(x)={{ a }}x (x<0), f(x)={{ b }}x+{{ c }} (x≥0)이다. f({{ k }})를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| polar_arc_length_calculation | scalar | r={{ a }}, 0≤θ≤π/2인 극좌표 곡선의 길이를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| polar_area_calculation | scalar | r={{ a }}, 0≤θ≤π/2인 부채꼴의 넓이를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| polar_cartesian_conversion | expression | 극좌표 (r,θ)=({{ a }},{{ c }}π/2)의 직교좌표 중 x 좌표를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| polar_curve_identification | classification | 극좌표 r={{ a }}의 곡선 종류를 원/직선/포물선 중에서 답하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| polar_curve_intersection | scalar | r={{ a }}와 r=2*{{ a }}cos(θ)가 만나는 θ∈[0,π/2]를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| polar_symmetry_classification | boolean | 극좌표 곡선 r={{ a }}(1+{{ k }}cos(θ))는 극축(직교 x축)에 대칭인가? | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| polar_tangent_slope_calculation | scalar | r={{ a }}인 극좌표 원의 θ=π/4에서 접선 기울기 dy/dx를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| pole_tangent_calculation | scalar | r={{ a }}sin(θ)인 극좌표 곡선의 θ=0에서 극점을 지나는 접선 기울기를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| ratio_test_application | classification | 급수 ∑({{ a }}/{{ b }})^n (n≥1)를 비율판정법으로 분류하시오: 수렴/발산/판정 불가. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| rational_end_behavior_classification | classification | f(x)=x^{{ a }}/(x^{{ b }}+1)의 x→+∞ 거동을 0 또는 1 또는 +∞로 분류하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| reciprocal_trig_evaluation | scalar | csc(π/2+{{ c }}π)의 값을 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| recursive_sequence_limit_calculation | scalar | u₁=0, u_(n+1)=(u_n+{{ a }})/2인 수열의 극한을 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| related_rates_equation_formulation | expression | 구의 현재 반지름은 {{ a }}이고 V(t)=4πr(t)³/3이다. 현재 dr/dt를 y로 놓고 dV/dt를 y의 식으로 나타내시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| related_rates_solving | scalar | 구의 반지름이 {{ a }}이고 dr/dt=({{ k }})*{{ b }}일 때 dV/dt를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| remainder_estimation | numerical_approximation | 급수 ∑1/n²를 n={{ N }}까지 합했다. 적분판정법으로 R_N≤∫_N^∞1/x² dx의 상한을 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| riemann_sum_calculation | scalar | [0,1]에서 f(x)={{ a }}x²를 {{ N }}등분한 오른쪽 끝점 리만합을 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| rolle_condition_check | boolean | f(x)={{ a }}(x-{{ c }})²의 [0,2]에서 롤의 정리의 세 가정을 모두 만족하는가? | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| root_interval_location | interval | f(x)=x³-{{ a }} (a={{ a }})의 영점이 존재하는 연속함수 구간 [0,3]를 답하시오. 끝점의 부호로 보장됨을 확인하시오. | 주어진 부호 변화 구간을 확인하는 답; 최소 구간/유일근 증명은 묻지 않음 |
| root_test_application | classification | 급수 ∑({{ a }}/{{ b }})^n (n≥1)를 근판정법으로 분류하시오: 수렴/발산/판정 불가. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| second_derivative_test_classification | classification | f(x)=({{ k }})*{{ a }}(x-{{ c }})²+{{ b }}의 x={{ c }}에서 이계도함수 판정 결과를 극대/극소로 답하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| sequence_convergence_check | boolean | 수열 a_n=({{ a }}/(({{ a }}+1)))^n이 수렴하는가? | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| sequence_limit_calculation | scalar | 수열 a_n=({{ a }}n+{{ c }})/({{ b }}n+1)의 n→∞ 극한을 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| shell_vs_disk_method_selection | expression | 0≤x≤1, 0≤y≤{{ a }}x인 영역을 y축 둘레로 회전한다. x에 대한 원통껍질법을 선택할 때 부피 적분의 피적분함수를 구하시오. | 명시된 방법의 적분 설정; 자유로운 방법 선택/풀이 설명은 사람 검수 |
| squeeze_theorem_application | scalar | x≠0에서 f(x)={{ a }}x² sin(1/x)이다. 조임정리로 x→0의 극한을 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| surface_area_calculation | scalar | y={{ a }}x, 0≤x≤{{ b }}를 x축 둘레로 회전한 곡면의 넓이를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| surface_area_setup | expression | y={{ a }}x, 0≤x≤1을 x축 둘레로 회전한 곡면의 넓이 적분에서 피적분함수를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| tangent_line_implicit | equation | 곡선 x²+y²={{ a }}²+{{ b }}²의 점 ({{ a }},{{ b }})에서 접선 방정식을 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| tangent_normal_line_derivation | equation | y={{ a }}x²+{{ b }}의 x=1에서 법선 방정식을 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| tangent_slope_interpretation | scalar | y=exp({{ a }}x)의 x=0에서 접선의 기울기를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| telescoping_series_calculation | scalar | n=1부터 무한대까지 ∑{{ a }}/(n(n+1))의 합을 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| test_selection_reasoning | classification | 급수 ∑{{ a }}^n/n!에서 항의 비 a_(n+1)/a_n={{ a }}/(n+1)을 이용한다. 사용하는 판정법 이름을 비율판정법 또는 근판정법으로 답하시오. | 주어진 항의 비에 맞는 판정법 식별; 선택 이유의 서술은 사람 검수 |
| transformation_identification | expression | 기본 그래프 y=x²를 오른쪽 {{ c }}만큼, 위쪽 {{ b }}만큼 옮겼다(음수 이동량은 반대 방향). 변환 후 y의 식을 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| trig_domain_range_period_identification | scalar | 함수 sin({{ a }}x)의 최소 양의 주기를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| trig_integral_strategy_selection | expression | ∫sin(x)cos(x)^{{ a }} dx에 u=cos(x)를 선택했다. x 대신 u를 기호 x로 적을 때 변환된 피적분함수를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| trig_substitution_integral_calculation | expression | \|x\|<{{ a }}에서 ∫1/sqrt({{ a }}²-x²) dx의 원시함수 하나를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| trig_substitution_selection | expression | sqrt({{ a }}²-x²)의 적분을 위해 x={{ a }}sin(u)를 선택했다. dx/du를 u 대신 기호 x로 답하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| variable_bound_integral_derivative | expression | F(x)=∫₀ˣ² ({{ a }}t+{{ b }})dt의 도함수를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| variable_choice_for_area | expression | 영역 0≤y≤{{ a }}, 0≤x≤y²를 y에 대해 적분할 때 넓이 적분의 피적분함수를 x를 적분변수 y의 자리표시자로 사용하여 답하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| vertical_asymptote_calculation | scalar | f(x)={{ a }}/(x-{{ c }})의 수직점근선 x=d에서 d를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| vertical_line_test_check | boolean | 관계 x=y^{{ a }} (a={{ a }})는 모든 실수 x에서 y=f(x)인 함수의 그래프인가? 참/거짓으로 답하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
| width_function_construction | expression | 꼭짓점 (0,0), 높이 {{ a }}, 윗변 너비 {{ b }}인 역삼각형 판의 높이 x(0≤x≤{{ a }})에서 너비 w(x)를 구하시오. | 질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수 |
