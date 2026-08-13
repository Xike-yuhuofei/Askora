# Askora Testing Standard

> Spec ID：`TEST-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3

## 1. Existing Testing Contracts Retained

### TEST-001 — Contract-oriented Testing

测试目标不只是“代码能跑”，而是验证 Spec 的业务边界、状态所有权、失败语义与学习闭环。

### TEST-002 — Spec Traceability

新增/修改关键行为 MUST 有自动化测试，并在测试名/docstring/marker/邻近注释中引用至少一个 Spec/AC ID。

## 2. L0～L6 Levels

```text
L0 Static / Architecture
L1 Unit
L2 Contract
L3 Integration
L4 End-to-End
L5 Replay / Migration / Recovery
L6 AI Quality / Security Evaluation
```

### TEST-010 — L0

验证 lint、type、import/dependency rules、禁止 cross-owner repository writes 等。

### TEST-011 — L1

纯领域算法/规则使用 deterministic unit tests，不依赖 DB/network/LLM。

### TEST-012 — L2

验证 Command/Event/API/public schema、error code、version compatibility、adapter contract。

### TEST-013 — L3

使用真实 SQLite repository/outbox/worker/orchestration adapter；模型/外部依赖 MAY mock。

### TEST-014 — L4

验证真实教学 vertical loop；至少一个受控 E2E MUST 使用实际配置模型，Mock-only 不算模型接通验收。

### TEST-015 — L5

验证 restart recovery、event/policy replay、migration、projection rebuild、idempotency、late event、invalidated evidence recompute。

### TEST-016 — L6

固定 eval dataset 验证 citation、answer leakage、prompt injection、grader consistency、Teaching Policy、retrieval quality 等。

## 3. Existing Invariants / AI Rules

### TEST-020 — Architecture Invariants

至少自动验证：Assessment 不直接写 mastery；SYS08/LLM 不直接写 mastery/plan/review/action；Planner 不改 ReviewSchedule；SYS02/SYS08 不扩大 TeachingAction support/exposure；replay 不调用在线 LLM；ordinary/streaming 使用同 canonical facade。

### TEST-030 — Mock vs Real Model

Unit/多数 integration 使用 mock/fixture；provider connectivity/真实 structured output/E2E 使用真实模型；eval SHOULD 固定 model snapshot/config。

### TEST-031

不得用真实模型替代 deterministic unit test，也不得用 Mock 宣称真实模型可用。

### TEST-032

AI 输出测试 SHOULD 验证 structure/constraints/grounding，而不是对完整自然语言字符串做脆弱 exact match。

### TEST-040 — Determinism

Event replay、learner projection、review update、fixed planner/policy 在 fixed inputs/version 下 MUST deterministic。

### TEST-041 — Nondeterminism Isolation

模型生成 nondeterminism MUST 隔离在 ModelInference；canonical replay MUST NOT 重新生成历史决策。

### TEST-050 — Fixture Classification

Test fixture MUST 标记 synthetic/public/user-provided-local；CI MUST NOT 依赖私密用户资料。

### TEST-051 — Minimal Curriculum Fixture

关键学习闭环 MUST 维护至少一个 deterministic curriculum fixture：material → KnowledgeUnit → item → responses → evidence → mastery → review；v0.3 SHOULD 再包含 TeachingContext/TeachingAction/DecisionTrace。

### TEST-060 — Existing Failures

若全量 suite 有与本任务无关的历史失败，执行代理 MUST 区分 targeted/new/known failures，不得删除、skip 或弱化测试伪造通过。

## 4. v0.3 OPVE Definition

### TEST-200

`OPVE = Offline Policy Verification & Evaluation`。

它验证 constrained deterministic Teaching Policy 的离线工程/策略正确性，MUST NOT 与 RL 的 causal Offline Policy Evaluation (OPE) 混淆。

### TEST-201 — OPVE Layers

OPVE 至少 MUST 包含：

1. Contract Verification；
2. Scenario Replay；
3. Sequential Transition Replay；
4. Property / Metamorphic Tests；
5. Baseline Differential Replay；
6. Synthetic Learner Stress Test。

## 5. Gold Set Contract

### TEST-210

```text
G0 — Hard Constraint Gold
G1 — Acceptable Action Set Gold
G2 — Research / Calibration Set
```

### TEST-211 — G0 Gate

G0 MUST `100% pass`，且 `forbidden action = 0`。任一 hard-rule forbidden TeachingAction 被选择都是 release blocker。

### TEST-212 — G1 Gate

G1 标准：`selected_action ∈ acceptable_actions`。MUST NOT 要求所有教学案例只有唯一 gold action；同时仍须满足 G0。

### TEST-213 — G2 Boundary

G2 用于研究/calibration/policy comparison；MUST NOT 把未冻结的 G2 preference 伪装为 hard truth。

## 6. OPVE Contract Verification

### TEST-220

至少验证：six StrategyFamily only；four-layer ontology；Productive Failure non-selectable/Socratic bounded move；ErrorType 7+UNKNOWN；TeachingContext exact-version/missing semantics；orthogonal assistance；immutable PolicyBundle；deterministic action propensity semantics；Outcome/Decision separation；single-writer ownership。

## 7. Scenario Replay

### TEST-230

相同 `TeachingContext + exact PolicyBundle + ExperimentAssignment` MUST 产生同一个 semantic TeachingAction 与等价 decision content。Replay MUST NOT 读取当前 mutable state 或调用在线 LLM。

### TEST-231

缺历史 owner version/PolicyBundle/feature source 时 MUST 期望 `PARTIAL|NON_REPLAYABLE` + reason，MUST NOT 用当前状态补成 FULL replay。

## 8. Sequential Transition Replay / Anti-Oscillation

### TEST-240

序列测试 MUST 覆盖 Material Evidence Gate、Sticky Continuity、Minimum Dwell by Evidence Opportunity、Hysteresis、Transition Priority、Repeated Failure Override。

### TEST-241

额外聊天轮、重复 policy call、LLM wording change、wall clock 仅多几秒，单独发生时 MUST NOT 触发 StrategyFamily transition。

### TEST-242

Repeated failure 达到 versioned ceiling 时 MUST 能 exit/escalate/re-diagnose；independent success evidence 应允许 fade；answer/assisted success 必须建立 validation obligation。

## 9. Property / Metamorphic Tests

### TEST-250

至少验证：hard-filtered candidate 永不被 score/experiment 恢复；SYS02/SYS08 only tighten；low confidence 不因伪 default 变激进；`MISSING != 0`；stable tie-break 不受 candidate order 影响；no candidate-set dynamic min-max semantic drift；Outcome 不回写 DecisionTrace；fresh independent Attempt 前 obligation 不自动完成；no infinite policy loop。

## 10. Baseline Differential Replay

### TEST-260

B3 MAY 与 fixed strategy、legacy selector 或 B2 LLM baseline 做 differential replay，但 comparison MUST 使用同 scenario inputs、hard shield、action vocabulary。Behavior difference 是工程/策略证据，MUST NOT 自动称为 learning efficacy。

## 11. Synthetic Learner Stress Test

### TEST-270

Synthetic learner MAY 用于 failure sequence、oscillation、transition、fallback、edge case、performance stress；MUST NOT 被引用为 human learning efficacy、retention、transfer 或 population superiority 证据。

## 12. Offline Evaluation Boundary

### TEST-280

OPVE 可以验证：determinism、constraint compliance、transition correctness、candidate validity、anti-oscillation、no infinite loop、behavior difference。

### TEST-281

OPVE 不能证明：human learning efficacy、retention benefit、transfer benefit、population superiority。

## 13. Migration / Compatibility Tests

### TEST-290

九类 migration candidates MUST 有 fixtures：historical strategy、TeachingAction、scaffold_level、hint_level、old answer exposure、legacy Socratic selector/state machine、old policy config、old DecisionTrace propensity、historical replay。

每类 MUST 验证 canonical target、read compatibility、ambiguity behavior、replayability 与 retirement condition。

### TEST-291

Ambiguous legacy propensity MUST 迁移为 null/unknown + migration reason + PARTIAL，MUST NOT 无条件变成 action propensity。

## 14. Database / Failure / Security Gates

Database tests MUST 覆盖 SQLite FK/constraints、unique aggregate version、transactional outbox、idempotency、concurrency conflict、migration fixture、projection rebuild。

每个外部依赖 MUST 测 timeout/unavailable/invalid response/partial failure/retry exhausted/fallback success/failure，并验证不会错误记录为 learner failure。

Security tests MUST 覆盖 malicious document prompt injection、unauthorized tool call、answer/rubric leakage、citation mismatch、cross-user access（服务模式）、path traversal/unsafe upload、secret leakage/logging、cross-owner write attempt。

Desktop model configuration MUST 分层验证：L1 profile/vault/atomic revision；L2 preload IPC 与稳定错误；L3 local-only probe、candidate no-persist、restart/revision verify、rollback 与 DISABLED tombstone；L4 packaged macOS app 中真实 provider probe、激活、一次 canonical learning turn 与 relaunch 恢复。Mock/fake provider 只能满足 L1～L3，不得替代 L4 当前可用性证据。

## 15. Test Data / Parameter Governance

### TEST-300

Gold/scenario fixtures MUST 固定 schema version、PolicyBundle、owner refs、expected constraints/acceptable actions，并标注 G0/G1/G2；MUST NOT 依赖 production mutable config。

### TEST-301

Threshold/weights/dwell/switch margin 等 MUST 以 fixture/profile version 固定；测试 MUST NOT 把临时值描述为科学常数。

## 16. Acceptance Criteria

原有 AC 保留：

- `TEST-AC-001`：每个系统 Spec 至少有对应 contract/unit test suite。
- `TEST-AC-002`：首个 vertical slice 有真实 SQLite E2E。
- `TEST-AC-003`：至少一个 E2E 使用真实配置模型。
- `TEST-AC-004`：event replay 固定版本 deterministic。
- `TEST-AC-005`：architecture tests 捕获 cross-owner direct write。
- `TEST-AC-006`：restart/outbox recovery 通过。
- `TEST-AC-007`：prompt injection/answer leakage 有固定回归样本。

新增 v0.3 AC：

- `TEST-AC-201`：OPVE 六层均有 test category/fixture entry。
- `TEST-AC-202`：G0 = 100%，forbidden action = 0。
- `TEST-AC-203`：G1 使用 acceptable action set。
- `TEST-AC-204`：deterministic policy replay 不调用在线 LLM。
- `TEST-AC-205`：anti-oscillation 可 sequential replay 验证。
- `TEST-AC-206`：synthetic learner 不作为 learning evidence。
- `TEST-AC-207`：migration ambiguity / partial replay 有 fixture。

## 17. Forbidden Implementations

禁止：happy-path only；Mock-only E2E；为 CI 删除/弱化测试；实时网络内容作为无版本关键 fixture；AI full-string brittle match；provider timeout 被记 learner incorrect；把 OPVE 称 causal RL OPE；synthetic learner 宣称学习效果；G1 强制唯一 gold；online LLM 参与 policy replay；engagement/turn count 替代 learning outcome；Engineering Correct 推导 Learning Effective。

## 18. P1-06 Onboarding Gates

### TEST-320

必须覆盖 strict schema/source/version、四步所有状态、single next action、ambiguous selection、first
completion negative inference、backfill/new-user、SQLite/PostgreSQL migration、preference concurrency/
idempotency/restart、cross-user/cache/leakage、default/deep-link、dismiss/reopen 与 P1-07 action mapping。

### TEST-321

产品 gate 必须同时包含 deterministic browser E2E、真实 provider 的 clean-profile 主路径、App restart
无重复副作用、360/768/1024/1440、200% zoom、keyboard/focus/live region，以及无内部知识首次用户
体验。Mock-only、模型连接成功或单元测试均不能单独关闭 P1-06。

## 19. Course Workspace Selection Gates

### TEST-330

ADR-0023 / `CWSP-*` requires L0 ownership/import tests、L2 strict schema/error/idempotency tests、L3 real SQLite transaction/isolation/projection tests and L5 fresh/legacy/upgraded migration/restart/forward-fix tests。PostgreSQL constraint tests run where the existing optional CI lane is available。

### TEST-331

Browser/E2E acceptance must separately prove Course Empty State、create-and-select、multi-Course switch、every draft/stream/note/session/material-position recovery branch、deep-link/refresh no side effect、Activity resume/start separation、360px/keyboard/focus/console。Static/component tests do not replace live browser evidence。

### TEST-AC-330

fresh SQLite、legacy fixture、cross-Workspace A/B、stale concurrency、same/different idempotency digest、atomic rollback、stable Activity ordering and no-write route refresh all PASS before XIK-189 can close。

---

## Askora CI Infrastructure Standard

> Spec ID：`CI-*`  
> 状态：Canonical Implementation Contract  
> 版本：v1 Local Web Baseline  
> 上位约束：`docs/product/PRODUCT-POSITIONING.md`  
> 适用范围：GitHub Actions、Required Status Checks、测试门禁、发布前工程验证、CI 运行依赖治理

---

### 1. Purpose

本规范定义 Askora v1 的 CI 基础设施必须证明什么、哪些失败必须阻断进入 `main`、哪些验证只能作为 Optional / Scheduled / Release Evidence，以及如何防止历史 SaaS / 多用户 /分布式基础设施假设继续成为当前产品真值。

CI 的目标不是证明“所有历史实现仍可运行”，也不是保护所有曾经存在过的技术栈，而是持续验证：

> **Askora v1 作为单用户 Local Web Application，在仅依赖本机 Local Server + SQLite + Local Files + Local Index / Memory + 有界 Background Jobs 的前提下，仍满足数据正确性、学习内核正确性、可恢复性、可解释性与产品边界。**

本规范不直接规定具体 GitHub Actions action major version、runner image 或缓存实现；这些属于可更新执行细节，不得反向改变本规范中的 Gate 语义。

---

### 2. Authority and Supersession

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

#### CI-001 — Known Superseded CI Assumptions

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

### 3. CI Design Principles

#### CI-010 — Product Invariants Before Technology Compatibility

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

#### CI-011 — Deterministic Required Gate

普通 PR / push Required Gate SHOULD 尽可能 deterministic、可重复、无需真实外部 Provider、无需用户 secret、无需外部长期在线服务。

Required CI MUST NOT 因以下外部条件而天然不稳定：

- 用户 BYOK API Key 不存在；
- OpenAI / Anthropic / Google / compatible provider 临时不可用；
- rate limit；
- 外部模型输出自然语言随机性；
- Docker Registry 或非必要第三方服务不可用。

#### CI-012 — Production Local Truth

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

#### CI-013 — One Stable Required Status

仓库 SHOULD 对 GitHub branch protection / ruleset 暴露一个稳定聚合状态：

```text
Askora CI / Required
```

内部 job 可拆分、重命名或并行优化，但 aggregate Required Status 的语义必须稳定。

---

### 4. Required Gate Topology

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

### 5. Product Boundary Gate

#### CI-100 — Local Single-user Runtime

必须自动验证至少以下事实：

- Production Local profile 可在无 Login / Register / JWT / AuthSession 条件下访问业务 API；
- 唯一本地身份语义服从 LocalOwner / equivalent canonical local-owner context；
- Workspace 不被建模为 Tenant / Organization；
- Local Server 默认只绑定 loopback；
- 非支持的 remote/LAN bind 不得静默成为默认成功路径；
- 正常业务流不要求 `Authorization` header。

#### CI-101 — No External Infrastructure Requirement

必须存在自动化验证：

```text
Redis unavailable
PostgreSQL unavailable
Docker unavailable
Askora cloud unavailable

