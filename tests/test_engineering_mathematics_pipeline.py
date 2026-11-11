"""공학수학 전체 유형: 생성 연결, 오답, 실제 ODE/PDE 잔차, 수작업 기준 검사."""
import json
from pathlib import Path
import pytest
import sympy as s
from app.schemas.problem_template import ProblemTemplate
from scripts.problems.engineering_math.engineering_mathematics_rule_profiles import PROFILES,SYMBOLS,calculate,validate
from scripts.problems.common.problem_instance_generator import generate_problem_instance

ROOT=Path(__file__).resolve().parents[1]
P={q:s.Symbol(q,real=True) for q in SYMBOLS};P['w']=s.Symbol('w');P.update(a=2,b=3,c=1,n=2,k=-1)
x,y,t,ss=P['x'],P['y'],P['t'],P['s']

@pytest.fixture(scope='module')
def templates():
    result={}
    for path in (ROOT/'data/problem_templates/engineering_mathematics').rglob('*.json'):
        value=ProblemTemplate.model_validate_json(path.read_bytes())
        if value.executable:result[value.classification.problem_type]=value
    assert set(result)==set(PROFILES)
    return result

@pytest.mark.parametrize('name',sorted(PROFILES))
@pytest.mark.parametrize('seed',[0,17,42])
def test_generation(name,seed,templates):
    result=generate_problem_instance(templates[name],seed=seed,max_attempts=40)
    assert result.instance['publishable'] is False
    assert result.instance['template_status']=='draft'
    assert all(v['passed'] for v in result.instance['validation_trace']['validators'])


def wrong(value):
    if isinstance(value,(bool,s.logic.boolalg.BooleanAtom)):return not bool(value)
    if isinstance(value,str):return '오답'
    if isinstance(value,s.MatrixBase):out=value.copy();out[0]+=1;return out
    if isinstance(value,list):return [wrong(value[0]),*value[1:]]
    return value+1

@pytest.mark.parametrize('name',sorted(PROFILES))
def test_wrong_answers_and_range(name):
    answer=calculate(P,name);assert validate(answer,P,{'operation':name})
    assert not validate(wrong(answer),P,{'operation':name})
    with pytest.raises(ValueError):calculate({**P,'a':1000},name)
    with pytest.raises(ValueError):calculate({**P,'a':True},name)

MANUAL={
 'separable_ode_solving':3*s.exp(2*t),
 'linear_ode_solving':s.Rational(3,2)-s.exp(-2*t)/2,
 'bernoulli_ode_solving':1/(1+s.exp(2*t)),
 'exact_integrating_factor_solving':x**s.Rational(-3,5),
 'higher_order_ivp_solving':3*s.cos(2*t)+s.sin(2*t)/2,
 'basic_laplace_calculation':4/ss**3,
 'first_shifting_calculation':3/((ss-2)**2+9),
 'derivative_laplace_transformation':-6/(ss+2),
 'convolution_calculation':3*t**2,
 'matrix_exponential_calculation':s.diag(s.exp(2*t),s.exp(-3*t)),
 'curl_calculation':s.Matrix([0,0,4]),
 'divergence_theorem_calculation':8*s.pi,
 'stokes_theorem_calculation':4*s.pi,
 'complex_fourier_calculation':1-s.Rational(3,2)*s.I,
 'half_range_expansion_calculation':0,
 'parseval_identity_calculation':13,
 'fourier_transform_calculation':12/(4+ss**2),
 'heat_equation_solving':2*s.sin(2*x)*s.exp(-12*t),
 'wave_equation_solving':2*s.sin(2*x)*s.cos(6*t),
 'cauchy_integral_formula_calculation':4*s.pi*s.I,
 'complex_line_integral_calculation':-s.Rational(5,2)+6*s.I,
 'newton_method_calculation':s.Rational(11,6),
 'secant_method_calculation':s.Rational(2,3),
 'simpson_rule_calculation':18,
 'euler_method_calculation':9,
 'runge_kutta_calculation':4,
 'lagrange_interpolation_calculation':2+3*x+x*x,
 'least_squares_calculation':-1+3*x,
 'condition_number_calculation':s.Rational(3,2),
}
@pytest.mark.parametrize('name',sorted(MANUAL))
def test_manual_reference(name):assert validate(s.sympify(MANUAL[name]),P,{'operation':name})


def test_duplicate_roots_and_boundary_conditions():
    p={**P,'a':2,'b':2}
    result=calculate(p,'euler_cauchy_solving')
    assert s.simplify(t*t*s.diff(result,t,2)-3*t*s.diff(result,t)+4*result)==0
    for name in ['heat_equation_solving','wave_equation_solving']:
        assert not validate(calculate(P,name)+1,P,{'operation':name})


def test_numeric_rendering_is_arithmetic(templates):
    result=generate_problem_instance(templates['lagrange_interpolation_calculation'],seed=17)
    p=result.instance['parameters'];a,b,c=map(int,[p['a'],p['b'],p['c']])
    statement=result.instance['statement']
    assert f'(1,{a+b+c})' in statement and f'(2,{a+2*b+4*c})' in statement
