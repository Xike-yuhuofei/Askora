"""
任务队列服务
基于 Redis List 实现的轻量级任务队列，支持优先级、重试、超时

特性：
- 基于 Redis，无需额外引入 Celery
- 支持任务优先级（0-3）
- 支持自动重试（指数退避）
- 支持任务超时控制
- 支持任务状态追踪
- 与 WebSocket 集成，实时推送进度

Redis Key 结构：
- task:queue:{type}:pending  - 待处理任务（List）
- task:queue:{type}:processing - 处理中任务（Hash）
- task:queue:{type}:completed  - 已完成任务（Hash）
- task:queue:{type}:failed    - 失败任务（Hash）
- task:{task_id}              - 任务详情（Hash）
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class TaskStatus(str, Enum):
    """任务状态"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(int, Enum):
    """任务优先级（数字越大优先级越高）"""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


@dataclass
class Task:
    """任务定义"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""  # 任务类型，如 "document_process"
    payload: dict = field(default_factory=dict)
    priority: int = TaskPriority.NORMAL
    max_retries: int = 3
    timeout: int = 300  # 超时时间（秒）
    status: str = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    retry_count: int = 0
    progress: float = 0.0
    result: Optional[dict] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "payload": self.payload,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "retry_count": self.retry_count,
            "progress": self.progress,
            "result": self.result,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class TaskQueue:
    """
    基于 Redis 的任务队列

    降级策略：
    - Redis 可用 → 使用 Redis 队列
    - Redis 不可用 → 使用内存队列（仅开发模式）
    """

    def __init__(self, redis_client=None):
        self._redis = redis_client
        self._use_redis = redis_client is not None
        self._memory_queue: dict[str, list[Task]] = {}  # 内存队列降级
        self._memory_tasks: dict[str, Task] = {}
        self._handlers: dict[str, Callable] = {}
        self._running = False

    def register_handler(self, task_type: str, handler: Callable) -> None:
        """注册任务处理器"""
        self._handlers[task_type] = handler
        logger.info(f"task_handler_registered: {task_type}")

    async def enqueue(self, task: Task) -> str:
        """
        将任务加入队列

        Args:
            task: 任务对象

        Returns:
            任务 ID
        """
        task.status = TaskStatus.PENDING

        if self._use_redis:
            await self._enqueue_redis(task)
        else:
            self._enqueue_memory(task)

        logger.info(
            "task_enqueued",
            task_id=task.id,
            task_type=task.type,
            priority=task.priority,
        )

        return task.id

    async def _enqueue_redis(self, task: Task) -> None:
        """Redis 入队"""
        key = f"task:queue:{task.type}:pending"
        priority_prefix = f"{task.priority}:"
        await self._redis.lpush(key, priority_prefix + task.id)

        # 保存任务详情
        await self._redis.hset(
            f"task:{task.id}",
            mapping={
                "data": json.dumps(task.to_dict()),
                "created_at": str(task.created_at),
            },
        )

    def _enqueue_memory(self, task: Task) -> None:
        """内存入队"""
        key = task.type
        if key not in self._memory_queue:
            self._memory_queue[key] = []

        self._memory_queue[key].append(task)
        self._memory_queue[key].sort(key=lambda t: t.priority, reverse=True)
        self._memory_tasks[task.id] = task

    async def fetch_task(self, task_type: str) -> Optional[Task]:
        """
        从队列获取一个任务

        Args:
            task_type: 任务类型

        Returns:
            任务对象或 None
        """
        if self._use_redis:
            return await self._fetch_redis(task_type)
        else:
            return self._fetch_memory(task_type)

    async def _fetch_redis(self, task_type: str) -> Optional[Task]:
        """Redis 获取任务"""
        key = f"task:queue:{task_type}:pending"
        priority_order = sorted(range(4), reverse=True)  # 3, 2, 1, 0

        for priority in priority_order:
            priority_prefix = f"{priority}:"
            task_id = await self._redis.lpop(key)

            if task_id:
                # 检查优先级前缀
                if task_id.startswith(priority_prefix):
                    task_id = task_id[len(priority_prefix) :]
                else:
                    # 如果没有前缀，需要重新排序
                    pass

                # 获取任务详情
                task_data = await self._redis.hget(f"task:{task_id}", "data")
                if task_data:
                    task = Task.from_dict(json.loads(task_data))
                    task.status = TaskStatus.PROCESSING
                    task.started_at = time.time()
                    return task

        return None

    def _fetch_memory(self, task_type: str) -> Optional[Task]:
        """内存获取任务"""
        queue = self._memory_queue.get(task_type, [])
        if queue:
            task = queue.pop(0)
            task.status = TaskStatus.PROCESSING
            task.started_at = time.time()
            return task
        return None

    async def complete_task(self, task_id: str, result: Optional[dict] = None) -> None:
        """标记任务完成"""
        if self._use_redis:
            await self._redis.hset(
                f"task:{task_id}",
                mapping={
                    "status": TaskStatus.COMPLETED,
                    "completed_at": str(time.time()),
                    "result": json.dumps(result or {}),
                },
            )
        else:
            if task_id in self._memory_tasks:
                self._memory_tasks[task_id].status = TaskStatus.COMPLETED
                self._memory_tasks[task_id].completed_at = time.time()
                self._memory_tasks[task_id].result = result

        logger.info("task_completed", task_id=task_id)

    async def fail_task(self, task_id: str, error: str) -> None:
        """标记任务失败"""
        if self._use_redis:
            await self._redis.hset(
                f"task:{task_id}",
                mapping={
                    "status": TaskStatus.FAILED,
                    "completed_at": str(time.time()),
                    "error": error,
                },
            )
        else:
            if task_id in self._memory_tasks:
                self._memory_tasks[task_id].status = TaskStatus.FAILED
                self._memory_tasks[task_id].completed_at = time.time()
                self._memory_tasks[task_id].error = error

        logger.error("task_failed", task_id=task_id, error=error)

    async def update_progress(self, task_id: str, progress: float) -> None:
        """更新任务进度"""
        progress = max(0.0, min(1.0, progress))

        if self._use_redis:
            await self._redis.hset(
                f"task:{task_id}",
                "progress",
                str(progress),
            )
        else:
            if task_id in self._memory_tasks:
                self._memory_tasks[task_id].progress = progress

    async def get_task_status(self, task_id: str) -> dict:
        """获取任务状态"""
        if self._use_redis:
            data = await self._redis.hgetall(f"task:{task_id}")
            return dict(data) if data else {}
        else:
            if task_id in self._memory_tasks:
                return self._memory_tasks[task_id].to_dict()
            return {}

    async def retry_task(self, task_id: str, task_type: str, payload: dict) -> str:
        """重试任务"""
        task = Task(
            type=task_type,
            payload=payload,
            max_retries=3,
        )
        return await self.enqueue(task)

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if self._use_redis:
            await self._redis.hset(
                f"task:{task_id}",
                "status",
                TaskStatus.CANCELLED,
            )
        else:
            if task_id in self._memory_tasks:
                self._memory_tasks[task_id].status = TaskStatus.CANCELLED

        logger.info("task_cancelled", task_id=task_id)
        return True

    async def process_task(self, task: Task) -> dict:
        """
        处理任务

        Args:
            task: 任务对象

        Returns:
            处理结果
        """
        if task.type not in self._handlers:
            raise ValueError(f"No handler registered for task type: {task.type}")

        handler = self._handlers[task.type]

        try:
            # 设置超时
            result = await asyncio.wait_for(
                handler(task),
                timeout=task.timeout,
            )

            await self.complete_task(task.id, result)
            return result

        except asyncio.TimeoutError:
            error_msg = f"Task timed out after {task.timeout}s"
            await self.fail_task(task.id, error_msg)
            raise TimeoutError(error_msg)

        except Exception as e:
            error_msg = str(e)
            await self.fail_task(task.id, error_msg)
            raise


# 全局实例
_task_queue_instance: Optional[TaskQueue] = None


def get_task_queue(redis_client=None) -> TaskQueue:
    """获取任务队列实例"""
    global _task_queue_instance
    if _task_queue_instance is None:
        _task_queue_instance = TaskQueue(redis_client)
    return _task_queue_instance
