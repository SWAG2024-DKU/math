"""미적분 2의 명시적인 제한 함수족과 정답 계약.

그림/서술 증명/선택한 풀이 방법 자체는 검사하지 않는다. 질문에 지정한 식,
방정식, 벡터, 수치, 판정 답을 검증한다. 사용자 문자열은 실행하지 않는다.
"""
from copy import deepcopy
import math
import sympy as s
PROFILES={}
CALCULATORS={}


def integer(lo=1,hi=12,choices=None):
    result={'type':'integer','min':lo,'max':hi}
    if choices is not None:result['choices']=choices
    return result


BASE={'a':integer(),'b':integer(1,6),'c':integer(1,4),'d':integer(-2,2),
      'k':integer(-1,1,[-1,1]),'N':integer(2,4)}
SYMBOLS={name:{'role':'independent_variable' if name in ('x','t') else ('constant' if name in ('C1','C2') else 'unknown'),
               'assumptions':{'real':True}} for name in ('x','y','z','t','C1','C2')}


def reg(name,question,formula,kind,fn,*,params=None,scope=''):
    if name in PROFILES:raise ValueError('중복 유형: '+name)
    pars=deepcopy(BASE if params is None else params)
    references=','.join(repr(key)+':'+key for key in [*pars,*SYMBOLS])
    PROFILES[name]={'question':question,'formula':formula,'answer_type':kind,
        'expression':'calculus_2_value({'+references+'},'+repr(name)+')',
        'validator':'calculus_2_check','config':{'operation':name},
        'parameters':pars,'constraints':[],'symbols':deepcopy(SYMBOLS),
        'scope':scope or '질문에 명시한 모델/구간의 최종 답만 검사; 자유로운 그림과 서술 풀이는 별도 검수'}
    CALCULATORS[name]=fn


def a(p):return s.Integer(p['a'])
def b(p):return s.Integer(p['b'])
def c(p):return s.Integer(p['c'])
def d(p):return s.Integer(p['d'])
def k(p):return s.Integer(p['k'])
def n(p):return int(p['N'])
def x(p):return p['x']
def y(p):return p['y']
def z(p):return p['z']
def t(p):return p['t']
def V(*items):return s.Matrix(items)
def A(p):return V(a(p),b(p),c(p))
def B(p):return V(b(p),-a(p),k(p))
def norm(v):return s.sqrt(v.dot(v))
def curve(p):return V(a(p)*t(p),b(p)*t(p)**2,c(p)*t(p)**3)
def linecurve(p):return V(a(p)*t(p),b(p)*t(p),c(p)*t(p))
def expr2(p):return a(p)*x(p)**2+b(p)*x(p)*y(p)+c(p)*y(p)**2

def exp_poly(p):return sum(a(p)**j*x(p)**j/s.factorial(j) for j in range(n(p)+1))
def ode_general(p):return p['C1']*s.exp(a(p)*x(p))+p['C2']*s.exp(-b(p)*x(p))
def ivp(p):return (d(p)+b(p)*c(p))*s.exp(a(p)*x(p))/(a(p)+b(p))+(a(p)*c(p)-d(p))*s.exp(-b(p)*x(p))/(a(p)+b(p))
def linear_ode(p,f):return s.diff(f,x(p),2)+(b(p)-a(p))*s.diff(f,x(p))-a(p)*b(p)*f

def line_equations(p,start,direction):
    return s.Tuple(*(s.Eq(coord,origin+t(p)*delta,evaluate=False)
        for coord,origin,delta in zip((x(p),y(p),z(p)),start,direction)))

# 급수: 무한급수 전체를 요구하는 대신 질문에서 계수/부분합/닫힌 합을 명시한다.
reg('common_series_recall','exp({{ a }}x)의 Maclaurin 전개를 x^{{ N }} 항까지 쓰시오.','exp_maclaurin','expression',exp_poly)
reg('series_convergence_interval_identification','ln(1+{{ a }}x)의 급수 ∑(-1)^(n+1)({{ a }}x)^n/n (n≥1)의 수렴 구간을 구하시오.','ln_maclaurin','interval',lambda p:s.Interval(-1/a(p),1/a(p),left_open=True))
reg('geometric_power_series_representation','|{{ a }}x|<1에서 ∑({{ a }}x)^n (n=0부터 무한대)의 합을 닫힌 함수로 나타내시오.','geometric_series_as_power_series','expression',lambda p:1/(1-a(p)*x(p)))
reg('power_series_substitution','1/(1-{{ a }}x²)의 거듭제곱급수에서 x^(2{{ N }}) 항까지의 부분합을 쓰시오. |{{ a }}x²|<1이다.','power_series_substitution','expression',lambda p:sum(a(p)**j*x(p)**(2*j) for j in range(n(p)+1)))
reg('term_by_term_differentiation','∑({{ a }}x)^n (n≥0)의 수렴 구간 안에서 항별 미분한 급수의 닫힌 합을 구하시오.','term_by_term_differentiation','expression',lambda p:a(p)/(1-a(p)*x(p))**2)
reg('term_by_term_integration','∑({{ a }}x)^n (n≥0)을 0부터 x까지 항별 적분한 급수의 닫힌 합을 구하시오. |{{ a }}x|<1이다.','term_by_term_integration','expression',lambda p:-s.log(1-a(p)*x(p))/a(p))
reg('radius_of_convergence_calculation','거듭제곱급수 ∑({{ a }}x)^n (n≥0)의 수렴 반지름을 구하시오.','radius_of_convergence_ratio','scalar',lambda p:1/a(p))
reg('interval_of_convergence_determination','급수 ∑({{ a }}x)^n/n (n≥1)의 수렴 구간을 끝점 포함 여부까지 구하시오.','radius_of_convergence_ratio','interval',lambda p:s.Interval(-1/a(p),1/a(p),right_open=True))
reg('endpoint_convergence_check','급수 ∑({{ a }}x)^n/n² (n≥1)의 수렴 구간을 끝점 포함 여부까지 구하시오.','power_series_def','interval',lambda p:s.Interval(-1/a(p),1/a(p)))
reg('power_series_combination','F=∑x^n, G=∑({{ a }}x)^n (n≥0)일 때 {{ b }}F+G의 x^{{ N }} 계수를 구하시오.','power_series_sum_diff','scalar',lambda p:b(p)+a(p)**n(p))
reg('coefficient_determination','∑({{ a }}x)^n (n≥0)의 x^{{ N }} 계수를 구하시오.','coefficient_uniqueness','scalar',lambda p:a(p)**n(p))
reg('cauchy_product_calculation','∑x^n과 ∑({{ a }}x)^n (각 n≥0)의 Cauchy 곱에서 x^{{ N }} 계수를 구하시오.','cauchy_product','scalar',lambda p:sum(a(p)**j for j in range(n(p)+1)))
reg('taylor_coefficient_extraction','exp({{ a }}x)의 x=0 Taylor 전개에서 x^{{ N }} 계수를 구하시오.','taylor_coefficient','expression',lambda p:a(p)**n(p)/s.factorial(n(p)))
reg('taylor_polynomial_construction','exp({{ a }}x)의 x=0에서 {{ N }}차 Taylor 다항식을 구하시오.','taylor_polynomial','expression',exp_poly)
reg('taylor_series_derivation','exp({{ a }}x)의 Maclaurin 급수를 유도하시오. 자동 채점 답은 0차부터 {{ N }}차까지의 다항식이다.','maclaurin_series','expression',exp_poly,scope='유도 결과의 유한 부분합만 검사; 무한 전개/서술 유도는 사람 검수')
reg('binomial_series_expansion','(1+x)^{{ a }}를 이항급수로 전개하여 x^{{ N }} 이하 항만 쓰시오.','binomial_series','expression',lambda p:sum(s.binomial(a(p),j)*x(p)**j for j in range(n(p)+1)))
reg('series_based_integration','exp({{ a }}x)의 {{ N }}차 Maclaurin 다항식을 0부터 x까지 적분하시오.','series_integration_example','expression',lambda p:s.integrate(exp_poly(p),(x(p),0,x(p))))
reg('series_based_limit_evaluation','이항급수 전개를 이용하여 x→0에서 ((1+x)^{{ a }}-1-{{ a }}x)/x²의 극한을 구하시오.','binomial_series','scalar',lambda p:a(p)*(a(p)-1)/2)
reg('taylor_error_estimation','[-1,1]에서 |f^({{ N+1 }})(x)|≤{{ a }}이다. 0 중심 {{ N }}차 Taylor 다항식으로 f(1)을 근사할 때 Lagrange 나머지 상한을 구하시오.','lagrange_remainder','numerical_approximation',lambda p:a(p)/s.factorial(n(p)+1))
reg('required_degree_determination','f(x)=1/(1-x)의 0 중심 Taylor 다항식으로 f(1/2)를 근사한다. 정확한 나머지 2^(-m)≤1/(10*{{ a }})를 만족하는 최소 차수 m을 구하시오.','taylor_inequality','scalar',lambda p:s.Integer((10*int(a(p))-1).bit_length()))

