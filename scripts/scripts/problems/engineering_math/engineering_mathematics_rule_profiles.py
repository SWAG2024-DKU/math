"""공학수학 104개 유형의 명시적 생성 계약.

각 질문에 함수족·정의역·초기/경계 조건·변환 관례·요구 답을 명시한다.
일반적인 임의 ODE/PDE 자동 풀이기가 아니다. 각 유형의 지원 함수족은 question과
scope에 공개한다. 자동 실행 검증은 사람의 콘텐츠 승인과 구분한다.
"""
from copy import deepcopy
import sympy as sp

MARKER='[engineering_mathematics_execution_v1]'
PROFILES={}; CALCULATORS={}; RESIDUALS={}

def integer(lo=1,hi=4,choices=None):
    value={'type':'integer','min':lo,'max':hi}
    if choices is not None:value['choices']=choices
    return value
BASE={'a':integer(),'b':integer(),'c':integer(),'n':integer(1,3),'k':integer(-1,1,[-1,1])}
SYMBOLS={q:{'role':'independent_variable','assumptions':{'real':True}} for q in ('x','y','z','t','s','C1','C2')}
SYMBOLS['w']={'role':'independent_variable','assumptions':{}}

def v(p,name):return p[name]
def a(p):return sp.Integer(p['a'])
def b(p):return sp.Integer(p['b'])
def c(p):return sp.Integer(p['c'])
def n(p):return sp.Integer(p['n'])
def k(p):return sp.Integer(p['k'])
def x(p):return p['x']
def y(p):return p['y']
def t(p):return p['t']
def z(p):return p['z']
def S(p):return p['s']
def w(p):return p['w']
def V(*values):return sp.Matrix(values)
def linear(p):return b(p)/a(p)+(c(p)-b(p)/a(p))*sp.exp(-a(p)*t(p))
def heat(p):return a(p)*sp.sin(n(p)*x(p))*sp.exp(-b(p)*n(p)**2*t(p))
def wave(p):return a(p)*sp.sin(n(p)*x(p))*sp.cos(b(p)*n(p)*t(p))

def reg(name,question,kind,fn,scope='',residual=None):
    if name in PROFILES:raise ValueError('중복 공학수학 유형: '+name)
    params=deepcopy(BASE);symbols=deepcopy(SYMBOLS)
    refs=','.join(repr(q)+':'+q for q in [*params,*symbols])
    PROFILES[name]={'question':question,'formula':None,'answer_type':kind,
        'expression':'engineering_mathematics_value({'+refs+'},'+repr(name)+')',
        'validator':'engineering_mathematics_check','config':{'operation':name},
        'parameters':params,'symbols':symbols,'constraints':[],
        'scope':scope or question}
    CALCULATORS[name]=fn
    if residual:RESIDUALS[name]=residual

