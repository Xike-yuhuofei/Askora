# Askora

Askora 是一个**私人自用、不公开发布**的苏格拉底式学习 App。当前仓库包含 FastAPI 后端、React/Vite 前端和 macOS Electron 桌面壳；项目不以多租户 SaaS、未成年人平台或公开互联网服务为默认运行场景。

私人使用不等于可以忽略安全：本地数据库、上传文档、LLM 密钥、JWT/加密密钥和备份仍应按敏感数据处理。不要提交 `.env`、数据库、构建产物或桌面后端二进制。

当前代码架构、核心数据流和实现边界见 [`docs/architecture/当前项目架构.md`](docs/architecture/当前项目架构.md)。

## 当前实现

主要数据流：

1. React 前端通过 `/api/v1/auth` 完成注册、登录、刷新和登出。
2. 对话请求进入 `/api/v1/dialog`，由对话服务调用编排器与苏格拉底式引擎。
3. 引擎根据输入、会话历史和知识追踪状态选择策略；配置了 LLM 时调用对应供应商，否则明确返回模拟响应。
4. 用户上传的 Markdown、文本、EPUB、PDF 或 DOCX 保存在本地存储，后台任务完成解析、分块和可选向量化。
5. 桌面版启动内嵌的单文件后端，在用户数据目录创建 SQLite 数据库和文档目录，再加载静态前端。

核心路径位于：

- `apps/backend/app/api/v1`：认证、对话、文档、用户和 WebSocket API。
- `apps/backend/app/services`：认证、对话、文档、模型路由、知识追踪和存储。
- `apps/backend/app/engines`：学习策略与教学引擎。
- `apps/frontend/src`：桌面/Web 共用的页面、状态与 API 客户端。
- `apps/frontend/electron`：macOS 桌面进程和本地后端生命周期。

`assessment`、`dkt`、`knowledge_graph`、`workers`、旧的监护/同意数据模型以及 `gateway` 当前未接入主 API 路径，属于实验性或历史代码。`docs/architecture` 是早期设计资料，不代表当前实现或产品承诺。

## 环境要求

- Python 3.11 或 3.12
- Node.js 20.19+（Vite 8 要求）
- npm
- 可选：Redis 7、PostgreSQL 16、Docker Compose v2.20+
- 构建 macOS 桌面版时需要 Xcode Command Line Tools

## 本地源码运行

后端：

```bash
cd apps/backend
python3.11 -m venv .venv
.venv/bin/pip install -e '.[dev,desktop]'
cp .env.example .env
# 编辑 .env，至少替换 JWT_SECRET_KEY 与 KEK_MASTER_KEY；需要真实对话时填写 LLM Key
.venv/bin/alembic upgrade head
.venv/bin/python -m app.main
```

本地 `APP_ENV=local` 默认可使用 SQLite；Redis 不可用时会降级到单进程内存状态。生产/容器模式要求 PostgreSQL 和 Redis 可用并拒绝示例密钥。

前端：

```bash
cd apps/frontend
npm ci
npm run dev
```

打开 `http://127.0.0.1:5173`。默认 API 为 `http://127.0.0.1:8000/api/v1`。真实登录失败不会进入演示模式；演示入口必须显式选择，且不表示后端成功。

## 验证命令

```bash
cd apps/backend
.venv/bin/ruff check app tests scripts test_document_service.py test_optimizations.py
.venv/bin/black --check app tests scripts test_document_service.py test_optimizations.py
.venv/bin/mypy app --ignore-missing-imports --no-error-summary
.venv/bin/pytest tests --cov=app --cov-report=term-missing --cov-fail-under=45
.venv/bin/python test_document_service.py
.venv/bin/python test_optimizations.py
.venv/bin/alembic check

cd ../frontend
npm ci
npm audit
npm run build
```

45% 是当前全仓基线，不代表核心路径充分覆盖；应优先提高认证 API、WebSocket、文档后台任务与真实数据库集成覆盖率。

## macOS 私人桌面版

```bash
cd apps/frontend
npm run backend:build
npm run electron:build:mac
```

桌面后端构建使用 `apps/backend/.venv` 中已经锁定范围的 PyInstaller。Electron 每次安装会在应用数据目录创建权限为 `0600` 的随机本地密钥；后端只监听 `127.0.0.1`。未签名/未公证的构建只适合本机开发验证，不应对外分发。

## Docker（可选）

根目录 Compose 面向单机私人部署，只把 API 绑定到环回地址，数据库与 Redis 不暴露宿主端口：

```bash
cp .env.example .env
# 设置三个随机密码/密钥，并按需填写 LLM Key
docker compose config
docker compose up --build
```

容器启动时先执行 `alembic upgrade head`，随后使用单个 Uvicorn worker。当前进程内会话锁和降级状态不支持直接扩为多 worker。

## 健康与运维

- `/health`：仅表示进程存活。
- `/ready`：检查数据库与 Redis；本地模式允许 Redis 缺失并报告降级能力，生产模式两者都必须可用。
- `/health/config`：仅暴露私人模式和 LLM 是否配置，不返回密钥或连接信息。
- `/metrics`：Prometheus 文本指标（可通过配置关闭）。
- 本地 SQLite、文档目录和 `.env` 需要自行做加密备份；仓库当前没有自动备份/恢复任务。

## 配置与安全边界

- 配置模板见根目录和 `apps/backend/.env.example`。
- 调试编排 API 默认关闭，只能通过 `ENABLE_ORCHESTRATOR_DEBUG_API=true` 显式开启。
- CORS 和 WebSocket Origin 默认只允许本地开发来源。
- 上传文件按用户隔离、限制类型与大小；不要把文档存储目录放在同步公开目录。
- 如果任何真实 API Key 曾出现在共享日志、提交历史或外发文件中，应到供应商控制台轮换；删除本地文本不能撤销已泄露凭据。

## 迁移和数据

Alembic 是 PostgreSQL/容器部署的结构来源。桌面本地模式为了首次启动会自动建表，但升级已有数据时仍建议备份后执行迁移。数据库迁移位于 `apps/backend/alembic/versions`。

本仓库当前尚无正式提交；所有文件都处于初始工作区阶段。执行修复或审计时应先查看 `git status --short --branch`，不要清理用户文件或自动推送。
