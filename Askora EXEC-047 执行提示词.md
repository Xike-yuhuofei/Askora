# Askora EXEC-047 执行提示词

你现在是 Askora 项目的工程执行代理。

你的唯一目标是：

> **完整执行并关闭** **`EXEC-047 — LocalOwner Foundation & Migration`。**

本 EXEC 只建立 Local Single-User Identity 的底层 ownership foundation。

禁止提前执行：

- EXEC-048 Backend No-Auth Cutover
- EXEC-049 Frontend / Settings / Onboarding De-accounting
- EXEC-050 Auth Persistence Cleanup
- EXEC-051 Local Identity Release Closure
- EXEC-043～046 UI-03

***

# 1. 必须从当前 main 开始

开始前执行：

```bash
git status
git branch --show-current
git pull --ff-only
git log -10 --oneline
```

必须确认：

- 当前工作基于最新 `main`；
- 无未经授权的 dirty changes；
- 不依赖旧对话摘要推断当前仓库状态。

***

# 2. 必读治理文档

严格按以下顺序读取：

1. `AGENTS.md`
2. `docs/specs/README.md`
3. `docs/design/Local-Single-User-Identity-Authentication-Removal-Canonical-Design-Delta.md`
4. `docs/adr/ADR-0015-local-single-user-identity-without-authentication.md`
5. `docs/specs/platform/identity-privacy-lifecycle.md`
6. `docs/specs/vertical-slices/local-single-user-authentication-removal.md`
7. persistence / data-control / learner ownership 相关最新 Specs
8. `docs/exec-plans/active/EXEC-047-local-owner-foundation-migration.md`

同时审计当前真实代码：

- `User`
- auth/session/JWT
- `get_current_user`
- `canonical_user_id()`
- learner ownership
- documents
- goals
- dialogs
- learning activities
- learner state
- decision records
- 所有关键 `user_id` / owner references
- Alembic migrations

不得只根据 EXEC 摘要编码。

***

# 3. 第一件事：Dependency Gate

必须确认：

```text
EXEC-1062 = DONE
```

且已经：

- 在当前 `main` 中真实存在；
- 从 active 归档到 completed；
- P1-06 release evidence 已形成；
- ADR-0015 = Accepted；
- Local Identity Specs = FROZEN；
- Alembic migration heads clean。

如果当前 main 尚未真正包含 EXEC-1062 DONE：

```text
BLOCKED_BY_DEPENDENCY
```

立即停止 EXEC-047。

禁止因为“用户说已经完成”而绕过仓库事实。

***

# 4. EXEC-047 的核心目标

建立：

```text
唯一 durable LocalOwner
+
LocalOwnerContext
+
legacy learner ownership migration
```

使 Askora 从：

```text
User / Auth Identity
≈
Learner Ownership
```

逐步解耦成：

```text
LocalOwner
=
本机单用户数据所有权唯一事实源
```

但本 EXEC **暂时不能删除现有 Authentication 系统**。

***

# 5. 第一性原则

Askora 已冻结为：

```text
Local
Single User
Private
Self-use
```

因此：

> 用户对本地数据的 ownership 不应该依赖登录账号、JWT、session、密码或设备指纹。

最终必须存在且只存在：

```text
1 LocalOwner
```

它负责回答：

> “这台 Askora 本地实例中的学习数据属于哪个 canonical owner？”

它不是：

- Account；
- Login identity；
- Session；
- Device fingerprint；
- machine-id；
- JWT subject；
- API Key identity。

***

# 6. 必须先做 Ownership Inventory

在写 schema 前，必须审计真实仓库并建立 inventory。

至少覆盖：

```text
Documents / Materials
Goals
LearningPlans
LearningActivities
Dialogs / Tutor sessions
LearnerState
Assessments
ReviewSchedule
DecisionTrace / Teaching decisions
Progress / Evidence
Data export / recovery ownership
```

识别：

- 当前 owner field；
- 当前 FK；
- 数据类型；
- UUID/string compatibility；
- 是否依赖 User；
- 是否依赖 `get_current_user`；
- migration 风险。

不得为了“统一”而在本 EXEC 中批量重命名所有 `user_id`。

***

# 7. LocalOwner Schema

实现 canonical LocalOwner persistence。

必须满足：

```text
cardinality = exactly one
```

需要支持：

```text
empty datastore
legacy single learner datastore
ambiguous multi-subject datastore
repeated restart
migration replay
```

LocalOwner ID 必须稳定。

推荐性质：

```text
UUID
durable
opaque
non-secret
locally generated or deterministically migrated
```

禁止使用：

- hostname；
- MAC；
- machine serial；
- device fingerprint；
- password hash；
- access token；
- refresh token；
- recovery secret。

***

# 8. Bootstrap Contract

必须实现或等价实现：

```text
ensure_local_owner()
get_local_owner_context()
```

