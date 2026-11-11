"""수학적 의미를 지정한 미적분 1 실행 프로필. 이름 유사성으로 자동 매핑하지 않는다.

작은 매개변수로 문제를 생성하며, 지원 범위를 제한한 부분은 question/scope에 쓴다.
한 Concept의 여러 유형에 동일한 문제를 복사하지 않는다.
"""
from copy import deepcopy


def integer(lo=-3,hi=3,exclude=()):
    return {'type':'integer','min':lo,'max':hi,'exclude':list(exclude)}


def expression(text,depends=()):
    return {'type':'expression','variable':'x','derived':{
        'engine':'sympy','expression':text,'depends_on':list(depends)}}


def polynomial():
    return {'type':'expression','variable':'x','allowed_families':['polynomial'],
            'element_type':'integer','degree_min':1,'degree_max':3,'min':-3,'max':3}


def profile(question,formula,expression_text,validator,answer_type='expression',
            parameters=None,config=None,domain=(1,3),scope=''):
    params=deepcopy(parameters or {'f':polynomial()})
    if domain is not None:
        params['domain']={'type':'interval','lower':domain[0],'upper':domain[1]}
    return {'question':question,'formula':formula,'expression':expression_text,
            'validator':validator,'answer_type':answer_type,'parameters':params,
            'config':config or {},'scope':scope,
            'constraints':([{'type':'domain_condition','expression':'is_defined_on_domain(f,x,domain)',
                             'required':True,'description':'질문에서 사용하는 함수의 검사 구간 정의역'}]
                           if domain is not None else [])}


PROFILES={}

def add(name,**kwargs): PROFILES[name]=profile(**kwargs)


def derivative(name,formula,parameters=None,order=1,question=None,point=False,scope=''):
    p=parameters or {'f':polynomial()}
    if point:p={**p,'point':integer(-2,2)}
    config={'order':order}
    if point:config['point_key']='point'
    calc='diff(f,x)' if order==1 else 'diff(diff(f,x),x)'
    if point:
        # 점 대입은 AST 메서드를 개방하지 않고 정식 계산 helper를 쓴다.
        calc=f'derivative_value(f,x,{order},point)'
    add(name,question=question or "함수 f(x)={{ f }}의 도함수를 구하시오.",formula=formula,
        expression_text=calc,validator='derivative_check',parameters=p,config=config,
        answer_type='scalar' if point else 'expression',scope=scope,
        domain=None if point else (1,3))


derivative('polynomial_differentiation','power_rule',scope='1~3차 다항식')
derivative('exponential_derivative_calculation','natural_exponential_derivative',
           {'a':integer(1,3),'b':integer(-2,2),'f':expression('exp(a*x+b)',['a','b'])})
derivative('log_derivative_calculation','log_derivative',
           {'a':integer(1,3),'b':integer(1,3),'f':expression('log(a*x+b)',['a','b'])},scope='x>0에서 자연로그 합성함수')
derivative('trig_derivative_calculation','sin_cos_derivative',
           {'a':integer(1,3),'b':integer(-2,2),'f':expression('sin(a*x)+cos(b*x)',['a','b'])},scope='sin/cos 조합')
derivative('chain_rule_application','chain_rule',
           {'a':integer(1,3),'b':integer(1,3),'f':expression('(a*x**2+b)**2',['a','b'])})
derivative('repeated_chain_rule','chain_rule',
           {'a':integer(1,2),'b':integer(1,2),'f':expression('sin((a*x+b)**2)',['a','b'])},scope='세 함수의 합성')
derivative('product_rule_application','product_rule',
           {'a':integer(1,3),'b':integer(1,3),'f':expression('(a*x+b)*sin(x)',['a','b'])})
derivative('repeated_product_rule','product_rule',
           {'a':integer(1,2),'b':integer(1,2),'f':expression('(a*x+b)*sin(x)*cos(x)',['a','b'])},scope='세 인수의 곱')