# 평면 매개변수/회전체/극좌표.
reg('line_segment_parametrization','A=({{ a }},0), B=(0,{{ b }})를 잇는 선분의 매개화 x=a(1-t), y=bt, 0≤t≤1을 방정식 쌍으로 쓰시오(a={{ a }}, b={{ b }}).','segment_parametrization','equation',lambda p:s.Tuple(s.Eq(x(p),a(p)*(1-t(p)),evaluate=False),s.Eq(y(p),b(p)*t(p),evaluate=False)))
reg('parameter_elimination','X(t)={{ a }}t, Y(t)={{ b }}t²에서 t를 제거하여 y,x 방정식을 구하시오.','parameter_elimination_example','equation',lambda p:s.Eq(y(p),b(p)*x(p)**2/a(p)**2,evaluate=False))
reg('parametric_tangent_line_equation','X(t)={{ a }}t, Y(t)={{ b }}t²의 t=1에서 접선 방정식을 구하시오.','parametric_tangent_line_equation','equation',lambda p:s.Eq(y(p),b(p)+2*b(p)*(x(p)-a(p))/a(p),evaluate=False))
reg('parametric_concavity_classification','X(t)={{ a }}t, Y(t)=({{ k }})*{{ b }}t²인 곡선을 위로 오목/아래로 오목으로 분류하시오.','parametric_concavity','classification',lambda p:'위로 오목' if k(p)>0 else '아래로 오목')
reg('surface_area_of_revolution_about_x_axis','y={{ a }}x, 0≤x≤{{ b }}를 x축 둘레로 회전한 곡면의 넓이를 구하시오.','surface_area_revolution_x_axis','scalar',lambda p:s.pi*a(p)*b(p)**2*s.sqrt(1+a(p)**2))
reg('surface_area_of_revolution_about_y_axis','y={{ a }}x, 0≤x≤{{ b }}를 y축 둘레로 회전한 곡면의 넓이를 구하시오.','surface_area_revolution_y_axis','scalar',lambda p:s.pi*b(p)**2*s.sqrt(1+a(p)**2))
reg('polar_curve_identification','극좌표 r={{ a }}(1+cos θ)는 카디오이드/장미곡선 중 무엇인가?','cardioid_limacon','classification',lambda p:'카디오이드')
reg('polar_symmetry_test_application','r={{ a }}(1+({{ k }})*cos θ)는 극축에 대칭인가?','polar_symmetry_tests','boolean',lambda p:True)
reg('polar_to_cartesian_circle_conversion','극좌표 r=2*{{ a }}cos θ를 직교좌표 방정식으로 바꾸시오.','cardioid_limacon','equation',lambda p:s.Eq((x(p)-a(p))**2+y(p)**2,a(p)**2,evaluate=False))
reg('conic_polar_equation_construction','초점이 극점, 준선이 x={{ a }}, 이심률 e=1/{{ b }}인 이차곡선의 r(θ)를 구하시오. 방정식에서는 θ=t, r=z로 쓰시오.','conic_polar_equation','equation',lambda p:s.Eq(z(p),a(p)/(b(p)+s.cos(t(p))),evaluate=False))
reg('eccentricity_classification','이심률 e={{ a }}/{{ b }}인 이차곡선을 타원/포물선/쌍곡선으로 분류하시오.','eccentricity_classification','classification',lambda p:'타원' if a(p)<b(p) else ('포물선' if a(p)==b(p) else '쌍곡선'))
reg('discriminant_classification','이차곡선 {{ a }}x²+({{ k }})*{{ b }}y²=1을 타원/쌍곡선으로 분류하시오.','discriminant_classification','classification',lambda p:'타원' if k(p)>0 else '쌍곡선')

