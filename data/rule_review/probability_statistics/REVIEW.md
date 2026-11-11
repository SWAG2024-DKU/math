# 확률통계 대표 유형 전체 Rule 검수 결과

총 23개. 결과: {'applied': 23}
실행 검증 통과: 23개. 최종 사람 검수는 별도입니다.

자동 검수/생성 검증과 최종 사람 검수는 다릅니다. applied도 ready 또는 출제 승인 상태가 아닙니다.

| 유형 | 처리 | 실행 검사 | 원본 문제 | 적용 범위/남은 작업 |
|---|---|---|---|---|
| anova_table_completion | applied | passed | 기존 구현 | 균형 3집단의 집단간 제곱합 한 셀 |
| assumption_check | applied | passed | 기존 구현 | 표본분산 정의에 필요한 n≥2 판정 |
| coefficient_estimation | applied | passed | 기존 구현 | 등간격 x와 정확한 직선 자료의 OLS 기울기 |
| concept_identification | applied | passed | 기존 구현 | 무작위 처치 배정 여부로 실험/관측 연구 식별 |
| confidence_interval | applied | passed | 기존 구현 | 알려진 σ의 정규 모평균 구간; 임계값 2를 명시, 95% 구간과 구분 |
| contingency_table_calculation | applied | passed | 기존 구현 | 기대도수 계산만 수행; 작은 기대도수로 χ² 근사 검정을 실시하지 않음 |
| correlation_calculation | applied | passed | 기존 구현 | 세 쌍 자료, 두 표본분산 양수; 상관계수 계산 |
| counting_calculation | applied | passed | 기존 구현 | 비복원·순서 없는 2개 선택 |
| diagnostic_check | applied | passed | 기존 구현 | 원시 잔차만 계산; 전체 모형 진단을 대체하지 않음 |
| distribution_identification | applied | passed | 기존 구현 | 한 시행 지시변수의 Bernoulli 분포 식별 |
| effect_measure_interpretation | applied | passed | 기존 구현 | 양의 2×2 셀 빈도로 오즈비 계산; 인과효과를 주장하지 않음 |
| estimator_derivation | applied | passed | 기존 구현 | Uniform(0,θ)의 1차 적률 추정 결과; 서술 유도는 별도 검수 |
| f_test | applied | passed | 기존 구현 | F=MS_A/MS_E; 임계값 계산·유의성 결정은 제외 |
| formula_application | applied | passed | 기존 구현 | 대칭인 세 자료의 산술평균 |
| hypothesis_decision | applied | passed | 기존 구현 | 명시된 양측 기각역의 판정; p값 추정 없음 |
| method_selection | applied | passed | 기존 구현 | 순서 여부에 따른 비복원 순열 사용 판정 |
| model_interpretation | applied | passed | 기존 구현 | 기울기의 조건부 평균 변화 해석 |
| moment_calculation | applied | passed | 기존 구현 | Binomial(n,p)의 1차 적률 |
| post_hoc_selection | applied | passed | 기존 구현 | 제공된 p값의 Bonferroni 결정만 검사; p값 산출·전체 사후분석은 제외 |
| power_analysis | applied | passed | 기존 구현 | 알려진 σ의 정규 상측 검정; 검정력=1-Φ(2-δ) |
| probability_calculation | applied | passed | 기존 구현 | 상보적 두 사건 분할에서 Bayes 확률 |
| relationship_interpretation | applied | passed | 기존 구현 | 비영 아핀 변환의 상관계수 부호 |
| test_statistic_calculation | applied | passed | 기존 구현 | 알려진 σ의 모평균 Z 통계량 |
