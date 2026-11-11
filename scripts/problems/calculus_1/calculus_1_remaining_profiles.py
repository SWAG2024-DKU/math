"""미적분 1의 나머지 유형: 명시한 작은 함수족 안에서만 생성한다.

레지스트리는 문제 유형마다 질문과 계산을 명시한다. 이름 부분 일치로 추측하거나
사용자 문자열을 eval하지 않는다. 그래프는 방정식/구간 같은 객관식 표현으로,
증명/방법 문제는 질문에 명시한 판정 또는 설정 답만 검사한다. 서술 증명은 별도 검수다.
"""
from copy import deepcopy
import sympy as s

PROFILES = {}
CALCULATORS = {}
x, y = s.symbols('x y', real=True)


def integer(lo=1, hi=3, choices=None):
    result = {'type': 'integer', 'min': lo, 'max': hi}
    if choices is not None:
        result['choices'] = choices
    return result


BASE = {'a': integer(1,12), 'b': integer(1,6), 'c': integer(-6,6),
        'k': integer(-1, 1, [-1, 1]), 'N': integer(2, 4)}


def register(name, question, formula, answer_type, calculator, *, params=None, scope=''):
    if name in PROFILES:
        raise ValueError('중복 문제 유형: ' + name)
    parameters = deepcopy(BASE if params is None else params)
    references = ','.join(repr(key)+':'+key for key in parameters)
    references += ",'x':x,'y':y"
    PROFILES[name] = {
        'question': question, 'formula': formula, 'answer_type': answer_type,
        'expression': 'remaining_calculus_value({'+references+'},'+repr(name)+')',
        'validator': 'calculus_remaining_check', 'config': {'operation': name},
        'parameters': parameters, 'constraints': [],
        'symbols': {'x': {'role': 'independent_variable', 'assumptions': {'real': True}},
                    'y': {'role': 'unknown', 'assumptions': {'real': True}}},
        'scope': scope or '질문에 명시한 함수족과 구간의 최종 답만 검사; 서술 풀이/그림은 별도 검수',
    }
    CALCULATORS[name] = calculator


def reg(name, question, formula, kind, fn, **kw):
    register(name, question, formula, kind, fn, **kw)


def a(p): return s.Integer(p['a'])
def b(p): return s.Integer(p['b'])
def c(p): return s.Integer(p['c'])
def k(p): return s.Integer(p['k'])
def n(p): return int(p['N'])
def px(p): return p['x']
def py(p): return p['y']
def quadratic(p): return a(p)*(px(p)-c(p))**2+b(p)
def cubic(p): return a(p)*(px(p)-c(p))**3+b(p)
def line(p): return a(p)*px(p)+b(p)
def interval(lo, hi): return s.Interval(lo, hi)
def eq(p, rhs): return s.Eq(py(p),rhs,evaluate=False)

