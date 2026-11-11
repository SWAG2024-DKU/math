"""미분 생성 흐름의 실제 문제와 정답을 검사한다."""
from copy import deepcopy
import json
from pathlib import Path
import pytest
import sympy as sp
from app.schemas.generation_rule import GenerationRuleCatalog
from app.problems.problem_type_extractor import extract_from_directory
from app.problems.template_builder import build_template
from scripts.problems.calculus_1.migrate_calculus_power_rule import migrate_catalog
from scripts.problems.common.problem_instance_generator import generate_problem_instance, _subject_answer_grade, ProblemGenerationError
from scripts.problems.common import parameter_sampler
ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def template():
    raw=json.loads((ROOT/'data/generation_rules/calculus_1.json').read_text(encoding='utf-8'))
    updated,_=migrate_catalog(raw)
    rule=next(r for r in GenerationRuleCatalog.model_validate(updated).rules if r.problem_type=='power_rule_application')
    item=next(v for v in extract_from_directory(ROOT/'data/concepts') if v.subject_id=='calculus_1' and v.problem_type==rule.problem_type)
    return build_template(item,rule)

@pytest.mark.parametrize('seed',range(40))
def test_polynomial_generation(template,seed):
    result=generate_problem_instance(template,seed=seed,max_attempts=3)
    assert result.seed==seed
    payload=result.instance
    assert payload['publishable'] is False
    assert payload['template_status']=='draft'
    f=parameter_sampler.sample_parameters(template.parameters,seed=seed)['f']
    x=sp.Symbol('x',real=True)
    polynomial=sp.Poly(f,x)
    expected=sum(coefficient*power[0]*x**(power[0]-1) for power,coefficient in polynomial.terms() if power[0])
    actual=sp.sympify(payload['expected_answer'],locals={'x':x})
    assert sp.expand(actual-expected)==0
    assert all(v['passed'] for v in payload['validation_trace']['validators'])


def test_template_status_and_config(template):
    assert template.status=='draft' and template.executable
    assert template.metadata.review_status=='not_reviewed'
    assert template.validation.validators[0].config['order']==1
    assert template.solution_spec.primary_formula_id=='power_rule'


def test_migration_preserves_other_rules_and_human_changes():
    raw=json.loads((ROOT/'data/generation_rules/calculus_1.json').read_text(encoding='utf-8'))
    trial=deepcopy(raw)
    target=next(r for r in trial['rules'] if r['problem_type']=='power_rule_application')
    target.update(status='draft_auto',executable=False,notes='마이그레이션 전 원본')
    updated,changed=migrate_catalog(trial)
    assert changed
    before={r['problem_type']:r for r in trial['rules']}
    for rule in updated['rules']:
        if rule['problem_type']!='power_rule_application': assert rule==before[rule['problem_type']]
    after,changed=migrate_catalog(updated)
    assert not changed and after==updated
    next(r for r in after['rules'] if r['problem_type']=='power_rule_application')['parameter_spec']['f']['degree_max']=2
    retained,changed=migrate_catalog(after)
    assert not changed and retained==after

@pytest.mark.parametrize('answer',[1/sp.Symbol('x',real=True),sp.sqrt(2),sp.sin(sp.Symbol('x',real=True)),sp.pi])
def test_symbolic_answers_allowed(template,answer):
    assert _subject_answer_grade(template,answer,integer_answers_only=False,max_fraction_part=99)[0] is None


def test_fraction_bound(template):
    assert _subject_answer_grade(template,sp.Rational(1156,583),integer_answers_only=False,max_fraction_part=99)[0] is not None


def test_symbol_mismatch_fails(template):
    changed=template.model_copy(deep=True)
    changed.symbols['x'].assumptions={'positive':True}
    with pytest.raises(ProblemGenerationError,match='가정 불일치'):
        generate_problem_instance(changed,seed=17,max_attempts=1)


def test_subject_preview_draft_option_and_folder(template,tmp_path,monkeypatch):
    from scripts.problems.common import save_problem_previews as preview
    folder=tmp_path/'templates'
    folder.mkdir()
    path=folder/'calculus.power_rule__power_rule_application.json'
    path.write_text(template.model_dump_json(),encoding='utf-8')
    def generate(template_bytes,seed,max_attempts,timeout_seconds):
        from app.schemas.problem_template import ProblemTemplate
        result=generate_problem_instance(ProblemTemplate.model_validate_json(template_bytes),seed=seed,max_attempts=max_attempts)
        return result.instance,result.seed,len(result.attempts)
    monkeypatch.setattr(preview,'_generate_bounded',generate)
    _,skipped=preview.save_subject_previews(folder,tmp_path/'output',subject_id='calculus_1',problem_type='power_rule_application',count=3)
    assert skipped['skipped']==1 and skipped['completed']==0
    directory,result=preview.save_subject_previews(folder,tmp_path/'output',subject_id='calculus_1',problem_type='power_rule_application',include_draft=True,count=3)
    assert result['completed']==1 and result['errors']==0
    files=list((directory/'power_rule_application').glob('start_*.json'))
    assert len(files)==3
    assert directory.parent.name=='calculus_1'
    for file in files:
        assert json.loads(file.read_text(encoding='utf-8'))['publishable'] is False


def test_legacy_preview_wrapper(monkeypatch):
    from scripts.problems.common import save_problem_previews as preview
    seen={}
    def batch(*args,**kwargs):
        seen.update(kwargs)
        return Path('dummy'),{}
    monkeypatch.setattr(preview,'save_subject_previews',batch)
    preview.save_all_linear_algebra_previews(Path('a'),Path('b'),count=10)
    assert seen['subject_id']=='linear_algebra' and seen['count']==10
