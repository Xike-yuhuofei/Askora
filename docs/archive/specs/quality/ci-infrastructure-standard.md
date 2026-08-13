# Askora CI Infrastructure Standard

> Spec ID：`CI-*`  
> 状态：Canonical Implementation Contract  
> 版本：v1 Local Web Baseline  
> 上位约束：`docs/product/PRODUCT-POSITIONING.md`  
> 适用范围：GitHub Actions、Required Status Checks、测试门禁、发布前工程验证、CI 运行依赖治理

---

## 1. Purpose

本规范定义 Askora v1 的 CI 基础设施必须证明什么、哪些失败必须阻断进入 `main`、哪些验证只能作为 Optional / Scheduled / Release Evidence，以及如何防止历史 SaaS / 多用户 /分布式基础设施假设继续成为当前产品真值。

CI 的目标不是证明“所有历史实现仍可运行”，也不是保护所有曾经存在过的技术栈，而是持续验证：

> **Askora v1 作为单用户 Local Web Application，在仅依赖本机 Local Server + SQLite + Local Files + Local Index / Memory + 有界 Background Jobs 的前提下，仍满足数据正确性、学习内核正确性、可恢复性、可解释性与产品边界。**

本规范不直接规定具体 GitHub Actions action major version、runner image 或缓存实现；这些属于可更新执行细节，不得反向改变本规范中的 Gate 语义。

---

## 2. Authority and Supersession

CI 与测试基础设施的约束优先级：

```text
PRODUCT-POSITIONING.md
        ↓
Canonical Design / Accepted ADR
        ↓
CI Infrastructure Standard
        ↓
Testing Standard / Definition of Done
        ↓
Workflow / Scripts / Test Suites
```

若现有 `testing-standard.md`、`definition-of-done.md`、历史 EXEC、测试代码或 workflow 与当前 Product Positioning 冲突：

- MUST 以 `PRODUCT-POSITIONING.md` 为上位真值；
- MUST 将冲突条目标记为 superseded / historical / optional，而不是继续作为 Required Gate；
- MUST NOT 因旧测试仍存在而恢复已经退出 v1 的产品能力；
- MUST NOT 通过隐藏 UI、自动登录、兼容 shim 或测试环境专用基础设施继续维持已被产品定位否定的 runtime truth。

### CI-001 — Known Superseded CI Assumptions

以下内容不得继续作为 Askora v1 Required CI 的产品真值：

- Login / Register / Password / Recovery / AuthSession / JWT 作为业务访问前提；
- Organization / Tenant / RBAC / cross-user service-mode 作为 v1 产品能力；
- PostgreSQL 作为生产持久化合同；
- Redis 作为 production runtime requirement；
- Docker 作为最终用户运行前提；
- packaged macOS native application 作为 v1 release prerequisite；
- Safari / Firefox full compatibility matrix；
- SaaS / LAN / remote-server deployment compatibility；
- Askora 官方中心服务、远程 Feature Flag、远程 Analytics 作为正常运行前提。

历史测试 MAY 保留为迁移证据或历史兼容证据，但 MUST NOT 阻止符合当前 Product Positioning 的实现进入 `main`，除非该测试已被重写为当前 v1 contract。

---

## 3. CI Design Principles

### CI-010 — Product Invariants Before Technology Compatibility

Required CI MUST 优先保护产品不变量，而不是保护某种历史技术栈。

推荐优先级：

```text
Product Boundary
>
Durable Data Integrity
>
Migration / Recovery
>
Learning Core Correctness
>
Local Runtime Correctness
>
Security / Secret Boundary
>
Frontend Local Web Experience
>
Optional Technology Compatibility
```

### CI-011 — Deterministic Required Gate

普通 PR / push Required Gate SHOULD 尽可能 deterministic、可重复、无需真实外部 Provider、无需用户 secret、无需外部长期在线服务。

Required CI MUST NOT 因以下外部条件而天然不稳定：

- 用户 BYOK API Key 不存在；
- OpenAI / Anthropic / Google / compatible provider 临时不可用；
- rate limit；
- 外部模型输出自然语言随机性；
- Docker Registry 或非必要第三方服务不可用。

### CI-012 — Production Local Truth

CI 可以使用容器、PostgreSQL、额外 runner service 或其他开发工具辅助测试，但 MUST 始终存在一条不依赖它们的 Production Local truth path：

```text
Local Server
+ SQLite
+ Local Files
+ Local Index / Memory
+ Local Background Jobs
+ no authentication
+ loopback-only
```