→ Production Local bootstrap / core usage remains valid
```

若 production-local 配置引用 Redis/PostgreSQL/JWT 等变量，只能作为 legacy optional / ignored compatibility，MUST NOT 成为启动所需 secret 或连接。

#### CI-102 — Domain Boundary Invariants

至少验证：

- `Conversation != LearningEvidence`；
- `Chunk != KnowledgeUnit`；
- Learner State 不由 LLM 直接作为 canonical truth 写入；
- Learning Evidence 是 Learner State 推导事实基础；
- Source-grounded claim 可追溯至 Material / Section / Passage 或等价 provenance；
- Retrieval 有 Workspace scope，默认不跨 Workspace 扩大检索；
- AI Provider 失败不得被记录为 learner failure。

#### CI-103 — v1 Non-goal Guard

架构 / import / dependency checks SHOULD 防止新的 mandatory runtime dependency 将以下能力偷偷引入 v1：

- Redis / PostgreSQL runtime；
- distributed queue / Kafka；
- mandatory cloud service；
- multi-tenant auth stack；
- remote analytics hard dependency；
- open-ended autonomous agent runtime。

该 Gate 应检查“是否成为运行前提”，而不是禁止开发依赖或实验代码存在。

---

### 6. Backend Core Gate

#### CI-200 — Deterministic Core Suites

Required backend core 至少覆盖：

- Architecture tests；
- Domain/unit tests；
- Contract tests；
- SQLite integration tests；
- deterministic policy/eval tests；
- core failure semantics tests。

#### CI-201 — Learning Core

至少持续保护以下核心系统可脱离 Browser UI deterministic 测试：

- Teaching Policy；
- Assessment；
- Learner State Update；
- Review Scheduler；
- Retrieval；
- Content Pipeline。

#### CI-202 — Policy Correctness

已有 OPVE / G0 / G1 等 deterministic contract 仍然有效的部分继续作为 Required Gate：

- G0 hard constraints = 100%；
- forbidden action = 0；
- deterministic replay；
- no illegal oscillation；
- no infinite policy loop；
- assisted / answer-exposed success 产生正确 validation obligation；
- system/provider failure 不污染 learner evidence。

CI PASS 不得被描述为已证明 human learning efficacy。

#### CI-203 — Test Oracle Hygiene

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

### 7. Local Data Integrity Gate

#### CI-300 — SQLite as v1 Canonical Structured Store

Required CI MUST 使用真实 SQLite 验证 persistence contract。

至少覆盖：

- foreign keys / constraints；
- transaction boundaries；
- idempotency；
- aggregate / revision concurrency semantics；
- restart persistence；
- workspace isolation；
- durable background-task state。

#### CI-301 — Schema Migration

Required CI MUST 覆盖：

```text
fresh database → head
representative old database → head
migration validation
application start after migration
```

不得把“删除数据库后重新创建”当作升级通过。

#### CI-302 — Upgrade Safety

至少存在 representative fixture 验证：

```text
pre-upgrade durable data
→ backup/preserve
→ migration
→ validation
→ success
```

以及 migration failure 时 durable source data 不被不可逆破坏。

#### CI-303 — Data-directory Compatibility

若实现已具备 `schema_version / minimum_reader_version / minimum_writer_version` 或等价版本元数据，Required CI 必须验证：

- supported data directory 正常打开；
- unsupported newer/incompatible data directory fail closed；
- 不确定兼容时不得直接写入。

---

### 8. Recovery & Rebuild Gate

#### CI-400 — Derived Data Rebuildability

Required CI MUST 至少验证代表性派生数据删除后可从 Durable Data 重建：

- chunks；
- retrieval/search index；
- rebuildable embeddings metadata / fixtures；
- cached retrieval；
- derived Learner State / projection；
- knowledge modeling derived outputs where deterministic fixture exists。

目标不是要求重建结果逐字节完全相同，而是 canonical semantics、provenance 与版本边界正确。

#### CI-401 — Interrupted Job Recovery

至少验证：

```text
job running
→ process interruption
→ app restart
→ interrupted state detected
→ resume / retry / restart according to contract
→ durable data intact
```

#### CI-402 — Idempotent Local Jobs

Import / Parsing / Indexing / Rebuild 等适用任务必须验证：

- duplicate invocation 不重复破坏 durable state；
- same-material conflicting rebuild 有互斥/去重；
- downstream failure 不无条件重复无变化 upstream work。

#### CI-403 — Evidence Recompute

删除或 invalidation 某条影响 Learner State 的 Learning Evidence 后，必须重新计算相关派生状态，不得继续保留旧 projection。

---

### 9. Local Web E2E Gate

#### CI-500 — Supported Browser Target

v1 Required E2E 以 Chromium 为正式基线；Chrome / Edge 兼容语义 MAY 由同 Chromium engine contract 覆盖。

Safari / Firefox MAY 作为 Optional exploratory validation，但不得成为 v1 Required Gate。

#### CI-501 — Local Web Smoke

Required E2E 至少验证：

```text
isolated test AskoraData
→ start Local Server on loopback
→ open Chromium
→ application reachable
→ core local API works without auth token
→ graceful shutdown
```

#### CI-502 — Canonical User Journey

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

#### CI-503 — Partial Pipeline Availability

内容处理出现允许的部分失败时，E2E / integration MUST 验证已成功阶段仍可按产品合同使用，并允许针对失败阶段重试，而不是默认全部重跑。

---

### 10. Quality & Security Gate

#### CI-600 — Static Quality

Required CI SHOULD 包含：

- Python lint；
- formatter check；
- type checking；
- frontend tests；
- frontend production build；
- dependency lock validation。

临时 baseline 文件只允许有明确 retirement condition。历史 EXEC 形成的 hash baseline 不得无限期作为长期架构。

#### CI-601 — Coverage

Coverage 是盲区发现工具，不是质量目标本身。

- MUST 防止 coverage threshold 被任意下调来伪造通过；
- SHOULD 以关键模块 / changed-code / architecture risk 为重点逐步提高有效覆盖；
- 单一全仓百分比不得替代 product/domain invariant tests。

#### CI-602 — Secret Boundary

必须验证 API Key / secret：

- 不写入默认日志；
- 不进入默认 backup；
- 不进入默认 diagnostics package；
- 不进入 Workspace / Project export；
- 不被 frontend bundle / renderer 暴露。

#### CI-603 — Local Security Boundary

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

#### CI-604 — Dependency Audits

Python / frontend dependency audit SHOULD 继续运行。

若第三方漏洞工具本身出现短时服务/数据库不可用，应区分：

- confirmed critical/high vulnerability；
- audit infrastructure unavailable。

具体 blocking 策略由执行规范实现，但不得静默忽略确认的高风险漏洞。

---

### 11. Real AI Provider Validation

#### CI-700 — BYOK Boundary

Askora v1 不提供官方 AI 额度，用户自行配置 Provider/API Key。因此普通 Required CI MUST NOT 要求仓库 secret 中永久维护用户级 AI Key 才能通过。

#### CI-701 — Required vs Real-model

模型相关测试分层：

```text
Required PR CI
→ deterministic mocks / fixtures / recorded schema-level samples

