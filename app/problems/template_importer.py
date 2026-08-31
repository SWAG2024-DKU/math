from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any
import hashlib
import json

from app.schemas.problem_template import ProblemTemplate

STATUS_RANK = {
    "deprecated": 0,
    "draft": 1,
    "ready": 2,
}


RULE_STATUS_RANK = {
    "draft_auto": 0,
    "reviewed": 1,
    "curated": 2,
}

def scan_template_files(
    template_root: Path,
) -> list[tuple[Path, dict[str, Any]]]:
    """
    problem_templates 아래의 모든 JSON을 읽고
    실제 ProblemTemplate 객체만 반환한다.
    """

    results: list[
        tuple[Path, dict[str, Any]]
    ] = []

    for path in sorted(
        template_root.rglob("*.json")
    ):
        try:
            data = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid JSON: {path}"
            ) from exc

        # manifest 등은 여기서 제외
        if (
            data.get("object_type")
            != "problem_template"
        ):
            continue

        results.append(
            (path, data)
        )

    return results

def group_templates(
    items: list[tuple[Path, dict[str, Any]]],
) -> dict[
    tuple[str, str],
    list[tuple[Path, dict[str, Any]]]
]:

    groups = defaultdict(list)

    for path, data in items:

        key = (
            data["template_id"],
            data["template_version"],
        )

        groups[key].append(
            (path, data)
        )

    return dict(groups)

def template_rank(
    data: dict[str, Any],
) -> tuple[int, int, int]:

    status = data.get(
        "status"
    )

    executable = data.get(
        "executable",
        False,
    )

    rule_status = data.get(
        "generation_rule_status"
    )

    return (
        STATUS_RANK.get(
            status,
            -1,
        ),

        int(
            bool(executable)
        ),

        RULE_STATUS_RANK.get(
            rule_status,
            -1,
        ),
    )

def choose_winner(
    candidates: list[
        tuple[Path, dict[str, Any]]
    ],
):
    ranked = sorted(
        candidates,
        key=lambda item:
            template_rank(item[1]),
        reverse=True,
    )

    winner = ranked[0]

    if len(ranked) == 1:
        return winner, []

    winner_rank = template_rank(
        ranked[0][1]
    )

    second_rank = template_rank(
        ranked[1][1]
    )

    # 자동 판단 불가능한 충돌은
    # 절대로 임의 선택하지 않는다.
    if winner_rank == second_rank:
        raise RuntimeError(
            "Unable to resolve duplicate "
            "ProblemTemplate automatically:\n"
            f"  {ranked[0][0]}\n"
            f"  {ranked[1][0]}"
        )

    return winner, ranked[1:]

def resolve_duplicates(
    groups,
):
    winners = []
    audit_records = []

    for key, candidates in groups.items():

        winner, rejected = (
            choose_winner(candidates)
        )

        winners.append(
            winner
        )

        if rejected:

            for rejected_path, _ in rejected:

                audit_records.append(
                    {
                        "template_id": key[0],
                        "template_version": key[1],

                        "selected_path":
                            str(winner[0]),

                        "rejected_path":
                            str(rejected_path),

                        "action":
                            "duplicate_resolved",

                        "reason":
                            "Higher-priority "
                            "template selected",
                    }
                )

    return winners, audit_records

def validate_answer_type(
    template: ProblemTemplate,
) -> None:
    """
    classification.answer_type과
    answer_spec.answer_type이 일치하는지 확인한다.
    """

    classification_type = (
        template.classification.answer_type
    )

    spec_type = (
        template.answer_spec.answer_type
    )

    if classification_type != spec_type:
        raise ValueError(
            "answer_type mismatch: "
            f"{template.template_id}: "
            f"classification={classification_type}, "
            f"answer_spec={spec_type}"
        )

def validate_templates(
    winners,
):
    validated = []

    for path, raw in winners:
        try:
            template = (
                ProblemTemplate.model_validate(
                    raw
                )
            )

            validate_answer_type(
                template
            )

        except Exception as exc:
            raise ValueError(
                f"Template validation failed: {path}"
            ) from exc

        validated.append(
            (
                path,
                raw,
                template,
            )
        )

    return validated

def calculate_content_hash(
    data: dict[str, Any],
) -> str:
    """
    Template JSON의 논리적 내용에 대한 SHA-256 hash를 생성한다.

    JSON key 순서나 공백, 줄바꿈이 달라도
    실제 데이터가 같으면 동일한 hash가 생성된다.
    """

    canonical = json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()

def normalize_source_path(
    path: Path,
    project_root: Path,
) -> str:
    """
    레포 루트 기준의 상대 경로를 반환한다.
    Windows에서도 '/'로 통일한다.
    """

    return (
        path
        .relative_to(project_root)
        .as_posix()
    )

def build_db_record(
    path: Path,
    raw: dict[str, Any],
    template: ProblemTemplate,
    project_root: Path,
) -> dict[str, Any]:
    """
    검증된 ProblemTemplate을
    PostgreSQL problem.problem_templates
    INSERT에 사용할 record로 변환한다.
    """

    return {
        "template_id":
            template.template_id,

        "template_version":
            template.template_version,

        "schema_version":
            template.schema_version,

        "status":
            template.status,

        "executable":
            template.executable,

        "generation_rule_id":
            template.generation_rule_id,

        "generation_rule_version":
            template.generation_rule_version,

        "generation_rule_status":
            template.generation_rule_status,

        "subject_id":
            template.taxonomy.subject_id,

        "unit_id":
            template.taxonomy.unit_id,

        "problem_type":
            template.classification.problem_type,

        "answer_type":
            template.classification.answer_type,

        "difficulty_base":
            template.classification.difficulty.base,

        "difficulty_min":
            template.classification.difficulty.min,

        "difficulty_max":
            template.classification.difficulty.max,

        "generation_strategy":
            template.classification.generation_strategy,

        "language":
            template.classification.language,

        "source_path":
            normalize_source_path(
                path,
                project_root,
            ),

        "content_hash":
            calculate_content_hash(
                raw
            ),

        "payload":
            raw,
    }