"""
Product Boundary Tests — Workspace Isolation

验证 Askora v1 的 Workspace 数据隔离边界：
- Workspace != Tenant / Organization
- 不同 Workspace 的学习状态互不影响
- 默认不跨 Workspace 搜索
- v1 不设独立全局资料库

Product Positioning Assertions:
- Workspace 是高层数据隔离边界
- 不同 Workspace 的资料关系互相隔离
- 默认不跨 Workspace 搜索
- v1 不设独立全局资料库
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.document import UserDocument
from app.models.user import User, UserRole, UserStatus


def _make_engine_and_factory(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'workspace-isolation.db'}")

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine, async_sessionmaker(engine, expire_on_commit=False)


def _get_mapper(model_class):
    """获取 SQLAlchemy mapper（兼容 2.x API）。"""
    from sqlalchemy.orm import class_mapper

    return class_mapper(model_class)


@pytest.mark.asyncio
class TestWorkspaceIsolation:
    """验证 Workspace 数据隔离边界。"""

    async def test_workspace_is_not_tenant_or_organization(self, tmp_path) -> None:
        """
        PRODUCT-POSITIONING: Workspace 不得被误建模为 Tenant 或 Organization。

        v1 没有 Tenant/RBAC/multi-user 概念。
        """
        engine, factory = _make_engine_and_factory(tmp_path)
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        # 验证 User 模型不包含 tenant_id 或 organization_id 字段
        mapper = _get_mapper(User)
        column_names = {column.name for column in mapper.columns}

        # v1 不应有多租户字段
        assert "tenant_id" not in column_names, "v1 不应包含 tenant_id 字段"
        assert "organization_id" not in column_names, "v1 不应包含 organization_id 字段"
        assert "role_id" not in column_names, "v1 不应包含 RBAC role_id 字段"

        await engine.dispose()

    async def test_workspace_data_isolation_between_owners(self, tmp_path) -> None:
        """
        CI-102: Retrieval 有 Workspace scope，默认不跨 Workspace 扩大检索。

        不同用户的数据在存储层隔离。
        """
        engine, factory = _make_engine_and_factory(tmp_path)
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        # 创建两个独立的 LocalOwner（在当前架构中通过 pseudonym_id 隔离）
        user_a_id = str(uuid4())
        user_b_id = str(uuid4())

        async with factory() as session:
            user_a = User(
                id=user_a_id,
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                pseudonym_id="workspace_a",
            )
            user_b = User(
                id=user_b_id,
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                pseudonym_id="workspace_b",
            )
            session.add_all([user_a, user_b])
            await session.commit()

        # 验证数据通过 pseudonym_id 隔离
        async with factory() as session:
            doc_a = UserDocument(
                id=str(uuid4()),
                pseudonym_id="workspace_a",
                original_filename="doc_a.pdf",
                file_extension="pdf",
                file_size_bytes=1024,
                storage_path="/data/workspace_a/doc_a.pdf",
            )
            doc_b = UserDocument(
                id=str(uuid4()),
                pseudonym_id="workspace_b",
                original_filename="doc_b.pdf",
                file_extension="pdf",
                file_size_bytes=2048,
                storage_path="/data/workspace_b/doc_b.pdf",
            )
            session.add_all([doc_a, doc_b])
            await session.commit()

        # 查询时按 workspace/pseudonym_id 隔离
        async with factory() as session:
            from sqlalchemy import select

            docs_a = await session.scalars(
                select(UserDocument).where(UserDocument.pseudonym_id == "workspace_a")
            )
            docs_b = await session.scalars(
                select(UserDocument).where(UserDocument.pseudonym_id == "workspace_b")
            )

            docs_a_list = list(docs_a)
            docs_b_list = list(docs_b)

            assert len(docs_a_list) == 1
            assert len(docs_b_list) == 1
            assert docs_a_list[0].original_filename == "doc_a.pdf"
            assert docs_b_list[0].original_filename == "doc_b.pdf"

        await engine.dispose()


@pytest.mark.asyncio
class TestNoGlobalMaterialLibrary:
    """验证 v1 不设独立全局资料库。"""

    async def test_no_cross_workspace_material_sharing(self, tmp_path) -> None:
        """
        PRODUCT-POSITIONING: v1 不建设跨 Workspace 的 Global Material Library。

        Material 属于特定 Workspace，不默认跨 Workspace 可见。
        """
        engine, factory = _make_engine_and_factory(tmp_path)
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with factory() as _:
            # 验证 UserDocument 模型强制要求 pseudonym_id（Workspace 隔离）
            mapper = _get_mapper(UserDocument)
            pseudonym_id_column = mapper.columns.get("pseudonym_id")

            # pseudonym_id 应为 NOT NULL（每个 Material 必须属于某个 Workspace）
            assert pseudonym_id_column is not None
            assert pseudonym_id_column.nullable is False

        await engine.dispose()
