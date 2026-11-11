"""공학수학 전체 Rule을 검수하고 구현된 유형에만 실행 계약을 적용한다.

기본은 검사만 수행한다. --apply로 적용하며 다른 과목 파일은 쓰지 않는다.
검수 리포트는 모든 Rule을 포함한다. 자동 검사와 사람 검수는 구분한다.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
from collections import Counter
from datetime import datetime,timezone
import json
import hashlib
import re
from pathlib import Path
from uuid import uuid4
from app.schemas.generation_rule import GenerationRuleCatalog
from app.problems.validator_policy import ALLOWED_VALIDATORS
from scripts.problems.engineering_math.engineering_mathematics_rule_profiles import PROFILES
from scripts.problems.common.generation_rule_validator import validate_generation_rule,ensure_generation_rule_valid

ROOT=Path(__file__).resolve().parents[3]
MARKER='[engineering_mathematics_execution_v1]'
CONTRACT_FIELDS=('status','executable','manual_review_required','rule_version','primary_formula_id',
                 'parameter_spec','symbol_spec','constraints','construction','answer_spec','validation')


def contract_hash(rule):
    contract={key:rule.get(key) for key in CONTRACT_FIELDS}
    return hashlib.sha256(json.dumps(contract,sort_keys=True,ensure_ascii=False).encode()).hexdigest()



def blocked_reason(name):
    if any(word in name for word in ('proof','reasoning','theorem_application','test_selection','strategy_selection','method_selection','formulation','sketch','identification','construction','classification')):
        return '판정/풀이/설정 문제의 유형별 답 형식과 전제조건 검증을 별도로 구현해야 함'
    if any(word in name for word in ('series','sequence','ratio_test','root_test','comparison_test')):
        return '수렴/발산/조건수렴과 판정법 적용 조건을 검사하는 전용 계약 필요'
    if any(word in name for word in ('polar','parametric','conic','implicit','related_rates')):
        return '다변수/곡선 기하 조건과 유일한 답의 범위를 검사하는 전용 계약 필요'
    if any(word in name for word in ('improper','infinite','asymptote','infinity')):
        return '특이점/무한 구간/무한 결과를 구분하는 전용 계산 및 답 표현 정책 필요'
    if any(word in name for word in ('numeric','estimation','approximation','cardiac')):
        return '표본/수치적분/오차 허용 범위와 단위가 명시된 전용 계약 필요'
    return '해당 문제 의도를 보존하는 전용 생성/검증 계약이 아직 없음'


def inspect_and_apply(raw):
    if raw.get('subject_id')!='engineering_mathematics':raise ValueError('engineering_mathematics만 처리합니다.')
    output=deepcopy(raw);records=[]
    for original,rule in zip(raw['rules'],output['rules']):
        name=rule['problem_type'];profile=PROFILES.get(name)
        issues=[]
        if original['status']=='draft_auto' and original.get('executable') is True:issues.append('draft_auto/executable=True 모순')
        if not original['answer_spec'].get('expression'):issues.append('정답 계산식 누락')
        invalid=set(original['validation']['validators'])-ALLOWED_VALIDATORS.get(original['answer_spec']['answer_type'],set())
        if invalid:issues.append('답 유형과 맞지 않는 Validator: '+','.join(sorted(invalid)))
        if any(spec.get('type')=='symbolic_input' for spec in original['parameter_spec'].values()):issues.append('symbolic_input 미구현')
        if not original['construction'].get('builder_expression'):issues.append('문제 입력 조립식 누락')
        if any("'" in text and '문제를 해결하시오' in text for text in original['construction'].get('text_templates',[])):issues.append('유형 이름만 있는 일반 문제 문장')
        record={'rule_id':rule['rule_id'],'problem_type':name,'original_issues':issues,
                'human_review':'required','runtime_test':'not_run',
                'source_concept_ids':rule['source_concept_ids'],
                'original_question_intent':original['construction']['semantic_structure'],
                'original_answer_type':original['answer_spec']['answer_type'],
                'original_parameter_types':{k:v['type'] for k,v in original['parameter_spec'].items()},
                'source_formula_ids':original['source_formula_ids']}
        stored_hash=re.search(r'contract_sha256:([0-9a-f]{64})',rule.get('notes') or '')
        changed_by_owner=stored_hash is not None and stored_hash.group(1)!=contract_hash(rule)
        if changed_by_owner or (rule['status'] in {'curated','reviewed'} and rule.get('executable') and MARKER not in (rule.get('notes') or '')):
            record.update(result='preserved_existing',scope='기존 구현 계약 보존',reason='이전 단계/팀원의 구현을 덮어쓰지 않음')
        elif profile is None:
            if rule['status']=='draft_auto' and rule.get('executable') is True:
                rule['executable']=False
                record['disabled_invalid_executable_flag']=True
            record.update(result='blocked',scope='미구현 초안',reason=blocked_reason(name))
        else:
            kind=profile['answer_type']
            if kind not in rule['supported_answer_types']:
                record.update(result='blocked',scope=profile['scope'],reason=f'Concept 지원 답 유형과 불일치: {kind}')
                records.append(record);continue
            formula=profile['formula'] if profile['formula'] in rule['source_formula_ids'] else None
            rule.update(status='curated',executable=True,manual_review_required=True,
                        rule_version='1.1.0',primary_formula_id=formula,
                        parameter_spec=deepcopy(profile['parameters']),
                        symbol_spec=deepcopy(profile.get('symbols',{'x':{'role':'independent_variable','assumptions':{'real':True}}})),
                        constraints=deepcopy(profile['constraints']),
                        construction={'operation':name,'required_objects':list(profile['parameters'])+list(profile.get('symbols',{'x':{}})),
                                      'semantic_structure':[profile['scope'] or profile['question']],
                                      'text_templates':[profile['question']],'latex_templates':[],
                                      'builder_expression':'sequence' if 'sequence' in profile['parameters'] else ('f' if 'f' in profile['parameters'] else next(iter(profile['parameters'])))},
                        answer_spec={'answer_type':kind,'engine':'sympy','expression':profile['expression'],
                                     'latex_expression':None,'canonicalization':'simplify'},
                        validation={'validators':[profile['validator']],
                                    'validator_configs':{profile['validator']:deepcopy(profile['config'])},
                                    'all_required':True,'max_generation_attempts':40},
                        notes=MARKER+' '+(profile['scope'] or '문제에 명시한 제한 범위')+'; 자동 실행 검증 후에도 사람 검수 필요.')
            rule['notes']+=' contract_sha256:'+contract_hash(rule)
            record.update(result='applied',scope=profile['scope'] or '문제 문장에 명시한 범위',reason='실제 생성/계산/검증 계약 작성')
            if formula is None:record['formula_review']='대표 공식 자동 선택 보류: 원본 공식 ID와의 수동 매핑 필요'
        records.append(record)
    catalog=GenerationRuleCatalog.model_validate(output)
    for parsed,record in zip(catalog.rules,records):
        issues=validate_generation_rule(parsed)
        record['static_issues']=[{'code':v.code,'severity':v.severity,'message':v.message} for v in issues]
        if record['result'] in {'applied','preserved_existing'}:
            ensure_generation_rule_valid(parsed)
    return output,records


def verify_records(output,records,seed_count=5):
    """원본 Concept에 연결한 실제 Template으로 매개변수/정답/검증을 실행한다."""
    from app.problems.problem_type_extractor import extract_from_directory
    from app.problems.template_builder import build_template
    from scripts.problems.common.problem_instance_generator import generate_problem_instance
    catalog=GenerationRuleCatalog.model_validate(output)
    items=extract_from_directory(ROOT/'data/concepts')
    by_name={r['problem_type']:r for r in records}
    for rule in catalog.rules:
        if not rule.executable or rule.status=='draft_auto':continue
        templates=[build_template(item,rule) for item in items
                   if item.subject_id=='engineering_mathematics' and item.problem_type==rule.problem_type]
        results=[]
        for template in templates:
            for seed in range(17,17+seed_count):
                try:
                    generated=generate_problem_instance(template,seed=seed,max_attempts=40)
                    results.append({'requested_seed':seed,'actual_seed':generated.seed,'passed':True,
                                    'template_id':template.template_id})
                except Exception as exc:
                    results.append({'requested_seed':seed,'passed':False,'error':str(exc),
                                    'template_id':template.template_id})
        record=by_name[rule.problem_type]
        record['seed_results']=results
        record['runtime_test']='passed' if results and all(r['passed'] for r in results) else 'failed'
        print(f"[VERIFY] {rule.problem_type}: {record['runtime_test']} ({len(results)}건)",flush=True)
    return not any(r['runtime_test']=='failed' for r in records)


def write_report(path,records):
    path.mkdir(parents=True,exist_ok=True)
    counts=dict(Counter(r['result'] for r in records))
    (path/'review.json').write_text(json.dumps({'subject_id':'engineering_mathematics','counts':counts,'rules':records},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# 공학수학 전체 Rule 검수 결과','',f'총 {len(records)}개. 결과: {counts}',
           f'실행 검증 통과: {sum(r["runtime_test"]=="passed" for r in records)}개. 최종 사람 검수는 별도입니다.',
           '', '자동 검수/생성 검증과 최종 사람 검수는 다릅니다. applied도 ready 또는 출제 승인 상태가 아닙니다.',
           '', '| 유형 | 처리 | 실행 검사 | 원본 문제 | 적용 범위/남은 작업 |', '|---|---|---|---|---|']
    for r in records:
        detail=r['reason'] if r['result']=='blocked' else r['scope']
        if r.get('formula_review'):detail+='; '+r['formula_review']
        lines.append('| '+r['problem_type']+' | '+r['result']+' | '+r['runtime_test']+' | '+(' / '.join(r['original_issues']) or '기존 구현')+' | '+detail.replace('|','/')+' |')
    (path/'REVIEW.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--verify',action='store_true',help='적용 전에 실제 생성/정답 검증도 실행')
    parser.add_argument('--seed-count',type=int,default=5)
    parser.add_argument('--rule-file',type=Path,default=ROOT/'data/generation_rules/engineering_mathematics.json')
    parser.add_argument('--report-dir',type=Path,default=ROOT/'data/rule_review/engineering_mathematics')
    args=parser.parse_args()
    raw=json.loads(args.rule_file.read_text(encoding='utf-8'))
    args.report_dir.mkdir(parents=True,exist_ok=True)
    snapshot=args.report_dir/'source_snapshot.json'
    if not snapshot.exists(): snapshot.write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    output,records=inspect_and_apply(raw)
    if args.seed_count<1:parser.error('--seed-count는 1 이상이어야 합니다.')
    verified=verify_records(output,records,args.seed_count) if args.verify else True
    write_report(args.report_dir,records)
    if not verified:
        print('실행 검증 실패: Rule 파일을 적용하지 않았습니다.')
        return 1
    changed=[a['problem_type'] for a,b in zip(raw['rules'],output['rules']) if a!=b]
    print(f'전체 검수: {len(records)}개 / 수정 필요: {len(changed)}개')
    print(dict(Counter(r['result'] for r in records)))
    if args.apply and changed:
        backup=args.rule_file.with_name(args.rule_file.name+'.before-full-review.'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:8]+'.bak')
        backup.write_bytes(args.rule_file.read_bytes())
        temp=args.rule_file.with_name(args.rule_file.name+'.'+uuid4().hex+'.tmp')
        temp.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');temp.replace(args.rule_file)
        print(f'적용 완료. 백업: {backup}')
    print(f'검수 리포트: {args.report_dir}')
    return 0


if __name__=='__main__':raise SystemExit(main())
