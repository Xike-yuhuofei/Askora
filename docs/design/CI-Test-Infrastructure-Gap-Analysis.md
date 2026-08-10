# Askora CI / Test Infrastructure Gap Analysis

> 状态：Current Gap Analysis  
> 日期：2026-08-10  
> 上位约束：`docs/product/PRODUCT-POSITIONING.md`  
> 目标规范：`docs/specs/quality/ci-infrastructure-standard.md`  
> 质量调和：`docs/specs/quality/v1-local-web-quality-reconciliation.md`

---

## 1. Executive Summary

Askora 当前 CI / Test Infrastructure 的主要问题不是单纯“版本旧”，而是 **历史 SaaS / 多用户 / native desktop / distributed backend 产品假设仍然残留在 Required CI、依赖、测试 oracle 和质量规范中**。

最新产品定位已经冻结 Askora v1 为：

```text
single user
+ Local Web Application
+ Browser → loopback Local Server
+ SQLite + Local Files
+ local background jobs
+ BYOK external AI providers
```

因此 CI 目标必须从：

> 验证历史 Backend 技术栈是否继续兼容

转为：

> 验证当前代码是否仍然实现产品定位定义的 Local-first AI Learning System，并能证明数据正确、学习内核正确、可迁移、可恢复、可追溯和可安全本地运行。

当前结论：**需要 CI v2 系统重构，不建议继续在现有 `ci.yml` 上做零散补丁。**

---

## 2. Current Snapshot

### 2.1 Current Workflow

当前 `.github/workflows/ci.yml` 主要包含：

- documentation；
- backend tests Python 3.11 / 3.12；
- backend quality Python 3.11 / 3.12；
- Alembic migration；
- PostgreSQL persistence contract；
- frontend Vitest + build；
- frontend dependency audit；
- Python dependency audit；
- Docker image build。

当前 Required-like workflow 仍显式配置：

- `REDIS_URL`；
- `JWT_SECRET_KEY`；
- `KEK_MASTER_KEY`；
- PostgreSQL service；
- Docker Buildx。

这不能证明 Product Positioning 要求的 Production Local runtime truth。

### 2.2 Current Branch Governance

`main` 当前未启用有效 Branch Protection / Required Status Check。

结果是：

```text
CI failure
≠
merge blocked
```

因此当前 CI 更接近“报告系统”，而不是“门禁系统”。

### 2.3 Current Runtime / Dependency Residue

`apps/backend/pyproject.toml` 当前仍包含：

- `asyncpg`；
- `redis`；
- `PyJWT`；
- `passlib[bcrypt]`；
- `bcrypt`；
- `aiokafka`；
- 同时已有 `aiosqlite`。

这些依赖不能仅因“存在”就判违规，但必须完成 runtime reachability 分类：

```text
CURRENT_REQUIRED
OPTIONAL_DEV_CI
LEGACY_MIGRATION
UNUSED_DELETE
```

其中 Redis / Auth / PostgreSQL / Kafka 不能继续成为 v1 Production Local 启动条件。

### 2.4 Current Docker Compose

根目录 `docker-compose.yml` 仍描述：

```text
backend
+ PostgreSQL
+ Redis
+ JWT secret
+ KEK secret
```

其 `backend` production environment 仍使用 PostgreSQL + Redis，并将 `HOST=0.0.0.0` 注入容器。

该文件可以保留为开发/兼容工具，但必须明确降级，不能继续表达“Askora v1 production deployment truth”。

### 2.5 Current Frontend Quality

`apps/frontend/package.json` 当前只有：

```text
dev
build
preview
test
```

缺少明确的：

- lint/static quality script；
- Local Server + Chromium E2E；
- supported-browser product smoke。

v1 不需要 Safari / Firefox matrix，但需要真实 Chromium Local Web 路径。

---

## 3. Quality Spec Drift

### 3.1 Testing Standard

有效部分：

