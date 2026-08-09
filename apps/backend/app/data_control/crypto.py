"""Versioned chunked AEAD container for Askora recovery packages."""

from __future__ import annotations

import base64
import json
import os
import struct
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

MAGIC = b"ASKORA_RECOVERY_V1\n"
HEADER_LENGTH = struct.Struct(">I")
RECORD_LENGTH = struct.Struct(">I")
DEFAULT_CHUNK_SIZE = 1024 * 1024
MAX_HEADER_SIZE = 16 * 1024


class ContainerError(ValueError):
    """Recovery container failed authentication or structural validation."""


def generate_recovery_key() -> str:
    return base64.urlsafe_b64encode(os.urandom(32)).decode("ascii").rstrip("=")


def parse_recovery_key(value: str) -> bytes:
    try:
        padded = value.strip() + "=" * (-len(value.strip()) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise ContainerError("invalid recovery key") from exc
    if len(decoded) != 32:
        raise ContainerError("invalid recovery key")
    return decoded


def _derive_key(recovery_key: bytes, salt: bytes) -> bytes:
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        info=b"askora-recovery-container/1.0",
    ).derive(recovery_key)


def encrypt_file(
    source: Path,
    destination: Path,
    recovery_key: bytes,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> None:
    if chunk_size < 64 * 1024 or chunk_size > 8 * 1024 * 1024:
        raise ValueError("invalid recovery chunk size")
    salt = os.urandom(16)
    header = json.dumps(
        {
            "algorithm": "AES-256-GCM",
            "chunk_size": chunk_size,
            "kdf": "HKDF-SHA256",
            "salt": base64.urlsafe_b64encode(salt).decode("ascii"),
            "schema_version": "1.0",
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    aes = AESGCM(_derive_key(recovery_key, salt))
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with source.open("rb") as reader, destination.open("xb") as writer:
        writer.write(MAGIC)
        writer.write(HEADER_LENGTH.pack(len(header)))
        writer.write(header)
        index = 0
        while chunk := reader.read(chunk_size):
            nonce = os.urandom(12)
            aad = MAGIC + header + index.to_bytes(8, "big")
            ciphertext = aes.encrypt(nonce, chunk, aad)
            record = nonce + ciphertext
            writer.write(RECORD_LENGTH.pack(len(record)))
            writer.write(record)
            index += 1
        writer.write(RECORD_LENGTH.pack(0))
        writer.flush()
        os.fsync(writer.fileno())
    destination.chmod(0o600)


def decrypt_file(
    source: Path,
    destination: Path,
    recovery_key: bytes,
    *,
    max_plaintext_bytes: int,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        with source.open("rb") as reader:
            if reader.read(len(MAGIC)) != MAGIC:
                raise ContainerError("unsupported recovery container")
            raw_header_length = reader.read(HEADER_LENGTH.size)
            if len(raw_header_length) != HEADER_LENGTH.size:
                raise ContainerError("truncated recovery header")
            header_length = HEADER_LENGTH.unpack(raw_header_length)[0]
            if header_length < 2 or header_length > MAX_HEADER_SIZE:
                raise ContainerError("invalid recovery header")
            header = reader.read(header_length)
            if len(header) != header_length:
                raise ContainerError("truncated recovery header")
            try:
                parsed = json.loads(header)
                if parsed.get("schema_version") != "1.0":
                    raise ContainerError("unsupported recovery container")
                salt = base64.urlsafe_b64decode(parsed["salt"])
            except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
                raise ContainerError("invalid recovery header") from exc
            aes = AESGCM(_derive_key(recovery_key, salt))
            total = 0
            index = 0
            with destination.open("xb") as writer:
                while True:
                    raw_record_length = reader.read(RECORD_LENGTH.size)
                    if len(raw_record_length) != RECORD_LENGTH.size:
                        raise ContainerError("truncated recovery container")
                    record_length = RECORD_LENGTH.unpack(raw_record_length)[0]
                    if record_length == 0:
                        if reader.read(1):
                            raise ContainerError("trailing recovery data")
                        break
                    if record_length < 28 or record_length > 8 * 1024 * 1024 + 64:
                        raise ContainerError("invalid recovery record")
                    record = reader.read(record_length)
                    if len(record) != record_length:
                        raise ContainerError("truncated recovery container")
                    nonce, ciphertext = record[:12], record[12:]
                    aad = MAGIC + header + index.to_bytes(8, "big")
                    plaintext = aes.decrypt(nonce, ciphertext, aad)
                    total += len(plaintext)
                    if total > max_plaintext_bytes:
                        raise ContainerError("recovery package exceeds plaintext limit")
                    writer.write(plaintext)
                    index += 1
                writer.flush()
                os.fsync(writer.fileno())
        destination.chmod(0o600)
    except (InvalidTag, OSError) as exc:
        destination.unlink(missing_ok=True)
        if isinstance(exc, InvalidTag):
            raise ContainerError("recovery authentication failed") from exc
        raise
    except Exception:
        destination.unlink(missing_ok=True)
        raise