Manual / Scheduled / Release Evidence
→ real provider connectivity
→ actual structured output
→ canonical learning turn with configured provider
```

#### CI-702 — Real-model Evidence

当任务声明“某 Provider 当前真实可用”时，Mock 不可替代真实调用证据。

但真实 Provider 失败只应阻断对应 provider/release claim，不应把整个代码库的 deterministic Required Gate 变成对外部服务 uptime 的函数。

#### CI-703 — No Silent Fallback

真实模型验证必须记录实际 Provider / Model / fallback reason；关键任务发生不可追踪 silent fallback 必须失败。

---

### 12. Optional / Scheduled / Manual Gates

以下内容 MAY 保留，但默认不得成为 Askora v1 `main` Required Status：

#### CI-800 — PostgreSQL Compatibility

PostgreSQL 可用于：

- historical migration confidence；
- future-version experiment；
- adapter compatibility research。

PostgreSQL failure MUST NOT 单独阻断 v1 Local Web release，除非未来 Product Positioning 明确把 PostgreSQL 纳入受支持 runtime。

#### CI-801 — Docker Build

Docker build MAY 用于开发者便利、CI isolation 或 future deployment experiment。

`Docker build failed` 不等价于 `Askora v1 product failed`。

#### CI-802 — Secondary Python Runtime

若项目只声明一个生产 Python runtime，Secondary Python version MAY 作为 scheduled compatibility matrix，而不要求每个 Required job 双版本重复执行。

只有当 Askora 正式声明多个 Python runtime 为 v1 support matrix 时，才升级为 Required。

#### CI-803 — Expensive / Real-model Evals

高成本 eval、真实 Provider、多模型对比、长时 sequential simulation MAY 通过 scheduled / workflow_dispatch / release workflow 执行。

#### CI-804 — Legacy Compatibility

旧 Auth/Postgres/Redis/desktop-native 等兼容验证若仍有迁移价值，应放在明确标注的 legacy compatibility workflow 中，并定义 retirement condition。

---

### 13. GitHub Workflow Governance

#### CI-900 — Branch Targets

Workflow trigger MUST 对齐真实分支治理。

不存在且无治理意义的长期分支（例如历史 `develop`）不得继续作为主要 trigger 造成错误认知。

#### CI-901 — Concurrency

PR/push workflow SHOULD 使用 concurrency + cancel-in-progress，避免同一 branch/PR 的过期 CI 占用资源。

#### CI-902 — Path-aware Execution

在不破坏 aggregate gate 语义的前提下，SHOULD 对 docs/frontend/backend 等使用 path-aware execution 或可证明安全的 skip strategy，以缩短反馈时间。

被 skip 的 Required 子 Gate 必须以明确的 neutral/success semantics 汇总，不得导致 branch rule 永久 pending。

#### CI-903 — Action Runtime Hygiene

GitHub Actions / setup actions / runner runtime 必须使用当前受支持版本。

具体 major version属于 implementation detail；升级时应依据 GitHub 官方当前文档/release，而不是在本 Spec 固定会快速过时的 action major。

#### CI-904 — Dependency Update Automation

SHOULD 引入 GitHub-native 或等价 dependency update automation，至少覆盖：

- GitHub Actions；
- Python lock/dependencies；
- npm dependencies。

自动更新 PR 仍必须通过相同 Required Gate，不得自动绕过产品边界。

#### CI-905 — Repository Artifacts Hygiene

缓存、数据库 dump、Redis dump、测试运行产物、coverage 输出、local AskoraData 等不得作为普通源码长期跟踪，除非它们是明确版本化的 test fixture。

---

### 14. Aggregate Required Gate

#### CI-950 — Required Composition

`Askora CI / Required` 必须至少聚合：

```text
Product Boundary
Backend Core
Local Data Integrity
Recovery & Rebuild
Local Web E2E
Quality & Security
```

#### CI-951 — Optional Isolation

以下失败默认不得改变 aggregate Required 状态：

```text
PostgreSQL compatibility
Docker build
secondary runtime matrix
real-provider smoke\expensive model eval
legacy compatibility
```

若未来某项升级为 Required，必须先有上位 Product Positioning / Canonical Design / ADR 依据。

#### CI-952 — Main Protection

`main` SHOULD 通过 GitHub Ruleset / Branch Protection 要求 `Askora CI / Required` 成功后才能合并。

CI 文件存在但 `main` 可以绕过失败状态直接合并，不视为完整 CI governance。

---

### 15. Migration from Current CI

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

### 16. Acceptance Criteria

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

### 17. Forbidden Implementations

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

### 18. Final CI Judgment Standard

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

---

## Askora v1 Local Web Quality Reconciliation

> Spec ID：`QUAL-V1-*`  
> 状态：Canonical Superseding Quality Delta  
> 版本：v1 Local Web Baseline  
> 上位约束：`docs/product/PRODUCT-POSITIONING.md`  
> 配套规范：`docs/specs/quality/ci-infrastructure-standard.md`

---

### 1. Purpose

本文件用于消解 Askora 历史 v0.3 / P1 质量规范与当前冻结产品定位之间的冲突。

它不重写已经有效的教学正确性、replay、assessment、security、recovery、observability 合同；只对已经失效的产品形态假设做 supersession。

发生冲突时，权威顺序为：

```text
PRODUCT-POSITIONING.md
        ↓
Accepted current ADR / Canonical Design
        ↓
v1 Local Web Quality Reconciliation
        ↓
CI Infrastructure Standard
        ↓
Testing / Security / Observability / Definition of Done historical clauses
        ↓