# 공간 벡터와 기하.
reg('vector_from_points_construction','P=({{ a }},{{ b }},{{ c }}), Q=({{ b }},{{ c }},{{ a }})이다. 벡터 PQ를 구하시오.','vector_pq','vector',lambda p:V(b(p)-a(p),c(p)-b(p),a(p)-c(p)))
reg('magnitude_and_unit_vector_calculation','v=({{ a }},{{ b }},{{ c }})의 방향 단위벡터를 구하시오.','unit_vector','vector',lambda p:A(p)/norm(A(p)))
reg('direction_angle_calculation','v=({{ a }},{{ b }},0)와 양의 x축 사이 각을 라디안으로 구하시오.','direction_angle','scalar',lambda p:s.atan(b(p)/a(p)))
reg('3d_distance_midpoint_calculation','P=(0,0,0), Q=({{ a }},{{ b }},{{ c }})의 거리를 구하시오.','distance_3d','scalar',lambda p:norm(A(p)))
reg('sphere_equation_construction','중심 ({{ a }},{{ b }},{{ c }}), 반지름 {{ N }}인 구의 방정식을 구하시오.','sphere_equation','equation',lambda p:s.Eq((x(p)-a(p))**2+(y(p)-b(p))**2+(z(p)-c(p))**2,n(p)**2,evaluate=False))
reg('dot_product_calculation','u=({{ a }},{{ b }},{{ c }}), v=({{ b }},-{{ a }},{{ k }})의 내적을 구하시오.','dot_product_definition','scalar',lambda p:A(p).dot(B(p)))
reg('angle_or_orthogonality_determination','u=({{ a }},{{ b }},0), v=({{ b }},-{{ a }},0)는 직교하는가?','orthogonality_condition','boolean',lambda p:True)
reg('projection_calculation','u=({{ a }},{{ b }},{{ c }}), v=({{ b }},-{{ a }},{{ k }})이다. u를 v에 정사영한 벡터를 구하시오.','vector_projection','vector',lambda p:A(p).dot(B(p))*B(p)/B(p).dot(B(p)))
reg('work_calculation','일정한 힘 F=({{ a }},{{ b }},{{ c }})가 변위 d=({{ b }},-{{ a }},{{ k }}) 동안 한 일을 구하시오.',None,'scalar',lambda p:A(p).dot(B(p)))
reg('cross_product_calculation','u=({{ a }},{{ b }},{{ c }}), v=({{ b }},-{{ a }},{{ k }})의 u×v를 구하시오.','cross_product_definition','vector',lambda p:A(p).cross(B(p)))
reg('area_via_cross_product','u=({{ a }},0,0), v=(0,{{ b }},0)가 만드는 삼각형 넓이를 구하시오.','parallelogram_triangle_area','scalar',lambda p:a(p)*b(p)/2)
reg('parallelism_check','u=({{ a }},{{ b }},{{ c }}), v=({{ k }})*{{ N }}u는 평행한가?','cross_product_definition','boolean',lambda p:True)
reg('coplanarity_check','u=({{ a }},0,0), v=(0,{{ b }},0), w=(1,1,{{ d }})가 동일 평면에 놓이는가?','coplanar_condition','boolean',lambda p:d(p)==0)
reg('parallelepiped_volume_calculation','세 모서리 ({{ a }},0,0),(0,{{ b }},0),(0,0,{{ c }})인 평행육면체 부피를 구하시오.','scalar_triple_product','scalar',lambda p:a(p)*b(p)*c(p))
reg('line_equation_construction','점 ({{ a }},{{ b }},{{ c }})를 지나고 방향 (1,1,1)인 직선의 매개방정식을 변수 t로 쓰시오.','line_parametric_equations','equation',lambda p:line_equations(p,A(p),V(1,1,1)))
reg('two_lines_relation_classification','L1=(t,0,0), L2=(t,{{ a }},{{ d }})이다. 두 직선을 평행/교차/꼬임 중에서 분류하시오.','line_vector_equation','classification',lambda p:'평행')
reg('plane_equation_construction','법선 ({{ a }},{{ b }},{{ c }})이고 점 ({{ d }},0,0)을 지나는 평면 방정식을 구하시오.','plane_point_normal_form','equation',lambda p:s.Eq(a(p)*x(p)+b(p)*y(p)+c(p)*z(p),a(p)*d(p),evaluate=False))
reg('two_planes_relation_classification','P1: x+y+z={{ a }}, P2: x+y+z={{ b }}이다. 두 평면을 일치/평행으로 분류하시오.','two_planes_relation','classification',lambda p:'일치' if a(p)==b(p) else '평행')
reg('angle_between_plane_and_line','평면 x=0과 방향벡터 ({{ a }},{{ b }},0)인 직선의 예각을 구하시오.','line_plane_angle','scalar',lambda p:s.asin(a(p)/s.sqrt(a(p)**2+b(p)**2)))
reg('point_plane_distance_calculation','점 ({{ a }},{{ b }},{{ c }})과 평면 x+y+z=0의 거리를 구하시오.','point_plane_distance','scalar',lambda p:(a(p)+b(p)+c(p))/s.sqrt(3))
reg('point_line_distance_calculation','점 ({{ a }},{{ b }},{{ c }})과 x축 사이 거리를 구하시오.','point_line_distance','scalar',lambda p:s.sqrt(b(p)**2+c(p)**2))
reg('parallel_planes_distance_calculation','평면 x+y+z={{ a }}와 x+y+z=-{{ b }} 사이 거리를 구하시오.','parallel_planes_distance','scalar',lambda p:(a(p)+b(p))/s.sqrt(3))
reg('quadric_surface_classification','곡면 z=({{ k }})*x²+{{ a }}y²를 타원포물면/쌍곡포물면으로 분류하시오.','elliptic_paraboloid','classification',lambda p:'타원포물면' if k(p)>0 else '쌍곡포물면')
reg('cross_section_identification','곡면 x²+y²+z²={{ a }}²의 z=0 단면의 종류를 원/타원/쌍곡선 중에서 답하시오.','ellipsoid','classification',lambda p:'원')

