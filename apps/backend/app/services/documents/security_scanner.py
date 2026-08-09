"""
文件安全扫描服务
轻量级文件安全检查，无需 ClamAV 等外部依赖

功能：
- 文件魔数校验：检查文件真实类型与声明类型是否匹配
- 危险扩展名检查：阻止可执行文件、脚本等危险文件
- 内容特征扫描：检测可执行代码片段、混淆特征
- 压缩炸弹检测：识别压缩率异常高的文件

检测级别：
- LOW: 安全，无威胁
- MEDIUM: 可疑，需人工审核
- HIGH: 危险，直接拒绝
"""

from __future__ import annotations

import io
import re
import stat
import zipfile
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.domains.content_knowledge import SAFETY_SCANNER_VERSION

logger = get_logger(__name__)

SCANNER_VERSION = SAFETY_SCANNER_VERSION

_ENTITY_DECLARATION_PATTERN = re.compile(r"<!\s*ENTITY\b", re.IGNORECASE)
_EXTERNAL_DOCTYPE_PATTERN = re.compile(
    r"<!\s*DOCTYPE\b[^>]*\b(?:SYSTEM|PUBLIC)\b",
    re.IGNORECASE | re.DOTALL,
)
_PUBLIC_DOCTYPE_PATTERN = re.compile(
    r"""
    <!\s*DOCTYPE\s+
    (?P<root>[A-Za-z_][\w:.-]*)\s+
    PUBLIC\s+
    (?P<public_quote>["'])(?P<public_id>.*?)(?P=public_quote)\s+
    (?P<system_quote>["'])(?P<system_id>.*?)(?P=system_quote)\s*>
    """,
    re.IGNORECASE | re.DOTALL | re.VERBOSE,
)

# These identifiers are legacy EPUB format declarations, not permission to
# fetch a remote DTD. Downstream XML parsing remains configured with entity
# resolution and network access disabled.
_ALLOWED_PUBLIC_DOCTYPES = {
    (
        "html",
        "-//W3C//DTD XHTML 1.0 Strict//EN",
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd",
    ),
    (
        "html",
        "-//W3C//DTD XHTML 1.0 Transitional//EN",
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd",
    ),
    (
        "html",
        "-//W3C//DTD XHTML 1.0 Frameset//EN",
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-frameset.dtd",
    ),
    (
        "html",
        "-//W3C//DTD XHTML 1.1//EN",
        "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd",
    ),
    (
        "ncx",
        "-//NISO//DTD ncx 2005-1//EN",
        "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd",
    ),
}


def _contains_unsafe_external_declaration(text: str) -> bool:
    """Allow exact legacy EPUB DTD identifiers while rejecting all variants."""
    external_markers = list(_EXTERNAL_DOCTYPE_PATTERN.finditer(text))
    if not external_markers:
        return False

    public_doctypes = list(_PUBLIC_DOCTYPE_PATTERN.finditer(text))
    if len(external_markers) != 1 or len(public_doctypes) != 1:
        return True

    declaration = public_doctypes[0]
    if declaration.start() != external_markers[0].start():
        return True

    identity = (
        declaration.group("root").casefold(),
        " ".join(declaration.group("public_id").split()),
        declaration.group("system_id").strip(),
    )
    return identity not in _ALLOWED_PUBLIC_DOCTYPES


