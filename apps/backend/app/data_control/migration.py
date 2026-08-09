"""Deterministic Alembic compatibility checks for staged SQLite restores."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine

from alembic import command
from app.core.config import settings
from app.core.database import Base


class SchemaCompatibilityError(RuntimeError):
    pass


class StagedSchemaMigrator:
    """Validate one linear revision and forward-migrate only inside staging."""

    def __init__(self, resource_root: Path | None = None) -> None:
        default_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
        self.resource_root = (resource_root or default_root).resolve()
        self.alembic_ini = self.resource_root / "alembic.ini"
        self.script_location = self.resource_root / "alembic"
        if not self.alembic_ini.is_file() or not self.script_location.is_dir():
            raise SchemaCompatibilityError("Alembic migration resources are unavailable")

    @property
    def current_head(self) -> str:
        script = ScriptDirectory.from_config(self._config())
        heads = script.get_heads()
        if len(heads) != 1:
            raise SchemaCompatibilityError("multiple migration heads are unsupported")
        return heads[0]

    def plan(self, database_path: Path) -> tuple[str | None, str, bool]:
        before = self.revision(database_path)
        head = self.current_head
        script = ScriptDirectory.from_config(self._config())
        known_path = {revision.revision for revision in script.iterate_revisions(head, "base")}
        if before is None:
            if not self._matches_current_metadata(database_path):
                raise SchemaCompatibilityError(
                    "unversioned database does not match current schema"
                )
            return before, head, True
        if before not in known_path:
            raise SchemaCompatibilityError("database revision is future, unknown, or divergent")
        return before, head, before != head

    def prepare(self, database_path: Path) -> tuple[str | None, str]:
        before, head, required = self.plan(database_path)
        if before is None:
            self._run_alembic(database_path, "stamp", head)
        elif required:
            self._run_alembic(database_path, "upgrade", head)

        after = self.revision(database_path)
        if after != head:
            raise SchemaCompatibilityError("staged migration did not reach the current head")
        return before, after

    def _config(self) -> Config:
        config = Config(str(self.alembic_ini))
        config.set_main_option("script_location", str(self.script_location))
        return config

    def _run_alembic(self, database_path: Path, operation: str, revision: str) -> None:
        database_url = f"sqlite+aiosqlite:///{database_path.as_posix()}"
        original_url = settings.database_url
        settings.database_url = database_url
        try:
            config = self._config()
            config.set_main_option("sqlalchemy.url", database_url)
            if operation == "stamp":
                command.stamp(config, revision)
            else:
                command.upgrade(config, revision)
        except Exception as exc:
            raise SchemaCompatibilityError("staged Alembic operation failed") from exc
        finally:
            settings.database_url = original_url

    @staticmethod
    def revision(database_path: Path) -> str | None:
        uri = f"file:{database_path.as_posix()}?mode=ro"
        with sqlite3.connect(uri, uri=True) as connection:
            exists = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='alembic_version'"
            ).fetchone()
            if exists is None:
                return None
            revisions = connection.execute("SELECT version_num FROM alembic_version").fetchall()
        if len(revisions) != 1:
            raise SchemaCompatibilityError("database has missing or multiple revisions")
        return str(revisions[0][0])

    @staticmethod
    def _matches_current_metadata(database_path: Path) -> bool:
        from app import models  # noqa: F401

        engine = create_engine(f"sqlite:///{database_path.as_posix()}")
        try:
            with engine.connect() as connection:
                context = MigrationContext.configure(connection)
                return compare_metadata(context, Base.metadata) == []
        finally:
            engine.dispose()