# 함수의 정의역, 그래프를 표현하는 식, 역함수와 합성.
reg('domain_range_identification','f(x)=arctan({{ a }}x)의 실수 정의역을 구하시오.',None,'interval',lambda p:s.S.Reals)
reg('vertical_line_test_check','관계 x=y^{{ a }} (a={{ a }})는 모든 실수 x에서 y=f(x)인 함수의 그래프인가? 참/거짓으로 답하시오.','function_graph','boolean',lambda p: int(a(p))%2==1)
reg('piecewise_evaluation','f(x)={{ a }}x (x<0), f(x)={{ b }}x+{{ c }} (x≥0)이다. f({{ k }})를 구하시오.','piecewise_example','scalar',lambda p: a(p)*k(p) if k(p)<0 else b(p)*k(p)+c(p))
reg('domain_segment_identification','f(x)={{ a }}x (x<{{ c }}), f(x)={{ b }}x (x≥{{ c }})이다. x={{ c }}+{{ k }}에는 몇 번째 식을 쓰는가? 1 또는 2로 답하시오.','piecewise_example','scalar',lambda p:s.Integer(1 if k(p)<0 else 2))
reg('monotonic_interval_identification','f(x)={{ a }}(x-{{ c }})²가 증가하는 최대 열린 구간을 구하시오.','increasing_condition','interval',lambda p:s.Interval.open(c(p),s.oo))
reg('function_family_classification','f(x)={{ a }}x^{{ b }}+{{ c }}를 다항함수 또는 유리함수(다항함수 제외)로 분류하시오.','polynomial_general','classification',lambda p:'다항함수')
reg('domain_by_family','유리함수 f(x)={{ a }}/(x-{{ c }})의 실수 정의역을 구하시오.','rational_function','interval',lambda p:s.Union(s.Interval.open(-s.oo,c(p)),s.Interval.open(c(p),s.oo)))
reg('transformation_identification','기본 그래프 y=x²를 오른쪽 {{ c }}만큼, 위쪽 {{ b }}만큼 옮겼다(음수 이동량은 반대 방향). 변환 후 y의 식을 구하시오.','horizontal_shift','expression',lambda p:(px(p)-c(p))**2+b(p))
reg('graph_sketch_rule','y={{ k }}x²의 그래프를 오른쪽 {{ c }}만큼 이동할 때, 스케치의 기준이 되는 y의 식을 구하시오.','reflection','expression',lambda p:k(p)*(px(p)-c(p))**2,scope='스케치를 나타내는 함수식만 검사; 실제 그림은 사람 검수')
reg('heaviside_modeling','x<{{ c }}일 때 0, x≥{{ c }}일 때 {{ a }}인 계단함수를 Piecewise 식으로 나타내시오.','heaviside_function','expression',lambda p:s.Piecewise((0,px(p)<c(p)),(a(p),True)))
reg('domain_of_combination','f(x)=sqrt(x-{{ c }}), g(x)=x-{{ c }}-{{ a }}이다. f/g의 실수 정의역을 구하시오.','quotient','interval',lambda p:s.Complement(interval(c(p),s.oo),s.FiniteSet(c(p)+a(p))))
reg('function_decomposition','h(x)=({{ a }}x+{{ b }})²를 f(u)=u²와 g(x)로 분해하시오. g(x)만 답하시오.','composition','expression',line)
reg('exponent_law_application','{{ a }}^(x+{{ b }}) / {{ a }}^x 를 간단히 하시오.','exponent_laws','expression',lambda p:a(p)**b(p))
reg('monotonicity_from_base','함수 f(x)=({{ a }}+1)^({{ k }}x)는 실수 전체에서 증가하는가? 참/거짓으로 답하시오.','exponential_function','boolean',lambda p:k(p)>0)
reg('graph_identification','f(x)=({{ a }}+1)^x의 그래프가 지나는 x=0에서의 y 좌표를 구하시오.','exponential_function','expression',lambda p:s.Integer(1),scope='지수 그래프의 절편 식별; 이미지 선택은 미지원')
reg('one_to_one_check','실수 전체에서 f(x)={{ a }}x^{{ b }}는 일대일 함수인가?','one_to_one_definition','boolean',lambda p:int(b(p))%2==1)
reg('inverse_function_derivation','실수 전체에서 f(x)={{ a }}x+{{ b }}이다. 역함수 f^(-1)(x)를 구하시오.','inverse_definition','expression',lambda p:(px(p)-b(p))/a(p))
reg('cancellation_verification','f(x)={{ a }}x+{{ b }}, g(x)=(x-{{ c }})/{{ a }}이다. f(g(x))=x가 모든 실수 x에서 성립하는가?','cancellation_equations','boolean',lambda p:b(p)==c(p))
reg('log_law_application','x>0일 때 log(x^{{ a }})+log(x^{{ b }})를 자연로그 하나로 합치시오.','log_laws','expression',lambda p:s.log(px(p)**(a(p)+b(p))))
reg('change_of_base','log_({{ a }}+1)((({{ a }}+1))^{{ b }}) 값을 구하시오.','change_of_base','scalar',b)
reg('natural_vs_common_log','log는 자연로그를 뜻한다. log(exp({{ a }})) / log(10^{{ b }})를 정확한 식으로 구하시오.','natural_log','expression',lambda p:a(p)/(b(p)*s.log(10)))
reg('inverse_trig_evaluation','주값 arctan({{ k }})를 사용하여 {{ a }}*arctan({{ k }})를 구하시오.','arctan','scalar',lambda p:a(p)*k(p)*s.pi/4)
reg('trig_domain_range_period_identification','함수 sin({{ a }}x)의 최소 양의 주기를 구하시오.','sin_cos_periodicity','scalar',lambda p:2*s.pi/a(p))
reg('reciprocal_trig_evaluation','csc(π/2+{{ c }}π)의 값을 구하시오.','reciprocal_trig_functions','scalar',lambda p:s.Integer((-1)**int(c(p))))

# 극한, 연속성과 정리의 가정. 무한 결과는 값 자체 대신 명시한 판정으로 답한다.
reg('limit_numeric_estimation','f(x)={{ a }}x+{{ b }}이다. x=1-1/{{ N }}와 x=1+1/{{ N }}의 함수값 평균을 극한 추정값으로 사용하시오.','limit_notation','scalar',lambda p:(line(p).subs(px(p),1-s.Rational(1,n(p)))+line(p).subs(px(p),1+s.Rational(1,n(p))))/2)
reg('infinite_limit_identification','f(x)=({{ k }})*{{ a }}/x²의 x→0 극한이 +∞인가? 참/거짓으로 답하시오.','infinite_limit','boolean',lambda p:k(p)>0)
reg('vertical_asymptote_calculation','f(x)={{ a }}/(x-{{ c }})의 수직점근선 x=d에서 d를 구하시오.','one_sided_infinite_limit','scalar',c)
reg('limit_law_precondition_check','x→0에서 f(x)={{ a }}x+1, g(x)=x+{{ c }}이다. 분모 극한이 0이 아닌 경우에 쓰는 몫의 극한 법칙을 바로 적용할 수 있는가?','product_quotient_law','boolean',lambda p:c(p)!=0)
reg('squeeze_theorem_application','x≠0에서 f(x)={{ a }}x² sin(1/x)이다. 조임정리로 x→0의 극한을 구하시오.','squeeze_theorem','scalar',lambda p:s.Integer(0))
reg('discontinuity_classification','x≠{{ c }}에서 f(x)=((x-{{ c }})²)/(x-{{ c }}), f({{ c }})={{ a }}이다. x={{ c }}의 불연속을 제거 가능 또는 점프 또는 무한으로 분류하시오.','continuity_definition','classification',lambda p:'제거 가능')
reg('continuity_algebra_application','f(x)=1/(x-{{ c }})+{{ a }}x는 x=0에서 연속인가?','continuous_algebra','boolean',lambda p:c(p)!=0)
reg('composition_continuity_check','h(x)=sqrt({{ a }}x+{{ c }})가 x=0의 열린 근방에서 실수 함수로 연속인가?','composition_continuity','boolean',lambda p:c(p)>0)
reg('ivt_condition_check','f(x)=x²-{{ a }}가 [0,{{ b }}]에서 연속이다. 끝점의 함수값만으로 중간값정리가 이 구간의 영점 존재를 보장하는가(끝점 영점 포함)?','ivt','boolean',lambda p:b(p)**2>=a(p))
reg('root_interval_location','f(x)=x³-{{ a }} (a={{ a }})의 영점이 존재하는 연속함수 구간 [0,3]를 답하시오. 끝점의 부호로 보장됨을 확인하시오.','ivt','interval',lambda p:interval(0,3),scope='주어진 부호 변화 구간을 확인하는 답; 최소 구간/유일근 증명은 묻지 않음')
reg('limit_at_infinity_calculation','x→+∞에서 ({{ a }}x²+{{ c }})/({{ b }}x²+1)의 극한을 구하시오.','rational_end_behavior','scalar',lambda p:a(p)/b(p))
reg('horizontal_asymptote_identification','f(x)=({{ a }}x+{{ c }})/({{ b }}x+1)의 수평점근선 y=L에서 L을 구하시오.','rational_end_behavior','scalar',lambda p:a(p)/b(p))
reg('rational_end_behavior_classification','f(x)=x^{{ a }}/(x^{{ b }}+1)의 x→+∞ 거동을 0 또는 1 또는 +∞로 분류하시오.','rational_end_behavior','classification',lambda p:'0' if a(p)<b(p) else ('1' if a(p)==b(p) else '+∞'))

