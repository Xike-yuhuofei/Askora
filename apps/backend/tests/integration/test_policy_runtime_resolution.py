"""ADR-0003 active PolicyBundle to exact runtime resolution."""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import models  # noqa: F401
from app.contracts.adaptive import PolicyBundleActivationV03, VersionedRef
from app.core.database import Base
from app.infrastructure.adaptive_records import AdaptiveContractRepository
from app.services.policy_runtime import (
    ActivePolicyRuntimeResolver,
    PolicyRuntimeResolutionError,
    default_policy_activation,
    default_policy_bundle,
)


@pytest.fixture
async def policy_runtime_db(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'policy-runtime.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_active_policy_runtime_resolves_exact_default(policy_runtime_db) -> None:
    repository = AdaptiveContractRepository(policy_runtime_db)
    bundle = default_policy_bundle()
    await repository.publish_policy_bundle(bundle)
    await repository.activate_policy_bundle(default_policy_activation())

    runtime = await ActivePolicyRuntimeResolver(policy_runtime_db).resolve()
    assert runtime.bundle == bundle
    assert runtime.profile.content_digest == bundle.content_digest
    assert UUID(str(default_policy_activation().activation_id))


@pytest.mark.asyncio
async def test_active_policy_runtime_missing_activation_fails_closed(policy_runtime_db) -> None:
    with pytest.raises(
        PolicyRuntimeResolutionError, match="POLICY_RUNTIME_PROFILE_UNAVAILABLE"
    ):
        await ActivePolicyRuntimeResolver(policy_runtime_db).resolve()


@pytest.mark.asyncio
async def test_latest_incompatible_activation_fails_closed_without_fallback(
    policy_runtime_db,
) -> None:
    repository = AdaptiveContractRepository(policy_runtime_db)
    default_bundle = default_policy_bundle()
    await repository.publish_policy_bundle(default_bundle)
    await repository.activate_policy_bundle(default_policy_activation())
    incompatible = default_bundle.model_copy(
        update={
            "bundle_id": "askora-v03-incompatible-bundle",
            "policy_version": "policy-incompatible",
            "content_digest": "sha256:incompatible",
        }
    )
    await repository.publish_policy_bundle(incompatible)
    await repository.activate_policy_bundle(
        PolicyBundleActivationV03(
            activation_id=uuid4(),
            bundle_ref=VersionedRef(
                entity_type="PolicyBundle",
                entity_id=incompatible.bundle_id,
                version=incompatible.policy_version,
            ),
            activated_at=default_policy_activation().activated_at + timedelta(seconds=1),
            supersedes_activation_id=default_policy_activation().activation_id,
            reason_codes=("TEST_INCOMPATIBLE_LATEST",),
        )
    )

    with pytest.raises(
        PolicyRuntimeResolutionError, match="POLICY_RUNTIME_PROFILE_BUNDLE_MISMATCH"
    ):
        await ActivePolicyRuntimeResolver(policy_runtime_db).resolve()
