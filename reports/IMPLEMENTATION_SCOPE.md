# 미적분 2 구현 및 검수 결과

166개 Rule을 명시한 제한 함수족에서 실행하도록 연결했습니다. work_calculation이 두 Concept에 연결되어 Template은 167개입니다. 모든 가능한 수학 문제를 처리하는 범용 엔진은 아닙니다.

## 검증

- 실제 Concept→Template 연결: 167개 Template × 5개 seed = 835건 생성/정답 검사 통과.
- 관련 테스트 2,136개 통과: 기존 두 과목 회귀 검사, 전체 미적분 2 생성/오답 거부, 수작업 기준값, 벡터 성질, 초기값/미분방정식 대입, 조건 경계, 반복 적용/사용자 변경 보존 포함.
- 저장/중복 제거 함수로 167개 Template × 10개 = 1,670개 Preview 파일 확인. 테스트 환경에서는 생성 시간 제한을 Linux signal로 적용했습니다.
- 실제 CLI의 별도 프로세스 경로: 전체 167개 × 1개 성공. 마지막 수정한 극좌표 이중적분/구면좌표 삼중적분은 실제 CLI에서 각각 10개 추가 성공.
- 최종 Preview 실패/제외/시간 초과/파일 오류 0. 생성 가능한 문장이 유한하므로 임의의 count에서 무한 다양성을 보장하지 않습니다.
- 선형대수 및 미적분 1 Rule JSON은 동일. 선형대수 62개와 미적분 1 202개 Template 및 seed 17 결과가 이전 코드와 동일. 모든 seed에 대한 동일성 증명은 아닙니다.
- 정적 검사: 누락 0, 오류 0, 경고 1. work_calculation은 내적/선적분 두 Concept에 연결되어 단일 primary_formula_id를 고정하지 않았습니다. 대표 공식/해설 매핑은 사람이 확인해야 합니다.

## 구현 범위

질문에 명시한 입력/구간/방향/형식 안에서 계산합니다. 그래프는 기준 방정식으로, 서술 증명은 명제 판정으로, 급수 유도는 질문에 지정한 계수/유한 부분합/닫힌 합으로 답을 제한한 유형이 있습니다. 이러한 유형의 그림·완전한 서술 유도·선택한 풀이 방법 자체는 자동 검증하지 않습니다. 급수해 유한 부분합은 원 미분방정식의 완전한 해로 승인하지 않습니다.

수학적 의미와 학습 의도는 사람 검수가 남아 있습니다. curated는 실행 계약 작성 상태이며, Template은 draft/not_reviewed, Instance는 publishable=False입니다.

