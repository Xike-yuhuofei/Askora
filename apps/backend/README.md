# Askora 后端

这是 Askora 私人自用学习 App 的 FastAPI 后端。完整项目边界、运行和验证说明见项目根目录 `README.md`。

## 入口与模块

- 应用入口：`app/main.py`（`python -m app.main` 或 `uvicorn app.main:app`）
- HTTP/WS 路由：`app/api/v1`
- 核心对话：`app/services/dialog` 与 `app/engines`
- 认证：`app/services/auth`
- 文档/RAG：`app/services/documents` 与 `app/services/storage`
- 数据模型：`app/models`
- 迁移：`alembic/versions`

主 API 是认证、用户、对话、文档和 WebSocket。评估、DKT、知识图谱、Worker、旧监护/同意模型和 PEP 网关尚未接入当前主路径，不应据其代码或早期架构文档宣称功能已经交付。

## 快速开始

```bash
python3.11 -m venv .venv
.venv/bin/pip install -e '.[dev,desktop]'
cp .env.example .env
.venv/bin/alembic upgrade head
.venv/bin/python -m app.main
```

Swagger 只在 `local`、`development`、`test` 环境开放：`http://127.0.0.1:8000/docs`。

## 检查

```bash
.venv/bin/ruff check app tests scripts test_document_service.py test_optimizations.py
.venv/bin/black --check app tests scripts test_document_service.py test_optimizations.py
.venv/bin/mypy app --ignore-missing-imports --no-error-summary
.venv/bin/pytest tests --cov=app --cov-report=term-missing --cov-fail-under=45
.venv/bin/python test_document_service.py
.venv/bin/python test_optimizations.py
.venv/bin/alembic check
```

## 私人模式说明

本项目不公开发布，不以多租户或公共互联网服务为默认场景。生产环境仍会强制要求非默认的 JWT/KEK 密钥，并要求数据库和 Redis 可用；本地模式允许 SQLite 与无 Redis 的单进程降级运行。真实 LLM Key 只放在未跟踪的 `.env` 或桌面应用私有数据目录中。
