"""
文档解析器模块
支持多种文档格式的解析与分块

支持格式：
- Markdown (.md, .markdown)
- 纯文本 (.txt)
- EPUB (.epub) - 需安装 ebooklib
- PDF (.pdf) - 需安装 pdfplumber
- DOCX (.docx) - 需安装 python-docx

设计原则：
- 优先按文档结构（标题、段落）进行分块
- 保持语义完整性，避免在句子/段落中间切割
- 支持重叠窗口，确保上下文连贯
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ParsedContent:
    """解析后的内容结构"""

    full_text: str
    chunks: list[str]
    metadata: dict
    """
    example: {
        "total_paragraphs": 45,
        "headings": ["Introduction", "Chapter 1", ...],
        "language": "zh",
        "estimated_tokens": 2500
    }
    """


@dataclass
class ChunkResult:
    """分块结果"""

    chunks: list[str]
    total_chunks: int
    total_tokens: int


class DocumentParser:
    """
    文档解析器基类

    子类实现 parse() 方法以支持不同格式
    """

    def parse(self, file_content: bytes, file_extension: str) -> ParsedContent:
        """
        解析文档内容

        Args:
            file_content: 文件二进制内容
            file_extension: 文件扩展名（不含点号）

        Returns:
            ParsedContent 解析结果
        """
        raise NotImplementedError

    def _estimate_tokens(self, text: str) -> int:
        """粗略估算 token 数量（中文约 1.5 字符/token，英文约 4 字符/token）"""
        # 简化估算：中文按 1.5 字符/token，其他按 4 字符/token
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        other_chars = len(text) - chinese_chars
        estimated = chinese_chars / 1.5 + other_chars / 4
        return max(1, int(estimated))


class MarkdownParser(DocumentParser):
    """
    Markdown 文档解析器

    特点：
    - 保留标题层级结构
    - 支持代码块、列表等格式
    - 按标题/段落智能分块
    """

    def parse(self, file_content: bytes, file_extension: str) -> ParsedContent:
        text = file_content.decode("utf-8", errors="ignore")

        # 提取元数据
        headings = re.findall(r"^(#+)\s+(.+)$", text, re.MULTILINE)
        heading_list = [h[1].strip() for h in headings]

        metadata = {
            "total_headings": len(headings),
            "heading_titles": heading_list,
            "estimated_tokens": self._estimate_tokens(text),
            "format": "markdown",
        }

        # 按结构分块
        chunks = self._split_by_structure(text)

        return ParsedContent(
            full_text=text,
            chunks=chunks,
            metadata=metadata,
        )

    def _split_by_structure(self, text: str) -> list[str]:
        """
        按 Markdown 结构分块

        策略：
        1. 优先按标题分割
        2. 长段落再按句号/换行二次分割
        3. 小段落合并避免过碎
        """
        min_tokens = settings.local_storage_chunk_min_tokens
        max_tokens = settings.local_storage_chunk_max_tokens

        # 按标题分割
        sections = re.split(r"\n(?=^#)", text, flags=re.MULTILINE)

        chunks: list[str] = []
        current_chunk: list[str] = []
        current_tokens = 0

        for section in sections:
            section_tokens = self._estimate_tokens(section)

            # 如果当前块已满，保存并开始新块
            if current_tokens >= min_tokens and current_tokens + section_tokens > max_tokens:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_tokens = 0

            # 如果段落本身超过 max_tokens，需要进一步分割
            if section_tokens > max_tokens:
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = []
                    current_tokens = 0
                # 长段落按换行进一步分割
                sub_chunks = self._split_long_text(section, max_tokens)
                chunks.extend(sub_chunks)
            else:
                current_chunk.append(section)
                current_tokens += section_tokens

        # 添加最后一个块
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        return chunks

    def _split_long_text(self, text: str, max_tokens: int) -> list[str]:
        """分割长文本"""
        paragraphs = text.split("\n\n")
        chunks: list[str] = []
        current: list[str] = []
        current_tokens = 0

        for para in paragraphs:
            para_tokens = self._estimate_tokens(para)
            if current_tokens + para_tokens > max_tokens and current:
                chunks.append("\n\n".join(current))
                current = []
                current_tokens = 0
            current.append(para)
            current_tokens += para_tokens

        if current:
            chunks.append("\n\n".join(current))

        return chunks


class PlainTextParser(DocumentParser):
    """
    纯文本解析器

    特点：
    - 按段落/句子分块
    - 支持中英文混排
    """

    def parse(self, file_content: bytes, file_extension: str) -> ParsedContent:
        text = file_content.decode("utf-8", errors="ignore")

        metadata = {
            "total_paragraphs": len(text.split("\n\n")),
            "estimated_tokens": self._estimate_tokens(text),
            "format": "plain_text",
        }

        chunks = self._split_by_paragraphs(text)

        return ParsedContent(
            full_text=text,
            chunks=chunks,
            metadata=metadata,
        )

    def _split_by_paragraphs(self, text: str) -> list[str]:
        """按段落分块"""
        min_tokens = settings.local_storage_chunk_min_tokens
        max_tokens = settings.local_storage_chunk_max_tokens

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        chunks: list[str] = []
        current_chunk: list[str] = []
        current_tokens = 0

        for para in paragraphs:
            para_tokens = self._estimate_tokens(para)

            if current_tokens >= min_tokens and current_tokens + para_tokens > max_tokens:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_tokens = 0

            if para_tokens > max_tokens:
                # 单段过长，按句子分割
                sentences = re.split(r"(?<=[。！？.!?])\s*", para)
                sent_chunk: list[str] = []
                sent_tokens = 0

                for sent in sentences:
                    sent_tokens_est = self._estimate_tokens(sent)
                    if sent_tokens + sent_tokens_est > max_tokens and sent_chunk:
                        chunks.append("".join(sent_chunk))
                        sent_chunk = []
                        sent_tokens = 0
                    sent_chunk.append(sent)
                    sent_tokens += sent_tokens_est

                if sent_chunk:
                    current_chunk.append("".join(sent_chunk))
                    current_tokens += sent_tokens
            else:
                current_chunk.append(para)
                current_tokens += para_tokens

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks


class EPubParser(DocumentParser):
    """
    EPUB 文档解析器（需安装 ebooklib）

    特点：
    - 按章节分块
    - 保留目录结构
    """

    def parse(self, file_content: bytes, file_extension: str) -> ParsedContent:
        try:
            from ebooklib import epub
        except ImportError:
            raise ImportError("EPUB 解析需要安装 ebooklib: pip install ebooklib")

        import io

        book = epub.read_epub(io.BytesIO(file_content))

        chapters = []
        for item in book.get_items_of_type(9):  # 9 = DOCUMENT
            content = item.get_content().decode("utf-8", errors="ignore")
            # 主动内容只作为扫描证据，不得进入知识建模文本。
            content = re.sub(
                r"<(?:script|style)\b[^>]*>.*?</(?:script|style)\s*>",
                " ",
                content,
                flags=re.IGNORECASE | re.DOTALL,
            )
            # 简单提取文本（去除 HTML 标签）
            text = re.sub(r"<[^>]+>", " ", content)
            text = re.sub(r"\s+", " ", text).strip()
            if text:
                chapters.append(text)

        full_text = "\n\n".join(chapters)

        metadata = {
            "total_chapters": len(chapters),
            "estimated_tokens": self._estimate_tokens(full_text),
            "format": "epub",
        }

        # 使用 PlainTextParser 进行分块
        plain_parser = PlainTextParser()
        chunks = plain_parser._split_by_paragraphs(full_text)

        return ParsedContent(
            full_text=full_text,
            chunks=chunks,
            metadata=metadata,
        )


class PdfParser(DocumentParser):
    """
    PDF 文档解析器（需安装 pdfplumber）

    特点：
    - 按页分块
    - 保留页码信息
    """

    def parse(self, file_content: bytes, file_extension: str) -> ParsedContent:
        try:
            import pdfplumber
        except ImportError:
            raise ImportError("PDF 解析需要安装 pdfplumber: pip install pdfplumber")

        import io

        pages_text = []
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ""
                if text.strip():
                    pages_text.append(f"[Page {page_num}]\n{text}")

        full_text = "\n\n".join(pages_text)

        metadata = {
            "total_pages": len(pages_text),
            "estimated_tokens": self._estimate_tokens(full_text),
            "format": "pdf",
        }

        plain_parser = PlainTextParser()
        chunks = plain_parser._split_by_paragraphs(full_text)

        return ParsedContent(
            full_text=full_text,
            chunks=chunks,
            metadata=metadata,
        )


class DocxParser(DocumentParser):
    """
    DOCX 文档解析器（需安装 python-docx）

    特点：
    - 按段落分块
    - 保留样式信息
    """

    def parse(self, file_content: bytes, file_extension: str) -> ParsedContent:
        try:
            from docx import Document
        except ImportError:
            raise ImportError("DOCX 解析需要安装 python-docx: pip install python-docx")

        import io

        doc = Document(io.BytesIO(file_content))

        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        full_text = "\n\n".join(paragraphs)

        metadata = {
            "total_paragraphs": len(paragraphs),
            "estimated_tokens": self._estimate_tokens(full_text),
            "format": "docx",
        }

        plain_parser = PlainTextParser()
        chunks = plain_parser._split_by_paragraphs(full_text)

        return ParsedContent(
            full_text=full_text,
            chunks=chunks,
            metadata=metadata,
        )


def get_parser(file_extension: str) -> DocumentParser:
    """
    根据文件扩展名获取对应的解析器

    Args:
        file_extension: 文件扩展名（不含点号）

    Returns:
        对应的解析器实例
    """
    ext = file_extension.lstrip(".").lower()

    parsers = {
        "md": MarkdownParser,
        "markdown": MarkdownParser,
        "txt": PlainTextParser,
        "epub": EPubParser,
        "pdf": PdfParser,
        "docx": DocxParser,
    }

    parser_class = parsers.get(ext)
    if parser_class is None:
        raise ValueError(f"不支持的文件格式: .{ext}，支持的格式: {list(parsers.keys())}")

    return parser_class()
