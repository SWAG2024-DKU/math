"""다양성 확장 인수 테스트 TODO.

기본 pytest 자동 수집을 피하도록 todo_ 이름을 사용합니다.
구현 후 test_linear_algebra_diversity.py로 변경하세요.
명시적으로 실행하면 미구현 테스트는 실패합니다. skip으로 완료를 위장하지 않습니다.
"""

def test_review_metadata_preserved_and_policy_idempotent():
    # TODO[LA-T01] test_review_metadata_preserved_and_policy_idempotent 구현
    # 1. 기존 curated/reviewed/사용자 메모/제약 fixture를 이용해.
    # 2. 보호 필드 보존, 원본 무변경, 반복 적용 멱등성, 정책 충돌 명시적 실패를 확인한다.
    raise NotImplementedError("TODO[LA-T01]: test_review_metadata_preserved_and_policy_idempotent")

def test_exact_rational_sampling_and_serialization():
    # TODO[LA-T02] test_exact_rational_sampling_and_serialization 구현
    # 1. 양/음/0, exclude/step/choices, 분모 1 및 다양한 분모,.
    # 2. 잘못된 설정, 기약분수 중복을 검사한다.
    # 3. 단일 seed 우연 대신 고정 seed 집합을.
    # 4. 사용한다.
    # 5. 정책에서 약속한 유형에만 분수 출현율 기준을 적용한다.
    # 6. JSON 왕복 후 정확한 값이 같아야 하며 float 근사로 통과시키지 않는다.
    raise NotImplementedError("TODO[LA-T02]: test_exact_rational_sampling_and_serialization")

def test_matrix_structure_invariants_and_diversity():
    # TODO[LA-T03] test_matrix_structure_invariants_and_diversity 구현
    # 1. 모든 특수 generator에서 차원/랭크/직교/대칭/중심화/.
    # 2. 고유값 중복도를 확인한다.
    # 3. 고정 seed 집합에서 조밀한 비대각 입력과 복수 구조가.
    # 4. 실제로 생성되는지 검사한다.
    # 5. 구조 의무가 없는 유형에 임의 기준을 강요하지 않는다.
    raise NotImplementedError("TODO[LA-T03]: test_matrix_structure_invariants_and_diversity")

