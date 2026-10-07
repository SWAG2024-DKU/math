# 선형대수 Template DB 파트

`template_db_todo.py`는 `linear_algebra.zip`에서 `ready`이고 `executable=true`인 선형대수 Template 62개를 읽고 해시를 계산합니다. DB 쓰기 함수는 한국어 TODO로 남겨 두었습니다.

## 실제 프로젝트와의 연결

- 기존 `sql/005_create_problem_schema.sql`, `006_create_problem_templates.sql`, `007_create_template_concepts.sql`, `008_create_template_import_audit.sql`을 사용합니다. Template 테이블을 다시 만들지 않습니다.
- 실제 적재는 `app.db.connection.get_connection`, `app.problems.template_importer`, `app.problems.template_repository`를 재사용하는 방향입니다. 현재 `scripts/problems/import_problem_templates.py`는 전체 과목 폴더를 읽으므로 선형대수 ZIP에 한정한 연결 작업이 TODO입니다.
- ZIP 경로를 DB `source_path`에 어떻게 기록할지 정한 뒤 동일 키/버전의 기존 행과 content hash를 비교하세요. Concept FK를 참조하므로 `kb.concepts` 선행 적재도 확인해야 합니다.

## DB 연결 없는 파일 확인

```bat
python template_db_todo.py --templates linear_algebra.zip
```

이 명령은 Template를 저장하지 않습니다. 프로젝트 루트에서 실행하거나 파일 경로를 정확히 지정하세요.