Workflow / Tests / Code
```

---

### 2. Global Reconciliation Rules

#### QUAL-V1-001 — Current Product Truth

Askora v1 的质量合同必须以以下产品事实为前提：

- 单用户；
- Local Web Application；
- Browser → loopback Local Server；
- SQLite + Local Files 为核心本地权威存储；
- 无注册、无登录、无账号体系；
- 无 Tenant / Organization / RBAC / 多用户服务模式；
- Docker / Redis / PostgreSQL 不得成为最终用户 runtime requirement；
- BYOK 外部 AI Provider 是不可靠外部依赖；
- Chrome / Edge / Chromium 为 v1 正式浏览器基线；
- macOS / Windows 原生客户端不是 v1 release prerequisite。

#### QUAL-V1-002 — Preserve Learning-core Contracts

以下合同继续有效，不因 Local Web 产品形态变化而弱化：

- Teaching Policy deterministic / explainable；
- Assessment integrity；
- Learning Evidence → Learner State；
- replay / trace / version pinning；
- G0 / G1 policy correctness；
- no forbidden TeachingAction；
- answer / rubric leakage protection；
- prompt injection / tool authorization；
- Derived Data rebuildability；
- migration / restart / recovery / idempotency；
- Source-grounded provenance；
- LLM 不直接成为 Canonical State writer。

#### QUAL-V1-003 — Historical Test Oracle Must Not Restore Removed Product Features

历史测试仍然可以作为迁移证据或历史回归样本，但如果其预期行为要求恢复以下能力，则不得继续作为 v1 Required truth：

```text
Login / Register
Password lifecycle
AuthSession / JWT
Account recovery
multi-user / cross-user service mode
PostgreSQL production persistence
Redis production runtime
packaged native macOS application
Electron-only credential semantics
```

---

### 3. Testing Standard Reconciliation

#### QUAL-V1-100 — Retained Testing Layers

`testing-standard.md` 的 L0～L6 分层继续有效：

```text
L0 Static / Architecture
L1 Unit
L2 Contract
L3 Integration
L4 End-to-End
L5 Replay / Migration / Recovery
L6 AI Quality / Security Evaluation
```

其中 L3 Required persistence baseline 必须以真实 SQLite 为主；PostgreSQL 只能作为 Optional compatibility，除非未来产品定位重新纳入。

#### QUAL-V1-101 — Current Required Integration Truth

Required integration tests SHOULD 优先使用：

```text
isolated AskoraData
+ SQLite
+ Local Files
+ local background jobs
+ deterministic model fixtures
```

不得要求 Redis / PostgreSQL / Docker 才能建立有效 integration environment。

#### QUAL-V1-102 — Browser E2E

v1 Required L4 的产品级入口改为：

```text
Chromium
→ 127.0.0.1:<port>
→ Askora Local Server
→ SQLite / Local Files
```

历史 packaged macOS / Electron E2E 只能作为 historical/optional evidence，不得继续作为 v1 Required release prerequisite。

#### QUAL-V1-103 — Real Model Evidence

保留“Mock 不得伪装真实 Provider 当前可用”的原则。

但普通 PR Required CI 不要求真实 BYOK Key。真实 Provider connectivity、actual structured output、configured-model canonical learning turn 应放在：

- manual validation；
- scheduled provider smoke；
- release evidence；
- 明确声称 Provider 当前可用的任务验收。

#### QUAL-V1-104 — Cross-user Tests

历史 `cross-user` / service-mode authorization tests 的 Required 语义被 supersede。

当前必须重写为适用的边界测试：

- LocalOwnerContext 唯一 owner；
- Workspace isolation；
- RetrievalScope isolation；
- 禁止跨 Workspace 非授权批量状态修改；
- legacy owner migration fail-closed。

#### QUAL-V1-105 — Database Compatibility

历史 SQLite/PostgreSQL 双数据库 Required matrix 被 supersede。

当前 Required：

- fresh SQLite → head；
- representative legacy SQLite → head；
- migration failure preserves durable data；
- schema/minimum reader/writer compatibility；
- rebuild / restart recovery。

PostgreSQL migration/adapter verification MAY 保留在 Optional workflow。

#### QUAL-V1-106 — Desktop Model Configuration Tests

历史 `Desktop model configuration L1～L4` 中与模型安全和原子配置相关的意图继续有效，但 native desktop-specific transport/packaging 要求被 supersede。

当前应验证：

- API Key 由本机安全凭据抽象保存；
- frontend 永不获得 secret；
- provider probe 使用最小 synthetic payload；
- candidate config 不在验证前错误成为 active truth；
- activation / rollback / clear / revision 可验证；
- Local Server restart 后配置状态正确恢复；
- 真实 Provider evidence 与 deterministic Required CI 分离。

---

### 4. Definition of Done Reconciliation

#### QUAL-V1-200 — Retained DoD

`DOD-001`～`DOD-030`、Engineering Gate、Policy Correctness Gate、Learning Evidence Gate 的核心语义继续有效。

Engineering Correct 仍不得被描述为 Learning Effective。

#### QUAL-V1-201 — DOD-031 Supersession

历史 `DOD-031 Desktop Model Settings Closure` 中以下要求不再是 v1 产品 DoD：

- packaged macOS app；
- Electron renderer/main IPC 作为唯一验收路径；
- macOS relaunch 作为 v1 release prerequisite。

当前对应 closure 改为：

```text
Local Web Settings
→ local credential storage abstraction
→ provider probe
→ atomic activation / rollback
→ Local Server restart
→ browser reconnect
→ configured state preserved
```

若声明某真实 Provider 当前可用，仍必须提供当前真实 Provider 证据。

#### QUAL-V1-202 — Product DoD

任何功能声称 v1 Engineering DONE 时，不得新增以下隐式运行前提：

- Docker daemon；
- Redis server；
- PostgreSQL server；
- Askora cloud；
- Authentication service；
- native desktop shell。

---

### 5. Security Standard Reconciliation

#### QUAL-V1-300 — Current Authorization Boundary

`security-standard.md` 中“服务模式 cross-user authorization”不再是 v1 产品合同。

当前安全边界为：

```text
loopback process boundary
+ LocalOwnerContext
+ Workspace / object scope
+ typed domain authorization
+ explicit destructive-operation confirmation
```

单用户不等于无安全边界；路径、Workspace、工具、LLM 写入权限、secret 与 destructive action 仍必须 fail closed。

#### QUAL-V1-301 — Desktop Credential Clause Supersession

历史 `SEC-071 Desktop Model Credential` 的安全意图保留，但 Electron/macOS `safeStorage` 不是 v1 唯一 canonical implementation。

当前 canonical contract：

- secret 仅在本机保存；
-优先使用操作系统安全凭据存储；
- browser/frontend 不接触明文 API Key；
- secret 不进入日志、backup、diagnostics、export、Prompt；
- credential backend 必须可替换，不能绑定 native desktop UI 架构。

#### QUAL-V1-302 — Historical Auth Security

`SEC-300`～`SEC-303` 中 password/access token/refresh token/AuthSession/account recovery 等认证合同对 v1 runtime 已 superseded。

它们 MAY 保留为 historical migration / deletion evidence，但不得：

- 成为 Required test oracle；
- 迫使 runtime 继续保留 JWT/password/session tables 或 write path；
- 通过 hidden login / auto-login 继续存在。

#### QUAL-V1-303 — Erasure Semantics

历史 `current-user` / account deletion wording 应重解释为当前 LocalOwner 数据控制语义。

删除仍必须满足：

- impact preview；
- explicit confirmation；
- idempotency；
- canonical durable data scope；
- derived data cleanup/rebuild semantics；
- backup/restore resurrection protection where applicable。

---

### 6. Observability Standard Reconciliation

#### QUAL-V1-400 — Local Observability First

保留 DecisionTrace / OutcomeObservation / ModelInference / retrieval / job / recovery observability。

v1 默认目标是本地诊断，不要求远程 telemetry backend。

Logs / traces / metrics 不得成为业务事实源。

#### QUAL-V1-401 — Model Configuration Observability

历史 desktop-specific model configuration observability 应重解释为 Local Web model configuration lifecycle：

```text
candidate
→ probe
→ activate / reject
→ revision
→ rollback / clear
→ Local Server restart verification
```

记录 provider/model/revision/outcome/latency/stable error code；不得记录 credential、完整 Prompt 或原始敏感 provider body。

#### QUAL-V1-402 — Ownership Alerts

历史 `cross-owner write violation` 应在 v1 Required Gate 中解释为：

- invalid LocalOwner mutation；
- cross-Workspace scope violation；
- retrieval scope leakage；
- canonical owner bypass。

---

### 7. CI Classification Contract

#### QUAL-V1-500 — Required

以下属于 v1 Required quality truth：

- Product Boundary；
- backend architecture / unit / contract / SQLite integration；
- Teaching Policy / Assessment / Learner State correctness；
- migration / restart / recovery / rebuild；
- Local Web Chromium E2E；
- static quality；
- secret/data boundary；
- Workspace / RetrievalScope isolation。

#### QUAL-V1-501 — Optional / Manual / Scheduled

以下默认不作为 `Askora CI / Required`：

- PostgreSQL compatibility；
- Docker image build；
- Redis legacy adapter tests；
- secondary Python compatibility；
- real-provider uptime smoke；
- expensive multi-model eval；
- native desktop historical validation；
- service-mode multi-user tests。

#### QUAL-V1-502 — Delete vs Historical

没有未来迁移、审计或兼容价值的 stale tests SHOULD 删除。

仍有价值的旧测试必须明确：

```text
HISTORICAL
or
OPTIONAL_COMPATIBILITY
```

禁止让未分类 legacy tests 混在 Required suite 中。

---

### 8. Acceptance Criteria

- `QUAL-V1-AC-001`：Testing / Security / Observability / DoD 的当前解释不再要求 native desktop、multi-user、Auth、PostgreSQL production 或 Redis production。
- `QUAL-V1-AC-002`：历史教学内核 deterministic / replay / policy / assessment / evidence contracts 未被弱化。
- `QUAL-V1-AC-003`：Required integration baseline 明确为 SQLite Production Local。
- `QUAL-V1-AC-004`：Required E2E 明确为 Chromium + loopback Local Server。
- `QUAL-V1-AC-005`：真实 Provider evidence 与普通 deterministic PR CI 分离。
- `QUAL-V1-AC-006`：cross-user tests 已重写为 LocalOwner / Workspace / RetrievalScope 边界，或降级为 historical。
- `QUAL-V1-AC-007`：password/JWT/AuthSession security clauses 不再成为 v1 Required runtime truth。
- `QUAL-V1-AC-008`：credential security 不绑定 Electron/macOS implementation。
- `QUAL-V1-AC-009`：PostgreSQL/Docker compatibility failure 默认不阻断 v1 Required Gate。

---

### 9. Forbidden Interpretations

禁止：

- 因旧测试仍存在而恢复 Login/JWT/AuthSession；
- 因旧 DOD 写有 packaged macOS app 而把原生客户端重新纳入 v1；
- 因旧 security 文档写有 cross-user 而建立多租户授权层；
- 因 PostgreSQL contract test 存在而将其重新变成 production persistence；
- 因 Electron `safeStorage` 历史实现存在而让浏览器依赖 Electron；
- 删除 Teaching Policy / Assessment / Evidence / replay 等仍有效核心测试来“简化”CI；
- 把真实 Provider outage 解释为 deterministic product logic failure。

---

### 10. Final Rule

质量基础设施只保护**当前产品真值**和**仍有效的学习系统合同**。

历史技术栈、历史客户端形态和历史账号系统可以保留为证据，但不得继续拥有 v1 release veto 权。

---

## Askora Observability Standard

> Spec ID：`OBS-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3

