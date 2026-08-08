# Askora

Askora 是一个**私人自用、不公开发布**的本地 AI 学习 App。仓库包含 FastAPI 后端、React/Vite 前端和 macOS Electron 桌面壳；默认运行边界是单用户、单设备、本地优先，而不是多租户 SaaS 或公共互联网服务。

私人使用不等于可以忽略安全。本地数据库、上传资料、LLM 密钥、JWT/加密密钥和备份均应按敏感数据处理；不得提交 `.env`、数据库、用户资料、构建产物或桌面后端二进制。

## 当前基线

当前冻结基线是 v0.3 Adaptive Teaching Loop：

```text
Engineering Gate: PASS
Policy Correctness Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

这表示工程链路和教学策略约束通过验收，不表示已经证明真人学习效果。完整证据见 [v0.3 Release Report](docs/releases/v0.3-adaptive-teaching-loop.md)。

实现必须服从 [Implementation Specs](docs/specs/README.md)；系统边界和单一写入者分别见 [System Architecture](docs/specs/architecture/system-architecture.md) 与 [State Ownership](docs/specs/architecture/state-ownership.md)。

## 当前实现边界

所有普通、流式和 WebSocket 教学入口都必须进入 `LearningOrchestrationFacade`，transport adapter 不直接选择教学引擎。完整 v0.3 adaptive 请求按以下链路执行：

```text
TeachingContext + PolicyBundle
→ SYS05 TeachingAction / DecisionTrace
→ SYS02 EvidenceBundle
→ SYS08 受约束执行
→ SYS04 Attempt / AssessmentResult
→ SYS03 LearnerEvidence / MasteryEstimate
→ SYS07 ReviewSchedule
→ SYS06 在触发时重规划
```

当前普通 `/api/v1/dialog` 适配器已汇入 canonical facade，但仍构造 v0.2 compatibility 输入；只有传入完整 v0.3 adaptive context 时才进入 v0.3 policy-bound execution。v0.3 路径已经过独立 E2E/release gate，不应据此声称所有前端对话默认启用了 adaptive policy。

主要代码位置：

- `apps/backend/app/orchestration/`：canonical learning facade 与跨系统执行；
- `apps/backend/app/domains/teaching_policy/`：SYS05 deterministic policy 与 sequential transition；
- `apps/backend/app/contracts/`：公共、版本化领域合同；
- `apps/backend/app/queries/`：只读 query boundary；
- `apps/backend/app/services/dialog/`：对话 transport/compatibility adapter；
- `apps/backend/app/services/documents/`：文档导入和检索适配；
- `apps/frontend/src/`：Web/Electron 共用前端；
- `apps/frontend/electron/`：桌面进程和本地后端生命周期。

`assessment`、`dkt`、`knowledge_graph`、`kt` 等 legacy 目录是迁移起点，不因目录存在而自动拥有 canonical 状态或代表功能已接入默认产品路径。

## 环境要求

- Python 3.11 或 3.12；
- `uv 0.9.5`（与 CI 一致）；
- Node.js 22（CI 版本；Vite 8 的最低兼容版本为 Node.js 20.19+）；
- npm；
- 构建 macOS 桌面版时需要 Xcode Command Line Tools；
- Redis 7、PostgreSQL 16 和 Docker Compose 仅在相应运行模式下需要。

## 本地源码运行

后端：

```bash
cd apps/backend
python -m pip install uv==0.9.5
uv sync --frozen --extra dev --extra desktop
cp .env.example .env
# 编辑 .env，替换本地密钥；需要真实模型时再填写对应 LLM Key
uv run alembic upgrade head
uv run python -m app.main
```

本地 `APP_ENV=local` 默认可使用 SQLite；Redis 不可用时降级为单进程内存状态。生产/容器模式要求 PostgreSQL、Redis 和非示例密钥可用。

前端：

```bash
cd apps/frontend
npm ci
npm run dev
```

开发页面默认是 `http://127.0.0.1:5173`，API 默认是 `http://127.0.0.1:8000/api/v1`。更多前端和 Electron 命令见 [前端说明](apps/frontend/README.md)。

## 验证命令

后端命令从 `apps/backend` 执行：

```bash
uv run pytest tests --cov=app --cov-report=term-missing --cov-fail-under=45
uv run python test_document_service.py
uv run python test_optimizations.py
uv run ruff check app tests scripts test_document_service.py test_optimizations.py
uv run python ../../.github/workflows/check_black_baseline.py
uv run mypy app --no-error-summary
uv run alembic check
```

前端和文档：

```bash
cd apps/frontend
npm ci
npm run build
npm audit --audit-level=high

cd ../..
python3 .github/workflows/check_docs.py
```

45% 是当前全仓覆盖率门禁，不代表关键路径已充分覆盖。格式检查必须使用仓库的 hash-locked Black baseline，不应通过全量格式化扩大文档任务范围。

## macOS 私人桌面版

```bash
cd apps/frontend
npm run electron:build:mac:with-backend
```

Electron 将 PyInstaller 后端作为资源打包。本地后端只应监听 `127.0.0.1`；未签名、未公证的构建只适合本机开发验证，不应对外分发。

## Docker（可选）

根目录 Compose 面向私人单机部署：

```bash
cp .env.example .env
# 设置随机数据库密码、JWT/KEK 密钥，并按需填写 LLM Key
docker compose config
docker compose up --build
```

数据库和 Redis 不应暴露到宿主公网。当前进程内会话锁和降级状态不支持直接扩展为多 worker。

## 健康、配置与数据

- `/health`：进程存活；
- `/ready`：数据库和 Redis readiness；本地模式允许 Redis degraded；
- `/health/config`：只暴露私人模式和 LLM 配置状态；
- `/metrics`：Prometheus 文本指标，可通过配置关闭；
- 调试编排 API 默认关闭，通过 `ENABLE_ORCHESTRATOR_DEBUG_API=true` 显式开启；
- Alembic 是服务模式的 schema migration 来源；升级本地历史数据前也应先备份再迁移；
- 仓库没有自动备份/恢复服务，本地数据库、文档目录和 `.env` 需要自行做加密备份。

## 文档规则

文档权威顺序、生命周期和当前处置状态见 [文档中心](docs/README.md) 与 [文档清单](docs/document-inventory.md)。历史 EXEC 和 Release Report 是不可变执行证据；研究稿用于解释设计依据，不是实现接口合同。