如果只有 Docker/PostgreSQL/Redis 环境能通过，而 Production Local 路径失败，则 Required CI MUST FAIL。

### CI-013 — One Stable Required Status

仓库 SHOULD 对 GitHub branch protection / ruleset 暴露一个稳定聚合状态：

```text
Askora CI / Required
```

内部 job 可拆分、重命名或并行优化，但 aggregate Required Status 的语义必须稳定。

---

## 4. Required Gate Topology

Askora v1 Required CI 至少由以下六类 Gate 组成：

```text
Askora CI / Required
│
├── Product Boundary Gate
├── Backend Core Gate
├── Local Data Integrity Gate
├── Recovery & Rebuild Gate
├── Local Web E2E Gate
└── Quality & Security Gate
```

任一 Required 子 Gate 失败，aggregate gate MUST FAIL。

---

## 5. Product Boundary Gate

### CI-100 — Local Single-user Runtime

必须自动验证至少以下事实：

- Production Local profile 可在无 Login / Register / JWT / AuthSession 条件下访问业务 API；
- 唯一本地身份语义服从 LocalOwner / equivalent canonical local-owner context；
- Workspace 不被建模为 Tenant / Organization；
- Local Server 默认只绑定 loopback；
- 非支持的 remote/LAN bind 不得静默成为默认成功路径；
- 正常业务流不要求 `Authorization` header。

### CI-101 — No External Infrastructure Requirement

必须存在自动化验证：

```text
Redis unavailable
PostgreSQL unavailable
Docker unavailable
Askora cloud unavailable

→ Production Local bootstrap / core usage remains valid
```

若 production-local 配置引用 Redis/PostgreSQL/JWT 等变量，只能作为 legacy optional / ignored compatibility，MUST NOT 成为启动所需 secret 或连接。

### CI-102 — Domain Boundary Invariants

至少验证：

- `Conversation != LearningEvidence`；
- `Chunk != KnowledgeUnit`；
- Learner State 不由 LLM 直接作为 canonical truth 写入；
- Learning Evidence 是 Learner State 推导事实基础；
- Source-grounded claim 可追溯至 Material / Section / Passage 或等价 provenance；
- Retrieval 有 Workspace scope，默认不跨 Workspace 扩大检索；
- AI Provider 失败不得被记录为 learner failure。

### CI-103 — v1 Non-goal Guard

架构 / import / dependency checks SHOULD 防止新的 mandatory runtime dependency 将以下能力偷偷引入 v1：

- Redis / PostgreSQL runtime；
- distributed queue / Kafka；
- mandatory cloud service；
- multi-tenant auth stack；
- remote analytics hard dependency；
- open-ended autonomous agent runtime。

该 Gate 应检查“是否成为运行前提”，而不是禁止开发依赖或实验代码存在。

---

## 6. Backend Core Gate

### CI-200 — Deterministic Core Suites

Required backend core 至少覆盖：

- Architecture tests；
- Domain/unit tests；
- Contract tests；
- SQLite integration tests；
- deterministic policy/eval tests；
- core failure semantics tests。

### CI-201 — Learning Core

至少持续保护以下核心系统可脱离 Browser UI deterministic 测试：

- Teaching Policy；
- Assessment；
- Learner State Update；
- Review Scheduler；
- Retrieval；
- Content Pipeline。

### CI-202 — Policy Correctness

已有 OPVE / G0 / G1 等 deterministic contract 仍然有效的部分继续作为 Required Gate：

- G0 hard constraints = 100%；
- forbidden action = 0；
- deterministic replay；
- no illegal oscillation；
- no infinite policy loop；
- assisted / answer-exposed success 产生正确 validation obligation；
- system/provider failure 不污染 learner evidence。

CI PASS 不得被描述为已证明 human learning efficacy。

### CI-203 — Test Oracle Hygiene

历史测试如果保护已经被 Product Positioning supersede 的行为，必须分类为：

```text
DELETE
REWRITE_TO_CURRENT_CONTRACT
MIGRATION_FIXTURE_ONLY
OPTIONAL_COMPATIBILITY
HISTORICAL_EVIDENCE
```

禁止让 stale test oracle 迫使当前代码继续实现已退出产品范围的能力。

---

## 7. Local Data Integrity Gate

### CI-300 — SQLite as v1 Canonical Structured Store

Required CI MUST 使用真实 SQLite 验证 persistence contract。

至少覆盖：

- foreign keys / constraints；
- transaction boundaries；
- idempotency；
- aggregate / revision concurrency semantics；
- restart persistence；
- workspace isolation；
- durable background-task state。