# 미분/음함수/변화율. 증명 요구는 주어진 명제의 판정 답에 한정한다.
reg('derivative_from_definition','f(x)={{ a }}x²+{{ b }}x이다. 차분몫의 극한 정의로 f\'(x)를 구하시오.','derivative_function','expression',lambda p:s.diff(a(p)*px(p)**2+b(p)*px(p),px(p)))
reg('differentiability_continuity_reasoning','f(x)=|x-{{ c }}|는 x={{ c }}에서 연속이지만 미분 불가능하다는 명제는 참인가?','differentiability_implies_continuity','boolean',lambda p:True,scope='절댓값 반례의 명제 판정; 서술 논증은 검사하지 않음')
reg('tangent_normal_line_derivation','y={{ a }}x²+{{ b }}의 x=1에서 법선 방정식을 구하시오.','power_rule','equation',lambda p:eq(p,a(p)+b(p)-(px(p)-1)/(2*a(p))))
reg('horizontal_tangent_point_calculation','y={{ a }}(x-{{ c }})²+{{ b }}의 수평접선이 생기는 x 좌표들의 집합을 구하시오.','polynomial_derivative','set',lambda p:s.FiniteSet(c(p)))
reg('tangent_slope_interpretation','y=exp({{ a }}x)의 x=0에서 접선의 기울기를 구하시오.','natural_exponential_derivative','scalar',a)
reg('inner_outer_identification','h(x)=sin(({{ a }}x+{{ b }})²)에서 최외곽 함수를 sin(u)로 선택한다. 안쪽 함수 u(x)를 구하시오.','chain_rule','expression',lambda p:line(p)**2)
reg('implicit_differentiation','곡선 x²+{{ a }}y²={{ b }}에서 y≠0이다. dy/dx를 x,y로 나타내시오.','implicit_diff_general','expression',lambda p:-px(p)/(a(p)*py(p)))
reg('implicit_second_derivative','곡선 x²+{{ a }}y²={{ b }}에서 y≠0이다. d²y/dx²를 x,y로 나타내시오.','power_of_y_chain_rule','expression',lambda p:-b(p)/(a(p)**2*py(p)**3))
reg('tangent_line_implicit','곡선 x²+y²={{ a }}²+{{ b }}²의 점 ({{ a }},{{ b }})에서 접선 방정식을 구하시오.','implicit_diff_general','equation',lambda p:eq(p,b(p)-a(p)*(px(p)-a(p))/b(p)))
reg('inverse_trig_derivative_calculation','f(x)=arctan({{ a }}x)의 도함수를 구하시오.','arctan_arccot_derivative','expression',lambda p:s.diff(s.atan(a(p)*px(p)),px(p)))
reg('inverse_function_derivative_rule_application','f(x)={{ a }}x+{{ b }}의 역함수의 도함수를 구하시오.','inverse_function_derivative','expression',lambda p:s.Integer(1)/a(p))
reg('related_rates_equation_formulation','구의 현재 반지름은 {{ a }}이고 V(t)=4πr(t)³/3이다. 현재 dr/dt를 y로 놓고 dV/dt를 y의 식으로 나타내시오.','related_rates_sphere','expression',lambda p:4*s.pi*a(p)**2*py(p))
reg('related_rates_solving','구의 반지름이 {{ a }}이고 dr/dt=({{ k }})*{{ b }}일 때 dV/dt를 구하시오.','related_rates_sphere','scalar',lambda p:4*s.pi*a(p)**2*k(p)*b(p))
reg('error_propagation_estimation','f(x)=x², 측정값 x={{ a }}, dx=1/{{ N }}이다. 미분을 이용한 df의 추정값을 구하시오.','differential','expression',lambda p:2*a(p)/n(p))
reg('hyperbolic_identity_application','cosh²({{ a }}x)-sinh²({{ a }}x)를 간단히 하시오.','hyperbolic_identity','expression',lambda p:s.simplify(s.cosh(a(p)*px(p))**2-s.sinh(a(p)*px(p))**2))
reg('inverse_hyperbolic_derivative_calculation','f(x)=asinh({{ a }}x)의 도함수를 구하시오.','inverse_hyperbolic_derivatives','expression',lambda p:s.diff(s.asinh(a(p)*px(p)),px(p)))

