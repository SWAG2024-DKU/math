from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from transformers import AutoTokenizer
except ImportError:
    AutoTokenizer = None  # type: ignore[assignment]


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_DIR = PROJECT_ROOT / "data" / "chunks"
REPORT_DIR = PROJECT_ROOT / "scripts" / "search"
JSON_REPORT_PATH = REPORT_DIR / "chunk_validation_report.json"
TEXT_REPORT_PATH = REPORT_DIR / "chunk_validation_report.txt"

ALLOWED_CHUNK_TYPES = {
    "definition",
    "formula",
    "condition",
    "property",
    "learning",
    "misconception",
    "generation",
}

EXPECTED_INFO_TYPE = {
    "definition": "정의 및 개요",
    "formula": "핵심 공식",
    "condition": "적용 조건",
    "property": "주요 성질",
    "learning": "선수 및 학습 관계",
    "misconception": "오개념 및 피드백",
    "generation": "문제 생성 정보",
}

EXPECTED_MARKERS = {
    "definition": ["개념 정의", "정의:"],
    "formula": ["핵심 공식", "공식명:", "공식 ID:", "LaTeX:"],
    "condition": ["공식 및 개념의 적용 조건", "조건 ID:", "설명:", "검증 규칙:"],
    "property": ["주요 성질", "성질 ID:", "설명:"],
    "learning": ["선수 개념·관련 개념·학습 목표"],
    "misconception": [
        "자주 발생하는 오개념과 피드백",
        "오개념:",
        "오개념 ID:",
        "설명:",
        "진단 태그:",
        "피드백:",
    ],
    "generation": ["문제 생성 프로필"],
}

LEARNING_ANY_MARKERS = ("선수 개념:", "관련 개념:", "학습 목표 ID:")
GENERATION_ANY_MARKERS = (
    "문제 생성 활성화:",
    "지원 문제 유형:",
    "지원 정답 유형:",
    "난이도 범위:",
    "권장 검증기:",
)

SENTENCE_PREFIXES = (
    "정의:",
    "설명:",
    "목표:",
    "피드백:",
    "생성 참고사항:",
)

SENTENCE_END_PATTERN = re.compile(r"[.!?。！？][\"'”’）)\]}]*$")
SUSPICIOUS_FINAL_PATTERN = re.compile(r"(?:[,;:]|[+*/=]|(?<!\d)-|\\)$")
SUSPICIOUS_KOREAN_ENDINGS = (
    "그리고",
    "또한",
    "하지만",
    "그러나",
    "따라서",
    "즉",
    "또는",
    "및",
    "때문에",
    "통하여",
    "활용하여",
    "적용하여",
    "계산하여",
    "구하여",
    "이며",
    "이고",
    "하거나",
)

TOKENIZER_CACHE: dict[str, Any] = {}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Chunk JSON 파일의 구조, 내용, 토큰 수를 종합 검사함."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help="검사할 JSON 파일 또는 폴더. 기본값: data/chunks",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=None,
        help="설정하면 JSON의 max_tokens 대신 이 값을 강제로 사용함.",
    )
    parser.add_argument(
        "--skip-token-recount",
        action="store_true",
        help="Tokenizer로 실제 token_count를 다시 계산하지 않음.",
    )
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="WARNING만 있어도 종료 코드 1을 반환함.",
    )
    return parser.parse_args()


def relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def add_issue(
    issues: list[dict[str, Any]],
    *,
    severity: str,
    code: str,
    message: str,
    file_path: Path,
    concept_id: str = "",
    chunk_index: int | str = "",
    chunk_type: str = "",
    excerpt: str = "",
) -> None:
    issues.append(
        {
            "severity": severity,
            "code": code,
            "message": message,
            "file": relative_path(file_path),
            "concept_id": concept_id,
            "chunk_index": chunk_index,
            "chunk_type": chunk_type,
            "excerpt": excerpt[:500],
        }
    )


def find_json_files(input_path: Path) -> list[Path]:
    if input_path.is_file():
        if input_path.suffix.lower() != ".json":
            raise ValueError("입력 파일은 .json 파일이어야 함.")
        return [input_path]

    if not input_path.exists():
        raise FileNotFoundError(f"입력 경로가 존재하지 않음: {input_path}")

    return sorted(input_path.rglob("*.json"))


