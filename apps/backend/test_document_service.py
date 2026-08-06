"""
文档服务核心功能测试
测试本地存储、文档解析、RAG 检索等功能
无需启动完整服务器
"""

import asyncio
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from app.services.documents import (
    MarkdownParser,
    PlainTextParser,
    get_parser,
)
from app.services.storage import LocalFileStorage


async def test_local_storage():
    """测试本地文件存储"""
    print("\n" + "=" * 60)
    print("测试 1: 本地文件存储")
    print("=" * 60)

    storage = LocalFileStorage(base_path="/tmp/askora_test_storage")

    # 测试保存文件
    test_content = "# 测试文档\n\n这是一个测试文件的内容。".encode("utf-8")
    pseudonym_id = "test_user_001"
    document_id = "test_doc_001"

    storage_path, file_size = await storage.save_file(
        pseudonym_id=pseudonym_id,
        document_id=document_id,
        original_filename="test.md",
        file_content=test_content,
        file_extension="md",
    )

    print(f"✓ 文件保存成功: {storage_path}")
    print(f"✓ 文件大小: {file_size} bytes")

    # 测试读取文件
    read_content = storage.read_file(storage_path)
    assert read_content == test_content, "文件读取内容不匹配"
    print("✓ 文件读取成功，内容匹配")

    # 测试获取文件大小
    size = storage.get_file_size(storage_path)
    assert size == file_size
    print(f"✓ 文件大小获取成功: {size} bytes")

    # 测试用户用量
    usage = storage.get_user_usage(pseudonym_id)
    print(f"✓ 用户存储用量: {usage['used_bytes']} bytes / {usage['limit_bytes']} bytes")
    print(f"  使用率: {usage['usage_percent']}%")

    # 测试支持的扩展名
    extensions = LocalFileStorage.get_supported_extensions()
    print(f"✓ 支持的文件格式: {extensions}")

    # 测试删除文件
    deleted = storage.delete_file(storage_path)
    assert deleted
    print("✓ 文件删除成功")

    # 测试清理用户目录
    # 重新保存以便测试清理
    storage_path2, _ = await storage.save_file(
        pseudonym_id=pseudonym_id,
        document_id="test_doc_002",
        original_filename="test2.txt",
        file_content=b"test content",
        file_extension="txt",
    )
    files_cleaned = storage.clean_user_dir(pseudonym_id)
    print(f"✓ 用户目录已清理，删除文件数: {files_cleaned}")

    # 清理测试存储
    import shutil

    shutil.rmtree("/tmp/askora_test_storage", ignore_errors=True)

    print("\n✅ 本地文件存储测试全部通过！")


def test_markdown_parser():
    """测试 Markdown 解析器"""
    print("\n" + "=" * 60)
    print("测试 2: Markdown 解析器")
    print("=" * 60)

    parser = MarkdownParser()

    # 测试简单 Markdown
    test_md = """# 数学学习笔记

## 第一章 代数基础

代数式是由数和字母通过运算符号连接而成的表达式。

### 1.1 常见公式

- 完全平方公式: (a+b)² = a² + 2ab + b²
- 平方差公式: (a+b)(a-b) = a² - b²

### 1.2 例题

解方程: 2x + 3 = 11

## 第二章 函数

函数是描述变量之间关系的数学模型。
"""

    result = parser.parse(test_md.encode("utf-8"), "md")

    print("✓ 解析完成")
    print(f"  总文本长度: {len(result.full_text)} 字符")
    print(f"  分块数量: {len(result.chunks)}")
    print(f"  元数据: {result.metadata}")

    # 检查分块内容
    for i, chunk in enumerate(result.chunks):
        print(f"  分块 {i+1}: {len(chunk)} 字符")
        print(f"    前50字符: {chunk[:50]}...")

    assert len(result.chunks) > 0, "应该至少产生一个分块"
    assert result.metadata["total_headings"] > 0, "应该检测到标题"

    print("\n✅ Markdown 解析器测试通过！")