### 1. Existing Observability Contracts Retained

#### OBS-001 — End-to-end Traceability

任何关键学习结果 MUST 能从用户请求追踪到领域决策、retrieval/model/tool execution、AssessmentResult、LearnerEvidence/state update，并在 v0.3 有 OutcomeObservation 时继续关联 outcome/experiment refs。

#### OBS-002 — Observability Is Not Truth

Logs、metrics、traces 是观测/审计投影，MUST NOT 成为业务事实源。

#### OBS-010 — Process Metrics Are Not Primary Learning Outcomes

聊天时长、token 数、点赞只能作为体验/成本/process metrics，MUST NOT 作为主要 learning outcome/reward。v0.3 同样适用于 conversation turns、hint count、session duration 与 engagement。

### 2. Correlation / Logging Baseline

每个教学 round SHOULD 传播 request_id、correlation_id、trace_id、session_id、workflow_run_id；关键 domain object/DecisionTrace/Event/Outcome SHOULD 可关联。

Structured logs 至少 SHOULD 包含 timestamp、level、component/system、event/error code、trace/correlation、object ids/versions。MUST NOT 默认记录 password、token、API key、完整敏感文档或完整 privacy-sensitive Prompt。

DecisionTrace 按 `decision-contract.md`；ModelInference 至少记录 provider/model/snapshot、task、prompt version、latency、usage、fallback、validation、error；retrieval observability 必须包含 candidates/routes/ranks/filters/selected evidence/index versions/citation validation/leakage reason。

Model configuration 事件只可记录 schema/source/revision、sanitized provider/model、probe/apply/rollback outcome、latency 与稳定 error code。MUST NOT 记录 credential、ciphertext、control token、完整 synthetic prompt 或原始 provider body。

### 3. v0.3 Decision vs Outcome

#### OBS-200

`DecisionTrace = decision-time reasoning`；`OutcomeObservation = later measurement`。Outcome MUST NOT 回写历史 DecisionTrace。

#### OBS-201 — Attribution

Delayed outcome MUST NOT 自动 last-touch attribution 给最后一个 TeachingAction。Attribution scope 仅允许：

```text
ACTION_DIRECT
EPISODE_ASSOCIATED
TRAJECTORY_ASSOCIATED
EXPERIMENTALLY_CAUSAL
UNATTRIBUTABLE
```

只有满足实验识别条件时 MAY 使用 `EXPERIMENTALLY_CAUSAL`。

### 4. Outcome Hierarchy

#### OBS-210 — Primary Learning Outcomes

v0.3 primary learning outcomes：

```text
no-hint independent success
delayed independent performance
independent transfer
unit-time capability gain
```

实现 MUST 能从 actual assistance/exposure、delay、transfer novelty、measurement refs 与 active learning time 计算/聚合，而不是从聊天表象推断。

#### OBS-211 — Secondary Learning Outcomes

Secondary MAY 包含 near-transfer/explanation quality、不同 capability dimension improvement、independent success stability、misconception recurrence/decay 等；必须固定 measurement definition/version。

#### OBS-212 — Process Diagnostics

Engagement、conversation turns、likes、hint count、token count、session duration、candidate distribution、transition rate、latency/cost、retrieval metrics 均属于 process/experience diagnostics；MUST NOT 标记为 primary learning outcome/reward。

#### OBS-213 — Safety / Trust Guardrails

至少 SHOULD 观测 forbidden-action rate、answer leakage、assessment integrity violation、hard-rule conflict、policy bypass attempt、prompt-injection/tool-authorization failure、trace persistence failure、replayability 与 learning-harm indicators。

### 5. OutcomeObservation Contract

#### OBS-220

OutcomeObservation 至少 MUST 支持：

```text
outcome_type
measurement_reference
independence
assistance_state
scaffold_control
hint_specificity
answer_exposure
actual_delay
transfer_distance / novelty
score / success
measurement_confidence
active_learning_time
time_cost
hint_cost
contamination_status
attribution_scope
teaching_episode_ref
learning_trajectory_ref
experiment_association
```

#### OBS-221 — Missing / Confidence

Measurement confidence、contamination、missing status MUST 与 observation 一起保存；`MISSING` MUST NOT 伪装成 0。

### 6. Teaching Policy Observability

#### OBS-230

每个 SYS05 decision SHOULD 记录 context fingerprint/exact source versions、PolicyBundle ref/hash、TeachingStage、available/filtered candidates + reasons、feature value/availability/confidence/version、scores、material evidence、anti-oscillation、tie-break、selected/previous action、validation obligation、ExperimentAssignment 与 replayability。

#### OBS-231 — Probability Observability

B3 MUST 可审计：

```text
behavior_policy_type = DETERMINISTIC
action_propensity = null
```

ExperimentAssignment `assignment_probability` MUST 独立观测，MUST NOT 复用 action propensity 名义。

### 7. TeachingEpisode / LearningTrajectory

#### OBS-240

TeachingEpisode/Trajectory MAY 聚合跨 action outcomes，但只是 grouping/analytics refs，不是新 TeachingAction/LearnerState owner。

#### OBS-241

Trajectory association MUST 保留 attribution uncertainty。时间上最近的 action MUST NOT 自动获得 causal attribution。

### 8. Engineering / AI / Learning Observability

系统指标 SHOULD 包括 availability、p95 latency、error/fallback、queue/outbox lag、restart recovery、cache/index health、persistence conflict；AI 指标包括 model/tool failure、schema fail、citation unsupported、answer leakage、tool denial、cost。

学习 observability SHOULD 包括 Attempt actual assistance、AssessmentResult/diagnosis confidence、EvidenceAccepted/Rejected、Mastery prior/new version、Review prior/new schedule、Plan/TeachingAction reasons 与 primary/secondary OutcomeObservation。

### 9. Privacy / Health

Telemetry MUST 按 privacy classification 最小化采集；raw content 非必要时优先 hash/reference/reason code。Health 至少区分 liveness、DB readiness、durable queue/outbox、configured model availability（可 degraded）、index freshness。

### 10. Alerts

#### OBS-250

至少 SHOULD 对 forbidden action > 0、assessment leakage、hard-rule bypass、trace persistence failure、outbox backlog、deterministic non-null action_propensity、illegal oscillation/no-progress loop、cross-owner write violation 建 alert/release guard。

### 11. Tests

测试 MUST 覆盖 DecisionTrace/Outcome separation；primary vs process metric classification；delayed outcome no last-touch；attribution enum；actual assistance/exposure observability；deterministic probability fields；trace correlation；missing semantics；privacy redaction；model configuration probe/apply/rollback 脱敏事件与 secret-negative assertions。

### 12. Acceptance Criteria

原有 AC 保留：

- `OBS-AC-001`：任一 TeachingAction 可通过 trace 找到执行模型与最终 response。
- `OBS-AC-002`：任一 MasteryEstimate 可找到 source AssessmentResult/LearnerEvidence。
- `OBS-AC-003`：fallback/repair 可区分并可统计。
- `OBS-AC-004`：日志扫描不包含测试 secret/token。
- `OBS-AC-005`：queue/outbox lag/failure 可观测。

新增 v0.3 AC：

- `OBS-AC-201`：四类 primary learning outcome 可从审计 measurement/event refs 计算。
- `OBS-AC-202`：process metrics 不进入 primary learning outcome/reward。
- `OBS-AC-203`：OutcomeObservation 不修改 DecisionTrace。
- `OBS-AC-204`：delayed outcome 不自动 last-touch attribution。
- `OBS-AC-205`：deterministic B3 可检测任何 non-null `action_propensity` 异常。
- `OBS-AC-206`：SYS05 decision 可关联 exact context/bundle 与后续 outcome，而不混淆 ownership。
- `OBS-AC-207`：可审计 desktop model configuration revision/apply/rollback，且日志/trace 不含 secret/ciphertext/control token。

### 13. Forbidden Implementations

禁止：只有自由文本日志无 stable code；默认记录完整敏感 Prompt；无 trace 的模型调用；只统计 engagement 不统计学习/可信指标；engagement/turns/likes/hint/token/session 作为主要 learning outcome/reward；delayed outcome 自动归因最后 action；analytics grouping 取得 domain ownership；Outcome 回写 DecisionTrace；deterministic action_propensity=1.0；Engineering Correct 指标替代 learning efficacy。

---

## Askora Definition of Done

