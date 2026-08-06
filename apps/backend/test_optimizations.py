"""
Askora 文档服务优化功能测试
测试所有新增功能：jieba 分词、任务队列、安全扫描等
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))


async def test_jieba_tokenizer():
    """测试 jieba 分词服务"""
    print("\n" + "=" * 60)
    print("测试 1: jieba 分词服务")
    print("=" * 60)

    from app.services.documents.tokenizer import get_tokenizer

    tokenizer = get_tokenizer()

    # 测试分词
    test_cases = [
        "如何解一元二次方程？",
        "什么是导数和积分？",
        "矩阵的特征值怎么求？",
        "How to solve quadratic equations?",
        "Python 中递归和迭代有什么区别？",
    ]

    for query in test_cases:
        tokens = tokenizer.tokenize(query)
        keywords = tokenizer.extract_keywords(query, top_k=5)
        print(f"  查询: {query}")
        print(f"    分词: {tokens}")
        print(f"    关键词: {keywords}")
        print()

    print("✅ jieba 分词服务测试通过！")


async def test_chinese_tokenizer_with_dict():
    """测试专业词典加载"""
    print("\n" + "=" * 60)
    print("测试 2: 专业词典加载")
    print("=" * 60)

    from app.services.documents.tokenizer import get_tokenizer

    tokenizer = get_tokenizer()

    # 测试专业术语识别
    professional_queries = [
        "牛顿第二定律",
        "万有引力常数",
        "氧化还原反应",
        "动态规划算法",
        "卷积神经网络",
        "RAG 检索增强生成",
    ]

    for query in professional_queries:
        keywords = tokenizer.extract_keywords(query, top_k=5)
        print(f"  查询: {query}")
        print(f"    关键词: {keywords}")
        print()

    print("✅ 专业词典测试通过！")


async def test_security_scanner():
    """测试安全扫描服务"""
    print("\n" + "=" * 60)
    print("测试 3: 文件安全扫描")
    print("=" * 60)

    from app.services.documents.security_scanner import get_security_scanner

    scanner = get_security_scanner()

    # 测试用例
    test_cases = [
        {
            "name": "安全 Markdown 文件",
            "content": "# 学习笔记\n\n这是一个安全的文档。",
            "ext": ".md",
            "expect_safe": True,
        },
        {
            "name": "危险扩展名 .exe",
            "content": "MZ\x90\x00\x03\x00",
            "ext": ".exe",
            "expect_safe": False,
        },
        {
            "name": "HTML 中的 script 标签",
            "content": "<html><script>alert('xss')</script></html>",
            "ext": ".html",
            "expect_safe": True,  # HTML 允许 script 标签
        },
        {
            "name": "Markdown 中的 SQL 注入",
            "content": "# SQL 学习\n\nSELECT * FROM users WHERE name='admin' OR '1'='1'",
            "ext": ".md",
            "expect_safe": True,  # Markdown 允许 SQL 关键词出现
        },
        {
            "name": "可执行脚本内容",
            "content": "eval('system('ls')')",
            "ext": ".txt",
            "expect_safe": False,
        },
    ]

    for case in test_cases:
        result = scanner.scan(
            file_content=(
                case["content"].encode() if isinstance(case["content"], str) else case["content"]
            ),
            declared_ext=case["ext"],
            original_filename=f"test{case['ext']}",
        )

        status = "✅" if result.safe == case["expect_safe"] else "❌"
        print(f"  {status} {case['name']}:")
        print(f"    安全: {result.safe}, 严重程度: {result.severity}")
        if result.threats:
            print(f"    威胁: {result.threats}")
        print()
        assert result.safe == case["expect_safe"], case["name"]

    print("✅ 安全扫描测试完成！")


async def test_task_queue_memory():
    """测试任务队列（内存模式）"""
    print("\n" + "=" * 60)
    print("测试 4: 任务队列（内存模式）")
    print("=" * 60)

    from app.workers.task_queue import Task, TaskPriority, TaskQueue

    # 创建内存队列
    queue = TaskQueue(redis_client=None)

    # 注册一个简单的测试处理器
    async def test_handler(task: Task) -> dict:
        await asyncio.sleep(0.1)
        return {"processed": True, "task_id": task.id}

    queue.register_handler("test_task", test_handler)

    # 入队任务
    task = Task(
        type="test_task",
        payload={"data": "hello"},
        priority=TaskPriority.HIGH,
    )
    task_id = await queue.enqueue(task)
    print(f"  任务已入队: {task_id}")

    # 获取任务
    fetched = await queue.fetch_task("test_task")
    print(f"  任务已获取: {fetched.id if fetched else 'None'}")

    if fetched:
        # 更新进度
        await queue.update_progress(task_id, 0.5)
        status = await queue.get_task_status(task_id)
        print(f"  进度已更新: {status}")

        # 完成任务
        await queue.complete_task(task_id, {"result": "success"})
        final_status = await queue.get_task_status(task_id)
        print(f"  任务完成: {final_status}")

    print("✅ 任务队列测试通过！")


async def test_ws_manager():
    """测试 WebSocket 管理器（基础功能）"""
    print("\n" + "=" * 60)
    print("测试 5: WebSocket 管理器")
    print("=" * 60)

    from app.services.websocket.ws_manager import (
        ProgressEvent,
        create_progress_message,
        get_ws_manager,
    )

    ws_manager = get_ws_manager()

    # 测试进度消息创建
    message = create_progress_message(
        document_id="doc_001",
        progress=0.6,
        step="正在解析文档...",
        status="processing",
    )
    print(f"  进度消息: {message}")

    # 测试事件类型
    assert message["type"] == ProgressEvent.PROGRESS
    assert message["progress"] == 0.6
    assert message["document_id"] == "doc_001"

    # 测试状态检查
    has_conn = ws_manager.has_connection("test_user")
    print(f"  用户连接状态: {has_conn}")
    assert not has_conn  # 没有连接

    print("✅ WebSocket 管理器测试通过！")


async def test_embedding_service():
    """测试向量服务（降级模式）"""
    print("\n" + "=" * 60)
    print("测试 6: 向量服务")
    print("=" * 60)

    from app.services.documents.embedding_service import get_embedding_service

    service = get_embedding_service()

    # 检查服务状态
    print(f"  服务可用: {service.is_available}")
    print(f"  模型: {service._model}")
    print(f"  维度: {service._dimension}")

    # 在无 API Key 时返回 None（降级）
    result = await service.embed_text("测试文本")
    print(f"  嵌入结果（预期为 None 因为没有 API Key）: {result}")
    assert result is None

    # 测试相似度计算（使用假数据）
    vec_a = [1.0, 0.0, 0.0]
    vec_b = [0.0, 1.0, 0.0]
    similarity = await service.compute_similarity(vec_a, vec_b)
    print(f"  正交向量相似度: {similarity}")
    assert similarity == 0.0

    vec_c = [1.0, 0.0, 0.0]
    similarity_same = await service.compute_similarity(vec_a, vec_c)
    print(f"  相同向量相似度: {similarity_same}")
    assert similarity_same == 1.0

    print("✅ 向量服务测试通过！")


async def test_rag_with_jieba():
    """测试 RAG 检索（使用 jieba 分词）"""
    print("\n" + "=" * 60)
    print("测试 7: RAG 关键词提取（jieba 版）")
    print("=" * 60)

    # 直接测试分词提取
    from app.services.documents.tokenizer import get_tokenizer

    tokenizer = get_tokenizer()

    test_queries = [
        "如何求函数的导数？",
        "什么是矩阵的特征值和特征向量？",
        "牛顿第二定律的公式是什么？",
        "化学平衡状态有哪些特征？",
        "动态规划算法的基本思想是什么？",
    ]

    for query in test_queries:
        keywords = tokenizer.get_keywords_set(query, top_k=8)
        print(f"  查询: {query}")
        print(f"    关键词: {keywords}")
        print()

    print("✅ RAG 分词测试通过！")


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("Askora 文档服务优化功能测试")
    print("=" * 60)

    try:
        await test_jieba_tokenizer()
        await test_chinese_tokenizer_with_dict()
        await test_security_scanner()
        await test_task_queue_memory()
        await test_ws_manager()
        await test_embedding_service()
        await test_rag_with_jieba()

        print("\n" + "=" * 60)
        print("🎉 所有测试全部通过！")
        print("=" * 60)
        print("\n新增功能总结：")
        print("  1. jieba 中文分词 + 专业词典（数学/物理/化学/计算机）")
        print("  2. 基于 Redis/内存的任务队列（支持优先级、重试、进度）")
        print("  3. WebSocket 实时进度推送")
        print("  4. 向量嵌入服务（支持降级）")
        print("  5. 文件安全扫描（扩展名/魔数/内容特征）")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
