# 함수별 TODO 위치

| ID | 파일 | 함수 | 할 일 |
|---|---|---|---|
| LA-D001 | `scripts/problems/common/generate_generation_rules.py` | `_fallback_parameter_spec()` | 신규 초안의 기본값과 기존 curated/reviewed 규칙 갱신을 구분한다. PARAMETER_LIBRARY 변경만으로 기존 규칙이 갱신된다고 처리하지 않는다. |
| LA-D002 | `scripts/problems/common/generate_generation_rules.py` | `_migrate_linear_algebra_runtime_requirements()` | 회귀·고유값 등의 generator/allowed_families 강제 대입이 다양성 정책을 되돌리는지 확인한다. 정책 적용 순서를 명시하고 차원·종속성·기존 제약을 보존한다. |
| LA-D003 | `scripts/problems/common/generate_generation_rules.py` | `_migrate_linear_algebra_curated_shapes()` | 유형별 차원 확장은 실제 정답 계산기·독립 검증기가 지원하는 범위만 허용한다. 서로 독립적으로 rows/cols를 확대해 정사각형·곱셈 차원 계약을 깨지 않는다. |
| LA-D004 | `scripts/problems/common/generate_generation_rules.py` | `_refresh_existing_rule()` | 새 linear_algebra_diversity_profiles.apply_policy() 연결 지점. 기존 보정 후 정책을 적용하되 기존 JSON을 참조하는 순환만 남기지 않는다. 명시적 opt-in, 불변 입력, 멱등성을 보장한다. 원본 검수 정보는 이력으로 보존하고 확장한 생성 범위의 검수 완료를 자동 주장하지 않는다. |
| LA-D005 | `scripts/problems/common/generate_generation_rules.py` | `build_rules()` | 정책 적용은 subject_id=linear_algebra로 한정한다. 기존 ID·공식·정답식·검증기·사용자 제약·검수 메모의 보존 여부를 비교 보고한다. 다른 네 과목은 의미상 동일해야 한다. |
| LA-D006 | `scripts/problems/common/generate_generation_rules.py` | `main()` | 재생성 가능한 Python 정책을 명시적으로 선택하는 CLI와 dry-run 차이를 제공한다. 후보는 별도 output-dir에 쓰며, 후보 카탈로그·manifest·정책 버전·seed·원본 hash를 기록한다. JSON 수동 편집을 요구하지 않는다. |
| LA-D007 | `scripts/problems/common/parameter_sampler.py` | `sample_parameters()` | 정책과 같은 seed로 결과가 재현되는지, 파라미터 순서·depends_on·derived 평가가 유지되는지 검증한다. 생성 실패/재시도 원인을 기록할 연결 지점을 마련한다. |
| LA-D008 | `scripts/problems/common/parameter_sampler.py` | `sample_parameter()` | 복소 내적 등 특수 분기에서 하드코딩한 후보와 분수 지원을 확인한다. 유형별 수학 조건을 지키면서 확대하고 모든 과목에 전역 적용하지 않는다. |
| LA-D009 | `scripts/problems/common/parameter_sampler.py` | `sample_scalar()` | 고정 분모 10 격자 외에 opt-in 유리수 정책을 구현한다. 기약분수 중복·분모 부호·0분모·exclude·step·choices를 처리하고, 분자/분모 균등과 값 균등의 차이를 명시한다. legacy 모드의 seed 결과는 보존한다. |
| LA-D010 | `scripts/problems/common/parameter_sampler.py` | `_element_spec()` | 행렬·벡터의 element_* 유리수 옵션과 가중치가 스칼라 설정으로 올바르게 전달되도록 한다. 외부 객체용 옵션을 스칼라에 잘못 적용하거나 기존 사용자 설정을 잃지 않는다. |
| LA-D011 | `scripts/problems/common/parameter_sampler.py` | `sample_vector()` | 실수 벡터/복소 벡터에서 계수 분포와 구조를 다양화한다. 차원, 0벡터 금지, 복소 내적 조건을 지킨다. |
| LA-D012 | `scripts/problems/common/parameter_sampler.py` | `sample_matrix()` | 숫자 범위뿐 아니라 성긴/조밀/비대각 구조를 유형별로 선택한다. SVD·대각화·양의 정부호 등의 전제조건은 생성 과정에서 보장한다. 특수 생성기 호출에 spec/정책을 전달하는 인터페이스도 기존 호출과 호환되게 확장한다. |
| LA-D013 | `scripts/problems/common/parameter_sampler.py` | `_small_svd_matrix()` | 대각/반대각 형태만 생성하는 제한을 확장한다. 합리적인 유리 직교변환과 분리된 특이값으로 조밀한 행렬도 생성한다. 최적 rank-1 근사의 비유일성·계산량·원소 범위를 확인한다. |
| LA-D014 | `scripts/problems/common/parameter_sampler.py` | `_rank_one_pseudoinverse_matrix()` | 한 열 또는 한 행만 0이 아닌 제한을 넘어 A=u*v.T 형태로 조밀한 rank-1 예제를 생성한다. u,v 비영 조건과 정확한 유리수 계산을 검증한다. |
| LA-D015 | `scripts/problems/common/parameter_sampler.py` | `_centered_pca_matrix()` | 축 방향/45도 방향 고정 조합을 확장한다. 표본 중심화, 열 차원, 유일한 최대 고유값 및 주성분 부호 동치를 유지한다. |
| LA-D016 | `scripts/problems/common/parameter_sampler.py` | `_defective_jordan_matrix()` | 표준 Jordan 블록 외에 가역변환 P*J*P.inv()로 다양한 표현을 만든다. 결함 행렬 조건과 기하적 중복도, 정확한 계수, 연산량을 확인한다. |
| LA-D017 | `scripts/problems/common/parameter_sampler.py` | `_easy_orthogonal_columns()` | 세 기본 조합의 부호·순열 반복을 확장한다. 정수/유리 직교 열벡터를 구성하고 full column rank·직교성·노름과 QR/Gram-Schmidt의 정답 난도 조건을 유지한다. |
| LA-D018 | `scripts/problems/common/parameter_sampler.py` | `_small_integer_spectrum_symmetric()` | 고정 2x2 대칭 블록·작은 정수 스펙트럼 제한을 opt-in 정책으로 확장한다. 유리 직교 유사변환으로 대칭성을 유지하고 고유값 간격·중복도·검증기 지원 차원을 관리한다. |
| LA-D019 | `scripts/problems/common/parameter_sampler.py` | `_coefficient_spec()` | 계수 옵션 전달 방식의 참고 지점. 선형대수는 주로 matrix/vector 원소를 사용하므로 이 함수만 바꾸면 해결된다고 가정하지 않는다. 미적분 등 다른 과목의 기본값은 보존한다. |
| LA-D020 | `scripts/problems/linear_algebra/activate_advanced_linear_algebra.py` | `upgrade()` | 현재 parameter_spec 전체 교체, constraints 초기화, status/notes 강제 설정이 검수 정보를 지울 수 있다. 최초 활성화와 다양성 갱신을 분리하고 기존 사용자 수정/검수 이력을 보존한다. ADVANCED 설정은 새 Python 정책과 중복 정의하지 않는다. |
| LA-D021 | `scripts/problems/linear_algebra/activate_advanced_linear_algebra.py` | `main()` | 이미 검수된 카탈로그에 활성화 스크립트를 재실행할 때 무엇이 바뀌는지 dry-run/백업/변경 보고를 제공한다. 신규 후보에 자동 승인 플래그를 부여하지 않는다. |
| LA-D022 | `scripts/problems/linear_algebra/migrate_linear_algebra_runtime_rules.py` | `repair_rule()` | QR·Gram-Schmidt 등의 고정 generator/shape 보정이 새 정책을 다시 제한하지 않도록 연결 순서를 정한다. 기존 정답식·검증기·사용자 Constraint는 보존하고 두 번 적용 결과가 같도록 한다. |
| LA-D023 | `scripts/problems/linear_algebra/limit_eigenvector_spectrum.py` | `patch_catalog()` | 기존 안전 모드의 작은 정수 스펙트럼 제한은 유지한다. 확장 정책에서는 새로운 generator를 충돌로 오판하거나 다시 고정하지 않도록 버전/모드에 따른 동작을 명시한다. |
| LA-D024 | `app/schemas/generation_rule.py` | `validate_ranges_and_derivation()` | 유리수 분자·분모 범위, 혼합 비율, 구조별 가중치를 ParameterSpec의 선택적 필드로 명시할지 결정한다. 현재 extra=allow만으로 잘못된 설정이 통과하지 않게 검증하고 기존 카탈로그와 하위 호환한다. |
| LA-D025 | `app/problems/template_builder.py` | `build_template()` | 새 파라미터 옵션이 Rule에서 Template로 손실 없이 전달되는지 확인한다. 기존 검수 정보는 보존하되 확장된 후보 생성 범위가 기존 reviewed/ready/publishable 판정을 무조건 상속하지 않도록 버전/검수 범위를 구분한다. 보고서 필드를 임의로 strict schema에 삽입하지 않는다. |
| LA-D026 | `scripts/problems/common/build_problem_templates.py` | `main()` | 원본 reviewed 카탈로그를 덮지 않고 후보 규칙을 읽어 별도 디렉터리에 템플릿을 재생성하는 경로를 제공한다. app의 registry가 전역 경로에 캐시하는 점을 확인하고 후보 정책이 실제 적용됐는지 manifest에 기록한다. |
| LA-D027 | `scripts/problems/common/problem_instance_generator.py` | `prepare_linear_algebra_context()` | 확장 입력의 symbol/derived 파라미터를 정확한 SymPy 수로 유지한다. 고유값·차원 등 의존 파라미터를 이전 고정 범위와 불일치하게 만들지 않는다. |
| LA-D028 | `scripts/problems/common/problem_instance_generator.py` | `_json_value()` | 유리수 입력/정답의 분자·분모가 float로 손실되지 않고 저장 후 독립 parse로 동일하게 복원되는지 왕복 테스트한다. |
| LA-D029 | `scripts/problems/common/problem_instance_generator.py` | `_answer_fraction_grade()` | 현재 최대 분수 부분 99 및 무리수/복소수 제한 때문에 생성 후 탈락하는 비율을 측정한다. 수학적 정당성 실패와 표시/난도 제한을 구분하며, 제한을 무작정 제거하지 않는다. 복소/근호 정답은 유형별 명시적 지원이 있는 경우에만 확장한다. |
| LA-D030 | `scripts/problems/common/problem_instance_generator.py` | `generate_problem_instance()` | 후보 정책별 재시도/제약 실패/정답 난도 탈락/시간 초과를 집계한다. 정책 혼합 후 최종 통과 표본의 분포가 한 구조로 수렴하는 편향을 측정한다. 검수 전 결과는 publishable=False로 유지한다. |
| LA-D031 | `scripts/problems/common/independent_instance_validator.py` | `parse()` | 정확한 기약분수·복소수·행렬 값의 저장 표현을 기존 안전 AST 파서로 처리하는지 확인한다. eval 또는 문자열 sympify로 우회하지 않는다. |
| LA-D032 | `scripts/problems/common/independent_instance_validator.py` | `math_check()` | 분수·조밀 행렬·유사변환 입력을 생성기의 helper를 호출하지 않고 재계산한다. 기저/고유벡터/QR/SVD/PCA의 비유일한 정답은 해당 수학 조건과 동치로 검사한다. |
| LA-D033 | `scripts/problems/common/independent_instance_validator.py` | `parameter_checks()` | 확장 정책의 범위·랭크·대칭·중심화·중복도·행렬 크기를 원본 문제 파라미터에서 확인한다. 생성 시 validation_trace나 정책 label만으로 통과시키지 않는다. |
| LA-D034 | `scripts/problems/common/independent_instance_validator.py` | `validate_payload()` | 기존 문장 계약은 그대로 두고 숫자·행렬 표현이 바뀐 문제를 검증한다. 문장 의미까지 바꾸는 확장은 별도 계약 작업으로 분리한다. 미지원 유형/조건은 unsupported로 집계하고 성공률 분모에서 숨기지 않는다. |
| LA-D035 | `scripts/problems/common/save_problem_previews.py` | `save_subject_previews()` | 6단원의 최신 후보 manifest를 실행 대상으로 삼고 오래된 ready/draft 사본을 섞지 않는다. 단원·유형·정책 버전·seed·시도 수를 기록하고 후보 실행은 검수용 옵션으로만 허용한다. |
| LA-D036 | `scripts/problems/common/save_problem_previews.py` | `main()` | 원본 템플릿 경로와 후보 재생성 템플릿 경로를 분리한다. 생성기에서 제외/부분 실패한 유형도 최종 검증 보고서에서 누락되지 않도록 전달한다. |
| LA-D037 | `scripts/problems/common/InstanceDB_MAKE/validate_stored_instances.py` | `validate_with_timeout()` | 확대된 유리수/행렬 구조에서도 제한 시간과 Windows spawn을 보장한다. timeout을 unsupported 또는 성공으로 숨기지 않는다. |
| LA-D038 | `scripts/problems/common/InstanceDB_MAKE/validate_stored_instances.py` | `main()` | 후보 Preview ZIP 전체에 독립 검증을 실행한다. 단원·유형별 passed/failed/unsupported/timeout 및 누락된 유형을 집계한다. 이번 워크플로에서는 DB --write를 사용하지 않고 별도 보고서에만 기록한다. |

신규 뼈대: LA-N01~N04(정책), LA-N05~N11(실행기), LA-T01~T06(인수 테스트).
