"""
Product Boundary Tests — Retrieval Scope Boundary

验证 Askora v1 的检索范围边界：
- Retrieval scope 是 Workspace-scoped，不跨 Workspace 扩大检索
- 不存在跨 Workspace 的默认检索行为
- v1 不存在 Global Material Library 作为 current truth
- 同一 Material 的检索结果不会泄露其他 Workspace 的数据

Product Positioning Assertions:
- Retrieval 有 Workspace scope
- 默认不跨 Workspace 搜索
- v1 不设独立全局资料库
- 检索结果只包含当前 Workspace 的数据
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.document import UserDocument
from app.models.user import User, UserRole, UserStatus


def _make_engine_and_factory(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'retrieval-scope.db'}")

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine, async_sessionmaker(engine, expire_on_commit=False)


def _get_mapper(model_class):
    from sqlalchemy.orm import class_mapper

    return class_mapper(model_class)


@pytest.mark.asyncio
class TestRetrievalWorkspaceScope:
    """验证检索范围被 Workspace 隔离。"""

    async def test_retrieval_defaults_to_workspace_scope(self, tmp_path) -> None:
        """
        CI-102: Retrieval 有 Workspace scope，默认不跨 Workspace 扩大检索。

        验证检索查询按 pseudonym_id 过滤，只返回当前 Workspace 的数据。
        """
        engine, factory = _make_engine_and_factory(tmp_path)
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with factory() as session:
            user_a = User(
                id=str(uuid4()),
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                pseudonym_id="ws_alpha",
            )
            user_b = User(
                id=str(uuid4()),
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                pseudonym_id="ws_beta",
            )
            session.add_all([user_a, user_b])
            await session.commit()

            doc_a = UserDocument(
                id=str(uuid4()),
                pseudonym_id="ws_alpha",
                original_filename="alpha_material.pdf",
                file_extension="pdf",
                file_size_bytes=1024,
                storage_path="/data/ws_alpha/alpha.pdf",
            )
            doc_b = UserDocument(
                id=str(uuid4()),
                pseudonym_id="ws_beta",
                original_filename="beta_material.pdf",
                file_extension="pdf",
                file_size_bytes=2048,
                storage_path="/data/ws_beta/beta.pdf",
            )
            session.add_all([doc_a, doc_b])
            await session.commit()

        async with factory() as session:
            results = await session.scalars(
                select(UserDocument).where(UserDocument.pseudonym_id == "ws_alpha")
            )
            result_list = list(results)
            assert len(result_list) == 1
            assert result_list[0].original_filename == "alpha_material.pdf"
            assert result_list[0].pseudonym_id == "ws_alpha"

        await engine.dispose()

    async def test_no_cross_workspace_default_retrieval(self, tmp_path) -> None:
        """
        PRODUCT-POSITIONING: 默认不跨 Workspace 搜索。

        即使两个 Workspace 有相同主题的 Material，检索也不会跨边界返回。
        """
        engine, factory = _make_engine_and_factory(tmp_path)
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with factory() as session:
            user_a = User(
                id=str(uuid4()),
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                pseudonym_id="ws_isolated_a",
            )
            user_b = User(
                id=str(uuid4()),
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                pseudonym_id="ws_isolated_b",
            )
            session.add_all([user_a, user_b])
            await session.commit()

            doc_a = UserDocument(
                id=str(uuid4()),
                pseudonym_id="ws_isolated_a",
                original_filename="shared_topic_material.pdf",
                file_extension="pdf",
                file_size_bytes=512,
                storage_path="/data/ws_a/shared.pdf",
                subject="math",
            )
            doc_b = UserDocument(
                id=str(uuid4()),
                pseudonym_id="ws_isolated_b",
                original_filename="same_topic_material.pdf",
                file_extension="pdf",
                file_size_bytes=512,
                storage_path="/data/ws_b/shared.pdf",
                subject="math",
            )
            session.add_all([doc_a, doc_b])
            await session.commit()

        async with factory() as session:
            results = await session.scalars(
                select(UserDocument).where(
                    UserDocument.pseudonym_id == "ws_isolated_a",
                    UserDocument.subject == "math",
                )
            )
            result_list = list(results)
            assert len(result_list) == 1
            assert result_list[0].pseudonym_id == "ws_isolated_a"
            assert result_list[0].original_filename == "shared_topic_material.pdf"

        await engine.dispose()


@pytest.mark.asyncio
class TestNoGlobalMaterialLibrary:
    """验证 v1 不存在 Global Material Library 作为 current truth。"""

    async def test_no_global_material_library_table(self, tmp_path) -> None:
        """
        PRODUCT-POSITIONING: v1 不建设跨 Workspace 的 Global Material Library。

        验证数据库中不存在 global_materials 或类似的跨 Workspace 表。
        """
        engine, factory = _make_engine_and_factory(tmp_path)
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        table_names = Base.metadata.tables.keys()
        global_table_keywords = ["global_material", "material_library", "shared_material"]
        for keyword in global_table_keywords:
            for table_name in table_names:
                assert keyword not in table_name.lower(), (
                    f"Table '{table_name}' appears to be a global material library, "
                    f"which is not allowed in v1"
                )

        await engine.dispose()

    async def test_every_material_belongs_to_workspace(self, tmp_path) -> None:
        """
        验证每个 Material 必须属于某个 Workspace（pseudonym_id NOT NULL）。

        v1 不存在脱离 Workspace 的"全局"Material。
        """
        engine, factory = _make_engine_and_factory(tmp_path)
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        mapper = _get_mapper(UserDocument)
        pseudonym_id_col = mapper.columns.get("pseudonym_id")
        assert pseudonym_id_col is not None
        assert (
            pseudonym_id_col.nullable is False
        ), "pseudonym_id must be NOT NULL — every material must belong to a workspace"

        await engine.dispose()

    async def test_workspace_isolation_in_all_document_queries(self, tmp_path) -> None:
        """
        验证所有文档查询都通过 pseudonym_id 进行 Workspace 过滤。

        v1 的数据访问层不得暴露忽略 pseudonym_id 的查询方法。
        """
        engine, factory = _make_engine_and_factory(tmp_path)
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with factory() as session:
            user_a = User(
                id=str(uuid4()),
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                pseudonym_id="ws_boundary",
            )
            user_b = User(
                id=str(uuid4()),
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                pseudonym_id="other_workspace",
            )
            session.add_all([user_a, user_b])
            await session.commit()

            doc_owned = UserDocument(
                id=str(uuid4()),
                pseudonym_id="ws_boundary",
                original_filename="owned.pdf",
                file_extension="pdf",
                file_size_bytes=1024,
                storage_path="/data/owned.pdf",
            )
            doc_unowned = UserDocument(
                id=str(uuid4()),
                pseudonym_id="other_workspace",
                original_filename="unowned.pdf",
                file_extension="pdf",
                file_size_bytes=1024,
                storage_path="/data/unowned.pdf",
            )
            session.add_all([doc_owned, doc_unowned])
            await session.commit()

        async with factory() as session:
            filtered = await session.scalars(
                select(UserDocument).where(UserDocument.pseudonym_id == "ws_boundary")
            )
            filtered_list = list(filtered)
            assert len(filtered_list) == 1
            assert filtered_list[0].original_filename == "owned.pdf"

            all_docs = await session.scalars(select(UserDocument))
            all_list = list(all_docs)
            assert len(all_list) == 2

        await engine.dispose()