# 벡터 함수 및 운동: 벡터 답의 자유기호를 피하려고 질문의 지정 시간에 평가한다.
reg('vector_function_domain_calculation','r(t)=(sqrt(t-{{ a }}),log(t-{{ b }}),t)의 실수 정의역을 집합으로 구하시오.','vector_function_domain','set',lambda p:s.Intersection(s.Interval(a(p),s.oo),s.Interval.open(b(p),s.oo)))
reg('space_curve_identification','r(t)=({{ a }}cos t,{{ a }}sin t,{{ b }}t)가 놓이는 원기둥의 방정식 좌변을 x,y,z로 쓰시오. 우변은 {{ a }}²이다.','helix_example','expression',lambda p:x(p)**2+y(p)**2)
reg('curve_intersection_calculation','r(t)=({{ a }}t,{{ b }}t²,{{ c }}t³)가 평면 x={{ a }}와 만나는 점을 벡터로 구하시오.','vector_valued_function_def','vector',A)
reg('vector_derivative_calculation','r(t)=({{ a }}t,{{ b }}t²,{{ c }}t³)의 t={{ N }}에서 r\'(t)를 구하시오.','vector_derivative_def','vector',lambda p:curve(p).diff(t(p)).subs(t(p),n(p)))
reg('unit_tangent_calculation','r(t)=({{ a }}t,{{ b }}t,{{ c }}t)의 단위 접선벡터를 구하시오.','unit_tangent_vector','vector',lambda p:A(p)/norm(A(p)))
reg('tangent_line_construction','r(t)=({{ a }}t,{{ b }}t²,{{ c }}t³)의 t=1에서 접선의 매개방정식을 새 매개변수 t로 쓰시오.','tangent_line_vector_equation','equation',lambda p:line_equations(p,A(p),V(a(p),2*b(p),3*c(p))))
reg('vector_differentiation_rule_application','u(t)=({{ a }}t,0,0), v(t)=(0,{{ b }}t,0)이다. d(u×v)/dt를 t={{ N }}에서 구하시오.','vector_diff_rules','vector',lambda p:V(0,0,2*a(p)*b(p)*n(p)))
reg('constant_magnitude_orthogonality_proof','r(t)=({{ a }}cos t,{{ a }}sin t,{{ b }})이다. 모든 t에서 r·r\'=0이라는 명제를 판정하시오.','constant_magnitude_orthogonality','boolean',lambda p:True,scope='상수 길이 곡선의 명제 판정; 서술 증명은 별도 검수')
reg('vector_chain_rule_application','r(u)=({{ a }}u,{{ b }}u²,0), u=t²이다. d r(u(t))/dt를 t=1에서 구하시오.','vector_chain_rule','vector',lambda p:V(2*a(p),4*b(p),0))
reg('vector_integral_calculation','r(t)=({{ a }}t,{{ b }}t²,{{ c }}t³)를 t=0부터 1까지 적분한 벡터를 구하시오.','vector_definite_integral','vector',lambda p:V(a(p)/2,b(p)/3,c(p)/4))
reg('vector_initial_value_problem','r\'(t)=({{ a }},{{ b }}t,{{ c }}t²), r(0)=(0,0,0)이다. r(1)을 구하시오.','vector_ftc','vector',lambda p:V(a(p),b(p)/2,c(p)/3))
reg('space_curve_arc_length_calculation','r(t)=({{ a }}t,{{ b }}t,{{ c }}t), 0≤t≤{{ N }}의 길이를 구하시오.','vector_arc_length','scalar',lambda p:n(p)*norm(A(p)))
reg('curvature_calculation','원 r(t)=({{ a }}cos t,{{ a }}sin t,0)의 곡률을 구하시오.','curvature_definition','scalar',lambda p:1/a(p))
reg('frenet_frame_calculation','r(t)=({{ a }}cos t,{{ a }}sin t,0)의 t=0에서 단위 주법선 N을 구하시오.','unit_normal_vector','vector',lambda p:V(-1,0,0))
reg('osculating_circle_construction','r(t)=({{ a }}cos t,{{ a }}sin t,0)의 t=0에서 접촉원의 중심을 벡터로 구하시오.','osculating_circle_center','vector',lambda p:V(0,0,0))
reg('velocity_acceleration_calculation','r(t)=({{ a }}t,{{ b }}t²,{{ c }}t³)의 t={{ N }}에서 가속도를 구하시오.','velocity_acceleration_def','vector',lambda p:V(0,2*b(p),6*c(p)*n(p)))
reg('position_reconstruction_from_acceleration','r\'\'(t)=({{ a }},{{ b }},{{ c }}), r\'(0)=r(0)=(0,0,0)이다. r(1)을 구하시오.','velocity_from_acceleration','vector',lambda p:A(p)/2)
reg('displacement_vs_distance_calculation','r(t)=({{ a }}t,{{ b }}t,{{ c }}t), 0≤t≤{{ N }}에서 이동 거리를 구하시오.','displacement_vs_distance','scalar',lambda p:n(p)*norm(A(p)))
reg('projectile_position_construction','중력가속도 g=2, 초기위치 0, 초기속도 ({{ a }},{{ b }},{{ c }})인 포물체의 t=1 위치를 구하시오(z가 수직축).','projectile_position','vector',lambda p:V(a(p),b(p),c(p)-1))
reg('projectile_motion_solving','수직위치 z(t)={{ a }}t-t²인 포물체가 다시 z=0에 도달하는 양의 시간을 구하시오.','projectile_position','scalar',a)
reg('acceleration_decomposition','r(t)=({{ a }}cos({{ b }}t),{{ a }}sin({{ b }}t),0)의 법선 가속도 크기를 구하시오.','normal_acceleration','scalar',lambda p:a(p)*b(p)**2)
reg('speed_change_analysis','r(t)=({{ a }}t²,0,0), t>0일 때 속력의 시간 변화율을 구하시오.','tangential_acceleration','scalar',lambda p:2*a(p))
reg('uniform_circular_motion_calculation','r(t)=({{ a }}cos({{ b }}t),{{ a }}sin({{ b }}t),0)의 속력을 구하시오.','uniform_circular_motion','scalar',lambda p:a(p)*b(p))