def safe_file_stem(concept_id: str) -> str:
    return concept_id.replace("/", "_").replace("\\", "_").replace(":", "_")


def extract_header(content_text: str) -> dict[str, str]:
    """content_text 첫 번째 문단의 공통 헤더만 추출함."""
    header_block = content_text.split("\n\n", 1)[0]
    result: dict[str, str] = {}

    key_map = {
        "과목:": "subject_name",
        "단원:": "chapter_name",
        "개념:": "concept_name",
        "개념 ID:": "concept_id",
        "정보 유형:": "info_type",
    }

    for raw_line in header_block.splitlines():
        line = raw_line.strip()
        for prefix, key in key_map.items():
            if line.startswith(prefix):
                result[key] = line[len(prefix) :].strip()
                break

    return result


def check_balanced_delimiters(text: str) -> tuple[bool, str]:
    pairs = {")": "(", "]": "[", "}": "{"}
    opening = set(pairs.values())
    stack: list[tuple[str, int]] = []

    escaped = False
    for position, character in enumerate(text):
        if escaped:
            escaped = False
            continue
        if character == "\\":
            escaped = True
            continue

        if character in opening:
            stack.append((character, position))
        elif character in pairs:
            if not stack:
                return False, f"닫는 괄호 {character!r} 앞에 여는 괄호가 없음."
            last_character, _ = stack.pop()
            if last_character != pairs[character]:
                return False, (
                    f"괄호 순서 불일치: {last_character!r} 다음에 "
                    f"{character!r}가 나타남."
                )

    if stack:
        character, position = stack[-1]
        return False, f"여는 괄호 {character!r}가 닫히지 않음. 위치: {position}"

    return True, ""


def check_latex(latex: str) -> list[tuple[str, str]]:
    problems: list[tuple[str, str]] = []

    ok, message = check_balanced_delimiters(latex)
    if not ok:
        problems.append(("LATEX_DELIMITER_MISMATCH", message))

    begin_envs = re.findall(r"\\begin\{([^{}]+)\}", latex)
    end_envs = re.findall(r"\\end\{([^{}]+)\}", latex)
    if begin_envs != end_envs:
        problems.append(
            (
                "LATEX_ENVIRONMENT_MISMATCH",
                f"begin={begin_envs}, end={end_envs}",
            )
        )

    if re.search(r"\\[A-Za-z]+$", latex.strip()):
        problems.append(
            (
                "INCOMPLETE_LATEX_COMMAND",
                "LaTeX가 명령어 이름으로 끝나 중간 절단 가능성이 있음.",
            )
        )

    return problems


def check_cas(cas: str) -> list[tuple[str, str]]:
    problems: list[tuple[str, str]] = []

    ok, message = check_balanced_delimiters(cas)
    if not ok:
        problems.append(("CAS_DELIMITER_MISMATCH", message))

    if SUSPICIOUS_FINAL_PATTERN.search(cas.strip()):
        problems.append(
            (
                "SUSPICIOUS_CAS_END",
                "CAS 표현이 연산자 또는 구분자로 끝남.",
            )
        )

    return problems


def check_sentence_line(line: str) -> list[tuple[str, str]]:
    problems: list[tuple[str, str]] = []
    prefix = next((item for item in SENTENCE_PREFIXES if line.startswith(item)), None)

    if prefix is None:
        return problems

    sentence = line[len(prefix) :].strip()
    if not sentence:
        return [("EMPTY_SEMANTIC_SENTENCE", f"{prefix} 뒤의 내용이 비어 있음.")]

    if not SENTENCE_END_PATTERN.search(sentence):
        problems.append(
            (
                "SUSPICIOUS_SENTENCE_END",
                f"{prefix} 문장이 종결 문장부호로 끝나지 않음.",
            )
        )

    if sentence.endswith(SUSPICIOUS_KOREAN_ENDINGS):
        problems.append(
            (
                "INCOMPLETE_KOREAN_SENTENCE",
                "문장이 연결 표현으로 끝나 중간 절단 가능성이 있음.",
            )
        )

    if SUSPICIOUS_FINAL_PATTERN.search(sentence):
        problems.append(
            (
                "SUSPICIOUS_SEMANTIC_END",
                "문장이 구분자 또는 연산자로 끝남.",
            )
        )

    return problems