# 극값/증감/오목성/최적화.
reg('critical_number_calculation','f(x)={{ a }}(x-{{ c }})²+{{ b }}의 임계수 집합을 구하시오.','critical_number_def','set',lambda p:s.FiniteSet(c(p)))
reg('extrema_classification','f(x)=({{ k }})*{{ a }}(x-{{ c }})²+{{ b }}의 x={{ c }}는 극대 또는 극소 중 무엇인가?','local_extrema_def','classification',lambda p:'극소' if k(p)>0 else '극대')
reg('evt_condition_check','f(x)=1/(x-{{ c }})에 대해 [-1,1]에서 최대·최소 정리를 적용할 연속성 가정을 만족하는가?','extreme_value_theorem','boolean',lambda p:abs(c(p))>1)
reg('closed_interval_extrema_calculation','f(x)={{ a }}x²+{{ b }}x+{{ c }}의 [0,1]에서 최댓값을 구하시오.','closed_interval_method_procedure','scalar',lambda p:a(p)+b(p)+c(p))
reg('rolle_condition_check','f(x)={{ a }}(x-{{ c }})²의 [0,2]에서 롤의 정리의 세 가정을 모두 만족하는가?','rolles_theorem','boolean',lambda p:c(p)==1)
reg('mvt_point_calculation','f(x)={{ a }}x²+{{ b }}의 [0,2]에서 평균값정리를 만족하는 c∈(0,2)를 구하시오.','mean_value_theorem','scalar',lambda p:s.Integer(1))
reg('mvt_bound_estimation','[0,1]에서 |f\'(x)|≤{{ a }}이다. 평균값정리로 얻는 |f(1)-f(0)|의 상한을 구하시오.','derivative_bound_estimate','scalar',a)
reg('increasing_decreasing_interval_identification','f(x)={{ a }}(x-{{ c }})²+{{ b }}가 감소하는 최대 열린 구간을 구하시오.','increasing_decreasing_test','interval',lambda p:s.Interval.open(-s.oo,c(p)))
reg('first_derivative_test_classification','f(x)=({{ k }})*{{ a }}(x-{{ c }})²의 x={{ c }}에서 일계도함수 판정 결과를 극대/극소로 답하시오.','first_derivative_test','classification',lambda p:'극소' if k(p)>0 else '극대')
reg('concavity_interval_identification','f(x)={{ a }}(x-{{ c }})³가 f\'\'(x)>0인 최대 열린 구간을 구하시오.','concavity_test','interval',lambda p:s.Interval.open(c(p),s.oo))
reg('inflection_point_calculation','f(x)={{ a }}(x-{{ c }})³+{{ b }}의 변곡점 x 좌표들의 집합을 구하시오.','concavity_test','set',lambda p:s.FiniteSet(c(p)))
reg('second_derivative_test_classification','f(x)=({{ k }})*{{ a }}(x-{{ c }})²+{{ b }}의 x={{ c }}에서 이계도함수 판정 결과를 극대/극소로 답하시오.','second_derivative_test','classification',lambda p:'극소' if k(p)>0 else '극대')
reg('curve_sketching','f(x)={{ a }}(x-{{ c }})³+{{ b }}의 그래프를 분석하시오. 스케치의 핵심인 아래로 오목한 구간(f\'\'<0)만 답하시오.','concavity_test','interval',lambda p:s.Interval.open(-s.oo,c(p)),scope='곡선 분석의 오목 구간 답만 검사; 완전한 그림/모든 특징은 사람 검수')
reg('indeterminate_form_classification','x→0에서 (exp({{ a }}x)-1)/sin({{ b }}x)의 부정형을 0 나누기 0 또는 무한대 나누기 무한대로 분류하시오.','lhopitals_rule','classification',lambda p:'0 나누기 0')
reg('growth_rate_comparison','x→+∞에서 x^{{ a }}/exp({{ b }}x)의 극한을 구하시오.','growth_rate_comparison','scalar',lambda p:s.Integer(0))
reg('optimization_formulation','둘레가 2*{{ a }}인 직사각형의 한 변을 x라 할 때, 넓이를 x의 함수로 세우시오(0<x<{{ a }}).','optimization_procedure','expression',lambda p:px(p)*(a(p)-px(p)))
reg('optimization_solving','두 변의 합이 {{ a }}인 직사각형의 넓이를 최대화하는 한 변의 길이를 구하시오.','optimization_procedure','scalar',lambda p:a(p)/2)
reg('economic_optimization','0≤q≤{{ a }}에서 이익 P(q)={{ a }}q-q²이다. 이익을 최대화하는 생산량 q를 구하시오.','economic_functions','scalar',lambda p:a(p)/2)
reg('motion_reconstruction','가속도 s\'\'(x)={{ a }}, s\'(0)={{ b }}, s(0)={{ c }}이다. 위치 함수 s(x)를 구하시오.','general_antiderivative','expression',lambda p:a(p)*px(p)**2/2+b(p)*px(p)+c(p))