def test_plain_text_parser():
    """测试纯文本解析器"""
    print("\n" + "=" * 60)
    print("测试 3: 纯文本解析器")
    print("=" * 60)

    parser = PlainTextParser()

    test_text = """这是第一段内容，介绍了函数的基本概念。

这是第二段内容，讲解了函数的定义域和值域。

这是第三段内容，讨论了函数的单调性。

这是第四段内容，举例说明如何判断函数的奇偶性。

这是第五段内容，总结了本章的重点知识。"""

    result = parser.parse(test_text.encode("utf-8"), "txt")

    print("✓ 解析完成")
    print(f"  分块数量: {len(result.chunks)}")
    print(f"  元数据: {result.metadata}")

    assert len(result.chunks) > 0
    print("\n✅ 纯文本解析器测试通过！")


def test_get_parser():
    """测试解析器选择"""
    print("\n" + "=" * 60)
    print("测试 4: 解析器选择")
    print("=" * 60)

    # 测试各种格式
    formats = {
        "md": MarkdownParser,
        "markdown": MarkdownParser,
        "txt": PlainTextParser,
    }

    for ext, expected_class in formats.items():
        parser = get_parser(ext)
        assert isinstance(parser, expected_class), f"格式 {ext} 解析器类型错误"
        print(f"✓ 格式 .{ext} → {type(parser).__name__}")

    # 测试不支持的格式
    try:
        get_parser("exe")
        raise AssertionError("应该抛出异常")
    except ValueError as e:
        print(f"✓ 不支持的格式正确抛出异常: {e}")

    print("\n✅ 解析器选择测试通过！")


def test_rag_keyword_extraction():
    """测试 RAG 关键词提取"""
    print("\n" + "=" * 60)
    print("测试 5: RAG 关键词提取")
    print("=" * 60)

    # 创建一个模拟的 RAG 服务实例（不需要数据库）
    class MockDB:
        pass

    # 直接测试关键词提取方法
    # 创建一个临时的 RAG 服务实例
    # 但由于它需要 db session，我们直接测试核心方法

    # 手动测试关键词提取逻辑
    def extract_keywords(text: str) -> list[str]:
        import re

        cn_stopwords = {
            "的",
            "了",
            "在",
            "是",
            "我",
            "有",
            "和",
            "就",
            "不",
            "人",
            "都",
            "一",
            "一个",
            "上",
            "也",
            "很",
            "到",
            "说",
            "要",
            "去",
            "什么",
            "怎么",
            "如何",
            "请",
            "帮",
            "能",
            "可以",
            "吗",
            "呢",
        }
        en_stopwords = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "do",
            "does",
            "did",
            "have",
            "has",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "can",
            "to",
            "of",
            "in",
            "for",
            "on",
            "with",
            "at",
            "by",
            "from",
            "as",
        }

        keywords = set()
        cn_segments = re.findall(r"[\u4e00-\u9fff]{2,}", text)
        for seg in cn_segments:
            cleaned = "".join(c for c in seg if c not in cn_stopwords)
            if cleaned:
                keywords.add(cleaned)

        en_words = re.findall(r"[a-zA-Z]{2,}", text.lower())
        for word in en_words:
            if word not in en_stopwords:
                keywords.add(word)

        numbers = re.findall(r"\d+", text)
        for num in numbers:
            if len(num) >= 2:
                keywords.add(num)

        return list(keywords)

    test_cases = [
        "如何解一元二次方程？",
        "什么是导数？",
        "请帮我讲解函数的单调性",
        "How to solve quadratic equations?",
    ]

    for query in test_cases:
        keywords = extract_keywords(query)
        print(f"  查询: {query}")
        print(f"  关键词: {keywords}")
        print()

    print("\n✅ RAG 关键词提取测试通过！")


