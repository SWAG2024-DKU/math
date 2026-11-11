"""네 과목의 Rule 적용→정적 검사→Template→검수용 Preview를 순서대로 실행한다.

선형대수 및 PostgreSQL은 실행 대상이 아니다. 기존 팀원이 수정한 계약은 각
review 스크립트의 보존 규칙을 따르며, 지원 유형 누락/실패를 완료로 처리하지 않는다.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]
SUBJECTS=('calculus_1','calculus_2','engineering_mathematics','probability_statistics')


def positive(value):
    result=int(value)
    if result<1:raise argparse.ArgumentTypeError('1 이상의 정수 필요')
    return result


def protect_linear_algebra():
    """선형대수 Rule/Template의 파일 이름과 바이트를 실행 전후 비교한다."""
    rule=ROOT/'data/generation_rules/linear_algebra.json'
    paths=[rule] if rule.is_file() else []
    paths+=sorted((ROOT/'data/problem_templates/linear_algebra').rglob('*.json'))
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def run(arguments):
    print('\n[RUN] '+' '.join([sys.executable,*arguments]),flush=True)
    subprocess.run([sys.executable,*arguments],cwd=ROOT,check=True)


def check_coverage(subject):
    rules=json.loads((ROOT/'data/generation_rules'/f'{subject}.json').read_text(encoding='utf-8'))['rules']
    required={r['problem_type'] for r in rules}
    if any(r.get('executable') is not True for r in rules):raise ValueError(f'{subject}: 실행 불가 Rule이 남아 있습니다.')
    manifest=json.loads((ROOT/'data/problem_templates'/f'manifest_{subject}.json').read_text(encoding='utf-8'))
    if manifest['counts'].get('failed',0):raise ValueError(f'{subject}: Template 생성 실패')
    covered=set()
    for name in manifest['generated_files']:
        value=json.loads((ROOT/'data/problem_templates'/name).read_text(encoding='utf-8'))
        if value.get('executable') is not True:raise ValueError(f'{subject}: 실행 불가 Template')
        covered.add(value['classification']['problem_type'])
    if covered!=required:raise ValueError(f'{subject}: 유형 누락 {sorted(required-covered)}, 초과 {sorted(covered-required)}')
    print(f'[COVERAGE] {subject}: {len(covered)}/{len(required)} 유형',flush=True)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--subject',choices=SUBJECTS,action='append',help='반복 지정 가능, 기본 네 과목 전체')
    parser.add_argument('--prepare-only',action='store_true',help='Rule/Template만 준비, Preview 저장 생략')
    parser.add_argument('--count',type=positive,default=1,help='Template당 Preview 목표 수')
    parser.add_argument('--seed-start',type=int,default=17)
    parser.add_argument('--verify-seeds',type=positive,default=3)
    parser.add_argument('--timeout-seconds',type=positive,default=300)
    args=parser.parse_args(argv)
    before=protect_linear_algebra()
    try:
        for subject in dict.fromkeys(args.subject or SUBJECTS):
            module_subject='engineering_math' if subject=='engineering_mathematics' else subject
            run(['-m',f'scripts.problems.{module_subject}.review_{subject}_rules','--apply','--verify','--seed-count',str(args.verify_seeds)])
            run(['-m','scripts.problems.common.validate_generation_rules','--subject',subject])
            run(['-m','scripts.problems.common.build_problem_templates','--subject',subject,'--overwrite'])
            check_coverage(subject)
            if not args.prepare_only:
                run(['-m','scripts.problems.common.save_problem_previews','--all','--subject',subject,
                     '--include-draft','--count',str(args.count),'--seed-start',str(args.seed_start),
                     '--timeout-seconds',str(args.timeout_seconds)])
    finally:
        if protect_linear_algebra()!=before:
            raise RuntimeError('선형대수 Rule/Template가 변경되었습니다. 완료로 간주하지 마세요.')
    print('\n[DONE] 요청 과목의 모든 Rule 유형 준비 완료. 사람 검수 및 공개 승인은 별도입니다.',flush=True)
    return 0


if __name__=='__main__':raise SystemExit(main())
