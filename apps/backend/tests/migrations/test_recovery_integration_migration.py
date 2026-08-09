"""P1-07 dependency integration must leave one deployable migration head."""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

BACKEND_ROOT = Path(__file__).resolve().parents[2]
INTEGRATED_HEAD = "p103m4a8c002"


def test_p1_07_dependency_migrations_have_one_integrated_head() -> None:
    config = Config(BACKEND_ROOT / "alembic.ini")
    scripts = ScriptDirectory.from_config(config)

    assert scripts.get_heads() == [INTEGRATED_HEAD]
