"""
Worker 启动入口
启动后台任务处理 Worker，持续消费任务队列

特性：
- 支持多个任务类型并发消费
- 优雅关闭：处理完当前任务后退出
- 健康检查：暴露心跳状态
- 与 WebSocket 集成：实时推送任务进度

使用方式：
    # 开发模式（使用内存队列）
    python -m app.workers

    # 生产模式（使用 Redis 队列）
    WORKER_MODE=redis python -m app.workers
"""

from __future__ import annotations

import asyncio
import signal
import sys
from typing import Optional

from app.core.logging import get_logger
from app.workers.handlers import register_handlers
from app.workers.task_queue import get_task_queue

logger = get_logger(__name__)

# 全局状态
worker_state = {
    "running": False,
    "started_at": None,
    "tasks_processed": 0,
    "tasks_failed": 0,
}


async def start_worker(
    task_types: Optional[list[str]] = None,
    poll_interval: float = 1.0,
    max_concurrent: int = 5,
) -> None:
    """
    启动 Worker 主循环

    Args:
        task_types: 需要处理的任务类型列表
        poll_interval: 轮询间隔（秒）
        max_concurrent: 最大并发任务数
    """
    # 初始化 Redis 客户端（如果可用）
    redis_client = None
    try:
        from app.core.redis_client import get_redis_client

        redis_client = get_redis_client()
        logger.info("worker_redis_connected")
    except Exception:
        logger.warning("worker_redis_not_available_using_memory_queue")

    # 创建任务队列
    task_queue = get_task_queue(redis_client)

    # 注册处理器
    register_handlers(task_queue)

    # 确定要处理的任务类型
    if task_types is None:
        task_types = list(task_queue._handlers.keys())

    logger.info(
        "worker_starting",
        task_types=task_types,
        poll_interval=poll_interval,
        max_concurrent=max_concurrent,
    )

    # 更新状态
    worker_state["running"] = True
    worker_state["started_at"] = asyncio.get_event_loop().time()

    # 并发控制
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_one(task_type: str) -> None:
        """处理单个任务"""
        async with semaphore:
            task = await task_queue.fetch_task(task_type)
            if task is None:
                return

            try:
                # 更新进度
                await task_queue.update_progress(task.id, 0.1)

                # 处理任务
                await task_queue.process_task(task)

                # 更新进度
                await task_queue.update_progress(task.id, 1.0)

                worker_state["tasks_processed"] += 1
                logger.info(
                    "task_processed",
                    task_id=task.id,
                    task_type=task_type,
                )

            except Exception as e:
                worker_state["tasks_failed"] += 1
                logger.error(
                    "task_processing_failed",
                    task_id=task.id,
                    task_type=task_type,
                    error=str(e),
                )

    # 主循环
    try:
        while worker_state["running"]:
            tasks_to_process = []

            for task_type in task_types:
                # 检查队列中是否有任务
                task = await task_queue.fetch_task(task_type)
                if task is not None:
                    # 放回队列并处理
                    tasks_to_process.append(process_one.__wrapped__(task_queue, task))

            if tasks_to_process:
                # 并发处理
                await asyncio.gather(*tasks_to_process, return_exceptions=True)
            else:
                # 没有任务时等待
                await asyncio.sleep(poll_interval)

    except asyncio.CancelledError:
        logger.info("worker_cancelled")
    finally:
        worker_state["running"] = False
        logger.info(
            "worker_stopped",
            tasks_processed=worker_state["tasks_processed"],
            tasks_failed=worker_state["tasks_failed"],
        )


def stop_worker() -> None:
    """停止 Worker"""
    worker_state["running"] = False
    logger.info("worker_stop_requested")


async def run_forever(
    task_types: Optional[list[str]] = None,
    poll_interval: float = 1.0,
) -> None:
    """
    持续运行 Worker

    支持信号处理（SIGTERM, SIGINT）实现优雅关闭
    """
    loop = asyncio.get_event_loop()

    # 信号处理
    async def shutdown(signal_type):
        logger.info(f"received_signal_{signal_type}")
        stop_worker()

    try:
        loop.add_signal_handler(signal.SIGTERM, lambda: asyncio.create_task(shutdown("SIGTERM")))
        loop.add_signal_handler(signal.SIGINT, lambda: asyncio.create_task(shutdown("SIGINT")))
    except NotImplementedError:
        pass

    await start_worker(task_types=task_types, poll_interval=poll_interval)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Askora Task Worker")
    parser.add_argument(
        "--types",
        nargs="*",
        help="Task types to process (default: all)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Polling interval in seconds",
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=5,
        help="Max concurrent tasks",
    )

    args = parser.parse_args()

    try:
        asyncio.run(
            start_worker(
                task_types=args.types,
                poll_interval=args.interval,
                max_concurrent=args.max_concurrent,
            )
        )
    except KeyboardInterrupt:
        logger.info("worker_interrupted")
        sys.exit(0)
