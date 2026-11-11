"""미적분 1의 거듭제곱 미분 Rule 하나만 반복 가능하게 보완한다.

--check로 확인한 뒤 옵션 없이 실행한다. 다른 Rule은 보존한다.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from uuid import uuid4
from app.schemas.generation_rule import GenerationRuleCatalog
from scripts.problems.common.generation_rule_validator import ensure_generation_rule_valid
PROJECT_ROOT = Path(__file__).resolve().parents[3]
TYPE = 'power_rule_application'
MARKER = '[polynomial_power_rule_v1]'


def migrate_catalog(raw: dict) -> tuple[dict, bool]:
    if raw.get('subject_id') != 'calculus_1':
        raise ValueError('calculus_1 catalog만 처리합니다.')
    output = deepcopy(raw)
    matches = [r for r in output['rules'] if r['problem_type'] == TYPE]
    if len(matches) != 1:
        raise ValueError('대상 Rule이 정확히 하나여야 합니다.')
    rule = matches[0]
    if MARKER in (rule.get('notes') or ''):
        # 이후 사람이 수정한 값을 재실행으로 덮어쓰지 않는다.
        GenerationRuleCatalog.model_validate(output)
        return output, False
    if rule['status'] != 'draft_auto' or rule.get('executable') is True:
        raise ValueError('이미 구현/검수한 Rule을 자동 덮어쓰지 않습니다.')
    rule.update(
        rule_version='1.1.0', status='curated', executable=True,
        manual_review_required=True, primary_formula_id='power_rule',
        parameter_spec={
            'f': {'type':'expression', 'allowed_families':['polynomial'],
                  'variable':'x', 'degree_min':1, 'degree_max':3,
                  'min':-3, 'max':3, 'element_type':'integer',
                  'description':'작은 정수 계수의 1~3차 다항함수'},
            'domain': {'type':'interval','lower':-5,'upper':5},
        },
        symbol_spec={'x': {'role':'independent_variable','assumptions':{'real':True}}},
        constraints=[{'type':'domain_condition','expression':'is_defined_on_domain(f,x,domain)',
                      'required':True,'description':'다항함수의 정의역을 검사한다.'}],
        construction={
            'operation':TYPE,'required_objects':['f','x'],
            'semantic_structure':['각 항에 거듭제곱 미분 법칙을 적용한다.'],
            'text_templates':["다음 다항함수의 도함수 f'(x)를 구하시오.\nf(x) = {{ f }}"],
            'latex_templates':["다항함수 \\(f(x)={{ f }}\\)의 도함수를 구하시오."],
            'builder_expression':'f',
        },
        answer_spec={'answer_type':'expression','engine':'sympy','expression':'diff(f,x)',
                     'latex_expression':None,'canonicalization':'simplify'},
        validation={'validators':['derivative_check'],
                    'validator_configs':{'derivative_check':{'function_key':'f','variable_key':'x','order':1}},
                    'all_required':True,'max_generation_attempts':20},
        notes=MARKER+' 정수 지수 다항식 실행 계약 구현. 사람 검수 전이므로 manual_review_required=True. '+(rule.get('notes') or ''),
    )
    parsed = GenerationRuleCatalog.model_validate(output)
    target = next(r for r in parsed.rules if r.problem_type == TYPE)
    ensure_generation_rule_valid(target)
    return output, output != raw


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rule-file',type=Path,default=PROJECT_ROOT/'data/generation_rules/calculus_1.json')
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    path=args.rule_file if args.rule_file.is_absolute() else PROJECT_ROOT/args.rule_file
    raw=json.loads(path.read_text(encoding='utf-8'))
    output,changed=migrate_catalog(raw)
    print(f'calculus_1/{TYPE}: '+('변경 필요' if changed else '변경 없음'))
    if args.check or not changed: return 0
    backup=path.with_name(path.name+'.before-power-rule.'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:8]+'.bak')
    backup.write_bytes(path.read_bytes())
    temp=path.with_name(path.name+'.'+uuid4().hex+'.tmp')
    temp.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    temp.replace(path)
    print(f'수정 완료: {path}\n백업: {backup}')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
