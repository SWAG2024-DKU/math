"""미적분 1의 제한된 관계형 문제를 원본 매개변수에서 계산하고 검사한다."""
import sympy as sp
from scripts.problems.common.constraint_evaluator import is_defined_on_domain

OPERATIONS={'linearization','linear_estimate','secant','tangent','initial_antiderivative',
            'composition','parity','continuous_at','differentiable_at','limit_exists',
            'area_between','cross_section_volume','reversed_integral','disk_volume','washer_volume','consumer_surplus','producer_surplus'}


def calculate(parameters,operation):
    if operation not in OPERATIONS:raise ValueError('미지원 미적분 관계 연산')
    p=parameters
    x=p['x']
    if not isinstance(x,sp.Symbol):raise ValueError('x를 Symbol로 선언해야 합니다.')
    f=p.get('f')
    if f is not None and (not isinstance(f,sp.Expr) or f.has(sp.nan,sp.zoo)):
        raise ValueError('문자열이 아닌 유한한 수식 f가 필요합니다.')
    if operation in {'linearization','linear_estimate','tangent'}:
        point=p['point'];value=f.subs(x,point);slope=sp.diff(f,x).subs(x,point)
        line=value+slope*(x-point)
        if operation=='linearization':return line
        if operation=='linear_estimate':return line.subs(x,p['target'])
        y=p['y']
        if not isinstance(y,sp.Symbol) or y==x:raise ValueError('독립적인 y 기호 필요')
        return sp.Eq(y,line,evaluate=False)
    if operation=='secant':
        point,step=p['point'],p['step']
        if step==0:raise ValueError('차분 구간 길이는 0이 아니어야 합니다.')
        return (f.subs(x,point+step)-f.subs(x,point))/step
    if operation=='initial_antiderivative':
        antiderivative=sp.integrate(f,x)
        return antiderivative-antiderivative.subs(x,p['point'])+p['initial']
    if operation=='composition':
        if not isinstance(p['g'],sp.Expr):raise ValueError('g는 수식이어야 합니다.')
        return sp.expand(f.subs(x,p['g']))
    if operation=='parity':
        even=sp.simplify(f.subs(x,-x)-f)==0
        odd=sp.simplify(f.subs(x,-x)+f)==0
        if even and odd:return '우함수이면서 기함수'
        if even:return '우함수'
        if odd:return '기함수'
        return '둘 다 아님'
    if operation in {'continuous_at','differentiable_at','limit_exists'}:
        point=p['point']
        if operation=='differentiable_at':
            h=sp.Symbol('_h',real=True)
            if f.subs(x,point).is_finite is not True:return False
            quotient=(f.subs(x,point+h)-f.subs(x,point))/h
            left=sp.limit(quotient,h,0,dir='-');right=sp.limit(quotient,h,0,dir='+')
        else:
            left=sp.limit(f,x,point,dir='-');right=sp.limit(f,x,point,dir='+')
        if left.has(sp.Limit) or right.has(sp.Limit):raise ValueError('극한 계산 미완료')
        exists=left.is_finite is True and right.is_finite is True and sp.simplify(left-right)==0
        if operation=='continuous_at':
            value=f.subs(x,point)
            return exists and value.is_finite is True and sp.simplify(left-value)==0
        return exists
    if operation in {'area_between','cross_section_volume'}:
        a,b=p['a'],p['b']
        if a<=0 or b<=0 or p['lower']!=0 or p['upper']!=1:
            raise ValueError('생성 범위/적분 경계/기하 양수 조건 오류')
        original=a*x*(1-x)*(x+b) if operation=='area_between' else a*x**2+b
        if sp.expand(f-original)!=0:raise ValueError('파생 함수가 기하 생성 계약과 다릅니다.')
        if operation=='area_between':return sp.Rational(a*(1+2*b),12)
        return sp.Rational(a,3)+b
    if operation in {'reversed_integral','disk_volume','washer_volume'}:
        lo,hi=(p['lower'],p['upper']) if operation=='reversed_integral' else (p['lower'],p['upper'])
        if not is_defined_on_domain(f,x,sp.Interval(lo,hi)):raise ValueError('적분 구간 정의역 오류')
        if operation=='reversed_integral':return -sp.integrate(f,(x,lo,hi))
        if not f.is_polynomial(x) or sp.degree(f,x)>1:
            raise ValueError('회전체의 현재 생성 계약은 일차 반지름 함수입니다.')
        minimum=sp.Min(f.subs(x,lo),f.subs(x,hi))
        threshold=0 if operation=='disk_volume' else 1
        if (minimum-threshold).is_nonnegative is not True:
            raise ValueError('외반지름/내반지름의 순서 또는 양수 조건 오류')
        if operation=='disk_volume':return sp.pi*sp.integrate(f**2,(x,lo,hi))
        return sp.pi*sp.integrate(f**2-1,(x,lo,hi))
    if operation in {'consumer_surplus','producer_surplus'}:
        a,q=p['a'],p['quantity']
        if a<=0 or q<=0 or (operation=='consumer_surplus' and p['b']-a*q<0):raise ValueError('경제학 문제의 양수/가격 조건 오류')
        return sp.Rational(a*q**2,2)
    raise ValueError('미구현 연산')


def validate(answer,parameters,config):
    from scripts.problems.common.math_validators import _check,equal,boolean,_resolved
    operation=config.get('operation')
    expected=calculate(parameters,operation)
    _resolved(expected)
    if isinstance(expected,bool):return boolean(answer)==expected
    if isinstance(expected,str):return isinstance(answer,str) and answer==expected
    if isinstance(expected,sp.Equality):return _check('equation_equivalence',answer,expected,parameters,config,None)
    if isinstance(answer,str):return False
    if operation=='initial_antiderivative':
        if not isinstance(answer,sp.Expr):return False
        x=parameters['x']
        return equal(sp.diff(answer,x),parameters['f'],config) and equal(answer.subs(x,parameters['point']),parameters['initial'],config)
    return equal(answer,expected,config)