class ScanReasonCode:
    """Stable internal reason codes persisted with a document processing run."""

    DANGEROUS_EXTENSION = "CONTENT_DANGEROUS_EXTENSION"
    UNSUPPORTED_EXTENSION = "CONTENT_UNSUPPORTED_EXTENSION"
    FILE_TOO_LARGE = "CONTENT_FILE_SIZE_EXCEEDED"
    TYPE_MISMATCH = "CONTENT_TYPE_MISMATCH"
    DANGEROUS_TEXT_PATTERN = "CONTENT_DANGEROUS_TEXT_PATTERN"
    EPUB_ARCHIVE_INVALID = "EPUB_ARCHIVE_INVALID"
    EPUB_MIMETYPE_INVALID = "EPUB_MIMETYPE_INVALID"
    EPUB_CONTAINER_INVALID = "EPUB_CONTAINER_INVALID"
    EPUB_ENTRY_PATH_UNSAFE = "EPUB_ENTRY_PATH_UNSAFE"
    EPUB_ENTRY_SYMLINK = "EPUB_ENTRY_SYMLINK"
    EPUB_ENTRY_ENCRYPTED = "EPUB_ENTRY_ENCRYPTED"
    EPUB_ENTRY_COUNT_EXCEEDED = "EPUB_ENTRY_COUNT_EXCEEDED"
    EPUB_ENTRY_SIZE_EXCEEDED = "EPUB_ENTRY_SIZE_EXCEEDED"
    EPUB_TOTAL_SIZE_EXCEEDED = "EPUB_TOTAL_UNCOMPRESSED_SIZE_EXCEEDED"
    EPUB_COMPRESSION_RATIO_EXCEEDED = "EPUB_COMPRESSION_RATIO_EXCEEDED"
    EPUB_NESTED_ARCHIVE = "EPUB_NESTED_ARCHIVE_BLOCKED"
    EPUB_EXTERNAL_ENTITY = "EPUB_EXTERNAL_ENTITY_BLOCKED"
    EPUB_ENTITY_DECLARATION = "EPUB_ENTITY_DECLARATION_BLOCKED"
    EPUB_ACTIVE_CONTENT = "EPUB_ACTIVE_CONTENT_STRIPPED"
    EPUB_EXTERNAL_RESOURCE = "EPUB_EXTERNAL_RESOURCE_IGNORED"


@dataclass
class ScanResult:
    """安全扫描结果"""

    safe: bool
    threats: list[str]
    severity: str  # "low", "medium", "high"
    details: dict[str, Any]
    reason_codes: list[str]

    @property
    def should_block(self) -> bool:
        """是否应该阻止上传"""
        return self.severity == "high"

    @property
    def should_reject(self) -> bool:
        """Whether the file is invalid/unsupported rather than a security risk."""
        return self.should_block and not self.should_quarantine

    @property
    def should_quarantine(self) -> bool:
        """Whether a structurally valid upload triggered a security boundary."""
        quarantine_reasons = {
            ScanReasonCode.DANGEROUS_EXTENSION,
            ScanReasonCode.DANGEROUS_TEXT_PATTERN,
            ScanReasonCode.EPUB_ENTRY_PATH_UNSAFE,
            ScanReasonCode.EPUB_ENTRY_SYMLINK,
            ScanReasonCode.EPUB_ENTRY_ENCRYPTED,
            ScanReasonCode.EPUB_ENTRY_COUNT_EXCEEDED,
            ScanReasonCode.EPUB_ENTRY_SIZE_EXCEEDED,
            ScanReasonCode.EPUB_TOTAL_SIZE_EXCEEDED,
            ScanReasonCode.EPUB_COMPRESSION_RATIO_EXCEEDED,
            ScanReasonCode.EPUB_NESTED_ARCHIVE,
            ScanReasonCode.EPUB_EXTERNAL_ENTITY,
            ScanReasonCode.EPUB_ENTITY_DECLARATION,
        }
        return self.should_block and bool(quarantine_reasons.intersection(self.reason_codes))

    @property
    def requires_review(self) -> bool:
        """是否需要人工审核"""
        return self.severity == "medium"

    def to_record(self) -> dict[str, Any]:
        """Return a versioned, JSON-safe audit record."""
        return {
            "scanner_version": SCANNER_VERSION,
            "verdict": self.verdict,
            "severity": self.severity,
            "reason_codes": list(self.reason_codes),
            "threats": list(self.threats),
            "checks": dict(self.details.get("checks", {})),
            "file_size_bytes": self.details.get("file_size"),
            "declared_ext": self.details.get("declared_ext"),
            "limits": dict(self.details.get("limits", {})),
        }

    @property
    def verdict(self) -> str:
        if self.should_reject:
            return "reject"
        if self.should_quarantine:
            return "quarantine"
        if self.requires_review:
            return "review"
        return "allow"


