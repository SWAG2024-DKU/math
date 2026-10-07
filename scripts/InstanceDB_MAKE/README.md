# 선형대수 Instance DB 파트

`instance_db_todo.py`는 선형대수 Template ZIP과 Preview ZIP을 대조해 1,240개 `pending` 후보를 확인합니다. Template DB Python 파일을 import하지 않습니다. PostgreSQL에 저장하는 함수와 사람 검수 후 승격 함수는 한국어 TODO입니다.

## 프로젝트의 PostgreSQL 스키마

기존 `problem.problem_templates`를 외래 키로 참조합니다. `009_problem_instances_todo.sql`은 새 `problem.problem_instances`, 검증 이력 테이블, 공개용 `problem.confirmed_instances` VIEW에 대한 **검토 초안**입니다. 실제 DB의 005~008 적용 상태와 기존 권한을 대조한 뒤 사용하세요. VIEW에서는 정답과 전체 payload를 반환하지 않습니다.

- Preview는 `pending`으로 적재하고 생성 시점의 `validation_trace`를 독립 재검증으로 간주하지 않습니다.
- `confirmed`는 최신 독립 재검증과 실명 담당자의 검수 결정이 모두 있는 경우에만 허용합니다.
- 서비스에서 문제 문장을 제공할 때는 공개용 VIEW를 사용하고, 사용자에게 정답이 들어 있는 원본 테이블을 노출하지 않습니다.

## DB 연결 없는 파일 확인

```bat
python instance_db_todo.py --templates linear_algebra.zip --previews all_20260930T130721Z_f5ed40c3.zip
```

이 명령과 동봉된 SQL 파일은 자동 DB 적재를 수행하지 않습니다.
