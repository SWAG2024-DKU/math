"""확률통계 1차 계약: 유형마다 지정한 대표 Concept만 실행한다.

23개 유형 전체에 대표 모델을 제공하지만 520개 Concept 전체 구현은 아니다.
선택지 번호/판정/최종 수치만 채점하며 서술 증명·일반 통계 분석은 별도이다.
"""
from copy import deepcopy
import sympy as s

MARKER = '[probability_statistics_representatives_v1]'
PROFILES = {}
CALCULATORS = {}


def integer(lo=1, hi=6, choices=None):
    result = {'type': 'integer', 'min': lo, 'max': hi}
    if choices is not None:
        result['choices'] = choices
    return result


def reg(name, concept, question, kind, fn, params, scope):
    if name in PROFILES:
        raise ValueError('중복 유형: ' + name)
    refs = ','.join(repr(key) + ':' + key for key in params)
    PROFILES[name] = {'concept_id': concept, 'question': question,
        'formula': concept + '.formula_01', 'answer_type': kind,
        'expression': 'probability_statistics_value({' + refs + '},' + repr(name) + ')',
        'validator': 'probability_statistics_check', 'config': {'operation': name},
        'parameters': deepcopy(params), 'symbols': {}, 'constraints': [], 'scope': scope}
    CALCULATORS[name] = fn


def I(p, key):
    return s.Integer(p[key])


def correlation(p):
    xx = [s.Integer(0), s.Integer(1), s.Integer(2)]
    yy = [I(p,'a'), I(p,'a') + I(p,'b'), I(p,'a') + 2*I(p,'b') + I(p,'c')]
    xm, ym = sum(xx)/3, sum(yy)/3
    xy = sum((u-xm)*(v-ym) for u,v in zip(xx,yy))
    return xy/s.sqrt(sum((u-xm)**2 for u in xx)*sum((v-ym)**2 for v in yy))


reg('anova_table_completion','ps.anova.oneway_sums_of_squares_and_df.f01',
    '일원 ANOVA 표의 집단간 제곱합 SS_A를 채우시오. 세 집단의 표본크기는 각각 {{ b }}이고 표본평균은 0, {{ a }}, -{{ a }}이다.',
    'scalar',lambda p:2*I(p,'b')*I(p,'a')**2,{'a':integer(1,8),'b':integer(2,6)},'균형 3집단의 집단간 제곱합 한 셀')
reg('assumption_check','ps.descriptive_statistics.sample_variance_standard_deviation.f01',
    '자료 개수 n={{ n }}일 때 분모 n-1을 쓰는 불편 표본분산을 정의할 수 있는가? 각 관측값은 유한한 실수이다.',
    'boolean',lambda p:I(p,'n')>=2,{'n':integer(1,15)},'표본분산 정의에 필요한 n≥2 판정')
reg('coefficient_estimation','ps.simple_linear_regression.least_squares.f01',
    '절편을 포함한 단순 OLS에서 세 자료 (0, {{ a-b }}), (1, {{ a }}), (2, {{ a+b }})의 기울기 추정값을 구하시오.',
    'scalar',lambda p:I(p,'b'),{'a':integer(-5,5),'b':integer(-5,5)},'등간격 x와 정확한 직선 자료의 OLS 기울기')
reg('concept_identification','ps.foundations.observational_experimental_studies.f01',
    '{{ n }}명을 연구한다. mode={{ mode }}이다(1: 연구자가 처치를 무작위 배정, 2: 기존 처치 여부를 관찰). 연구 종류의 번호를 답하시오: 1=실험연구, 2=관측연구.',
    'single_choice',lambda p:I(p,'mode'),{'n':integer(10,60),'mode':integer(1,2)},'무작위 처치 배정 여부로 실험/관측 연구 식별')