class SecurityScanner:
    """
    文件安全扫描器

    检查项：
    1. 危险扩展名
    2. 文件魔数（Magic Number）
    3. 内容特征（代码注入、混淆）
    4. 文件大小异常
    """

    # 绝对禁止的扩展名
    BLOCKED_EXTENSIONS = {
        ".exe",
        ".bat",
        ".cmd",
        ".com",
        ".scr",
        ".vbs",
        ".js",
        ".wsf",
        ".cpl",
        ".jar",
        ".ps1",
        ".psm1",
        ".vbe",
        ".jse",
        ".hta",
        ".msc",
        ".msi",
        ".msp",
        ".paf",
        ".pif",
        ".reg",
        ".rgs",
        ".sct",
        ".shb",
        ".shs",
        ".vb",
        ".wsc",
        ".ws",
        ".msix",
        ".msixbundle",
        ".appx",
        ".appxbundle",
    }

    # 可接受的文档扩展名（白名单）
    ALLOWED_EXTENSIONS = {
        ".md",
        ".markdown",
        ".txt",
        ".epub",
        ".pdf",
        ".docx",
        ".doc",
        ".tex",
        ".rst",
        ".html",
        ".htm",
        ".csv",
        ".json",
        ".xml",
        ".yaml",
        ".yml",
        ".pptx",
        ".ppt",
        ".xlsx",
        ".xls",
    }

    # 危险内容特征模式
    DANGEROUS_PATTERNS = [
        # 脚本注入
        (r"<script[^>]*>", "script_tag", "medium"),
        (r"javascript:", "javascript_uri", "medium"),
        (r"on\w+\s*=", "event_handler", "low"),
        # SQL 注入
        (r"('|%27)\s*(OR|AND|UNION|SELECT|DROP|INSERT)", "sql_injection", "high"),
        # 命令执行
        (r"(eval|exec|system|passthru|shell_exec)\s*\(", "command_execution", "high"),
        (r"powershell|cmd\.exe|command\.com", "windows_command", "high"),
        # 路径遍历
        (r"(\.\.[/\\]){2,}", "path_traversal", "medium"),
        # XSS
        (r"<iframe[^>]*>", "iframe_tag", "medium"),
        (r"<object[^>]*>", "object_tag", "medium"),
        # 混淆代码
        (r"base64_decode\s*\(", "obfuscation", "high"),
        (r"gzinflate\s*\(", "obfuscation", "high"),
        (r"str_rot13\s*\(", "obfuscation", "medium"),
    ]

    # 文件魔数映射
    MAGIC_NUMBERS = {
        b"\xff\xd8\xff": ".jpg",
        b"\x89PNG": ".png",
        b"GIF87": ".gif",
        b"GIF89": ".gif",
        b"PK\x03\x04": ".zip",
        b"\x1f\x8b": ".gz",
        b"Rar!": ".rar",
        b"%PDF": ".pdf",
        b"<?xml": ".xml",
        b"<!DOC": ".html",
        b"<html": ".html",
        b"{\\rtf": ".rtf",
        b"-----BEGIN": ".pem",
        b"#!": ".script",
        b"MZ": ".exe",
    }

    # 最大文件大小（50MB）
    MAX_FILE_SIZE = 50 * 1024 * 1024

    # 最小文件大小（100字节）
    MIN_FILE_SIZE = 100

    MAX_ARCHIVE_ENTRIES = settings.local_storage_archive_max_entries
    MAX_ARCHIVE_ENTRY_SIZE = settings.local_storage_archive_max_entry_size_mb * 1024 * 1024
    MAX_ARCHIVE_UNCOMPRESSED_SIZE = (
        settings.local_storage_archive_max_uncompressed_size_mb * 1024 * 1024
    )
    MAX_ARCHIVE_COMPRESSION_RATIO = settings.local_storage_archive_max_compression_ratio
    COMPRESSION_RATIO_MIN_SIZE = 1024 * 1024

    EPUB_TEXT_EXTENSIONS = {
        ".xhtml",
        ".html",
        ".htm",
        ".xml",
        ".opf",
        ".ncx",
        ".svg",
        ".css",
    }
    NESTED_ARCHIVE_EXTENSIONS = {".zip", ".rar", ".7z", ".tar", ".gz"}

    def scan(
        self,
        file_content: bytes,
        declared_ext: str,
        original_filename: str = "",
    ) -> ScanResult:
        """
        执行安全扫描

        Args:
            file_content: 文件内容
            declared_ext: 声明的扩展名
            original_filename: 原始文件名

        Returns:
            ScanResult 扫描结果
        """
        threats: list[str] = []
        reason_codes: list[str] = []
        severity = "low"
        details: dict[str, Any] = {
            "scanner_version": SCANNER_VERSION,
            "file_size": len(file_content),
            "declared_ext": declared_ext,
            "original_filename": original_filename,
            "checks": {},
            "limits": {
                "max_file_size_bytes": self.MAX_FILE_SIZE,
                "archive_max_entries": self.MAX_ARCHIVE_ENTRIES,
                "archive_max_entry_size_bytes": self.MAX_ARCHIVE_ENTRY_SIZE,
                "archive_max_uncompressed_size_bytes": self.MAX_ARCHIVE_UNCOMPRESSED_SIZE,
                "archive_max_compression_ratio": self.MAX_ARCHIVE_COMPRESSION_RATIO,
            },
        }

        ext = declared_ext.lower()
        if not ext.startswith("."):
            ext = f".{ext}"
        details["declared_ext"] = ext

        # 检查 1: 扩展名检查
        ext_result = self._check_extension(ext)
        if ext_result:
            threats.append(ext_result)
            reason_codes.append(
                ScanReasonCode.DANGEROUS_EXTENSION
                if ext in self.BLOCKED_EXTENSIONS
                else ScanReasonCode.UNSUPPORTED_EXTENSION
            )
            severity = self._update_severity(severity, "high")
            details["checks"]["extension"] = "blocked"
        else:
            details["checks"]["extension"] = "pass"

        # 检查 2: 文件大小检查
        size_result = self._check_file_size(len(file_content))
        if size_result:
            size_message, size_severity = size_result
            threats.append(size_message)
            if size_severity == "high":
                reason_codes.append(ScanReasonCode.FILE_TOO_LARGE)
            severity = self._update_severity(severity, size_severity)
            details["checks"]["file_size"] = size_severity
        else:
            details["checks"]["file_size"] = "pass"

        # 检查 3: 文件魔数检查
        magic_result = self._check_magic_number(file_content, ext)
        if magic_result:
            threats.append(magic_result)
            reason_codes.append(ScanReasonCode.TYPE_MISMATCH)
            severity = self._update_severity(severity, "high")
            details["checks"]["media_type"] = "blocked"
        else:
            details["checks"]["media_type"] = "pass"

        # 检查 4: 文件类型感知扫描。压缩容器不得按 UTF-8 原始文本扫描。
        if ext == ".epub" and severity != "high":
            epub_threats, epub_reasons, epub_severity, epub_checks = self._scan_epub(file_content)
            threats.extend(epub_threats)
            reason_codes.extend(epub_reasons)
            severity = self._update_severity(severity, epub_severity)
            details["checks"].update(epub_checks)
        elif self._is_direct_text_file(ext):
            text_threats, text_severity = self._check_content_patterns(file_content, ext)
            threats.extend(text_threats)
            if text_threats:
                reason_codes.append(ScanReasonCode.DANGEROUS_TEXT_PATTERN)
            severity = self._update_severity(severity, text_severity)
            details["checks"]["text_patterns"] = text_severity if text_threats else "pass"

        # 构建结果
        safe = severity != "high"

        return ScanResult(
            safe=safe,
            threats=threats,
            severity=severity,
            details=details,
            reason_codes=list(dict.fromkeys(reason_codes)),
        )

    def _scan_epub(self, content: bytes) -> tuple[list[str], list[str], str, dict[str, str]]:
        """Validate an EPUB container without executing or extracting it to disk."""
        threats: list[str] = []
        reason_codes: list[str] = []
        severity = "low"
        checks = {
            "epub_structure": "pass",
            "archive_limits": "pass",
            "archive_paths": "pass",
            "active_content": "pass",
            "external_resources": "pass",
        }

        def report(code: str, message: str, level: str, check: str) -> None:
            nonlocal severity
            severity = self._update_severity(severity, level)
            checks[check] = level
            if code not in reason_codes:
                threats.append(message)
                reason_codes.append(code)

        try:
            archive = zipfile.ZipFile(io.BytesIO(content))
        except (zipfile.BadZipFile, OSError):
            report(
                ScanReasonCode.EPUB_ARCHIVE_INVALID,
                "EPUB 压缩结构无效",
                "high",
                "epub_structure",
            )
            return threats, reason_codes, severity, checks

        with archive:
            infos = archive.infolist()
            if len(infos) > self.MAX_ARCHIVE_ENTRIES:
                report(
                    ScanReasonCode.EPUB_ENTRY_COUNT_EXCEEDED,
                    f"EPUB 文件条目过多: {len(infos)}",
                    "high",
                    "archive_limits",
                )
                return threats, reason_codes, severity, checks

            names = {info.filename for info in infos}
            if not infos or infos[0].filename != "mimetype":
                report(
                    ScanReasonCode.EPUB_MIMETYPE_INVALID,
                    "EPUB mimetype 不是首个归档条目",
                    "high",
                    "epub_structure",
                )
            elif infos[0].compress_type != zipfile.ZIP_STORED:
                report(
                    ScanReasonCode.EPUB_MIMETYPE_INVALID,
                    "EPUB mimetype 压缩方式无效",
                    "high",
                    "epub_structure",
                )

            if "META-INF/container.xml" not in names:
                report(
                    ScanReasonCode.EPUB_CONTAINER_INVALID,
                    "EPUB 缺少 META-INF/container.xml",
                    "high",
                    "epub_structure",
                )

            # Validate central-directory metadata before decompressing any entry.
            total_uncompressed = 0
            for info in infos:
                normalized = info.filename.replace("\\", "/")
                path = PurePosixPath(normalized)
                if (
                    not normalized
                    or normalized.startswith("/")
                    or "\x00" in normalized
                    or ".." in path.parts
                    or (path.parts and ":" in path.parts[0])
                ):
                    report(
                        ScanReasonCode.EPUB_ENTRY_PATH_UNSAFE,
                        "EPUB 包含不安全的归档路径",
                        "high",
                        "archive_paths",
                    )
                mode = (info.external_attr >> 16) & 0o170000
                if mode == stat.S_IFLNK:
                    report(
                        ScanReasonCode.EPUB_ENTRY_SYMLINK,
                        "EPUB 包含符号链接条目",
                        "high",
                        "archive_paths",
                    )
                if info.flag_bits & 0x1:
                    report(
                        ScanReasonCode.EPUB_ENTRY_ENCRYPTED,
                        "EPUB 包含无法安全检查的加密条目",
                        "high",
                        "archive_limits",
                    )
                if path.suffix.lower() in self.NESTED_ARCHIVE_EXTENSIONS:
                    report(
                        ScanReasonCode.EPUB_NESTED_ARCHIVE,
                        "EPUB 包含嵌套压缩归档",
                        "high",
                        "archive_limits",
                    )
                if info.file_size > self.MAX_ARCHIVE_ENTRY_SIZE:
                    report(
                        ScanReasonCode.EPUB_ENTRY_SIZE_EXCEEDED,
                        f"EPUB 单个条目解压后过大: {info.file_size} bytes",
                        "high",
                        "archive_limits",
                    )
                total_uncompressed += info.file_size
                if total_uncompressed > self.MAX_ARCHIVE_UNCOMPRESSED_SIZE:
                    report(
                        ScanReasonCode.EPUB_TOTAL_SIZE_EXCEEDED,
                        f"EPUB 累计解压大小过大: {total_uncompressed} bytes",
                        "high",
                        "archive_limits",
                    )
                if info.file_size >= self.COMPRESSION_RATIO_MIN_SIZE:
                    ratio = info.file_size / max(info.compress_size, 1)
                    if ratio > self.MAX_ARCHIVE_COMPRESSION_RATIO:
                        report(
                            ScanReasonCode.EPUB_COMPRESSION_RATIO_EXCEEDED,
                            f"EPUB 条目压缩比异常: {ratio:.1f}",
                            "high",
                            "archive_limits",
                        )

            if severity == "high":
                return threats, list(dict.fromkeys(reason_codes)), severity, checks

            try:
                mimetype = archive.read(infos[0])
            except (RuntimeError, OSError, NotImplementedError, zipfile.BadZipFile):
                mimetype = b""
            if mimetype != b"application/epub+zip":
                report(
                    ScanReasonCode.EPUB_MIMETYPE_INVALID,
                    "EPUB mimetype 内容无效",
                    "high",
                    "epub_structure",
                )
            elif not self._valid_epub_container(archive, names):
                report(
                    ScanReasonCode.EPUB_CONTAINER_INVALID,
                    "EPUB container.xml 或内容清单无效",
                    "high",
                    "epub_structure",
                )

            if severity == "high":
                return threats, list(dict.fromkeys(reason_codes)), severity, checks

            self._scan_epub_markup(archive, infos, report)

        return threats, list(dict.fromkeys(reason_codes)), severity, checks

    @staticmethod
    def _valid_epub_container(archive: zipfile.ZipFile, names: set[str]) -> bool:
        try:
            raw = archive.read("META-INF/container.xml")
            raw_paths = re.findall(
                rb"<(?:[A-Za-z_][\w.-]*:)?rootfile\b[^>]*\bfull-path\s*=\s*['\"]([^'\"]+)['\"]",
                raw,
                re.IGNORECASE,
            )
            rootfiles = [path.decode("utf-8") for path in raw_paths]
        except (
            KeyError,
            RuntimeError,
            OSError,
            UnicodeDecodeError,
            NotImplementedError,
            zipfile.BadZipFile,
        ):
            return False
        return bool(rootfiles) and all(path in names for path in rootfiles)

    def _scan_epub_markup(self, archive, infos, report) -> None:
        for info in infos:
            suffix = PurePosixPath(info.filename).suffix.lower()
            if suffix not in self.EPUB_TEXT_EXTENSIONS or info.is_dir():
                continue
            try:
                raw = archive.read(info)
            except (RuntimeError, OSError, NotImplementedError, zipfile.BadZipFile):
                report(
                    ScanReasonCode.EPUB_ARCHIVE_INVALID,
                    "EPUB 文本条目无法读取",
                    "high",
                    "epub_structure",
                )
                return
            text = raw.decode("utf-8", errors="ignore")
            if _ENTITY_DECLARATION_PATTERN.search(text):
                report(
                    ScanReasonCode.EPUB_ENTITY_DECLARATION,
                    "EPUB 包含不安全的实体声明",
                    "high",
                    "external_resources",
                )
            if _contains_unsafe_external_declaration(text):
                report(
                    ScanReasonCode.EPUB_EXTERNAL_ENTITY,
                    "EPUB 包含外部实体声明",
                    "high",
                    "external_resources",
                )
            if re.search(r"<script\b|javascript:|\son\w+\s*=", text, re.IGNORECASE):
                report(
                    ScanReasonCode.EPUB_ACTIVE_CONTENT,
                    "EPUB 包含会被剥离的主动内容",
                    "medium",
                    "active_content",
                )
            if re.search(
                r"(?:src\s*=|url\s*\()[\s'\"]*https?://",
                text,
                re.IGNORECASE,
            ):
                report(
                    ScanReasonCode.EPUB_EXTERNAL_RESOURCE,
                    "EPUB 包含不会被加载的远程资源",
                    "medium",
                    "external_resources",
                )

    def _check_extension(self, ext: str) -> Optional[str]:
        """检查扩展名安全性"""
        # 检查是否在黑名单中
        if ext in self.BLOCKED_EXTENSIONS:
            return f"危险扩展名: {ext}（可执行/脚本文件被禁止）"

        # 检查是否在白名单中
        if ext not in self.ALLOWED_EXTENSIONS:
            return f"未知扩展名: {ext}（不在允许列表中）"

        return None

    def _check_file_size(self, size: int) -> Optional[tuple[str, str]]:
        """检查文件大小"""
        if size > self.MAX_FILE_SIZE:
            return f"文件过大: {size} bytes (最大 {self.MAX_FILE_SIZE})", "high"

        if size < self.MIN_FILE_SIZE:
            return f"文件过小: {size} bytes (可能为空文件)", "low"

        return None

    def _check_magic_number(self, content: bytes, declared_ext: str) -> Optional[str]:
        """检查文件魔数"""
        if len(content) < 4:
            return None

        # 检查魔数匹配
        for magic, expected_ext in self.MAGIC_NUMBERS.items():
            if content.startswith(magic):
                # 魔数与声明的扩展名不匹配
                if expected_ext != declared_ext:
                    # 一些特殊情况允许不匹配
                    if not self._is_mismatch_allowed(expected_ext, declared_ext):
                        return f"文件类型不匹配: 检测为 {expected_ext}，声明为 {declared_ext}"
                break

        return None

    def _check_content_patterns(
        self,
        content: bytes,
        ext: str,
    ) -> tuple[list[str], str]:
        """检查内容危险模式"""
        threats: list[str] = []
        severity = "low"

        try:
            text = content.decode("utf-8", errors="ignore")
        except Exception:
            return threats, severity

        for pattern, name, risk_level in self.DANGEROUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                # 某些模式在特定文件类型中是正常的
                if self._is_pattern_allowed(name, ext):
                    continue

                threats.append(f"检测到危险特征 [{name}]: {pattern}")
                severity = self._update_severity(severity, risk_level)

        return threats, severity

    def _is_direct_text_file(self, ext: str) -> bool:
        """Return true only when the uploaded bytes are themselves text."""
        text_extensions = {
            ".md",
            ".markdown",
            ".txt",
            ".tex",
            ".rst",
            ".html",
            ".htm",
            ".csv",
            ".json",
            ".xml",
            ".yaml",
            ".yml",
        }
        return ext in text_extensions

    def _is_mismatch_allowed(self, detected_ext: str, declared_ext: str) -> bool:
        """某些扩展名与魔数不匹配是允许的"""
        allowed_mismatches = [
            (".zip", ".docx"),  # DOCX 本质是 ZIP
            (".zip", ".pptx"),  # PPTX 本质是 ZIP
            (".zip", ".xlsx"),  # XLSX 本质是 ZIP
            (".zip", ".epub"),  # EPUB 本质是 ZIP
            (".xml", ".docx"),  # DOCX 包含 XML
            (".xml", ".pptx"),
            (".xml", ".xlsx"),
        ]

        return (detected_ext, declared_ext) in allowed_mismatches

    def _is_pattern_allowed(self, pattern_name: str, ext: str) -> bool:
        """某些模式在特定文件类型中是允许的"""
        # HTML 文件中允许 script 标签
        if pattern_name in ("script_tag", "iframe_tag", "object_tag"):
            return ext in (".html", ".htm")

        # SQL 关键词在 markdown 代码块中可能出现
        if pattern_name == "sql_injection":
            return ext == ".md"

        return False

    def _update_severity(self, current: str, new_level: str) -> str:
        """更新严重程度"""
        levels = {"low": 0, "medium": 1, "high": 2}
        if levels.get(new_level, 0) > levels.get(current, 0):
            return new_level
        return current

    def get_allowed_extensions(self) -> set[str]:
        """获取允许的扩展名列表"""
        return self.ALLOWED_EXTENSIONS.copy()

    def get_blocked_extensions(self) -> set[str]:
        """获取禁止的扩展名列表"""
        return self.BLOCKED_EXTENSIONS.copy()


# 全局实例
_scanner_instance: Optional[SecurityScanner] = None


def get_security_scanner() -> SecurityScanner:
    """获取安全扫描器实例"""
    global _scanner_instance
    if _scanner_instance is None:
        _scanner_instance = SecurityScanner()
    return _scanner_instance
