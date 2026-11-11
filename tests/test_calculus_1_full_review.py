"""전체 catalog 검수와 실행 프로필의 정답/오답, 반복 적용 보존 검사."""
from copy import deepcopy
import json
from pathlib import Path
import pytest
import sympy as sp
from app.schemas.problem_template import ProblemTemplate
from scripts.problems.calculus_1.review_calculus_1_rules import inspect_and_apply
from scripts.problems.common.problem_instance_generator import generate_problem_instance,_symbolic_values,_bind_subject_symbols
from scripts.problems.common import parameter_sampler,math_validators
from scripts.problems.calculus_1.calculus_1_rule_profiles import PROFILES
ROOT=Path(__file__).resolve().parents[1]
TYPES=sorted(set(PROFILES)|{'power_rule_application'})

@pytest.fixture(scope='module')
def templates():
    parsed={}
    for path in (ROOT/'data/problem_templates/calculus_1').rglob('*.json'):
        template=ProblemTemplate.model_validate_json(path.read_bytes())
        if template.executable:parsed[template.classification.problem_type]=template
    return parsed

@pytest.mark.parametrize('kind',TYPES)
@pytest.mark.parametrize('seed',[0,17,42])
def test_supported_type_generates(kind,seed,templates):
    result=generate_problem_instance(templates[kind],seed=seed,max_attempts=40)
    assert result.instance['publishable'] is False
    assert result.instance['template_status']=='draft'
    assert all(v['passed'] for v in result.instance['validation_trace']['validators'])

@pytest.mark.parametrize('kind',TYPES)
def test_wrong_answer_rejected(kind,templates):
    template=templates[kind]
    result=generate_problem_instance(template,seed=17,max_attempts=40)
    values=parameter_sampler.sample_parameters(template.parameters,seed=result.seed)
    symbols=_symbolic_values(template,values)
    values={**_bind_subject_symbols(values,symbols),**symbols}
    answer=math_validators.compute_expected_answer(template.answer_spec,values)
    name=template.validation.validators[0].name
    if isinstance(answer,bool) or answer is sp.true or answer is sp.false:bad=not bool(answer)
    elif isinstance(answer,sp.Set):bad=sp.FiniteSet(100)
    elif isinstance(answer,str):bad='잘못된 분류'
    elif isinstance(answer,sp.Equality):bad=sp.Eq(answer.lhs,answer.rhs+1,evaluate=False)
    elif name=='antiderivative_check' or kind=='trig_substitution_integral_calculation':bad=answer+values['x']
    else:bad=answer+1
    report=math_validators.run_math_validators(bad,values,template.validation.validators,
        answer_type=template.answer_spec.answer_type,required_checks=template.answer_spec.required_checks,
        problem_type=template.classification.problem_type)
    assert not report.passed,kind


def test_all_rules_have_review_and_repeat_is_identical():
    raw=json.loads((ROOT/'data/generation_rules/calculus_1.json').read_text(encoding='utf-8'))
    output,records=inspect_and_apply(raw)
    assert output==raw
    assert len(records)==201
    assert len({r['rule_id'] for r in records})==201
    assert sum(r['result']=='blocked' for r in records)==0
    assert sum(r['executable'] for r in output['rules'])==201
    for record in records:
        if record['result']=='blocked':
            assert record['reason'] and record['runtime_test']=='not_run'


def test_human_edits_not_overwritten():
    raw=json.loads((ROOT/'data/generation_rules/calculus_1.json').read_text(encoding='utf-8'))
    changed=deepcopy(raw)
    target=next(r for r in changed['rules'] if r['problem_type']=='polynomial_differentiation')
    target['parameter_spec']['f']['degree_max']=2
    output,records=inspect_and_apply(changed)
    assert output==changed
    assert next(r for r in records if r['problem_type']=='polynomial_differentiation')['result']=='preserved_existing'


def test_classification_and_differentiability_both_cases():
    from scripts.problems.calculus_1.calculus_1_operations import calculate
    x=sp.Symbol('x',real=True)
    assert calculate({'x':x,'f':x*x},'parity')=='우함수'
    assert calculate({'x':x,'f':x**3},'parity')=='기함수'
    assert calculate({'x':x,'f':x*x+x},'parity')=='둘 다 아님'
    assert not calculate({'x':x,'f':sp.Abs(x),'point':0},'differentiable_at')
    assert calculate({'x':x,'f':sp.Abs(x),'point':1},'differentiable_at')


def test_fixed_manual_answers_for_relations():
    from scripts.problems.calculus_1.calculus_1_operations import calculate,validate
    x,y=sp.symbols('x y',real=True)
    assert calculate({'x':x,'f':x**2,'point':1},'linearization')==2*x-1
    assert calculate({'x':x,'y':y,'f':x**2,'point':1},'tangent')==sp.Eq(y,2*x-1)
    assert calculate({'x':x,'f':x,'lower':0,'upper':2},'disk_volume')==sp.Rational(8,3)*sp.pi
    assert calculate({'x':x,'f':x+1,'lower':0,'upper':1},'washer_volume')==sp.Rational(4,3)*sp.pi
    assert calculate({'x':x,'a':2,'b':10,'quantity':3},'consumer_surplus')==9
    p={'x':x,'f':2*x,'point':0,'initial':3}
    assert validate(x**2+3,p,{'operation':'initial_antiderivative'})
    assert not validate(x**2+4,p,{'operation':'initial_antiderivative'})


def test_geometric_conditions_do_not_pass_signed_integrals():
    from scripts.problems.calculus_1.calculus_1_operations import calculate
    x=sp.Symbol('x',real=True)
    with pytest.raises(ValueError): calculate({'x':x,'f':sp.Integer(0),'lower':0,'upper':1},'washer_volume')
    with pytest.raises(ValueError): calculate({'x':x,'a':-1,'b':1,'f':-x*(1-x)*(x+1),'lower':0,'upper':1},'area_between')
    assert calculate({'x':x,'a':1,'b':1,'f':x*(1-x)*(x+1),'lower':0,'upper':1},'area_between')==sp.Rational(1,4)
    assert calculate({'x':x,'a':3,'b':2,'f':3*x**2+2,'lower':0,'upper':1},'cross_section_volume')==3
