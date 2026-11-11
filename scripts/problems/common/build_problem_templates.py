from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.problems.generation_rule_registry import get_rule
from app.problems.problem_type_extractor import extract_from_directory
from app.problems.template_builder import build_template
from scripts.problems.common.generation_rule_validator import (
    GenerationRuleValidationError,
    ensure_generation_rule_valid,
)


DEFAULT_CONCEPT_DIR = PROJECT_ROOT / "data" / "concepts"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "problem_templates"


def safe_filename(value: str) -> str:
    value = re.sub(r"[^0-9A-Za-z._-]+", "_", value)
    return value.strip("._")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Concept + Problem Type + Generation Rule로 ProblemTemplate JSON을 생성합니다."
    )
    parser.add_argument(
        "--concept-dir",
        type=Path,
        default=DEFAULT_CONCEPT_DIR,
        help="Concept JSON 루트 디렉터리",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="ProblemTemplate 저장 루트 디렉터리",
    )
    parser.add_argument(
        "--subject",
        type=str,
        default=None,
        help="특정 subject_id만 생성 (예: linear_algebra)",
    )
    parser.add_argument(
        "--ready-only",
        action="store_true",
        help="ready Template만 저장하고 draft_auto 기반 Template은 건너뜁니다.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="동일한 출력 파일이 있으면 덮어씁니다.",
    )
    return parser.parse_args()


def main() -> None:
    # TODO[LA-D026] main 구현
    # 1. 원본 reviewed 카탈로그를 덮지 않고 후보 규칙을 읽어 별도 디렉터리에 템플릿을 재생성하는 경로를 제공한다.
    # 2. app의 registry가 전역 경로에 캐시하는 점을 확인하고 후보 정책이 실제 적용됐는지 manifest에 기록한다.
    raise NotImplementedError("TODO[LA-D026]: main")


if __name__ == "__main__":
    main()