# 리만합, 적분 성질, 기하/물리. 설정 문제는 적분의 피적분함수/경계를 명시한다.
reg('riemann_sum_calculation','[0,1]에서 f(x)={{ a }}x²를 {{ N }}등분한 오른쪽 끝점 리만합을 구하시오.','rectangle_approximation','scalar',lambda p:a(p)*sum(s.Rational(j,n(p))**2 for j in range(1,n(p)+1))/n(p))
reg('area_limit_estimation','[0,1]에서 f(x)={{ a }}x²의 오른쪽 끝점 리만합의 분할 수를 무한히 늘릴 때 넓이의 극한값을 구하시오.','area_as_limit','scalar',lambda p:a(p)/3)
reg('integrability_check','f(x)=1/(x-{{ c }})는 [-1,1]에서 유계인 보통의 리만 적분 가능한 함수인가?','integrability_theorem','boolean',lambda p:abs(c(p))>1)
reg('integral_property_application','∫₀¹ f={{ a }}, ∫₀¹ g={{ b }}이다. ∫₀¹ (2f-3g)를 구하시오.','integral_linearity','scalar',lambda p:2*a(p)-3*b(p))
reg('midpoint_rule_estimation','[0,1]에서 f(x)={{ a }}x²를 {{ N }}등분한 중점 공식 근사값을 구하시오.','midpoint_rule','scalar',lambda p:a(p)*sum(s.Rational(2*j-1,2*n(p))**2 for j in range(1,n(p)+1))/n(p))
reg('integral_inequality_proof','0≤x≤1에서 f(x)={{ a }}x, g(x)={{ b }}이다. f≤g의 점별 조건과 ∫f≤∫g가 모두 성립하는지 참/거짓으로 판정하시오. 서술 증명은 별도 제출이다.','integral_comparison','boolean',lambda p:a(p)<=b(p),scope='적분 비교의 전제 및 결론 판정만 자동 검사; 서술 증명의 정당성은 사람 검수')
reg('accumulation_function_derivative','F(x)=∫₀ˣ ({{ a }}t²+{{ b }})dt의 도함수를 구하시오.','ftc1','expression',lambda p:a(p)*px(p)**2+b(p))
reg('variable_bound_integral_derivative','F(x)=∫₀ˣ² ({{ a }}t+{{ b }})dt의 도함수를 구하시오.','ftc1_chain_rule_variant','expression',lambda p:2*px(p)*(a(p)*px(p)**2+b(p)))
reg('displacement_and_distance_calculation','0≤t≤2에서 속도 v(t)={{ a }}(t-1)이다. 변위가 아니라 총 이동 거리를 구하시오.','displacement_vs_distance','scalar',a)
reg('intersection_point_calculation','y={{ a }}x와 y={{ b }}의 교점 x 좌표를 구하시오.','area_between_curves_x','scalar',lambda p:b(p)/a(p))
reg('variable_choice_for_area','영역 0≤y≤{{ a }}, 0≤x≤y²를 y에 대해 적분할 때 넓이 적분의 피적분함수를 x를 적분변수 y의 자리표시자로 사용하여 답하시오.','area_between_curves_y','expression',lambda p:px(p)**2)
reg('cross_section_area_construction','x축에 수직인 단면이 한 변 {{ a }}x+{{ b }}인 정사각형이다. 단면 넓이 A(x)를 구하시오.','square_cross_section','expression',lambda p:line(p)**2)
reg('axis_distance_calculation','점 (x,y)에서 직선 x={{ c }}까지의 거리를 x의 식으로 구하시오.','axis_distance','expression',lambda p:s.Abs(px(p)-c(p)))
reg('cylindrical_shell_volume_calculation','0≤x≤1에서 y={{ a }}x 아래 영역을 y축 둘레로 회전한다. 원통껍질법으로 부피를 구하시오.','cylindrical_shell_y_axis','scalar',lambda p:2*s.pi*a(p)/3)
reg('shell_vs_disk_method_selection','0≤x≤1, 0≤y≤{{ a }}x인 영역을 y축 둘레로 회전한다. x에 대한 원통껍질법을 선택할 때 부피 적분의 피적분함수를 구하시오.','cylindrical_shell_y_axis','expression',lambda p:2*s.pi*a(p)*px(p)**2,scope='명시된 방법의 적분 설정; 자유로운 방법 선택/풀이 설명은 사람 검수')
reg('trig_integral_strategy_selection','∫sin(x)cos(x)^{{ a }} dx에 u=cos(x)를 선택했다. x 대신 u를 기호 x로 적을 때 변환된 피적분함수를 구하시오.','sin_cos_power_odd','expression',lambda p:-px(p)**a(p))
reg('trig_substitution_selection','sqrt({{ a }}²-x²)의 적분을 위해 x={{ a }}sin(u)를 선택했다. dx/du를 u 대신 기호 x로 답하시오.','trig_sub_table','expression',lambda p:a(p)*s.cos(px(p)))
reg('trig_substitution_integral_calculation','|x|<{{ a }}에서 ∫1/sqrt({{ a }}²-x²) dx의 원시함수 하나를 구하시오.','trig_sub_table','expression',lambda p:s.asin(px(p)/a(p)))
reg('partial_fraction_decomposition','1/(x(x+{{ a }}))의 부분분수 분해를 구하시오. x=0,-{{ a }}는 제외한다.','partial_fraction_case1','expression',lambda p:1/(a(p)*px(p))-1/(a(p)*(px(p)+a(p))))
reg('improper_integral_type_classification','∫₁^∞ x^(-{{ a }})dx의 이상적분 유형을 제1종 또는 제2종으로 분류하시오.','improper_type1','classification',lambda p:'제1종')
reg('improper_integral_evaluation','p={{ a }}+1일 때 ∫₁^∞ x^(-p)dx를 구하시오.','p_integral_test','scalar',lambda p:1/a(p))
reg('comparison_theorem_application','x≥1에서 f(x)=1/x^{{ a }}이다. ∫₁^∞ f가 수렴하는지 참/거짓으로 답하시오.','p_integral_test','boolean',lambda p:a(p)>1)
reg('arc_length_setup','곡선 y={{ a }}x, 0≤x≤{{ b }}의 호의 길이를 구할 때 적분할 피적분함수를 구하시오.','arc_length_formula','expression',lambda p:s.sqrt(1+a(p)**2))
reg('arc_length_calculation','곡선 y={{ a }}x, 0≤x≤{{ b }}의 호의 길이를 구하시오.','arc_length_formula','scalar',lambda p:b(p)*s.sqrt(1+a(p)**2))
reg('surface_area_setup','y={{ a }}x, 0≤x≤1을 x축 둘레로 회전한 곡면의 넓이 적분에서 피적분함수를 구하시오.','surface_area_x_axis','expression',lambda p:2*s.pi*a(p)*px(p)*s.sqrt(1+a(p)**2))
reg('surface_area_calculation','y={{ a }}x, 0≤x≤{{ b }}를 x축 둘레로 회전한 곡면의 넓이를 구하시오.','surface_area_x_axis','scalar',lambda p:s.pi*a(p)*b(p)**2*s.sqrt(1+a(p)**2))
reg('width_function_construction','꼭짓점 (0,0), 높이 {{ a }}, 윗변 너비 {{ b }}인 역삼각형 판의 높이 x(0≤x≤{{ a }})에서 너비 w(x)를 구하시오.','hydrostatic_force','expression',lambda p:b(p)*px(p)/a(p))
reg('hydrostatic_force_calculation','수면에서 깊이 0≤h≤{{ b }}에 너비 {{ a }}인 직사각형 판이 있다. 유체의 비중량을 1로 놓고 정수압 힘을 구하시오.','hydrostatic_force','scalar',lambda p:a(p)*b(p)**2/2)
reg('pappus_theorem_application','반지름 {{ a }}인 원판을 원판 중심에서 ({{ a }}+{{ b }})만큼 떨어진 같은 평면의 축 둘레로 회전한다. 부피를 구하시오.','torus_volume','scalar',lambda p:2*s.pi**2*a(p)**2*(a(p)+b(p)))
reg('pappus_applicability_check','반지름 {{ a }}인 원판의 중심과 회전축 사이 거리가 {{ b }}이다. 축이 원판과 만나지 않아 파푸스 부피 정리를 직접 적용할 수 있는가?','pappus_theorem','boolean',lambda p:b(p)>a(p))
reg('numeric_integration_from_data','시간 0,1,2의 농도 측정값이 각각 {{ a }},{{ b }},{{ a }}이다. 간격 1의 사다리꼴 공식으로 농도 적분을 근사하시오.','cardiac_output','numerical_approximation',lambda p:a(p)+b(p),scope='표본 사다리꼴 공식의 정확한 유리수 표현; 측정 오차는 별도')
reg('cardiac_output_calculation','주입량 A={{ a }}이고 시간 0,1,2의 농도는 {{ b }},{{ a }},{{ b }}이다. 사다리꼴 적분으로 A/∫농도 dt를 근사하시오. 단위는 일관된 단위계다.','cardiac_output','numerical_approximation',lambda p:a(p)/(a(p)+b(p)))

