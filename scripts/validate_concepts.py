from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path
from typing import Any

from pydantic import ValidationError


# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# app 모듈을 import할 수 있도록 프로젝트 루트를 Python 경로에 추가
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.schemas.concept import ConceptCatalog


CONCEPTS_DIR = PROJECT_ROOT / "data" / "concepts"
REPORT_PATH = PROJECT_ROOT / "validation_report.txt"


def format_location(location: tuple[Any, ...]) -> str:
    """
    Pydantic 오류 위치를 사람이 읽기 쉬운 형태로 변환한다.

    예:
    concepts → 3 → formulas → 0 → cas
    """
    if not location:
        return "(최상위 JSON)"

    return " → ".join(str(item) for item in location)


def shorten_value(value: Any, max_length: int = 200) -> str:
    """오류가 발생한 실제 입력값을 짧게 표시한다."""

    try:
        rendered = json.dumps(
            value,
            ensure_ascii=False,
            default=str,
        )
    except (TypeError, ValueError):
        rendered = repr(value)

    if len(rendered) > max_length:
        return rendered[:max_length] + "..."

    return rendered


def format_validation_errors(
    error: ValidationError,
) -> list[str]:
    """Pydantic ValidationError를 자세한 문자열 목록으로 변환한다."""

    messages: list[str] = []

    for index, item in enumerate(
        error.errors(include_url=False),
        start=1,
    ):
        location = format_location(item.get("loc", ()))
        message = item.get("msg", "알 수 없는 검증 오류")
        error_type = item.get("type", "unknown")
        input_value = shorten_value(item.get("input"))

        messages.append(
            "\n".join(
                [
                    f"  오류 {index}",
                    f"    위치: {location}",
                    f"    내용: {message}",
                    f"    유형: {error_type}",
                    f"    입력값: {input_value}",
                ]
            )
        )

    return messages


def validate_catalog_file(
    file_path: Path,
) -> tuple[ConceptCatalog | None, list[str]]:
    """JSON 파일 하나를 읽고 ConceptCatalog Schema로 검증한다."""

    errors: list[str] = []

    # 1. 파일 읽기
    try:
        raw_text = file_path.read_text(encoding="utf-8-sig")
    except OSError as error:
        return None, [
            f"파일 읽기 실패: {type(error).__name__}: {error}"
        ]

    # 2. JSON 문법 검사
    try:
        raw_data = json.loads(raw_text)
    except json.JSONDecodeError as error:
        return None, [
            "\n".join(
                [
                    "JSON 문법 오류",
                    f"  위치: {error.lineno}행 {error.colno}열",
                    f"  내용: {error.msg}",
                ]
            )
        ]

    # 3. Pydantic Schema 검사
    try:
        catalog = ConceptCatalog.model_validate(raw_data)

    except ValidationError as error:
        return None, format_validation_errors(error)

    except Exception as error:
        # 예상하지 못한 Python 오류도 숨기지 않고 출력
        return None, [
            "\n".join(
                [
                    "예상하지 못한 검증 오류",
                    f"  유형: {type(error).__name__}",
                    f"  내용: {error}",
                    "",
                    traceback.format_exc(),
                ]
            )
        ]

    # 4. 폴더명과 subject_id 일치 검사
    try:
        relative_path = file_path.relative_to(CONCEPTS_DIR)
    except ValueError:
        relative_path = file_path

    if len(relative_path.parts) >= 2:
        subject_folder = relative_path.parts[0]
        subject_id = catalog.subject.subject_id

        if subject_folder != subject_id:
            errors.append(
                "\n".join(
                    [
                        "과목 폴더와 subject_id가 일치하지 않습니다.",
                        f"  폴더명: {subject_folder}",
                        f"  subject_id: {subject_id}",
                    ]
                )
            )

    if errors:
        return None, errors

    return catalog, []


