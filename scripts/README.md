# Math platform scripts (reorganized)

This archive contains the `scripts/` subtree from the original `scripts.Zip`. Course scripts are grouped inside `scripts/problems/`; run commands from the math platform repository root.

```text
scripts/
├── problems/
│   ├── linear_algebra/
│   ├── calculus_1/
│   ├── calculus_2/
│   ├── engineering_math/
│   ├── probability_statistics/
│   └── common/
├── kb/
├── tests/
└── init_database.py
```

Course rule profiles and course-specific migration/review tools are under their matching `problems/` folder. Shared generation, validation, preview, and database helpers are under `problems/common/`. Knowledge-base utilities remain under `kb/`; tests remain under `tests/`.

Examples (from repository root):

```sh
python -m scripts.problems.linear_algebra.limit_eigenvector_spectrum
python -m scripts.problems.calculus_1.review_calculus_1_rules --help
python -m scripts.problems.common.save_problem_previews --help
```

The subject identifier `engineering_mathematics` remains unchanged in data and CLI contracts; its script folder is `engineering_math`. The original ZIP is unchanged. Cached bytecode and embedded `.git` metadata from the source ZIP are excluded from the reorganized ZIP.