### CI-301 — Schema Migration

Required CI MUST 覆盖：

```text
fresh database → head
representative old database → head
migration validation
application start after migration
```

不得把“删除数据库后重新创建”当作升级通过。

### CI-302 — Upgrade Safety

至少存在 representative fixture 验证：

```text
pre-upgrade durable data
→ backup/preserve
→ migration
→ validation
→ success
```

以及 migration failure 时 durable source data 不被不可逆破坏。

### CI-303 — Data-directory Compatibility

若实现已具备 `schema_version / minimum_reader_version / minimum_writer_version` 或等价版本元数据，Required CI 必须验证：

- supported data directory 正常打开；
- unsupported newer/incompatible data directory fail closed；
- 不确定兼容时不得直接写入。

---

## 8. Recovery & Rebuild Gate

### CI-400 — Derived Data Rebuildability

Required CI MUST 至少验证代表性派生数据删除后可从 Durable Data 重建：

- chunks；
- retrieval/search index；
- rebuildable embeddings metadata / fixtures；
- cached retrieval；
- derived Learner State / projection；
- knowledge modeling derived outputs where deterministic fixture exists。

目标不是要求重建结果逐字节完全相同，而是 canonical semantics、provenance 与版本边界正确。

### CI-401 — Interrupted Job Recovery

至少验证：

```text
job running
→ process interruption
→ app restart
→ interrupted state detected
→ resume / retry / restart according to contract
→ durable data intact
```

### CI-402 — Idempotent Local Jobs

Import / Parsing / Indexing / Rebuild 等适用任务必须验证：

- duplicate invocation 不重复破坏 durable state；
- same-material conflicting rebuild 有互斥/去重；
- downstream failure 不无条件重复无变化 upstream work。

### CI-403 — Evidence Recompute

删除或 invalidation 某条影响 Learner State 的 Learning Evidence 后，必须重新计算相关派生状态，不得继续保留旧 projection。

---

## 9. Local Web E2E Gate

### CI-500 — Supported Browser Target

v1 Required E2E 以 Chromium 为正式基线；Chrome / Edge 兼容语义 MAY 由同 Chromium engine contract 覆盖。

Safari / Firefox MAY 作为 Optional exploratory validation，但不得成为 v1 Required Gate。

### CI-501 — Local Web Smoke

Required E2E 至少验证：

```text
isolated test AskoraData
→ start Local Server on loopback
→ open Chromium
→ application reachable
→ core local API works without auth token
→ graceful shutdown
```

### CI-502 — Canonical User Journey

至少维护一条不依赖真实外部 AI 的 deterministic E2E：

```text
create/open Workspace
→ import supported local material fixture
→ source copied into Askora-managed data dir
→ material reaches usable state
→ create/start learning context
→ persist durable learning state
→ restart Local Server
→ reopen Chromium
→ durable state still available
```

### CI-503 — Partial Pipeline Availability

内容处理出现允许的部分失败时，E2E / integration MUST 验证已成功阶段仍可按产品合同使用，并允许针对失败阶段重试，而不是默认全部重跑。

---

## 10. Quality & Security Gate

### CI-600 — Static Quality

Required CI SHOULD 包含：

- Python lint；
- formatter check；
- type checking；
- frontend tests；
- frontend production build；
- dependency lock validation。

临时 baseline 文件只允许有明确 retirement condition。历史 EXEC 形成的 hash baseline 不得无限期作为长期架构。

### CI-601 — Coverage

Coverage 是盲区发现工具，不是质量目标本身。

- MUST 防止 coverage threshold 被任意下调来伪造通过；
- SHOULD 以关键模块 / changed-code / architecture risk 为重点逐步提高有效覆盖；
- 单一全仓百分比不得替代 product/domain invariant tests。

### CI-602 — Secret Boundary

必须验证 API Key / secret：

- 不写入默认日志；
- 不进入默认 backup；
- 不进入默认 diagnostics package；
- 不进入 Workspace / Project export；
- 不被 frontend bundle / renderer 暴露。

### CI-603 — Local Security Boundary

至少覆盖：

- loopback bind policy；
- path traversal / unsafe upload；
- archive/path extraction safety where applicable；
- malicious document prompt injection；
- answer/rubric leakage；
- retrieval scope leakage；
- cross-workspace isolation；
- unauthorized / out-of-policy tool or state mutation；
- LLM structured proposal schema validation。

`cross-user service-mode` 不再是 v1 Required security contract；其相关历史测试须重写为 LocalOwner / Workspace boundary 或降级为 historical/optional。