# 1차 ODE: 정의역과 초기값을 통해 특정 해를 요청한다.
reg('separable_ode_solving',"y'=({{ a }})y, y(0)={{ b }}의 해 y(t)를 구하시오.",'expression',lambda p:b(p)*sp.exp(a(p)*t(p)),residual=lambda p,q:[sp.diff(q,t(p))-a(p)*q,q.subs(t(p),0)-b(p)])
reg('linear_ode_solving',"y'+{{ a }}y={{ b }}, y(0)={{ c }}의 해 y(t)를 구하시오.",'expression',linear,residual=lambda p,q:[sp.diff(q,t(p))+a(p)*q-b(p),q.subs(t(p),0)-c(p)])
reg('applied_ode_modeling','초기 개체수 {{ b }}, 연속 상대성장률 {{ a }}인 지수성장 모델의 N(t)를 구하시오. 시간 단위는 성장률의 역수이다.','expression',lambda p:b(p)*sp.exp(a(p)*t(p)))
reg('bernoulli_ode_solving',"y'+{{ a }}y={{ a }}y², y(0)=1/({{ c }}+1)의 해 y(t)를 구하시오.",'expression',lambda p:1/(1+c(p)*sp.exp(a(p)*t(p))),residual=lambda p,q:[sp.diff(q,t(p))+a(p)*q-a(p)*q*q,q.subs(t(p),0)-1/(c(p)+1)])
reg('homogeneous_ode_solving',"t>0에서 y'=y/t+{{ a }}, y(1)={{ b }}의 해 y(t)를 구하시오.",'expression',lambda p:t(p)*(b(p)+a(p)*sp.log(t(p))))
reg('exact_ode_solving','(2*{{ a }}x+y)dx+(x+2*{{ b }}y)dy=0의 보존량 F(x,y)를 구하시오. F(0,0)=0으로 정규화하시오.','expression',lambda p:a(p)*x(p)**2+x(p)*y(p)+b(p)*y(p)**2,residual=lambda p,q:[sp.diff(q,x(p))-(2*a(p)*x(p)+y(p)),sp.diff(q,y(p))-(x(p)+2*b(p)*y(p)),q.subs({x(p):0,y(p):0})])
reg('exact_integrating_factor_solving','x>0에서 {{ a }}y dx+({{ a+b }})x dy=0에 곱할 x만의 적분인자 μ(x)를 구하시오. μ(1)=1이다.','expression',lambda p:x(p)**(-b(p)/(a(p)+b(p))),residual=lambda p,q:[sp.diff(q*a(p)*y(p),y(p))-sp.diff((a(p)+b(p))*x(p)*q,x(p)),q.subs(x(p),1)-1])
reg('autonomous_stability_analysis',"자율방정식 y'=y({{ a }}-y)의 모든 평형값을 오름차순 목록으로 구하시오.",'scalar_list',lambda p:[sp.Integer(0),a(p)],'평형점 계산; 안정성 서술 대신 평형값 전체 목록')
reg('ivp_uniqueness_test',"y'=({{ k }})*{{ a }}y+{{ b }}t, y(0)={{ c }}는 모든 유한한 t에서 유일한 해를 갖는가?",'boolean',lambda p:True)
reg('ode_classification',"y'+{{ a }}y^{{ n }}={{ b }}t는 y에 관한 선형 ODE인가?",'boolean',lambda p:n(p)==1)
# 고차 ODE와 진동.
reg('characteristic_equation_setup',"y''+({{ a+b }})y'+({{ a*b }})y=0의 특성다항식을 s로 쓰시오.",'expression',lambda p:S(p)**2+(a(p)+b(p))*S(p)+a(p)*b(p))
reg('homogeneous_ode_solution_construction',"y''-{{ a*a }}y=0의 일반해를 C1,C2,t로 쓰시오.",'expression',lambda p:p['C1']*sp.exp(a(p)*t(p))+p['C2']*sp.exp(-a(p)*t(p)))
reg('higher_order_ivp_solving',"y''+{{ a*a }}y=0, y(0)={{ b }}, y'(0)={{ c }}의 해를 구하시오.",'expression',lambda p:b(p)*sp.cos(a(p)*t(p))+c(p)/a(p)*sp.sin(a(p)*t(p)),residual=lambda p,q:[sp.diff(q,t(p),2)+a(p)**2*q,q.subs(t(p),0)-b(p),sp.diff(q,t(p)).subs(t(p),0)-c(p)])
reg('higher_order_ode_classification',"y''+{{ a }}y'+{{ b }}y^{{ n }}=0은 선형 ODE인가?",'boolean',lambda p:n(p)==1)
reg('euler_cauchy_solving',"t>0에서 t²y''+(1-{{ a+b }})ty'+{{ a*b }}y=0의 일반해를 구하시오.",'expression',lambda p:p['C1']*t(p)**a(p)+p['C2']*(t(p)**b(p) if a(p)!=b(p) else t(p)**a(p)*sp.log(t(p))))
reg('undetermined_coefficients_solving',"y''-{{ a*a }}y={{ b }}의 상수 특수해를 구하시오.",'expression',lambda p:-b(p)/a(p)**2)
reg('variation_of_parameters_solving',"매개변수변환법으로 y''={{ a }}t, y(0)=y'(0)=0의 해를 구하시오.",'expression',lambda p:a(p)*t(p)**3/6,residual=lambda p,q:[sp.diff(q,t(p),2)-a(p)*t(p),q.subs(t(p),0),sp.diff(q,t(p)).subs(t(p),0)])
reg('nonhomogeneous_solution_structure',"y''-{{ a*a }}y={{ b }}의 일반해 y_h+y_p를 구하시오.",'expression',lambda p:p['C1']*sp.exp(a(p)*t(p))+p['C2']*sp.exp(-a(p)*t(p))-b(p)/a(p)**2)
reg('wronskian_calculation','f(t)=exp({{ a }}t), g(t)=exp(-{{ b }}t)의 W=f*g′-f′*g를 구하시오.','expression',lambda p:-(a(p)+b(p))*sp.exp((a(p)-b(p))*t(p)))
reg('superposition_verification',"y''+{{ a*a }}y=0의 두 해 sin({{ a }}t), cos({{ a }}t의 {{ b }},{{ c }} 선형결합도 해인가?",'boolean',lambda p:True)
reg('mechanical_vibration_solving',"질량1, 감쇠0, 용수철상수 {{ a*a }}의 자유진동 x(0)={{ b }}, x'(0)=0의 변위 x(t)를 구하시오.",'expression',lambda p:b(p)*sp.cos(a(p)*t(p)))
# Laplace: 단측 변환, t>=0; s의 수렴 영역을 문장에 명시.
reg('basic_laplace_calculation','f(t)={{ a }}t^{{ n }}의 단측 Laplace 변환 F(s), s>0을 구하시오.','expression',lambda p:a(p)*sp.factorial(n(p))/S(p)**(n(p)+1))
reg('laplace_definition_check','f(t)=exp({{ a }}t)의 단측 Laplace 적분은 s={{ a }}+({{ k }})에서 수렴하는가?','boolean',lambda p:k(p)>0)
reg('inverse_laplace_calculation','F(s)={{ b }}/(s+{{ a }})의 t≥0 역 Laplace 변환을 구하시오.','expression',lambda p:b(p)*sp.exp(-a(p)*t(p)))
reg('first_shifting_calculation','exp({{ a }}t)*sin({{ b }}t)의 단측 Laplace 변환을 구하시오(s>{{ a }}).','expression',lambda p:b(p)/((S(p)-a(p))**2+b(p)**2))
reg('second_shifting_calculation','H(t-{{ a }})*(t-{{ a }})^{{ n }}의 단측 Laplace 변환을 구하시오(s>0). H는 Heaviside 함수이다.','expression',lambda p:sp.exp(-a(p)*S(p))*sp.factorial(n(p))/S(p)**(n(p)+1))
reg('dirac_delta_laplace','Dirac delta δ(t-{{ a }})의 단측 Laplace 변환을 구하시오.','expression',lambda p:sp.exp(-a(p)*S(p)))
reg('derivative_laplace_transformation',"f(t)={{ b }}exp(-{{ a }}t)의 f'(t)에 대한 단측 Laplace 변환을 구하시오(s>0).",'expression',lambda p:-a(p)*b(p)/(S(p)+a(p)))
reg('s_differentiation_calculation','t*exp(-{{ a }}t)의 단측 Laplace 변환을 s 미분 성질로 구하시오(s>0).','expression',lambda p:1/(S(p)+a(p))**2)
reg('convolution_calculation','t≥0에서 f(t)={{ a }}, g(t)={{ b }}t의 인과적 합성곱 (f*g)(t)를 구하시오.','expression',lambda p:a(p)*b(p)*t(p)**2/2)
reg('laplace_ivp_solving',"Laplace 변환으로 y'+{{ a }}y={{ b }}, y(0)={{ c }}의 해 y(t)를 구하시오.",'expression',linear,residual=lambda p,q:[sp.diff(q,t(p))+a(p)*q-b(p),q.subs(t(p),0)-c(p)])
# 선형 시스템: 작고 정확한 행렬을 구성한다.
reg('system_matrix_form_conversion',"u'={{ a }}u+{{ b }}v, v'=-{{ b }}u+{{ c }}v를 U'=MU로 쓰기 위한 M을 구하시오.",'matrix',lambda p:sp.Matrix([[a(p),b(p)],[-b(p),c(p)]]))
reg('state_space_conversion',"y''+{{ a }}y'+{{ b }}y=0에서 U=(y,y')^T의 상태행렬을 구하시오.",'matrix',lambda p:sp.Matrix([[0,1],[-b(p),-a(p)]]))
reg('matrix_exponential_calculation','M=diag({{ a }},-{{ b }})의 exp(tM)을 구하시오.','matrix',lambda p:sp.diag(sp.exp(a(p)*t(p)),sp.exp(-b(p)*t(p))))
reg('eigenvalue_system_solving',"u'={{ a }}u, v'=-{{ b }}v, U(0)=({{ b }},{{ c }})의 벡터해를 열행렬로 구하시오.",'expression',lambda p:V(b(p)*sp.exp(a(p)*t(p)),c(p)*sp.exp(-b(p)*t(p))))
reg('complex_eigenvalue_solving',"u'=-{{ a }}v, v'={{ a }}u, U(0)=({{ b }},0)의 벡터해를 열행렬로 구하시오.",'expression',lambda p:V(b(p)*sp.cos(a(p)*t(p)),b(p)*sp.sin(a(p)*t(p))))
reg('generalized_eigenvector_solving','M=[[{{ a }},1],[0,{{ a }}]], 고유벡터 v=(1,0)이다. (M-aI)w=v, w의 첫 성분0을 만족하는 w를 열행렬로 구하시오.','expression',lambda p:V(0,1))
reg('nonhomogeneous_system_solving',"u'=-{{ a }}u+{{ b }}, v'=-{{ c }}v, U(0)=(0,1)의 벡터해를 열행렬로 구하시오.",'expression',lambda p:V(b(p)/a(p)*(1-sp.exp(-a(p)*t(p))),sp.exp(-c(p)*t(p))))
reg('linear_stability_analysis','M=diag(({{ k }})*{{ a }},-{{ b }})인 U′=MU의 원점을 안정점/안장점으로 분류하시오. 안정점은 점근안정 절점을 뜻한다.','string',lambda p:'안정점' if k(p)<0 else '안장점')
reg('nonlinear_linearization_analysis',"u'={{ a }}u+v², v'=-{{ b }}v+u²를 원점에서 선형화한 Jacobian을 구하시오.",'matrix',lambda p:sp.diag(a(p),-b(p)))
reg('phase_plane_analysis',"u'=u({{ a }}-u), v'=-{{ b }}v의 모든 평형점을 벡터 목록으로 구하시오.",'vector_list',lambda p:[V(0,0),V(a(p),0)])
# 벡터 해석: 방향, 방향성, 영역을 명시한다.
reg('field_identification','F(x,y,z)=({{ a }}x,{{ b }}y,{{ c }}z)는 스칼라장이 아니라 벡터장인가?','boolean',lambda p:True)
reg('gradient_directional_derivative_calculation','f(x,y,z)={{ a }}x²+{{ b }}y²+{{ c }}z²의 점(1,0,0), 단위방향(1,0,0) 방향미분을 구하시오.','scalar',lambda p:2*a(p))
reg('divergence_calculation','F=({{ a }}x,{{ b }}y,{{ c }}z)의 divergence를 구하시오.','expression',lambda p:a(p)+b(p)+c(p))
reg('curl_calculation','F=(-{{ a }}y,{{ a }}x,{{ b }}z)의 curl을 열벡터로 구하시오.','vector',lambda p:V(0,0,2*a(p)))
reg('laplacian_calculation','f={{ a }}x²+{{ b }}y²+{{ c }}z²의 Laplacian을 구하시오.','expression',lambda p:2*(a(p)+b(p)+c(p)))
reg('conservative_field_verification','R²에서 F=({{ a }}y,({{ k }})*{{ a }}x)는 보존장인가?','boolean',lambda p:k(p)==1)
reg('line_integral_calculation','F=({{ a }}x,{{ b }}y), r(t)=(t,t), 0≤t≤{{ c }}를 따르는 선적분 ∫F·dr를 구하시오.','scalar',lambda p:(a(p)+b(p))*c(p)**2/2)
reg('green_theorem_calculation','단위정사각형의 반시계 경계에서 ∮(-{{ a }}y)dx+({{ b }}x)dy를 구하시오.','scalar',lambda p:a(p)+b(p))
reg('surface_integral_calculation','F=(0,0,{{ a }}), 0≤x≤{{ b }}, 0≤y≤{{ c }}, z=0의 위쪽 방향 flux를 구하시오.','scalar',lambda p:a(p)*b(p)*c(p))
reg('divergence_theorem_calculation','단위구의 바깥쪽 법선에 대해 F=({{ a }}x,{{ a }}y,{{ a }}z)의 전체 flux를 구하시오.','scalar',lambda p:4*sp.pi*a(p))
reg('stokes_theorem_calculation','단위원판의 위쪽 법선에 맞춘 반시계 경계에서 F=(-{{ a }}y,{{ a }}x,0)의 순환을 구하시오.','scalar',lambda p:2*sp.pi*a(p))
reg('coordinate_transformation_integration','반지름 {{ a }}, 높이 {{ b }}인 원기둥의 ∭1 dV를 원통좌표로 계산하시오.','scalar',lambda p:sp.pi*a(p)**2*b(p))
# Fourier: angular-frequency 관례를 질문에 고정한다.
reg('fourier_series_calculation','f(x)={{ a }}cos({{ n }}x)+{{ b }}sin({{ n }}x)의 2π Fourier 계수 (a_n,b_n)를 열행렬로 구하시오.','expression',lambda p:V(a(p),b(p)))
reg('complex_fourier_calculation','f(x)={{ a }}cos({{ n }}x)+{{ b }}sin({{ n }}x)를 Σc_m exp(imx)로 쓴다. c_n을 구하시오.','expression',lambda p:(a(p)-sp.I*b(p))/2)
reg('fundamental_frequency_calculation','f(t)={{ a }}sin({{ n }}t)의 기본 각주파수를 구하시오.','expression',n)
reg('orthogonality_integral_check','∫[-π,π] cos({{ a }}x)cos({{ b }}x) dx를 구하시오.','scalar',lambda p:sp.pi if a(p)==b(p) else sp.Integer(0))
reg('half_range_expansion_calculation','0<x<π에서 f(x)={{ a }}의 반구간 sine 급수의 b_n을 n={{ n }}에 대해 구하시오.','expression',lambda p:2*a(p)*(1-(-1)**n(p))/(sp.pi*n(p)))
reg('parseval_identity_calculation','f(x)={{ a }}cos({{ n }}x)+{{ b }}sin({{ n }}x)에 대해 (1/π)∫[-π,π] f² dx를 구하시오.','scalar',lambda p:a(p)**2+b(p)**2)
reg('gibbs_phenomenon_analysis','2π 주기 함수의 x=0 좌극한은 -{{ a }}, 우극한은 {{ b }}이다. Fourier 부분합의 0에서의 극한값을 구하시오.','scalar',lambda p:(b(p)-a(p))/2)
reg('fourier_transform_calculation','F(s)=∫R f(t)exp(-ist)dt 관례로 f(t)={{ b }}exp(-{{ a }}|t|)의 Fourier 변환을 구하시오.','expression',lambda p:2*a(p)*b(p)/(a(p)**2+S(p)**2))
reg('fourier_properties_calculation','F(s)=∫R f(t)exp(-ist)dt 관례로 f(t)=exp(-{{ a }}|t-{{ b }}|)의 Fourier 변환을 구하시오.','expression',lambda p:sp.exp(-sp.I*b(p)*S(p))*2*a(p)/(a(p)**2+S(p)**2))
reg('fourier_convolution_calculation','F(s)=∫R f(t)exp(-ist)dt 관례에서 f=exp(-{{ a }}|t|), g=exp(-{{ b }}|t|)이다. f*g의 Fourier 변환을 구하시오.','expression',lambda p:4*a(p)*b(p)/((a(p)**2+S(p)**2)*(b(p)**2+S(p)**2)))
# PDE: 구간/시간과 호환되는 초기/경계 자료를 구성한다.
reg('heat_equation_solving','0<x<π,t≥0에서 u_t={{ b }}u_xx, u(0,t)=u(π,t)=0, u(x,0)={{ a }}sin({{ n }}x)의 해를 구하시오.','expression',heat,residual=lambda p,q:[sp.diff(q,t(p))-b(p)*sp.diff(q,x(p),2),q.subs(t(p),0)-a(p)*sp.sin(n(p)*x(p)),q.subs(x(p),0),q.subs(x(p),sp.pi)])
reg('eigenfunction_expansion_solving','열방정식 u_t={{ b }}u_xx의 한 고유함수 초기자료 {{ a }}sin({{ n }}x), 구간(0,π), 영 Dirichlet 경계의 해를 구하시오.','expression',heat)
reg('wave_equation_solving','0<x<π에서 u_tt={{ b*b }}u_xx, 영 Dirichlet 경계, u(x,0)={{ a }}sin({{ n }}x), u_t(x,0)=0의 해를 구하시오.','expression',wave,residual=lambda p,q:[sp.diff(q,t(p),2)-b(p)**2*sp.diff(q,x(p),2),q.subs(t(p),0)-a(p)*sp.sin(n(p)*x(p)),sp.diff(q,t(p)).subs(t(p),0),q.subs(x(p),0),q.subs(x(p),sp.pi)])
reg('separation_of_variables_solving','u_t={{ b }}u_xx, 0<x<π, 영 Dirichlet 경계이다. n={{ n }} 분리해의 T(0)=1인 시간인자 T(t)를 구하시오.','expression',lambda p:sp.exp(-b(p)*n(p)**2*t(p)))
reg('sturm_liouville_analysis','-X″=λX, X(0)=X({{ a }}π)=0의 n={{ n }}번째 고윳값을 구하시오.','expression',lambda p:(n(p)/a(p))**2)
reg('boundary_condition_identification','끝점의 경계조건(mode={{ n }}). mode 1: u={{ a }}, mode 2: u_x={{ a }}, mode 3: u+u_x={{ a }}. 경계조건을 Dirichlet/Neumann/Robin 중 분류하시오.','string',lambda p:['Dirichlet','Neumann','Robin'][int(n(p))-1])
reg('pde_classification','u_xx+({{ k }})*{{ a }}u_yy=0을 elliptic/hyperbolic으로 분류하시오.','string',lambda p:'elliptic' if k(p)>0 else 'hyperbolic')
reg('laplace_poisson_analysis','단위 정사각형에서 Δu=2({{ a+b }}), 경계값 u={{ a }}x²+{{ b }}y²이다. u(x,y)를 구하시오.','expression',lambda p:a(p)*x(p)**2+b(p)*y(p)**2)
reg('steady_transient_analysis','막대 0≤x≤{{ b }}, 열방정식의 끝 온도 u(0,t)=0,u({{ b }},t)={{ a }}이다. 정상상태 온도 u_s(x)를 구하시오.','expression',lambda p:a(p)*x(p)/b(p))
# 복소 해석: w는 복소 변수; a,b,c,n은 양의 정수.
reg('complex_form_conversion','복소수 {{ a }}+i{{ b }}를 r*exp(iθ) 극형식으로 바꾸되 (r,θ)를 열행렬로 쓰시오. θ는 주편각이다.','expression',lambda p:V(sp.sqrt(a(p)**2+b(p)**2),sp.atan(b(p)/a(p))))
reg('demoivre_power_calculation','(cos(π/2)+i sin(π/2))^{{ n }}을 직교형식으로 구하시오.','expression',lambda p:sp.I**n(p))
reg('complex_elementary_function_calculation','exp({{ a }}+iπ) 값을 구하시오.','expression',lambda p:-sp.exp(a(p)))
reg('complex_limit_evaluation','lim[w→{{ b }}] (w^{{ n }}-{{ b**n }})/(w-{{ b }})를 구하시오.','expression',lambda p:n(p)*b(p)**(n(p)-1))
reg('analyticity_verification','f(w)=w^{{ n }}+{{ a }}*conjugate(w)는 복소평면 전체에서 해석적인가?','boolean',lambda p:False)
reg('cauchy_riemann_verification','u(x,y)={{ a }}x²-{{ a }}y², v(x,y)=({{ k }})*2*{{ a }}xy는 R² 전체에서 Cauchy–Riemann 방정식을 만족하는가?','boolean',lambda p:k(p)==1)
reg('harmonic_conjugate_calculation','u={{ a }}(x²-y²)의 조화켤레 v(x,y)를 v(0,0)=0으로 구하시오. f=u+iv 관례이다.','expression',lambda p:2*a(p)*x(p)*y(p))
reg('complex_line_integral_calculation','직선경로 w:0→{{ a }}+i{{ b }}를 따라 ∫w dw를 구하시오.','scalar',lambda p:(a(p)+sp.I*b(p))**2/2)
reg('cauchy_theorem_application','양의 방향 단위원에서 ∮{{ a }}w^{{ n }} dw를 구하시오.','scalar',lambda p:sp.Integer(0))
reg('cauchy_integral_formula_calculation','양의 방향 |w|=2에서 ∮{{ a }}/w dw를 구하시오.','expression',lambda p:2*sp.pi*sp.I*a(p))
reg('laurent_series_calculation','f(w)={{ a }}/w+{{ b }}+{{ c }}w의 0<|w|<1 Laurent 다항식을 쓰시오.','expression',lambda p:a(p)/w(p)+b(p)+c(p)*w(p))
reg('singularity_classification','f(w)={{ a }}/w^{{ n }}의 w=0 특이점을 분류하시오. 답 형식은 pole:N이다(N은 차수).','string',lambda p:'pole:'+str(n(p)))
reg('residue_theorem_calculation','양의 방향 단위원에서 ∮{{ a }}/w dw를 residue 정리로 구하시오.','expression',lambda p:2*sp.pi*sp.I*a(p))
# 수치해석: 반복 횟수/초깃값/노름 및 오차 정의를 고정한다.
reg('error_calculation','정확값 {{ a }}/{{ b }}, 근삿값 ({{ a }}/{{ b }})+1/{{ c }}의 절대오차를 구하시오.','scalar',lambda p:1/c(p))
reg('bisection_iteration','f(x)=x²-{{ a }}, 초기구간[0,{{ a+1 }}]에서 이분법의 첫 평가점 c0를 구하시오.','scalar',lambda p:(a(p)+1)/2)
reg('newton_method_calculation','f(x)=x²-{{ a }}, x0={{ b }}의 Newton 첫 반복 x1을 구하시오.','scalar',lambda p:(b(p)+a(p)/b(p))/2)
reg('secant_method_calculation','f(x)=x²-{{ a }}, x0=0,x1={{ b }}의 할선법 첫 새 반복 x2를 구하시오.','scalar',lambda p:a(p)/b(p))
reg('fixed_point_iteration_calculation','g(x)=(x+{{ a }})/2, x0={{ b }}일 때 고정점 반복 x1=g(x0)를 구하시오.','scalar',lambda p:(a(p)+b(p))/2)
reg('numerical_differentiation_calculation','f(x)={{ a }}x², x={{ b }}, h=1/{{ c }}의 중앙차분 [f(x+h)-f(x-h)]/(2h)를 구하시오.','scalar',lambda p:2*a(p)*b(p))
reg('trapezoidal_rule_calculation','f(x)={{ a }}x²를 [0,{{ b }}]에서 한 패널 사다리꼴 공식으로 적분 근사하시오.','scalar',lambda p:a(p)*b(p)**3/2)
reg('simpson_rule_calculation','f(x)={{ a }}x²를 [0,{{ b }}]에서 2개 하위구간 Simpson 공식으로 적분 근사하시오.','scalar',lambda p:a(p)*b(p)**3/3)
reg('euler_method_calculation',"y'={{ a }}y,y(0)={{ b }}, h=1/{{ c }}의 명시 Euler 첫 단계 y1을 구하시오.",'scalar',lambda p:b(p)*(1+a(p)/c(p)))
reg('runge_kutta_calculation',"y'={{ a }}t,y(0)={{ b }}, h=1/{{ c }}의 고전 RK4 첫 단계 y1을 구하시오.",'scalar',lambda p:b(p)+a(p)/(2*c(p)**2))
reg('lagrange_interpolation_calculation','점 (0,{{ a }}),(1,{{ a+b+c }}),(2,{{ a+2*b+4*c }})의 Lagrange 보간다항식 p(x)를 구하시오.','expression',lambda p:a(p)+b(p)*x(p)+c(p)*x(p)**2)
reg('newton_divided_difference_calculation','점 (0,{{ a }}),(1,{{ a+b+c }}),(2,{{ a+2*b+4*c }})의 Newton 차분 보간다항식 p(x)를 구하시오.','expression',lambda p:a(p)+b(p)*x(p)+c(p)*x(p)**2)
reg('interpolation_error_analysis','f(x)={{ a }}x²의 0,1 선형보간값 p(1/2)와 실제 f(1/2)의 절대오차를 구하시오.','scalar',lambda p:a(p)/4)
reg('least_squares_calculation','점 (0,{{ a-b }}),(1,{{ a }}),(2,{{ a+b }})의 절편 포함 OLS 직선 yhat(x)를 구하시오.','expression',lambda p:a(p)-b(p)+b(p)*x(p))
reg('gaussian_elimination_solving','[[1,{{ a }}],[0,1]]u=({{ b }},{{ c }})를 푸시오. 답은 열벡터이다.','vector',lambda p:V(b(p)-a(p)*c(p),c(p)))
reg('lu_decomposition_calculation','A=[[1,{{ a }}],[{{ b }},{{ a*b+c }}]]의 대각원소1인 L을 갖는 LU 분해를 [L|U]로 쓰시오.','matrix',lambda p:sp.Matrix([[1,0,1,a(p)],[b(p),1,0,c(p)]]))
reg('iterative_solver_calculation','A=[[{{ a+1 }},1],[1,{{ b+1 }}]], rhs=({{ b }},{{ c }}), x0=(0,0)의 Jacobi 첫 반복을 구하시오.','vector',lambda p:V(b(p)/(a(p)+1),c(p)/(b(p)+1)))
reg('condition_number_calculation','A=diag({{ a }},{{ b }})의 2-노름 조건수 κ2를 구하시오.','scalar',lambda p:max(a(p),b(p))/min(a(p),b(p)))
reg('finite_difference_solving','u″=0, 0≤x≤1, u(0)=0,u(1)={{ a }}, h=1/3에서 중앙차분 내부값 (u1,u2)를 구하시오.','vector',lambda p:V(a(p)/3,2*a(p)/3))


