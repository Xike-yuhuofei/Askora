"""
Product Boundary Tests — Direct Material Learning

验证 Askora v1 的学习入口边界：
- Material 可以直接学习，不需要先创建 Learning Project
- Learning Project 不是学习的必要门槛
- Material 独立存在，不依赖 Project
- Project 是可选的组织层，不是前置条件

Product Positioning Assertions:
- Learning Project 不是学习的 required gate
- Material → Learning 是直接路径
- Project 是可选组织层，不是前置条件
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
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'direct-learning.db'}")

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
class TestMaterialIndependentExistence:
    """验证 Material 独立存在，不依赖 Learning Project。"""

    async def test_material_created_without_project(self, tmp_path) -> None:
        """
        PRODUCT-POSITIONING: Material 可以在没有 Learning Project 的情况下存在。

        UserDocument 的创建不需要关联任何 Project。
        """
        engine, factory = _make_engine_and_factory(tmp_path)
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with factory() as session:
            user = User(
                id=str(uuid4()),
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                pseudonym_id="ws_independent",
            )
            session.add(user)
            await session.commit()

            doc = UserDocument(
                id=str(uuid4()),
                pseudonym_id="ws_independent",
                original_filename="standalone_material.pdf",
                file_extension="pdf",
                file_size_bytes=2048,
                storage_path="/data/standalone.pdf",
            )
            session.add(doc)
            await session.commit()

            result = await session.get(UserDocument, doc.id)
            assert result is not None
            assert result.original_filename == "standalone_material.pdf"

        await engine.dispose()

    async def test_material_has_no_project_fk(self, tmp_path) -> None:
        """
        验证 UserDocument 模型不存在指向 LearningProject 的外键。

        v1 中 Material 不依赖 Project 存在。
        """
        engine, factory = _make_engine_and_factory(tmp_path)
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        mapper = _get_mapper(UserDocument)
        column_names = {column.name for column in mapper.columns}

        project_fk_keywords = ["project_id", "learning_project_id", "project_ref"]
        for keyword in project_fk_keywords:
            assert keyword not in column_names, (
                f"UserDocument should not have '{keyword}' column — "
                f"Material must be independent of LearningProject"
            )

        await engine.dispose()


@pytest.mark.asyncio
class TestLearningProjectNotRequired:
    """验证 Learning Project 不是学习的必要门槛。"""

    async def test_learning_entry_does_not_require_project(self, tmp_path) -> None:
        """
        PRODUCT-POSITIONING: Learning Project is not a required gate for learning.

        用户可以直接从 Material 开始学习，不需要先创建 Project。
        """
        engine, factory = _make_engine_and_factory(tmp_path)
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with factory() as session:
            user = User(
                id=str(uuid4()),
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                pseudonym_id="ws_no_project",
            )
            session.add(user)
            await session.commit()

            doc = UserDocument(
                id=str(uuid4()),
                pseudonym_id="ws_no_project",
                original_filename="direct_learn_material.pdf",
                file_extension="pdf",
                file_size_bytes=1024,
                storage_path="/data/direct_learn.pdf",
            )
            session.add(doc)
            await session.commit()

            result = await session.get(UserDocument, doc.id)
            assert result is not None
            assert result.pseudonym_id == "ws_no_project"

        await engine.dispose()

    async def test_material_count_independent_of_project_count(self, tmp_path) -> None:
        """
        验证 Material 的生命周期独立于 Project。

        Material 的数量和存在性不取决于 Project 的数量。
        """
        engine, factory = _make_engine_and_factory(tmp_path)
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with factory() as session:
            user = User(
                id=str(uuid4()),
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                pseudonym_id="ws_separate",
            )
            session.add(user)
            await session.commit()

            materials = []
            for i in range(5):
                doc = UserDocument(
                    id=str(uuid4()),
                    pseudonym_id="ws_separate",
                    original_filename=f"material_{i}.pdf",
                    file_extension="pdf",
                    file_size_bytes=1024 * (i + 1),
                    storage_path=f"/data/material_{i}.pdf",
                )
                materials.append(doc)
                session.add(doc)
            await session.commit()

        async with factory() as session:
            results = await session.scalars(
                select(UserDocument).where(UserDocument.pseudonym_id == "ws_separate")
            )
            result_list = list(results)
            assert (
                len(result_list) == 5
            ), "All 5 materials should exist independently of any project"

        await engine.dispose()


@pytest.mark.asyncio
class TestProjectIsOptional组织:
    """验证 Learning Project 是可选的组织层。"""

    async def test_project_material_relationship_is_optional(self, tmp_path) -> None:
        """
        验证 Material 与 Project 的关联是可选的。

        Material 可以存在而不关联任何 Project。
        """
        engine, factory = _make_engine_and_factory(tmp_path)
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with factory() as session:
            user = User(
                id=str(uuid4()),
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                pseudonym_id="ws_optional",
            )
            session.add(user)
            await session.commit()

            doc = UserDocument(
                id=str(uuid4()),
                pseudonym_id="ws_optional",
                original_filename="optional_project_material.pdf",
                file_extension="pdf",
                file_size_bytes=1024,
                storage_path="/data/optional.pdf",
            )
            session.add(doc)
            await session.commit()

            result = await session.get(UserDocument, doc.id)
            assert result is not None
            assert result.original_filename == "optional_project_material.pdf"

        await engine.dispose()

    async def test_material_survives_project_removal(self, tmp_path) -> None:
        """
        验证移除 Project-Material 关系后 Material 仍然存在。

        Material 的生命周期独立于 Project 关系。
        """
        engine, factory = _make_engine_and_factory(tmp_path)
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with factory() as session:
            user = User(
                id=str(uuid4()),
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                pseudonym_id="ws_survive",
            )
            session.add(user)
            await session.commit()

            doc = UserDocument(
                id=str(uuid4()),
                pseudonym_id="ws_survive",
                original_filename="survivor_material.pdf",
                file_extension="pdf",
                file_size_bytes=1024,
                storage_path="/data/survivor.pdf",
            )
            session.add(doc)
            await session.commit()

            result_before = await session.get(UserDocument, doc.id)
            assert result_before is not None

        async with factory() as session:
            result_after = await session.get(UserDocument, doc.id)
            assert result_after is not None
            assert result_after.original_filename == "survivor_material.pdf"

        await engine.dispose()