derivative('quotient_rule_application','quotient_rule',
           {'a':integer(1,3),'b':integer(1,3),'f':expression('(x**2+a)/(x+b)',['a','b'])},scope='x>0에서 분모가 0이 아닌 유리함수')
derivative('reciprocal_derivative','reciprocal_rule',
           {'a':integer(1,3),'b':integer(1,3),'f':expression('1/(a*x+b)',['a','b'])})
derivative('higher_derivative_calculation','second_derivative',order=2,
           question="f(x)={{ f }}의 이계도함수 f''(x)를 구하시오.",scope='2차 미분')
derivative('position_derivative_interpretation','velocity_acceleration_jerk',order=2,
           question="시간 x에서 위치 s(x)={{ f }}이다. 가속도 함수 s''(x)를 구하시오.",scope='시간 변수 x; 가속도 계산')
derivative('derivative_at_point_calculation','derivative_at_point',point=True,
           question="f(x)={{ f }}의 x={{ point }}에서 미분계수를 구하시오.")
derivative('rate_of_change_interpretation','instantaneous_rate_of_change',point=True,
           question="양 Q(x)={{ f }}의 x={{ point }}에서 순간변화율을 구하시오.")
derivative('instantaneous_velocity_calculation','instantaneous_velocity',point=True,
           question="시간 x에서 위치 s(x)={{ f }}이다. x={{ point }}에서 순간속도를 구하시오.")
derivative('hyperbolic_derivative_calculation','hyperbolic_derivatives',
           {'a':integer(1,3),'f':expression('(exp(a*x)-exp(-a*x))/2',['a'])},
           question="f(x)={{ f }} = sinh({{ a }}x)의 도함수를 구하시오.",scope='sinh의 지수 정의를 사용')
derivative('logarithmic_differentiation_application','logarithmic_differentiation',
           {'a':integer(1,3),'b':integer(2,3),'f':expression('(x+a)**b',['a','b'])},
           question="x>0에서 f(x)={{ f }}이다. 로그 미분법을 사용해 도함수를 구하시오.",scope='양의 함수에서 로그 미분; 최종 답만 검증, 풀이 방법은 사람 검수')


def anti(name,formula,params=None,question=None,scope=''):
    add(name,question=question or 'x>0에서 f(x)={{ f }}의 원시함수 하나를 구하시오. 적분상수는 0으로 선택하시오.',
        formula=formula,expression_text='antiderivative(f,x)',validator='antiderivative_check',
        parameters=params,config={'domain_key':'domain'},scope=scope)

anti('antiderivative_table_lookup','antiderivative_table',scope='다항식 공식표')
anti('indefinite_integral_substitution','substitution_indefinite',
     {'a':integer(1,2),'b':integer(1,2),'f':expression('2*a*x*(a*x**2+b)**2',['a','b'])},scope='u=a*x²+b 치환')
anti('integration_by_parts_application','integration_by_parts',
     {'a':integer(1,3),'f':expression('x*exp(a*x)',['a'])},scope='u=x, dv=exp(a*x)dx')
anti('partial_fraction_integration','partial_fraction_integration',
     {'a':integer(1,3),'f':expression('1/(x*(x+a))',['a'])},scope='x>0의 서로 다른 일차 인수')
anti('trig_power_integral_calculation','sin_cos_power_odd',
     {'a':integer(1,3),'f':expression('sin(x)*cos(x)**a',['a'])},scope='u=cos(x) 치환')
anti('self_referential_integral_solving','integration_by_parts',
     {'a':integer(1,2),'f':expression('exp(a*x)*sin(x)',['a'])},scope='반복 부분적분')
anti('reduction_formula_application','reduction_formula_sin',
     {'n':integer(2,4),'f':expression('sin(x)**n',['n'])},scope='sin의 작은 정수 거듭제곱; 풀이 단계는 사람 검수')


