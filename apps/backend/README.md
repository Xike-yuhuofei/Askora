# Askora 后端

> 状态：当前开发与运行说明
> 稳定基线：v0.3 Adaptive Teaching Loop

Askora 后端是面向私人本地学习 App 的 FastAPI 模块化单体。公共实现合同以 [`../../docs/specs/README.md`](../../docs/specs/README.md) 为准；本文件只说明当前代码入口和工程命令。

## 模块边界

- `app/main.py`：应用入口、健康检查和路由装配；
- `app/api/v1/`：用户、对话、文档和 WebSocket transport（无认证路由）；
- `app/orchestration/`：所有教学 transport 共用的 canonical facade；
- `app/domains/teaching_policy/`：SYS05 v0.3 policy kernel、transition 和 OPVE；
- `app/contracts/`：版本化公共合同；
- `app/queries/`：只读 query boundary；
- `app/infrastructure/`：领域记录、ledger/outbox 和 repository adapter；
- `app/services/dialog/`：对话 transport/legacy compatibility adapter；
- `app/services/documents/`：文档导入、解析和检索相关服务；
- `app/models/`、`alembic/versions/`：持久化模型和数据库迁移。

普通 `/api/v1/dialog` 当前通过 canonical facade 执行，但其 transport request 仍是 v0.2 compatibility 输入。v0.3 adaptive execution 需要完整的 TeachingContext、PolicyBundle、policy profile 和 retrieval candidates；两条分支共享同一 facade，legacy 分支不能产生 canonical v0.3 TeachingAction。

旧 `assessment`、`dkt`、`knowledge_graph`、`kt` 等目录可能包含 compatibility 或实验代码；状态所有权必须以 Specs 和 architecture tests 为准，不能根据目录名推断。

## 本地启动

```bash
python -m pip install uv==0.9.5
uv sync --frozen --extra dev
cp .env.example .env
uv run alembic upgrade head
uv run python -m app.main
```

Swagger 仅在 `local`、`development`、`test` 环境开放：`http://127.0.0.1:8000/docs`。

## 验证

```bash
uv run pytest tests --cov=app --cov-report=term-missing --cov-fail-under=45
uv run python test_document_service.py
uv run python test_optimizations.py
uv run ruff check app tests scripts test_document_service.py test_optimizations.py
uv run python ../../.github/workflows/check_black_baseline.py
uv run mypy app --no-error-summary
uv run alembic check
```

直接运行全量 `black --check` 会命中 EXEC-007 之前的锁定遗留债务；正式门禁是 `check_black_baseline.py`。

## 运行边界

- 本地模式允许 SQLite 和无 Redis 的单进程降级；
- 服务/生产模式要求 PostgreSQL、Redis 和非示例密钥；
- 真实 LLM Key 只能放在未跟踪的 `.env` 或桌面应用私有数据目录；
- replay 不调用在线 LLM；
- 模型、retrieval 或基础设施失败不得记录为学习者失败；
- `GET /users/profile` 通过 `ProfileQueryService` 读取 SYS03 canonical projection，legacy 字段只能作为来源标记清晰的只读兼容投影。
