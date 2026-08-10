# Askora

Askora 是一个**面向单用户、长期个人学习的本地运行 AI 学习工具**。Askora v1 的正式产品形态是 **Local Web Application**：浏览器访问运行于用户设备上的 Local Server，核心学习数据默认保存在本机，用户自行配置 AI API Key，并通过互联网调用外部 AI 服务。

Askora v1 仅提供简体中文 Web UI，暂不提供 macOS / Windows 原生客户端，也不提供 iOS / Android；不依赖 Askora 官方中心服务器，不提供官方云同步，不以公网 SaaS、多租户或团队协作为目标。完整产品边界、Non-goals 与 Hard Constraints 见 [PRODUCT-POSITIONING](docs/product/PRODUCT-POSITIONING.md)，该文件是 Canonical Design、ADR、Spec、EXEC 和代码之上的产品级最高约束。

最终用户运行环境不应要求手工安装、启动或维护 Docker、Redis、PostgreSQL 或远程后端等独立基础设施；这些组件可以继续存在于当前开发、测试或历史兼容运行模式，但不得被解释为 Askora v1 的强制产品运行前置条件。

本地使用不等于可以忽略安全。本地数据库、上传资料、LLM 密钥和备份均应按敏感数据处理；不得提交 `.env`、数据库、用户资料或构建产物。Askora 为本地单机个人学习 App，不提供用户账号、注册、登录、用户 session、密码或多用户认证体系；Learner / LocalOwner 是学习数据归属主体，与“认证用户账号”无关。历史实现中残留的账号/JWT/桌面封装等能力属于已/待收敛实现事实，不得反向定义产品定位。

## 当前基线

当前冻结基线是 v0.3 Adaptive Teaching Loop：

```text
Engineering Gate: PASS
Policy Correctness Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

这表示工程链路和教学策略约束通过验收，不表示已经证明真人学习效果。完整证据见 [v0.3 Release Report](docs/releases/v0.3-adaptive-teaching-loop.md)。

所有设计与实现首先必须服从 [PRODUCT-POSITIONING](docs/product/PRODUCT-POSITIONING.md)；实现层随后服从 [Implementation Specs](docs/specs/README.md)。系统边界和单一写入者分别见 [System Architecture](docs/specs/architecture/system-architecture.md) 与 [State Ownership](docs/specs/architecture/state-ownership.md)。

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
- `apps/frontend/src/`：Web 前端；

`assessment`、`dkt`、`knowledge_graph`、`kt` 等 legacy 目录是迁移起点，不因目录存在而自动拥有 canonical 状态或代表功能已接入默认产品路径。

## 环境要求

- Python 3.11 或 3.12；
- `uv 0.9.5`（与 CI 一致）；
- Node.js 22（CI 版本；Vite 8 的最低兼容版本为 Node.js 20.19+）；
- npm。

Redis 7、PostgreSQL 16 和 Docker Compose 仅在相应开发/兼容运行模式下需要，不属于 v1 最终用户强制依赖。

## 本地源码运行

后端：

```bash
cd apps/backend
python -m pip install uv==0.9.5
uv sync --frozen --extra dev
cp .env.example .env
# 编辑 .env，按需填写 LLM Key（BYOK）；未配置时对话返回明确模拟响应
uv run python -m app.main
```

正常 Local Web 启动默认使用 Askora 管理的本地 SQLite（`./data/askora.db`），自动在本地数据目录建表，无需 Docker、PostgreSQL、Redis，也不要求登录/JWT。Alembic 迁移仅在需要升级既有历史数据或运行兼容模式时使用：

```bash
uv run alembic upgrade head
```

Redis 是可选优化：未配置 `REDIS_URL` 或 Redis 不可用时，Askora 仍可正常启动、服务与持久化，任务/状态使用本地 durable 行为。

前端：

```bash
cd apps/frontend
npm ci
npm run dev
```

开发页面默认是 `http://127.0.0.1:5173`，API 默认是 `http://127.0.0.1:8000/api/v1`。更多前端命令见 [前端说明](apps/frontend/README.md)。

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

## Docker（开发/兼容模式，可选）

根目录 Compose 只作为当前开发、测试或兼容运行方式之一，不是 Askora v1 最终用户运行前提：

```bash
cp .env.example .env
# 设置随机数据库密码、KEK 密钥，并按需填写 LLM Key
docker compose config
docker compose up --build
```

数据库和 Redis 不应暴露到宿主公网。当前进程内会话锁和降级状态不支持直接扩展为多 worker。

## 健康、配置与数据

- `/health`：进程存活；
- `/ready`：核心功能就绪（database/SQLite 为 Required；Redis 为可选，不导致 FAIL）；
- `/health/config`：只暴露私人模式和 LLM 配置状态；
- `/metrics`：Prometheus 文本指标，可通过配置关闭；
- 调试编排 API 默认关闭，通过 `ENABLE_ORCHESTRATOR_DEBUG_API=true` 显式开启；
- Alembic 是服务模式的 schema migration 来源；升级本地历史数据前也应先备份再迁移。

## 文档规则

产品级最高约束见 [PRODUCT-POSITIONING](docs/product/PRODUCT-POSITIONING.md)。其下的文档权威顺序、生命周期和当前处置状态见 [文档中心](docs/README.md) 与 [文档清单](docs/document-inventory.md)。历史 EXEC 和 Release Report 是不可变执行证据；研究稿用于解释设计依据，不是实现接口合同。