> Spec ID：`DOD-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3 + Product Definition Traceability  
> 上游产品定义：`docs/product/PRODUCT-DEFINITION.md`

### 0. Acceptance Ownership

Askora 的 DONE / PASS 必须区分：

```text
Product Acceptance
UX Acceptance
Technical / Engineering Acceptance
Quality Acceptance
Learning Evidence
```

这些层级可以相互提供证据，但不能互相替代。

#### DOD-000 — Product Traceability

任何**面向产品行为**的新建或实质重构 Design / ADR / Spec / Vertical Slice / EXEC / Linear Issue，MUST 明确引用适用的：

- `CAP-*`；
- `PD-REQ-*`；
- `PD-RULE-*` / `PD-NFR-*`（适用时）；
- 已存在的 `PD-AC-*`（适用时）。

纯 infrastructure / internal maintenance 工作 MAY 标记 `Product Traceability: N/A — infrastructure-only`，但必须说明为什么不会改变 Product Capability、v1 Feature Scope、Product Rule 或 Product Acceptance。

技术 AC、Vertical Slice AC、UI AC 不得自行升级为新的 `PD-AC-*`。若产品层定义缺失，报告 `PRODUCT DEFINITION GAP`。

### 1. Existing Completion Contracts Retained

#### DOD-001 — Scope

实现任务只有在以下条件满足时 MAY 报 DONE：

- 对应 Spec/EXEC Acceptance Criteria 满足；
- 修改范围合规；
- 无未声明公共 API/Schema/DB semantic change；
- 产品面向任务已引用适用 `CAP-* / PD-REQ-*`，且没有用技术 PASS 冒充 Product Acceptance；
- 若 Issue 声称“该产品能力/Feature 已完成”，则适用 Product Acceptance 必须有明确证据或在上游明确标注未完成。

Infrastructure-only 任务可以 Engineering DONE，但不得据此声称上游 Product Capability 已完整交付。

#### DOD-002 — Architecture

MUST 遵守 `ARCH-*`、`DEP-*`、`STATE-*`；不得新增第二 truth、绕过 canonical orchestration/policy path，legacy adapter 必须有迁移目的/retirement condition。

#### DOD-003 — Data

新状态必须有 owner；关键更新可追溯 event/evidence/decision；idempotency/concurrency/version/migration 语义明确；需要恢复的 durable task/outbox 有效。

#### DOD-004 — AI

Model/Prompt/schema/version 可追踪；fallback MUST NOT 改领域语义；prompt injection / exposure leakage / tool authorization guard 不得绕过；Mock MUST NOT 当真实模型连接证据。

#### DOD-005 — Tests

新增关键行为有自动化测试；targeted/applicable suites 已运行；lint/type/build 按范围执行；不得 skip/delete/weaken tests 伪造通过。

#### DOD-006 — Failure

Timeout、invalid input、dependency failure、retry exhausted 等适用失败路径必须定义/测试；系统故障 MUST NOT 记录为 learner error；side-effect retry 必须 idempotent。

#### DOD-007 — Observability

新关键 decision/event/model call 有 trace；新 error 使用稳定 code；logs 不泄漏 secret/不必要敏感内容。

#### DOD-008 — Product / Design / SPEC GAP

若实现需要改变已冻结的 Product Capability、v1 Feature Scope、Product Rule、Product Requirement 或 Product Acceptance，执行代理 MUST 先报告 `PRODUCT DEFINITION GAP`，不得在 Design / Spec / code 中自行决定。

若 Product Definition 已明确，但实现需要改变已冻结 Design / ADR / Spec 公共行为，则报告对应 `DESIGN GAP` / `SPEC GAP`。已获用户架构自治委托时，MUST 先在正确 authority 层完成变更并冻结，再继续修改代码；未获委托时 MUST 停止并等待决定。

任何情况下都 MUST NOT 先改代码后补 Product Definition / ADR / Spec。

#### DOD-020 — PARTIAL / BLOCKED

若大部分工作完成但存在无法在当前 Product Definition / Design / Spec 安全实现的缺口，必须标 `PARTIAL`、`BLOCKED_BY_PRODUCT_DEFINITION_GAP` 或 `BLOCKED_BY_SPEC_GAP`，MUST NOT 称 DONE。

#### DOD-030 — Real Model E2E

涉及 LLM gateway/orchestrator“已接通”的任务，至少一次真实已配置模型调用成功才可满足对应 AC；普通 unit/integration 仍应主要使用 Mock/fixture。

#### DOD-031 — Desktop Model Settings Closure

桌面模型设置只有在 OS-protected save、synthetic probe、runtime revision verification、apply rollback、clear tombstone、renderer secret isolation 与 relaunch recovery 均通过自动化测试后才可报 Engineering DONE。若声称当前真实 provider 可用，还必须在 packaged macOS app 中重新完成 provider probe、激活、canonical learning turn 与重启恢复；历史成功记录不能替代当前证据。

该条款仅保留历史/兼容工程语义；不得据此把 Desktop 重新解释为当前 v1 Product Scope。

### 2. Migration Done Baseline

Database/state migration 只有在 migration 可执行、representative fixture backfill 正确、owner truth 明确、reconciliation test 通过、legacy write path 关闭或有关闭条件、rollback/forward-fix 明确时才算完成。

Migration DONE 只说明迁移合同完成，不自动证明用户可观察 Product Acceptance 已成立。

### 3. v0.3 Release Gate — Engineering

#### DOD-200

Engineering Gate 至少 MUST 验证：

```text
deterministic replay
immutable TeachingAction
TeachingContext / PolicyBundle exact version pinning
DecisionTrace completeness
no policy bypass
assessment integrity
explicit failure semantics
state ownership / no duplicate truth
schema/config versioning
persistence / idempotency / recovery
SYS02/SYS08 tightening-only
```

#### DOD-201

Engineering Gate PASS 只意味着系统按合同可靠执行；MUST NOT 宣称 Product Acceptance、adaptive learning outcome 或 human efficacy 已由此成立。

### 4. v0.3 Release Gate — Policy Correctness

#### DOD-210

Policy Correctness Gate 至少 MUST 满足：

```text
G0 = 100%
forbidden action = 0
G1 selected_action ∈ acceptable_actions
repeated failure exits/escalates/re-diagnoses
independent success can fade support
answer exposure → independent validation obligation
assisted success → independent validation obligation
low confidence → conservative behavior
no illegal oscillation
no infinite policy loop
deterministic tie-break
action_propensity = null for B3
```

#### DOD-211

任何 hard-rule violation、forbidden action、policy bypass、random tie-break 或无法解释的 illegal oscillation MUST 阻断 Policy Correctness Gate。

#### DOD-212

G1 MAY 有多个 acceptable actions；MUST NOT 为方便测试强制所有教学情境唯一 gold action。

### 5. v0.3 Release Gate — Learning Evidence

#### DOD-220

Learning Evidence Gate canonical condition：

```text
Engineering Correct
+
Policy Correct
+
No Learning Harm
+
Directional Individual Learning Evidence
+
Correct Experimental Data Foundation
```

#### DOD-221 — Primary Outcomes

学习证据 SHOULD 以 no-hint independent success、delayed independent performance、independent transfer、unit-time capability gain 为 primary outcomes。Engagement、conversation turns、likes、hint count、token count、session duration MUST NOT 作为 primary learning outcome/reward。

#### DOD-222 — Insufficient Evidence

Engineering/Policy gates 已通过但真实学习证据不足时，status MUST 为：

```text
LEARNING_EVIDENCE_INSUFFICIENT
```

该状态不是 engineering failure，也 MUST NOT 改写成“已证明有效”。

#### DOD-223 — No Learning Harm

Practical harm margin/criteria MUST versioned/traceable，并基于真实 OutcomeObservation/experiment design；具体值是 configurable/experimental parameter，MUST NOT 伪装成学习科学常数。

#### DOD-224 — Experimental Data Foundation

至少要求 ExperimentAssignment、assignment probability、TeachingContext/PolicyBundle/action refs、actual assistance/exposure、OutcomeObservation、attribution/contamination、active learning time 与 replayability 可支持后续分析。Assignment probability MUST NOT 与 action propensity 混淆。

### 6. OPVE Boundary

#### DOD-230

OPVE PASS MAY 支持 Engineering/Policy Correctness Gate，验证 determinism、constraint compliance、transition correctness、candidate validity、anti-oscillation、no infinite loop、behavior difference。

#### DOD-231

OPVE、G0/G1、synthetic learner MUST NOT 单独满足 Product Acceptance 或 Learning Evidence Gate；不能证明完整用户任务成立，也不能证明 human efficacy/retention/transfer/population superiority。

### 7. v0.3 Spec / Migration Gate

#### DOD-240

进入 v0.3 Vertical Slice 前必须确认：ADR-0001/0002 reflected；SD-01～SD-11 resolved；six StrategyFamily only；TeachingContext/TeachingStage/PolicyBundle contracts；ErrorType 7+UNKNOWN；orthogonal assistance；anti-oscillation/deterministic tie-break；DecisionTrace probability unambiguous；Outcome/Experiment no second truth；legacy Socratic no final action owner；6 Breaking Changes + 9 Migration Candidates 有 migration semantics。

#### DOD-241

任何 active writer 继续把 legacy strategy enum、integer scaffold/hint/exposure、ambiguous propensity 写为 canonical truth，均为 migration gate failure。

### 8. Recovery / Security / Observability Gates

#### DOD-250

Release candidate MUST 能从 TeachingAction 追到 context/bundle/DecisionTrace/execution/Attempt/AssessmentResult，并在有 outcome 时关联 OutcomeObservation/ExperimentAssignment；MUST NOT 要求 Outcome 回写 DecisionTrace 才能关联。

### 9. Status Vocabulary

#### DOD-260

至少支持：

```text
ENGINEERING_GATE_FAILED
POLICY_CORRECTNESS_GATE_FAILED
LEARNING_EVIDENCE_INSUFFICIENT
RELEASE_ELIGIBLE
```

Issue / release MAY 另外声明：

```text
PRODUCT_ACCEPTANCE_PARTIAL
BLOCKED_BY_PRODUCT_DEFINITION_GAP
BLOCKED_BY_SPEC_GAP
```

但这些状态不得混淆 Engineering / Policy / Learning Evidence 三层 gate 的既有语义。

### 10. Acceptance Criteria

新增 v0.3 AC：

- `DOD-AC-201`：Engineering Gate 与 Policy Correctness Gate 可独立判定。
- `DOD-AC-202`：G0 < 100% 或 forbidden action > 0 时 Policy Gate 必失败。
- `DOD-AC-203`：answer-exposed/assisted success 后无 validation obligation 时 Policy Gate 必失败。
- `DOD-AC-204`：Engineering/Policy PASS 但学习证据不足时为 `LEARNING_EVIDENCE_INSUFFICIENT`。
- `DOD-AC-205`：process metrics 不可满足 primary Learning Evidence Gate。
- `DOD-AC-206`：synthetic learner/OPVE 不被当 human learning evidence。
- `DOD-AC-207`：release data foundation 区分 assignment probability/action propensity。
- `DOD-AC-208`：product-facing task 未建立 `CAP-* / PD-REQ-*` trace 时不得声称对应 Product Capability 已完成。
- `DOD-AC-209`：Vertical Slice / UI / Technical AC 不会被自动升级为 `PD-AC-*`。

### 11. Forbidden Completion / Release Claims

禁止：

- 关键 TODO/pass/NotImplemented 却声称 DONE；
- 只有 Mock 却声称真实模型可用；
- 测试未运行却说通过；
- 删除失败测试；
- 发现 Product Definition / Spec conflict 后未完成治理就隐式选方案；
- 新旧 truth 双写无 reconciliation/retirement；
- 仅 UI 正常但事件/证据/状态链未接通；
- Engineering Correct → Product Acceptance 已完成；
- Engineering Correct → 学习有效；
- Policy Correct → retention/transfer 已提升；
- Vertical Slice AC PASS → 新 Product Requirement / Product AC 已成立；
- synthetic learner → 真人效果；
- process metrics → primary reward；
- ambiguous propensity → causal experiment data；
- 隐藏 `LEARNING_EVIDENCE_INSUFFICIENT`。

### 12. Final v0.3 Gate

当且仅当 Engineering Gate、Policy Correctness Gate 满足，release 所需学习证据状态被诚实标记、实验数据基础正确、无 blocking Product Definition / SPEC GAP 时，implementation MAY 进入相应 release/experimental stage。

如果 release 同时声称某个用户可观察 Product Feature 已完成，还必须单独核对适用 Product Acceptance。学习证据不足时 MAY 工程迭代，但 MUST 保持 `LEARNING_EVIDENCE_INSUFFICIENT`。

### 13. P1-06 Completion Gate

#### DOD-300

P1-06 只有在 P1-02/P1-03/P1-07 真实依赖、对应 current implementation evidence、全量自动门禁、真实 provider/App restart、deep-link/recovery/accessibility 与无内部知识首次用户验收全部有当前证据后才可标 DONE。历史 EXEC 编号只作为证据引用，不作为实时状态源。

#### DOD-301

Engineering、Security/Privacy、Product Acceptance / Product Usability 与 Learning Evidence 必须分开。Onboarding 完成、activity completion 或真实模型可用均不得把 Learning Evidence 从 `LEARNING_EVIDENCE_INSUFFICIENT` 改为有效。

### 14. Course Workspace Completion Gate

#### DOD-320

Course Workspace implementation is not DONE until ADR-0023 / `CWSP-AC-001..012`、migration/rollback/forward-fix、contract/isolation/recovery tests、fresh SQLite upgrade/check、current full backend gates and real API evidence PASS。Frontend selected styling、mock list or default-only query cannot close the Platform gate。

#### DOD-321

Course-centric frontend/route completion additionally requires live browser evidence for multi-Course create/switch/recovery、Activity resume/start、legacy route no-side-effect、responsive/accessibility/console。Engineering PASS must still report Product Acceptance、UX、Security、Quality and Learning Evidence separately。

---

## Askora Security Standard

> Spec ID：`SEC-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3 Learning Core + v1 Local Web / BYOK Alignment  
> 上位约束：`docs/product/PRODUCT-POSITIONING.md`  
> Local Secret governing：ADR-0017 + `docs/specs/platform/local-secret-store.md`

