# Askora Backend Alembic 实施计划

## 背景

为 Askora 后端项目创建 Alembic 数据库迁移基础设施。项目已有 SQLAlchemy 2.0 async 模型定义（在 `app/models/knowledge.py` 中），现在需要建立 Alembic 迁移体系。

## 现有架构分析

- **ORM 模型**：`app/models/knowledge.py` 定义了 `KnowledgePoint`、`LearningMaterial`、`StrategyTemplate` 三个模型
- **数据库配置**：`app/core/database.py` 中的 `Base`（DeclarativeBase 子类），使用 `asyncpg` 异步引擎
- **配置管理**：`app/core/config.py` 中 `Settings` 使用 pydantic-settings，`database_url` 为 `postgresql+asyncpg://`
- **注意**：`StrategyTemplate` 模型未在 `app/models/__init__.py` 中导入，需在迁移环境中直接 import

## 要创建的文件

### 1. `alembic.ini` — Alembic 主配置文件
- 路径：`apps/backend/alembic.ini`
- 配置 `sqlalchemy.url = postgresql://user:pass@localhost/askora`（占位符）
- 配置 `script_location = alembic`
- 添加 `[loggers]`、`[handlers]`、`[formatters]` 基本配置

### 2. `alembic/env.py` — Alembic 异步环境配置
- 路径：`apps/backend/alembic/env.py`
- 从 `app.core.config` 导入 `settings`
- 从 `app.core.database` 导入 `Base`
- 导入所有 ORM 模型（包括 `StrategyTemplate`、`KnowledgePoint`、`LearningMaterial`）
- 使用 `settings.database_url` 配置异步引擎
- 实现 `run_async_migrations()` 函数

### 3. `alembic/versions/__init__.py`
- 路径：`apps/backend/alembic/versions/__init__.py`
- 空文件

### 4. `alembic/versions/001_add_strategy_templates.py` — 初始迁移脚本
- 路径：`apps/backend/alembic/versions/001_add_strategy_templates.py`
- Revision ID: `001`
- 创建 `strategy_templates` 表（按用户要求的列）
- 创建 `knowledge_points` 表
- 创建 `learning_materials` 表
- 包含复合索引和 downgrade 函数

### 5. `alembic/script.py.mako` — 标准 Alembic 模板
- 路径：`apps/backend/alembic/script.py.mako`

## 文件结构

```
apps/backend/
├── alembic.ini
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── __init__.py
│       └── 001_add_strategy_templates.py
```

## 执行步骤

1. 创建 `alembic.ini`
2. 创建 `alembic/env.py`
3. 创建 `alembic/versions/` 目录和 `__init__.py`
4. 创建 `alembic/versions/001_add_strategy_templates.py`
5. 创建 `alembic/script.py.mako`
