from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.schemas.generation_rule import GenerationRule, GenerationRuleCatalog


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RULE_DIR = PROJECT_ROOT / "data" / "generation_rules"


@lru_cache(maxsize=None)
def load_rule_catalog(subject_id: str) -> GenerationRuleCatalog:
    path = RULE_DIR / f"{subject_id}.json"

    if not path.exists():
        raise KeyError(f"Generation Rule catalog이 없습니다: {subject_id}")

    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    catalog = GenerationRuleCatalog.model_validate(raw)

    if catalog.rule_count != len(catalog.rules):
        raise ValueError(
            f"rule_count 불일치: {subject_id} "
            f"({catalog.rule_count} != {len(catalog.rules)})"
        )

    return catalog


def get_rule(subject_id: str, problem_type: str) -> GenerationRule:
    catalog = load_rule_catalog(subject_id)

    for rule in catalog.rules:
        if rule.problem_type == problem_type:
            return rule

    raise KeyError(
        f"Generation Rule이 없습니다: {subject_id} / {problem_type}"
    )


def has_rule(subject_id: str, problem_type: str) -> bool:
    try:
        get_rule(subject_id, problem_type)
        return True
    except KeyError:
        return False


def list_rules(subject_id: str | None = None) -> list[GenerationRule]:
    if subject_id is not None:
        return list(load_rule_catalog(subject_id).rules)

    results: list[GenerationRule] = []

    for path in sorted(RULE_DIR.glob("*.json")):
        if path.name == "manifest.json":
            continue
        results.extend(load_rule_catalog(path.stem).rules)

    return results


def registered_problem_types(subject_id: str) -> list[str]:
    return sorted(
        rule.problem_type
        for rule in load_rule_catalog(subject_id).rules
    )