### 1. Trust Boundaries

#### SEC-001

用户上传文件、网页、retrieval result、model/tool output、用户自由文本、第三方 API 数据一律 untrusted。Untrusted data MUST NOT 覆盖 system policy、TeachingAction、PolicyBundle hard rules、tool permissions、state ownership 或 grader rules。

### 2. Prompt Injection

#### SEC-010

材料中的“忽略指令”“调用工具”“直接给答案”等只能作为内容数据处理。

#### SEC-011

防御 MUST 组合：content boundary → retrieval visibility/exposure → prompt construction → tool authorization → output validation。仅依赖 system prompt 不合格。

### 3. Tool Security

#### SEC-020

模型工具 MUST registry + typed schema + allowlist + least privilege + audit。

#### SEC-021

默认禁止模型任意 shell、宿主文件写入、开放网络、凭据读取。

#### SEC-022

有副作用工具 MUST 有 idempotency/confirmation/reconciliation，并记录 ToolCall/ToolResult。

### 4. Model / Data Boundary

#### SEC-030

外部模型只接收完成任务所需最小数据；密钥/token/无关完整 learner history MUST NOT 进入 Prompt。

#### SEC-031

Sensitive data external processing 必须服从产品配置/用户授权；model router/LLM MUST NOT 自行放宽。

### 5. Answer / Support Leakage

#### SEC-040 — Superseded v0.2 Exposure Field

v0.2 `TeachingAction.answer_exposure_max` 曾作为 answer leakage hard boundary。该字段语义在 v0.3 被 `SEC-200` 的正交 TeachingAction envelope supersede；`SEC-040` 仅保留历史审计线索，MUST NOT 作为 v0.3 canonical writer contract。

#### SEC-041 — Grader-only Isolation

grader-only reference answer/rubric/evidence MUST 与 learner-visible context 隔离。

#### SEC-200 — v0.3 TeachingAction Envelope

SYS05 TeachingAction 定义 canonical hard envelope：

```text
scaffold_control = NONE|LOW|MEDIUM|HIGH
hint_specificity = NONE|ORIENTATION|CONCEPTUAL_STRATEGIC|SUBGOAL|PARTIAL_STEP|BOTTOM_OUT
answer_exposure = NONE|PARTIAL|COMPLETE
```

SYS02 与 SYS08 MAY 因证据/安全收紧，MUST NOT 扩大。任何无法可靠判断 exposure/support 的内容 MUST conservative block/tighten。

#### SEC-201 — Assessment Integrity

独立 assessment/retrieval 场景 MUST 执行 SYS05 hard constraints；`SEC-041` 的 grader-only isolation 同时适用。Explicit user direct-answer request MUST NOT 自动绕过 assessment integrity。

#### SEC-202 — Actual Exposure

实际呈现的 support/hint/exposure MUST 可记录到 SYS04 Attempt/event chain；MUST NOT 仅假设计划 envelope 等于实际经历。

### 6. Citation / Grounding

#### SEC-050

资料型输出 MUST NOT 用未检索到的模型常识伪装资料事实。引用必须映射 EvidenceBundle/SourceSpan。

### 7. Upload Security

至少防御文件类型伪造、超大文件/压缩炸弹、path traversal、恶意外部引用、parser resource exhaustion、quarantined content 进入索引。阈值可配置且默认保守。

### 8. Code Execution

#### SEC-060

代码评估必须隔离运行，默认无宿主敏感文件/凭据/开放网络，并限制 CPU/memory/time/process。

### 9. LocalOwner / Workspace Boundary

#### SEC-065

v1 无 Account/Login/Tenant/RBAC。无认证不等于无安全边界：Local Server MUST 仅绑定 loopback，并验证受支持 browser origin；资源 query/write 仍必须解析唯一 LocalOwner 并执行 Workspace scope。

#### SEC-066

Workspace 是单机数据隔离边界，不是权限角色。跨 Workspace object ref、retrieval scope、ProjectMaterial、Goal/Session binding MUST fail closed，并不得泄漏不相关 Workspace 的 object metadata。

### 10. Secrets / Logging

#### SEC-070 — Logging

日志默认保存 metadata/reason/reference，不保存完整敏感上下文；debug capture 必须显式、限期、可删除。

任何 API key、Authorization、secret material、secret-bearing request body 或可恢复 credential representation MUST NOT 进入普通 log、trace、diagnostic、Prompt、frontend cache、export 或默认 backup。

#### SEC-071 — Historical Desktop Model Credential

旧版 `SEC-071` 规定 Electron main + `safeStorage` + preload IPC。该 **Desktop-specific mechanism 已由 Product Positioning、ADR-0017 与 `LSS-*` supersede**。

其仍有效的保护意图仅包括：

- OS-backed secure persistence；
- no plaintext fallback；
- browser/renderer 无 saved-key readback；
- probe 不携带私人资料；
- credential 不进入日志/Prompt/export。

Electron/safeStorage/IPC/control-token 不得再作为 v1 production Local Web 的 Required 安全机制。

#### SEC-072 — Local Web BYOK Credential

Production v1 provider credential MUST 服从 ADR-0017 + `LSS-*`：

```text
macOS   → exact keyring.backends.macOS.Keyring
Windows → exact keyring.backends.Windows.WinVaultKeyring
```