def integral(name,formula,params=None,question=None,scope=''):
    p=deepcopy(params or {'f':polynomial()})
    p.setdefault('lower',{'type':'integer','choices':[0]})
    p.setdefault('upper',{'type':'integer','choices':[1]})
    add(name,question=question or '함수 f(x)={{ f }}를 x={{ lower }}부터 {{ upper }}까지 정적분하시오.',
        formula=formula,expression_text='definite_integral(f,x,lower,upper)',
        validator='definite_integral_check',answer_type='scalar',parameters=p,domain=(0,1),scope=scope)

integral('definite_integral_evaluation','ftc2')
integral('definite_integral_substitution','substitution_definite',
         {'a':integer(1,2),'b':integer(1,2),'f':expression('2*a*x*(a*x**2+b)**2',['a','b'])},scope='u=a*x²+b 치환')
integral('displacement_calculation','ftc2',question='시간 x에서 속도 v(x)={{ f }}이다. 시간 0부터 1까지의 변위를 구하시오. 이동 거리는 묻지 않는다.')
integral('net_change_calculation','net_change_theorem',question='시간 x에서 양 Q의 변화율 Q\'(x)={{ f }}이다. 시간 0부터 1까지 Q의 순변화량을 구하시오.')
integral('symmetric_interval_shortcut','symmetric_function_integral',
         {'a':integer(1,3),'b':integer(1,3),'f':expression('a*x**3+b*x**2',['a','b']),
          'lower':{'type':'integer','choices':[-1]},'upper':{'type':'integer','choices':[1]}},scope='[-1,1]의 기함수/우함수 항')
# 위 유형의 정의역 검사는 [-1,1]로 동일하게 맞춘다.
PROFILES['symmetric_interval_shortcut']['parameters']['domain'].update(lower=-1,upper=1)
integral('volume_by_cross_section_calculation','volume_by_cross_section',
         {'a':integer(1,3),'b':integer(1,3),'f':expression('a*x**2+b',['a','b'])},
         question='0≤x≤1에서 x축에 수직인 단면의 넓이가 A(x)={{ f }}인 입체의 부피를 구하시오.',scope='단면 넓이 함수가 문제에 주어짐')
integral('area_between_curves_calculation','area_between_curves',
         {'a':integer(1,3),'f':expression('a*x*(1-x)',['a'])},
         question='0≤x≤1에서 y={{ f }}와 y=0 사이의 넓이를 구하시오.',scope='구간 내 위/아래 순서가 보장됨')


def limit_profile(name,formula,params,point=0,direction='+-',question=None,scope=''):
    p=deepcopy(params);p['point']={'type':'integer','choices':[point]}
    add(name,question=question or 'f(x)={{ f }}일 때 x→{{ point }}에서 함수의 극한을 구하시오.',
        formula=formula,expression_text=f"limit_value(f,x,point,'{direction}')",validator='limit_check',
        answer_type='scalar',parameters=p,config={'direction':direction},domain=None,scope=scope)

limit_profile('direct_substitution_limit','direct_substitution',{'f':polynomial()},point=1)
limit_profile('limit_law_application','sum_difference_law',
              {'a':integer(-3,3),'b':integer(-3,3),'f':expression('a*x**2+b*x+1',['a','b'])},point=2)
limit_profile('indeterminate_form_resolution','local_agreement',
              {'a':integer(1,3),'f':expression('(x**2-a**2)/(x-a)',['a'])},point=0,
              question='f(x)={{ f }}일 때 x→0의 극한을 구하시오.',scope='현재 프로필은 재검수 필요')
