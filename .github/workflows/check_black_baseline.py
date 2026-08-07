"""Enforce Black for new code while locking the pre-existing format baseline.

EXEC-007 cannot modify the legacy files below because they are outside its
Allowed Files. Their exact hashes make the exception non-expandable: changing
one requires formatting it and removing it from this baseline in an authorized
follow-up change.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

LEGACY_UNFORMATTED: dict[str, str] = {
    "app/domains/assessment/service.py": (
        "f8fbad33293fe93fcd4a04b2114e526aaa2fed165fa1e17896d5e25be2d36ef6"
    ),
    "app/domains/learning_planner/planner.py": (
        "b493d33ff3edd078bf1324658b6fe1cd9c8a3993fdcd741c9140014581e82520"
    ),
    "app/domains/review_scheduler/scheduler.py": (
        "8bbfb6f99b7aaf6f7f34ba422a703d10173661bfbb4a8ff69b927bd175cdf173"
    ),
    "app/domains/retrieval/evidence_service.py": (
        "86863eb34b89299b97ff321539af73868e282ec578622253c80c8804f6503a8d"
    ),
    "app/infrastructure/planning_records.py": (
        "f71e978e48418b033fc556c6623a750445513b2f054a80c98a46132db709490d"
    ),
    "app/models/planning.py": ("994cc0929b46520f548c2e8afb8fa692a1f1c74c85f5f0c189cdc4c1906eaaa3"),
    "app/services/dialog/dialog_service.py": (
        "8f68780d7816655154bfe31f41fe39acbbdca47e35d5ea6a7b5a58a773148200"
    ),
    "app/services/documents/document_service.py": (
        "d1acc613e9e9ac07e30fa0abc6d78fc47f57bfda10872fbeb29454b116873186"
    ),
    "tests/test_assessment_mastery_replay.py": (
        "1e2641e7631ba093d0b3be40d109174bfaf5792e3d59b8ecccf0faf3db0f9c23"
    ),
    "tests/test_dialog_canonical_entry.py": (
        "b53fcc34cb1b5ecd0b4e474a3cf0562b2e80dfdabe84958864235cfc9ebb2c5d"
    ),
    "tests/test_learning_planner.py": (
        "5c8485134a2edebe1e5e327a2fdaada889f4df68e31a6bce76f8338b0fde2671"
    ),
    "tests/test_content_retrieval_v02.py": (
        "99cdb5931c9080c5f1c02a4e98c30fb809b7d0063361ad6a2f13f88cd9c51e16"
    ),
}


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    backend_root = repo_root / "apps" / "backend"

    drifted = [
        relative
        for relative, expected in LEGACY_UNFORMATTED.items()
        if not (backend_root / relative).is_file() or _digest(backend_root / relative) != expected
    ]
    if drifted:
        print("Black baseline drifted; format these files and remove their baseline entries:")
        for relative in drifted:
            print(f"- {relative}")
        return 1

    candidates: set[Path] = {Path(__file__).resolve()}
    for directory in ("app", "tests", "scripts"):
        candidates.update((backend_root / directory).rglob("*.py"))
    candidates.update(
        {
            backend_root / "test_document_service.py",
            backend_root / "test_optimizations.py",
        }
    )
    checked = sorted(
        path
        for path in candidates
        if path.is_relative_to(backend_root)
        and path.is_file()
        and path.relative_to(backend_root).as_posix() not in LEGACY_UNFORMATTED
    )
    checked.append(Path(__file__).resolve())

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "black",
            "--check",
            "--config",
            str(backend_root / "pyproject.toml"),
            *(str(path) for path in checked),
        ],
        cwd=backend_root,
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