reg('confidence_interval','ps.estimation.mean_ci_known_sigma',
    '정규 모집단의 독립 동일분포 표본에서 표본평균={{ a }}, 알려진 모집단 표준편차={{ b }}, 표본크기={{ c*c }}이다. 임계값 z=2, 신뢰수준 2Φ(2)-1(약 95.45%)인 모평균 양측 신뢰구간을 구하시오.',
    'interval',lambda p:s.Interval(I(p,'a')-2*I(p,'b')/I(p,'c'),I(p,'a')+2*I(p,'b')/I(p,'c')),
    {'a':integer(1,8),'b':integer(1,4),'c':integer(1,5)},'알려진 σ의 정규 모평균 구간; 임계값 2를 명시, 95% 구간과 구분')
reg('contingency_table_calculation','ps.categorical_analysis.independence_homogeneity.f01',
    '2×2 빈도표 [[{{ a }},{{ b }}],[{{ c }},{{ d }}]]에서 독립성 귀무가설 아래 첫 행·첫 열 셀의 기대도수를 구하시오.',
    'scalar',lambda p:(I(p,'a')+I(p,'b'))*(I(p,'a')+I(p,'c'))/sum(I(p,q) for q in 'abcd'),
    {q:integer(1,6) for q in 'abcd'},'기대도수 계산만 수행; 작은 기대도수로 χ² 근사 검정을 실시하지 않음')
reg('correlation_calculation','ps.correlation.sample_pearson_correlation',
    '짝지어진 자료 x=(0,1,2), y=({{ a }},{{ a+b }},{{ a+2*b+c }})의 표본 Pearson 상관계수를 구하시오.',
    'scalar',correlation,{'a':integer(-4,4),'b':integer(-3,3,[-3,-2,-1,1,2,3]),'c':integer(1,4)},'세 쌍 자료, 두 표본분산 양수; 상관계수 계산')
reg('counting_calculation','ps.counting.ordinary_combination.f01',
    '서로 다른 {{ n }}개 중 순서 없이 2개를 고르는 방법의 수를 구하시오.',
    'scalar',lambda p:s.binomial(I(p,'n'),2),{'n':integer(4,18)},'비복원·순서 없는 2개 선택')
reg('diagnostic_check','ps.simple_linear_regression.raw_residual',
    '회귀 진단에서 관측값 y={{ a }}, 예측값 yhat={{ b+c }}일 때 원시 잔차 e=y-yhat을 구하시오.',
    'scalar',lambda p:I(p,'a')-I(p,'b')-I(p,'c'),{'a':integer(-6,6),'b':integer(-4,4),'c':integer(1,4)},'원시 잔차만 계산; 전체 모형 진단을 대체하지 않음')
reg('distribution_identification','ps.discrete_distributions.bernoulli.f01',
    '독립 시행 {{ n }}회를 계획한다. 한 시행의 성공확률은 {{ a }}/10이고 X는 그 한 시행의 성공 지시변수이다. X의 분포 번호를 답하시오: 1=Bernoulli, 2=Poisson, 3=정규분포.',
    'single_choice',lambda p:s.Integer(1),{'n':integer(2,20),'a':integer(1,9)},'한 시행 지시변수의 Bernoulli 분포 식별')
reg('effect_measure_interpretation','ps.categorical_analysis.odds_ratio_2x2',
    '노출군의 사건/비사건 수가 {{ a }}/{{ b }}, 비노출군이 {{ c }}/{{ d }}일 때 노출군 대비 비노출군을 분모로 하는 오즈비를 구하시오.',
    'scalar',lambda p:I(p,'a')*I(p,'d')/(I(p,'b')*I(p,'c')),
    {q:integer(1,8) for q in 'abcd'},'양의 2×2 셀 빈도로 오즈비 계산; 인과효과를 주장하지 않음')
reg('estimator_derivation','ps.estimation.method_of_moments',
    'X는 Uniform(0,θ), θ>0이고 표본평균은 {{ a }}/{{ b }}이다. E[X]=θ/2에 기반한 적률법 θ 추정값을 구하시오.',
    'scalar',lambda p:2*I(p,'a')/I(p,'b'),{'a':integer(1,8),'b':integer(1,6)},'Uniform(0,θ)의 1차 적률 추정 결과; 서술 유도는 별도 검수')