def validate_repeated_blocks(
    *,
    content_text: str,
    marker: str,
    required_fields: tuple[str, ...],
    block_name: str,
) -> list[tuple[str, str, str]]:
    """공식·조건·오개념 묶음에서 필수 필드가 함께 유지됐는지 검사함."""
    results: list[tuple[str, str, str]] = []
    parts = content_text.split(marker)[1:]

    if not parts:
        return [
            (
                f"MISSING_{block_name}_BLOCK",
                f"{marker}로 시작하는 {block_name} 묶음을 찾지 못함.",
                content_text,
            )
        ]

    for block_number, part in enumerate(parts, start=1):
        block = marker + part
        for field in required_fields:
            if field not in block:
                results.append(
                    (
                        f"INCOMPLETE_{block_name}_BLOCK",
                        f"{block_name} {block_number}번 묶음에 {field}가 없음.",
                        block,
                    )
                )

    return results


def get_tokenizer(model_name: str) -> Any:
    if AutoTokenizer is None:
        raise RuntimeError("transformers가 설치되지 않음.")

    if model_name not in TOKENIZER_CACHE:
        print(f"Tokenizer 불러오는 중: {model_name}")
        TOKENIZER_CACHE[model_name] = AutoTokenizer.from_pretrained(model_name)

    return TOKENIZER_CACHE[model_name]


def recount_tokens(model_name: str, text: str) -> int:
    tokenizer = get_tokenizer(model_name)
    encoded = tokenizer(
        text,
        add_special_tokens=True,
        truncation=False,
    )
    return len(encoded["input_ids"])


