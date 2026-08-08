"""UI02B1 legacy local identity compatibility tests."""

from uuid import NAMESPACE_URL, UUID, uuid5

from app.services.auth.canonical_identity import canonical_user_id


def test_ui02b1_legacy_user_identity_projection_is_stable_and_non_mutating() -> None:
    """UI02B1-AC-001: local legacy ids project deterministically into owner contracts."""

    assert canonical_user_id("test-user-001") == uuid5(
        NAMESPACE_URL, "askora:legacy-user:test-user-001"
    )
    canonical = UUID("11111111-1111-4111-8111-111111111111")
    assert canonical_user_id(str(canonical)) == canonical
    assert canonical_user_id(canonical) == canonical