def test_legacy_and_other_subjects_unchanged(tmp_path, monkeypatch):
    """LA-T04: 후보는 opt-in이고 원본/타 과목 경로가 바뀌지 않는다.

    Part 4의 ParameterSpec.validator TODO가 아직 미구현이므로, 이 회귀
    테스트는 외부 Rule 로더와 실제 수학 엔진을 stub으로 대체하여 Part 2의
    경로 선택·status·manifest·비파괴 실행 계약만 독립 검증한다.
    """
    import hashlib
    import json
    import sys
    from pathlib import Path
    from types import SimpleNamespace

    import scripts.problems.common.build_problem_templates as builder
    import scripts.problems.common.save_problem_previews as previews

    subjects = (
        "calculus_1", "calculus_2", "engineering_mathematics",
        "probability_statistics",
    )
    source_dir = tmp_path / "data" / "generation_rules"
    original_output = tmp_path / "data" / "problem_templates"
    for folder in (source_dir, original_output, tmp_path / "concepts"):
        folder.mkdir(parents=True, exist_ok=True)
    source = source_dir / "linear_algebra.json"
    source.write_bytes(b"LEGACY_RULES_PROTECTED\n")
    original = original_output / "protected.json"
    original.write_bytes(b"LEGACY_TEMPLATE_PROTECTED\n")
    protected_hashes = {
        path: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (source, original)
    }

    monkeypatch.setattr(builder, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(builder, "DEFAULT_OUTPUT_DIR", original_output)
    monkeypatch.setattr(builder, "DEFAULT_CONCEPT_DIR", tmp_path / "concepts")
    info = lambda subject: SimpleNamespace(
        subject_id=subject, unit_id=f"{subject}_u1",
        concept_id=f"{subject}.concept", problem_type="practice",
    )
    all_items = [info(s) for s in subjects] + [info("linear_algebra")]
    monkeypatch.setattr(builder, "extract_from_directory", lambda path: all_items)
    loaded = []
    def get_legacy_rule(subject, kind):
        loaded.append((subject,kind))
        return SimpleNamespace(subject_id=subject, problem_type=kind,
                               rule_id=f"{subject}:practice", notes=None,
                               status="reviewed")
    monkeypatch.setattr(builder, "get_rule", get_legacy_rule)
    monkeypatch.setattr(builder, "ensure_generation_rule_valid", lambda rule: [])

    def build_fake_template(item, rule, *, candidate_mode=False):
        return SimpleNamespace(
            template_id=f"{item.subject_id}.template",
            status="draft" if candidate_mode else "ready",
            executable=True,
            model_dump_json=lambda indent=2: json.dumps({
                "subject": item.subject_id, "type": item.problem_type,
                "candidate": candidate_mode, "rule_id": rule.rule_id,
            }, ensure_ascii=False, indent=indent),
        )
    monkeypatch.setattr(builder, "build_template", build_fake_template)

    def run_build(*args):
        monkeypatch.setattr(sys, "argv", ["build_problem_templates.py", *map(str,args)])
        builder.main()

    legacy_a = tmp_path / "legacy_a"
    legacy_b = tmp_path / "legacy_b"
    run_build("--concept-dir", tmp_path / "concepts", "--output-dir", legacy_a)
    before = len(loaded)

    # Part 4가 만든 후보 카탈로그를 가정. 후보 모드에서 get_rule(registry)
    # 호출이 증가하지 않는지 확인한다.
    candidate_file = tmp_path / "candidate_rules.json"
    candidate_file.write_text('{"stub":true}', encoding="utf-8")
    from app.schemas.generation_rule import GenerationRuleCatalog
    candidate_rule = SimpleNamespace(
        subject_id="linear_algebra", problem_type="practice",
        rule_id="LA_NEW_RULE", notes="candidate", status="reviewed",
    )
    monkeypatch.setattr(
        GenerationRuleCatalog, "model_validate_json",
        classmethod(lambda cls, data: SimpleNamespace(
            subject_id="linear_algebra", rules=[candidate_rule],
        )),
    )
    candidate_dir = tmp_path / "candidates" / "run1"
    run_build("--candidate-rule-catalog", candidate_file,
              "--subject", "linear_algebra", "--policy-version", "la-v2",
              "--output-dir", candidate_dir)
    assert len(loaded) == before, "후보 모드가 전역 Rule registry를 참조했습니다."
    cand_manifest = json.loads((candidate_dir / "manifest_linear_algebra.json").read_text(encoding="utf-8"))
    assert cand_manifest["candidate"] is True
    assert cand_manifest["policy_version"] == "la-v2"
    assert cand_manifest["source_rule_catalog_sha256"] == hashlib.sha256(candidate_file.read_bytes()).hexdigest()
    assert len(cand_manifest["generated_files"]) == 1
    cand_file = candidate_dir / cand_manifest["generated_files"][0]
    assert json.loads(cand_file.read_text(encoding="utf-8"))["candidate"] is True

    run_build("--concept-dir", tmp_path / "concepts", "--output-dir", legacy_b)
    for subject in subjects:
        rel = f"{subject}/{subject}_u1/{subject}.concept__practice.json"
        assert (legacy_a / rel).read_bytes() == (legacy_b / rel).read_bytes()
        assert json.loads((legacy_b / rel).read_text(encoding="utf-8"))["candidate"] is False
    for path, before_hash in protected_hashes.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == before_hash

    # 별도 후보 manifest에 포함된 하나만 프리뷰 생성. stale JSON을
    # 디렉터리에 함께 두어도 실행 대상이 되지 않아야 한다.
    stale = candidate_dir / "linear_algebra" / "stale.json"
    stale.write_text('{"object_type":"problem_template"}', encoding="utf-8")
    canonical = json.loads(cand_file.read_text(encoding="utf-8"))
    canonical.update({
        "object_type": "problem_template", "template_id": "la.t1",
        "taxonomy": {"subject_id":"linear_algebra", "unit_id":"la_01_matrix_algebra", "concept_ids":["linear_algebra.concept"]},
        "classification": {"problem_type":"practice"},
        "status": "draft", "executable": True,
    })
    cand_file.write_text(json.dumps(canonical), encoding="utf-8")
    cand_manifest["records"].append({
        "subject_id":"linear_algebra", "unit_id":"la_02_vector_spaces",
        "problem_type":"not_supported", "status":"failed",
        "error":"후보 Rule 미구현",
    })
    (candidate_dir / "manifest_linear_algebra.json").write_text(json.dumps(cand_manifest), encoding="utf-8")
    called = []
    def fake_save_previews(path, output_root, **kwargs):
        called.append(Path(path).resolve())
        return (kwargs["output_dir_override"], {
            "succeeded":1,"failed":0,"timed_out":0,
            "results":[{"passed":True,"requested_seed":17,"actual_seed":17,"attempts":1}],
        })
    monkeypatch.setattr(previews, "save_previews", fake_save_previews)
    _, report = previews.save_subject_previews(
        candidate_dir / "linear_algebra", tmp_path / "preview",
        manifest_path=candidate_dir / "manifest_linear_algebra.json",
        include_draft=True, count=1,
    )
    assert called == [cand_file.resolve()]
    assert report["candidate"] is True and report["completed"] == 1
    assert report["upstream_failed"] == 1 and report["errors"] == 1
    assert report["source_rule_catalog_sha256"] == cand_manifest["source_rule_catalog_sha256"]


def test_independent_validator_rejects_tampering():
    # TODO[LA-T05] test_independent_validator_rejects_tampering 구현
    # 1. 새 분수/조밀 행렬 문제의 정답·문장·조건을 각각 변조해.
    # 2. 독립 검증이 거부하는지 확인한다.
    # 3. 비유일하지만 올바른 기저·부호 대안은 인정한다.
    # 4. 생성기 계산 helper를 검증기에서 호출하면 안 된다.
    raise NotImplementedError("TODO[LA-T05]: test_independent_validator_rejects_tampering")

def test_regeneration_and_all_six_units_end_to_end():
    # TODO[LA-T06] test_regeneration_and_all_six_units_end_to_end 구현
    # 1. tmp_path에서 Python→후보 Rule→후보 Template→Preview→.
    # 2. ZIP→독립 검증→다양성 보고서를 실행한다.
    # 3. 누락/0건/unsupported/timeout을.
    # 4. 성공으로 간주하지 않고 원본 파일 및 DB를 변경하지 않는다.
    raise NotImplementedError("TODO[LA-T06]: test_regeneration_and_all_six_units_end_to_end")
