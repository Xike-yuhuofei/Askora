"""Workers 层对 durable outbox worker 的稳定 adapter 入口。"""

from app.infrastructure.outbox import DurableOutboxWorker, PermanentTaskError

__all__ = ["DurableOutboxWorker", "PermanentTaskError"]