# 실제 0/0 지점이 반드시 명시되도록 고정 위치 1, 매개변수 a는 계수로만 쓴다.
PROFILES['indeterminate_form_resolution']['parameters']={'a':integer(1,3),'f':expression('a*(x**2-1)/(x-1)',['a']),'point':{'type':'integer','choices':[1]}}
PROFILES['indeterminate_form_resolution']['question']='x≠1에서 f(x)=a(x²-1)/(x-1), a={{ a }}이다. x→1의 극한을 구하시오.'
PROFILES['indeterminate_form_resolution']['scope']='약분 전 원식과 삭제된 점을 문제 문장에 명시'
limit_profile('trig_limit_via_substitution','special_trig_limits',
              {'a':integer(1,3),'f':expression('sin(a*x)/x',['a'])})
limit_profile('one_sided_limit_calculation','right_limit',
              {'a':integer(1,3),'f':expression('a*Abs(x)/x',['a'])},direction='+',
              question='f(x)={{ f }}일 때 x→0+의 우극한을 구하시오.')
limit_profile('lhopital_application','lhopital_rule',
              {'a':integer(1,3),'f':expression('(exp(a*x)-1)/x',['a'])},
              question='f(x)={{ f }}의 x→0 극한을 로피탈 법칙으로 구하시오.',scope='0/0 꼴; 최종 값만 검증')

# 기하급수: 수렴하는 공비만 직접 뽑는다. 인덱스와 시작점을 반환하는 샘플러를 사용한다.
add('geometric_series_sum_calculation',question='n=1부터 무한대까지 일반항 {{ sequence }}의 급수 합을 구하시오.',
    formula='geometric_series',expression_text='series_value(sequence)',validator='series_sum_check',answer_type='scalar',
    parameters={'sequence':{'type':'sequence','allowed_families':['geometric'],'start':1,
                            'ratio_choices':['1/2']}},domain=None,scope='샘플러의 수렴 기하급수족')

# 원본에 실제로 존재하는 공식 ID만 사용한다.
PROFILES['polynomial_differentiation']['formula']='polynomial_derivative'
PROFILES['logarithmic_differentiation_application']['formula']='log_derivative'
PROFILES['partial_fraction_integration']['formula']='partial_fraction_case1'
PROFILES['area_between_curves_calculation']['formula']='area_between_curves_x'
PROFILES['geometric_series_sum_calculation']['formula']='geometric_series_sum'
PROFILES['geometric_series_sum_calculation']['parameters']['sequence'].pop('ratio_choices',None)
# 문자열 식을 파싱하지 않는다. 샘플러의 기본 공비 후보는 모두 절댓값이 1보다 작다.
PROFILES['geometric_series_sum_calculation']['parameters']['sequence'].update(min=-3,max=3)
PROFILES['geometric_series_sum_calculation']['question']='일반항 정보가 {{ sequence }}인 급수의 n=1부터 무한대까지의 합을 구하시오.'
PROFILES['indeterminate_form_resolution']['formula']='direct_substitution' # 실제 Concept에 없으면 적용 단계에서 None으로 보류한다.


def relation(name,operation,question,formula,params,answer_type='expression',scope='',domain=(1,3),symbols=None):
    config={'operation':operation}
    references=','.join(repr(key)+':'+key for key in params)
    # 샘플링하지 않는 x/y도 명시적으로 전달한다.
    references+=",'x':x"
    if symbols and 'y' in symbols:references+=",'y':y"
    add(name,question=question,formula=formula,
        expression_text="calculus_value({"+references+"},'"+operation+"')",
        validator='calculus_relation_check',answer_type=answer_type,
        parameters=params,config=config,scope=scope,domain=domain)
    if symbols:PROFILES[name]['symbols']=symbols

p={'f':polynomial(),'point':{'type':'integer','choices':[0]}}
relation('linearization_construction','linearization','f(x)={{ f }}의 x=0에서 선형화 L(x)를 구하시오.',
         'linearization',p)
relation('linear_approximation_estimation','linear_estimate','f(x)={{ f }}이다. x=0에서 선형화를 이용해 f({{ target }})를 근사하시오.',
         'linear_approximation',{**p,'target':{'type':'rational','min':0,'max':1,'denominator':10}},
         scope='선형화 값의 정확한 유리수 표현; 수치 참값 오차와 구분')