# 다변수 미분: 정의역은 부등식, 선/평면은 방정식 묶음으로 표현한다.
reg('multivariable_domain_calculation','f(x,y)=log({{ a }}²-x²-y²)의 실수 정의역 조건을 부등식으로 쓰시오.','domain_definition','expression',lambda p:s.Lt(x(p)**2+y(p)**2,a(p)**2))
reg('level_curve_sketching','f(x,y)={{ a }}x²+{{ b }}y²의 높이 {{ c }} 등위곡선을 스케치할 기준 방정식을 쓰시오.','level_curve','equation',lambda p:s.Eq(a(p)*x(p)**2+b(p)*y(p)**2,c(p),evaluate=False),scope='등위곡선 방정식만 검사; 그림은 별도 검수')
reg('path_test_limit_nonexistence','f(x,y)={{ a }}xy/(x²+y²)의 (0,0) 극한이 존재하지 않는가? 참/거짓으로 답하시오.','path_test_examples','boolean',lambda p:True)
reg('continuity_verification','f(x,y)={{ a }}xy/(x²+y²), f(0,0)=0이다. 원점에서 연속인가?','multivariable_continuity','boolean',lambda p:False)
reg('polar_substitution_limit_calculation','(x,y)→(0,0)에서 {{ a }}(x²+y²)의 극한을 구하시오.','polar_substitution_for_limit','scalar',lambda p:s.Integer(0))
reg('partial_derivative_calculation','f(x,y)={{ a }}x²+{{ b }}xy+{{ c }}y²의 ∂f/∂x를 구하시오.','partial_derivative_def','expression',lambda p:s.diff(expr2(p),x(p)))
reg('second_order_partial_calculation','f(x,y)={{ a }}x²+{{ b }}xy+{{ c }}y²의 ∂²f/∂x∂y를 구하시오.','second_order_partials','expression',b)
reg('clairaut_theorem_verification','f(x,y)={{ a }}x²y+{{ b }}xy²의 f_xy와 f_yx의 공통값을 계산하시오.','clairauts_theorem','expression',lambda p:2*a(p)*x(p)+2*b(p)*y(p))
reg('tangent_plane_construction','z={{ a }}x²+{{ b }}y²의 (x,y)=(1,1)에서 접평면 방정식을 쓰시오.','tangent_plane_formula','equation',lambda p:s.Eq(z(p),2*a(p)*x(p)+2*b(p)*y(p)-a(p)-b(p),evaluate=False))
reg('linearization_estimation','f(x,y)={{ a }}x²+{{ b }}y²를 (1,1)에서 선형화해 f(3/2,1)을 근사하시오.','linearization_2var','numerical_approximation',lambda p:2*a(p)+b(p))
reg('total_differential_estimation','f(x,y)={{ a }}x²+{{ b }}y², (x,y)=(1,1), dx=dy=1/2이다. df를 구하시오.','total_differential','numerical_approximation',lambda p:a(p)+b(p))
reg('multivariable_chain_rule_application','f(x,y)={{ a }}x²+{{ b }}y², x=t, y=t²이다. 합성함수의 t 도함수를 구하시오.','chain_rule_one_parameter','expression',lambda p:2*a(p)*t(p)+4*b(p)*t(p)**3)
reg('multivariable_implicit_differentiation','x²+y²+z²={{ a }}²에서 z≠0이다. z_x를 구하시오.','multivariable_implicit_diff','expression',lambda p:-x(p)/z(p))
reg('directional_derivative_calculation','f(x,y)={{ a }}x+{{ b }}y의 방향 (1,1)/sqrt(2) 미분값을 구하시오.','directional_derivative_gradient_relation','scalar',lambda p:(a(p)+b(p))/s.sqrt(2))
reg('max_increase_direction_calculation','f(x,y,z)={{ a }}x+{{ b }}y+{{ c }}z의 최대 증가 방향 단위벡터를 구하시오.','max_increase_rate','vector',lambda p:A(p)/norm(A(p)))
reg('level_surface_tangent_plane_construction','구 x²+y²+z²={{ a }}²+{{ b }}²+{{ c }}²의 점 ({{ a }},{{ b }},{{ c }})에서 접평면을 구하시오.','level_surface_tangent_plane','equation',lambda p:s.Eq(a(p)*x(p)+b(p)*y(p)+c(p)*z(p),A(p).dot(A(p)),evaluate=False))
reg('normal_line_construction','구 x²+y²+z²={{ a }}²+{{ b }}²+{{ c }}²의 점 ({{ a }},{{ b }},{{ c }})에서 법선 직선의 매개방정식을 변수 t로 쓰시오.','normal_line','equation',lambda p:line_equations(p,A(p),A(p)))
reg('critical_point_calculation','f(x,y)={{ a }}(x-{{ d }})²+{{ b }}(y-{{ c }})²의 임계점들의 집합을 구하시오.','critical_point_def','set',lambda p:s.FiniteSet(s.Tuple(d(p),c(p))))
reg('second_derivative_test_classification','f(x,y)={{ a }}x²+({{ k }})*{{ b }}y²의 원점 임계점을 극소/안장점으로 분류하시오.','second_derivative_test','classification',lambda p:'극소' if k(p)>0 else '안장점')
reg('absolute_extrema_on_closed_region','f(x,y)={{ a }}x+{{ b }}y의 닫힌 정사각형 [0,1]²에서 최댓값을 구하시오.','extreme_value_theorem_multivariable','scalar',lambda p:a(p)+b(p))
reg('lagrange_system_construction','f=x²+y², 제약 x+y={{ a }}이다. Lagrange 조건으로 얻는 최소점의 x 좌표를 구하시오.','lagrange_system_2var','scalar',lambda p:a(p)/2,scope='제약식/정상 조건에서 얻는 좌표 답만 검사; 시스템을 세우는 서술은 별도 검수')
reg('constrained_optimization_solving','x+y={{ a }}에서 x²+y²의 최솟값을 구하시오.','lagrange_condition','scalar',lambda p:a(p)**2/2)

# 중적분/질량/변수변환: 구간은 전부 질문에 명시한다.
reg('double_integral_rectangle_calculation','[0,{{ a }}]×[0,{{ b }}]에서 f(x,y)=x+y의 이중적분을 구하시오.','fubini_rectangle','scalar',lambda p:a(p)*b(p)*(a(p)+b(p))/2)
reg('average_value_2d_calculation','[0,{{ a }}]×[0,{{ b }}]에서 f=x+y의 평균값을 구하시오.','double_integral_average','scalar',lambda p:(a(p)+b(p))/2)
reg('region_type_classification','영역 0≤x≤{{ a }}, 0≤y≤x는 I형(세로 단면)으로 기술 가능한가? 가능하면 1, 불가능하면 0으로 답하시오.','type1_region_integral','scalar',lambda p:s.Integer(1))
reg('integration_order_swap','0≤x≤{{ a }},0≤y≤x의 적분 순서를 바꾸면 0≤y≤{{ a }}, y≤x≤{{ a }}이다. 함수 1의 적분값을 구하시오.','type2_region_integral','scalar',lambda p:a(p)**2/2,scope='순서 변경의 영역은 질문에 명시; 변경 후 적분값을 검사')
reg('volume_between_surfaces_calculation','[0,{{ a }}]×[0,{{ b }}] 위에서 z=0과 z={{ c }} 사이 부피를 구하시오.','volume_between_surfaces','scalar',lambda p:a(p)*b(p)*c(p))
reg('polar_double_integral_setup','반지름 {{ a }}인 원판에서 f(x,y)=x²+y²의 극좌표 적분을 세우시오. r=x로 적을 때 Jacobian 포함 피적분함수를 구하시오.','polar_area_element','expression',lambda p:x(p)**3)
reg('polar_double_integral_calculation','반지름 {{ a }}인 원판에서 {{ b }}*(x²+y²)를 이중적분하시오.','polar_double_integral','scalar',lambda p:b(p)*s.pi*a(p)**4/2)
reg('mass_and_moment_calculation','밀도 {{ c }}인 [0,{{ a }}]×[0,{{ b }}] 직사각형 판의 질량을 구하시오.','mass_2d','scalar',lambda p:a(p)*b(p)*c(p))
reg('center_of_mass_calculation','균일한 밀도의 [0,{{ a }}]×[0,{{ b }}] 직사각형 판의 무게중심 x 좌표를 구하시오.','centroid_uniform_density','scalar',lambda p:a(p)/2)
reg('triple_integral_setup','0≤x≤{{ a }},0≤y≤{{ b }},0≤z≤{{ c }}에서 밀도 x+y+z를 적분한다. z를 먼저 적분한 결과를 x,y의 식으로 구하시오.','triple_integral_general_region','expression',lambda p:c(p)*(x(p)+y(p))+c(p)**2/2)
reg('triple_integral_calculation','[0,{{ a }}]×[0,{{ b }}]×[0,{{ c }}]에서 x+y+z를 삼중적분하시오.','triple_integral_def','scalar',lambda p:a(p)*b(p)*c(p)*(a(p)+b(p)+c(p))/2)
reg('solid_volume_via_triple_integral','모서리 길이 {{ a }},{{ b }},{{ c }}인 직육면체의 부피를 삼중적분으로 구하시오.','volume_via_triple_integral','scalar',lambda p:a(p)*b(p)*c(p))
reg('3d_mass_center_calculation','균일한 밀도의 [0,{{ a }}]×[0,{{ b }}]×[0,{{ c }}] 직육면체의 무게중심 z 좌표를 구하시오.','center_of_mass_3d','scalar',lambda p:c(p)/2)
reg('moment_of_inertia_calculation','밀도 1인 [0,{{ a }}]×[0,{{ b }}]×[0,{{ c }}] 직육면체의 z축 관성모멘트를 구하시오.','moment_of_inertia_3d','scalar',lambda p:a(p)*b(p)*c(p)*(a(p)**2+b(p)**2)/3)
reg('cylindrical_triple_integral_setup','원기둥 0≤r≤{{ a }},0≤θ≤2π,0≤z≤{{ b }}에서 밀도 r²를 적분한다. Jacobian 포함 피적분함수를 r=x로 쓰시오.','cylindrical_volume_element','expression',lambda p:x(p)**3)
reg('cylindrical_triple_integral_calculation','반지름 {{ a }}, 높이 {{ b }}인 원기둥에서 x²+y²를 삼중적분하시오.','cylindrical_conversion','scalar',lambda p:s.pi*a(p)**4*b(p)/2)
reg('spherical_triple_integral_setup','반지름 {{ a }}인 구의 부피를 구면좌표로 적분한다. ρ=x, φ=y로 쓸 때 Jacobian을 쓰시오.','spherical_volume_element','expression',lambda p:x(p)**2*s.sin(y(p)))
reg('spherical_triple_integral_calculation','반지름 {{ a }}인 구에서 상수 함수 {{ b }}를 구면좌표로 삼중적분하시오.','spherical_volume_element','scalar',lambda p:4*s.pi*b(p)*a(p)**3/3)
reg('jacobian_calculation','x={{ a }}u, y={{ b }}v의 Jacobian ∂(x,y)/∂(u,v)를 구하시오.','jacobian_2d','scalar',lambda p:a(p)*b(p))
reg('change_of_variables_integral_calculation','변환 x={{ a }}u,y={{ b }}v에서 0≤u,v≤1인 영역의 면적을 Jacobian으로 구하시오.','change_of_variables_2d','scalar',lambda p:a(p)*b(p))