并要求：

- production explicit backend allowlist；
- automatic/third-party/Null/file backend rejected；
- Windows credential 使用 local-machine persistence；
- no plaintext persistent fallback；
- browser/public API 无 secret read/enumerate capability；
- ordinary SQLite 只保存 non-secret profile/ref/journal metadata；
- apply/clear 使用 durable non-secret activation journal 解决 SQLite + OS store crash consistency；
- restore 缺 secret 时进入 degraded/reconfigure，不允许 `.env` fallback。

#### SEC-073 — Local Secret Threat Claim Boundary

OS credential storage 保护的是 Askora 普通数据文件、browser、日志、诊断和 backup/export 泄漏面。Askora MUST NOT 宣称它能抵御同一 OS 用户权限下的任意代码执行、完整机器 compromise 或提供 native app sandbox/hardware-backed isolation。

未来更强 native credential ACL MAY 通过新的 ADR 引入，但 MUST NOT 让 Desktop shell 成为 v1 prerequisite。

### 11. Dependencies

#### SEC-080

新增生产依赖需要目的/维护/安全评估；执行代理 MUST NOT 自行加入大型 autonomous-agent/security framework 解决局部问题。

`keyring` 作为 ADR-0017 已批准的窄 production dependency；版本必须 lock，升级必须重新运行 `LSS-*` backend allowlist/leakage/crash tests。

#### SEC-081 — Rich Response Renderer

模型/检索/工具产生的 Markdown、公式和结构化 block 一律 untrusted。前端 MUST 使用 typed component allowlist；MUST NOT 执行 raw HTML、MDX、script、模型指定组件、代码块或 arbitrary card command。链接协议只允许 `http`/`https`；v1.0 remote image/file/data URL MUST blocked。公式 renderer MUST 禁止 trusted external-resource commands，并限制 expansion/size。

#### SEC-082 — Recovery and Export

Recovery/backup/export 必须服从当前 v1 Data Control contract。任何 package/export MUST NOT 包含 provider API key、recoverable model credential、内部 Prompt/system instructions、grader-only answer/rubric、其他 Workspace 数据或本地绝对路径。

User Data Export 使用显式 allowlist，MUST NOT 包含 KEK/Recovery Key/provider key、内部 Prompt/system instructions、grader-only answer/rubric、其他 owner 数据或本地绝对路径。若历史 recovery package 仍使用加密恢复密钥，其机制只作为对应 historical/current data-control contract 的实现证据，不得重新引入 Account credential semantics。

#### SEC-083 — Destructive Data Control

Erasure/Permanent Delete 必须固定 scope、影响预览、显式用户动作、幂等与最小 audit receipt。外部模型、资料内容、renderer 或普通 retry 无权触发/扩大删除范围。

### 12. Policy Override Protection

#### SEC-210

LLM/Agent、retrieved content、SYS08 fallback、experiment variant MUST NOT override SYS05 typed hard constraint 或恢复 hard-filtered action。

#### SEC-211

Legacy Socratic selector/state graph MUST NOT 成为 final TeachingAction owner 或 exposure override；迁移期只允许 bounded adapter/move provider/execution role。

### 13. Tests

必须覆盖：

- document/retrieval/tool injection；
- grader/answer leakage；
- attempted scaffold/hint/exposure expansion；
- direct-answer assessment integrity；
- actual exposure capture；
- path traversal；
- LocalOwner/Workspace cross-scope isolation；
- secret/log leakage；
- malicious structured output；
- tool parameter validation；
- legacy Socratic no override；
- LocalSecretStore exact backend allowlist；
- Null/third-party/override backend rejection；
- Windows local-machine credential persistence；
- probe payload excludes private data；
- browser/API/SQLite/log/export/backup zero-secret leakage；
- activation crash/restart matrix；
- clear remains disabled even if orphan-secret cleanup fails；
- restore missing secret requires reconfiguration and no env resurrection。

Data lifecycle 还必须覆盖 recovery wrong-key/tamper/truncation/path/limits（如当前 recovery format 适用）、export zero-secret leakage、erasure confirmation/scope、managed old-backup no-resurrection。

### 14. Acceptance Criteria

- `SEC-AC-001`：恶意文档不能改变 TeachingAction/PolicyBundle/tool permission。
- `SEC-AC-002`：模型不能调用未注册工具。
- `SEC-AC-003`：grader-only answer 不进入 learner output。
- `SEC-AC-004`：外部模型请求不包含测试密钥/token 或无关个人数据。
- `SEC-AC-005`：quarantined 内容不进入 retrieval。
- `SEC-AC-006`：代码评估无法访问宿主敏感资源。
- `SEC-AC-007`：引用声明可追踪 SourceSpan。
- `SEC-AC-201`：SYS02/SYS08 无扩大 SYS05 support/exposure envelope 的路径。
- `SEC-AC-202`：hard rule 无 LLM/experiment/legacy bypass。
- `SEC-AC-203`：browser、普通 API、SQLite profile、日志、Prompt、telemetry、export/default backup 无模型明文 credential。
- `SEC-AC-204`：production LocalSecretStore 只接受 ADR-0017/LSS 指定 OS-backed backend；安全存储不可用时拒绝持久化，不降级明文。
- `SEC-AC-205`：clear 后 canonical routing 保持 disabled，即使旧 secret 删除失败或开发 `.env` 仍存在。
- `SEC-AC-206`：模型配置任一 crash phase 不产生 silent profile/runtime split-brain。

### 15. Legacy Mapping

历史整数/L0-L4 exposure MAY read-only/audit；canonical writer MUST 只写 `answer_exposure`，不得 permanent dual-write。旧 `SEC-040` 的保护意图仍由 `SEC-200` 承接；旧 `SEC-041` 保留 grader-only isolation。

旧 Desktop credential security 只保留安全意图，具体 Electron mechanics 由 `SEC-071` 明确 superseded。

### 16. Forbidden Implementations

禁止：

- Prompt 作为唯一权限层；
- autonomous agent 任意 shell/network；
- reference answer 与 learner prompt 无隔离混放；
- 外部模型默认接收全部个人资料；
- 日志打印 secret/完整敏感 Prompt；
- browser 获取 saved credential/decrypt/file control capability；
- LocalSecretStore 不可用时明文落盘；
- automatic/unknown keyring backend 作为 production security decision；
- probe 携带个人资料；
- parser 信任扩展名；
- 恶意 retrieval content 提升为 system instruction；
- 继续写 `answer_exposure_max` 为 canonical security truth；
- SYS08/LLM 自动扩大 TeachingAction envelope；
- Account/JWT/AuthSession 重新成为 v1 security prerequisite。

### 17. Historical Identity / Account Security

旧 `SEC-300..303` 关于 Password、JWT、AuthSession、Account Deletion 的要求属于 P1-05 历史实现合同，已由 `PRODUCT-POSITIONING.md` + ADR-0015 / `LID-*` supersede，不得作为 v1 active runtime requirement。其仍有价值的通用原则（secret 不明文、rate-limit destructive/recovery operations、删除 no-resurrection、最小 audit）由当前 LocalOwner/Data Control/LocalSecretStore 合同承接。以下为 v1 生效的无认证 active requirements：

Askora 为本地单用户 App，无注册/登录/登出、无密码、无 JWT/会话、无 recovery credential、无账号删除。`LocalOwner` 是唯一本地数据归属主体，MUST NOT 保存 phone/email/password/token/recovery secret/device fingerprint 等认证材料（见 `identity-privacy-lifecycle.md` LID-003）。

#### SEC-301

无认证 runtime MUST 只监听 loopback（`127.0.0.1` / `::1`）；`0.0.0.0`、LAN 或公网接口 MUST fail startup。CORS/WebSocket MUST 仅 allowlist loopback origins（LID-020..022）。`/auth/*`、dev auto-login、account deletion routes MUST 停止注册（LID-040）。

#### SEC-302

危险本地数据清除（Erase Selected Local Data / Reset Local Workspace）MUST 使用 preview + expiring confirmation + typed phrase + idempotency + durable receipt，且不得重新引入 password 或 account-deletion 语义（LID-061/062）。

#### SEC-303

数据清除必须 owner-scoped、reconciliation zero-residual；tombstone/receipt 不得保存 PII/content/secret；restore barrier 必须在本地数据恢复与后台处理前生效。

### 18. P1-06 Onboarding Security

#### SEC-320

Onboarding view/preference/log MUST NOT 包含 Key/fragment、Prompt、grader-only、raw provider body、absolute path 或其他 Workspace ref。Boundary copy 只能引用当前 MODEL-CONFIG/P1-03 已验证事实，不得承诺完全离线或绝对隐私。

#### SEC-321

Onboarding MUST NOT 自动 probe provider、加载未经选择的私人文档、创建样例/Goal/Activity 或执行 recovery command。所有导航后的副作用仍由原 owner command 的 idempotency/security gate 控制。

### 19. Course Workspace Selection Security

#### SEC-330

ADR-0023 / `CWSP-*` list/get/create/current/switch/Activity query MUST resolve LocalOwner first and validate exact Workspace before returning metadata。Foreign and nonexistent refs use the same non-enumerable result；logs/errors MUST NOT expose other-Workspace name、Activity title、note/transcript content or local path。

#### SEC-331

Workspace transition guard may carry only typed state and versioned refs, never draft/note正文、Prompt or secret。Create/switch idempotency receipt stores sanitized result only。Route/GET/refresh cannot mutate selection；browser state cannot bypass server owner/version/isolation checks。

#### SEC-AC-330

Isolation/security tests prove no cross-Workspace existence leakage、no transition-content logging、no GET hidden write and no browser/default-marker selection takeover。