def validate_chunk(
    *,
    chunk: dict[str, Any],
    list_index: int,
    document: dict[str, Any],
    file_path: Path,
    configured_max_tokens: int | None,
    skip_token_recount: bool,
    issues: list[dict[str, Any]],
) -> None:
    document_concept_id = str(document.get("concept_id", ""))
    document_subject_id = str(document.get("subject_id", ""))
    document_chapter_id = str(document.get("chapter_id", ""))
    document_concept_name = str(document.get("concept_name_ko", ""))

    concept_id = str(chunk.get("concept_id", ""))
    subject_id = str(chunk.get("subject_id", ""))
    chapter_id = str(chunk.get("chapter_id", ""))
    concept_name = str(chunk.get("concept_name_ko", ""))
    chunk_index = chunk.get("chunk_index", "")
    chunk_type = str(chunk.get("chunk_type", ""))
    content_text = chunk.get("content_text")

    # 1, 9. Concept 혼합 및 ID 일치 검사
    for field_name, chunk_value, document_value in (
        ("concept_id", concept_id, document_concept_id),
        ("subject_id", subject_id, document_subject_id),
        ("chapter_id", chapter_id, document_chapter_id),
        ("concept_name_ko", concept_name, document_concept_name),
    ):
        if chunk_value != document_value:
            add_issue(
                issues,
                severity="ERROR",
                code="CHUNK_DOCUMENT_IDENTITY_MISMATCH",
                message=(
                    f"Chunk의 {field_name}={chunk_value!r}가 "
                    f"최상위 값 {document_value!r}와 다름."
                ),
                file_path=file_path,
                concept_id=concept_id,
                chunk_index=chunk_index,
                chunk_type=chunk_type,
            )

    # 10. 순서 검사
    if chunk_index != list_index:
        add_issue(
            issues,
            severity="ERROR",
            code="CHUNK_INDEX_ORDER_MISMATCH",
            message=f"배열 위치는 {list_index}인데 chunk_index는 {chunk_index!r}임.",
            file_path=file_path,
            concept_id=concept_id,
            chunk_index=chunk_index,
            chunk_type=chunk_type,
        )

    # 8. 빈 content_text 검사
    if not isinstance(content_text, str):
        add_issue(
            issues,
            severity="ERROR",
            code="CONTENT_TEXT_NOT_STRING",
            message="content_text가 문자열이 아님.",
            file_path=file_path,
            concept_id=concept_id,
            chunk_index=chunk_index,
            chunk_type=chunk_type,
            excerpt=repr(content_text),
        )
        return

    if not content_text.strip():
        add_issue(
            issues,
            severity="ERROR",
            code="EMPTY_CONTENT_TEXT",
            message="content_text가 비어 있음.",
            file_path=file_path,
            concept_id=concept_id,
            chunk_index=chunk_index,
            chunk_type=chunk_type,
        )
        return

    header = extract_header(content_text)

    # 공통 헤더가 중복되면 두 Chunk 또는 다른 Concept가 합쳐졌을 가능성이 큼.
    for header_marker in ("과목:", "단원:", "개념:", "개념 ID:", "정보 유형:"):
        marker_count = sum(
            1
            for line in content_text.splitlines()
            if line.strip().startswith(header_marker)
        )
        if marker_count != 1:
            add_issue(
                issues,
                severity="ERROR",
                code="COMMON_HEADER_COUNT_INVALID",
                message=(
                    f"공통 헤더 {header_marker!r}가 {marker_count}개임. "
                    "다른 Chunk 또는 Concept가 합쳐졌는지 확인해야 함."
                ),
                file_path=file_path,
                concept_id=concept_id,
                chunk_index=chunk_index,
                chunk_type=chunk_type,
                excerpt=content_text,
            )

    if header.get("concept_id") != document_concept_id:
        add_issue(
            issues,
            severity="ERROR",
            code="CONTENT_HEADER_CONCEPT_MISMATCH",
            message=(
                f"content_text 헤더의 개념 ID={header.get('concept_id')!r}가 "
                f"최상위 concept_id={document_concept_id!r}와 다름."
            ),
            file_path=file_path,
            concept_id=concept_id,
            chunk_index=chunk_index,
            chunk_type=chunk_type,
            excerpt=content_text.split("\n\n", 1)[0],
        )

    if header.get("concept_name") != document_concept_name:
        add_issue(
            issues,
            severity="ERROR",
            code="CONTENT_HEADER_CONCEPT_NAME_MISMATCH",
            message=(
                f"content_text 헤더의 개념명={header.get('concept_name')!r}가 "
                f"최상위 개념명={document_concept_name!r}와 다름."
            ),
            file_path=file_path,
            concept_id=concept_id,
            chunk_index=chunk_index,
            chunk_type=chunk_type,
            excerpt=content_text.split("\n\n", 1)[0],
        )

    # 2. Chunk 유형 적절성 검사
    if chunk_type not in ALLOWED_CHUNK_TYPES:
        add_issue(
            issues,
            severity="ERROR",
            code="INVALID_CHUNK_TYPE",
            message=f"허용되지 않은 chunk_type: {chunk_type!r}",
            file_path=file_path,
            concept_id=concept_id,
            chunk_index=chunk_index,
            chunk_type=chunk_type,
        )
    else:
        expected_info_type = EXPECTED_INFO_TYPE[chunk_type]
        if header.get("info_type") != expected_info_type:
            add_issue(
                issues,
                severity="ERROR",
                code="CHUNK_TYPE_HEADER_MISMATCH",
                message=(
                    f"chunk_type={chunk_type!r}이면 정보 유형은 "
                    f"{expected_info_type!r}이어야 하나 {header.get('info_type')!r}임."
                ),
                file_path=file_path,
                concept_id=concept_id,
                chunk_index=chunk_index,
                chunk_type=chunk_type,
            )

        for marker in EXPECTED_MARKERS[chunk_type]:
            if marker not in content_text:
                add_issue(
                    issues,
                    severity="ERROR",
                    code="MISSING_TYPE_MARKER",
                    message=f"{chunk_type} Chunk에 필수 표식 {marker!r}가 없음.",
                    file_path=file_path,
                    concept_id=concept_id,
                    chunk_index=chunk_index,
                    chunk_type=chunk_type,
                    excerpt=content_text,
                )

        if chunk_type == "learning" and not any(
            marker in content_text for marker in LEARNING_ANY_MARKERS
        ):
            add_issue(
                issues,
                severity="ERROR",
                code="EMPTY_LEARNING_CONTENT",
                message="learning Chunk에 선수·관련·학습 목표 정보가 하나도 없음.",
                file_path=file_path,
                concept_id=concept_id,
                chunk_index=chunk_index,
                chunk_type=chunk_type,
                excerpt=content_text,
            )

        if chunk_type == "generation" and not any(
            marker in content_text for marker in GENERATION_ANY_MARKERS
        ):
            add_issue(
                issues,
                severity="ERROR",
                code="EMPTY_GENERATION_CONTENT",
                message="generation Chunk에 생성 프로필 정보가 없음.",
                file_path=file_path,
                concept_id=concept_id,
                chunk_index=chunk_index,
                chunk_type=chunk_type,
                excerpt=content_text,
            )

        # 다른 유형의 핵심 표식이 들어가면 유형 혼합 가능성이 있음.
        foreign_markers = {
            "공식명:": "formula",
            "조건 ID:": "condition",
            "성질 ID:": "property",
            "오개념 ID:": "misconception",
            "학습 목표 ID:": "learning",
            "문제 생성 활성화:": "generation",
        }
        for marker, owner_type in foreign_markers.items():
            if owner_type != chunk_type and marker in content_text:
                add_issue(
                    issues,
                    severity="ERROR",
                    code="CHUNK_TYPE_CONTENT_MIXED",
                    message=(
                        f"{chunk_type} Chunk에 {owner_type} 유형 표식 "
                        f"{marker!r}가 포함됨."
                    ),
                    file_path=file_path,
                    concept_id=concept_id,
                    chunk_index=chunk_index,
                    chunk_type=chunk_type,
                    excerpt=content_text,
                )

    # 3. 공식명, 역할, LaTeX 묶음 유지 검사
    # CAS는 선택 필드이며, 존재할 때만 아래에서 구조를 검사함.
    if chunk_type == "formula":
        block_problems = validate_repeated_blocks(
            content_text=content_text,
            marker="공식명:",
            required_fields=("공식 ID:", "역할:", "LaTeX:"),
            block_name="FORMULA",
        )
        for code, message, excerpt in block_problems:
            add_issue(
                issues,
                severity="ERROR",
                code=code,
                message=message,
                file_path=file_path,
                concept_id=concept_id,
                chunk_index=chunk_index,
                chunk_type=chunk_type,
                excerpt=excerpt,
            )

    # 4. 조건 설명과 검증 규칙 묶음 유지 검사
    if chunk_type == "condition":
        block_problems = validate_repeated_blocks(
            content_text=content_text,
            marker="조건 ID:",
            required_fields=("설명:", "검증 규칙:"),
            block_name="CONDITION",
        )
        for code, message, excerpt in block_problems:
            add_issue(
                issues,
                severity="ERROR",
                code=code,
                message=message,
                file_path=file_path,
                concept_id=concept_id,
                chunk_index=chunk_index,
                chunk_type=chunk_type,
                excerpt=excerpt,
            )

    # 5. 오개념 설명과 피드백 묶음 유지 검사
    if chunk_type == "misconception":
        block_problems = validate_repeated_blocks(
            content_text=content_text,
            marker="오개념:",
            required_fields=("오개념 ID:", "설명:", "진단 태그:", "피드백:"),
            block_name="MISCONCEPTION",
        )
        for code, message, excerpt in block_problems:
            add_issue(
                issues,
                severity="ERROR",
                code=code,
                message=message,
                file_path=file_path,
                concept_id=concept_id,
                chunk_index=chunk_index,
                chunk_type=chunk_type,
                excerpt=excerpt,
            )

    # 6. 문장·수식 중간 절단 징후 검사
    lines = [line.strip() for line in content_text.splitlines() if line.strip()]

    for line_number, line in enumerate(lines, start=1):
        for code, message in check_sentence_line(line):
            add_issue(
                issues,
                severity="WARNING",
                code=code,
                message=f"{message} content_text 줄: {line_number}",
                file_path=file_path,
                concept_id=concept_id,
                chunk_index=chunk_index,
                chunk_type=chunk_type,
                excerpt=line,
            )

        if line.startswith("LaTeX:"):
            latex = line[len("LaTeX:") :].strip()
            if not latex:
                add_issue(
                    issues,
                    severity="ERROR",
                    code="EMPTY_LATEX",
                    message="LaTeX 표현이 비어 있음.",
                    file_path=file_path,
                    concept_id=concept_id,
                    chunk_index=chunk_index,
                    chunk_type=chunk_type,
                    excerpt=line,
                )
            else:
                for code, message in check_latex(latex):
                    add_issue(
                        issues,
                        severity="ERROR",
                        code=code,
                        message=f"{message} content_text 줄: {line_number}",
                        file_path=file_path,
                        concept_id=concept_id,
                        chunk_index=chunk_index,
                        chunk_type=chunk_type,
                        excerpt=line,
                    )

        if line.startswith("CAS 표현:"):
            cas = line[len("CAS 표현:") :].strip()
            if not cas:
                add_issue(
                    issues,
                    severity="ERROR",
                    code="EMPTY_CAS",
                    message="CAS 표현이 비어 있음.",
                    file_path=file_path,
                    concept_id=concept_id,
                    chunk_index=chunk_index,
                    chunk_type=chunk_type,
                    excerpt=line,
                )
            else:
                for code, message in check_cas(cas):
                    add_issue(
                        issues,
                        severity="ERROR",
                        code=code,
                        message=f"{message} content_text 줄: {line_number}",
                        file_path=file_path,
                        concept_id=concept_id,
                        chunk_index=chunk_index,
                        chunk_type=chunk_type,
                        excerpt=line,
                    )

    if lines and SUSPICIOUS_FINAL_PATTERN.search(lines[-1]):
        add_issue(
            issues,
            severity="WARNING",
            code="SUSPICIOUS_CONTENT_END",
            message="content_text가 구분자·연산자·역슬래시로 끝남.",
            file_path=file_path,
            concept_id=concept_id,
            chunk_index=chunk_index,
            chunk_type=chunk_type,
            excerpt=lines[-1],
        )

    # 7. token_count 및 최대 토큰 검사
    document_max_tokens = document.get("max_tokens", 420)
    max_tokens = configured_max_tokens or document_max_tokens
    stored_token_count = chunk.get("token_count")

    if not isinstance(stored_token_count, int) or stored_token_count < 1:
        add_issue(
            issues,
            severity="ERROR",
            code="INVALID_TOKEN_COUNT",
            message=f"token_count가 유효한 양의 정수가 아님: {stored_token_count!r}",
            file_path=file_path,
            concept_id=concept_id,
            chunk_index=chunk_index,
            chunk_type=chunk_type,
        )
    elif stored_token_count > max_tokens:
        add_issue(
            issues,
            severity="ERROR",
            code="TOKEN_LIMIT_EXCEEDED",
            message=f"저장된 token_count={stored_token_count}가 상한 {max_tokens}를 초과함.",
            file_path=file_path,
            concept_id=concept_id,
            chunk_index=chunk_index,
            chunk_type=chunk_type,
        )

    if not skip_token_recount:
        model_name = str(
            chunk.get("metadata", {}).get(
                "embedding_model",
                document.get("embedding_model", "intfloat/multilingual-e5-base"),
            )
        )
        try:
            actual_token_count = recount_tokens(model_name, content_text)
        except Exception as error:
            add_issue(
                issues,
                severity="WARNING",
                code="TOKEN_RECOUNT_FAILED",
                message=f"실제 토큰 재계산 실패: {error}",
                file_path=file_path,
                concept_id=concept_id,
                chunk_index=chunk_index,
                chunk_type=chunk_type,
            )
        else:
            if isinstance(stored_token_count, int) and actual_token_count != stored_token_count:
                add_issue(
                    issues,
                    severity="ERROR",
                    code="TOKEN_COUNT_MISMATCH",
                    message=(
                        f"저장 token_count={stored_token_count}, "
                        f"실제 tokenizer 계산={actual_token_count}."
                    ),
                    file_path=file_path,
                    concept_id=concept_id,
                    chunk_index=chunk_index,
                    chunk_type=chunk_type,
                )

            if actual_token_count > max_tokens:
                add_issue(
                    issues,
                    severity="ERROR",
                    code="ACTUAL_TOKEN_LIMIT_EXCEEDED",
                    message=f"실제 token_count={actual_token_count}가 상한 {max_tokens}를 초과함.",
                    file_path=file_path,
                    concept_id=concept_id,
                    chunk_index=chunk_index,
                    chunk_type=chunk_type,
                )

    # 추가 무결성 검사: content_hash
    stored_hash = chunk.get("content_hash")
    actual_hash = hashlib.sha256(content_text.encode("utf-8")).hexdigest()
    if stored_hash != actual_hash:
        add_issue(
            issues,
            severity="ERROR",
            code="CONTENT_HASH_MISMATCH",
            message="content_hash가 현재 content_text의 SHA-256과 일치하지 않음.",
            file_path=file_path,
            concept_id=concept_id,
            chunk_index=chunk_index,
            chunk_type=chunk_type,
        )