具体名称可按现有代码规范调整，但职责必须明确。

## Empty datastore

首次启动：

```text
0 LocalOwner
→ atomically create 1
```

并发/重复 bootstrap 后仍必须：

```text
count(LocalOwner) == 1
```

## Existing datastore

再次启动：

```text
same LocalOwner ID
```

禁止每次启动新建 owner。

***

# 9. Legacy Single Learner Migration

如果旧数据库只有一个真实 learner subject：

必须：

1. 识别唯一 learner ownership；
2. 映射为 canonical LocalOwner；
3. 保持数据数量不变；
4. 保持 owner relationships 可解析；
5. 保持稳定 owner ID。

优先复用已有稳定 UUID，如果符合 ADR/Spec。

如果必须做 deterministic mapping：

必须：

- 可 replay；
- 有测试；
- 不依赖 secret；
- 不依赖 session；
- 不依赖运行时随机条件。

***

# 10. Ambiguous Multi-Subject

这是关键安全边界。

如果数据库中发现多个真实 learner subjects，且无法无歧义判断唯一所有者：

禁止：

- 自动选择第一个；
- 选择最近登录用户；
- 选择数据最多用户；
- 选择最近活跃用户；
- merge；
- delete；
- silently normalize。

必须：

```text
fail closed
```

返回 canonical error：

```text
LOCAL_OWNER_AMBIGUOUS
```

或 Spec 已冻结的等价错误。

必须保证：

```text
no destructive mutation
```

***

# 11. LocalOwnerContext

建立统一 ownership resolution boundary。

后续业务层应该可以逐步从：

```python
get_current_user(...)
```

迁移为：

```text
LocalOwnerContext
```

但 **EXEC-047 不负责完成 backend 全量 cutover**。

那属于：

```text
EXEC-048
```

本 EXEC 只建立稳定 foundation 和兼容投影。

***

# 12. Compatibility Boundary

当前旧系统仍可能存在：

```text
User
JWT
Session
Auth routes
Password
Recovery
```

在 EXEC-047 中它们：

```text
MAY remain operational
```

但必须明确：

```text
User != canonical ownership truth
```

允许临时：

```text
Legacy User
→ compatibility projection
→ LocalOwner
```

禁止：

```text
LocalOwner
→ Auth session truth
```

***

# 13. 明确禁止的范围

本 EXEC 禁止：

### 不删除 Auth

不得：

- 删除 `/auth/*`；
- 删除 Login/Register；
- 删除 JWT；
- 删除 session；
- 删除 password；
- 删除 RecoveryKit；
- 修改 Settings account UI。

这些属于后续 EXEC。

***

### 不全面重写 FK

禁止批量：

```text
user_id → owner_id
```

除非 EXEC-047 Spec 明确要求某处属于 foundation migration。

优先建立 compatibility boundary，而不是大爆炸迁移。

***

### 不碰教学算法

禁止修改：

- Teaching Policy；
- Learner Model；
- Assessment；
- Retrieval；
- LearningPlan algorithm；
- Review scheduling；
- Decision Policy。

***

### 不碰 UI-03

禁止修改：

- Sidebar；
- Today hierarchy；
- Learning IA；
- Library progressive disclosure；
- Settings hierarchy。

***

# 14. 数据迁移要求

如果新增 Alembic migration：

必须：

- 单一明确 revision；
- upgrade deterministic；
- migration 可在真实 legacy fixture 上运行；
- 不读取 secret 决定 owner；
- 不删除 legacy data；
- 不改变业务记录数量；
- migration heads clean。

必须验证：

```bash
alembic upgrade head
alembic check
```

并测试至少：

```text
fresh DB
legacy single learner DB
ambiguous multi-subject DB
```

***

# 15. RED Tests First

实现前先补测试。

至少包括：

## Bootstrap

```text
empty DB
→ exactly one LocalOwner
```

## Stability

```text
restart N times
→ same owner_id
```

## Concurrency / idempotency

```text
ensure_local_owner() repeated/concurrent
→ exactly one owner
```

## Legacy migration

```text
one legacy learner
→ stable mapping
→ record counts unchanged
```

## Referential integrity

验证 documents/goals/dialogs/learning/decision 等关键 ownership references。

## Ambiguous migration

```text
multiple real subjects
→ LOCAL_OWNER_AMBIGUOUS
→ zero destructive cleanup
```

## Secret isolation

确保 migration / logs / errors 不输出：

- password；
- token；
- recovery secret；
- API keys。

## Auth compatibility

旧 Auth smoke tests 仍然通过。

***

# 16. Migration Replay / Determinism

必须证明：

相同 legacy input：

```text
Run A
Run B
```

得到相同 ownership mapping。

不得依赖：

```text
current timestamp
random choice
current session
last login
query ordering accident
```

***

# 17. Logging / Error Handling

允许记录：

