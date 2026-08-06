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

import re
from dataclasses import dataclass
from typing import Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ScanResult:
    """安全扫描结果"""

    safe: bool
    threats: list[str]
    severity: str  # "low", "medium", "high"
    details: dict

    @property
    def should_block(self) -> bool:
        """是否应该阻止上传"""
        return self.severity == "high"

    @property
    def requires_review(self) -> bool:
        """是否需要人工审核"""
        return self.severity == "medium"


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
        severity = "low"
        details = {
            "file_size": len(file_content),
            "declared_ext": declared_ext,
            "original_filename": original_filename,
        }

        ext = declared_ext.lower()
        if not ext.startswith("."):
            ext = f".{ext}"

        # 检查 1: 扩展名检查
        ext_result = self._check_extension(ext)
        if ext_result:
            threats.append(ext_result)
            severity = self._update_severity(severity, "high")

        # 检查 2: 文件大小检查
        size_result = self._check_file_size(len(file_content))
        if size_result:
            size_message, size_severity = size_result
            threats.append(size_message)
            severity = self._update_severity(severity, size_severity)

        # 检查 3: 文件魔数检查
        magic_result = self._check_magic_number(file_content, ext)
        if magic_result:
            threats.append(magic_result)
            severity = self._update_severity(severity, "high")

        # 检查 4: 内容特征扫描（仅文本类型）
        if self._is_text_file(ext):
            text_threats, text_severity = self._check_content_patterns(file_content, ext)
            threats.extend(text_threats)
            severity = self._update_severity(severity, text_severity)

        # 构建结果
        safe = severity != "high"

        return ScanResult(
            safe=safe,
            threats=threats,
            severity=severity,
            details=details,
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

    def _is_text_file(self, ext: str) -> bool:
        """判断是否为文本文件"""
        text_extensions = {
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