### CI-604 — Dependency Audits

Python / frontend dependency audit SHOULD 继续运行。

若第三方漏洞工具本身出现短时服务/数据库不可用，应区分：

- confirmed critical/high vulnerability；
- audit infrastructure unavailable。

具体 blocking 策略由执行规范实现，但不得静默忽略确认的高风险漏洞。

---

## 11. Real AI Provider Validation

### CI-700 — BYOK Boundary

Askora v1 不提供官方 AI 额度，用户自行配置 Provider/API Key。因此普通 Required CI MUST NOT 要求仓库 secret 中永久维护用户级 AI Key 才能通过。

### CI-701 — Required vs Real-model

模型相关测试分层：

```text
Required PR CI
→ deterministic mocks / fixtures / recorded schema-level samples

Manual / Scheduled / Release Evidence
→ real provider connectivity
→ actual structured output
→ canonical learning turn with configured provider
```

### CI-702 — Real-model Evidence

当任务声明“某 Provider 当前真实可用”时，Mock 不可替代真实调用证据。

但真实 Provider 失败只应阻断对应 provider/release claim，不应把整个代码库的 deterministic Required Gate 变成对外部服务 uptime 的函数。

### CI-703 — No Silent Fallback

真实模型验证必须记录实际 Provider / Model / fallback reason；关键任务发生不可追踪 silent fallback 必须失败。

---

## 12. Optional / Scheduled / Manual Gates

以下内容 MAY 保留，但默认不得成为 Askora v1 `main` Required Status：

### CI-800 — PostgreSQL Compatibility

PostgreSQL 可用于：

- historical migration confidence；
- future-version experiment；
- adapter compatibility research。

PostgreSQL failure MUST NOT 单独阻断 v1 Local Web release，除非未来 Product Positioning 明确把 PostgreSQL 纳入受支持 runtime。

### CI-801 — Docker Build

Docker build MAY 用于开发者便利、CI isolation 或 future deployment experiment。

`Docker build failed` 不等价于 `Askora v1 product failed`。

### CI-802 — Secondary Python Runtime

若项目只声明一个生产 Python runtime，Secondary Python version MAY 作为 scheduled compatibility matrix，而不要求每个 Required job 双版本重复执行。

只有当 Askora 正式声明多个 Python runtime 为 v1 support matrix 时，才升级为 Required。

### CI-803 — Expensive / Real-model Evals

高成本 eval、真实 Provider、多模型对比、长时 sequential simulation MAY 通过 scheduled / workflow_dispatch / release workflow 执行。

### CI-804 — Legacy Compatibility

旧 Auth/Postgres/Redis/desktop-native 等兼容验证若仍有迁移价值，应放在明确标注的 legacy compatibility workflow 中，并定义 retirement condition。

---

## 13. GitHub Workflow Governance

### CI-900 — Branch Targets

Workflow trigger MUST 对齐真实分支治理。

不存在且无治理意义的长期分支（例如历史 `develop`）不得继续作为主要 trigger 造成错误认知。

### CI-901 — Concurrency

PR/push workflow SHOULD 使用 concurrency + cancel-in-progress，避免同一 branch/PR 的过期 CI 占用资源。

### CI-902 — Path-aware Execution

在不破坏 aggregate gate 语义的前提下，SHOULD 对 docs/frontend/backend 等使用 path-aware execution 或可证明安全的 skip strategy，以缩短反馈时间。

被 skip 的 Required 子 Gate 必须以明确的 neutral/success semantics 汇总，不得导致 branch rule 永久 pending。

### CI-903 — Action Runtime Hygiene

GitHub Actions / setup actions / runner runtime 必须使用当前受支持版本。

具体 major version属于 implementation detail；升级时应依据 GitHub 官方当前文档/release，而不是在本 Spec 固定会快速过时的 action major。

### CI-904 — Dependency Update Automation

SHOULD 引入 GitHub-native 或等价 dependency update automation，至少覆盖：

- GitHub Actions；
- Python lock/dependencies；
- npm dependencies。

自动更新 PR 仍必须通过相同 Required Gate，不得自动绕过产品边界。

### CI-905 — Repository Artifacts Hygiene

缓存、数据库 dump、Redis dump、测试运行产物、coverage 输出、local AskoraData 等不得作为普通源码长期跟踪，除非它们是明确版本化的 test fixture。

---

## 14. Aggregate Required Gate

### CI-950 — Required Composition

`Askora CI / Required` 必须至少聚合：

```text
Product Boundary
Backend Core
Local Data Integrity
Recovery & Rebuild
Local Web E2E
Quality & Security
```

