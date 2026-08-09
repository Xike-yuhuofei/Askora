"""P1-07 and onboarding integration must leave one deployable migration head."""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

BACKEND_ROOT = Path(__file__).resolve().parents[2]
INTEGRATED_HEAD = "p107f1061a02"
EXPECTED_PARENTS = {"m103f1061a01", "p103c5a0d003"}


def test_p1_07_and_onboarding_migrations_have_one_integrated_head() -> None:
    config = Config(BACKEND_ROOT / "alembic.ini")
    scripts = ScriptDirectory.from_config(config)

    assert scripts.get_heads() == [INTEGRATED_HEAD]
    revision = scripts.get_revision(INTEGRATED_HEAD)
    assert revision is not None
    assert set(revision._normalized_down_revisions) == EXPECTED_PARENTS
