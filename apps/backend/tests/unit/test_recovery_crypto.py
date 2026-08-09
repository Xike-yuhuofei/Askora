from __future__ import annotations

from pathlib import Path

import pytest

from app.data_control.crypto import (
    ContainerError,
    decrypt_file,
    encrypt_file,
    generate_recovery_key,
    parse_recovery_key,
)


def test_chunked_container_round_trip(tmp_path: Path) -> None:
    source = tmp_path / "source.bin"
    encrypted = tmp_path / "recovery.askora-recovery"
    restored = tmp_path / "restored.bin"
    source.write_bytes(b"a" * 70_000 + b"private-data" + b"b" * 80_000)
    key = parse_recovery_key(generate_recovery_key())

    encrypt_file(source, encrypted, key, chunk_size=64 * 1024)
    decrypt_file(encrypted, restored, key, max_plaintext_bytes=source.stat().st_size)

    assert restored.read_bytes() == source.read_bytes()
    assert encrypted.stat().st_mode & 0o777 == 0o600
    assert restored.stat().st_mode & 0o777 == 0o600


def test_wrong_recovery_key_is_rejected_before_plaintext_survives(tmp_path: Path) -> None:
    source = tmp_path / "source.bin"
    encrypted = tmp_path / "recovery.askora-recovery"
    restored = tmp_path / "restored.bin"
    source.write_bytes(b"private-data")
    encrypt_file(source, encrypted, parse_recovery_key(generate_recovery_key()))

    with pytest.raises(ContainerError, match="authentication"):
        decrypt_file(
            encrypted,
            restored,
            parse_recovery_key(generate_recovery_key()),
            max_plaintext_bytes=1024,
        )

    assert not restored.exists()


@pytest.mark.parametrize("mutation", ["tamper", "truncate", "append"])
def test_modified_container_is_rejected(tmp_path: Path, mutation: str) -> None:
    source = tmp_path / "source.bin"
    encrypted = tmp_path / "recovery.askora-recovery"
    restored = tmp_path / "restored.bin"
    source.write_bytes(b"private-data" * 10_000)
    key = parse_recovery_key(generate_recovery_key())
    encrypt_file(source, encrypted, key, chunk_size=64 * 1024)
    content = bytearray(encrypted.read_bytes())
    if mutation == "tamper":
        content[len(content) // 2] ^= 0x01
    elif mutation == "truncate":
        del content[-10:]
    else:
        content.extend(b"unexpected")
    encrypted.write_bytes(content)

    with pytest.raises(ContainerError):
        decrypt_file(encrypted, restored, key, max_plaintext_bytes=1024**2)

    assert not restored.exists()


def test_plaintext_limit_is_fail_closed(tmp_path: Path) -> None:
    source = tmp_path / "source.bin"
    encrypted = tmp_path / "recovery.askora-recovery"
    restored = tmp_path / "restored.bin"
    source.write_bytes(b"x" * 100_000)
    key = parse_recovery_key(generate_recovery_key())
    encrypt_file(source, encrypted, key, chunk_size=64 * 1024)

    with pytest.raises(ContainerError, match="plaintext limit"):
        decrypt_file(encrypted, restored, key, max_plaintext_bytes=99_999)

    assert not restored.exists()
