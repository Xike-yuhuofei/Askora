# Askora CI v2 + Local Web Baseline 全链路自主执行提示词

你是 Askora 项目的高级软件架构师、CI/CD 工程师、测试架构师和执行代理。

GitHub 仓库：

`https://github.com/Xike-yuhuofei/Askora.git`

## 最终目标

不要把本任务理解为“执行某一份 EXEC”。

你的目标是：

> **基于当前最新 main 和已经冻结的 Product Positioning / ADR / Spec / EXEC，自主完成 Askora 从历史多用户 / Auth / PostgreSQL / Redis / Docker / Desktop 假设，向 v1 单用户 Local Web + SQLite + Local Files 架构的工程收口，并完成 CI v2 Required Gate。**

最终目标状态：

```text
Askora v1
=
Single User
+ Local Web Application
+ Browser → Loopback Local Server
+ SQLite
+ Local Files
+ Local Index / Memory
+ Local Background Jobs
+ BYOK AI Providers
+ No Login / Register / Account
+ No Redis / PostgreSQL / Docker runtime requirement
```

并最终形成：

```text
Askora CI / Required
├── Product Boundary
├── Backend Core
├── Local Data Integrity
├── Recovery & Rebuild
├── Local Web Chromium E2E
└── Quality & Security
```

---

# 一、不要等待用户逐个批准 EXEC

你必须使用**目标模式 / autonomous execution**。

开始后自行读取：

```text
AGENTS.md
docs/product/PRODUCT-POSITIONING.md
docs/specs/**
docs/adr/**
docs/design/**
docs/exec-plans/README.md
docs/exec-plans/active/**
```

重点读取：

```text
ADR-0015

docs/specs/quality/ci-infrastructure-standard.md
docs/specs/quality/v1-local-web-quality-reconciliation.md
docs/design/CI-Test-Infrastructure-Gap-Analysis.md

EXEC-047～051
EXEC-043～046
EXEC-052～058
```

以**执行时最新 main**为唯一代码事实。

不要依赖本提示词对仓库现状的摘要。

---

# 二、以最终状态为目标，而不是机械执行文档

EXEC 是：

> 已冻结的约束与验收合同。

不是要求用户逐份触发的工作单。

你必须：

1. 建立当前 EXEC dependency graph；
2. 检查哪些已经 DONE；
3. 检查哪些可以立即执行；
4. 自动执行所有已满足 dependency 的任务；
5. 一个 EXEC 完成后自动解锁并继续下一个；
6. 安全可并行的任务可以并行；
7. 有文件重叠或状态依赖的任务必须串行；
8. 不需要每完成一个 EXEC 就停下来询问用户。

只在真正出现：

```text
POSITIONING GAP
SPEC GAP
无法安全自动解决的 destructive migration
缺失不可推断的外部凭据
GitHub 权限不足
```

时停止对应分支。

其他普通工程问题必须自行解决。

---

# 三、权威优先级

严格遵循：

```text
PRODUCT-POSITIONING.md
        ↓
Canonical Design / Accepted ADR
        ↓
Canonical Specs
        ↓
Vertical Slice
        ↓
EXEC
        ↓
Code / Tests / Workflow
```

如果下位内容冲突：

> 上位真值优先。

不得因为历史代码、测试或 EXEC 已存在，就恢复已经被 Product Positioning supersede 的产品能力。

---

# 四、执行依赖图

根据当前仓库重新验证，不要盲信下面状态。

总体逻辑：

```text
                 EXEC-042
           Teaching Policy Closure
                  │
                  │ independent
                  │

EXEC-047
   ↓
EXEC-048
   ↓
EXEC-049
   ↓
EXEC-050
   ↓
EXEC-051
   ↓
   ├─────────────→ EXEC-053
   │                   ↓
   │                EXEC-054
   │                   ↓
   │                EXEC-055
   │                 ↙    ↘
   │           EXEC-056   EXEC-057
   │              ↑          │
   │              │          │
   ↓              │          │
EXEC-043          │          │
   ↓              │          │
EXEC-044          │          │
   ↓              │          │
EXEC-045          │          │
   ↓              │          │
EXEC-046 ─────────┘          │
                             ↓
                         EXEC-058
```

另外：

```text
EXEC-052
```

属于 Governance / Test Oracle Classification，可在不修改冲突代码的前提下优先执行。

---

# 五、允许提高执行效率

不要人为坚持“一 EXEC = 一次 Codex 会话”。

允许：

### 1. 连续执行

例如：

```text
EXEC-047 DONE
→ 自动执行 048
→ 自动执行 049
→ 自动执行 050
→ 自动执行 051
```