# 벡터장/선적분/면적분/정리: 방향 및 구멍의 경계를 명시한다.
reg('vector_field_classification','F(x,y)=({{ a }}x,{{ a }}y)를 방사형/회전형으로 분류하시오.','radial_and_rotational_fields','classification',lambda p:'방사형')
reg('vector_field_domain_calculation','F=({{ a }}x,{{ b }}y,{{ c }}z)/(x²+y²+z²)의 정의역을 R³ 또는 R³에서 원점 제외 중에서 답하시오.','vector_field_2d_3d','classification',lambda p:'R³에서 원점 제외')
reg('scalar_line_integral_calculation','선분 r(t)=({{ a }}t,{{ b }}t,0),0≤t≤1에서 f=1의 선적분을 구하시오.','scalar_line_integral','scalar',lambda p:s.sqrt(a(p)**2+b(p)**2))
reg('curve_mass_calculation','선밀도 {{ c }}인 선분 r(t)=({{ a }}t,{{ b }}t,0),0≤t≤1의 질량을 구하시오.','mass_via_line_integral','scalar',lambda p:c(p)*s.sqrt(a(p)**2+b(p)**2))
reg('vector_line_integral_calculation','F=(x,y,0), r(t)=({{ a }}t,{{ b }}t,0),0≤t≤1에서 F·dr의 적분을 구하시오.','vector_line_integral','scalar',lambda p:(a(p)**2+b(p)**2)/2)
reg('conservativeness_test','F=({{ a }}y,{{ b }}x)는 R² 전체에서 보존장인가?','conservative_test_2d','boolean',lambda p:a(p)==b(p))
reg('potential_function_construction','F=(2*{{ a }}x,2*{{ b }}y,2*{{ c }}z)의 퍼텐셜 중 원점에서 0인 함수를 구하시오.','conservative_field_def','expression',lambda p:a(p)*x(p)**2+b(p)*y(p)**2+c(p)*z(p)**2)
reg('line_integral_via_potential','F=∇(x²+y²+z²), 시작점 원점, 끝점 ({{ a }},{{ b }},{{ c }})인 곡선을 따른 선적분을 구하시오.','fundamental_theorem_line_integrals','scalar',lambda p:A(p).dot(A(p)))
reg('greens_theorem_application','F=(-y,x), 반지름 {{ a }}인 원의 반시계 경계에서 ∮F·dr를 Green 정리로 구하시오.','greens_theorem_circulation','scalar',lambda p:2*s.pi*a(p)**2)
reg('area_via_greens_theorem','반지름 {{ a }}인 원판의 넓이를 Green 정리로 구하시오.','greens_area_formula','scalar',lambda p:s.pi*a(p)**2)
reg('region_with_hole_line_integral','{{ a }}≤r≤{{ a+b }}인 원환에서 F=(-y,x)의 경계 선적분을 구하시오. 바깥은 반시계, 안쪽은 시계다.','greens_theorem_circulation','scalar',lambda p:2*s.pi*((a(p)+b(p))**2-a(p)**2))
reg('divergence_calculation','F=({{ a }}x,{{ b }}y,{{ c }}z)의 발산을 구하시오.','divergence_def','scalar',lambda p:a(p)+b(p)+c(p))
reg('curl_calculation','F=(-{{ a }}y,{{ b }}x,0)의 회전을 벡터로 구하시오.','curl_def','vector',lambda p:V(0,0,a(p)+b(p)))
reg('fundamental_identity_application','f(x,y,z)={{ a }}x²+{{ b }}y²+{{ c }}z²에 대해 curl(grad f)를 구하시오.','fundamental_identities','vector',lambda p:V(0,0,0))
reg('surface_normal_calculation','평면 z={{ a }}x+{{ b }}y에서 위쪽 단위법선벡터를 구하시오.','surface_normal_vector','vector',lambda p:V(-a(p),-b(p),1)/s.sqrt(1+a(p)**2+b(p)**2))
reg('surface_area_calculation','z={{ a }}x+{{ b }}y,0≤x,y≤1인 평면 조각의 넓이를 구하시오.','surface_area_graph','scalar',lambda p:s.sqrt(1+a(p)**2+b(p)**2))
reg('scalar_surface_integral_calculation','반지름 {{ a }}인 구면에서 상수 함수 {{ b }}의 면적분을 구하시오.','scalar_surface_integral','scalar',lambda p:4*s.pi*a(p)**2*b(p))
reg('flux_calculation','F=(0,0,{{ c }}),0≤x≤{{ a }},0≤y≤{{ b }},z=0인 면의 위쪽 유량을 구하시오.','flux_integral','scalar',lambda p:a(p)*b(p)*c(p))
reg('stokes_theorem_application','F=(-y,x,0), 반지름 {{ a }}인 z=0 원의 반시계 방향 선적분을 Stokes 정리로 구하시오.','stokes_theorem','scalar',lambda p:2*s.pi*a(p)**2)
reg('surface_choice_for_stokes','반지름 {{ a }}인 z=0 원의 반시계 경계에 대해 Stokes 정리의 위쪽 원판을 선택했다. F=(-y,x,0)의 curl 유량을 구하시오.','stokes_theorem','scalar',lambda p:2*s.pi*a(p)**2,scope='선택한 원판/방향을 명시하고 결과만 검사; 임의 곡면 선택은 별도 검수')
reg('divergence_theorem_application','F=(x,y,z), 반지름 {{ a }}인 구면의 바깥쪽 유량을 발산정리로 구하시오.','divergence_theorem','scalar',lambda p:4*s.pi*a(p)**3)
reg('region_with_cavity_flux','F=(x,y,z), {{ a }}≤r≤{{ a+b }}인 구껍질 경계의 영역 바깥 방향 총유량을 구하시오(안쪽 법선은 중심 방향).','divergence_theorem','scalar',lambda p:4*s.pi*((a(p)+b(p))**3-a(p)**3))

