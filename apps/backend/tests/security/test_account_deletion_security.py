"""Security boundaries for account deletion API, controls and retained evidence."""

from __future__ import annotations

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import app
from app.services.auth.auth_service import AuthService
from app.services.auth.dependencies import get_current_user


@pytest.mark.asyncio
async def test_deletion_api_separates_ordinary_auth_from_control_and_never_caches(
    tmp_path: Path,
) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'api-security.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        user, _, _ = await AuthService(session).register_user(
            "13500135000", "Askora security password 2026", "安全用户"
        )

        async def override_db():
            yield session

        async def override_user():
            return user

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_user] = override_user
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            preview = await client.post("/api/v1/account/deletion/preview")
            assert preview.status_code == 200
            assert preview.headers["cache-control"] == "private, no-store"
            preview_payload = preview.json()

            wrong_phrase = await client.post(
                "/api/v1/account/deletion/request",
                json={
                    "schema_version": "1.0",
                    "current_password": "Askora security password 2026",
                    "confirmation_phrase": "删除我的账号",
                    "preview_id": preview_payload["preview_id"],
                    "preview_digest": preview_payload["preview_digest"],
                    "policy_version": preview_payload["policy_version"],
                    "idempotency_key": "security-delete-command-0001",
                },
            )
            assert wrong_phrase.status_code == 422
            assert wrong_phrase.json()["error"]["code"] == "ACCOUNT_DELETION_CONFIRMATION_INVALID"

            accepted = await client.post(
                "/api/v1/account/deletion/request",
                json={
                    "schema_version": "1.0",
                    "current_password": "Askora security password 2026",
                    "confirmation_phrase": "永久删除我的 Askora 账号",
                    "preview_id": preview_payload["preview_id"],
                    "preview_digest": preview_payload["preview_digest"],
                    "policy_version": preview_payload["policy_version"],
                    "idempotency_key": "security-delete-command-0002",
                },
            )
            assert accepted.status_code == 200, accepted.text
            assert accepted.headers["cache-control"] == "private, no-store"
            token = accepted.json()["deletion_control_token"]

            missing = await client.get("/api/v1/account/deletion/status")
            assert missing.status_code == 401
            invalid = await client.get(
                "/api/v1/account/deletion/status",
                headers={"X-Deletion-Control": "not-the-real-token"},
            )
            assert invalid.status_code == 401
            status = await client.get(
                "/api/v1/account/deletion/status",
                headers={"X-Deletion-Control": token},
            )
            assert status.status_code == 200
            assert status.headers["cache-control"] == "private, no-store"
            serialized = status.text
            assert "13500135000" not in serialized
            assert "安全用户" not in serialized
            assert "password" not in serialized.lower()
        app.dependency_overrides.clear()
    await engine.dispose()