### CI-951 — Optional Isolation

以下失败默认不得改变 aggregate Required 状态：

```text
PostgreSQL compatibility
Docker build
secondary runtime matrix
real-provider smoke\expensive model eval
legacy compatibility
```

若未来某项升级为 Required，必须先有上位 Product Positioning / Canonical Design / ADR 依据。

### CI-952 — Main Protection

`main` SHOULD 通过 GitHub Ruleset / Branch Protection 要求 `Askora CI / Required` 成功后才能合并。

CI 文件存在但 `main` 可以绕过失败状态直接合并，不视为完整 CI governance。

---

## 15. Migration from Current CI

当前 CI 重构 MUST 按语义迁移，而不是一次简单重命名 job。

建议顺序：

```text
1. inventory existing jobs/tests
2. classify current tests against Product Positioning
3. create Product Boundary tests
4. establish Production Local SQLite path
5. split Required vs Optional workflows
6. add recovery/rebuild tests
7. add Chromium local-web E2E
8. replace temporary quality baselines
9. create stable aggregate Required status
10. enable main protection
11. retire stale workflows/tests/dependencies
```

在迁移完成前，禁止通过删除大量旧测试并暂时不建立新 contract 的方式制造绿色 CI。

---

## 16. Acceptance Criteria

- `CI-AC-001`：存在稳定 aggregate status `Askora CI / Required`。
- `CI-AC-002`：Production Local path 在无 Redis/PostgreSQL/Docker/Auth 前提下通过。
- `CI-AC-003`：SQLite migration 至少覆盖 fresh + representative legacy fixture。
- `CI-AC-004`：至少一条 derived-data rebuild 自动化测试通过。
- `CI-AC-005`：至少一条 interrupted-job restart recovery 自动化测试通过。
- `CI-AC-006`：至少一条 Chromium + Local Server E2E 通过。
- `CI-AC-007`：Required CI 不依赖真实 AI API Key。
- `CI-AC-008`：真实 Provider validation 被隔离到 manual/scheduled/release evidence 层。
- `CI-AC-009`：stale auth/multi-user/PostgreSQL/Docker tests 已完成 delete/rewrite/optional/historical 分类。
- `CI-AC-010`：API Key / secret leakage tests 覆盖 logs、backup、diagnostics、frontend exposure。
- `CI-AC-011`：Workspace isolation / RetrievalScope contract 有自动化测试。
- `CI-AC-012`：旧 `develop` 等无效 trigger 已清理或有当前分支治理依据。
- `CI-AC-013`：临时 hash/baseline 门禁有 retirement closure，质量门禁不依赖永久 legacy snapshot。
- `CI-AC-014`：`main` 合并受 Required Status Check 保护。
- `CI-AC-015`：Optional compatibility failure 不阻断 v1 Required Gate。

---

## 17. Forbidden Implementations

禁止：

- 为让 CI 变绿而删除/skip/弱化当前有效 product contract test；
- 让 stale legacy test oracle 迫使 v1 恢复已 supersede 的产品能力；
- Required CI 强依赖用户 BYOK secret；
- Required CI 只有 PostgreSQL 路径、没有真实 SQLite Production Local 路径；
- Required CI 只有 Docker 启动路径；
- Redis 不可用时 Production Local 无法启动；
- 把真实 AI provider 临时 outage 当成整个代码库 deterministic engineering failure；
- 把 Mock provider 当成“当前真实 Provider 可用”证据；
- 用 coverage 百分比替代关键领域不变量测试；
- 用 UI smoke 替代 durable data / migration / recovery 验证；
- 让 LLM 直接修改 canonical SQLite state 并靠 E2E 覆盖其风险；
- branch protection 不存在却宣称 Required Gate 已成为 merge gate；
- Docker/PostgreSQL compatibility failure 被描述为 v1 product release blocker，除非上位产品定位已经变更。

---

## 18. Final CI Judgment Standard

Askora CI 的最终判断不是：

> “历史系统的所有组件是否仍然工作？”

而是：

> **“当前代码是否仍然实现 Frozen Product Positioning 所定义的单用户 Local Web AI Learning System，并且其 durable data、学习决策、迁移、恢复、安全边界和浏览器本地运行路径可以被自动验证？”**

当两种 CI 方案冲突时，优先选择：

```text
产品边界正确
>
数据正确与可恢复
>
教学决策可验证
>
本地运行真实性
>
确定性与低脆弱性
>
CI 反馈速度
>
历史技术兼容性
```
