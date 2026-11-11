"""과목별 Rule 등록/Schema/정적 계약 검사. 실제 수학 실행 검증과는 구분한다."""
from __future__ import annotations
import argparse
from collections import Counter
from pathlib import Path
from app.problems.problem_type_extractor import extract_from_directory
from app.problems.generation_rule_registry import has_rule,list_rules
from scripts.problems.common.generation_rule_validator import validate_generation_rule
ROOT=Path(__file__).resolve().parents[3]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--subject',choices=['linear_algebra','calculus_1','calculus_2','engineering_mathematics','probability_statistics'])
    parser.add_argument('--details',action='store_true')
    args=parser.parse_args()
    items=extract_from_directory(ROOT/'data/concepts')
    if args.subject:items=[item for item in items if item.subject_id==args.subject]
    missing={(item.subject_id,item.problem_type) for item in items if not has_rule(item.subject_id,item.problem_type)}
    rules=list_rules(args.subject)
    issues=[(rule.rule_id,issue) for rule in rules for issue in validate_generation_rule(rule)]
    counts=Counter(issue.severity for _,issue in issues)
    print(f'대상 과목: {args.subject or "전체"}')
    print(f'Concept에서 추출된 Problem Type 항목: {len(items)}')
    print(f'Generation Rule 수(subject/problem_type): {len(rules)}')
    print(f'Rule 상태: {dict(Counter(rule.status for rule in rules))}')
    print(f'누락 Rule: {len(missing)} / 정적 오류: {counts["error"]} / 정적 경고: {counts["warning"]}')
    print('이 검사는 수학 실행 성공이나 사람 검수 완료를 의미하지 않습니다.')
    for subject,kind in sorted(missing):print(f'[MISSING] {subject}/{kind}')
    for rule_id,issue in issues:
        if args.details or issue.severity=='error':print(f'[{issue.severity.upper()}] {rule_id} [{issue.code}] {issue.message}')
    return 1 if missing or counts['error'] else 0


if __name__=='__main__':raise SystemExit(main())
