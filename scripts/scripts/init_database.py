import sys
from pathlib import Path


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.db.connection import get_connection


SQL_DIR = PROJECT_ROOT / "sql"


SQL_FILES = [
    "001_create_kb_schema.sql",
    "002_create_concepts_table.sql",
    "003_enable_pgvector.sql",
    "004_create_concept_chunks_table.sql",
    "005_create_problem_schema.sql",
    "006_create_problem_templates.sql",
    "007_create_template_concepts.sql",
    "008_create_template_import_audit.sql",
]


def main():
    conn = get_connection()

    try:
        with conn:

            for filename in SQL_FILES:
                sql_path = SQL_DIR / filename

                print(
                    f"Applying: {filename}"
                )

                sql = (
                    sql_path
                    .read_text(
                        encoding="utf-8"
                    )
                )

                with conn.cursor() as cur:
                    cur.execute(sql)

                print(
                    f"  OK: {filename}"
                )

    finally:
        conn.close()

    print(
        "Database initialization complete."
    )


if __name__ == "__main__":
    main()
