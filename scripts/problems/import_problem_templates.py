import sys
from pathlib import Path


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.db.connection import get_connection

from app.problems.template_importer import (
    scan_template_files,
    group_templates,
    resolve_duplicates,
    validate_templates,
    build_db_record,
)

from app.problems.template_repository import (
    find_existing_template,
    insert_template,
    insert_template_concept,
    insert_import_audit,
)


TEMPLATE_ROOT = (
    PROJECT_ROOT
    / "data"
    / "problem_templates"
)

def import_to_database(
    validated_templates,
    audit_records,
    project_root,
):
    """
    검증된 ProblemTemplate들을 PostgreSQL에 저장한다.
    Template + Concept links는 하나의 transaction으로 처리한다.
    """

    inserted_count = 0
    skipped_count = 0
    audit_inserted_count = 0

    with get_connection() as conn:

        for audit_record in audit_records:
            insert_import_audit(
                conn,
                audit_record,
            )
            audit_inserted_count += 1

        for path, raw, template in validated_templates:

            record = build_db_record(
                path,
                raw,
                template,
                project_root,
            )

            existing = find_existing_template(
                conn,
                record["template_id"],
                record["template_version"],
            )

            # ------------------------------------------------
            # Case 1. DB에 아직 없음 → INSERT
            # ------------------------------------------------
            if existing is None:

                insert_template(
                    conn,
                    record,
                )

                for concept_id in (
                    template.taxonomy.concept_ids
                ):
                    insert_template_concept(
                        conn,
                        template.template_id,
                        template.template_version,
                        concept_id,
                    )

                inserted_count += 1

                insert_import_audit(
                    conn,
                    {
                        "template_id":
                            template.template_id,

                        "template_version":
                            template.template_version,

                        "selected_path":
                            record["source_path"],

                        "rejected_path":
                            None,

                        "action":
                            "inserted",

                        "reason":
                            "New template inserted",
                    },
                )

            # ------------------------------------------------
            # Case 2. 이미 있고 hash가 같음 → SKIP
            # ------------------------------------------------
            elif (
                existing["content_hash"]
                == record["content_hash"]
            ):

                skipped_count += 1

                insert_import_audit(
                    conn,
                    {
                        "template_id":
                            template.template_id,

                        "template_version":
                            template.template_version,

                        "selected_path":
                            record["source_path"],

                        "rejected_path":
                            None,

                        "action":
                            "skipped",

                        "reason":
                            "Same template already exists",
                    },
                )

            # ------------------------------------------------
            # Case 3. ID/version은 같은데 내용이 다름 → ERROR
            # ------------------------------------------------
            else:

                raise RuntimeError(
                    "Existing template has a different "
                    "content_hash:\n"
                    f"template_id="
                    f"{template.template_id}\n"
                    f"template_version="
                    f"{template.template_version}"
                )

    return {
        "inserted": inserted_count,
        "skipped": skipped_count,
        "audit_records": audit_inserted_count,
    }

def main():

    items = scan_template_files(
        TEMPLATE_ROOT
    )

    print(
        "Template files:",
        len(items),
    )

    groups = group_templates(
        items
    )

    duplicate_groups = {
        key: value
        for key, value in groups.items()
        if len(value) > 1
    }

    print(
        "Unique template keys:",
        len(groups),
    )

    print(
        "Duplicate groups:",
        len(duplicate_groups),
    )

    winners, audit = (
        resolve_duplicates(groups)
    )

    print(
        "Winners:",
        len(winners),
    )

    print(
        "Rejected duplicates:",
        len(audit),
    )

    validated = validate_templates(
        winners
    )

    print(
        "Pydantic valid:",
        len(validated),
    )

        # DB에 넣을 record 구조가 정상적으로
    # 만들어지는지 하나 확인한다.
    sample_path, sample_raw, sample_template = (
        validated[0]
    )

    sample_record = build_db_record(
        sample_path,
        sample_raw,
        sample_template,
        PROJECT_ROOT,
    )

    print(
        "Sample DB record:"
    )

    print(
        "  template_id:",
        sample_record["template_id"],
    )

    print(
        "  template_version:",
        sample_record["template_version"],
    )

    print(
        "  source_path:",
        sample_record["source_path"],
    )

    print(
        "  content_hash:",
        sample_record["content_hash"],
    )

    result = import_to_database(
    validated,
    audit,
    PROJECT_ROOT,
    )

    print(
        "Database import complete"
    )

    print(
        "  inserted:",
        result["inserted"],
    )

    print(
        "  skipped:",
        result["skipped"],
    )


if __name__ == "__main__":
    main()