reg('f_test','ps.anova.oneway_exact_f_reference',
    '독립·정규·등분산 오차를 가정한 일원 ANOVA에서 집단 수={{ k }}, 총 표본수={{ k*n }}, 집단간 평균제곱={{ a }}, 오차 평균제곱={{ b }}이다. 검정통계량 F를 구하시오.',
    'scalar',lambda p:I(p,'a')/I(p,'b'),{'a':integer(1,8),'b':integer(1,6),'k':integer(2,4),'n':integer(2,6)},'F=MS_A/MS_E; 임계값 계산·유의성 결정은 제외')
reg('formula_application','ps.descriptive_statistics.central_tendency.f01',
    '자료 {{ a-b }}, {{ a }}, {{ a+b }}의 산술평균을 구하시오.',
    'scalar',lambda p:I(p,'a'),{'a':integer(-6,6),'b':integer(1,8)},'대칭인 세 자료의 산술평균')
reg('hypothesis_decision','ps.hypothesis_testing.one_sample_z_mean_exact',
    '정규 iid 표본의 알려진 σ 모평균 양측 Z 검정이다. H0: μ={{ a }}, σ={{ b }}, n={{ c*c }}, 표본평균={{ a+d*b/c }}이다. 기각 규칙 |Z|≥2에 따라 H0를 기각하는가?',
    'boolean',lambda p:abs(I(p,'d'))>=2,{'a':integer(1,6),'b':integer(1,4),'c':integer(1,5),'d':integer(-3,3)},'명시된 양측 기각역의 판정; p값 추정 없음')
reg('method_selection','ps.counting.permutation_without_repetition',
    '서로 다른 {{ n }}명 중 비복원으로 {{ k }}명을 뽑는다. mode={{ mode }}(1: 서로 다른 직책을 부여해 순서 중요, 2: 직책 없이 팀 구성)이다. 조합이 아니라 순열 nPk를 써야 하는가?',
    'boolean',lambda p:I(p,'mode')==1,{'n':integer(6,18),'k':integer(2,5),'mode':integer(1,2)},'순서 여부에 따른 비복원 순열 사용 판정')
reg('model_interpretation','ps.simple_linear_regression.regression_model.f01',
    '조건부 평균 모형 E[Y|x]={{ a }}+({{ b }})x에서 x가 {{ c }}만큼 증가할 때 조건부 평균의 변화량을 구하시오. 인과효과는 가정하지 않는다.',
    'scalar',lambda p:I(p,'b')*I(p,'c'),{'a':integer(-5,5),'b':integer(-4,4),'c':integer(1,6)},'기울기의 조건부 평균 변화 해석')
reg('moment_calculation','ps.discrete_distributions.binomial.f02',
    '서로 독립인 {{ n }}번 Bernoulli 시행의 성공확률은 {{ a }}/5이다. 성공 횟수 X의 기댓값을 구하시오.',
    'scalar',lambda p:I(p,'n')*I(p,'a')/5,{'n':integer(2,12),'a':integer(1,4)},'Binomial(n,p)의 1차 적률')
reg('post_hoc_selection','ps.anova.bonferroni_adjustment',
    '사전에 정한 {{ m }}개 가설을 가족별 유의수준 1/20으로 Bonferroni 보정한다. 한 비교의 p값은 {{ a }}/100이다. p≤(1/20)/m 규칙으로 이 비교를 유의한 것으로 선택하는가?',
    'boolean',lambda p:s.Rational(int(p['a']),100)<=s.Rational(1,20*int(p['m'])),
    {'m':integer(2,10),'a':integer(1,8)},'제공된 p값의 Bonferroni 결정만 검사; p값 산출·전체 사후분석은 제외')
reg('power_analysis','ps.hypothesis_testing.one_sample_z_mean_exact',
    '정규 iid 표본에서 알려진 σ={{ b }}, n={{ c*c }}, H0: μ={{ a }}인 상측 검정이다. 표본평균>{{ a+2*b/c }}이면 기각한다. 참평균 μ1={{ a+d*b/c }}에서 검정력을 Φ 또는 erf로 나타내시오.',
    'scalar',lambda p:s.erfc((2-I(p,'d'))/s.sqrt(2))/2,
    {'a':integer(1,6),'b':integer(1,4),'c':integer(1,5),'d':integer(-3,3)},'알려진 σ의 정규 상측 검정; 검정력=1-Φ(2-δ)')