# 단일 계수/주파수만 쓰는 유형도 서로 다른 Preview 10개를 만들 수 있게 한다.
# 질문 번호를 붙이지 않고 실제 방정식·경계값·지연 시간·주파수를 변화시킨다.
for _name in ('autonomous_stability_analysis','dirac_delta_laplace','generalized_eigenvector_solving',
              'complex_elementary_function_calculation','boundary_condition_identification','pde_classification'):
    PROFILES[_name]['parameters']['a']['max']=20
for _name in ('fundamental_frequency_calculation','demoivre_power_calculation'):
    PROFILES[_name]['parameters']['n']['max']=20
for _name in ('euler_cauchy_solving','variation_of_parameters_solving','characteristic_equation_setup',
              'homogeneous_ode_solution_construction','bisection_iteration','interpolation_error_analysis',
              'finite_difference_solving','s_differentiation_calculation','laplace_definition_check',
              'harmonic_conjugate_calculation','cauchy_riemann_verification','residue_theorem_calculation',
              'cauchy_integral_formula_calculation','stokes_theorem_calculation',
              'conservative_field_verification','divergence_theorem_calculation'):
    PROFILES[_name]['parameters']['a']['max']=20
PROFILES['fourier_transform_calculation']['parameters']['b']['max']=8
PROFILES['sturm_liouville_analysis']['parameters']['a']['max']=8
PROFILES['sturm_liouville_analysis']['parameters']['n']['max']=8