relation('difference_quotient_calculation','secant','f(x)={{ f }}의 x=0과 x={{ step }} 사이 차분몫을 구하시오.',
         'difference_quotient',{'f':polynomial(),'point':{'type':'integer','choices':[0]},'step':integer(1,3)},answer_type='expression',domain=None)
relation('secant_slope_calculation','secant','y={{ f }}에서 x=0과 x={{ step }}의 두 점을 잇는 할선 기울기를 구하시오.',
         'secant_slope',{'f':polynomial(),'point':{'type':'integer','choices':[0]},'step':integer(1,3)},answer_type='scalar',domain=None)
for name,formula in [('tangent_line_derivation','tangent_line_equation'),('tangent_line_via_derivative','tangent_line_at_derivative')]:
    relation(name,'tangent','y={{ f }}의 x=0에서 접선 방정식을 구하시오.',formula,p,answer_type='equation',
             symbols={'x':{'role':'independent_variable','assumptions':{'real':True}},'y':{'role':'unknown','assumptions':{'real':True}}})
relation('initial_value_problem','initial_antiderivative',"F'(x)={{ f }}, F(0)={{ initial }}이다. F(x)를 구하시오.",
         'general_antiderivative',{'f':polynomial(),'point':{'type':'integer','choices':[0]},'initial':integer(-3,3)},scope='다항식 원시함수의 적분상수 결정',domain=None)
relation('composition_evaluation','composition','f(x)={{ f }}, g(x)={{ g }}이다. (f∘g)(x)를 구하시오.',
         'composition',{'f':{**polynomial(),'degree_max':2},'g':{**polynomial(),'degree_max':2}},domain=None)
relation('even_odd_classification','parity','f(x)={{ f }}가 우함수, 기함수, 둘 다 아님 중 어디에 해당하는지 판정하시오.',
         'even_odd_def',{'a':integer(-2,2),'b':integer(-2,2),'f':expression('a*x**2+b*x**3',['a','b'])},answer_type='classification',domain=None,
         scope='영함수는 우함수이면서 기함수이므로 두 계수 모두 0인 경우 제외')
PROFILES['even_odd_classification']['constraints']=[{'type':'nonzero','expression':'a != 0 or b != 0','required':True}]
relation('continuity_check','continuous_at','f(x)={{ f }}는 x={{ point }}에서 연속인가?',
         'continuity_at_a',{'f':polynomial(),'point':integer(-2,2)},answer_type='boolean',domain=None,scope='다항식의 연속성')
relation('differentiability_check','differentiable_at','f(x)=a|x|, a={{ a }}는 x={{ point }}에서 미분가능한가?',
         'derivative_function',{'a':integer(1,3),'point':integer(-1,1),'f':expression('a*Abs(x)',['a'])},answer_type='boolean',domain=None,
         scope='좌우 미분계수의 존재와 일치 검사; True/False 모두 생성')
relation('two_sided_limit_existence_check','limit_exists','f(x)={{ f }}의 x→0 양쪽극한이 유한하게 존재하는가?',
         'two_sided_limit_condition',{'a':integer(-2,2),'f':expression('a*Abs(x)/x',['a']),'point':{'type':'integer','choices':[0]}},answer_type='boolean',domain=None)
relation('limit_existence_reasoning','limit_exists','x≠0에서 f(x)=a|x|/x, a={{ a }}이다. x→0에서 양쪽극한이 유한하게 존재하는가?',
         'limit_notation',{'a':integer(-2,2),'f':expression('a*Abs(x)/x',['a']),'point':{'type':'integer','choices':[0]}},answer_type='boolean',domain=None,
         scope='최종 판정만 자동 검증; 설명은 사람 검수')
