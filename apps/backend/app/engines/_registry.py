"""
Teaching Engine Registry —— 引擎注册表（独立叶子模块，避免循环 import）

ENGINE_REGISTRY 由 @register_engine 装饰器在引擎模块 import 时填充。

关键设计：本模块是「叶子模块」，**不 import 任何 app.engines.base / orchestrator /
具体引擎**。这样即使用户代码通过 `from app.engines.base import ...` 或
`from app.engines.orchestrator import ...` 触发包 __init__，也不会形成
`base → _registry → base` 或 `orchestrator → _registry → orchestrator` 的循环。

类型注解使用 `type` / `Type[Any]` 而非常量化的 `TeachingEngine`，从而彻底
切断 `_registry → base` 这条依赖边，为未来 base 反向引用注册表留出安全空间。
"""

from __future__ import annotations

from typing import Any, Type

ENGINE_REGISTRY: dict[str, Type[Any]] = {}


def register_engine(engine_cls: Type[Any]) -> Type[Any]:
    """向全局注册表注册一个教学引擎（按 engine_id 去重）"""
    if not engine_cls.engine_id:
        raise ValueError(f"engine_cls {engine_cls.__name__} has empty engine_id")
    if (
        engine_cls.engine_id in ENGINE_REGISTRY
        and ENGINE_REGISTRY[engine_cls.engine_id] is not engine_cls
    ):
        # 相同 engine_id 重复注册是错误（便于及早发现名字冲突）
        raise RuntimeError(f"duplicate register_engine: {engine_cls.engine_id}")
    ENGINE_REGISTRY[engine_cls.engine_id] = engine_cls
    return engine_cls


def list_registered_engines() -> list[dict]:
    """返回已注册引擎的元数据列表（用于调试 / API 发现）"""
    return [
        {
            "engine_id": cls.engine_id,
            "engine_name": cls.engine_name,
            "supported_cognitive_levels": [lv.value for lv in cls.supported_cognitive_levels],
            "supported_openness": [op.value for op in cls.supported_openness],
        }
        for cls in ENGINE_REGISTRY.values()
    ]


__all__ = ["ENGINE_REGISTRY", "register_engine", "list_registered_engines"]
