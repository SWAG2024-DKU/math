"""검증된 ProblemInstance를 사람 검수용 JSON/Markdown으로 임시 저장한다.

프로젝트 루트에서 실행:
    python -m scripts.problems.common.save_problem_previews --count 20 --seed-start 17
    python -m scripts.problems.common.save_problem_previews --all-linear-algebra --count 20 --seed-start 17
    python -m scripts.problems.common.save_problem_previews --subject calculus_1 --problem-type power_rule_application --include-draft --count 10

DB 저장 및 출제 상태 승격은 수행하지 않는다. 실행마다 새 폴더를 만든다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing
import re
from multiprocessing.connection import Connection, wait
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.schemas.problem_template import ProblemTemplate
from scripts.problems.common.problem_instance_generator import generate_problem_instance, ENABLED_SUBJECT_IDS


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TEMPLATE = (
    PROJECT_ROOT
    / "data"
    / "problem_templates"
    / "linear_algebra"
    / "la_01_matrix_algebra"
    / "la.matrix.multiplication__matrix_multiplication.json"
)
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "data" / "problem_previews"
DEFAULT_SUBJECT_ROOT = PROJECT_ROOT / "data" / "problem_templates" / "linear_algebra"


def _path_from_project(value: Path) -> Path:
    return value if value.is_absolute() else PROJECT_ROOT / value


def _json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def _safe_name(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z._-]+", "_", value).strip("._")


def _one_line(value: object, limit: int = 180) -> str:
    """로그에서 문제 문장을 한 줄로 보여준다."""
    text = " ".join(str(value).split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _generate_in_worker(
    template_bytes: bytes,
    seed: int,
    max_attempts: int | None,
    connection: Connection,
) -> None:
    """한 seed만 별도 프로세스에서 생성한다. Windows spawn 호환 함수."""
    try:
        template = ProblemTemplate.model_validate_json(template_bytes)
        result = generate_problem_instance(
            template, seed=seed, max_attempts=max_attempts
        )
        connection.send(("ok", result.instance, result.seed, len(result.attempts)))
    except Exception as exc:
        connection.send(("error", type(exc).__name__, str(exc)))
    finally:
        connection.close()


def _generate_bounded(
    template_bytes: bytes,
    seed: int,
    max_attempts: int | None,
    timeout_seconds: float,
) -> tuple[dict[str, object], int, int]:
    """제한 시간을 넘긴 SymPy 계산은 프로세스를 종료하고 실패로 기록한다."""
    context = multiprocessing.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    worker = context.Process(
        target=_generate_in_worker,
        args=(template_bytes, seed, max_attempts, sender),
    )
    try:
        worker.start()
        sender.close()
        ready = wait([receiver, worker.sentinel], timeout_seconds)
        if receiver in ready or receiver.poll(0):
            try:
                message = receiver.recv()
            except EOFError as exc:
                raise RuntimeError(f"seed {seed}: 작업 프로세스가 응답 없이 종료되었습니다.") from exc
            if message[0] == "error":
                raise RuntimeError(f"{message[1]}: {message[2]}")
            if message[0] != "ok":
                raise RuntimeError(f"seed {seed}: 알 수 없는 작업 응답입니다.")
            return message[1], message[2], message[3]
        if worker.sentinel in ready:
            raise RuntimeError(
                f"seed {seed}: 작업 프로세스가 종료되었습니다 (exitcode={worker.exitcode})."
            )
        raise TimeoutError(f"seed {seed}: {timeout_seconds:g}초 제한 시간을 초과했습니다.")
    finally:
        receiver.close()
        sender.close()
        if worker.is_alive():
            worker.terminate()
        worker.join(timeout=2)
        if worker.is_alive():
            worker.kill()
            worker.join()


def save_previews(
    template_path: Path,
    output_root: Path,
    *,
    seed_start: int = 17,
    count: int = 20,
    max_attempts: int | None = None,
    timeout_seconds: float = 300,
    output_dir_override: Path | None = None,
    include_draft: bool = False,
) -> tuple[Path, dict[str, object]]:
    """생성 결과와 실패 기록을 한 실행 폴더에 저장한다."""

    if count < 1:
        raise ValueError("count는 1 이상이어야 합니다.")
    if max_attempts is not None and max_attempts < 1:
        raise ValueError("max_attempts는 1 이상이어야 합니다.")
    if not 0 < timeout_seconds < float("inf"):
        raise ValueError("timeout_seconds는 유한한 양수여야 합니다.")

    template_path = _path_from_project(template_path)
    output_root = _path_from_project(output_root)
    template_bytes = template_path.read_bytes()
    template = ProblemTemplate.model_validate_json(template_bytes)

    subject = template.taxonomy.subject_id
    if subject not in ENABLED_SUBJECT_IDS:
        raise ValueError(f"미지원 과목: {subject}")
    if subject != "linear_algebra" and template.status != "ready" and not include_draft:
        raise ValueError("검수용 draft 실행은 --include-draft를 명시해야 합니다.")

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
    output_dir = (
        _path_from_project(output_dir_override)
        if output_dir_override is not None
        else output_root / subject / _safe_name(template.classification.problem_type) / run_id
    )
    output_dir.mkdir(parents=True, exist_ok=False)

    print(
        f"[START] {template.classification.problem_type} | {template.template_id} | "
        f"시작 seed {seed_start}, 목표 {count}개",
        flush=True,
    )

    manifest: dict[str, object] = {
        "purpose": "temporary_human_review",
        "publishable": False,
        "subject_id": subject,
        "template_id": template.template_id,
        "template_file": str(template_path),
        "template_sha256": hashlib.sha256(template_bytes).hexdigest(),
        "seed_start": seed_start,
        "requested_count": count,
        "timeout_seconds": timeout_seconds,
        "results": [],
    }
    results: list[dict[str, object]] = manifest["results"]  # type: ignore[assignment]
    review_sections = [f"# {subject} 문제 검수본\n\nTemplate: `{template.template_id}`\n"]
    next_seed = seed_start
    seen_statements: set[str] = set()

    for index in range(count):
        requested_seed = next_seed
        try:
            duplicate_count = 0
            while True:
                instance, actual_seed, attempt_count = _generate_bounded(
                    template_bytes, next_seed, max_attempts, timeout_seconds
                )
                if actual_seed < next_seed:
                    raise ValueError("생성기가 요청 seed보다 작은 실제 seed를 반환했습니다.")
                next_seed = actual_seed + 1
                if instance.get("publishable") is not False:
                    raise ValueError("검수 전 결과의 publishable 값은 False여야 합니다.")
                statement = instance["statement"]
                if not isinstance(statement, str) or not statement.strip():
                    raise ValueError("생성된 문제 문장이 비어 있습니다.")
                if statement not in seen_statements:
                    break
                duplicate_count += 1
                print(
                    f"  [DUPLICATE] actual={actual_seed} | 다음 seed {next_seed}로 재시도",
                    flush=True,
                )
                if duplicate_count >= 20:
                    raise RuntimeError("서로 다른 문제를 만들지 못했습니다 (중복 20회).")

            filename = f"start_{requested_seed}_actual_{actual_seed}.json"
            (output_dir / filename).write_text(_json_text(instance), encoding="utf-8")
            seen_statements.add(statement)
            results.append({
                "requested_seed": requested_seed,
                "actual_seed": actual_seed,
                "passed": True,
                "attempts": attempt_count,
                "duplicate_retries": duplicate_count,
                "file": filename,
            })
            print(
                f"  [OK] requested={requested_seed} actual={actual_seed} "
                f"attempts={attempt_count} | {_one_line(instance['statement'])} "
                f"| {filename}",
                flush=True,
            )
            answer_text = json.dumps(instance["expected_answer"], ensure_ascii=False, indent=2)
            review_sections.append(
                f"\n## {index + 1}. 시작 seed {requested_seed} (실제 seed {actual_seed})\n\n"
                f"[전체 JSON]({filename})\n\n"
                f"**문제**\n\n{instance['statement']}\n\n"
                f"**정답**\n\n```json\n{answer_text}\n```\n"
            )
        except Exception as exc:
            next_seed = max(next_seed, requested_seed + 1)
            results.append({
                "requested_seed": requested_seed,
                "passed": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "timed_out": isinstance(exc, TimeoutError),
            })
            print(
                f"  [{'TIMEOUT' if isinstance(exc, TimeoutError) else 'FAIL'}] "
                f"requested={requested_seed} | "
                f"{type(exc).__name__}: {_one_line(exc)}",
                flush=True,
            )
        finally:
            # 긴 배치가 중단되더라도 완료된 seed의 결과를 남긴다.
            manifest["succeeded"] = sum(bool(item["passed"]) for item in results)
            manifest["failed"] = len(results) - manifest["succeeded"]
            manifest["timed_out"] = sum(bool(item.get("timed_out")) for item in results)
            (output_dir / "manifest.json").write_text(_json_text(manifest), encoding="utf-8")
            (output_dir / "review.md").write_text("".join(review_sections), encoding="utf-8")

    succeeded = sum(bool(item["passed"]) for item in results)
    manifest["succeeded"] = succeeded
    manifest["failed"] = count - succeeded
    print(
        f"[DONE] {template.classification.problem_type} | 성공 {succeeded}/{count}, "
        f"실패 {count - succeeded} | {output_dir}",
        flush=True,
    )
    return output_dir, manifest


def save_subject_previews(
    template_root: Path,
    output_root: Path,
    *,
    seed_start: int = 17,
    count: int = 20,
    max_attempts: int | None = None,
    timeout_seconds: float = 300,
    subject_id: str = "linear_algebra",
    problem_type: str | None = None,
    include_draft: bool = False,
    manifest_path: Path | None = None,
) -> tuple[Path, dict[str, object]]:
    """템플릿 manifest로 입력을 고정해 사람 검수용 Preview를 생성한다.

    후보 모드에서는 manifest의 generated_files만 실행하며 디렉터리를
    무작정 스캔하지 않는다. upstream 실패/누락도 summary에 전달한다.
    """
    if subject_id not in ENABLED_SUBJECT_IDS:
        raise ValueError(f"미지원 과목: {subject_id}")
    if count < 1 or (max_attempts is not None and max_attempts < 1):
        raise ValueError("count와 max_attempts는 1 이상이어야 합니다.")
    if not 0 < timeout_seconds < float("inf"):
        raise ValueError("timeout_seconds는 유한한 양수여야 합니다.")
    template_root = _path_from_project(template_root).resolve()
    output_root = _path_from_project(output_root).resolve()
    if not template_root.is_dir():
        raise FileNotFoundError(f"Template 디렉터리가 없습니다: {template_root}")

    explicit_manifest = manifest_path is not None
    selected_manifest = (
        _path_from_project(manifest_path).resolve() if explicit_manifest
        else template_root.parent / f"manifest_{subject_id}.json"
    )
    source_manifest: dict[str, object] | None = None
    if selected_manifest.is_file():
        source_manifest = json.loads(selected_manifest.read_text(encoding="utf-8"))
        if source_manifest.get("object_type") != "problem_template_manifest":
            raise ValueError("Template manifest 형식이 아닙니다.")
        if source_manifest.get("subject_filter") != subject_id:
            raise ValueError("Template manifest의 subject_filter가 다릅니다.")
    elif explicit_manifest:
        raise FileNotFoundError(f"후보 Manifest가 없습니다: {selected_manifest}")

    candidate = bool(source_manifest and source_manifest.get("candidate") is True)
    if candidate and subject_id != "linear_algebra":
        raise ValueError("후보 생성은 선형대수 전용입니다.")
    if candidate and not include_draft:
        raise ValueError("후보 Preview는 --include-draft를 명시해야 합니다.")

    # candidate의 manifest가 지정한 template_root와 생성본 루트가 일치해야 한다.
    # template_root는 <output_dir>/<subject_id>를 가리켜야 한다.
    if candidate and selected_manifest.parent.resolve() != template_root.parent.resolve():
        raise ValueError("후보 Template root와 manifest의 생성 루트가 다릅니다.")

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
    batch_dir = output_root / subject_id / f"all_{run_id}"
    batch_dir.mkdir(parents=True, exist_ok=False)
    summary: dict[str, object] = {
        "purpose": "temporary_human_review",
        "publishable": False,
        "candidate": candidate,
        "subject_id": subject_id,
        "problem_type_filter": problem_type,
        "include_draft": include_draft,
        "seed_start": seed_start,
        "seeds_per_template": count,
        "max_attempts": max_attempts,
        "timeout_seconds": timeout_seconds,
        "template_manifest": str(selected_manifest) if source_manifest else None,
        "policy_version": source_manifest.get("policy_version") if source_manifest else None,
        "source_rule_catalog_sha256": source_manifest.get("source_rule_catalog_sha256") if source_manifest else None,
        "templates": [],
    }
    records: list[dict[str, object]] = summary["templates"]  # type: ignore[assignment]
    selected_files: list[Path] = []
    if source_manifest is not None and (candidate or subject_id != "linear_algebra"):
        declared = source_manifest.get("generated_files")
        if not isinstance(declared, list):
            raise ValueError("Template manifest.generated_files는 리스트여야 합니다.")
        # Manifest에 들어간 파일만 실행. 파일 누락·중복도 명시적으로 보고.
        used_paths: set[Path] = set()
        for name in declared:
            if not isinstance(name, str):
                records.append({"status":"error","error":"잘못된 manifest 파일 경로", "template_file":str(name)})
                continue
            path = (selected_manifest.parent / name).resolve()
            if path in used_paths:
                records.append({"status":"error","error":"manifest 중복 경로", "template_file":str(path)})
                continue
            used_paths.add(path)
            if path.parent != template_root and template_root not in path.parents:
                records.append({"status":"error","error":"Template 루트 밖 파일 경로", "template_file":str(path)})
            else:
                selected_files.append(path)
        for upstream in source_manifest.get("records", []):
            if not isinstance(upstream, dict):
                continue
            if upstream.get("status") not in {"failed", "excluded", "skipped"}:
                continue
            if problem_type and upstream.get("problem_type") != problem_type:
                continue
            records.append({
                **upstream,
                "status": "upstream_failed" if upstream.get("status") == "failed" else "upstream_excluded",
                "origin": "template_build",
            })
    else:
        # 기존 선형대수 경로만 canonical 파일 선택을 유지한다.
        selected_files = sorted(template_root.rglob("*.json"))

    seen_ids: set[str] = set()
    for path in selected_files:
        try:
            if not path.is_file():
                raise FileNotFoundError(f"Template 파일이 없습니다: {path}")
            raw = json.loads(path.read_text(encoding="utf-8"))
            if raw.get("object_type") != "problem_template":
                if candidate:
                    raise ValueError("후보 manifest에 Template 외 파일이 포함되었습니다.")
                continue
            classification, taxonomy = raw["classification"], raw["taxonomy"]
            if taxonomy["subject_id"] != subject_id:
                raise ValueError("지정 과목과 다른 Template입니다.")
            if problem_type and classification["problem_type"] != problem_type:
                continue
            expected_name = _safe_name(
                f"{taxonomy['concept_ids'][0]}__{classification['problem_type']}.json"
            )
            if path.name != expected_name:
                if candidate:
                    raise ValueError("후보 manifest의 파일명이 canonical 형식이 아닙니다.")
                continue
            template_id = raw["template_id"]
            if template_id in seen_ids:
                raise ValueError(f"중복 template_id: {template_id}")
            seen_ids.add(template_id)
            record: dict[str, object] = {
                "template_id": template_id,
                "template_file": str(path),
                "unit_id": taxonomy["unit_id"],
                "problem_type": classification["problem_type"],
                "policy_version": summary["policy_version"],
                "seed_start": seed_start,
                "requested_count": count,
            }
            if (raw.get("executable") is not True
                or raw.get("status") == "deprecated"
                or (raw.get("status") != "ready" and not include_draft)):
                record.update(status="skipped", reason="실행 가능 상태 또는 검수 옵션 불충족")
            else:
                # 경로 길이 제한 및 문제 유형 충돌 방지
                name = _safe_name(classification["problem_type"])
                folder = batch_dir / name
                if folder.exists():
                    folder = batch_dir / (name + "_" + hashlib.sha256(template_id.encode()).hexdigest()[:8])
                _, result = save_previews(
                    path, output_root, seed_start=seed_start, count=count,
                    max_attempts=max_attempts, timeout_seconds=timeout_seconds,
                    output_dir_override=folder, include_draft=include_draft,
                )
                record.update(
                    status="completed" if result["failed"] == 0 else "partial_failure",
                    succeeded=result["succeeded"], failed=result["failed"],
                    timed_out=result["timed_out"],
                    result_dir=str(folder.relative_to(batch_dir)),
                    results=result["results"],
                )
            records.append(record)
        except Exception as exc:
            records.append({"template_file":str(path),"status":"error",
                            "error_type":type(exc).__name__,"error":str(exc)})
            print(f"[ERROR] {path}: {type(exc).__name__}: {_one_line(exc)}", flush=True)
        finally:
            (batch_dir / "manifest.json").write_text(_json_text(summary), encoding="utf-8")

    summary["completed"] = sum(r.get("status") == "completed" for r in records)
    summary["partial_failure"] = sum(r.get("status") == "partial_failure" for r in records)
    summary["skipped"] = sum(r.get("status") in {"skipped", "upstream_excluded"} for r in records)
    summary["errors"] = sum(r.get("status") in {"error", "upstream_failed"} for r in records)
    summary["upstream_failed"] = sum(r.get("status") == "upstream_failed" for r in records)
    summary["timed_out"] = sum(int(r.get("timed_out", 0)) for r in records)
    summary["units"] = sorted({r.get("unit_id") for r in records if r.get("unit_id")})
    (batch_dir / "manifest.json").write_text(_json_text(summary), encoding="utf-8")
    print(f"[SUMMARY] 성공 {summary['completed']} / 부분실패 {summary['partial_failure']} / "
          f"제외 {summary['skipped']} / 오류 {summary['errors']} / timeout {summary['timed_out']}",
          flush=True)
    if problem_type and not records:
        raise FileNotFoundError(f"해당 유형 Template이 없습니다: {subject_id}/{problem_type}")
    return batch_dir, summary


def save_all_linear_algebra_previews(template_root, output_root, **kwargs):
    """기존 선형대수 호출 API를 유지한다."""
    return save_subject_previews(template_root, output_root, subject_id="linear_algebra", **kwargs)


def main() -> int:
    """원본/후보 모드를 명확히 분리하여 검수용 문제만 생성한다."""
    parser = argparse.ArgumentParser(description="문제 템플릿에서 검수용 Preview 생성")
    parser.add_argument("--template", type=Path, default=None)
    parser.add_argument("--subject", choices=sorted(ENABLED_SUBJECT_IDS), default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--problem-type", default=None)
    parser.add_argument("--include-draft", action="store_true")
    parser.add_argument("--all-linear-algebra", action="store_true")
    parser.add_argument("--template-root", type=Path, default=None)
    parser.add_argument("--candidate-manifest", type=Path, default=None,
                        help="Part 2 후보 template manifest 경로")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--seed-start", type=int, default=17)
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--max-attempts", type=int, default=None)
    parser.add_argument("--timeout-seconds", type=float, default=300)
    args = parser.parse_args()

    if args.all_linear_algebra and args.subject not in {None, "linear_algebra"}:
        parser.error("--all-linear-algebra와 다른 과목은 함께 선택할 수 없습니다.")
    if args.template and (args.all or args.all_linear_algebra or args.problem_type or args.candidate_manifest):
        parser.error("--template은 전체/후보 manifest 모드와 함께 사용할 수 없습니다.")
    if args.all and not args.subject:
        parser.error("--all에는 --subject가 필요합니다.")
    if args.candidate_manifest and args.subject not in {None, "linear_algebra"}:
        parser.error("후보 manifest는 선형대수 전용입니다.")
    if args.candidate_manifest and not args.include_draft:
        parser.error("후보 실행에는 --include-draft를 명시해야 합니다.")

    subject = args.subject or "linear_algebra"
    if args.candidate_manifest:
        candidate_path = _path_from_project(args.candidate_manifest).resolve()
        default_root = candidate_path.parent / subject
        if args.template_root is not None and _path_from_project(args.template_root).resolve() != default_root.resolve():
            parser.error("후보 --template-root가 manifest의 생성 디렉터리와 다릅니다.")
        template_root = default_root
        if not (args.all or args.all_linear_algebra or args.problem_type):
            args.all_linear_algebra = True
    else:
        template_root = args.template_root or PROJECT_ROOT / "data" / "problem_templates" / subject

    if args.all_linear_algebra or args.all or args.problem_type:
        output_dir, summary = save_subject_previews(
            template_root, args.output_dir, seed_start=args.seed_start,
            count=args.count, max_attempts=args.max_attempts,
            timeout_seconds=args.timeout_seconds, subject_id=subject,
            problem_type=args.problem_type, include_draft=args.include_draft,
            manifest_path=args.candidate_manifest,
        )
        print(f"검수 결과: 성공 {summary['completed']}, 부분실패 {summary['partial_failure']}, "
              f"제외 {summary['skipped']}, 오류 {summary['errors']}, timeout {summary['timed_out']}")
        print(f"manifest: {output_dir / 'manifest.json'}")
        if summary["completed"] == 0:
            return 1
        if summary["partial_failure"] or summary["errors"] or summary["timed_out"]:
            return 1
        # 후보 모드에서 제외된 유형도 전체 성공으로 보고하지 않는다.
        if args.candidate_manifest and summary["skipped"]:
            return 1
        return 0

    if not args.template and subject != "linear_algebra":
        parser.error("새 과목은 --problem-type, --template, --all 중 하나를 지정해야 합니다.")
    if args.template and args.subject:
        selected = ProblemTemplate.model_validate_json(_path_from_project(args.template).read_bytes())
        if selected.taxonomy.subject_id != subject:
            parser.error("--template과 --subject가 일치하지 않습니다.")
    output_dir, manifest = save_previews(
        args.template or DEFAULT_TEMPLATE, args.output_dir,
        seed_start=args.seed_start, count=args.count,
        max_attempts=args.max_attempts, timeout_seconds=args.timeout_seconds,
        include_draft=args.include_draft,
    )
    print(f"검수용 문제: 성공 {manifest['succeeded']}/{args.count}, 실패 {manifest['failed']}")
    print(f"저장 위치: {output_dir}")
    return 0 if manifest["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