- L0～L6 testing layers；
- deterministic unit tests；
- contract-oriented testing；
- SQLite integration；
- replay / migration / recovery；
- OPVE / G0 / G1；
- prompt injection / answer leakage；
- learning outcome 与 engineering correctness 分离。

需要 supersede / rewrite 的部分：

- cross-user service-mode security；
- SQLite/PostgreSQL 双数据库 Required assumption；
- packaged macOS app E2E；
- Desktop model configuration L1～L4 native shell assumption。

### 3.2 Definition of Done

有效部分：

- architecture / ownership / migration / failure / observability；
- real provider claim 不能用 Mock 伪造；
- Engineering / Policy / Learning Evidence 三层 gate；
- `LEARNING_EVIDENCE_INSUFFICIENT` 诚实状态。

需要 supersede：

- `DOD-031` 中 packaged macOS app / desktop relaunch 作为产品 release prerequisite。

### 3.3 Security Standard

有效部分：

- untrusted document / retrieval / model output；
- prompt injection；
- tool allowlist / least privilege；
- grader-only isolation；
- source grounding；
- path traversal / parser resource limit；
- secret/log boundary；
- destructive action confirmation。

需要 supersede：

- service-mode cross-user authorization；
- Electron/macOS `safeStorage` 作为唯一 credential implementation；
- password / access token / refresh token / AuthSession Required runtime clauses；
- account-auth wording。

### 3.4 Observability Standard

大部分仍有效。

需要调整：

- desktop model configuration wording → Local Web model configuration lifecycle；
- `cross-owner` alert → LocalOwner / Workspace / RetrievalScope violation；
- 保证本地 observability 不依赖远程 telemetry backend。

---

## 4. CI Implementation Gap Matrix

| Area | Current | Target | Action | Priority |
|---|---|---|---|---|
| Product boundary | 无独立 gate | 自动验证 Local Web / no-auth / loopback / no external infra | ADD | P0 |
| Main protection | `protected=false` | `Askora CI / Required` 必须成功才能合并 | ADD | P0 |
| Backend runtime | CI 仍注入 Redis/JWT | Production Local 无 Redis/Auth requirement | REWRITE | P0 |
| Persistence | SQLite + Required PostgreSQL contract | SQLite 为 Required truth；Postgres optional | REWRITE | P0 |
| Auth tests | 大量历史 account/JWT/password tests | delete/rewrite/historical classification | REWRITE | P0 |
| Docker build | Required dependency chain尾部 | optional developer/compat validation | DOWNGRADE | P1 |
| Migration | Alembic往返 | fresh + legacy + failure preservation + compatibility | EXPAND | P0 |
| Recovery/rebuild | 分散测试 | 独立 Required Gate | ADD | P0 |
| Chromium E2E | 缺失 | Local Server + Browser E2E | ADD | P0 |
| Real Provider | 历史 E2E 有真实 provider要求 | manual/scheduled/release evidence | SPLIT | P1 |
| Python matrix | Required 全量 3.11/3.12重复 | canonical runtime required + secondary optional | SIMPLIFY | P1 |
| Ruff | 已有 | 保留 | KEEP | P1 |
| Black | hash legacy baseline | 全仓 formatter check，无永久 hash exception | REWRITE | P1 |
| MyPy | 启用但大目录 exclude | 风险模块逐步纳入 | EXPAND | P1 |
| Coverage | fail-under 45 | 不下降 + 关键模块/changed-code导向 | REWRITE | P2 |
| Frontend unit/build | 已有 | 保留 | KEEP | P1 |
| Frontend lint | 无 | 增加静态质量 gate | ADD | P1 |
| Dependency audit | 已有 | 保留并区分 vulnerability vs audit outage | KEEP/REFINE | P1 |
| Dependency updates | 无明确自动化 | Actions/Python/npm update automation | ADD | P2 |
| `develop` trigger | 分支不存在 | 删除无效 trigger | DELETE | P1 |
| Workflow concurrency | 无 | cancel stale runs | ADD | P2 |
| Path-aware execution | 无 | 安全缩短反馈 | ADD | P2 |
| Docs link check | 有价值 | 保留 | KEEP | P1 |
| Docs stale patterns | 硬编码历史阶段文本 | 基于 lifecycle/metadata 的通用治理 | REWRITE | P1 |
| Document inventory | 当前已再次漂移 | 与 Product/ADR/Spec 当前状态同步 | RECONCILE | P0 |
| `dump.rdb` | 当前 main 已不存在 | 保持不跟踪 runtime dumps | CLOSED | — |

