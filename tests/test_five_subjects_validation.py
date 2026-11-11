"""새 과목의 정답/오답과 잘못된 입력이 실제로 구별되는지 확인한다."""
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import pytest
import sympy as s
from scripts.problems.common import math_validators as m
from app.problems.validator_policy import validate_validator_mapping, RULE_VALIDATORS

x, y, z, t = s.symbols('x y z t', real=True)
u = s.Symbol('s')
region = {'variables': (x,y), 'bounds': ((x,0,2),(y,0,2-x)), 'coordinate_system':'cartesian', 'family':'triangle'}
ode = {'equation':s.Eq(s.diff(s.Function('y')(t),t)+s.Function('y')(t),0), 'variable':t,'function':s.Function('y')(t),'order':1,'initial_conditions':[{'order':0,'point':0,'value':2}], 'family':'linear_constant'}
dist = {'family':'binomial','parameters':{'n':4,'p':s.Rational(1,2)}}
CASES = [
 ('derivative_check','expression',{'f':x**3,'x':x},{},3*x**2,x**2),
 ('derivative_check','scalar',{'f':x**3,'x':x,'point':2},{'point_key':'point'},12,6),
 ('antiderivative_check','expression',{'f':2*x,'x':x,'domain':s.Interval(-2,2)},{'domain_key':'domain'},x*x+7,x**3),
 ('definite_integral_check','scalar',{'f':x*x,'x':x,'lower':0,'upper':3},{},9,3),
 ('limit_check','scalar',{'f':s.sin(x)/x,'x':x,'point':0},{},1,0),
 ('multiple_integral_check','scalar',{'f':x+y,'region':region},{},s.Rational(8,3),4),
 ('gradient_check','vector_expression',{'f':x*x+y*y,'variables':(x,y)},{},s.Matrix([2*x,2*y]),s.Matrix([x,y])),
 ('divergence_check','scalar',{'field':s.Matrix([x,y]),'variables':(x,y)},{},2,1),
 ('curl_check','vector_expression',{'field':s.Matrix([-y,x,0]),'variables':(x,y,z)},{},s.Matrix([0,0,2]),s.zeros(3,1)),
 ('ode_solution_check','equation',{'ode':ode},{},s.Eq(ode['function'],2*s.exp(-t)),s.Eq(ode['function'],3*s.exp(-t))),
 ('laplace_transform_check','expression',{'f':t,'x':t,'s':u},{},1/u**2,1/u),
 ('fourier_transform_check','expression',{'f':s.exp(-t*t),'x':t,'s':u},{},s.sqrt(s.pi)*s.exp(-s.pi**2*u*u),s.exp(-u*u)),
 ('expectation_check','scalar',{'distribution':dist},{},2,3),
 ('variance_check','scalar',{'distribution':dist},{},1,2),
 ('probability_mass_check','scalar',{'distribution':dist,'k':2},{},s.Rational(3,8),s.Rational(1,8)),
 ('sample_statistic_check','scalar',{'data':[1,2,3]},{'statistic':'variance'},1,2),
]
@pytest.mark.parametrize('name,kind,p,c,good,bad',CASES)
def test_correct_and_wrong(name,kind,p,c,good,bad):
    for answer,passed in [(good,True),(bad,False)]:
        result=m.validate_answer(answer,answer_type=kind,validators=[name],parameters=p,config={name:c})
        assert result.passed is passed, result.results

@pytest.mark.parametrize('name,kind,p,c',[
 ('derivative_check','expression',{'f':x,'x':x},{'order':0}),
 ('antiderivative_check','expression',{'f':x,'x':x},{}),
 ('definite_integral_check','scalar',{'f':1/x,'x':x,'lower':-1,'upper':1},{}),
 ('limit_check','scalar',{'f':1/x,'x':x,'point':0},{}),
 ('expectation_check','scalar',{'distribution':{'family':'binomial','parameters':{'n':4,'p':2}}},{}),
 ('sample_statistic_check','scalar',{'data':[1]}, {'statistic':'variance'}),
 ('ode_solution_check','expression',{'ode':{**ode,'initial_conditions':[]}},{}),
 ('derivative_check','expression',{'f':'__import__("os")','x':x},{}),
])
def test_invalid_input_fails(name,kind,p,c):
    assert not m.validate_answer(s.Integer(0),answer_type=kind,validators=[name],parameters=p,config={name:c}).passed

@pytest.mark.parametrize('expression',[
 'definite_integral(f,x,lower,upper)',
 'region_integral(f,region)',
 'expectation(distribution)',
 'solve_initial_ode(ode)',
 'laplace_value(f,x,s)',
])
def test_safe_calculation_helpers(expression):
    values={'f':x*x,'x':x,'lower':0,'upper':3,'region':region,'distribution':dist,'ode':ode,'s':u}
    assert m._evaluate_expression(expression,values) is not None

def test_rule_entrypoint_and_draft_block():
    rule=SimpleNamespace(subject_id='calculus_1',status='curated',executable=True,problem_type='derivative_calculation',answer_spec=SimpleNamespace(answer_type='expression'),validation=SimpleNamespace(validators=['derivative_check']))
    assert m.validate_rule_answer(rule,2*x,{'f':x*x,'x':x}).passed
    rule.status='draft_auto'
    assert not m.validate_rule_answer(rule,2*x,{'f':x*x,'x':x}).passed

def test_type_contract():
    with pytest.raises(ValueError): validate_validator_mapping('matrix',['derivative_check'])

def test_registry_complete():
    assert m._NEW_MATH_VALIDATORS <= m.VALIDATOR_REGISTRY.keys()


def test_series_sum_and_divergence():
    n=s.Symbol('n',integer=True,positive=True)
    for term, good in [(s.Rational(1,2)**n,True),(1/n,False)]:
        sequence={'term':term,'index':n,'start':1,'family':'geometric'}
        result=m.validate_answer(s.Integer(1),answer_type='scalar',validators=['series_sum_check'],parameters={'sequence':sequence})
        assert result.passed is good

def test_strings_cannot_enter_new_cas_functions():
    with pytest.raises(ValueError): m._evaluate_expression('sin(bad)', {'bad':'__import__("os")'})

def test_new_calculation_to_validator_pipeline():
    from app.schemas.problem_template import AnswerTemplateSpec, ValidatorTemplate
    spec=AnswerTemplateSpec.model_validate({'answer_type':'expression','engine':'sympy','cas_template':'diff(f,x)','required_checks':['derivative_check'],'canonicalization':{'method':'simplify'}})
    values={'f':x**3,'x':x}
    answer=m.compute_expected_answer(spec,values)
    report=m.run_math_validators(answer,values,[ValidatorTemplate(name='derivative_check',required=True,config={})],answer_type='expression',required_checks=['derivative_check'])
    assert report.passed, report