# 2계 선형 ODE: 임의상수 C1,C2를 명시하고 초기값 문제는 별도로 계산한다.
reg('homogeneous_classification','y\'\'+{{ a }}y\'+{{ b }}y={{ d }}는 동차인가?','second_order_linear_ode','boolean',lambda p:d(p)==0)
reg('wronskian_linear_independence_check','exp({{ a }}x)와 exp({{ b }}x)는 실수 전체에서 선형독립인가?','wronskian','boolean',lambda p:a(p)!=b(p))
reg('characteristic_equation_solving','y\'\'+({{ b }}-{{ a }})y\'-{{ a }}*{{ b }}y=0의 특성근을 큰 근, 작은 근 순서의 쌍으로 답하시오.','characteristic_equation','expression',lambda p:s.Tuple(a(p),-b(p)))
reg('homogeneous_general_solution_construction','y\'\'+({{ b }}-{{ a }})y\'-{{ a }}*{{ b }}y=0의 일반해를 C1*exp({{ a }}x)+C2*exp(-{{ b }}x) 순서로 쓰시오.','distinct_real_roots_solution','expression',ode_general)
reg('second_order_ivp_solving','y\'\'+({{ b }}-{{ a }})y\'-{{ a }}*{{ b }}y=0, y(0)={{ c }}, y\'(0)={{ d }}의 해를 구하시오.','second_order_ivp','expression',ivp)
reg('general_solution_decomposition','y\'\'+({{ b }}-{{ a }})y\'-{{ a }}*{{ b }}y=-{{ a }}*{{ b }}이다. 일반해를 C1*exp({{ a }}x)+C2*exp(-{{ b }}x)+특수해 형태로 쓰시오.','nonhomogeneous_general_solution','expression',lambda p:ode_general(p)+1)
reg('undetermined_coefficients_ansatz_selection','y\'\'-{{ a }}²y=exp({{ b }}x), b={{ b }}, a={{ a }}이다. 미정계수법의 시험해를 미정계수 1로 놓고 쓰시오. 중복이면 x 인수를 붙이시오.','undetermined_coeff_exponential','expression',lambda p:(x(p) if a(p)==b(p) else 1)*s.exp(b(p)*x(p)))
reg('duplication_case_handling','y\'\'-{{ a }}²y=exp({{ a }}x)의 미정계수 시험해를 미정계수 1로 놓고 쓰시오.','undetermined_coeff_duplication_rule','expression',lambda p:x(p)*s.exp(a(p)*x(p)))
reg('undetermined_coefficients_solving','y\'\'-{{ a }}²y={{ b }}의 상수 특수해 하나를 구하시오.','undetermined_coeff_polynomial','expression',lambda p:-b(p)/a(p)**2)
reg('variation_of_parameters_application','y\'\'+{{ a }}²y={{ b }}에서 매개변수 변화법으로 구할 수 있는 상수 특수해 하나를 구하시오.','variation_of_parameters_formula','expression',lambda p:b(p)/a(p)**2,scope='매개변수 변화의 특수해 결과만 검사; 적분 과정은 별도 검수')
reg('shm_equation_setup','질량 m={{ a }}, 용수철 상수 K={{ b }}의 자유운동 방정식을 y\'\'+ω²y=0으로 쓴다. ω²를 구하시오.','simple_harmonic_ode','scalar',lambda p:b(p)/a(p))
reg('period_frequency_calculation','질량 m={{ a }}, 용수철 상수 K={{ b }}인 단순조화운동의 주기를 구하시오.','period_and_frequency','scalar',lambda p:2*s.pi*s.sqrt(a(p)/b(p)))
reg('amplitude_phase_conversion','y={{ a }}cos x+{{ b }}sin x의 진폭을 구하시오.','simple_harmonic_solution','scalar',lambda p:s.sqrt(a(p)**2+b(p)**2))
reg('damping_type_classification','방정식 y\'\'+2*{{ a }}y\'+{{ b }}²y=0을 과감쇠/임계감쇠/저감쇠로 분류하시오.','damping_classification','classification',lambda p:'과감쇠' if a(p)>b(p) else ('임계감쇠' if a(p)==b(p) else '저감쇠'))
reg('damped_motion_solving','y\'\'+2*{{ a }}y\'+({{ a }}²+{{ b }}²)y=0의 일반해를 C1,C2로 쓰시오.','underdamped_solution','expression',lambda p:s.exp(-a(p)*x(p))*(p['C1']*s.cos(b(p)*x(p))+p['C2']*s.sin(b(p)*x(p))))
reg('resonance_condition_check','감쇠 없는 y\'\'+{{ a }}²y=cos({{ b }}x)는 공진 조건을 만족하는가?','resonance_condition','boolean',lambda p:a(p)==b(p))
reg('forced_oscillation_solving','y\'\'+{{ a }}²y=cos({{ b }}x)의 특수해 하나를 구하시오. a=b인 공진 경우도 포함한다.','forced_oscillation_ode','expression',lambda p:x(p)*s.sin(a(p)*x(p))/(2*a(p)) if a(p)==b(p) else s.cos(b(p)*x(p))/(a(p)**2-b(p)**2))
reg('rlc_equation_construction','L={{ a }}, R={{ b }}, C=1/{{ c }}, 전압={{ d }}인 직렬 RLC에서 q\'\'를 q=x, q\'=y의 식으로 나타내시오.','rlc_circuit_equation','expression',lambda p:(d(p)-b(p)*y(p)-c(p)*x(p))/a(p))
reg('rlc_analogy_application','L={{ a }}, R={{ b }}, C=1/{{ c }}인 RLC를 용수철계 m u\'\'+γ u\'+K u=0에 대응시킨다. K만 구하시오.','rlc_spring_mass_analogy','expression',c)
reg('power_series_solution_construction','y\'\'+{{ a }}²y=0, y(0)=1,y\'(0)=0의 급수해에서 x^(2{{ N }}) 이하 부분합을 구하시오.','power_series_ansatz','expression',lambda p:sum((-1)**j*a(p)**(2*j)*x(p)**(2*j)/s.factorial(2*j) for j in range(n(p)+1)))
reg('recurrence_relation_derivation','y\'\'+{{ a }}²y=0에 y=∑c_n x^n를 대입한다. c_(n+2)=M(n)c_n에서 M(n)을 n=x로 쓰시오.','coefficient_comparison','expression',lambda p:-a(p)**2/((x(p)+1)*(x(p)+2)))
reg('bessel_equation_identification','x²y\'\'+xy\'+({{ a }}²x²-{{ c }}²)y=0을 u={{ a }}x로 바꾸면 Bessel 방정식이다. 그 차수 ν를 구하시오.','bessel_equation','expression',c)
reg('bessel_series_derivation','J0({{ a }}x)의 급수를 x^(2{{ N }}) 항까지 쓰시오. J0(u)=∑(-1)^j(u²/4)^j/(j!)² 이다.','bessel_j0','expression',lambda p:sum((-1)**j*a(p)**(2*j)*x(p)**(2*j)/(4**j*s.factorial(j)**2) for j in range(n(p)+1)))