---

## 5. Test Oracle Classification

任何现有测试进入 CI v2 前必须先分类。

### KEEP

仍直接证明当前产品 truth，例如：

- Teaching Policy deterministic behavior；
- Assessment integrity；
- Learner State projection；
- Review Scheduling；
- Retrieval scope；
- SQLite repository；
- Content Pipeline；
- replay / DecisionTrace；
- prompt injection / leakage；
- migration / recovery。

### REWRITE

测试意图正确，但产品形态假设过时：

```text
cross-user
→ Workspace / LocalOwner isolation

Desktop credential
→ local secure credential abstraction

PostgreSQL required integration
→ SQLite production-local contract

Auth-protected API
→ loopback no-auth + domain boundary
```

### HISTORICAL

用于证明历史 migration 或解释旧 schema 的测试：

- password / AuthSession migration；
- account deletion historical behavior；
- PostgreSQL compatibility；
- legacy desktop packaged flow。

这些测试不得混入 Required suite。

### DELETE

满足以下全部条件的旧测试 SHOULD 删除：

- 只保护已取消能力；
- 无 migration fixture 价值；
- 无安全审计价值；
- 无 future adapter compatibility价值；
- 会迫使当前实现保留 dead production path。

---

## 6. Runtime Dependency Classification

### 6.1 Must Become Production-local Core

```text
FastAPI / Local Server
SQLite / aiosqlite / SQLAlchemy
Local Files
local indexes
bounded local jobs
HTTP client for external AI
```

### 6.2 Must Be Reviewed for Retirement or Optionalization

```text
asyncpg
redis
PyJWT
passlib
bcrypt
aiokafka
```

不能仅通过“CI 不启动服务”解决；必须检查 production import / configuration / startup / repository / worker path 是否仍真实依赖。

### 6.3 Observability Libraries

`prometheus-client` / OpenTelemetry 的存在本身不违反产品定位，但必须满足：

- Local Server 不依赖远程 collector 才能启动；
- 默认不上传用户学习数据；
- 未配置远程 telemetry 时功能完整；
- 日志/trace 遵守 secret/content minimization。

---

## 7. Target Required CI

```text
Askora CI / Required
│
├── product-boundary
│   ├── no-auth runtime
│   ├── loopback-only
│   ├── no Redis/Postgres/Docker requirement
│   └── architecture/domain invariants
│
├── backend-core
│   ├── ruff / formatter / type
│   ├── unit
│   ├── contract
│   ├── SQLite integration
│   └── deterministic OPVE core
│
├── local-data-integrity
│   ├── fresh SQLite migration
│   ├── legacy SQLite migration
│   ├── failure preservation
│   └── data-dir compatibility
│
├── recovery-rebuild
│   ├── derived data rebuild
│   ├── learner-state recompute
│   ├── interrupted jobs
│   └── idempotency
│
├── local-web-e2e
│   ├── Local Server
│   ├── Chromium
│   ├── isolated AskoraData
│   └── restart persistence
│
└── quality-security
    ├── frontend test/build/lint
    ├── dependency audit
    ├── secret negative tests
    ├── prompt/tool/upload security
    └── Workspace/RetrievalScope isolation
```

---

## 8. Optional / Scheduled Validation

