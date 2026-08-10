"""P1 integrations must leave one deployable migration head."""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

BACKEND_ROOT = Path(__file__).resolve().parents[2]
INTEGRATED_HEAD = "x062d0e0a001"
EXPECTED_PARENTS = {"w171d0e0a001"}


def test_p1_migrations_have_one_integrated_head() -> None:
    config = Config(BACKEND_ROOT / "alembic.ini")
    scripts = ScriptDirectory.from_config(config)

    assert scripts.get_heads() == [INTEGRATED_HEAD]
    revision = scripts.get_revision(INTEGRATED_HEAD)
    assert revision is not None
    assert set(revision._normalized_down_revisions) == EXPECTED_PARENTS