reg('probability_calculation','ps.conditional_independence.bayes_theorem',
    'P(A)=P(Aᶜ)=1/2, P(B|A)={{ a }}/10, P(B|Aᶜ)={{ b }}/10이다. P(A|B)를 구하시오.',
    'scalar',lambda p:I(p,'a')/(I(p,'a')+I(p,'b')),{'a':integer(1,9),'b':integer(1,9)},'상보적 두 사건 분할에서 Bayes 확률')
reg('relationship_interpretation','ps.correlation.pearson_affine_transformation',
    'Var(X),Var(Y)>0이고 Corr(X,Y)={{ a }}/10이다. U=({{ b }})X+{{ d }}, V=({{ c }})Y이면 Corr(U,V)를 구하시오.',
    'scalar',lambda p:s.sign(I(p,'b')*I(p,'c'))*I(p,'a')/10,
    {'a':integer(1,9),'b':integer(-3,3,[-3,-2,-1,1,2,3]),'c':integer(-3,3,[-3,-2,-1,1,2,3]),'d':integer(-3,3)},'비영 아핀 변환의 상관계수 부호')
reg('test_statistic_calculation','ps.hypothesis_testing.one_sample_z_mean_statistic',
    '정규 iid 표본에서 H0: μ={{ a }}, 알려진 σ={{ b }}, n={{ c*c }}, 표본평균={{ a+d*b/c }}이다. Z=(표본평균-μ0)/(σ/√n)를 구하시오.',
    'scalar',lambda p:I(p,'d'),{'a':integer(1,6),'b':integer(1,4),'c':integer(1,5),'d':integer(-3,3)},'알려진 σ의 모평균 Z 통계량')


def is_supported_pair(concept_id, problem_type):
    profile = PROFILES.get(problem_type)
    return profile is not None and profile['concept_id'] == concept_id


def checked_parameters(parameters, operation):
    if operation not in PROFILES:
        raise ValueError('미구현 확률통계 유형: ' + str(operation))
    if not isinstance(parameters, dict):
        raise ValueError('매개변수 객체가 필요합니다.')
    for key, spec in PROFILES[operation]['parameters'].items():
        value = parameters.get(key)
        if isinstance(value,bool) or not isinstance(value,(int,s.Integer)):
            raise ValueError('정수 매개변수 필요: ' + key)
        if not spec['min'] <= value <= spec['max']:
            raise ValueError('매개변수 범위 위반: ' + key)
        if 'choices' in spec and value not in spec['choices']:
            raise ValueError('매개변수 선택값 위반: ' + key)
    return parameters


def calculate(parameters, operation):
    p = checked_parameters(parameters,operation)
    result = CALCULATORS[operation](p)
    if isinstance(result,s.Basic) and result.has(s.nan,s.zoo,s.Integral,s.Derivative,s.Sum):
        raise ValueError('유한한 계산 완료 정답이 필요합니다.')
    if isinstance(result,s.Expr) and (result.free_symbols or result.is_finite is not True):
        raise ValueError('유한한 숫자 정답이 필요합니다.')
    return result


def validate(answer, parameters, config):
    from scripts.problems.common.math_validators import equal
    operation = config.get('operation')
    expected = calculate(parameters,operation)
    if isinstance(expected,(bool,s.logic.boolalg.BooleanAtom)):
        # 0/1 숫자는 판정 답으로 허용하지 않는다.
        return isinstance(answer,(bool,s.logic.boolalg.BooleanAtom)) and bool(answer)==bool(expected)
    if isinstance(expected,s.Interval):
        return isinstance(answer,s.Interval) and answer==expected
    if isinstance(answer,bool) or not isinstance(answer,(int,float,s.Expr)):
        return False
    value = s.sympify(answer)
    if value.free_symbols or value.is_finite is not True or value.is_real is not True:
        return False
    if PROFILES[operation]['answer_type']=='single_choice' and value.is_integer is not True:
        return False
    return equal(value,expected,config)