def collect_json_files() -> list[Path]:
    """
    실행 인자가 있으면 지정한 파일이나 폴더만 검사하고,
    없으면 data/concepts 전체를 검사한다.
    """

    if len(sys.argv) == 1:
        return sorted(CONCEPTS_DIR.rglob("*.json"))

    target = Path(sys.argv[1])

    if not target.is_absolute():
        target = PROJECT_ROOT / target

    target = target.resolve()

    if target.is_file():
        if target.suffix.lower() != ".json":
            raise ValueError(
                f"JSON 파일이 아닙니다: {target}"
            )

        return [target]

    if target.is_dir():
        return sorted(target.rglob("*.json"))

    raise FileNotFoundError(
        f"검사 대상이 존재하지 않습니다: {target}"
    )


def output(
    message: str,
    report_lines: list[str],
) -> None:
    """터미널과 검증 보고서에 동시에 기록한다."""

    print(message)
    report_lines.append(message)


def main() -> None:
    report_lines: list[str] = []

    try:
        json_files = collect_json_files()
    except Exception as error:
        print(f"[실행 실패] {type(error).__name__}: {error}")
        raise SystemExit(1)

    if not json_files:
        print(f"검증할 JSON 파일이 없습니다: {CONCEPTS_DIR}")
        raise SystemExit(1)

    passed_files = 0
    failed_files = 0
    passed_concepts = 0

    # 전체 JSON 파일 사이의 concept_id 중복 검사
    concept_locations: dict[str, Path] = {}
    duplicated_concepts: list[str] = []

    output(
        f"검증 대상 JSON 파일: {len(json_files)}개",
        report_lines,
    )
    output("=" * 70, report_lines)

    for file_path in json_files:
        try:
            display_path = file_path.relative_to(PROJECT_ROOT)
        except ValueError:
            display_path = file_path

        catalog, errors = validate_catalog_file(file_path)

        if errors:
            failed_files += 1

            output("", report_lines)
            output(f"[실패] {display_path}", report_lines)

            for error in errors:
                output(error, report_lines)

            continue

        if catalog is None:
            failed_files += 1
            output("", report_lines)
            output(
                f"[실패] {display_path}: 검증 결과가 없습니다.",
                report_lines,
            )
            continue

        passed_files += 1
        passed_concepts += len(catalog.concepts)

        output(
            (
                f"[통과] {display_path} "
                f"({len(catalog.concepts)}개 Concept)"
            ),
            report_lines,
        )

        for concept in catalog.concepts:
            previous_path = concept_locations.get(
                concept.concept_id
            )

            if previous_path is not None:
                duplicated_concepts.append(
                    "\n".join(
                        [
                            f"concept_id: {concept.concept_id}",
                            f"  기존 파일: {previous_path}",
                            f"  중복 파일: {display_path}",
                        ]
                    )
                )
            else:
                concept_locations[concept.concept_id] = display_path

    output("", report_lines)
    output("=" * 70, report_lines)
    output(
        f"전체 JSON 파일: {len(json_files)}",
        report_lines,
    )
    output(
        f"검증 통과 파일: {passed_files}",
        report_lines,
    )
    output(
        f"검증 실패 파일: {failed_files}",
        report_lines,
    )
    output(
        f"검증 통과 Concept: {passed_concepts}",
        report_lines,
    )

    if duplicated_concepts:
        output("", report_lines)
        output(
            "[전체 파일 사이 concept_id 중복]",
            report_lines,
        )

        for duplicate in duplicated_concepts:
            output(duplicate, report_lines)

        failed_files += len(duplicated_concepts)

    REPORT_PATH.write_text(
        "\n".join(report_lines),
        encoding="utf-8",
    )

    output("", report_lines)
    print(f"상세 보고서 저장 위치: {REPORT_PATH}")

    if failed_files > 0:
        print()
        print("Concept JSON 검증에 실패했습니다.")
        raise SystemExit(1)

    print()
    print("모든 Concept JSON이 Schema 검증을 통과했습니다.")


if __name__ == "__main__":
    main()