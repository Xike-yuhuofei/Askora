"""Stable compatibility projection from legacy local user keys to canonical UUID identity."""

from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5


def canonical_user_id(user_id: str | UUID) -> UUID:
    """Return the UUID owner identity without mutating the legacy user primary key."""

    if isinstance(user_id, UUID):
        return user_id
    try:
        return UUID(user_id)
    except ValueError:
        return uuid5(NAMESPACE_URL, f"askora:legacy-user:{user_id}")
