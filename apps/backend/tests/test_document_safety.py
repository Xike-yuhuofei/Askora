"""文档上传、路径隔离和可选解析依赖的回归测试。"""

from __future__ import annotations

import io
import os
import stat
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException, UploadFile

from app.api.v1.documents import DocumentResponse, _read_upload_limited
from app.services.documents.parsers import get_parser
from app.services.documents.security_scanner import SecurityScanner
from app.services.storage.local_storage import LocalFileStorage


@pytest.mark.asyncio
async def test_upload_stops_after_configured_limit(monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.documents.settings.local_storage_max_file_size_mb",
        1,
    )
    upload = UploadFile(filename="large.txt", file=io.BytesIO(b"x" * (1024 * 1024 + 1)))

    with pytest.raises(HTTPException) as exc:
        await _read_upload_limited(upload)

    assert exc.value.status_code == 413


def test_storage_rejects_path_traversal(tmp_path):
    storage = LocalFileStorage(str(tmp_path / "documents"))

    with pytest.raises(ValueError, match="无效的存储路径"):
        storage.read_file("../outside.txt")


@pytest.mark.asyncio
async def test_local_document_storage_uses_private_permissions(tmp_path):
    storage = LocalFileStorage(str(tmp_path / "documents"))
    relative_path, _ = await storage.save_file(
        "private_user", "document-1", "notes.txt", b"private notes", "txt"
    )

    if os.name != "nt":
        assert stat.S_IMODE(storage.base_path.stat().st_mode) == 0o700
        assert stat.S_IMODE((storage.base_path / "private_user").stat().st_mode) == 0o700
        assert stat.S_IMODE((storage.base_path / relative_path).stat().st_mode) == 0o600


def test_security_scanner_blocks_high_risk_content_and_oversized_files(monkeypatch):
    scanner = SecurityScanner()
    executable = scanner.scan(b"eval('system(command)')", ".txt", "payload.txt")
    assert executable.safe is False
    assert executable.should_block is True
    assert executable.severity == "high"

    monkeypatch.setattr(scanner, "MAX_FILE_SIZE", 8)
    oversized = scanner.scan(b"plain text", ".txt", "large.txt")
    assert oversized.safe is False
    assert oversized.should_block is True
    assert oversized.severity == "high"


def test_declared_document_parsers_have_runtime_dependencies():
    assert get_parser("epub").__class__.__name__ == "EPubParser"
    assert get_parser("pdf").__class__.__name__ == "PdfParser"
    assert get_parser("docx").__class__.__name__ == "DocxParser"

    __import__("ebooklib")
    __import__("pdfplumber")
    __import__("docx")


def test_document_response_accepts_orm_datetimes():
    now = datetime.now(UTC)
    document = SimpleNamespace(
        id="document-1",
        original_filename="notes.md",
        file_extension="md",
        file_size_bytes=12,
        storage_path="user/document.md",
        processing_status="completed",
        moderation_status="approved",
        subject="math",
        knowledge_point_id=None,
        chunk_count=1,
        total_tokens=4,
        created_at=now,
        updated_at=now,
        last_accessed_at=now,
        access_count=1,
    )

    response = DocumentResponse.model_validate(document)
    assert response.created_at == now
    assert response.last_accessed_at == now
