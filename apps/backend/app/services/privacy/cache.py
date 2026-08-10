"""Ephemeral cache erasure derived from frozen manifest aliases and barriers."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from collections.abc import AsyncIterator, Iterable
from typing import Any

from app.core.config import settings
from app.core.redis_client import get_redis_client, is_redis_available
from app.infrastructure.privacy import FrozenSubjectManifest
from app.services.privacy.restore_barrier import RestoreBarrierStore

_TOKEN_SPLIT = re.compile(r"[:|/\s]+")


def cache_aliases(manifest: FrozenSubjectManifest) -> set[str]:
    aliases = {manifest.user_id, manifest.pseudonym_id}
    for entry in manifest.entries:
        aliases.update(
            str(value)
            for _, value in entry.primary_key
            if isinstance(value, str) and len(value) >= 8
        )
    return aliases


def cache_scope_digests(manifest: FrozenSubjectManifest) -> tuple[str, ...]:
    return tuple(sorted(_alias_digest(value) for value in cache_aliases(manifest)))


async def purge_manifest_cache_if_available(manifest: FrozenSubjectManifest) -> int:
    if is_redis_available() is not True:
        return 0
    client = get_redis_client()
    if client is None:
        return 0
    return await purge_matching_cache(client, aliases=cache_aliases(manifest))


async def reconcile_cache_barriers(store: RestoreBarrierStore) -> int:
    if is_redis_available() is not True:
        return 0
    client = get_redis_client()
    if client is None:
        return 0
    digests = {
        digest
        for entry in store.load().values()
        for digest in entry.get("cache_scope_digests", [])
        if isinstance(digest, str)
    }
    if not digests:
        return 0
    return await purge_matching_cache(client, alias_digests=digests)


async def purge_matching_cache(
    client: Any,
    *,
    aliases: set[str] | None = None,
    alias_digests: set[str] | None = None,
) -> int:
    aliases = aliases or set()
    alias_digests = alias_digests or set()
    deleted = 0
    async for raw_key in _scan_keys(client):
        key = _decode(raw_key)
        values = await _read_cache_values(client, key)
        candidates = _candidate_strings(key)
        for value in values:
            candidates.update(_candidate_strings(value))
        matches_plain = bool(candidates & aliases)
        matches_digest = any(_alias_digest(candidate) in alias_digests for candidate in candidates)
        if matches_plain or matches_digest:
            deleted += int(await client.delete(key) or 0)
    return deleted


async def _scan_keys(client: Any) -> AsyncIterator[Any]:
    async for key in client.scan_iter(match="*"):
        yield key


async def _read_cache_values(client: Any, key: str) -> list[Any]:
    kind = _decode(await client.type(key)).lower()
    if kind == "string":
        return [await client.get(key)]
    if kind == "hash":
        return [await client.hgetall(key)]
    if kind == "list":
        return list(await client.lrange(key, 0, -1))
    if kind == "set":
        return list(await client.smembers(key))
    if kind == "zset":
        return list(await client.zrange(key, 0, -1))
    return []


def _candidate_strings(value: Any) -> set[str]:
    candidates: set[str] = set()
    if value is None:
        return candidates
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="ignore")
    if isinstance(value, str):
        candidates.add(value)
        candidates.update(part for part in _TOKEN_SPLIT.split(value) if part)
        try:
            parsed = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return candidates
        candidates.update(_candidate_strings(parsed))
        return candidates
    if isinstance(value, dict):
        for key, item in value.items():
            candidates.update(_candidate_strings(key))
            candidates.update(_candidate_strings(item))
        return candidates
    if isinstance(value, Iterable):
        for item in value:
            candidates.update(_candidate_strings(item))
    return candidates


def _decode(value: Any) -> str:
    return value.decode("utf-8", errors="ignore") if isinstance(value, bytes) else str(value)


def _alias_digest(value: str) -> str:
    return hmac.new(
        settings.kek_master_key.encode("utf-8"),
        f"privacy-cache:{value}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