relation('orientation_convention_application','reversed_integral','f(x)={{ f }}이다. x=1부터 0까지의 정적분을 구하시오.',
         'integral_orientation',{'f':polynomial(),'lower':{'type':'integer','choices':[0]},'upper':{'type':'integer','choices':[1]}},answer_type='scalar',domain=(0,1))
relation('disk_method_volume','disk_volume','0≤x≤1에서 y={{ f }}와 x축 사이 영역을 x축 둘레로 회전한 부피를 구하시오.',
         'disk_method',{'a':integer(1,3),'b':integer(1,3),'f':expression('a*x+b',['a','b'])},answer_type='scalar',domain=(0,1),scope='반지름이 양수인 직선 그래프')
relation('washer_method_volume','washer_volume','0≤x≤1에서 위 곡선 y={{ f }}, 아래 곡선 y=1 사이를 x축 둘레로 회전한 부피를 구하시오.',
         'washer_method',{'a':integer(1,3),'b':integer(2,3),'f':expression('a*x+b',['a','b'])},answer_type='scalar',domain=(0,1),scope='외반지름≥내반지름=1')
relation('consumer_surplus_calculation','consumer_surplus','수요함수 D(q)=10-{{ a }}q, 거래량 Q={{ quantity }}, 시장가격 P=D(Q)이다. 소비자 잉여를 구하시오.',
         'consumer_surplus',{'a':integer(1,3),'quantity':integer(1,3)},answer_type='scalar',domain=None,scope='거래량 구간에서 음수가 아닌 선형 수요')
relation('producer_surplus_calculation','producer_surplus','공급함수 S(q)=1+{{ a }}q, 거래량 Q={{ quantity }}, 시장가격 P=S(Q)이다. 생산자 잉여를 구하시오.',
         'producer_surplus',{'a':integer(1,3),'quantity':integer(1,3)},answer_type='scalar',domain=None,scope='양수인 선형 공급')
PROFILES['continuity_check']['formula']='continuity_definition'
PROFILES['even_odd_classification']['formula']='even_function'
PROFILES['lhopital_application']['formula']='lhopitals_rule'
PROFILES['orientation_convention_application']['formula']='orientation_convention'

# 유형당 10개의 서로 다른 문제를 만들 수 있도록 유한 표본 공간도 점검한다.
for _name,_profile in PROFILES.items():
    _params=_profile['parameters']
    if 'b' in _params and _params['b'].get('min')==1 and _params['b'].get('max')==3:
        _params['b']['max']=4
for _name in ['hyperbolic_derivative_calculation','integration_by_parts_application',
              'partial_fraction_integration','self_referential_integral_solving',
              'reduction_formula_application','trig_power_integral_calculation',
              'indefinite_integral_substitution','definite_integral_substitution',
              'trig_limit_via_substitution','lhopital_application']:
    _params=PROFILES[_name]['parameters']
    _params['scale']=integer(1,6)
    _derived=_params['f']['derived']
    _derived['expression']='scale*('+_derived['expression']+')'
    _derived['depends_on'].append('scale')
PROFILES['hyperbolic_derivative_calculation']['question']='f(x)={{ f }} = {{ scale }} sinh({{ a }}x)의 도함수를 구하시오.'
for _name in ['antiderivative_table_lookup','indefinite_integral_substitution','integration_by_parts_application',
              'partial_fraction_integration','trig_power_integral_calculation','self_referential_integral_solving','reduction_formula_application']:
    PROFILES[_name]['question']='x>0에서 f(x)={{ f }}의 원시함수 하나를 구하시오. 새 기호 적분상수 C 없이 표현하시오.'
PROFILES['area_between_curves_calculation']['parameters'].update(b=integer(1,4),f=expression('a*x*(1-x)*(x+b)',['a','b']))
for _name in ['consumer_surplus_calculation','producer_surplus_calculation']:
    PROFILES[_name]['parameters']['b']=integer(10,12) if _name=='consumer_surplus_calculation' else integer(1,3)
