"""선형대수 curated Rule의 Validator 이름만 안전하게 마이그레이션한다.

기존 ``linear_algebra.json``의 shape, symbol_spec, 구조화 Constraint,
primary_formula_id 등 다른 필드는 건드리지 않는다. 기본 실행은 미리보기이며,
실제 반영에는 ``--write``가 필요하다.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from app.problems.validator_policy import RULE_VALIDATORS


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG = PROJECT_ROOT / "data" / "generation_rules" / "linear_algebra.json"


def migrate_catalog(data: dict[str, Any]) -> tuple[dict[str, Any], list[tuple[str, list[str], list[str]]]]:
    """Validator 목록만 수정한 catalog와 변경 내역을 반환한다."""
    if data.get("subject_id") != "linear_algebra":
        raise ValueError("linear_algebra catalog만 처리할 수 있습니다.")
    rules = data.get("rules")
    if not isinstance(rules, list):
        raise ValueError("catalog.rules가 목록이 아닙니다.")

    updated = json.loads(json.dumps(data, ensure_ascii=False))
    changes: list[tuple[str, list[str], list[str]]] = []
    found: set[str] = set()

    for rule in updated["rules"]:
        if rule.get("status") not in {"curated", "reviewed"}:
            continue
        problem_type = rule.get("problem_type")
        if problem_type not in RULE_VALIDATORS:
            raise ValueError(f"검수 매핑이 없는 curated Rule: {problem_type}")
        found.add(problem_type)
        validation = rule.get("validation")
        if not isinstance(validation, dict):
            raise ValueError(f"validation 객체가 없는 Rule: {problem_type}")
        previous = list(validation.get("validators", []))
        replacement = list(RULE_VALIDATORS[problem_type])
        if previous != replacement:
            validation["validators"] = replacement
            changes.append((problem_type, previous, replacement))

    missing = sorted(set(RULE_VALIDATORS) - found)
    if missing:
        raise ValueError("catalog에 없는 검수 대상 Rule: " + ", ".join(missing))
    return updated, changes


def write_atomic(path: Path, data: dict[str, Any], *, backup: bool) -> Path | None:
    """같은 디렉터리의 임시 파일을 사용해 catalog를 원자적으로 교체한다."""
    backup_path: Path | None = None
    if backup:
        backup_path = path.with_suffix(path.suffix + ".before-validator-mapping.bak")
        if backup_path.exists():
            raise FileExistsError(
                f"백업 파일이 이미 있습니다. 확인 후 이동/삭제하세요: {backup_path}"
            )
        shutil.copy2(path, backup_path)

    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=path.name + ".",
        suffix=".tmp",
        delete=False,
    )
    temporary_path = Path(handle.name)
    try:
        with handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
    return backup_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--write", action="store_true", help="검수된 Validator 매핑을 실제 저장")
    parser.add_argument("--no-backup", action="store_true", help="저장 전 백업 생성을 생략")
    args = parser.parse_args()

    catalog_path = args.catalog.resolve()
    if not catalog_path.is_file():
        raise FileNotFoundError(f"GenerationRule catalog이 없습니다: {catalog_path}")
    with catalog_path.open("r", encoding="utf-8") as file:
        original = json.load(file)

    migrated, changes = migrate_catalog(original)
    print(f"검수 대상: {len(RULE_VALIDATORS)}")
    print(f"변경 대상: {len(changes)}")
    for problem_type, previous, replacement in changes:
        print(f"- {problem_type}: {previous} -> {replacement}")

    if not args.write:
        print("미리보기만 수행했습니다. 실제 반영: --write")
        return 0
    if not changes:
        print("이미 최신 Validator 매핑입니다.")
        return 0

    backup_path = write_atomic(catalog_path, migrated, backup=not args.no_backup)
    print(f"저장 완료: {catalog_path}")
    if backup_path is not None:
        print(f"백업: {backup_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