# 매개변수 곡선/극좌표/이차곡선: 변수 x는 아래 질문에서 t 또는 θ를 나타낸다.
reg('parametric_curve_sketching','곡선 X(t)=t, Y(t)={{ a }}t²+{{ b }}의 t를 제거하여 평면 그래프 방정식을 y,x로 나타내시오.','parametric_equations','equation',lambda p:eq(p,a(p)*px(p)**2+b(p)),scope='매개변수 스케치의 직교좌표 방정식; 진행 방향/그림은 별도 검수')
reg('parameter_elimination','X(t)={{ a }}t, Y(t)={{ b }}t+{{ c }}에서 t를 제거한 y,x 방정식을 구하시오.','parametric_equations','equation',lambda p:eq(p,b(p)*px(p)/a(p)+c(p)))
reg('parametric_tangent_slope_calculation','X(t)={{ a }}t, Y(t)={{ b }}t²이다. t={{ k }}에서 dY/dX를 구하시오.','parametric_tangent_slope','scalar',lambda p:2*b(p)*k(p)/a(p))
reg('horizontal_vertical_tangent_identification','X(t)=t², Y(t)={{ a }}t인 곡선의 수직접선이 생기는 t 값들의 집합을 구하시오.','parametric_tangent_slope','set',lambda p:s.FiniteSet(0))
reg('parametric_second_derivative_calculation','X(t)={{ a }}t, Y(t)={{ b }}t²의 d²Y/dX²를 구하시오.','parametric_second_derivative','scalar',lambda p:2*b(p)/a(p)**2)
reg('parametric_area_calculation','X(t)={{ a }}t, Y(t)={{ b }}t², 0≤t≤1에서 곡선과 X축 사이 넓이를 구하시오.','parametric_area','scalar',lambda p:a(p)*b(p)/3)
reg('parametric_arc_length_calculation','X(t)={{ a }}t, Y(t)={{ b }}t, 0≤t≤1의 곡선 길이를 구하시오.','parametric_arc_length','scalar',lambda p:s.sqrt(a(p)**2+b(p)**2))
reg('parametric_surface_area_calculation','X(t)={{ a }}t, Y(t)={{ b }}t, 0≤t≤1을 X축 둘레로 회전한 곡면 넓이를 구하시오.','parametric_surface_area','scalar',lambda p:s.pi*b(p)*s.sqrt(a(p)**2+b(p)**2))
reg('polar_cartesian_conversion','극좌표 (r,θ)=({{ a }},{{ c }}π/2)의 직교좌표 중 x 좌표를 구하시오.','polar_to_cartesian','expression',lambda p:a(p)*s.cos(c(p)*s.pi/2))
reg('polar_symmetry_classification','극좌표 곡선 r={{ a }}(1+{{ k }}cos(θ))는 극축(직교 x축)에 대칭인가?','common_polar_curves','boolean',lambda p:True)
reg('polar_curve_identification','극좌표 r={{ a }}의 곡선 종류를 원/직선/포물선 중에서 답하시오.','common_polar_curves','classification',lambda p:'원')
reg('polar_area_calculation','r={{ a }}, 0≤θ≤π/2인 부채꼴의 넓이를 구하시오.','sector_area','scalar',lambda p:s.pi*a(p)**2/4)
reg('polar_curve_intersection','r={{ a }}와 r=2*{{ a }}cos(θ)가 만나는 θ∈[0,π/2]를 구하시오.','polar_area_between_curves','scalar',lambda p:s.pi/3)
reg('area_between_polar_curves','{{ a }}≤r≤({{ a }}+{{ b }}), 0≤θ≤π/2인 극좌표 영역의 넓이를 구하시오.','polar_area_between_curves','scalar',lambda p:s.pi*((a(p)+b(p))**2-a(p)**2)/4)
reg('polar_arc_length_calculation','r={{ a }}, 0≤θ≤π/2인 극좌표 곡선의 길이를 구하시오.','polar_arc_length','scalar',lambda p:a(p)*s.pi/2)
reg('polar_tangent_slope_calculation','r={{ a }}인 극좌표 원의 θ=π/4에서 접선 기울기 dy/dx를 구하시오.','polar_tangent_slope','scalar',lambda p:s.Integer(-1))
reg('pole_tangent_calculation','r={{ a }}sin(θ)인 극좌표 곡선의 θ=0에서 극점을 지나는 접선 기울기를 구하시오.','polar_tangent_at_pole','scalar',lambda p:s.Integer(0))
reg('conic_type_classification','x²/{{ a }}²+{{ k }}y²/{{ b }}²=1의 이차곡선을 타원/쌍곡선 중에서 답하시오.','ellipse_standard_form','classification',lambda p:'타원' if k(p)>0 else '쌍곡선')
reg('conic_element_calculation','타원 x²/({{ a }}²+{{ b }}²)+y²/{{ b }}²=1의 초점과 중심 사이 거리 c를 구하시오.','ellipse_standard_form','expression',a)
reg('general_to_standard_form_conversion','x²-2*{{ c }}x+y²-2*{{ b }}y+{{ c }}²+{{ b }}²={{ a }}²의 표준형을 좌변=우변 방정식으로 구하시오.','shifted_conic','equation',lambda p:s.Eq((px(p)-c(p))**2+(py(p)-b(p))**2,a(p)**2,evaluate=False))