| 유형 | 답 형식 | 생성 질문 | 검증 범위 |
|---|---|---|---|
| 3d_distance_midpoint_calculation | scalar | P=(0,0,0), Q=({{ a }},{{ b }},{{ c }})의 거리를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| 3d_mass_center_calculation | scalar | 균일한 밀도의 [0,{{ a }}]×[0,{{ b }}]×[0,{{ c }}] 직육면체의 무게중심 z 좌표를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| absolute_extrema_on_closed_region | scalar | f(x,y)={{ a }}x+{{ b }}y의 닫힌 정사각형 [0,1]²에서 최댓값을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| acceleration_decomposition | scalar | r(t)=({{ a }}cos({{ b }}t),{{ a }}sin({{ b }}t),0)의 법선 가속도 크기를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| amplitude_phase_conversion | scalar | y={{ a }}cos x+{{ b }}sin x의 진폭을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| angle_between_plane_and_line | scalar | 평면 x=0과 방향벡터 ({{ a }},{{ b }},0)인 직선의 예각을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| angle_or_orthogonality_determination | boolean | u=({{ a }},{{ b }},0), v=({{ b }},-{{ a }},0)는 직교하는가? | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| area_via_cross_product | scalar | u=({{ a }},0,0), v=(0,{{ b }},0)가 만드는 삼각형 넓이를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| area_via_greens_theorem | scalar | 반지름 {{ a }}인 원판의 넓이를 Green 정리로 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| average_value_2d_calculation | scalar | [0,{{ a }}]×[0,{{ b }}]에서 f=x+y의 평균값을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| bessel_equation_identification | expression | x²y''+xy'+({{ a }}²x²-{{ c }}²)y=0을 u={{ a }}x로 바꾸면 Bessel 방정식이다. 그 차수 ν를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| bessel_series_derivation | expression | J0({{ a }}x)의 급수를 x^(2{{ N }}) 항까지 쓰시오. J0(u)=∑(-1)^j(u²/4)^j/(j!)² 이다. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| binomial_series_expansion | expression | (1+x)^{{ a }}를 이항급수로 전개하여 x^{{ N }} 이하 항만 쓰시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| cauchy_product_calculation | scalar | ∑x^n과 ∑({{ a }}x)^n (각 n≥0)의 Cauchy 곱에서 x^{{ N }} 계수를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| center_of_mass_calculation | scalar | 균일한 밀도의 [0,{{ a }}]×[0,{{ b }}] 직사각형 판의 무게중심 x 좌표를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| change_of_variables_integral_calculation | scalar | 변환 x={{ a }}u,y={{ b }}v에서 0≤u,v≤1인 영역의 면적을 Jacobian으로 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| characteristic_equation_solving | expression | y''+({{ b }}-{{ a }})y'-{{ a }}*{{ b }}y=0의 특성근을 큰 근, 작은 근 순서의 쌍으로 답하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| clairaut_theorem_verification | expression | f(x,y)={{ a }}x²y+{{ b }}xy²의 f_xy와 f_yx의 공통값을 계산하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| coefficient_determination | scalar | ∑({{ a }}x)^n (n≥0)의 x^{{ N }} 계수를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| common_series_recall | expression | exp({{ a }}x)의 Maclaurin 전개를 x^{{ N }} 항까지 쓰시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| conic_polar_equation_construction | equation | 초점이 극점, 준선이 x={{ a }}, 이심률 e=1/{{ b }}인 이차곡선의 r(θ)를 구하시오. 방정식에서는 θ=t, r=z로 쓰시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| conservativeness_test | boolean | F=({{ a }}y,{{ b }}x)는 R² 전체에서 보존장인가? | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| constant_magnitude_orthogonality_proof | boolean | r(t)=({{ a }}cos t,{{ a }}sin t,{{ b }})이다. 모든 t에서 r·r'=0이라는 명제를 판정하시오. | 상수 길이 곡선의 명제 판정; 서술 증명은 별도 검수 |
| constrained_optimization_solving | scalar | x+y={{ a }}에서 x²+y²의 최솟값을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| continuity_verification | boolean | f(x,y)={{ a }}xy/(x²+y²), f(0,0)=0이다. 원점에서 연속인가? | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| coplanarity_check | boolean | u=({{ a }},0,0), v=(0,{{ b }},0), w=(1,1,{{ d }})가 동일 평면에 놓이는가? | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| critical_point_calculation | set | f(x,y)={{ a }}(x-{{ d }})²+{{ b }}(y-{{ c }})²의 임계점들의 집합을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| cross_product_calculation | vector | u=({{ a }},{{ b }},{{ c }}), v=({{ b }},-{{ a }},{{ k }})의 u×v를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| cross_section_identification | classification | 곡면 x²+y²+z²={{ a }}²의 z=0 단면의 종류를 원/타원/쌍곡선 중에서 답하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| curl_calculation | vector | F=(-{{ a }}y,{{ b }}x,0)의 회전을 벡터로 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| curvature_calculation | scalar | 원 r(t)=({{ a }}cos t,{{ a }}sin t,0)의 곡률을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| curve_intersection_calculation | vector | r(t)=({{ a }}t,{{ b }}t²,{{ c }}t³)가 평면 x={{ a }}와 만나는 점을 벡터로 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| curve_mass_calculation | scalar | 선밀도 {{ c }}인 선분 r(t)=({{ a }}t,{{ b }}t,0),0≤t≤1의 질량을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| cylindrical_triple_integral_calculation | scalar | 반지름 {{ a }}, 높이 {{ b }}인 원기둥에서 x²+y²를 삼중적분하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| cylindrical_triple_integral_setup | expression | 원기둥 0≤r≤{{ a }},0≤θ≤2π,0≤z≤{{ b }}에서 밀도 r²를 적분한다. Jacobian 포함 피적분함수를 r=x로 쓰시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| damped_motion_solving | expression | y''+2*{{ a }}y'+({{ a }}²+{{ b }}²)y=0의 일반해를 C1,C2로 쓰시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| damping_type_classification | classification | 방정식 y''+2*{{ a }}y'+{{ b }}²y=0을 과감쇠/임계감쇠/저감쇠로 분류하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| direction_angle_calculation | scalar | v=({{ a }},{{ b }},0)와 양의 x축 사이 각을 라디안으로 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| directional_derivative_calculation | scalar | f(x,y)={{ a }}x+{{ b }}y의 방향 (1,1)/sqrt(2) 미분값을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| discriminant_classification | classification | 이차곡선 {{ a }}x²+({{ k }})*{{ b }}y²=1을 타원/쌍곡선으로 분류하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| displacement_vs_distance_calculation | scalar | r(t)=({{ a }}t,{{ b }}t,{{ c }}t), 0≤t≤{{ N }}에서 이동 거리를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| divergence_calculation | scalar | F=({{ a }}x,{{ b }}y,{{ c }}z)의 발산을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| divergence_theorem_application | scalar | F=(x,y,z), 반지름 {{ a }}인 구면의 바깥쪽 유량을 발산정리로 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| dot_product_calculation | scalar | u=({{ a }},{{ b }},{{ c }}), v=({{ b }},-{{ a }},{{ k }})의 내적을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| double_integral_rectangle_calculation | scalar | [0,{{ a }}]×[0,{{ b }}]에서 f(x,y)=x+y의 이중적분을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| duplication_case_handling | expression | y''-{{ a }}²y=exp({{ a }}x)의 미정계수 시험해를 미정계수 1로 놓고 쓰시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| eccentricity_classification | classification | 이심률 e={{ a }}/{{ b }}인 이차곡선을 타원/포물선/쌍곡선으로 분류하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| endpoint_convergence_check | interval | 급수 ∑({{ a }}x)^n/n² (n≥1)의 수렴 구간을 끝점 포함 여부까지 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| flux_calculation | scalar | F=(0,0,{{ c }}),0≤x≤{{ a }},0≤y≤{{ b }},z=0인 면의 위쪽 유량을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| forced_oscillation_solving | expression | y''+{{ a }}²y=cos({{ b }}x)의 특수해 하나를 구하시오. a=b인 공진 경우도 포함한다. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| frenet_frame_calculation | vector | r(t)=({{ a }}cos t,{{ a }}sin t,0)의 t=0에서 단위 주법선 N을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| fundamental_identity_application | vector | f(x,y,z)={{ a }}x²+{{ b }}y²+{{ c }}z²에 대해 curl(grad f)를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| general_solution_decomposition | expression | y''+({{ b }}-{{ a }})y'-{{ a }}*{{ b }}y=-{{ a }}*{{ b }}이다. 일반해를 C1*exp({{ a }}x)+C2*exp(-{{ b }}x)+특수해 형태로 쓰시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| geometric_power_series_representation | expression | \|{{ a }}x\|<1에서 ∑({{ a }}x)^n (n=0부터 무한대)의 합을 닫힌 함수로 나타내시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| greens_theorem_application | scalar | F=(-y,x), 반지름 {{ a }}인 원의 반시계 경계에서 ∮F·dr를 Green 정리로 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| homogeneous_classification | boolean | y''+{{ a }}y'+{{ b }}y={{ d }}는 동차인가? | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| homogeneous_general_solution_construction | expression | y''+({{ b }}-{{ a }})y'-{{ a }}*{{ b }}y=0의 일반해를 C1*exp({{ a }}x)+C2*exp(-{{ b }}x) 순서로 쓰시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| integration_order_swap | scalar | 0≤x≤{{ a }},0≤y≤x의 적분 순서를 바꾸면 0≤y≤{{ a }}, y≤x≤{{ a }}이다. 함수 1의 적분값을 구하시오. | 순서 변경의 영역은 질문에 명시; 변경 후 적분값을 검사 |
| interval_of_convergence_determination | interval | 급수 ∑({{ a }}x)^n/n (n≥1)의 수렴 구간을 끝점 포함 여부까지 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| jacobian_calculation | scalar | x={{ a }}u, y={{ b }}v의 Jacobian ∂(x,y)/∂(u,v)를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| lagrange_system_construction | scalar | f=x²+y², 제약 x+y={{ a }}이다. Lagrange 조건으로 얻는 최소점의 x 좌표를 구하시오. | 제약식/정상 조건에서 얻는 좌표 답만 검사; 시스템을 세우는 서술은 별도 검수 |
| level_curve_sketching | equation | f(x,y)={{ a }}x²+{{ b }}y²의 높이 {{ c }} 등위곡선을 스케치할 기준 방정식을 쓰시오. | 등위곡선 방정식만 검사; 그림은 별도 검수 |
| level_surface_tangent_plane_construction | equation | 구 x²+y²+z²={{ a }}²+{{ b }}²+{{ c }}²의 점 ({{ a }},{{ b }},{{ c }})에서 접평면을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| line_equation_construction | equation | 점 ({{ a }},{{ b }},{{ c }})를 지나고 방향 (1,1,1)인 직선의 매개방정식을 변수 t로 쓰시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| line_integral_via_potential | scalar | F=∇(x²+y²+z²), 시작점 원점, 끝점 ({{ a }},{{ b }},{{ c }})인 곡선을 따른 선적분을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| line_segment_parametrization | equation | A=({{ a }},0), B=(0,{{ b }})를 잇는 선분의 매개화 x=a(1-t), y=bt, 0≤t≤1을 방정식 쌍으로 쓰시오(a={{ a }}, b={{ b }}). | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| linearization_estimation | numerical_approximation | f(x,y)={{ a }}x²+{{ b }}y²를 (1,1)에서 선형화해 f(3/2,1)을 근사하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| magnitude_and_unit_vector_calculation | vector | v=({{ a }},{{ b }},{{ c }})의 방향 단위벡터를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| mass_and_moment_calculation | scalar | 밀도 {{ c }}인 [0,{{ a }}]×[0,{{ b }}] 직사각형 판의 질량을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| max_increase_direction_calculation | vector | f(x,y,z)={{ a }}x+{{ b }}y+{{ c }}z의 최대 증가 방향 단위벡터를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| moment_of_inertia_calculation | scalar | 밀도 1인 [0,{{ a }}]×[0,{{ b }}]×[0,{{ c }}] 직육면체의 z축 관성모멘트를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| multivariable_chain_rule_application | expression | f(x,y)={{ a }}x²+{{ b }}y², x=t, y=t²이다. 합성함수의 t 도함수를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| multivariable_domain_calculation | expression | f(x,y)=log({{ a }}²-x²-y²)의 실수 정의역 조건을 부등식으로 쓰시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| multivariable_implicit_differentiation | expression | x²+y²+z²={{ a }}²에서 z≠0이다. z_x를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| normal_line_construction | equation | 구 x²+y²+z²={{ a }}²+{{ b }}²+{{ c }}²의 점 ({{ a }},{{ b }},{{ c }})에서 법선 직선의 매개방정식을 변수 t로 쓰시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| osculating_circle_construction | vector | r(t)=({{ a }}cos t,{{ a }}sin t,0)의 t=0에서 접촉원의 중심을 벡터로 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| parallel_planes_distance_calculation | scalar | 평면 x+y+z={{ a }}와 x+y+z=-{{ b }} 사이 거리를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| parallelepiped_volume_calculation | scalar | 세 모서리 ({{ a }},0,0),(0,{{ b }},0),(0,0,{{ c }})인 평행육면체 부피를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| parallelism_check | boolean | u=({{ a }},{{ b }},{{ c }}), v=({{ k }})*{{ N }}u는 평행한가? | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| parameter_elimination | equation | X(t)={{ a }}t, Y(t)={{ b }}t²에서 t를 제거하여 y,x 방정식을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| parametric_concavity_classification | classification | X(t)={{ a }}t, Y(t)=({{ k }})*{{ b }}t²인 곡선을 위로 오목/아래로 오목으로 분류하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| parametric_tangent_line_equation | equation | X(t)={{ a }}t, Y(t)={{ b }}t²의 t=1에서 접선 방정식을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| partial_derivative_calculation | expression | f(x,y)={{ a }}x²+{{ b }}xy+{{ c }}y²의 ∂f/∂x를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| path_test_limit_nonexistence | boolean | f(x,y)={{ a }}xy/(x²+y²)의 (0,0) 극한이 존재하지 않는가? 참/거짓으로 답하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| period_frequency_calculation | scalar | 질량 m={{ a }}, 용수철 상수 K={{ b }}인 단순조화운동의 주기를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| plane_equation_construction | equation | 법선 ({{ a }},{{ b }},{{ c }})이고 점 ({{ d }},0,0)을 지나는 평면 방정식을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| point_line_distance_calculation | scalar | 점 ({{ a }},{{ b }},{{ c }})과 x축 사이 거리를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| point_plane_distance_calculation | scalar | 점 ({{ a }},{{ b }},{{ c }})과 평면 x+y+z=0의 거리를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| polar_curve_identification | classification | 극좌표 r={{ a }}(1+cos θ)는 카디오이드/장미곡선 중 무엇인가? | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| polar_double_integral_calculation | scalar | 반지름 {{ a }}인 원판에서 {{ b }}*(x²+y²)를 이중적분하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| polar_double_integral_setup | expression | 반지름 {{ a }}인 원판에서 f(x,y)=x²+y²의 극좌표 적분을 세우시오. r=x로 적을 때 Jacobian 포함 피적분함수를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| polar_substitution_limit_calculation | scalar | (x,y)→(0,0)에서 {{ a }}(x²+y²)의 극한을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| polar_symmetry_test_application | boolean | r={{ a }}(1+({{ k }})*cos θ)는 극축에 대칭인가? | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| polar_to_cartesian_circle_conversion | equation | 극좌표 r=2*{{ a }}cos θ를 직교좌표 방정식으로 바꾸시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| position_reconstruction_from_acceleration | vector | r''(t)=({{ a }},{{ b }},{{ c }}), r'(0)=r(0)=(0,0,0)이다. r(1)을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| potential_function_construction | expression | F=(2*{{ a }}x,2*{{ b }}y,2*{{ c }}z)의 퍼텐셜 중 원점에서 0인 함수를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| power_series_combination | scalar | F=∑x^n, G=∑({{ a }}x)^n (n≥0)일 때 {{ b }}F+G의 x^{{ N }} 계수를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| power_series_solution_construction | expression | y''+{{ a }}²y=0, y(0)=1,y'(0)=0의 급수해에서 x^(2{{ N }}) 이하 부분합을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| power_series_substitution | expression | 1/(1-{{ a }}x²)의 거듭제곱급수에서 x^(2{{ N }}) 항까지의 부분합을 쓰시오. \|{{ a }}x²\|<1이다. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| projectile_motion_solving | scalar | 수직위치 z(t)={{ a }}t-t²인 포물체가 다시 z=0에 도달하는 양의 시간을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| projectile_position_construction | vector | 중력가속도 g=2, 초기위치 0, 초기속도 ({{ a }},{{ b }},{{ c }})인 포물체의 t=1 위치를 구하시오(z가 수직축). | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| projection_calculation | vector | u=({{ a }},{{ b }},{{ c }}), v=({{ b }},-{{ a }},{{ k }})이다. u를 v에 정사영한 벡터를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| quadric_surface_classification | classification | 곡면 z=({{ k }})*x²+{{ a }}y²를 타원포물면/쌍곡포물면으로 분류하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| radius_of_convergence_calculation | scalar | 거듭제곱급수 ∑({{ a }}x)^n (n≥0)의 수렴 반지름을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| recurrence_relation_derivation | expression | y''+{{ a }}²y=0에 y=∑c_n x^n를 대입한다. c_(n+2)=M(n)c_n에서 M(n)을 n=x로 쓰시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| region_type_classification | scalar | 영역 0≤x≤{{ a }}, 0≤y≤x는 I형(세로 단면)으로 기술 가능한가? 가능하면 1, 불가능하면 0으로 답하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| region_with_cavity_flux | scalar | F=(x,y,z), {{ a }}≤r≤({{ a }}+{{ b }})인 구껍질 경계의 영역 바깥 방향 총유량을 구하시오(안쪽 법선은 중심 방향). | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| region_with_hole_line_integral | scalar | {{ a }}≤r≤({{ a }}+{{ b }})인 원환에서 F=(-y,x)의 경계 선적분을 구하시오. 바깥은 반시계, 안쪽은 시계다. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| required_degree_determination | scalar | f(x)=1/(1-x)의 0 중심 Taylor 다항식으로 f(1/2)를 근사한다. 정확한 나머지 2^(-m)≤1/(10*{{ a }})를 만족하는 최소 차수 m을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| resonance_condition_check | boolean | 감쇠 없는 y''+{{ a }}²y=cos({{ b }}x)는 공진 조건을 만족하는가? | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| rlc_analogy_application | expression | L={{ a }}, R={{ b }}, C=1/{{ c }}인 RLC를 용수철계 m u''+γ u'+K u=0에 대응시킨다. K만 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| rlc_equation_construction | expression | L={{ a }}, R={{ b }}, C=1/{{ c }}, 전압={{ d }}인 직렬 RLC에서 q''를 q=x, q'=y의 식으로 나타내시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| scalar_line_integral_calculation | scalar | 선분 r(t)=({{ a }}t,{{ b }}t,0),0≤t≤1에서 f=1의 선적분을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| scalar_surface_integral_calculation | scalar | 반지름 {{ a }}인 구면에서 상수 함수 {{ b }}의 면적분을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| second_derivative_test_classification | classification | f(x,y)={{ a }}x²+({{ k }})*{{ b }}y²의 원점 임계점을 극소/안장점으로 분류하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| second_order_ivp_solving | expression | y''+({{ b }}-{{ a }})y'-{{ a }}*{{ b }}y=0, y(0)={{ c }}, y'(0)={{ d }}의 해를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| second_order_partial_calculation | expression | f(x,y)={{ a }}x²+{{ b }}xy+{{ c }}y²의 ∂²f/∂x∂y를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| series_based_integration | expression | exp({{ a }}x)의 {{ N }}차 Maclaurin 다항식을 0부터 x까지 적분하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| series_based_limit_evaluation | scalar | 이항급수 전개를 이용하여 x→0에서 ((1+x)^{{ a }}-1-{{ a }}x)/x²의 극한을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| series_convergence_interval_identification | interval | ln(1+{{ a }}x)의 급수 ∑(-1)^(n+1)({{ a }}x)^n/n (n≥1)의 수렴 구간을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| shm_equation_setup | scalar | 질량 m={{ a }}, 용수철 상수 K={{ b }}의 자유운동 방정식을 y''+ω²y=0으로 쓴다. ω²를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| solid_volume_via_triple_integral | scalar | 모서리 길이 {{ a }},{{ b }},{{ c }}인 직육면체의 부피를 삼중적분으로 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| space_curve_arc_length_calculation | scalar | r(t)=({{ a }}t,{{ b }}t,{{ c }}t), 0≤t≤{{ N }}의 길이를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| space_curve_identification | expression | r(t)=({{ a }}cos t,{{ a }}sin t,{{ b }}t)가 놓이는 원기둥의 방정식 좌변을 x,y,z로 쓰시오. 우변은 {{ a }}²이다. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| speed_change_analysis | scalar | r(t)=({{ a }}t²,0,0), t>0일 때 속력의 시간 변화율을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| sphere_equation_construction | equation | 중심 ({{ a }},{{ b }},{{ c }}), 반지름 {{ N }}인 구의 방정식을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| spherical_triple_integral_calculation | scalar | 반지름 {{ a }}인 구에서 상수 함수 {{ b }}를 구면좌표로 삼중적분하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| spherical_triple_integral_setup | expression | 반지름 {{ a }}인 구의 부피를 구면좌표로 적분한다. ρ=x, φ=y로 쓸 때 Jacobian을 쓰시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| stokes_theorem_application | scalar | F=(-y,x,0), 반지름 {{ a }}인 z=0 원의 반시계 방향 선적분을 Stokes 정리로 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| surface_area_calculation | scalar | z={{ a }}x+{{ b }}y,0≤x,y≤1인 평면 조각의 넓이를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| surface_area_of_revolution_about_x_axis | scalar | y={{ a }}x, 0≤x≤{{ b }}를 x축 둘레로 회전한 곡면의 넓이를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| surface_area_of_revolution_about_y_axis | scalar | y={{ a }}x, 0≤x≤{{ b }}를 y축 둘레로 회전한 곡면의 넓이를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| surface_choice_for_stokes | scalar | 반지름 {{ a }}인 z=0 원의 반시계 경계에 대해 Stokes 정리의 위쪽 원판을 선택했다. F=(-y,x,0)의 curl 유량을 구하시오. | 선택한 원판/방향을 명시하고 결과만 검사; 임의 곡면 선택은 별도 검수 |
| surface_normal_calculation | vector | 평면 z={{ a }}x+{{ b }}y에서 위쪽 단위법선벡터를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| tangent_line_construction | equation | r(t)=({{ a }}t,{{ b }}t²,{{ c }}t³)의 t=1에서 접선의 매개방정식을 새 매개변수 t로 쓰시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| tangent_plane_construction | equation | z={{ a }}x²+{{ b }}y²의 (x,y)=(1,1)에서 접평면 방정식을 쓰시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| taylor_coefficient_extraction | expression | exp({{ a }}x)의 x=0 Taylor 전개에서 x^{{ N }} 계수를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| taylor_error_estimation | numerical_approximation | [-1,1]에서 \|f^(({{ N }}+1))(x)\|≤{{ a }}이다. 0 중심 {{ N }}차 Taylor 다항식으로 f(1)을 근사할 때 Lagrange 나머지 상한을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| taylor_polynomial_construction | expression | exp({{ a }}x)의 x=0에서 {{ N }}차 Taylor 다항식을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| taylor_series_derivation | expression | exp({{ a }}x)의 Maclaurin 급수를 유도하시오. 자동 채점 답은 0차부터 {{ N }}차까지의 다항식이다. | 유도 결과의 유한 부분합만 검사; 무한 전개/서술 유도는 사람 검수 |
| term_by_term_differentiation | expression | ∑({{ a }}x)^n (n≥0)의 수렴 구간 안에서 항별 미분한 급수의 닫힌 합을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| term_by_term_integration | expression | ∑({{ a }}x)^n (n≥0)을 0부터 x까지 항별 적분한 급수의 닫힌 합을 구하시오. \|{{ a }}x\|<1이다. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| total_differential_estimation | numerical_approximation | f(x,y)={{ a }}x²+{{ b }}y², (x,y)=(1,1), dx=dy=1/2이다. df를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| triple_integral_calculation | scalar | [0,{{ a }}]×[0,{{ b }}]×[0,{{ c }}]에서 x+y+z를 삼중적분하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| triple_integral_setup | expression | 0≤x≤{{ a }},0≤y≤{{ b }},0≤z≤{{ c }}에서 밀도 x+y+z를 적분한다. z를 먼저 적분한 결과를 x,y의 식으로 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| two_lines_relation_classification | classification | L1=(t,0,0), L2=(t,{{ a }},{{ d }})이다. 두 직선을 평행/교차/꼬임 중에서 분류하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| two_planes_relation_classification | classification | P1: x+y+z={{ a }}, P2: x+y+z={{ b }}이다. 두 평면을 일치/평행으로 분류하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| undetermined_coefficients_ansatz_selection | expression | y''-{{ a }}²y=exp({{ b }}x), b={{ b }}, a={{ a }}이다. 미정계수법의 시험해를 미정계수 1로 놓고 쓰시오. 중복이면 x 인수를 붙이시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| undetermined_coefficients_solving | expression | y''-{{ a }}²y={{ b }}의 상수 특수해 하나를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| uniform_circular_motion_calculation | scalar | r(t)=({{ a }}cos({{ b }}t),{{ a }}sin({{ b }}t),0)의 속력을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| unit_tangent_calculation | vector | r(t)=({{ a }}t,{{ b }}t,{{ c }}t)의 단위 접선벡터를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| variation_of_parameters_application | expression | y''+{{ a }}²y={{ b }}에서 매개변수 변화법으로 구할 수 있는 상수 특수해 하나를 구하시오. | 매개변수 변화의 특수해 결과만 검사; 적분 과정은 별도 검수 |
| vector_chain_rule_application | vector | r(u)=({{ a }}u,{{ b }}u²,0), u=t²이다. d r(u(t))/dt를 t=1에서 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| vector_derivative_calculation | vector | r(t)=({{ a }}t,{{ b }}t²,{{ c }}t³)의 t={{ N }}에서 r'(t)를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| vector_differentiation_rule_application | vector | u(t)=({{ a }}t,0,0), v(t)=(0,{{ b }}t,0)이다. d(u×v)/dt를 t={{ N }}에서 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| vector_field_classification | classification | F(x,y)=({{ a }}x,{{ a }}y)를 방사형/회전형으로 분류하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| vector_field_domain_calculation | classification | F=({{ a }}x,{{ b }}y,{{ c }}z)/(x²+y²+z²)의 정의역을 R³ 또는 R³에서 원점 제외 중에서 답하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| vector_from_points_construction | vector | P=({{ a }},{{ b }},{{ c }}), Q=({{ b }},{{ c }},{{ a }})이다. 벡터 PQ를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| vector_function_domain_calculation | set | r(t)=(sqrt(t-{{ a }}),log(t-{{ b }}),t)의 실수 정의역을 집합으로 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| vector_initial_value_problem | vector | r'(t)=({{ a }},{{ b }}t,{{ c }}t²), r(0)=(0,0,0)이다. r(1)을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| vector_integral_calculation | vector | r(t)=({{ a }}t,{{ b }}t²,{{ c }}t³)를 t=0부터 1까지 적분한 벡터를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| vector_line_integral_calculation | scalar | F=(x,y,0), r(t)=({{ a }}t,{{ b }}t,0),0≤t≤1에서 F·dr의 적분을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| velocity_acceleration_calculation | vector | r(t)=({{ a }}t,{{ b }}t²,{{ c }}t³)의 t={{ N }}에서 가속도를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| volume_between_surfaces_calculation | scalar | [0,{{ a }}]×[0,{{ b }}] 위에서 z=0과 z={{ c }} 사이 부피를 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| work_calculation | scalar | 일정한 힘 F=({{ a }},{{ b }},{{ c }})가 변위 d=({{ b }},-{{ a }},{{ k }}) 동안 한 일을 구하시오. | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
| wronskian_linear_independence_check | boolean | exp({{ a }}x)와 exp({{ b }}x)는 실수 전체에서 선형독립인가? | 질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수 |
