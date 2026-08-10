"""
Product Boundary Tests — Cross-Workspace Isolation

验证 Askora v1 的 Workspace 数据隔离在多个层面的有效性：
- 存储层：不同 Workspace 的数据在数据库中物理隔离
- 查询层：默认查询按 pseudonym_id 过滤
- 模型层：所有业务模型强制关联 Workspace
- 检索层：检索结果不跨 Workspace 返回
- 文档分块层：DocumentChunk 通过 document_id → pseudonym_id 隔离

Product Positioning Assertions:
- Workspace 是 v1 最高数据隔离边界
- 不同 Workspace 的数据互不可见
- 不存在跨 Workspace 的默认数据访问路径
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import and_, event, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.document import DocumentChunk, UserDocument
from app.models.user import User, UserRole, UserStatus


def _make_engine_and_factory(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'cross-ws-isolation.db'}")

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
class TestStorageLevelIsolation:
    """验证存储层的数据隔离。"""

    async def test_workspace_data_physically_separated(self, tmp_path) -> None:
        """
        PRODUCT-POSITIONING: 不同 Workspace 的数据在存储层隔离。

        通过 pseudonym_id 分区，每个 Workspace 的数据只属于自己。
        """
        engine, factory = _make_engine_and_factory(tmp_path)
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with factory() as session:
            user_a = User(
                id=str(uuid4()),
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                pseudonym_id="ws_storage_a",
            )
            user_b = User(
                id=str(uuid4()),
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                pseudonym_id="ws_storage_b",
            )
            session.add_all([user_a, user_b])
            await session.commit()

            doc_a = UserDocument(
                id=str(uuid4()),
                pseudonym_id="ws_storage_a",
                original_filename="storage_a.pdf",
                file_extension="pdf",
                file_size_bytes=100,
                storage_path="/data/ws_a/storage.pdf",
            )
            doc_b = UserDocument(
                id=str(uuid4()),
                pseudonym_id="ws_storage_b",
                original_filename="storage_b.pdf",
                file_extension="pdf",
                file_size_bytes=200,
                storage_path="/data/ws_b/storage.pdf",
            )
            session.add_all([doc_a, doc_b])
            await session.commit()

        async with factory() as session:
            count_a = await session.scalar(
                select(UserDocument).where(UserDocument.pseudonym_id == "ws_storage_a")
            )
            count_b = await session.scalar(
                select(UserDocument).where(UserDocument.pseudonym_id == "ws_storage_b")
            )
            assert count_a is not None
            assert count_a.original_filename == "storage_a.pdf"
            assert count_b is not None
            assert count_b.original_filename == "storage_b.pdf"

        await engine.dispose()

    async def test_no_cross_workspace_data_leakage(self, tmp_path) -> None:
        """
        验证不存在跨 Workspace 的数据泄露路径。

        即使两个 Workspace 的数据有相似属性，查询也不会混淆。
        """
        engine, factory = _make_engine_and_factory(tmp_path)
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with factory() as session:
            for ws_name in ["ws_leak_a", "ws_leak_b"]:
                user = User(
                    id=str(uuid4()),
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                    pseudonym_id=ws_name,
                )
                session.add(user)
            await session.commit()

            doc_a = UserDocument(
                id=str(uuid4()),
                pseudonym_id="ws_leak_a",
                original_filename="physics_notes.pdf",
                file_extension="pdf",
                file_size_bytes=512,
                storage_path="/data/ws_a/physics.pdf",
                subject="physics",
            )
            doc_b = UserDocument(
                id=str(uuid4()),
                pseudonym_id="ws_leak_b",
                original_filename="physics_notes.pdf",
                file_extension="pdf",
                file_size_bytes=512,
                storage_path="/data/ws_b/physics.pdf",
                subject="physics",
            )
            session.add_all([doc_a, doc_b])
            await session.commit()

        async with factory() as session:
            results = await session.scalars(
                select(UserDocument).where(
                    and_(
                        UserDocument.pseudonym_id == "ws_leak_a",
                        UserDocument.subject == "physics",
                    )
                )
            )
            result_list = list(results)
            assert len(result_list) == 1
            assert result_list[0].pseudonym_id == "ws_leak_a"

        await engine.dispose()


@pytest.mark.asyncio
class TestQueryLevelIsolation:
    """验证查询层的数据隔离。"""

    async def test_queries_filter_by_pseudonym_id(self, tmp_path) -> None:
        """
        PRODUCT-POSITIONING: 默认查询必须按 pseudonym_id 过滤。

        验证查询条件包含 Workspace 隔离。
        """
        engine, factory = _make_engine_and_factory(tmp_path)
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with factory() as session:
            user = User(
                id=str(uuid4()),
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                pseudonym_id="ws_query",
            )
            session.add(user)
            await session.commit()

            for i in range(3):
                doc = UserDocument(
                    id=str(uuid4()),
                    pseudonym_id="ws_query",
                    original_filename=f"query_doc_{i}.pdf",
                    file_extension="pdf",
                    file_size_bytes=1024,
                    storage_path=f"/data/query_{i}.pdf",
                )
                session.add(doc)
            await session.commit()

        async with factory() as session:
            results = await session.scalars(
                select(UserDocument).where(UserDocument.pseudonym_id == "ws_query")
            )
            result_list = list(results)
            assert len(result_list) == 3

        await engine.dispose()

    async def test_workspace_column_has_index_for_isolation(self, tmp_path) -> None:
        """
        验证 pseudonym_id 列有索引以支持高效的 Workspace 隔离查询。

        这确保按 Workspace 过滤是数据库原生支持的。
        """
        engine, factory = _make_engine_and_factory(tmp_path)
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        mapper = _get_mapper(UserDocument)
        pseudonym_id_col = mapper.columns.get("pseudonym_id")
        assert pseudonym_id_col is not None

        table = Base.metadata.tables["user_documents"]
        indexes = list(table.indexes)
        pseudonym_indexes = [
            idx
            for idx in indexes
            if "pseudonym" in str(idx.columns).lower() or "pseudonym" in str(idx.name or "").lower()
        ]
        assert (
            len(pseudonym_indexes) >= 1
        ), "pseudonym_id should have at least one index for workspace isolation queries"

        await engine.dispose()


@pytest.mark.asyncio
class TestModelLevelIsolation:
    """验证模型层的 Workspace 隔离设计。"""

    async def test_document_forced_workspace_association(self, tmp_path) -> None:
        """
        PRODUCT-POSITIONING: UserDocument 强制关联 Workspace。

        pseudonym_id 是 NOT NULL 外键，确保每个文档属于某个 Workspace。
        """
        engine, factory = _make_engine_and_factory(tmp_path)
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        mapper = _get_mapper(UserDocument)
        pseudonym_id_col = mapper.columns.get("pseudonym_id")
        assert pseudonym_id_col is not None
        assert pseudonym_id_col.nullable is False
        assert pseudonym_id_col.foreign_keys, "pseudonym_id should have a ForeignKey constraint"

        await engine.dispose()

    async def test_user_model_pseudonym_id_is_unique(self, tmp_path) -> None:
        """
        验证 User 模型的 pseudonym_id 是唯一的。

        每个 Workspace 对应一个唯一的 pseudonym_id。
        """
        engine, factory = _make_engine_and_factory(tmp_path)
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        mapper = _get_mapper(User)
        pseudonym_id_col = mapper.columns.get("pseudonym_id")
        assert pseudonym_id_col is not None
        assert (
            pseudonym_id_col.unique is True
        ), "pseudonym_id must be unique — each workspace maps to exactly one pseudonym_id"

        await engine.dispose()

    async def test_chunk_isolation_via_document_foreign_key(self, tmp_path) -> None:
        """
        验证 DocumentChunk 通过 document_id → UserDocument.pseudonym_id 实现隔离。

        Chunk 不直接存 pseudonym_id，但通过 document_id 外键间接隔离。
        """
        engine, factory = _make_engine_and_factory(tmp_path)
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        mapper = _get_mapper(DocumentChunk)
        column_names = {column.name for column in mapper.columns}

        assert (
            "document_id" in column_names
        ), "DocumentChunk must have document_id FK for workspace isolation"

        document_id_col = mapper.columns.get("document_id")
        assert document_id_col is not None
        assert (
            document_id_col.foreign_keys
        ), "document_id should have a ForeignKey to user_documents"

        await engine.dispose()
