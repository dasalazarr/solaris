"""Alias de compatibilidad (M2-T6): la suite `qa` vive ahora en `app/evals/qa_suite.py` y se lanza
con el runner (M2-T7, una sola vía):

    uv run --project app/backend python app/evals/runner.py --suite qa [--only QA-001] [--label x]
    uv run --project app/backend python app/evals/runner.py --suite qa --calibrate

`python -m solaris.evals_qa [args]` reenvía a `runner.py --suite qa [args]`. **Solo evals
(PAT-004):** ningún módulo del runtime lo importa (tests/test_ask.py).
"""

from __future__ import annotations

import sys

from solaris.settings import REPO_ROOT

EVALS_DIR = REPO_ROOT / "app" / "evals"


def main(argv: list[str] | None = None) -> int:
    if str(EVALS_DIR) not in sys.path:
        sys.path.insert(0, str(EVALS_DIR))
    import runner  # app/evals/runner.py

    return runner.main(["--suite", "qa", *(sys.argv[1:] if argv is None else argv)])


if __name__ == "__main__":
    sys.exit(main())