def checked_parameters(parameters,operation):
    if operation not in PROFILES:raise ValueError('미구현 공학수학 유형: '+str(operation))
    if not isinstance(parameters,dict):raise ValueError('매개변수 객체 필요')
    for name,spec in PROFILES[operation]['parameters'].items():
        value=parameters.get(name)
        if isinstance(value,bool) or not isinstance(value,(int,sp.Integer)):raise ValueError('정수 매개변수 필요: '+name)
        if not spec['min']<=value<=spec['max'] or spec.get('choices') and value not in spec['choices']:raise ValueError('매개변수 범위 위반: '+name)
    for name in SYMBOLS:
        if not isinstance(parameters.get(name),sp.Symbol):raise ValueError('기호 필요: '+name)
    return parameters


def calculate(parameters,operation):
    p=checked_parameters(parameters,operation);answer=CALCULATORS[operation](p)
    if isinstance(answer,sp.Basic) and answer.has(sp.nan,sp.zoo,sp.Integral,sp.Derivative,sp.Sum):raise ValueError('미완료/비유한 정답')
    return answer


def equivalent(answer,expected):
    """구조를 먼저 검사하고 수학적 동치성을 판정한다. 문자열 수식은 실행하지 않는다."""
    if isinstance(expected,str):return isinstance(answer,str) and answer==expected
    if isinstance(expected,(bool,sp.logic.boolalg.BooleanAtom)):return isinstance(answer,(bool,sp.logic.boolalg.BooleanAtom)) and bool(answer)==bool(expected)
    if isinstance(expected,sp.MatrixBase):return isinstance(answer,sp.MatrixBase) and answer.shape==expected.shape and all(sp.simplify(a-b)==0 for a,b in zip(answer,expected))
    if isinstance(expected,list):return isinstance(answer,list) and len(answer)==len(expected) and all(equivalent(a,b) for a,b in zip(answer,expected))
    if isinstance(answer,bool) or not isinstance(answer,(int,float,sp.Expr)):return False
    if set(getattr(answer,'free_symbols',set()))-expected.free_symbols:return False
    return sp.simplify(answer-expected)==0


def validate(answer,parameters,config):
    operation=config.get('operation');p=checked_parameters(parameters,operation)
    if operation in RESIDUALS:
        if isinstance(answer,bool) or not isinstance(answer,sp.Expr):return False
        if answer.free_symbols-set(p[q] for q in SYMBOLS):return False
        return all(sp.simplify(r)==0 for r in RESIDUALS[operation](p,answer))
    return equivalent(answer,calculate(p,operation))