# 범위를 좁혀 CAS 실행 시간과 손계산용 분수 크기를 제한한다.
for name in ('power_series_solution_construction','bessel_series_derivation'):
    PROFILES[name]['parameters']['N']=integer(1,2)
for name in ('taylor_error_estimation','taylor_polynomial_construction','taylor_series_derivation','common_series_recall','series_based_integration','taylor_coefficient_extraction'):
    PROFILES[name]['parameters']['N']=integer(1,3)
# 표기에서 문자열끼리 연산하거나 숫자를 붙여 잘못된 계수를 만들지 않는다.
for profile in PROFILES.values():
    profile['question']=profile['question'].replace('{{ a+b }}','({{ a }}+{{ b }})').replace('{{ N+1 }}','({{ N }}+1)')


def checked_parameters(parameters,name):
    if name not in PROFILES:raise ValueError('미등록 미적분 2 유형: '+str(name))
    for key,spec in PROFILES[name]['parameters'].items():
        v=parameters.get(key)
        if isinstance(v,bool) or not isinstance(v,(int,s.Integer)) or not spec['min']<=v<=spec['max']:
            raise ValueError('정수 범위 계약 위반: '+key)
        if 'choices' in spec and v not in spec['choices']:raise ValueError('선택값 계약 위반: '+key)
    for key in SYMBOLS:
        v=parameters.get(key)
        if not isinstance(v,s.Symbol) or v.is_real is not True:raise ValueError('실수 Symbol 필요: '+key)
    if len({parameters[key] for key in SYMBOLS})!=len(SYMBOLS):raise ValueError('선언 기호는 서로 달라야 합니다.')
    return parameters


def calculate(parameters,name):
    values=checked_parameters(parameters,name)
    answer=CALCULATORS[name](values)
    def resolved(item):
        if isinstance(item,(tuple,list,s.Tuple)):
            for child in item:resolved(child)
        elif isinstance(item,s.MatrixBase):
            for child in item:resolved(child)
        elif isinstance(item,s.Basic):
            if item.has(s.Integral,s.Derivative,s.Sum,s.Limit,s.nan,s.zoo):raise ValueError('CAS 계산 미완료')
            if not isinstance(item,s.Set) and item.has(s.oo,-s.oo):raise ValueError('무한 스칼라 결과는 허용하지 않습니다.')
    resolved(answer)
    return answer


def validate(answer,parameters,config):
    from scripts.problems.common.math_validators import equal,boolean
    name=config.get('operation');p=checked_parameters(parameters,name);expected=calculate(p,name)
    def compare(candidate,target):
        if isinstance(target,(bool,s.logic.boolalg.BooleanAtom)):
            try:return boolean(candidate)==bool(target)
            except ValueError:return False
        if isinstance(target,str):return isinstance(candidate,str) and candidate==target
        if isinstance(target,s.Set):
            return isinstance(candidate,s.Set) and not candidate.has(s.ConditionSet,s.nan,s.zoo) and s.SymmetricDifference(candidate,target)==s.EmptySet
        if isinstance(target,s.MatrixBase):
            return isinstance(candidate,s.MatrixBase) and candidate.shape==target.shape and all(compare(v,w) for v,w in zip(candidate,target))
        if isinstance(target,(tuple,list,s.Tuple)):
            return isinstance(candidate,(tuple,list,s.Tuple)) and len(candidate)==len(target) and all(compare(v,w) for v,w in zip(candidate,target))
        if isinstance(target,s.Equality):
            if not isinstance(candidate,s.Equality):return False
            lhs=s.expand(candidate.lhs-candidate.rhs);rhs=s.expand(target.lhs-target.rhs)
            ratio=s.cancel(lhs/rhs) if rhs!=0 else None
            return lhs==0 if rhs==0 else (ratio.is_number is True and ratio.is_finite is True and ratio!=0)
        if isinstance(target,s.core.relational.Relational):
            return isinstance(candidate,s.core.relational.Relational) and s.simplify(candidate)==s.simplify(target)
        return equal(candidate,target,config)
    # 미분방정식은 식의 일치와 함께 원 방정식 및 초기조건을 검사한다.
    if name=='second_order_ivp_solving':
        if not isinstance(answer,s.Expr):return False
        return equal(linear_ode(p,answer),0) and equal(answer.subs(x(p),0),c(p)) and equal(s.diff(answer,x(p)).subs(x(p),0),d(p))
    if name in ('undetermined_coefficients_solving','variation_of_parameters_application','forced_oscillation_solving'):
        if not isinstance(answer,s.Expr):return False
        forcing=s.cos(b(p)*x(p)) if name=='forced_oscillation_solving' else b(p)
        sign=-1 if name=='undetermined_coefficients_solving' else 1
        return equal(s.diff(answer,x(p),2)+sign*a(p)**2*answer,forcing)
    if name=='potential_function_construction':
        if not isinstance(answer,s.Expr):return False
        return all(equal(s.diff(answer,var),deriv) for var,deriv in zip((x(p),y(p),z(p)),(2*a(p)*x(p),2*b(p)*y(p),2*c(p)*z(p)))) and equal(answer.subs({x(p):0,y(p):0,z(p):0}),0)
    return compare(answer,expected)