无需用户重新下指令。

### 2. 安全并行

如果文件域和状态 owner 不冲突，例如：

```text
CI governance
Teaching Policy closure
```

可以独立推进。

### 3. 合并验证

不要每个 EXEC 都重新执行完全相同的昂贵 full-suite。

采用：

```text
targeted tests
        ↓
subsystem regression
        ↓
milestone full-suite
```

在关键 integration milestone 再执行全量测试。

### 4. 批量提交

默认仍保持 EXEC 可追踪性。

推荐：

```text
一个逻辑 EXEC 一个 commit
```

但无需停止会话。

连续执行：

```text
commit EXEC-047
commit EXEC-048
commit EXEC-049
...
```

然后继续。

---

# 六、CI v2 最终必须完成

## A. Product Boundary

自动验证：

```text
no login
no register
no JWT requirement
no AuthSession runtime
single LocalOwner
Workspace != Tenant
loopback-only
no Redis requirement
no PostgreSQL requirement
no Docker requirement
no Askora Cloud requirement
LLM cannot directly write Canonical State
Conversation != Learning Evidence
Chunk != KnowledgeUnit
```

---

## B. Production Local Runtime

必须证明：

```text
Browser
→ Local Server
→ SQLite
→ Local Files
```

能够作为真实 Production Local path 工作。

最终用户启动不能要求：

```text
Docker
Redis
PostgreSQL
JWT secret
Kafka
external Askora server
```

---

## C. Test Oracle Realignment

历史测试必须分类：

```text
KEEP_REQUIRED
REWRITE_TO_V1
OPTIONAL_COMPATIBILITY
HISTORICAL
DELETE
ADD_REQUIRED
```

尤其清理：

```text
Auth
Password
Account
JWT
cross-user
Tenant
PostgreSQL production
Redis runtime
Desktop native
Electron release
```

相关 stale oracle。

禁止：

> 删除旧测试，却不建立新 v1 contract。

---

## D. SQLite Data Integrity

Required Gate 至少验证：

```text
fresh SQLite → migrate → usable
legacy SQLite fixture → migrate → usable
migration failure → durable data preserved
restart → data preserved
```

---

## E. Recovery & Rebuild

Required Gate 至少验证：

```text
Derived Data delete
→ rebuild
→ canonical semantics preserved
```

包括适用的：

```text
chunks
embeddings
indexes
retrieval cache
derived learner projection
```

以及：

```text
job running
→ process interrupted
→ restart
→ resume/retry/restart
→ durable data intact
```

---

# 七、Chromium Local Web E2E

使用 Playwright 或项目冻结的等价方案。

至少验证：

```text
isolated AskoraData
→ start Local Server
→ Chromium
→ open Askora
→ no login
→ create/open Workspace
→ import local fixture
→ learning flow
→ persist state
→ restart server
→ reopen browser
→ state remains
```

v1 不要求：

```text
Safari matrix
Firefox matrix
native macOS application E2E
Electron packaged release
```

---

# 八、Quality Gate

最终 Required CI 应包含：

```text
Ruff
Formatter
MyPy
Backend Tests
Frontend Tests
Frontend Build
Chromium E2E
SQLite Migration
Recovery/Rebuild
Security
Dependency Audit
```

逐步删除永久 technical debt：

```text
check_black_baseline.py
historical hash baseline
large permanent mypy exclusion
historical phase hard-coded docs checks
```

禁止为了全绿：

```text
降低 coverage
扩大 skip
删除有效测试
降低断言
```

---

# 九、Optional / Scheduled

以下可以继续存在：

```text
PostgreSQL compatibility
Docker build
secondary Python version
real AI provider smoke
expensive AI eval
legacy migration compatibility
```

但默认：

> 不属于 Askora v1 Required Gate。

不要为了“架构纯洁”无意义删除所有 PostgreSQL/Docker 代码。

判断标准是：

```text
是否是 Production Local requirement？
```

而不是：

```text
仓库里是否存在？
```

---

# 十、真实 AI Provider

Required PR CI：

```text
deterministic mock
fixture
recorded structured sample
```

真实 Provider：

```text
manual
scheduled
release evidence
```

BYOK API Key 不得成为普通 Required CI 的必要 secret。

但是如果声称：

> “某真实 Provider 当前可用”

则必须真正执行 provider validation，Mock 不能代替。

---

# 十一、Dependency Cleanup

审计：

```text
asyncpg
redis
PyJWT
passlib
bcrypt
aiokafka
```

根据 runtime reachability 分类：

```text
REQUIRED
OPTIONAL
LEGACY_MIGRATION
UNUSED
```

