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
    # TODO[LA-D035] save_subject_previews 구현
    # 1. 6단원의 최신 후보 manifest를 실행 대상으로 삼고 오래된 ready/draft 사본을 섞지 않는다.
    # 2. 단원·유형·정책 버전·seed·시도 수를 기록하고 후보 실행은 검수용 옵션으로만 허용한다.
    raise NotImplementedError("TODO[LA-D035]: save_subject_previews")


def save_all_linear_algebra_previews(template_root, output_root, **kwargs):
    """기존 선형대수 호출 API를 유지한다."""
    return save_subject_previews(template_root, output_root, subject_id="linear_algebra", **kwargs)


def main() -> int:
    # TODO[LA-D036] main 구현
    # 1. 원본 템플릿 경로와 후보 재생성 템플릿 경로를 분리한다.
    # 2. 생성기에서 제외/부분 실패한 유형도 최종 검증 보고서에서 누락되지 않도록 전달한다.
    raise NotImplementedError("TODO[LA-D036]: main")


if __name__ == "__main__":
    raise SystemExit(main())