PROFILES['consumer_surplus_calculation']['question']='수요함수 D(q)={{ b }}-{{ a }}q, 거래량 Q={{ quantity }}, 시장가격 P=D(Q)이다. 소비자 잉여를 구하시오.'
PROFILES['producer_surplus_calculation']['question']='공급함수 S(q)={{ b }}+{{ a }}q, 거래량 Q={{ quantity }}, 시장가격 P=S(Q)이다. 생산자 잉여를 구하시오.'
for _name in ['disk_method_volume','washer_method_volume']:
    _p=PROFILES[_name]
    _p['parameters'].update(lower={'type':'integer','choices':[0]},upper=integer(1,2))
    _p['parameters']['domain']['upper']=2
    _p['question']=_p['question'].replace('0≤x≤1','0≤x≤{{ upper }}')
for _name in ['two_sided_limit_existence_check','limit_existence_reasoning']:
    _params=PROFILES[_name]['parameters']
    _params['b']=integer(-2,2)
    _params['f']=expression('a*Abs(x)/x+b',['a','b'])
PROFILES['limit_existence_reasoning']['question']='x≠0에서 f(x)=a|x|/x+b, a={{ a }}, b={{ b }}이다. x→0에서 양쪽극한이 유한하게 존재하는가?'
PROFILES['differentiability_check']['parameters']['a']['max']=4
PROFILES['one_sided_limit_calculation']['parameters'].update(b=integer(-2,2),f=expression('a*Abs(x)/x+b',['a','b']))
PROFILES['indeterminate_form_resolution']['parameters'].update(b=integer(-2,2),f=expression('a*(x**2-1)/(x-1)+b',['a','b']))
PROFILES['indeterminate_form_resolution']['question']='x≠1에서 f(x)=a(x²-1)/(x-1)+b, a={{ a }}, b={{ b }}이다. x→1의 극한을 구하시오.'

for _p in PROFILES.values():
    if _p['validator']=='calculus_relation_check':
        _refs=','.join(repr(key)+':'+key for key in _p['parameters'])+",'x':x"
        if 'y' in _p.get('symbols',{}):_refs+=",'y':y"
        _p['expression']="calculus_value({"+_refs+"},'"+_p['config']['operation']+"')"
for _name in ['repeated_chain_rule','repeated_product_rule']:
    PROFILES[_name]['parameters']['a']['max']=3
    PROFILES[_name]['parameters']['b']['max']=4
PROFILES['logarithmic_differentiation_application']['parameters']['a']['max']=4
PROFILES['logarithmic_differentiation_application']['parameters']['b']['max']=4
PROFILES['trig_derivative_calculation']['parameters']['b']['max']=4

PROFILES['geometric_series_sum_calculation']['question']='수열의 일반항은 {{ sequence }}이다. n=1부터 무한대까지의 급수 합을 구하시오.'
# 넓이와 단면 부피는 부호 있는 적분 값만 비교하지 않고 기하 전제조건도 검사한다.
for _name,_operation in [('area_between_curves_calculation','area_between'),('volume_by_cross_section_calculation','cross_section_volume')]:
    _p=PROFILES[_name]
    _p['validator']='calculus_relation_check'
    _p['config']={'operation':_operation}
    _refs=','.join(repr(key)+':'+key for key in _p['parameters'])+",'x':x"
    _p['expression']="calculus_value({"+_refs+"},'"+_operation+"')"

# 나머지 유형은 별도 모듈로 유지해 기존 56개 계약을 보존한다.
from scripts.problems.calculus_1.calculus_1_remaining_profiles import PROFILES as REMAINING_PROFILES
if set(PROFILES) & set(REMAINING_PROFILES):
    raise ValueError('기존 프로필과 중복된 문제 유형')
PROFILES.update(REMAINING_PROFILES)
