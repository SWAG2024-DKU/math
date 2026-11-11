"""선형대수 Preview JSON의 수량과 식별자 중복을 PySpark로 집계한다.

예시:
    python scripts/analyze_problem_previews_spark.py ^
      --input-dir data/problem_previews/linear_algebra/all_20260930T130721Z_f5ed40c3

이 스크립트는 저장된 정답의 수학적 타당성을 판단하거나 DB에 쓰지 않는다.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import LongType, StringType, StructField, StructType


# Template snapshot과 expected_answer는 이 집계에 필요하지 않으므로 읽지 않는다.
# Python이 로컬 JSON을 읽고, Spark에는 이 작은 필드들만 전달한다.
PREVIEW_SCHEMA = StructType([
    StructField("subject_id", StringType(), True),
    StructField("template_id", StringType(), True),
    StructField("template_version", StringType(), True),
    StructField("problem_type", StringType(), True),
    StructField("seed", LongType(), True),
    StructField("statement", StringType(), True),
])


def summarize(input_dir: Path, expected_types: int, expected_per_type: int) -> dict:
    """유형별 개수, 필수값 누락, 동일 Template/seed 중복을 확인한다."""
    root = input_dir.resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Preview 폴더가 없습니다: {root}")

    # manifest.json과 review.md는 문제 파일이 아니므로 제외한다.
    sources = sorted(root.glob("*/start_*.json"))
    if not sources:
        raise ValueError(f"start_*.json 문제 파일을 찾지 못했습니다: {root}")

    # Windows에서 Spark/Hadoop의 file:// 직접 탐색은 NativeIO 네이티브
    # 라이브러리를 요구할 수 있다. 현재의 소량 Preview는 Python으로 읽는다.
    # 집계 자체는 아래 Spark DataFrame에서 실행한다.
    fields = PREVIEW_SCHEMA.fieldNames()
    rows = []
    for source in sources:
        with source.open(encoding="utf-8") as stream:
            value = json.load(stream)
        if not isinstance(value, dict):
            raise ValueError(f"JSON 최상위가 객체가 아닙니다: {source}")
        rows.append(tuple(value.get(name) for name in fields))

    spark = (SparkSession.builder
             .appName("linear-algebra-preview-audit")
             .master("local[2]")
             .getOrCreate())
    try:
        spark.sparkContext.setLogLevel("WARN")
        df = spark.createDataFrame(rows, schema=PREVIEW_SCHEMA)

        counts = df.groupBy("problem_type").count().collect()
        per_type = {row["problem_type"]: row["count"] for row in counts
                    if row["problem_type"] is not None}
        total = sum(row["count"] for row in counts)
        missing_required = df.filter(
            F.col("subject_id").isNull()
            | (F.col("subject_id") != "linear_algebra")
            | F.col("template_id").isNull()
            | F.col("template_version").isNull()
            | F.col("problem_type").isNull()
            | F.col("seed").isNull()
            | F.col("statement").isNull()
            | (F.length(F.trim(F.col("statement"))) == 0)
        ).count()
        duplicated_keys = (df.groupBy("template_id", "template_version", "seed")
                           .count().filter(F.col("count") > 1).count())

        wrong_counts = {kind: count for kind, count in per_type.items()
                        if count != expected_per_type}
        passed = (total == expected_types * expected_per_type
                  and len(per_type) == expected_types
                  and not wrong_counts
                  and missing_required == 0
                  and duplicated_keys == 0
                  and total == len(sources))
        return {
            "status": "passed" if passed else "failed",
            "input_dir": str(root),
            "expected_types": expected_types,
            "expected_per_type": expected_per_type,
            "source_file_count": len(sources),
            "total": total,
            "type_count": len(per_type),
            "missing_or_invalid_required_fields": missing_required,
            "duplicate_template_version_seed_keys": duplicated_keys,
            "wrong_type_counts": dict(sorted(wrong_counts.items())),
            "count_per_type": dict(sorted(per_type.items())),
        }
    finally:
        spark.stop()


def main() -> int:
    parser = argparse.ArgumentParser(description="선형대수 Preview 수량 집계 (DB 쓰기 없음)")
    parser.add_argument("--input-dir", required=True, type=Path,
                        help="all_... 실행 결과 폴더")
    parser.add_argument("--output", type=Path,
                        default=Path("data/reports/linear_algebra/preview_spark_summary.json"))
    parser.add_argument("--expected-types", type=int, default=62)
    parser.add_argument("--expected-per-type", type=int, default=20)
    args = parser.parse_args()
    if args.expected_types < 1 or args.expected_per_type < 1:
        parser.error("기대 유형 수와 유형별 개수는 양수여야 합니다.")

    report = summarize(args.input_dir, args.expected_types, args.expected_per_type)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items()
                      if key != "count_per_type"}, ensure_ascii=False, indent=2))
    print(f"보고서: {args.output.resolve()}")
    return 0 if report["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