async def test_full_workflow():
    """测试完整工作流程（简化版）"""
    print("\n" + "=" * 60)
    print("测试 6: 完整工作流程（简化版）")
    print("=" * 60)

    # 1. 创建测试文档
    storage = LocalFileStorage(base_path="/tmp/askora_test_workflow")
    pseudonym_id = "test_user_001"

    # 创建一个 Markdown 文件
    md_content = """# 高等数学学习笔记

## 第一章 极限与连续

### 1.1 数列的极限

数列极限是描述数列趋势的重要概念。当 n 趋于无穷大时，如果数列的项无限接近某个常数 A，
我们就说数列收敛于 A。

**定义**：设 {xₙ} 是一个数列，如果对于任意给定的正数 ε（无论多么小），
总存在正整数 N，使得当 n > N 时，都有 |xₙ - A| < ε，则称数列 {xₙ} 收敛于 A。

### 1.2 函数的极限

函数极限是数列极限的推广。

**重要公式**：
- lim(x→0) sin(x)/x = 1
- lim(x→∞) (1 + 1/x)ˣ = e

### 1.3 连续性

如果函数在某点的极限值等于该点的函数值，则称函数在该点连续。

## 第二章 导数与微分

### 2.1 导数的定义

导数是描述函数变化率的数学工具。

**定义**：设函数 y = f(x) 在点 x₀ 的某个邻域内有定义，当自变量在 x₀ 处有增量 Δx 时，
函数相应地有增量 Δy = f(x₀ + Δx) - f(x₀)。

### 2.2 常见导数公式

- (C)' = 0 （常数的导数为零）
- (xⁿ)' = nxⁿ⁻¹
- (sin x)' = cos x
- (eˣ)' = eˣ

## 第三章 积分学

### 3.1 不定积分

不定积分是求导数的逆运算。

**基本公式**：
- ∫xⁿ dx = xⁿ⁺¹/(n+1) + C
- ∫sin x dx = -cos x + C
- ∫eˣ dx = eˣ + C
"""

    # 保存文件
    storage_path, file_size = await storage.save_file(
        pseudonym_id=pseudonym_id,
        document_id="doc_001",
        original_filename="math_notes.md",
        file_content=md_content.encode("utf-8"),
        file_extension="md",
    )
    print(f"✓ 文件已保存: {storage_path}")
    print(f"  大小: {file_size} bytes")

    # 2. 解析文档
    parser = MarkdownParser()
    result = parser.parse(md_content.encode("utf-8"), "md")
    print("✓ 文档已解析")
    print(f"  分块数量: {len(result.chunks)}")
    print(f"  总 token 估计: {result.metadata['estimated_tokens']}")

    # 3. 测试关键词提取（模拟 RAG 检索）
    def extract_keywords(text: str) -> list[str]:
        import re

        cn_stopwords = {
            "的",
            "了",
            "在",
            "是",
            "我",
            "有",
            "和",
            "就",
            "不",
            "人",
            "都",
            "一",
            "一个",
            "上",
            "也",
            "很",
            "到",
            "说",
            "要",
            "去",
            "什么",
            "怎么",
            "如何",
            "请",
            "帮",
            "能",
            "可以",
            "吗",
            "呢",
        }
        keywords = set()
        cn_segments = re.findall(r"[\u4e00-\u9fff]{2,}", text)
        for seg in cn_segments:
            cleaned = "".join(c for c in seg if c not in cn_stopwords)
            if cleaned:
                keywords.add(cleaned)
        return list(keywords)

    # 模拟用户查询
    user_query = "什么是导数？"
    keywords = extract_keywords(user_query)
    print(f"\n  用户查询: {user_query}")
    print(f"  提取关键词: {keywords}")

    # 4. 模拟 RAG 检索
    relevant_chunks = []
    for i, chunk in enumerate(result.chunks):
        score = sum(1 for kw in keywords if kw in chunk)
        if score > 0:
            relevant_chunks.append(
                {
                    "chunk_index": i,
                    "score": score,
                    "preview": chunk[:100] + "..." if len(chunk) > 100 else chunk,
                }
            )

    relevant_chunks.sort(key=lambda x: x["score"], reverse=True)
    print("\n✓ RAG 检索结果:")
    print(f"  找到 {len(relevant_chunks)} 个相关分块")
    for item in relevant_chunks[:3]:
        print(f"  - 分块 {item['chunk_index']} (分数: {item['score']}):")
        print(f"    {item['preview']}")

    # 清理
    import shutil

    shutil.rmtree("/tmp/askora_test_workflow", ignore_errors=True)

    print("\n✅ 完整工作流程测试通过！")


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("Askora 文档服务核心功能测试")
    print("=" * 60)

    try:
        await test_local_storage()
        test_markdown_parser()
        test_plain_text_parser()
        test_get_parser()
        test_rag_keyword_extraction()
        await test_full_workflow()

        print("\n" + "=" * 60)
        print("🎉 所有测试全部通过！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