def validate_document(
    *,
    document: Any,
    file_path: Path,
    configured_max_tokens: int | None,
    skip_token_recount: bool,
) -> tuple[list[dict[str, Any]], int]:
    issues: list[dict[str, Any]] = []

    if not isinstance(document, dict):
        add_issue(
            issues,
            severity="ERROR",
            code="INVALID_ROOT_STRUCTURE",
            message="JSON 최상위 값이 객체가 아님.",
            file_path=file_path,
        )
        return issues, 0

    concept_id = str(document.get("concept_id", ""))
    subject_id = str(document.get("subject_id", ""))

    if not concept_id:
        add_issue(
            issues,
            severity="ERROR",
            code="MISSING_DOCUMENT_CONCEPT_ID",
            message="최상위 concept_id가 비어 있음.",
            file_path=file_path,
        )

    if not subject_id:
        add_issue(
            issues,
            severity="ERROR",
            code="MISSING_DOCUMENT_SUBJECT_ID",
            message="최상위 subject_id가 비어 있음.",
            file_path=file_path,
            concept_id=concept_id,
        )

    expected_prefix = safe_file_stem(concept_id)
    if concept_id and not file_path.stem.startswith(expected_prefix):
        add_issue(
            issues,
            severity="WARNING",
            code="FILENAME_CONCEPT_ID_MISMATCH",
            message=(
                f"파일명 {file_path.name!r}이 concept_id {concept_id!r}로 시작하지 않음."
            ),
            file_path=file_path,
            concept_id=concept_id,
        )

    if subject_id and file_path.parent.name != subject_id:
        add_issue(
            issues,
            severity="WARNING",
            code="SUBJECT_FOLDER_MISMATCH",
            message=(
                f"상위 폴더명 {file_path.parent.name!r}과 subject_id "
                f"{subject_id!r}가 다름."
            ),
            file_path=file_path,
            concept_id=concept_id,
        )

    chunks = document.get("chunks")
    if not isinstance(chunks, list):
        add_issue(
            issues,
            severity="ERROR",
            code="CHUNKS_NOT_LIST",
            message="chunks가 배열이 아님.",
            file_path=file_path,
            concept_id=concept_id,
        )
        return issues, 0

    seen_indexes: list[int] = []

    for list_index, chunk in enumerate(chunks):
        if not isinstance(chunk, dict):
            add_issue(
                issues,
                severity="ERROR",
                code="CHUNK_NOT_OBJECT",
                message=f"chunks[{list_index}]가 객체가 아님.",
                file_path=file_path,
                concept_id=concept_id,
                chunk_index=list_index,
                excerpt=repr(chunk),
            )
            continue

        chunk_index = chunk.get("chunk_index")
        if isinstance(chunk_index, int):
            seen_indexes.append(chunk_index)

        validate_chunk(
            chunk=chunk,
            list_index=list_index,
            document=document,
            file_path=file_path,
            configured_max_tokens=configured_max_tokens,
            skip_token_recount=skip_token_recount,
            issues=issues,
        )

    expected_indexes = list(range(len(chunks)))
    if sorted(seen_indexes) != expected_indexes:
        add_issue(
            issues,
            severity="ERROR",
            code="CHUNK_INDEX_SEQUENCE_INVALID",
            message=(
                f"chunk_index가 0부터 연속적이지 않음. "
                f"실제={sorted(seen_indexes)}, 기대={expected_indexes}"
            ),
            file_path=file_path,
            concept_id=concept_id,
        )

    return issues, len(chunks)