# 수열/급수. 수렴 판정법이 결론을 내리지 못하는 경우를 별도 값으로 반환한다.
reg('sequence_convergence_check','수열 a_n=({{ a }}/(({{ a }}+1)))^n이 수렴하는가?','geometric_sequence_limit','boolean',lambda p:True)
reg('sequence_limit_calculation','수열 a_n=({{ a }}n+{{ c }})/({{ b }}n+1)의 n→∞ 극한을 구하시오.','sequence_limit_laws','scalar',lambda p:a(p)/b(p))
reg('geometric_sequence_limit_classification','수열 a_n=(({{ k }})*{{ a }})^n의 극한 거동을 1/진동/발산(+∞)/발산(진동) 중에서 답하시오.','geometric_sequence_limit','classification',lambda p:('1' if a(p)==1 else '발산(+∞)') if k(p)>0 else ('진동' if a(p)==1 else '발산(진동)'))
reg('monotonicity_boundedness_classification','a_n={{ a }}-{{ b }}/n (n≥1)의 단조성과 유계성을 증가·유계 또는 감소·유계 중에서 답하시오.','bounded_sequence_def','classification',lambda p:'증가·유계')
reg('monotonic_theorem_application','a_n={{ a }}-{{ b }}/n (n≥1)에 단조·유계 수열 정리의 가정을 모두 적용할 수 있는가?','monotonic_sequence_theorem','boolean',lambda p:True)
reg('recursive_sequence_limit_calculation','u₁=0, u_(n+1)=(u_n+{{ a }})/2인 수열의 극한을 구하시오.','recursive_sequence_limit','scalar',a)
reg('divergence_test_application','급수 ∑( {{ a }}+1/n )에 일반항의 극한을 이용한 발산판정법으로 발산을 결론낼 수 있는가?','divergence_test','boolean',lambda p:True)
reg('telescoping_series_calculation','n=1부터 무한대까지 ∑{{ a }}/(n(n+1))의 합을 구하시오.','series_sum_def','scalar',a)
reg('integral_test_application','급수 ∑1/n^{{ a }} (n≥1)에 적분판정법을 적용한 수렴/발산 결과를 답하시오.','integral_test','classification',lambda p:'수렴' if a(p)>1 else '발산')
reg('p_series_classification','p={{ a }}일 때 p급수 ∑1/n^p (n≥1)의 수렴/발산을 답하시오.','p_series_test','classification',lambda p:'수렴' if a(p)>1 else '발산')
reg('remainder_estimation','급수 ∑1/n²를 n={{ N }}까지 합했다. 적분판정법으로 R_N≤∫_N^∞1/x² dx의 상한을 구하시오.','integral_test_remainder','numerical_approximation',lambda p:s.Rational(1,n(p)))
reg('direct_comparison_test_application','∑1/(n^{{ a }}+n), n≥1을 ∑1/n^{{ a }}와 직접 비교할 때, 수렴을 결론낼 수 있는가?','direct_comparison_test','boolean',lambda p:a(p)>1)
reg('limit_comparison_test_application','급수 ∑({{ a }}n+1)/n³를 ∑1/n²와 극한 비교하여 수렴/발산을 답하시오.','limit_comparison_test','classification',lambda p:'수렴')
reg('comparison_series_construction','1/(n²+{{ a }})≤1/n² (n≥1)이고 우변의 급수가 수렴한다. 이 비교 대상은 좌변 급수의 수렴 증명에 유효한가?','direct_comparison_test','boolean',lambda p:True)
reg('alternating_series_test_application','급수 ∑(-1)^(n-1)/n^{{ a }} (n≥1)는 교대급수 정리의 감소·0극한 조건을 만족하는가?','alternating_series_test','boolean',lambda p:True)
reg('alternating_series_error_estimation','교대급수 ∑(-1)^(n-1)/n을 n={{ N }}까지 합했다. 교대급수 오차정리의 상한을 구하시오.','alternating_series_error_bound','numerical_approximation',lambda p:s.Rational(1,n(p)+1))
reg('absolute_conditional_classification','급수 ∑(-1)^(n-1)/n^{{ a }} (n≥1)를 절대수렴/조건수렴/발산으로 분류하시오.','absolute_conditional_convergence_def','classification',lambda p:'조건수렴' if a(p)==1 else '절대수렴')
reg('ratio_test_application','급수 ∑({{ a }}/{{ b }})^n (n≥1)를 비율판정법으로 분류하시오: 수렴/발산/판정 불가.','ratio_test','classification',lambda p:'수렴' if a(p)<b(p) else ('발산' if a(p)>b(p) else '판정 불가'))
reg('root_test_application','급수 ∑({{ a }}/{{ b }})^n (n≥1)를 근판정법으로 분류하시오: 수렴/발산/판정 불가.','root_test','classification',lambda p:'수렴' if a(p)<b(p) else ('발산' if a(p)>b(p) else '판정 불가'))
reg('test_selection_reasoning','급수 ∑{{ a }}^n/n!에서 항의 비 a_(n+1)/a_n={{ a }}/(n+1)을 이용한다. 사용하는 판정법 이름을 비율판정법 또는 근판정법으로 답하시오.','ratio_test','classification',lambda p:'비율판정법',scope='주어진 항의 비에 맞는 판정법 식별; 선택 이유의 서술은 사람 검수')


