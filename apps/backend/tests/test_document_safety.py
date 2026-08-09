"""文档上传、路径隔离和可选解析依赖的回归测试。"""

from __future__ import annotations

import io
import os
import stat
import zipfile
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException, UploadFile

from app.api.v1.documents import DocumentResponse, _read_upload_limited
from app.services.documents.parsers import get_parser
from app.services.documents.security_scanner import (
    SCANNER_VERSION,
    ScanReasonCode,
    SecurityScanner,
)
from app.services.storage.local_storage import LocalFileStorage


def _epub_bytes(
    chapter: str = "<h1>示例章节</h1><p>正文。</p>",
    *,
    chapter_document: str | None = None,
    extras: dict[str, bytes] | None = None,
) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        mimetype = zipfile.ZipInfo("mimetype")
        mimetype.compress_type = zipfile.ZIP_STORED
        archive.writestr(mimetype, b"application/epub+zip")
        archive.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
  <rootfiles><rootfile full-path="OEBPS/content.opf"
    media-type="application/oebps-package+xml"/></rootfiles>
</container>""",
            compress_type=zipfile.ZIP_DEFLATED,
        )
        archive.writestr(
            "OEBPS/content.opf",
            """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid" version="2.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">test-book</dc:identifier>
    <dc:title>安全扫描测试</dc:title><dc:language>zh</dc:language>
  </metadata>
  <manifest><item id="chapter" href="chapter.xhtml"
    media-type="application/xhtml+xml"/></manifest>
  <spine><itemref idref="chapter"/></spine>
</package>""",
            compress_type=zipfile.ZIP_DEFLATED,
        )
        archive.writestr(
            "OEBPS/chapter.xhtml",
            chapter_document or f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><body>{chapter}</body></html>""",
            compress_type=zipfile.ZIP_DEFLATED,
        )
        for name, content in (extras or {}).items():
            archive.writestr(name, content, compress_type=zipfile.ZIP_DEFLATED)
    return stream.getvalue()


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


def test_epub_scanner_does_not_treat_book_text_or_compressed_bytes_as_sql_injection():
    scanner = SecurityScanner()
    epub = _epub_bytes("<h1>SQL 示例</h1><p>文本可以讨论 ' OR SELECT，但不会被执行。</p>")

    result = scanner.scan(epub, ".epub", "sql-textbook.epub")

    assert result.safe is True
    assert result.should_block is False
    assert result.reason_codes == []
    assert result.to_record() == {
        "scanner_version": SCANNER_VERSION,
        "verdict": "allow",
        "severity": "low",
        "reason_codes": [],
        "threats": [],
        "checks": {
            "extension": "pass",
            "file_size": "pass",
            "media_type": "pass",
            "epub_structure": "pass",
            "archive_limits": "pass",
            "archive_paths": "pass",
            "active_content": "pass",
            "external_resources": "pass",
        },
        "file_size_bytes": len(epub),
        "declared_ext": ".epub",
        "limits": {
            "max_file_size_bytes": scanner.MAX_FILE_SIZE,
            "archive_max_entries": scanner.MAX_ARCHIVE_ENTRIES,
            "archive_max_entry_size_bytes": scanner.MAX_ARCHIVE_ENTRY_SIZE,
            "archive_max_uncompressed_size_bytes": scanner.MAX_ARCHIVE_UNCOMPRESSED_SIZE,
            "archive_max_compression_ratio": scanner.MAX_ARCHIVE_COMPRESSION_RATIO,
        },
    }


def test_epub_scanner_blocks_unsafe_archive_paths():
    result = SecurityScanner().scan(
        _epub_bytes(extras={"../outside.txt": b"escape"}),
        ".epub",
        "unsafe.epub",
    )

    assert result.should_block is True
    assert ScanReasonCode.EPUB_ENTRY_PATH_UNSAFE in result.reason_codes
    assert result.to_record()["checks"]["archive_paths"] == "high"


def test_epub_scanner_blocks_abnormal_compression_ratio(monkeypatch):
    scanner = SecurityScanner()
    monkeypatch.setattr(scanner, "COMPRESSION_RATIO_MIN_SIZE", 1)
    monkeypatch.setattr(scanner, "MAX_ARCHIVE_COMPRESSION_RATIO", 10)

    result = scanner.scan(
        _epub_bytes(extras={"OEBPS/payload.bin": b"A" * 50_000}),
        ".epub",
        "compressed.epub",
    )

    assert result.should_block is True
    assert ScanReasonCode.EPUB_COMPRESSION_RATIO_EXCEEDED in result.reason_codes


