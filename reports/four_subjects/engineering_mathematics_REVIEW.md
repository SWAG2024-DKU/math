# 공학수학 전체 Rule 검수 결과

총 104개. 결과: {'applied': 104}
실행 검증 통과: 104개. 최종 사람 검수는 별도입니다.

자동 검수/생성 검증과 최종 사람 검수는 다릅니다. applied도 ready 또는 출제 승인 상태가 아닙니다.

| 유형 | 처리 | 실행 검사 | 원본 문제 | 적용 범위/남은 작업 |
|---|---|---|---|---|
| analyticity_verification | applied | passed | 기존 구현 | f(w)=w^{{ n }}+{{ a }}*conjugate(w)는 복소평면 전체에서 해석적인가?; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| applied_ode_modeling | applied | passed | 기존 구현 | 초기 개체수 {{ b }}, 연속 상대성장률 {{ a }}인 지수성장 모델의 N(t)를 구하시오. 시간 단위는 성장률의 역수이다.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| autonomous_stability_analysis | applied | passed | 기존 구현 | 평형점 계산; 안정성 서술 대신 평형값 전체 목록; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| basic_laplace_calculation | applied | passed | 기존 구현 | f(t)={{ a }}t^{{ n }}의 단측 Laplace 변환 F(s), s>0을 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| bernoulli_ode_solving | applied | passed | 기존 구현 | y'+{{ a }}y={{ a }}y², y(0)=1/({{ c }}+1)의 해 y(t)를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| bisection_iteration | applied | passed | 기존 구현 | f(x)=x²-{{ a }}, 초기구간[0,{{ a+1 }}]에서 이분법의 첫 평가점 c0를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| boundary_condition_identification | applied | passed | 기존 구현 | 끝점의 경계조건(mode={{ n }}). mode 1: u={{ a }}, mode 2: u_x={{ a }}, mode 3: u+u_x={{ a }}. 경계조건을 Dirichlet/Neumann/Robin 중 분류하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| cauchy_integral_formula_calculation | applied | passed | 기존 구현 | 양의 방향 /w/=2에서 ∮{{ a }}/w dw를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| cauchy_riemann_verification | applied | passed | 기존 구현 | u(x,y)={{ a }}x²-{{ a }}y², v(x,y)=({{ k }})*2*{{ a }}xy는 R² 전체에서 Cauchy–Riemann 방정식을 만족하는가?; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| cauchy_theorem_application | applied | passed | 기존 구현 | 양의 방향 단위원에서 ∮{{ a }}w^{{ n }} dw를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| characteristic_equation_setup | applied | passed | 기존 구현 | y''+({{ a+b }})y'+({{ a*b }})y=0의 특성다항식을 s로 쓰시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| complex_eigenvalue_solving | applied | passed | 기존 구현 | u'=-{{ a }}v, v'={{ a }}u, U(0)=({{ b }},0)의 벡터해를 열행렬로 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| complex_elementary_function_calculation | applied | passed | 기존 구현 | exp({{ a }}+iπ) 값을 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| complex_form_conversion | applied | passed | 기존 구현 | 복소수 {{ a }}+i{{ b }}를 r*exp(iθ) 극형식으로 바꾸되 (r,θ)를 열행렬로 쓰시오. θ는 주편각이다.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| complex_fourier_calculation | applied | passed | 기존 구현 | f(x)={{ a }}cos({{ n }}x)+{{ b }}sin({{ n }}x)를 Σc_m exp(imx)로 쓴다. c_n을 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| complex_limit_evaluation | applied | passed | 기존 구현 | lim[w→{{ b }}] (w^{{ n }}-{{ b**n }})/(w-{{ b }})를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| complex_line_integral_calculation | applied | passed | 기존 구현 | 직선경로 w:0→{{ a }}+i{{ b }}를 따라 ∫w dw를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| condition_number_calculation | applied | passed | 기존 구현 | A=diag({{ a }},{{ b }})의 2-노름 조건수 κ2를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| conservative_field_verification | applied | passed | 기존 구현 | R²에서 F=({{ a }}y,({{ k }})*{{ a }}x)는 보존장인가?; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| convolution_calculation | applied | passed | 기존 구현 | t≥0에서 f(t)={{ a }}, g(t)={{ b }}t의 인과적 합성곱 (f*g)(t)를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| coordinate_transformation_integration | applied | passed | 기존 구현 | 반지름 {{ a }}, 높이 {{ b }}인 원기둥의 ∭1 dV를 원통좌표로 계산하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| curl_calculation | applied | passed | 기존 구현 | F=(-{{ a }}y,{{ a }}x,{{ b }}z)의 curl을 열벡터로 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| demoivre_power_calculation | applied | passed | 기존 구현 | (cos(π/2)+i sin(π/2))^{{ n }}을 직교형식으로 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| derivative_laplace_transformation | applied | passed | 기존 구현 | f(t)={{ b }}exp(-{{ a }}t)의 f'(t)에 대한 단측 Laplace 변환을 구하시오(s>0).; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| dirac_delta_laplace | applied | passed | 기존 구현 | Dirac delta δ(t-{{ a }})의 단측 Laplace 변환을 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| divergence_calculation | applied | passed | 기존 구현 | F=({{ a }}x,{{ b }}y,{{ c }}z)의 divergence를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| divergence_theorem_calculation | applied | passed | 기존 구현 | 단위구의 바깥쪽 법선에 대해 F=({{ a }}x,{{ a }}y,{{ a }}z)의 전체 flux를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| eigenfunction_expansion_solving | applied | passed | 기존 구현 | 열방정식 u_t={{ b }}u_xx의 한 고유함수 초기자료 {{ a }}sin({{ n }}x), 구간(0,π), 영 Dirichlet 경계의 해를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| eigenvalue_system_solving | applied | passed | 기존 구현 | u'={{ a }}u, v'=-{{ b }}v, U(0)=({{ b }},{{ c }})의 벡터해를 열행렬로 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| error_calculation | applied | passed | 기존 구현 | 정확값 {{ a }}/{{ b }}, 근삿값 ({{ a }}/{{ b }})+1/{{ c }}의 절대오차를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| euler_cauchy_solving | applied | passed | 기존 구현 | t>0에서 t²y''+(1-{{ a+b }})ty'+{{ a*b }}y=0의 일반해를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| euler_method_calculation | applied | passed | 기존 구현 | y'={{ a }}y,y(0)={{ b }}, h=1/{{ c }}의 명시 Euler 첫 단계 y1을 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| exact_integrating_factor_solving | applied | passed | 기존 구현 | x>0에서 {{ a }}y dx+({{ a+b }})x dy=0에 곱할 x만의 적분인자 μ(x)를 구하시오. μ(1)=1이다.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| exact_ode_solving | applied | passed | 기존 구현 | (2*{{ a }}x+y)dx+(x+2*{{ b }}y)dy=0의 보존량 F(x,y)를 구하시오. F(0,0)=0으로 정규화하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| field_identification | applied | passed | 기존 구현 | F(x,y,z)=({{ a }}x,{{ b }}y,{{ c }}z)는 스칼라장이 아니라 벡터장인가?; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| finite_difference_solving | applied | passed | 기존 구현 | u″=0, 0≤x≤1, u(0)=0,u(1)={{ a }}, h=1/3에서 중앙차분 내부값 (u1,u2)를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| first_shifting_calculation | applied | passed | 기존 구현 | exp({{ a }}t)*sin({{ b }}t)의 단측 Laplace 변환을 구하시오(s>{{ a }}).; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| fixed_point_iteration_calculation | applied | passed | 기존 구현 | g(x)=(x+{{ a }})/2, x0={{ b }}일 때 고정점 반복 x1=g(x0)를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| fourier_convolution_calculation | applied | passed | 기존 구현 | F(s)=∫R f(t)exp(-ist)dt 관례에서 f=exp(-{{ a }}/t/), g=exp(-{{ b }}/t/)이다. f*g의 Fourier 변환을 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| fourier_properties_calculation | applied | passed | 기존 구현 | F(s)=∫R f(t)exp(-ist)dt 관례로 f(t)=exp(-{{ a }}/t-{{ b }}/)의 Fourier 변환을 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| fourier_series_calculation | applied | passed | 기존 구현 | f(x)={{ a }}cos({{ n }}x)+{{ b }}sin({{ n }}x)의 2π Fourier 계수 (a_n,b_n)를 열행렬로 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| fourier_transform_calculation | applied | passed | 기존 구현 | F(s)=∫R f(t)exp(-ist)dt 관례로 f(t)={{ b }}exp(-{{ a }}/t/)의 Fourier 변환을 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| fundamental_frequency_calculation | applied | passed | 기존 구현 | f(t)={{ a }}sin({{ n }}t)의 기본 각주파수를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| gaussian_elimination_solving | applied | passed | 기존 구현 | [[1,{{ a }}],[0,1]]u=({{ b }},{{ c }})를 푸시오. 답은 열벡터이다.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| generalized_eigenvector_solving | applied | passed | 기존 구현 | M=[[{{ a }},1],[0,{{ a }}]], 고유벡터 v=(1,0)이다. (M-aI)w=v, w의 첫 성분0을 만족하는 w를 열행렬로 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| gibbs_phenomenon_analysis | applied | passed | 기존 구현 | 2π 주기 함수의 x=0 좌극한은 -{{ a }}, 우극한은 {{ b }}이다. Fourier 부분합의 0에서의 극한값을 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| gradient_directional_derivative_calculation | applied | passed | 기존 구현 | f(x,y,z)={{ a }}x²+{{ b }}y²+{{ c }}z²의 점(1,0,0), 단위방향(1,0,0) 방향미분을 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| green_theorem_calculation | applied | passed | 기존 구현 | 단위정사각형의 반시계 경계에서 ∮(-{{ a }}y)dx+({{ b }}x)dy를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| half_range_expansion_calculation | applied | passed | 기존 구현 | 0<x<π에서 f(x)={{ a }}의 반구간 sine 급수의 b_n을 n={{ n }}에 대해 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| harmonic_conjugate_calculation | applied | passed | 기존 구현 | u={{ a }}(x²-y²)의 조화켤레 v(x,y)를 v(0,0)=0으로 구하시오. f=u+iv 관례이다.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| heat_equation_solving | applied | passed | 기존 구현 | 0<x<π,t≥0에서 u_t={{ b }}u_xx, u(0,t)=u(π,t)=0, u(x,0)={{ a }}sin({{ n }}x)의 해를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| higher_order_ivp_solving | applied | passed | 기존 구현 | y''+{{ a*a }}y=0, y(0)={{ b }}, y'(0)={{ c }}의 해를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| higher_order_ode_classification | applied | passed | 기존 구현 | y''+{{ a }}y'+{{ b }}y^{{ n }}=0은 선형 ODE인가?; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| homogeneous_ode_solution_construction | applied | passed | 기존 구현 | y''-{{ a*a }}y=0의 일반해를 C1,C2,t로 쓰시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| homogeneous_ode_solving | applied | passed | 기존 구현 | t>0에서 y'=y/t+{{ a }}, y(1)={{ b }}의 해 y(t)를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| interpolation_error_analysis | applied | passed | 기존 구현 | f(x)={{ a }}x²의 0,1 선형보간값 p(1/2)와 실제 f(1/2)의 절대오차를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| inverse_laplace_calculation | applied | passed | 기존 구현 | F(s)={{ b }}/(s+{{ a }})의 t≥0 역 Laplace 변환을 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| iterative_solver_calculation | applied | passed | 기존 구현 | A=[[{{ a+1 }},1],[1,{{ b+1 }}]], rhs=({{ b }},{{ c }}), x0=(0,0)의 Jacobi 첫 반복을 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| ivp_uniqueness_test | applied | passed | 기존 구현 | y'=({{ k }})*{{ a }}y+{{ b }}t, y(0)={{ c }}는 모든 유한한 t에서 유일한 해를 갖는가?; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| lagrange_interpolation_calculation | applied | passed | 기존 구현 | 점 (0,{{ a }}),(1,{{ a+b+c }}),(2,{{ a+2*b+4*c }})의 Lagrange 보간다항식 p(x)를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| laplace_definition_check | applied | passed | 기존 구현 | f(t)=exp({{ a }}t)의 단측 Laplace 적분은 s={{ a }}+({{ k }})에서 수렴하는가?; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| laplace_ivp_solving | applied | passed | 기존 구현 | Laplace 변환으로 y'+{{ a }}y={{ b }}, y(0)={{ c }}의 해 y(t)를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| laplace_poisson_analysis | applied | passed | 기존 구현 | 단위 정사각형에서 Δu=2({{ a+b }}), 경계값 u={{ a }}x²+{{ b }}y²이다. u(x,y)를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| laplacian_calculation | applied | passed | 기존 구현 | f={{ a }}x²+{{ b }}y²+{{ c }}z²의 Laplacian을 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| laurent_series_calculation | applied | passed | 기존 구현 | f(w)={{ a }}/w+{{ b }}+{{ c }}w의 0</w/<1 Laurent 다항식을 쓰시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| least_squares_calculation | applied | passed | 기존 구현 | 점 (0,{{ a-b }}),(1,{{ a }}),(2,{{ a+b }})의 절편 포함 OLS 직선 yhat(x)를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| line_integral_calculation | applied | passed | 기존 구현 | F=({{ a }}x,{{ b }}y), r(t)=(t,t), 0≤t≤{{ c }}를 따르는 선적분 ∫F·dr를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| linear_ode_solving | applied | passed | 기존 구현 | y'+{{ a }}y={{ b }}, y(0)={{ c }}의 해 y(t)를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| linear_stability_analysis | applied | passed | 기존 구현 | M=diag(({{ k }})*{{ a }},-{{ b }})인 U′=MU의 원점을 안정점/안장점으로 분류하시오. 안정점은 점근안정 절점을 뜻한다.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| lu_decomposition_calculation | applied | passed | 기존 구현 | A=[[1,{{ a }}],[{{ b }},{{ a*b+c }}]]의 대각원소1인 L을 갖는 LU 분해를 [L/U]로 쓰시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| matrix_exponential_calculation | applied | passed | 기존 구현 | M=diag({{ a }},-{{ b }})의 exp(tM)을 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| mechanical_vibration_solving | applied | passed | 기존 구현 | 질량1, 감쇠0, 용수철상수 {{ a*a }}의 자유진동 x(0)={{ b }}, x'(0)=0의 변위 x(t)를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| newton_divided_difference_calculation | applied | passed | 기존 구현 | 점 (0,{{ a }}),(1,{{ a+b+c }}),(2,{{ a+2*b+4*c }})의 Newton 차분 보간다항식 p(x)를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| newton_method_calculation | applied | passed | 기존 구현 | f(x)=x²-{{ a }}, x0={{ b }}의 Newton 첫 반복 x1을 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| nonhomogeneous_solution_structure | applied | passed | 기존 구현 | y''-{{ a*a }}y={{ b }}의 일반해 y_h+y_p를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| nonhomogeneous_system_solving | applied | passed | 기존 구현 | u'=-{{ a }}u+{{ b }}, v'=-{{ c }}v, U(0)=(0,1)의 벡터해를 열행렬로 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| nonlinear_linearization_analysis | applied | passed | 기존 구현 | u'={{ a }}u+v², v'=-{{ b }}v+u²를 원점에서 선형화한 Jacobian을 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| numerical_differentiation_calculation | applied | passed | 기존 구현 | f(x)={{ a }}x², x={{ b }}, h=1/{{ c }}의 중앙차분 [f(x+h)-f(x-h)]/(2h)를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| ode_classification | applied | passed | 기존 구현 | y'+{{ a }}y^{{ n }}={{ b }}t는 y에 관한 선형 ODE인가?; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| orthogonality_integral_check | applied | passed | 기존 구현 | ∫[-π,π] cos({{ a }}x)cos({{ b }}x) dx를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| parseval_identity_calculation | applied | passed | 기존 구현 | f(x)={{ a }}cos({{ n }}x)+{{ b }}sin({{ n }}x)에 대해 (1/π)∫[-π,π] f² dx를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| pde_classification | applied | passed | 기존 구현 | u_xx+({{ k }})*{{ a }}u_yy=0을 elliptic/hyperbolic으로 분류하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| phase_plane_analysis | applied | passed | 기존 구현 | u'=u({{ a }}-u), v'=-{{ b }}v의 모든 평형점을 벡터 목록으로 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| residue_theorem_calculation | applied | passed | 기존 구현 | 양의 방향 단위원에서 ∮{{ a }}/w dw를 residue 정리로 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| runge_kutta_calculation | applied | passed | 기존 구현 | y'={{ a }}t,y(0)={{ b }}, h=1/{{ c }}의 고전 RK4 첫 단계 y1을 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| s_differentiation_calculation | applied | passed | 기존 구현 | t*exp(-{{ a }}t)의 단측 Laplace 변환을 s 미분 성질로 구하시오(s>0).; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| secant_method_calculation | applied | passed | 기존 구현 | f(x)=x²-{{ a }}, x0=0,x1={{ b }}의 할선법 첫 새 반복 x2를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| second_shifting_calculation | applied | passed | 기존 구현 | H(t-{{ a }})*(t-{{ a }})^{{ n }}의 단측 Laplace 변환을 구하시오(s>0). H는 Heaviside 함수이다.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| separable_ode_solving | applied | passed | 기존 구현 | y'=({{ a }})y, y(0)={{ b }}의 해 y(t)를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| separation_of_variables_solving | applied | passed | 기존 구현 | u_t={{ b }}u_xx, 0<x<π, 영 Dirichlet 경계이다. n={{ n }} 분리해의 T(0)=1인 시간인자 T(t)를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| simpson_rule_calculation | applied | passed | 기존 구현 | f(x)={{ a }}x²를 [0,{{ b }}]에서 2개 하위구간 Simpson 공식으로 적분 근사하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| singularity_classification | applied | passed | 기존 구현 | f(w)={{ a }}/w^{{ n }}의 w=0 특이점을 분류하시오. 답 형식은 pole:N이다(N은 차수).; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| state_space_conversion | applied | passed | 기존 구현 | y''+{{ a }}y'+{{ b }}y=0에서 U=(y,y')^T의 상태행렬을 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| steady_transient_analysis | applied | passed | 기존 구현 | 막대 0≤x≤{{ b }}, 열방정식의 끝 온도 u(0,t)=0,u({{ b }},t)={{ a }}이다. 정상상태 온도 u_s(x)를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| stokes_theorem_calculation | applied | passed | 기존 구현 | 단위원판의 위쪽 법선에 맞춘 반시계 경계에서 F=(-{{ a }}y,{{ a }}x,0)의 순환을 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| sturm_liouville_analysis | applied | passed | 기존 구현 | -X″=λX, X(0)=X({{ a }}π)=0의 n={{ n }}번째 고윳값을 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| superposition_verification | applied | passed | 기존 구현 | y''+{{ a*a }}y=0의 두 해 sin({{ a }}t), cos({{ a }}t의 {{ b }},{{ c }} 선형결합도 해인가?; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| surface_integral_calculation | applied | passed | 기존 구현 | F=(0,0,{{ a }}), 0≤x≤{{ b }}, 0≤y≤{{ c }}, z=0의 위쪽 방향 flux를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| system_matrix_form_conversion | applied | passed | 기존 구현 | u'={{ a }}u+{{ b }}v, v'=-{{ b }}u+{{ c }}v를 U'=MU로 쓰기 위한 M을 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| trapezoidal_rule_calculation | applied | passed | 기존 구현 | f(x)={{ a }}x²를 [0,{{ b }}]에서 한 패널 사다리꼴 공식으로 적분 근사하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| undetermined_coefficients_solving | applied | passed | 기존 구현 | y''-{{ a*a }}y={{ b }}의 상수 특수해를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| variation_of_parameters_solving | applied | passed | 기존 구현 | 매개변수변환법으로 y''={{ a }}t, y(0)=y'(0)=0의 해를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| wave_equation_solving | applied | passed | 기존 구현 | 0<x<π에서 u_tt={{ b*b }}u_xx, 영 Dirichlet 경계, u(x,0)={{ a }}sin({{ n }}x), u_t(x,0)=0의 해를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
| wronskian_calculation | applied | passed | 기존 구현 | f(t)=exp({{ a }}t), g(t)=exp(-{{ b }}t)의 W=f*g′-f′*g를 구하시오.; 대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요 |
