"""Part 1: 선형대수 후보 규칙→템플릿→Preview→독립 검수→다양성 보고.

다른 파트의 코드는 수정하지 않으며, 출력은 별도의 run 폴더에만 작성한다.
현재 Part 2/4/6의 미구현 진입점은 DependencyBlocked로 명시한다.
검수 성공 != 사람 승인/출제 가능 상태.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import traceback
from typing import Any
from uuid import uuid4
from zipfile import ZipFile, ZIP_DEFLATED

SUBJECT = "linear_algebra"
UNITS = tuple(f"la_{i:02d}_" for i in range(1, 7))
OTHER_SUBJECTS = ("calculus_1", "calculus_2", "engineering_mathematics", "probability_statistics")
NUMERIC = re.compile(r"^[+-]?\d+(?:/[+-]?\d+)?$")


class Part1Error(RuntimeError):
    """Part 1 데이터 무결성 또는 실행 계약 오류."""


class DependencyBlocked(Part1Error):
    """다른 파트에 미구현/미확정 인터페이스가 있어 중단함."""


def _relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _inside(path: Path, parent: Path) -> bool:
    return path.resolve().is_relative_to(parent.resolve())


def _output_guard(root: Path, run_dir: Path) -> None:
    root, run_dir = root.resolve(), run_dir.resolve()
    if run_dir == root or _inside(root, run_dir):
        raise Part1Error("출력 폴더가 프로젝트 루트 또는 그 상위일 수 없습니다.")
    for protected in (root / "data", root / "app", root / "scripts", root / "tests", root / ".git"):
        if run_dir == protected.resolve() or _inside(run_dir, protected):
            raise Part1Error(f"원본 보호 경로에는 출력할 수 없습니다: {protected}")


def _json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise Part1Error(f"JSON 읽기 실패: {path}: {exc}") from exc


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)


def _hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _protected_snapshot(root: Path) -> dict[str, str]:
    # 후보 출력 경로와 무관하게 원본 Rule/Template, 다른 4과목을 보호한다.
    protected = (root / "data" / "generation_rules", root / "data" / "problem_templates")
    result = {}
    for base in protected:
        if not base.is_dir():
            raise Part1Error(f"원본 데이터 디렉터리 누락: {base}")
        for f in sorted(base.rglob("*.json")):
            if f.is_symlink():
                raise Part1Error(f"원본 JSON 심볼릭 링크는 지원하지 않습니다: {f}")
            result[_relative(f, root)] = _hash(f)
    return result


def _templates(root: Path) -> dict[str, dict[str, Any]]:
    if not root.is_dir():
        raise Part1Error(f"템플릿 경로 없음: {root}")
    found = {}
    for f in sorted(root.rglob("*.json")):
        data = _json(f)
        tax = data.get("taxonomy") or {}
        cls = data.get("classification") or {}
        unit, kind, template_id = tax.get("unit_id"), cls.get("problem_type"), data.get("template_id")
        if tax.get("subject_id") != SUBJECT or not isinstance(unit, str) or not any(unit.startswith(p) for p in UNITS):
            raise Part1Error(f"선형대수 6단원 외 템플릿: {f}")
        if f.relative_to(root).parts[0] != unit:
            raise Part1Error(f"6단원 디렉터리와 Template.unit_id가 불일치: {f} ({unit})")
        if not isinstance(kind, str) or not kind.strip() or not isinstance(template_id, str) or not template_id.strip() or kind in found:
            raise Part1Error(f"유형/ID 누락 또는 유형 중복: {f} ({kind})")
        found[kind] = {"unit": unit, "template_id": template_id, "sha256": _hash(f), "path": str(f.resolve())}
    if len({v["template_id"] for v in found.values()}) != len(found):
        raise Part1Error("template_id가 중복되었습니다.")
    unit_ids = {v['unit'] for v in found.values()}
    if not found or len(unit_ids) != 6 or {u[:6] for u in unit_ids} != set(UNITS):
        raise Part1Error("선형대수 6단원의 템플릿을 모두 찾지 못했습니다.")
    return found


def _rule_types(catalog: Path) -> set[str]:
    raw = _json(catalog)
    items = raw.get("rules")
    if not isinstance(items, list):
        raise Part1Error(f"rules 배열 없음: {catalog}")
    kinds = [x.get("problem_type") for x in items if isinstance(x, dict)]
    if (len(kinds) != len(items) or len(set(kinds)) != len(kinds) or
            not all(isinstance(k, str) and k.strip() for k in kinds)):
        raise Part1Error(f"규칙 문제 유형 중복/누락: {catalog}")
    if raw.get("rule_count") is not None and raw["rule_count"] != len(items):
        raise Part1Error(f"규칙의 rule_count 메타데이터 불일치: {catalog}")
    if any(item.get("subject_id", SUBJECT) != SUBJECT for item in items):
        raise Part1Error(f"다른 과목 Rule이 선형대수 catalog에 섞였습니다: {catalog}")
    return set(kinds)


def _rule_map(catalog: Path) -> dict[str, dict[str, Any]]:
    _rule_types(catalog)
    return {rule["problem_type"]: rule for rule in _json(catalog)["rules"]}


def _assert_review_contract_preserved(original: Path, candidate: Path) -> bool:
    """Part 4 후보가 승인·정답·문제 문장을 바꾸지 않았고 생성 입력만 확장했는지 확인한다.

    반환값은 적어도 하나의 parameter_spec이 실제로 변경되었는지 여부이다.
    확장된 파라미터 범위의 검수 승인은 별개이며 이 함수는 그것을 증명하지 않는다.
    """
    before, after = _rule_map(original), _rule_map(candidate)
    if before.keys() != after.keys():
        raise Part1Error("원본 Rule 유형과 후보 Rule 유형 불일치")
    immutable = ("rule_id", "rule_version", "subject_id", "problem_type", "status", "executable",
                 "manual_review_required", "source_concept_ids", "source_formula_ids",
                 "supported_answer_types", "constraints", "construction", "answer_spec",
                 "validation", "difficulty", "notes")
    changed_parameters = False
    for kind in before:
        for field in immutable:
            if before[kind].get(field) != after[kind].get(field):
                raise Part1Error(f"원본 검수/수학 계약 변경 금지: {kind}.{field}")
        if before[kind].get("parameter_spec") != after[kind].get("parameter_spec"):
            changed_parameters = True
    return changed_parameters


def capture_baseline(project_root: Path, output_dir: Path) -> dict[str, Any]:
    root, out = Path(project_root).resolve(), Path(output_dir).resolve()
    _output_guard(root, out)
    if not (root / "scripts" / "problems").is_dir():
        raise Part1Error("프로젝트 루트가 아닙니다 (scripts/problems 누락).")
    before = _protected_snapshot(root)
    ts = _templates(root / "data" / "problem_templates" / SUBJECT)
    kinds = _rule_types(root / "data" / "generation_rules" / f"{SUBJECT}.json")
    if kinds != set(ts):
        raise Part1Error(f"Rule/Template 유형 불일치: rule만={sorted(kinds-set(ts))}, template만={sorted(set(ts)-kinds)}")
    data = {"project_root": str(root), "protected_sha256": before,
            "baseline_templates": ts, "expected_types": {u: sorted(k for k, v in ts.items() if v['unit'] == u)
                                                       for u in sorted({v['unit'] for v in ts.values()})},
            "expected_count": len(ts)}
    _write_json(out / "baseline.json", data)
    return data


def _run_module(root: Path, module: str, args: list[str], timeout: float = 600) -> None:
    cmd = [sys.executable, "-m", module, *args]
    try:
        result = subprocess.run(cmd, cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        raise DependencyBlocked(f"외부 단계 실행 시간 초과: {module} ({timeout}초)") from exc
    except OSError as exc:
        raise DependencyBlocked(f"외부 단계 시작 실패: {module}: {exc}") from exc
    if result.returncode:
        details = (result.stderr + "\n" + result.stdout)[-3500:]
        if "NotImplementedError" in details or "unrecognized arguments" in details:
            raise DependencyBlocked(f"협력 파트 진입점 미구현/CLI 계약 불일치: {module}: {details}")
        raise DependencyBlocked(f"협력 파트 실행 실패: {module} (exit={result.returncode}): {details}")


def _json_fingerprint(directory: Path) -> dict[str, str]:
    if not directory.is_dir():
        raise Part1Error(f"생성 결과 디렉터리 없음: {directory}")
    files = sorted(f for f in directory.rglob("*.json") if f.name != "manifest.json")
    if not files:
        raise Part1Error(f"생성 결과 JSON이 없습니다: {directory}")
    # JSON 공백/키 순서는 비교하지 않고 의미상 구조만 비교한다.
    return {f.relative_to(directory).as_posix(): hashlib.sha256(
        json.dumps(_json(f), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()
            for f in files}


def regenerate_candidates(project_root: Path, output_dir: Path, policy_mode: str) -> dict[str, Any]:
    root, out = Path(project_root).resolve(), Path(output_dir).resolve()
    _output_guard(root, out)
    if policy_mode not in ("legacy", "extended"):
        raise Part1Error("--policy는 legacy 또는 extended여야 합니다.")
    baseline = _json(out / "baseline.json")
    # Part 4/2의 계약: --policy 와 --rule-dir 은 해당 파트가 제공해야 할 CLI 확장 옵션.
    # 현재 저장소에는 이 옵션이 없으므로 실행 시 DependencyBlocked 상태로 남긴다.
    runs = []
    original_rule = root / "data" / "generation_rules" / f"{SUBJECT}.json"
    for suffix in ("a", "b"):
        stage = out / "candidates" / suffix
        rules, templates = stage / "rules", stage / "templates"
        for sub in (rules, templates):
            if sub.exists():
                raise Part1Error(f"이전 후보 출력에 덮어쓸 수 없습니다: {sub}")
        _run_module(root, "scripts.problems.common.generate_generation_rules", [
            "--subject", SUBJECT, "--policy", policy_mode, "--output-dir", str(rules)])
        manifest_path = rules / "manifest.json"
        if not manifest_path.is_file():
            raise DependencyBlocked("Part 4 후보 Rule manifest.json이 없습니다 (정책 버전/모드 추적 불가).")
        policy_manifest = _json(manifest_path)
        if (not isinstance(policy_manifest, dict) or
                policy_manifest.get("policy_mode") != policy_mode or
                not isinstance(policy_manifest.get("policy_version"), str) or
                not policy_manifest["policy_version"].strip()):
            raise DependencyBlocked("Part 4 정책 manifest 계약 불일치 (policy_mode/policy_version).")
        _run_module(root, "scripts.problems.common.build_problem_templates", [
            "--subject", SUBJECT, "--rule-dir", str(rules), "--output-dir", str(templates)])
        source = templates / SUBJECT
        got = _templates(source)
        if set(got) != set(baseline["baseline_templates"]):
            raise Part1Error("후보 템플릿 유형이 원본 62개 유형과 다릅니다.")
        if _rule_types(rules / f"{SUBJECT}.json") != set(got):
            raise Part1Error("후보 Rule/Template 유형이 일치하지 않습니다.")
        input_changed = _assert_review_contract_preserved(original_rule, rules / f"{SUBJECT}.json")
        if policy_mode == "extended":
            if not input_changed:
                raise DependencyBlocked("extended 정책인데 실제 Rule parameter_spec이 달라지지 않았습니다.")
            if not any(
                _json(Path(baseline["baseline_templates"][kind]["path"])).get("parameters") !=
                _json(Path(got[kind]["path"])).get("parameters")
                for kind in got
            ):
                raise DependencyBlocked("extended 정책의 후보 Template parameters가 원본과 같습니다. 정책 전달을 확인하세요.")
        runs.append({"rules": _json_fingerprint(rules), "templates": _json_fingerprint(source),
                     "policy_version": policy_manifest["policy_version"]})
        if _protected_snapshot(root) != baseline["protected_sha256"]:
            raise Part1Error("재생성 중 원본 Rule/Template JSON이 변경되었습니다.")
    if runs[0] != runs[1]:
        raise Part1Error("동일 정책으로 두 번 재생성한 후보 JSON/정책 버전이 일치하지 않습니다.")
    original_rule_sha = baseline["protected_sha256"].get(f"data/generation_rules/{SUBJECT}.json")
    candidate_rule = out / "candidates" / "a" / "rules" / f"{SUBJECT}.json"
    if policy_mode == "extended" and _hash(candidate_rule) == original_rule_sha:
        raise DependencyBlocked("extended 정책으로 재생성했지만 Rule JSON이 원본과 동일합니다. 정책 연결을 확인해야 합니다.")
    result = {"policy_mode": policy_mode, "policy_version": runs[0]["policy_version"], "candidate_templates": str(out / "candidates" / "a" / "templates" / SUBJECT),
              "candidate_rules": str(out / "candidates" / "a" / "rules"), "deterministic": True,
              "type_count": len(baseline["baseline_templates"])}
    _write_json(out / "candidates.json", result)
    return result


def _find_manifests(unit_output: Path) -> list[Path]:
    return sorted(unit_output.rglob("manifest.json"))


def generate_by_unit(candidate_templates: Path, output_dir: Path, seeds: list[int]) -> dict[str, Any]:
    template_root, out = Path(candidate_templates).resolve(), Path(output_dir).resolve()
    if not seeds or any(type(s) is not int or s < 0 for s in seeds) or seeds != list(range(seeds[0], seeds[0] + len(seeds))):
        raise Part1Error("seeds는 0 이상의 연속된 정수 목록이어야 합니다.")
    templates = _templates(template_root)
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise Part1Error(f"문제 출력 디렉터리가 비어있지 않습니다: {out}")
    try:
        from scripts.problems.common.save_problem_previews import save_subject_previews
    except (ImportError, ModuleNotFoundError) as exc:
        raise DependencyBlocked(f"Part 2 Preview 생성 모듈을 불러올 수 없습니다: {exc}") from exc
    inventory: dict[str, Any] = {"seed_start": seeds[0], "count_per_type": len(seeds), "types": {}}
    for unit in sorted({v["unit"] for v in templates.values()}):
        source_dir = template_root / unit
        dest = out / unit
        dest.mkdir(parents=True, exist_ok=False)
        runtime_file = out.parent / "run_config.json"
        runtime = _json(runtime_file) if runtime_file.exists() else {}
        timeout = runtime.get("timeout", 30.0)
        try:
            save_subject_previews(source_dir, dest, subject_id=SUBJECT, seed_start=seeds[0],
                                  count=len(seeds), timeout_seconds=timeout, include_draft=True)
        except NotImplementedError as exc:
            raise DependencyBlocked("Part 2 save_subject_previews()가 미구현 상태입니다.") from exc
        except Exception as exc:
            raise DependencyBlocked(f"Part 2 {unit} 생성 실패: {type(exc).__name__}: {exc}") from exc
        for manifest_file in _find_manifests(dest):
            if not _inside(manifest_file, dest):
                raise Part1Error(f"생성 manifest 경로가 출력 영역을 벗어남: {manifest_file}")
            m = _json(manifest_file)
            tid = m.get("template_id")
            kinds = [k for k,v in templates.items() if v['template_id'] == tid]
            if len(kinds) != 1:
                raise Part1Error(f"예상하지 않은 템플릿의 manifest: {manifest_file} ({tid})")
            kind = kinds[0]
            if m.get("template_sha256") != templates[kind]["sha256"]:
                raise Part1Error(f"다른 버전 템플릿으로 생성된 Preview: {kind}")
            if "template_file" in m and Path(m["template_file"]).resolve() != Path(templates[kind]["path"]):
                raise Part1Error(f"원본/이전 후보 템플릿이 섞였습니다: {kind}")
            if templates[kind]["unit"] != unit or kind in inventory["types"]:
                raise Part1Error(f"중복 또는 잘못된 단원에서 생성: {kind}")
            if m.get("publishable") is True:
                raise Part1Error(f"검수용 manifest가 출제 가능으로 표시됨: {kind}")
            if m.get("requested_count") is not None and m["requested_count"] != len(seeds):
                raise Part1Error(f"manifest 요청 수 불일치: {kind}")
            result_rows = m.get("results")
            if not isinstance(result_rows, list) or len(result_rows) != len(seeds):
                raise Part1Error(f"유형별 요청 수가 맞지 않는 manifest: {kind}")
            recorded_seeds = [r.get("requested_seed") for r in result_rows if isinstance(r, dict)]
            if recorded_seeds != seeds:
                raise Part1Error(f"seed 중복/누락/순서 오류: {kind}")
            items = []
            used_files = set()
            used_actual_seeds = set()
            for row in result_rows:
                if not isinstance(row, dict) or type(row.get("passed")) is not bool:
                    raise Part1Error(f"잘못된 생성 결과 형식: {kind}")
                if row.get("actual_seed") is not None and (type(row["actual_seed"]) is not int or row["actual_seed"] < row["requested_seed"]):
                    raise Part1Error(f"actual_seed가 잘못됐습니다: {kind}")
                item = {"requested_seed": row.get("requested_seed"), "actual_seed": row.get("actual_seed"),
                        "passed": row["passed"],
                        "timed_out": bool(row.get("timed_out")), "attempts": row.get("attempts"),
                        "error_type": row.get("error_type"), "error": row.get("error")}
                if row["passed"]:
                    if row.get("timed_out"):
                        raise Part1Error(f"timeout 결과가 성공 처리됨: {kind}")
                    actual_seed = row.get("actual_seed")
                    if type(actual_seed) is not int or actual_seed in used_actual_seeds:
                        raise Part1Error(f"실제 생성 seed 누락/중복: {kind}/{actual_seed}")
                    used_actual_seeds.add(actual_seed)
                    relname = row.get("file")
                    if (not isinstance(relname, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*\.json", relname)
                            or ".." in relname or Path(relname).name != relname):
                        raise Part1Error(f"상대 파일 이름이 안전하지 않습니다: {kind}/{relname}")
                    if relname in used_files:
                        raise Part1Error(f"여러 seed가 하나의 Instance 파일을 참조: {kind}/{relname}")
                    used_files.add(relname)
                    f = (manifest_file.parent / relname).resolve()
                    if not _inside(f, manifest_file.parent) or not f.is_file():
                        raise Part1Error(f"생성 성공으로 기록됐으나 파일이 없습니다: {f}")
                    payload = _json(f)
                    if not isinstance(payload, dict):
                        raise Part1Error(f"Instance JSON은 객체여야 합니다: {f}")
                    if payload.get("subject_id") != SUBJECT or payload.get("problem_type") != kind:
                        raise Part1Error(f"Instance 유형/과목이 manifest와 다릅니다: {f}")
                    if type(payload.get("seed")) is not int or payload["seed"] != actual_seed:
                        raise Part1Error(f"Instance seed와 manifest actual_seed가 다릅니다: {f}")
                    if payload.get("publishable") is not False:
                        raise Part1Error(f"검수 전 출제 허용 값이 발견되었습니다: {f}")
                    if (not isinstance(payload.get("statement"), str) or not payload["statement"].strip()
                            or not isinstance(payload.get("parameters"), dict)
                            or "expected_answer" not in payload):
                        raise Part1Error(f"Instance 문장·파라미터·정답 필수 필드 오류: {f}")
                    if payload.get("template_id") != tid:
                        raise Part1Error(f"Instance template_id 불일치: {f}")
                    snapshot = payload.get("template_snapshot")
                    if (not isinstance(snapshot, dict) or snapshot.get("template_id") != tid or
                            (snapshot.get("taxonomy") or {}).get("unit_id") != unit or
                            (snapshot.get("classification") or {}).get("problem_type") != kind):
                        raise Part1Error(f"Instance 원본 Template snapshot 불일치: {f}")
                    item["file"] = str(f)
                items.append(item)
            referenced = {Path(x["file"]).name for x in items if x.get("file")}
            extra_json = {p.name for p in manifest_file.parent.glob("*.json") if p.name != "manifest.json"} - referenced
            if extra_json:
                raise Part1Error(f"manifest에 없는 Preview JSON이 섞였습니다: {kind}: {sorted(extra_json)}")
            for counter_name, actual in (("succeeded", sum(r["passed"] for r in items)),
                                         ("failed", sum(not r["passed"] for r in items)),
                                         ("timed_out", sum(r["timed_out"] for r in items))):
                if counter_name in m and (type(m[counter_name]) is not int or m[counter_name] != actual):
                    raise Part1Error(f"{kind}: manifest의 {counter_name} 집계 불일치")
            inventory["types"][kind] = {"unit": unit, "template_id": tid, "manifest": str(manifest_file), "results": items}
    # 누락 유형은 사라지지 않도록 명시적으로 남긴다.
    for kind, info in templates.items():
        inventory["types"].setdefault(kind, {"unit": info["unit"], "template_id": info["template_id"],
                                              "manifest": None, "results": [], "missing": True})
    _write_json(out / "inventory.json", inventory)
    return inventory



def _compare_instances(first: Path, second: Path) -> dict[str, Any]:
    """동일 후보 정책/seed로 생성한 실제 문제 내용의 재현성 검사."""
    left, right = _json(Path(first) / "inventory.json"), _json(Path(second) / "inventory.json")
    if left["seed_start"] != right["seed_start"] or left["count_per_type"] != right["count_per_type"]:
        raise Part1Error("반복 Preview의 seed/요청 건수가 다릅니다.")
    if set(left["types"]) != set(right["types"]):
        raise Part1Error("반복 Preview의 유형 목록이 다릅니다.")
    differences = []
    compared = 0
    for kind in sorted(left["types"]):
        a, b = left["types"][kind]["results"], right["types"][kind]["results"]
        if len(a) != len(b):
            differences.append(f"{kind}: 생성 결과 개수가 다름")
            continue
        for one, two in zip(a, b):
            if (one["requested_seed"] != two["requested_seed"] or one["passed"] != two["passed"] or
                    one["actual_seed"] != two["actual_seed"] or one["timed_out"] != two["timed_out"]):
                differences.append(f"{kind}: seed/성공 여부가 다름")
                continue
            if one["passed"]:
                payload1, payload2 = _json(Path(one["file"])), _json(Path(two["file"]))
                comparable_fields = ("statement", "statement_latex", "parameters", "expected_answer",
                                     "template_id", "template_version", "problem_type", "answer_type",
                                     "seed", "generation_rule_id", "generation_rule_version")
                if any(payload1.get(field) != payload2.get(field) for field in comparable_fields):
                    differences.append(f"{kind}/seed={one['requested_seed']}: 문제/정답/파라미터가 다름")
                compared += 1
            elif one.get("error_type") != two.get("error_type"):
                differences.append(f"{kind}/seed={one['requested_seed']}: 생성 실패 종류가 다름")
    if differences:
        raise Part1Error("같은 정책/seed의 Instance 재현성 실패: " + "; ".join(differences[:10]))
    return {"instance_deterministic": True, "compared_instances": compared}

def independently_validate(preview_root: Path, output_dir: Path) -> dict[str, Any]:
    preview_root, out = Path(preview_root).resolve(), Path(output_dir).resolve()
    inv = _json(preview_root / "inventory.json")
    out.mkdir(parents=True, exist_ok=True)
    try:
        from scripts.problems.common.InstanceDB_MAKE.validate_stored_instances import validate_with_timeout
    except (ImportError, ModuleNotFoundError) as exc:
        raise DependencyBlocked(f"Part 6 독립 검증 모듈을 불러올 수 없습니다: {exc}") from exc
    runtime_file = out.parent / "run_config.json"
    timeout = _json(runtime_file).get("timeout", 30.0) if runtime_file.exists() else 30.0
    rows = []
    counts = Counter()
    archive = out / "previews.zip"
    with ZipFile(archive, "x", compression=ZIP_DEFLATED, compresslevel=6) as z:
        z.write(preview_root / "inventory.json", "inventory.json")
        for kind, info in sorted(inv["types"].items()):
            if info.get("missing") or not info["results"]:
                counts["missing"] += inv["count_per_type"]
                for seed in range(inv["seed_start"], inv["seed_start"] + inv["count_per_type"]):
                    rows.append({"type": kind, "unit": info['unit'], "result": "missing",
                                 "seed": seed, "message": "manifest 누락"})
                continue
            for r in info["results"]:
                if not r["passed"]:
                    verdict = "timeout" if r["timed_out"] else "generation_failed"
                    counts[verdict] += 1
                    rows.append({"type": kind, "unit": info['unit'], "result": verdict, "seed": r['requested_seed']})
                    continue
                f = Path(r["file"])
                if not f.is_file() or not _inside(f, preview_root):
                    counts["missing"] += 1
                    rows.append({"type": kind, "unit": info['unit'], "result": "missing", "seed": r['requested_seed']})
                    continue
                z.write(f, f.relative_to(preview_root).as_posix())
                try:
                    verdict_obj = validate_with_timeout(_json(f), seconds=timeout)
                except NotImplementedError as exc:
                    raise DependencyBlocked("Part 6 validate_with_timeout/validate_payload 미구현") from exc
                except TimeoutError:
                    verdict_obj = {"result": "timeout"}
                except Exception as exc:
                    # Part 6의 코드 결함/인터페이스 오류를 문제 자체의 'unsupported'로 위장하지 않는다.
                    raise DependencyBlocked(
                        f"Part 6 검증 실행 자체가 실패: {type(exc).__name__}: {exc}"
                    ) from exc
                verdict = verdict_obj.get("result") if isinstance(verdict_obj, dict) else None
                if verdict not in {"passed", "failed", "unsupported", "timeout"}:
                    raise DependencyBlocked(f"Part 6 결과 계약 불일치: {verdict_obj!r}")
                counts[verdict] += 1
                rows.append({"type": kind, "unit": info["unit"], "result": verdict, "seed": r['requested_seed'],
                             "file": f.relative_to(preview_root).as_posix(),
                             "message": verdict_obj.get("message")})
    grouped = defaultdict(Counter)
    for row in rows:
        grouped[(row['unit'], row['type'])][row['result']] += 1
    result = {"counts": dict(counts), "by_type": {f"{u}/{k}": dict(c) for (u, k), c in sorted(grouped.items())},
              "results": rows, "archive": str(archive), "total_checked": sum(counts.values())}
    _write_json(out / "validation.json", result)
    return result


def _fractions(value: Any):
    if isinstance(value, bool):
        return
    if isinstance(value, int):
        yield Fraction(value)
    elif isinstance(value, str) and NUMERIC.fullmatch(value):
        try:
            yield Fraction(value)
        except (ZeroDivisionError, ValueError):
            return
    elif isinstance(value, (list, dict)):
        it = value.values() if isinstance(value, dict) else value
        for part in it:
            yield from _fractions(part)


def _matrices(value: Any):
    if isinstance(value, dict):
        for v in value.values():
            yield from _matrices(v)
    elif isinstance(value, list):
        if (value and all(isinstance(r, list) and r and
                              all(not isinstance(x, (list, dict)) for x in r) for r in value)
                and len({len(r) for r in value}) == 1):
            yield value
        else:
            for item in value:
                yield from _matrices(item)


def _declared_matrices(payload: dict[str, Any]):
    """벡터들의 목록과 진짜 행렬 파라미터를 혼동하지 않도록 Template 타입을 사용한다."""
    parameters = payload["parameters"]
    snapshot = payload.get("template_snapshot") or {}
    specs = snapshot.get("parameters") if isinstance(snapshot, dict) else None
    if not isinstance(specs, dict) or not specs:
        # 아직 스키마가 없는 테스트 데이터에서는 기존 구조 기반 지표를 사용한다.
        yield from _matrices(parameters)
        return
    for key, spec in specs.items():
        if not isinstance(spec, dict) or spec.get("type") != "matrix":
            continue
        if key not in parameters:
            continue
        value = parameters[key]
        if (not isinstance(value, list) or not value or
                any(not isinstance(row, list) or not row for row in value) or
                len({len(row) for row in value}) != 1 or
                any(isinstance(x, (list, dict)) for row in value for x in row)):
            raise Part1Error(f"행렬 파라미터의 배열 형태가 잘못됐습니다: {key}")
        yield value


def _matrix_rank(m: list[list[Any]]) -> int | None:
    try:
        a = [[Fraction(v) for v in row] for row in m]
    except (TypeError, ValueError, ZeroDivisionError):
        return None  # 복소수/기호 행렬은 별도의 수학 검증기 담당
    rank, cols = 0, len(a[0])
    for j in range(cols):
        pivot = next((i for i in range(rank, len(a)) if a[i][j]), None)
        if pivot is None:
            continue
        a[rank], a[pivot] = a[pivot], a[rank]
        pivot_val = a[rank][j]
        a[rank] = [x / pivot_val for x in a[rank]]
        for i in range(rank + 1, len(a)):
            factor = a[i][j]
            if factor:
                a[i] = [x - factor * y for x, y in zip(a[i], a[rank])]
        rank += 1
        if rank == len(a):
            break
    return rank


def measure_diversity(preview_root: Path, expected_types: dict[str, Any]) -> dict[str, Any]:
    preview_root = Path(preview_root).resolve()
    inv = _json(preview_root / "inventory.json")
    required = {typ for kinds in expected_types.values() for typ in kinds}
    if required != set(inv["types"]):
        raise Part1Error(f"다양성 측정의 유형 목록 불일치: 누락={sorted(required-set(inv['types']))}")
    output = {}
    for kind in sorted(required):
        info = inv["types"][kind]
        seen = Counter()
        scalar_count = rational_count = zero_count = negative_count = 0
        denoms = Counter()
        shapes = Counter()
        ranks = Counter()
        mat_total = mat_non_diag = mat_dense_off_diag = mat_symmetric = 0
        density_sum = 0.0
        density_eligible = 0
        successful = 0
        for row in info.get("results", []):
            if not row["passed"]:
                continue
            f = Path(row["file"])
            if not _inside(f, preview_root) or not f.is_file():
                raise Part1Error(f"다양성 입력 파일 누락/경로 이탈: {f}")
            payload = _json(f)
            p = payload.get("parameters")
            if not isinstance(p, dict):
                raise Part1Error(f"parameters가 dict가 아닙니다: {f}")
            successful += 1
            seen[json.dumps(p, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)] += 1
            for x in _fractions(p):
                scalar_count += 1
                rational_count += x.denominator != 1
                zero_count += x == 0
                negative_count += x < 0
                denoms[x.denominator] += 1
            for m in _declared_matrices(payload):
                mat_total += 1
                n, k = len(m), len(m[0]); shapes[f"{n}x{k}"] += 1
                rank = _matrix_rank(m)
                ranks[str(rank) if rank is not None else "unknown"] += 1
                vals = list(_fractions(m))
                if len(vals) != n*k:  # 복소/기호 데이터: 미지원 지표로 구분
                    continue
                nonzero = sum(bool(v) for v in vals)
                density_sum += nonzero / (n*k)
                density_eligible += 1
                normalized = [[Fraction(v) for v in r] for r in m]
                if n == k:
                    if all(normalized[i][j] == normalized[j][i] for i in range(n) for j in range(n)):
                        mat_symmetric += 1
                    if any(normalized[i][j] != 0 for i in range(n) for j in range(n) if i != j):
                        mat_non_diag += 1
                    if all(normalized[i][j] != 0 for i in range(n) for j in range(n) if i != j):
                        mat_dense_off_diag += 1
        requested = inv["count_per_type"]
        output[kind] = {"unit": info['unit'], "requested": requested, "generated": successful,
                        "generation_failed": requested-successful, "exact_unique": len(seen),
                        "exact_duplicate_rate": (successful-len(seen))/successful if successful else None,
                        "rational_fraction": rational_count/scalar_count if scalar_count else None,
                        "negative_fraction": negative_count/scalar_count if scalar_count else None,
                        "zero_fraction": zero_count/scalar_count if scalar_count else None,
                        "denominators": dict(denoms), "matrix_shapes": dict(shapes), "matrix_ranks": dict(ranks),
                        "matrix_count": mat_total, "matrix_nondiagonal_count": mat_non_diag, "matrix_dense_offdiagonal_count": mat_dense_off_diag,
                        "matrix_symmetric_count": mat_symmetric,
                        "matrix_mean_density": density_sum / density_eligible if density_eligible else None,
                        "matrix_density_supported_count": density_eligible}
    result = {"types": output, "type_count": len(output), "requested_count": sum(x['requested'] for x in output.values())}
    # 함수 호출만으로 preview_root 밖(원본 data일 수도 있음)에 파일을 쓰지 않는다.
    # CLI/main에서 안전한 고유 run 폴더를 확인한 뒤 최종 보고서를 기록한다.
    return result


def assert_acceptance(baseline: dict[str, Any], candidate: dict[str, Any]) -> None:
    reasons = []
    if not isinstance(baseline, dict) or not isinstance(candidate, dict):
        raise Part1Error("최종 검수 입력은 JSON 객체여야 합니다.")
    root = Path(baseline["project_root"])
    if _protected_snapshot(root) != baseline["protected_sha256"]:
        reasons.append("원본 Rule/Template 해시가 변경됨")
    validation, diversity = candidate.get("validation", {}), candidate.get("diversity", {})
    if not isinstance(validation, dict) or not isinstance(diversity, dict):
        raise Part1Error("검증 결과 및 다양성 요약은 객체여야 합니다.")
    types = {k for kinds in baseline["expected_types"].values() for k in kinds}
    measured = diversity.get("types", {})
    if not isinstance(measured, dict):
        raise Part1Error("다양성 유형 목록은 객체여야 합니다.")
    if set(measured) != types:
        reasons.append("대상 유형 누락 또는 초과")
    counts = validation.get("counts", {})
    records = validation.get("results", [])
    expected_instances = candidate.get("expected_instances")
    if type(expected_instances) is not int or expected_instances < 1:
        reasons.append("기대 인스턴스 수가 올바르지 않음")
        expected_instances = None
    elif not types or expected_instances % len(types):
        reasons.append("기대 인스턴스 수가 유형 수의 배수가 아님")
    if not isinstance(records, list) or not records:
        reasons.append("검증 결과 누락")
        records = []
    if isinstance(counts, dict):
        if any(type(v) is not int or v < 0 for v in counts.values()):
            reasons.append("검증 카운트는 0 이상의 정수여야 함")
        actual_counts = Counter(r.get("result") for r in records if isinstance(r, dict))
        if dict(actual_counts) != {k: v for k,v in counts.items() if v}:
            reasons.append("검증 카운트와 원본 결과 행이 불일치")
    else:
        counts = {}
        reasons.append("검증 카운트 형식 오류")
    if expected_instances is not None and len(records) != expected_instances:
        reasons.append("검증 결과 행 수가 총 요청 수와 불일치")
    unexpected = [r for r in records if not isinstance(r, dict) or r.get("type") not in types or
                  r.get("result") not in {"passed", "failed", "unsupported", "timeout", "missing", "generation_failed"} or
                  type(r.get("seed")) is not int or r["seed"] < 0]
    if unexpected:
        reasons.append("검증 결과에 예상 밖 유형이나 판정값이 포함됨")
    reference_seeds: set[int] | None = None
    for kind in types:
        expected_unit = next(unit for unit, kinds in baseline["expected_types"].items() if kind in kinds)
        listed = [r for r in records if isinstance(r, dict) and r.get("type") == kind and r.get("unit") == expected_unit]
        stat = measured.get(kind)
        if not isinstance(stat, dict):
            reasons.append(f"{kind}: 다양성 지표 형식 오류")
            continue
        if len(listed) != stat.get("requested"):
            reasons.append(f"{kind}: 검증 건수/단원 불일치")
        if expected_instances is not None and len(listed) != expected_instances // len(types):
            reasons.append(f"{kind}: 전체 요청에 비해 결과 건수 부족")
        seeds = [r.get("seed") for r in listed]
        if any(type(s) is not int or s < 0 for s in seeds) or len(set(seeds)) != len(seeds):
            reasons.append(f"{kind}: seed 누락/중복")
        else:
            unique_seeds = set(seeds)
            if reference_seeds is None:
                reference_seeds = unique_seeds
            elif unique_seeds != reference_seeds:
                reasons.append(f"{kind}: 다른 유형과 seed 집합 불일치")
        for metric in ("requested", "generated", "exact_unique"):
            if type(stat.get(metric)) is not int or stat[metric] < 0:
                reasons.append(f"{kind}: 다양성 {metric} 집계 오류")
        if all(type(stat.get(m)) is int for m in ("requested", "generated", "exact_unique")):
            if stat["generated"] > stat["requested"] or stat["exact_unique"] > stat["generated"]:
                reasons.append(f"{kind}: 다양성 건수 관계 오류")
        dup = stat.get("exact_duplicate_rate")
        if (dup is not None and (type(dup) not in (int, float) or not math.isfinite(dup) or not 0 <= dup <= 1)):
            reasons.append(f"{kind}: 중복률 지표 오류")
    for verdict in ("generation_failed", "missing", "failed", "unsupported", "timeout"):
        if counts.get(verdict, 0):
            reasons.append(f"{verdict}={counts[verdict]}")
    if counts.get("passed", 0) != expected_instances:
        reasons.append("검증 통과 수가 총 요청 수와 다름")
    if candidate.get("deterministic") is not True:
        reasons.append("후보 Rule/Template 재생성 재현성이 미확인됨")
    if candidate.get("instance_deterministic") is not True:
        reasons.append("같은 seed에서 Instance 재현성이 미확인됨")
    if candidate.get("policy_mode") not in ("legacy", "extended") or not candidate.get("policy_version"):
        reasons.append("후보 정책 모드/버전 추적 정보 누락")
    criteria = candidate.get("criteria")
    if not isinstance(criteria, dict) or criteria.get("approved_by") != "part4+part6":
        reasons.append("Part 4/6이 합의한 검수 임계 기준이 지정되지 않음")
    else:
        min_unique = criteria.get("min_unique_per_type")
        max_duplicate = criteria.get("max_exact_duplicate_rate")
        per_type = criteria.get("per_type", {})
        if min_unique is not None and (type(min_unique) is not int or min_unique < 0):
            reasons.append("min_unique_per_type은 음이 아닌 정수여야 함")
            min_unique = None
        if max_duplicate is not None and (type(max_duplicate) not in (int, float) or
                not math.isfinite(max_duplicate) or not 0 <= max_duplicate <= 1):
            reasons.append("max_exact_duplicate_rate은 0~1 사이 유한 숫자여야 함")
            max_duplicate = None
        if not isinstance(per_type, dict):
            reasons.append("per_type은 객체여야 함")
            per_type = {}
        for kind, row in measured.items():
            if not isinstance(row, dict):
                continue
            if row.get("generated", 0) != row.get("requested"):
                reasons.append(f"{kind}: 생성 건수 부족")
            if min_unique is not None and type(row.get("exact_unique")) is int and row["exact_unique"] < min_unique:
                reasons.append(f"{kind}: 유형별 고유 입력 건수 미달")
            if max_duplicate is not None and (type(row.get("exact_duplicate_rate")) not in (int, float) or
                                             row["exact_duplicate_rate"] > max_duplicate):
                reasons.append(f"{kind}: 입력 중복률 기준 초과")
        if min_unique is None and max_duplicate is None and not per_type:
            reasons.append("다양성 임계 기준이 비어 있음")
        for kind, limits in per_type.items():
            if kind not in measured:
                reasons.append(f"정책에 없는 유형: {kind}")
                continue
            if not isinstance(limits, dict):
                reasons.append(f"{kind}: 유형별 기준은 객체여야 함")
                continue
            row = measured[kind]
            if not isinstance(row, dict):
                reasons.append(f"{kind}: 다양성 객체 형식 오류")
                continue
            for key, metric in (("min_rational_fraction", "rational_fraction"),
                                ("min_nondiagonal_count", "matrix_nondiagonal_count"),
                                ("min_dense_offdiagonal_count", "matrix_dense_offdiagonal_count")):
                if key not in limits:
                    continue
                limit = limits[key]
                valid = ((type(limit) in (int, float) and math.isfinite(limit) and 0 <= limit <= 1)
                         if key == "min_rational_fraction" else (type(limit) is int and limit >= 0))
                if not valid:
                    reasons.append(f"{kind}: {key}가 올바른 기준이 아님")
                elif (type(row.get(metric)) not in (int, float) or
                      not math.isfinite(row[metric]) or row[metric] < limit):
                    reasons.append(f"{kind}: {metric} 목표 미달")
    if reasons:
        raise Part1Error("최종 수용 불가: " + "; ".join(reasons[:50]))


def _preflight(root: Path) -> dict[str, str]:
    checked = {
        "part4_rules": root / "scripts/problems/common/generate_generation_rules.py",
        "part2_templates": root / "scripts/problems/common/build_problem_templates.py",
        "part2_previews": root / "scripts/problems/common/save_problem_previews.py",
        "part6_validator": root / "scripts/problems/common/InstanceDB_MAKE/validate_stored_instances.py",
    }
    result = {}
    for name, path in checked.items():
        if not path.exists():
            result[name] = "missing"
        elif "raise NotImplementedError" in path.read_text(encoding="utf-8"):
            result[name] = "todo_present"  # 정적 힌트; 실행 가능 여부는 실제 실행으로만 판정
        else:
            result[name] = "source_present"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Part 1 선형대수 검수 파이프라인 (원본과 DB 읽기 전용)")
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--policy", choices=("legacy", "extended"), default="extended")
    parser.add_argument("--seed-start", type=int, default=17)
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--criteria", type=Path, default=None, help="Part 4/6 승인된 JSON 임계 기준")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="기본 동작: 원본 검토와 실행 준비도만 확인")
    mode.add_argument("--execute", action="store_true", help="협력 파트 진입점을 실제로 호출")
    args = parser.parse_args()
    if args.count < 1 or args.seed_start < 0 or not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("count>0, seed-start>=0, timeout>0 이어야 합니다.")
    root = args.project_root.resolve()
    safe_to_write_summary = False
    out = (args.output_dir or root / "reports" / "part1_runs" /
           f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid4().hex[:8]}").resolve()
    try:
        _output_guard(root, out)
        if out.exists() and any(out.iterdir()):
            raise Part1Error(f"실행 디렉터리가 비어있지 않습니다: {out}")
        out.mkdir(parents=True, exist_ok=True)
        safe_to_write_summary = True
        config = {"project_root": str(root), "output_dir": str(out), "policy": args.policy,
                  "seed_start": args.seed_start, "count": args.count, "timeout": args.timeout,
                  "execute": args.execute}
        _write_json(out / "run_config.json", config)
        baseline = capture_baseline(root, out)
        if not args.execute:
            _write_json(out / "summary.json", {"status": "planned", "expected_type_count": baseline['expected_count'],
                                                "preflight": _preflight(root), "message": "외부 파트 실행/승인을 수행하지 않았습니다."})
            print(f"[PLAN] {baseline['expected_count']}개 유형, {len(baseline['expected_types'])}단원 | {out}")
            return 0
        regenerated = regenerate_candidates(root, out, args.policy)
        preview_root = out / "previews"
        seed_set = list(range(args.seed_start, args.seed_start + args.count))
        generate_by_unit(Path(regenerated['candidate_templates']), preview_root, seed_set)
        preview_repeat = out / "previews_repeat"
        generate_by_unit(out / "candidates" / "b" / "templates" / SUBJECT, preview_repeat, seed_set)
        repeat_check = _compare_instances(preview_root, preview_repeat)
        _write_json(out / "repeatability.json", repeat_check)
        validation = independently_validate(preview_root, out / "validation")
        diversity = measure_diversity(preview_root, baseline['expected_types'])
        _write_json(out / "diversity.json", diversity)
        criteria = _json(args.criteria) if args.criteria else None
        candidate = {"validation": validation, "diversity": diversity, "criteria": criteria,
                     "policy_mode": regenerated["policy_mode"], "policy_version": regenerated["policy_version"],
                     "deterministic": regenerated["deterministic"],
                     "instance_deterministic": repeat_check["instance_deterministic"],
                     "expected_instances": baseline["expected_count"] * args.count}
        assert_acceptance(baseline, candidate)
        _write_json(out / "summary.json", {"status": "passed_automatic_checks_only", "candidate": {
            "validation_counts": validation['counts'], "diversity_type_count": diversity['type_count'],
            "deterministic": regenerated['deterministic']}, "note": "사람 승인 및 DB 기록은 수행하지 않음"})
        print(f"[PASS] 자동 검수 기준 충족(사람 승인 아님) | {out}")
        return 0
    except (Part1Error, OSError, ValueError) as exc:
        if safe_to_write_summary and out.is_dir():
            _write_json(out / "summary.json", {"status": "blocked" if isinstance(exc, DependencyBlocked) else "failed",
                                                "error_type": type(exc).__name__, "message": str(exc)})
        print(f"[STOP] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        # 실행기의 예기치 않은 프로그래밍 오류는 타 파트의 '미지원' 판정과 엄격히 구분한다.
        if safe_to_write_summary and out.is_dir():
            _write_json(out / "summary.json", {"status": "internal_error",
                                                "error_type": type(exc).__name__, "message": str(exc),
                                                "traceback_file": "internal_error.txt"})
            (out / "internal_error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        print(f"[INTERNAL ERROR] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