只有确认：

```text
无 Production Local 使用
无 migration 使用
无 test/compatibility 正当用途
```

才能删除。

不要基于名称机械删依赖。

---

# 十二、文档治理

必须同步维护：

```text
docs/document-inventory.md
docs/specs/README.md
docs/exec-plans/README.md
```

旧文档如果仍有历史价值：

> 保留历史，不必删除。

但必须清楚标记：

```text
SUPERSEDED
HISTORICAL
```

不能继续被解释为 current canonical truth。

---

# 十三、GitHub Actions

最终重构 `.github/workflows/**`。

要求：

### Required

暴露稳定 aggregate status：

```text
Askora CI / Required
```

内部 job 名称允许演进。

### Workflow

应支持：

```text
concurrency
cancel-in-progress
合理缓存
合理 path filtering
artifact only when useful
dependency lock/cache key correctness
```

不得让 Required job 因 path skip 永久 pending。

---

# 十四、GitHub Ruleset / Branch Protection

最后检查 `main`。

只有：

```text
Askora CI / Required
```

已经真实稳定产生并至少成功运行后，才配置 Required Status Check。

目标：

```text
CI FAIL
→ main merge blocked
```

不能出现：

```text
CI exists
but
main remains unprotected
```

如果当前 GitHub 工具权限不能修改 branch protection：

不要伪造完成。

输出：

```text
MANUAL_REPO_SETTING_REQUIRED
```

并给出精确配置内容。

---

# 十五、测试策略

不要每一步全部重跑。

采用分层：

```text
Phase change
→ targeted tests

Subsystem completion
→ relevant integration suite

Major milestone
→ full backend/frontend suite

CI workflow closure
→ actual GitHub Actions validation
```

重点保护：

```text
Teaching Policy
Assessment
Learner State
Review Scheduler
Retrieval
Content Pipeline
Migration
Recovery
Rebuild
Local Web runtime
```

---

# 十六、禁止事项

绝对禁止：

```text
为了绿 CI 删除有效 contract test
使用 skip 掩盖失败
降低断言
降低 coverage threshold
通过 Docker 才能启动 Production Local
通过 PostgreSQL 才能运行 Production Local
Redis outage 导致本地 App 无法启动
恢复 Login/AuthSession
恢复 multi-user SaaS
让 LLM 直接写 SQLite canonical state
用 Mock 宣称真实 Provider 可用
修改 Product Positioning 来迎合现有代码
```

---

# 十七、遇到普通问题不要停止

以下不属于需要用户介入的 blocker：

```text
lint error
type error
test failure
migration bug
dependency conflict
legacy unused code
broken import
workflow YAML error
Playwright config error
SQLite fixture error
```

自行修复。

只有真正改变冻结产品/架构语义时才报告 GAP。

---

# 十八、完成标准

不要因为某一个 EXEC 完成就结束。

尽可能推进到：

```text
所有当前可执行 EXEC DONE
```

最终理想状态：

```text
EXEC-047～051 DONE
EXEC-043～046 DONE
EXEC-052～058 DONE

Askora CI / Required PASS
Production Local PASS
Chromium E2E PASS
SQLite migration PASS
Recovery/Rebuild PASS
Quality/Security PASS
```

如果某条链因真实 dependency 无法继续：

继续执行其他独立可执行链。

---

# 十九、最终只给一份综合报告

不要每个 EXEC 都向用户输出长报告。

最终报告：

```text
ASKORA LOCAL WEB / CI V2 EXECUTION REPORT

1. Final Status
2. EXEC completed
3. EXEC blocked
4. Production Local status
5. Removed legacy runtime requirements
6. Test oracle migration
7. SQLite migration/recovery/rebuild
8. Chromium E2E
9. Required CI topology
10. Optional compatibility workflows
11. Dependency cleanup
12. Documentation governance
13. GitHub branch protection
14. Tests / workflows executed
15. Remaining blockers
16. Commits
17. Recommended next action
```

如果全部完成：

```text
CI_V2_DONE
```

如果存在真正 blocker：

```text
CI_V2_PARTIAL
```

明确 blocker，但不要把普通工程问题当 blocker。

---

# 核心原则

你的任务不是逐份完成工单。

你的任务是：

> **在已经冻结的设计与执行合同范围内，以最少人工干预把 Askora 收敛到正确的 v1 Local Web 产品架构与 CI v2 工程基线。**

优化目标：

```text
正确性
>
数据安全
>
产品定位一致性
>
自动验证能力
>
可维护性
>
执行效率
>
历史兼容性
```

开始执行，不要等待逐 EXEC 确认。