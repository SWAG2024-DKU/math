"""확률통계 23개 Rule 유형의 실제 생성/오답/정규성 전제/정확한 기준 검사."""
from pathlib import Path
import pytest
import sympy as s
from app.schemas.problem_template import ProblemTemplate
from scripts.problems.probability_statistics.probability_statistics_rule_profiles import PROFILES,calculate,validate
from scripts.problems.common.problem_instance_generator import generate_problem_instance
ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def templates():
    out={}
    for file in (ROOT/'data/problem_templates/probability_statistics').rglob('*.json'):
        value=ProblemTemplate.model_validate_json(file.read_bytes())
        if value.executable:out[value.classification.problem_type]=value
    assert set(out)==set(PROFILES)
    return out

@pytest.mark.parametrize('name',sorted(PROFILES))
@pytest.mark.parametrize('seed',[0,17,42])
def test_generation(name,seed,templates):
    result=generate_problem_instance(templates[name],seed=seed,max_attempts=40)
    assert result.instance['publishable'] is False
    assert result.instance['template_status']=='draft'
    assert all(row['passed'] for row in result.instance['validation_trace']['validators'])

@pytest.mark.parametrize('name',sorted(PROFILES))
def test_wrong_answers(name):
    p={q:(spec['choices'][0] if spec.get('choices') else spec['min']) for q,spec in PROFILES[name]['parameters'].items()}
    answer=calculate(p,name);cfg={'operation':name}
    assert validate(answer,p,cfg)
    if isinstance(answer,(bool,s.logic.boolalg.BooleanAtom)):bad=not bool(answer)
    elif isinstance(answer,s.Interval):bad=s.Interval(answer.start-1,answer.end)
    else:bad=answer+1
    assert not validate(bad,p,cfg)
    first=next(iter(p))
    with pytest.raises(ValueError):calculate({**p,first:True},name)

@pytest.mark.parametrize('name,p,expected',[
 ('counting_calculation',{'n':6},15),
 ('confidence_interval',{'a':5,'b':2,'c':4},s.Interval(4,6)),
 ('contingency_table_calculation',{'a':1,'b':2,'c':3,'d':4},s.Rational(6,5)),
 ('effect_measure_interpretation',{'a':2,'b':3,'c':4,'d':5},s.Rational(5,6)),
 ('moment_calculation',{'n':10,'a':2},4),
 ('hypothesis_decision',{'a':1,'b':2,'c':2,'d':2},True),
 ('hypothesis_decision',{'a':1,'b':2,'c':2,'d':1},False),
 ('correlation_calculation',{'a':1,'b':1,'c':1},3*s.sqrt(21)/14),
])
def test_manual_values(name,p,expected):assert validate(s.sympify(expected),p,{'operation':name})