def inspect_json_file(
    file_path: Path,
    *,
    configured_max_tokens: int | None,
    skip_token_recount: bool,
) -> tuple[list[dict[str, Any]], int]:
    try:
        document = json.loads(file_path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as error:
        issues: list[dict[str, Any]] = []
        add_issue(
            issues,
            severity="ERROR",
            code="INVALID_ENCODING",
            message=f"UTF-8 디코딩 실패: {error}",
            file_path=file_path,
        )
        return issues, 0
    except json.JSONDecodeError as error:
        issues = []
        add_issue(
            issues,
            severity="ERROR",
            code="INVALID_JSON",
            message=(
                f"JSON 구문 오류: line={error.lineno}, "
                f"column={error.colno}, message={error.msg}"
            ),
            file_path=file_path,
        )
        return issues, 0

    return validate_document(
        document=document,
        file_path=file_path,
        configured_max_tokens=configured_max_tokens,
        skip_token_recount=skip_token_recount,
    )


def save_reports(
    *,
    json_files: list[Path],
    chunk_count: int,
    issues: list[dict[str, Any]],
) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    severity_counts = Counter(issue["severity"] for issue in issues)
    code_counts = Counter(issue["code"] for issue in issues)

    report = {
        "summary": {
            "file_count": len(json_files),
            "chunk_count": chunk_count,
            "error_count": severity_counts.get("ERROR", 0),
            "warning_count": severity_counts.get("WARNING", 0),
            "issue_count": len(issues),
            "issue_code_counts": dict(sorted(code_counts.items())),
        },
        "issues": issues,
    }

    JSON_REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        "Chunk JSON 종합 검사 보고서",
        "=" * 70,
        f"검사 파일 수: {len(json_files)}",
        f"검사 Chunk 수: {chunk_count}",
        f"ERROR: {severity_counts.get('ERROR', 0)}",
        f"WARNING: {severity_counts.get('WARNING', 0)}",
        "",
    ]

    for number, issue in enumerate(issues, start=1):
        lines.extend(
            [
                f"[{number}] {issue['severity']} / {issue['code']}",
                f"파일: {issue['file']}",
                f"concept_id: {issue['concept_id']}",
                f"chunk_index: {issue['chunk_index']}",
                f"chunk_type: {issue['chunk_type']}",
                f"내용: {issue['message']}",
                f"문제 구간: {issue['excerpt']}",
                "-" * 70,
            ]
        )

    if not issues:
        lines.append("발견된 문제가 없음.")

    TEXT_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_arguments()

    input_path = args.input
    if not input_path.is_absolute():
        input_path = (PROJECT_ROOT / input_path).resolve()

    try:
        json_files = find_json_files(input_path)
    except Exception as error:
        print(f"[실행 실패] {error}")
        raise SystemExit(1)

    if not json_files:
        print(f"JSON 파일을 찾지 못함: {input_path}")
        raise SystemExit(1)

    all_issues: list[dict[str, Any]] = []
    total_chunk_count = 0

    print(f"검사 대상 JSON 파일: {len(json_files)}개")

    for file_number, file_path in enumerate(json_files, start=1):
        file_issues, chunk_count = inspect_json_file(
            file_path,
            configured_max_tokens=args.max_tokens,
            skip_token_recount=args.skip_token_recount,
        )
        all_issues.extend(file_issues)
        total_chunk_count += chunk_count

        error_count = sum(1 for issue in file_issues if issue["severity"] == "ERROR")
        warning_count = sum(
            1 for issue in file_issues if issue["severity"] == "WARNING"
        )

        print(
            f"[{file_number}/{len(json_files)}] {relative_path(file_path)} "
            f"→ ERROR {error_count}, WARNING {warning_count}"
        )

    save_reports(
        json_files=json_files,
        chunk_count=total_chunk_count,
        issues=all_issues,
    )

    severity_counts = Counter(issue["severity"] for issue in all_issues)

    print()
    print("=" * 70)
    print(f"검사 파일: {len(json_files)}개")
    print(f"검사 Chunk: {total_chunk_count}개")
    print(f"ERROR: {severity_counts.get('ERROR', 0)}개")
    print(f"WARNING: {severity_counts.get('WARNING', 0)}개")
    print(f"JSON 보고서: {JSON_REPORT_PATH}")
    print(f"TXT 보고서: {TEXT_REPORT_PATH}")

    has_errors = severity_counts.get("ERROR", 0) > 0
    has_warnings = severity_counts.get("WARNING", 0) > 0

    if has_errors or (args.fail_on_warning and has_warnings):
        raise SystemExit(1)


if __name__ == "__main__":
    main()