- migration phase；
- object counts；
- owner mapping outcome；
- ambiguity reason code。

禁止记录：

- plaintext password；
- password hash；
- token；
- JWT；
- recovery secret；
- API Key。

错误必须是结构化、稳定、可测试的。

***

# 18. 实施顺序

严格遵循：

## Phase A — Baseline Audit

记录：

```text
HEAD
git status
migration head
current identity model
current owner model
ownership inventory
```

***

## Phase B — RED Tests

先建立失败测试。

***

## Phase C — LocalOwner persistence

实现唯一 LocalOwner schema + migration。

***

## Phase D — Resolution boundary

实现：

```text
ensure_local_owner
get_local_owner_context
```

或规范等价物。

***

## Phase E — Legacy migration

完成：

```text
single learner
ambiguous learner
replay
integrity
```

***

## Phase F — Compatibility

证明：

```text
existing auth runtime still works
```

但 canonical ownership 已建立。

***

## Phase G — Full Gates

全部通过后才能关闭 EXEC。

***

# 19. Required Tests

至少执行：

```bash
cd apps/backend

pytest
ruff check app tests
mypy app
alembic check
```

如果仓库已有 migration-specific 命令，也必须运行。

随后：

```bash
cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

如果 EXEC-047 修改会影响全仓测试，应执行项目规定的完整 CI 等价测试。

禁止：

- 删除测试；
- `skip` 失败测试；
- 弱化 assertion；
- 扩大 ignore；
- 用 mock 绕过真实 migration。

***

# 20. Acceptance Criteria

必须逐项证明：

### E047-AC-001

空 datastore：

```text
bootstrap
→ exactly one LocalOwner
```

PASS。

### E047-AC-002

重复启动：

```text
owner_id stable
```

PASS。

### E047-AC-003

单 legacy learner：

```text
documents
goals
dialogs
learning
decision owner refs
```

均可映射，且数据数量不变。

PASS。

### E047-AC-004

multi-subject fixture：

```text
LOCAL_OWNER_AMBIGUOUS
```

并且 fail closed。

PASS。

### E047-AC-005

owner selection 不依赖：

```text
password
token
recovery secret
```

PASS。

### E047-AC-006

现有 auth flow smoke tests 仍可运行。

PASS。

### E047-AC-007

不存在第二个 canonical owner truth。

PASS。

***

# 21. Governance Closure

只有全部 AC 与 required tests PASS 后：

1. 将 EXEC-047 标为：

```text
DONE
```

1. 从：

```text
docs/exec-plans/active/
```

迁移到：

```text
docs/exec-plans/completed/
```

1. 更新：

```text
docs/exec-plans/README.md
docs/exec-plans/completed/README.md
docs/document-inventory.md
```

如治理规则要求，再更新对应 release / vertical-slice evidence。

1. 确认：

```text
EXEC-048
```

dependency gate 已解除。

不得因为 EXEC-047 完成而直接执行 EXEC-048。

***

# 22. Commit

完成后使用独立 commit。

建议：

```text
feat(identity): establish local owner foundation
```

不要混入其他任务。

***

# 23. 最终报告格式

最终只报告以下内容：

## Status

```text
DONE
```

或：

```text
BLOCKED_BY_DEPENDENCY
BLOCKED_BY_SPEC_GAP
BLOCKED_BY_MIGRATION_AMBIGUITY
```

***

## Baseline

- starting HEAD
- migration head
- dependency status

## Ownership Inventory

列出审计到的 canonical learner-owned data categories。

## Implemented

列出：

- LocalOwner schema
- bootstrap
- LocalOwnerContext
- legacy migration
- compatibility boundary

## Migration Evidence

分别报告：

```text
Fresh DB
Legacy Single Learner
Ambiguous Multi-Subject
Replay
```

## Acceptance Criteria

逐条：

```text
E047-AC-001 PASS/FAIL
...
E047-AC-007 PASS/FAIL
```

## Tests

列出实际执行命令和结果。

## Files Changed

列出所有修改文件。

## Security

明确报告：

- secret 是否参与 owner resolution；
- secret 是否出现在 logs/errors；
- 是否发生 destructive migration。

## Compatibility Residue

明确列出仍存在的：

```text
User
Auth
JWT
Session
Recovery
```

并注明它们属于 EXEC-048～050 后续处理，而不是 EXEC-047 遗漏。

## Governance

报告：

```text
EXEC-047 archived: YES/NO
EXEC-048 dependency unlocked: YES/NO
```

## Commit

报告 commit SHA。

***

# 最终执行原则

> **EXEC-047 的目标不是“删除登录”，而是先把“谁拥有本地学习数据”从 Authentication Identity 中彻底抽离，建立唯一、稳定、可迁移、可回放的 LocalOwner truth。**

> **先建立 ownership foundation，再在 EXEC-048～051 中逐步切断 Auth。不要跨阶段。**