# 작은 오차 상한 문제도 여러 seed에서 서로 다른 N을 만들 수 있게 한다.
for _name in ('remainder_estimation','alternating_series_error_estimation'):
    PROFILES[_name]['parameters']['N']=integer(2,15)


def checked_parameters(parameters, name):
    """등록된 작은 매개변수 범위를 벗어난 입력은 통과시키지 않는다."""
    if name not in PROFILES:
        raise ValueError('미등록 미적분 유형: '+str(name))
    for key, spec in PROFILES[name]['parameters'].items():
        value=parameters.get(key)
        if isinstance(value,bool) or not isinstance(value,(int,s.Integer)):
            raise ValueError('정수 매개변수 필요: '+key)
        if not spec['min']<=value<=spec['max'] or ('choices' in spec and value not in spec['choices']):
            raise ValueError('생성 계약의 범위를 벗어남: '+key)
    for key in ('x','y'):
        value=parameters.get(key)
        if not isinstance(value,s.Symbol) or value.is_real is not True:
            raise ValueError('실수 Symbol 필요: '+key)
    if px(parameters)==py(parameters):
        raise ValueError('x와 y는 다른 기호여야 합니다.')
    return parameters


def calculate(parameters, name):
    p=checked_parameters(parameters,name)
    answer=CALCULATORS[name](p)
    if isinstance(answer,s.Basic):
        if answer.has(s.Integral,s.Derivative,s.Sum,s.Limit,s.nan,s.zoo):
            raise ValueError('계산이 완료되지 않았습니다.')
        if not isinstance(answer,s.Set) and answer.has(s.oo,-s.oo):
            raise ValueError('무한 결과는 명시된 판정 유형으로만 답합니다.')
    return answer


def validate(answer, parameters, config):
    """원본 파라미터를 다시 계산하고 답 형식·집합 경계·방정식을 검사한다.

    문자열을 수식으로 평가하지 않는다. 무한 구간 끝점은 집합에서만 허용한다.
    부정적분은 상수 차이를 허용하고 원 함수 미분으로 검증한다.
    """
    from scripts.problems.common.math_validators import equal,boolean
    name=config.get('operation')
    expected=calculate(parameters,name)
    if isinstance(expected,(bool,s.logic.boolalg.BooleanAtom)):
        return boolean(answer)==bool(expected)
    if isinstance(expected,str):return isinstance(answer,str) and answer==expected
    if isinstance(expected,s.Set):
        if not isinstance(answer,s.Set) or answer.has(s.ConditionSet,s.nan,s.zoo):return False
        return s.SymmetricDifference(answer,expected)==s.EmptySet
    if isinstance(expected,s.Equality):
        if not isinstance(answer,s.Equality):return False
        # 방정식의 영점 집합을 보존하는 0이 아닌 상수배만 허용한다.
        target=s.expand(expected.lhs-expected.rhs);candidate=s.expand(answer.lhs-answer.rhs)
        if target==0:return candidate==0
        ratio=s.cancel(candidate/target)
        return ratio.is_number is True and ratio.is_finite is True and ratio!=0
    if not isinstance(answer,(s.Expr,int)) or isinstance(answer,bool):return False
    if name=='trig_substitution_integral_calculation':
        return equal(s.diff(answer,px(parameters)),1/s.sqrt(a(parameters)**2-px(parameters)**2))
    return equal(answer,expected,config)