def test_epub_scanner_applies_entry_limit_before_decompressing(monkeypatch):
    scanner = SecurityScanner()
    monkeypatch.setattr(scanner, "MAX_ARCHIVE_ENTRIES", 2)
    read_calls = 0
    original_read = zipfile.ZipFile.read

    def tracked_read(archive, *args, **kwargs):
        nonlocal read_calls
        read_calls += 1
        return original_read(archive, *args, **kwargs)

    monkeypatch.setattr(zipfile.ZipFile, "read", tracked_read)
    result = scanner.scan(_epub_bytes(), ".epub", "too-many-entries.epub")

    assert result.should_quarantine is True
    assert ScanReasonCode.EPUB_ENTRY_COUNT_EXCEEDED in result.reason_codes
    assert read_calls == 0


def test_epub_scanner_records_active_content_without_executing_it():
    epub = _epub_bytes("<script>alert('never execute')</script><p onclick=\"noop()\">正文</p>")
    result = SecurityScanner().scan(epub, ".epub", "active-content.epub")

    assert result.should_block is False
    assert result.requires_review is True
    assert ScanReasonCode.EPUB_ACTIVE_CONTENT in result.reason_codes
    assert result.to_record()["verdict"] == "review"
    parsed = get_parser("epub").parse(epub, ".epub")
    assert "never execute" not in parsed.full_text
    assert "正文" in parsed.full_text


def test_epub_scanner_allows_standard_xhtml_11_doctype_without_resolving_it():
    epub = _epub_bytes(chapter_document="""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
  "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml"><body><p>标准 EPUB 正文。</p></body></html>""")

    result = SecurityScanner().scan(epub, ".epub", "legacy-xhtml.epub")

    assert result.should_block is False
    assert ScanReasonCode.EPUB_EXTERNAL_ENTITY not in result.reason_codes
    assert "标准 EPUB 正文" in get_parser("epub").parse(epub, ".epub").full_text


@pytest.mark.parametrize(
    "doctype",
    [
        '<!DOCTYPE html SYSTEM "file:///etc/passwd">',
        (
            '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" '
            '"https://attacker.invalid/xhtml11.dtd">'
        ),
        (
            '<!DOCTYPE html PUBLIC "-//UNKNOWN//DTD XHTML 1.1//EN" '
            '"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">'
        ),
    ],
)
def test_epub_scanner_quarantines_unapproved_external_doctypes(doctype):
    epub = _epub_bytes(
        chapter_document=(
            f'<?xml version="1.0" encoding="UTF-8"?>\n{doctype}\n'
            '<html xmlns="http://www.w3.org/1999/xhtml"><body><p>正文。</p></body></html>'
        )
    )

    result = SecurityScanner().scan(epub, ".epub", "external-doctype.epub")

    assert result.should_quarantine is True
    assert ScanReasonCode.EPUB_EXTERNAL_ENTITY in result.reason_codes


@pytest.mark.parametrize(
    "entity",
    [
        '<!ENTITY local "expanded text">',
        '<!ENTITY xxe SYSTEM "file:///etc/passwd">',
    ],
)
def test_epub_scanner_quarantines_all_entity_declarations(entity):
    epub = _epub_bytes(
        chapter_document=(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f"<!DOCTYPE html [{entity}]>\n"
            '<html xmlns="http://www.w3.org/1999/xhtml"><body><p>&xxe;</p></body></html>'
        )
    )

    result = SecurityScanner().scan(epub, ".epub", "entity-declaration.epub")

    assert result.should_quarantine is True
    assert ScanReasonCode.EPUB_ENTITY_DECLARATION in result.reason_codes


def test_corrupted_epub_is_rejected_instead_of_security_quarantined():
    result = SecurityScanner().scan(b"PK\x03\x04not-a-valid-archive", ".epub", "broken.epub")

    assert result.should_block is True
    assert result.should_reject is True
    assert result.should_quarantine is False
    assert result.to_record()["verdict"] == "reject"
    assert ScanReasonCode.EPUB_ARCHIVE_INVALID in result.reason_codes


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