```text
PostgreSQL compatibility
Docker build
secondary Python runtime
real provider smoke
expensive model evals
native desktop historical validation
legacy service-mode compatibility
```

这些失败默认不改变 `Askora CI / Required`。

---

## 9. Recommended Execution Decomposition

### Phase CI-01 — Governance & Oracle Classification

目标：先让所有测试知道自己在保护什么。

- inventory current tests；
- classify KEEP / REWRITE / HISTORICAL / DELETE；
- reconcile document inventory；
- remove stale `develop` branch assumptions；
-建立 stable Required aggregate semantics。

### Phase CI-02 — Production Local Runtime Cutover

- no Redis startup dependency；
- no PostgreSQL production dependency；
- no JWT/Auth production dependency；
- SQLite / Local Files canonical path；
- Docker Compose降级为 developer/compat tool；
- dependency retirement/optionalization。

### Phase CI-03 — Core Required Test Rebuild

- product-boundary tests；
- current architecture contracts；
- SQLite integration；
- stale auth/cross-user tests rewrite/delete；
- deterministic required AI fixtures。

### Phase CI-04 — Migration / Recovery / Rebuild

- SQLite migrations；
- representative legacy fixtures；
- migration failure safety；
- derived rebuild；
- interrupted job recovery；
- learner state recompute。

### Phase CI-05 — Local Web Browser E2E

- Chromium automation；
- isolated AskoraData；
- core Local Web journey；
- Local Server restart；
- persistence / reconnect；
- no real Provider required。

### Phase CI-06 — Workflow / Quality / Supply-chain

- formatter baseline retirement；
- type-check blind spot reduction；
- frontend lint；
- dependency updates；
- concurrency/cancel-in-progress；
- path-aware execution；
- current supported GitHub Actions majors。

### Phase CI-07 — Required Gate & Main Protection Closure

- aggregate `Askora CI / Required`；
- optional workflows separated；
- GitHub Ruleset / Branch Protection；
- prove failing Required status blocks merge；
- final CI v2 release evidence。

---

## 10. Execution Ordering

建议严格按：

```text
CI-01
→ CI-02
→ CI-03
→ CI-04
→ CI-05
→ CI-06
→ CI-07
```

原因：如果先重写 workflow，而 runtime truth / stale tests 尚未清理，新的 workflow 只会重新包装旧错误。

CI-02 与 CI-03 可在同一总计划下局部交错，但不得在 Product Boundary tests 建立前删除大量 legacy tests。

---

## 11. Exit Criteria for Gap Closure

只有同时满足以下条件，CI Infrastructure Gap 才能标记 Closed：

1. Production Local 在无 Redis/PostgreSQL/Docker/Auth 前提下启动并完成核心使用；
2. SQLite 是唯一 v1 Required production persistence truth；
3. stale auth/multi-user/native-desktop/PostgreSQL tests 已全部分类；
4. migration/recovery/rebuild 有 Required automation；
5. Chromium Local Web E2E 存在；
6.真实 Provider 不影响普通 deterministic PR Required status；
7. formatter/type/frontend quality 不依赖永久 legacy exception；
8. `Askora CI / Required` 是稳定聚合 status；
9. `main` 受 Required status 保护；
10.文档/规范/测试/workflow 对 Product Positioning 的解释一致。

---

## 12. Final Assessment

当前 Askora 已拥有较强的领域测试、replay、policy correctness 和 migration 思想基础，因此不需要重建整个质量体系。

真正需要做的是：

> **把质量体系从历史“服务端平台兼容性”重新对准当前“Local Web AI Learning System correctness”。**

最重要的工程动作不是提高 CI job 数量，而是重新定义：

> **什么错误值得阻止代码进入 `main`。**

答案已经由 Product Positioning 冻结：产品边界、数据正确与可恢复、教学决策正确、Local Web 运行真实性和安全边界优先于历史技术兼容。