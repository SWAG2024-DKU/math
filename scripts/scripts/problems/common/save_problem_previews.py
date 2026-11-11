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
) -> tuple[Path, dict[str, object]]:
    """지정 과목의 현재 정식 이름 Template을 순회하고 유형별 결과를 기록한다.

    과거 생성기가 남긴 숫자 접두사 파일은 현재 Template의 중복본이므로 제외한다.
    draft 및 executable=False 항목은 시험 생성 대상에서 제외한다.
    """
    if subject_id not in ENABLED_SUBJECT_IDS:
        raise ValueError(f"미지원 과목: {subject_id}")
    if count < 1 or (max_attempts is not None and max_attempts < 1):
        raise ValueError("count와 max_attempts는 1 이상이어야 합니다.")
    if not 0 < timeout_seconds < float("inf"):
        raise ValueError("timeout_seconds는 유한한 양수여야 합니다.")
    template_root = _path_from_project(template_root)
    output_root = _path_from_project(output_root)
    if not template_root.is_dir():
        raise FileNotFoundError(f"Template 디렉터리가 없습니다: {template_root}")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
    batch_dir = output_root / subject_id / f"all_{run_id}"
    batch_dir.mkdir(parents=True, exist_ok=False)
    summary: dict[str, object] = {
        "purpose": "temporary_human_review",
        "publishable": False,
        "subject_id": subject_id,
        "problem_type_filter": problem_type,
        "include_draft": include_draft,
        "seed_start": seed_start,
        "seeds_per_template": count,
        "timeout_seconds": timeout_seconds,
        "templates": [],
    }
    records: list[dict[str, object]] = summary["templates"]  # type: ignore[assignment]
    seen_ids: set[str] = set()
    # 추가 과목은 최근 빌더의 manifest를 이용해 과거 draft 잔여물을 실행하지 않는다.
    # 선형대수의 기존 파일 선택 경로는 유지한다.
    current_files = None
    manifest_path = template_root.parent / f"manifest_{subject_id}.json"
    if subject_id != "linear_algebra" and manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("subject_filter") != subject_id:
            raise ValueError("Template manifest 과목 불일치")
        current_files = {(manifest_path.parent / name).resolve() for name in manifest["generated_files"]}
        if not current_files or any(not path.is_file() for path in current_files):
            raise ValueError("최신 Template manifest가 비었거나 파일이 없습니다. Template을 재생성하세요.")
    for path in sorted(template_root.rglob("*.json")):
        if current_files is not None and path.resolve() not in current_files:
            continue
        if path.name.startswith("manifest"):
            continue
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if raw.get("object_type") != "problem_template":
                continue
            classification = raw["classification"]
            taxonomy = raw["taxonomy"]
            if taxonomy["subject_id"] != subject_id:
                raise ValueError("지정 과목과 다른 Template이 포함되었습니다.")
            if problem_type and classification["problem_type"] != problem_type:
                continue
            expected_name = _safe_name(
                f"{taxonomy['concept_ids'][0]}__{classification['problem_type']}.json"
            )
            # 구 빌더의 숫자 접두사 복사본은 최신 canonical 파일로 대체한다.
            if path.name != expected_name:
                continue
            template_id = raw["template_id"]
            if template_id in seen_ids:
                raise ValueError(f"중복 template_id: {template_id}")
            seen_ids.add(template_id)
            record: dict[str, object] = {"template_id": template_id, "template_file": str(path)}
            if raw.get("executable") is not True or raw.get("status") == "deprecated" or (raw.get("status") != "ready" and not include_draft):
                record.update(status="skipped", reason="실행 가능 상태/옵션 조건 미충족")
                print(
                    f"[SKIP] {classification['problem_type']} | {template_id} | "
                    "실행 가능 상태/옵션 조건 미충족",
                    flush=True,
                )
            else:
                # Windows의 MAX_PATH 제한을 피하기 위해 긴 template_id를
                # 디렉터리명으로 다시 사용하지 않는다. 문제 유형은 현재
                # 선형대수 Catalog에서 고유하며, 충돌 시 짧은 해시를 붙인다.
                problem_type_dir = batch_dir / _safe_name(classification["problem_type"])
                folder = problem_type_dir
                if folder.exists():
                    short_hash = hashlib.sha256(template_id.encode("utf-8")).hexdigest()[:8]
                    folder = batch_dir / f"{_safe_name(classification['problem_type'])}_{short_hash}"
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
                )
            records.append(record)
        except Exception as exc:
            records.append({
                "template_file": str(path), "status": "error",
                "error_type": type(exc).__name__, "error": str(exc),
            })
            print(
                f"[ERROR] {path} | {type(exc).__name__}: {_one_line(exc)}",
                flush=True,
            )
        finally:
            (batch_dir / "manifest.json").write_text(_json_text(summary), encoding="utf-8")
    summary["completed"] = sum(r.get("status") == "completed" for r in records)
    summary["partial_failure"] = sum(r.get("status") == "partial_failure" for r in records)
    summary["skipped"] = sum(r.get("status") == "skipped" for r in records)
    summary["errors"] = sum(r.get("status") == "error" for r in records)
    summary["timed_out"] = sum(int(r.get("timed_out", 0)) for r in records)
    (batch_dir / "manifest.json").write_text(_json_text(summary), encoding="utf-8")
    print(
        f"[SUMMARY] 전부 성공 {summary['completed']}, 일부 실패 {summary['partial_failure']}, "
        f"제외 {summary['skipped']}, 제한 시간 초과 seed {summary['timed_out']}, "
        f"파일 오류 {summary['errors']}",
        flush=True,
    )
    if problem_type and not records:
        raise FileNotFoundError(f"해당 유형의 canonical Template이 없습니다: {subject_id}/{problem_type}")
    return batch_dir, summary


