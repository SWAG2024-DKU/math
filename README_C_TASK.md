# C 담당 — ProblemTemplate DB 검증 파일

이 ZIP은 `SWAG2024-DKU/math` 레포의 **C 담당(검증/Audit/Test)** 파일만
완성본으로 넣은 것입니다.

## 포함 파일

```text
scripts/problems/verify_problem_template_db.py
tests/test_problem_template_db.py
```

기존 파일을 일부만 수정하는 patch가 아니라, 두 파일 모두 **전체 파일**입니다.

## 적용 방법

ZIP을 푼 뒤 안의 `scripts/`, `tests/` 폴더를
`SWAG2024-DKU/math` 프로젝트 루트에 그대로 복사하세요.

최종 구조:

```text
math/
├─ scripts/
│  └─ problems/
│     └─ verify_problem_template_db.py
└─ tests/
   └─ test_problem_template_db.py
```

## 1. A/B 작업이 아직 합쳐지기 전

DB 없이 원본 파일만 독립 검증할 수 있습니다.

```bash
python scripts/problems/verify_problem_template_db.py --source-only
```

기대값:

```text
JSON file count: 3389
ProblemTemplate file count: 3383
duplicate group count: 56
unique template count: 3327
ready source count: 56
draft source count: 3271
```

## 2. A/B 작업이 main에 합쳐진 뒤

C 브랜치에서 최신 main을 가져옵니다.

```bash
git fetch origin
git merge origin/main
```

A의 SQL schema를 적용하고 B의 importer로 DB 적재를 끝낸 후:

```bash
python scripts/problems/verify_problem_template_db.py
```

최종 줄이 아래처럼 나오면 됩니다.

```text
ProblemTemplate DB verification PASSED
```

## 3. pytest

```bash
pytest tests/test_problem_template_db.py -v
```

모든 테스트가 PASS해야 합니다.

## 4. C가 검증하는 것

- raw JSON 3389개
- 실제 ProblemTemplate 3383개
- 중복 그룹 56개
- 고유 Template 3327개
- ready 56 / draft 3271
- ready가 모두 executable인지
- PK 중복이 없는지
- Template ↔ Concept FK가 정상인지
- payload의 concept_ids와 관계 테이블이 동일한지
- 일반 컬럼과 JSON payload가 동일한지
- content_hash가 payload와 일치하는지
- source와 DB의 template key가 동일한지
- duplicate audit 56건이 존재하는지
- 잘못된 status를 DB가 거부하는지
- 잘못된 difficulty 범위를 DB가 거부하는지
- 없는 concept_id를 DB가 거부하는지
- 동일 PK를 DB가 거부하는지

## 5. commit / push

```bash
git add scripts/problems/verify_problem_template_db.py tests/test_problem_template_db.py
git commit -m "test: verify problem template database integrity"
git push
```

## 주의

이 검증 코드는 팀에서 합의한 다음 DB 이름을 전제로 합니다.

```text
problem.problem_templates
problem.template_concepts
problem.template_import_audit
kb.concepts
```

A 담당자가 실제 테이블명이나 컬럼명을 다르게 만들었다면,
그 최종 schema에 맞춰 C 파일도 소폭 맞춰야 합니다.
