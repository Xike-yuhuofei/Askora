from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base
from app.core.exceptions import MaterialAlreadyAssignedError
from app.models.document import MaterialLifecycle, UserDocument
from app.models.local_owner import LocalOwnerRecord
from app.models.user import User
from app.models.workspace import Workspace
from app.services.documents.material_lifecycle import MaterialLifecycleService
from app.services.owner.canonical_identity import canonical_user_id


@pytest.mark.asyncio
async def test_assign_unassigned_material_is_idempotent(tmp_path) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'assign.db'}")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with factory() as session:
        user = User(id=str(uuid4()), pseudonym_id="assign-owner")
        owner_id = str(canonical_user_id(user.id))
        owner = LocalOwnerRecord(singleton_key=1, owner_id=owner_id, provenance="fresh")
        workspace = Workspace(
            workspace_id=str(uuid4()),
            owner_id=str(canonical_user_id(user.id)),
            display_name="微积分",
            lifecycle="active",
        )
        document = UserDocument(
            id=str(uuid4()),
            pseudonym_id=user.pseudonym_id,
            workspace_id=None,
            original_filename="notes.md",
            display_title="notes.md",
            file_extension="md",
            file_size_bytes=12,
            storage_path="notes.md",
            lifecycle=MaterialLifecycle.ACTIVE,
            lifecycle_version=1,
        )
        session.add_all([user, owner, workspace, document])
        await session.commit()

        service = MaterialLifecycleService(session)
        first = await service.assign_to_workspace(
            user=user,
            material_id=document.id,
            workspace_id=workspace.workspace_id,
            expected_version=1,
            idempotency_key="assign-1",
        )
        replay = await service.assign_to_workspace(
            user=user,
            material_id=document.id,
            workspace_id=workspace.workspace_id,
            expected_version=1,
            idempotency_key="assign-1",
        )
        assert first["outcome"] == "ASSIGNED"
        assert replay["outcome"] == "ASSIGNED"
        assert first["workspace_id"] == workspace.workspace_id
        stored = await session.get(UserDocument, document.id)
        assert stored is not None
        assert stored.workspace_id == workspace.workspace_id

        other = Workspace(
            workspace_id=str(uuid4()),
            owner_id=str(canonical_user_id(user.id)),
            display_name="另一空间",
            lifecycle="active",
        )
        session.add(other)
        await session.commit()
        with pytest.raises(MaterialAlreadyAssignedError):
            await service.assign_to_workspace(
                user=user,
                material_id=document.id,
                workspace_id=other.workspace_id,
                expected_version=stored.lifecycle_version,
                idempotency_key="assign-2",
            )

    await engine.dispose()