def save_all_linear_algebra_previews(template_root, output_root, **kwargs):
    """기존 선형대수 호출 API를 유지한다."""
    return save_subject_previews(template_root, output_root, subject_id="linear_algebra", **kwargs)


def main() -> int:
    parser = argparse.ArgumentParser(description="지정 과목의 검증된 문제를 검수용 JSON으로 저장")
    parser.add_argument("--template", type=Path, default=None)
    parser.add_argument("--subject", choices=sorted(ENABLED_SUBJECT_IDS), default=None)
    parser.add_argument("--all", action="store_true", help="지정 과목의 전체 Template 실행")
    parser.add_argument("--problem-type", help="해당 문제 유형만 실행")
    parser.add_argument("--include-draft", action="store_true", help="executable=True인 draft를 검수용으로 실행")
    parser.add_argument("--all-linear-algebra", action="store_true", help="선형대수 전체 Template 시험 생성")
    parser.add_argument("--template-root", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--seed-start", type=int, default=17)
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--max-attempts", type=int, default=None)
    parser.add_argument("--timeout-seconds", type=float, default=300,
                        help="seed당 최대 실행 시간(초), 기본 300초")
    args = parser.parse_args()

    if args.all_linear_algebra and args.subject not in {None, "linear_algebra"}:
        parser.error("--all-linear-algebra는 다른 --subject와 함께 사용할 수 없습니다.")
    if args.template and (args.all or args.all_linear_algebra or args.problem_type):
        parser.error("--template과 전체/유형 선택 옵션은 함께 사용할 수 없습니다.")
    if args.all and not args.subject:
        parser.error("--all에는 --subject를 명시해야 합니다.")
    subject = args.subject or "linear_algebra"
    template_root = args.template_root or PROJECT_ROOT / "data" / "problem_templates" / subject
    if args.all_linear_algebra or args.all or args.problem_type:
        output_dir, summary = save_subject_previews(
            template_root, args.output_dir, seed_start=args.seed_start,
            count=args.count, max_attempts=args.max_attempts,
            timeout_seconds=args.timeout_seconds, subject_id=subject,
            problem_type=args.problem_type, include_draft=args.include_draft,
        )
        print(
            f"유형 결과: 전부 성공 {summary['completed']}, 일부 실패 {summary['partial_failure']}, "
            f"제외 {summary['skipped']}, 제한 시간 초과 seed {summary['timed_out']}, "
            f"파일 오류 {summary['errors']}"
        )
        print(f"저장 위치: {output_dir}")
        if subject != "linear_algebra" and summary["completed"] == 0:
            return 1
        return 0 if not summary["partial_failure"] and not summary["errors"] else 1

    if not args.template and subject != "linear_algebra":
        parser.error("새 과목은 --problem-type 또는 --template 또는 --all을 지정해야 합니다.")
    if args.template and args.subject:
        selected = ProblemTemplate.model_validate_json(_path_from_project(args.template).read_bytes())
        if selected.taxonomy.subject_id != subject:
            parser.error("--template의 과목과 --subject가 다릅니다.")
    output_dir, manifest = save_previews(
        args.template or DEFAULT_TEMPLATE,
        args.output_dir,
        seed_start=args.seed_start,
        count=args.count,
        max_attempts=args.max_attempts,
        timeout_seconds=args.timeout_seconds, include_draft=args.include_draft,
    )
    print(f"검수용 문제: 성공 {manifest['succeeded']}/{args.count}, 실패 {manifest['failed']}")
    print(f"저장 위치: {output_dir}")
    print(f"사람 검수용 목록: {output_dir / 'review.md'}")
    return 0 if manifest["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
