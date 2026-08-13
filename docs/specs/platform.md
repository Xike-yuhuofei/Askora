# Askora Local Identity and Privacy Lifecycle Specification

> Spec ID：`LID-*`  
> 状态：FROZEN  
> 版本：v2.0  
> Governing decision：ADR-0015  
> Supersedes：本文件 v1.0 `IDP-*` account/authentication contract

## 1. Scope

### LID-001 — Product Boundary

Askora 当前是 local single-user product。

Runtime MUST NOT require：

- login / register / logout；
- password / password recovery；
- JWT access/refresh token；
- AuthSession / token family；
- authentication device fingerprint；
- recovery credential / recovery kit；
- account deletion lifecycle。

Identity & Privacy 仍是平台横切边界，不是第九学习系统。

### LID-002 — Canonical Identity Truth

唯一 durable local identity truth 是：

```yaml
local_owner:
  owner_id: uuid
  schema_version: "1.0"
  created_at: datetime
```

`owner_id` 表示本地数据归属主体，不表示 credential principal。

### LID-003 — Learner Boundary

Learner/Profile/learning state MAY 使用 `owner_id` 作为 canonical subject key。

nickname、presentation preference、学习偏好属于 LearnerProfile / Settings，不属于 LocalOwner。

`LocalOwner` MUST NOT 保存 phone、email、password、token、recovery secret、wechat id、device fingerprint 等认证材料。

## 2. LocalOwner Lifecycle

### LID-010 — Bootstrap

App 启动 MUST 在任何 learner-owned query/command 前完成：

```text
load LocalOwner
OR
atomically create LocalOwner
→ expose LocalOwnerContext
```

首次创建不是 registration，不要求联网，不产生 token/session。

### LID-011 — Cardinality

一个 canonical local data store MUST 最多存在一个 active LocalOwner。

新空数据存储不存在 owner 时 MAY 原子创建一个 UUID。

### LID-012 — Stability

LocalOwner `owner_id` 在正常使用、App 重启、版本升级和普通数据导出期间 MUST 稳定。

browser fingerprint、machine id、process id、frontend storage key MUST NOT 替代 `owner_id`。

### LID-013 — Runtime Dependency

Canonical dependency：

```text
get_local_owner_context()
→ LocalOwnerContext(owner_id)
```

所有原 `get_current_user` business dependencies MUST 迁移到 LocalOwnerContext 或由它生成的 learner context。

兼容层 MAY 临时返回旧 `User` ORM projection，但：

- 不得验证 token；
- 不得创建 auth session；
- projection 必须唯一映射到同一个 LocalOwner；
- compatibility layer 必须有明确退役点。

## 3. Network Security Boundary

### LID-020 — Loopback Only

无认证 runtime MUST 只监听 loopback：

```text
127.0.0.1
::1
localhost-resolved loopback
```

`0.0.0.0`、LAN address、public interface MUST fail startup。

### LID-021 — Frontend Origins

CORS MUST explicit allowlist local frontend origins only。

不得因 single-user 模式使用 `*`。

### LID-022 — WebSocket Boundary

WebSocket MUST 使用与 HTTP 相同的 loopback/origin trust boundary，不得要求或接受 auth token 作为 owner identity。

### LID-023 — Remote Mode Prohibited

当前 no-auth profile MUST NOT 被宣称支持：

- LAN sharing；
- remote browser access；
- multi-device service；
- multi-user deployment。

未来新增上述能力 MUST 先通过新的 Canonical Design + ADR 重新定义 authentication。

## 4. Frontend Contract

### LID-030 — No Auth Shell

Frontend MUST 删除：

- `/login`；
- Login/Register/Recover UI；
- ProtectedRoute；
- AuthProvider / auth-only hooks；
- auth redirect；
- logout action。

App root MUST 直接进入 local bootstrap / product routing。

### LID-031 — No Token Storage

Frontend MUST NOT 持久化：

```text
access_token
refresh_token
auth session
current authenticated user cache
auth device fingerprint
```

普通非认证 UI preference 不受本条限制。

### LID-032 — API Client

Request interceptor MUST NOT 附加 `Authorization: Bearer ...`。

Response interceptor MUST NOT：

- refresh token；
- retry using rotated token；
- clear auth storage；
- redirect `/login`。

401 不再属于“session expired”产品语义。

## 5. Backend Contract

### LID-040 — Retired Routes

Production application MUST NOT register：

```text
/auth/*
account-login/recovery/session routes
dev auto-login
account deletion lifecycle routes
```

旧路径 MAY 返回 normal 404；不得保留隐藏自动登录 compatibility service。

### LID-041 — Retired Runtime Services

以下服务不得存在于 production request path：

- AuthService；
- TokenService；
- password verifier/hasher solely for account auth；
- auth session repository；
- recovery credential service；
- auth throttle service；
- account deletion runtime。

### LID-042 — Retired Configuration

认证退役后 production config MUST 删除或停止要求：

- JWT secret/algorithm/expiry；
- auth session timeout；
- dev auto-login flag；
- account deletion grace/polling config；
- auth-only secret validation。

### LID-043 — Business APIs

Documents、Goals、Workspace、Dialog、Onboarding、Data Control、Profile、Assessment/Planning 等 learner-owned APIs MUST 在无 Authorization header 下工作，并通过 LocalOwnerContext 确定唯一 subject。

## 6. Persistence and Migration

### LID-050 — Migration Order

认证移除 migration MUST 严格遵循：

```text
1. inventory existing learner subjects
2. resolve one LocalOwner
3. verify owner reference integrity
4. cut runtime to LocalOwnerContext
5. remove auth runtime/routes/config
6. remove auth-only schema/columns
7. validate replay/data-control integrity
```

MUST NOT 先 drop auth/user tables 再尝试恢复 ownership。

### LID-051 — Unique Legacy Subject

若 legacy datastore 可以唯一确定一个真实 learner subject：

- MUST 复用其稳定 UUID；或使用有记录、确定性的 canonical mapping；
- MUST 保留 documents/goals/dialogs/profiles/learning records/DecisionTrace ownership；
- MUST NOT 创建新的空 learner 取代旧数据。

### LID-052 — Ambiguous Legacy Subject

若存在多个无法安全区分/合并的真实 learner subjects：

- migration MUST fail closed；
- stable issue code：`LOCAL_OWNER_AMBIGUOUS`；
- MUST NOT 依据“最后登录”“最大数据量”或随机顺序静默选择；
- MUST NOT 删除未解析 subject 数据。

测试/demo fixture 可通过明确 fixture metadata 排除，不能靠名字猜测。

### LID-053 — Compatibility Columns

历史列名 `user_id` / `pseudonym_id` MAY 暂时保留以降低一次性 schema 风险，但它们的 canonical semantics MUST 是 LocalOwner/Learner ownership。

新实现不得再次引入 Account credential semantics。

### LID-054 — Auth Secret Erasure

LocalOwner migration 成功后，以下数据 SHOULD 被物理删除：

- password hashes；
- phone/email/wechat auth identifiers；
- access/refresh/session state；
- recovery secret digests；
- auth throttle state；
- authentication command receipts；
- account lifecycle-only state。

日志和 migration report MUST NOT 输出 secret material。

## 7. Data Control and Privacy

### LID-060 — Preserve Useful Data Governance

认证退役 MUST NOT 删除：

- user-readable/local data export；
- document erasure；
- learning-record erasure；
- model-execution erasure；
- owner-safe erasure workflow；
- recovery center；
- durable receipt/checkpoint/no-resurrection safety where applicable。

### LID-061 — No Account Deletion

产品/API MUST 不再使用 `DeleteAccount` 语义。

如果提供全量本地清除，canonical command 应是 `ResetLocalWorkspace` 或等价明确本地数据语义。

### LID-062 — Destructive Confirmation

危险数据删除仍 MUST：

1. 读取真实影响 preview；
2. 使用短时/版本化 preview；
3. 要求精确 typed confirmation；
4. 使用 idempotency key；
5. durable report/receipt；
6. fail closed on partial failure。

不得要求 current password，因为不存在 credential identity。

### LID-063 — Owner Preservation During Partial Erasure

普通 scoped erasure MUST 保留 LocalOwner identity，以保证剩余数据仍有稳定归属。

完整 workspace reset 若选择 rotate owner_id，必须在旧 owner 全量 erasure + no-resurrection checkpoint 完成之后创建新 owner，禁止两个 canonical owner 并存。

## 8. Settings and Onboarding

### LID-070 — Settings

Settings MUST 删除：

- 账号信息/状态；
- 手机号；
- 修改密码；
- session/device management；
- recovery kit；
- logout；
- delete account；
- JWT/session 安全说明。

Settings SHOULD 组织为：AI/模型、本地数据、存储与运行状态、错误恢复中心、隐私、关于。

### LID-071 — Onboarding

First-use journey：

```text
LocalOwner bootstrap
→ readiness
→ model/material/goal
→ first learning activity
```

不得依赖 register/login/recovery kit。

## 9. Error Contract

### LID-080 — Stable Local Identity Errors

至少冻结：

```text
LOCAL_OWNER_MISSING
LOCAL_OWNER_AMBIGUOUS
LOCAL_OWNER_MIGRATION_FAILED
LOCAL_NETWORK_BOUNDARY_VIOLATION
LOCAL_DATA_RESET_PARTIAL
```

正常新空 datastore 的 `LOCAL_OWNER_MISSING` 应由 bootstrap 原子创建解决，不应成为普通用户错误页。

## 10. Observability and Privacy

### LID-090

日志 MAY 记录最小必要 owner UUID/request id/operation id，但不得重新引入 phone/email/device fingerprint/token 等认证遥测。

### LID-091

移除 authentication 不得改变：

- TeachingAction；
- DecisionTrace policy inputs；
- learner mastery semantics；
- OutcomeObservation；
- experiment assignment；
- learning evidence hierarchy。

身份迁移只改变 ownership resolution，不改变教学决策 truth。

## 11. Acceptance Criteria

- `LID-AC-001`：冷启动无 Login，直接进入 local bootstrap/product flow。
- `LID-AC-002`：frontend bundle/runtime 不读写 access/refresh token。
- `LID-AC-003`：主要 learner-owned API 无 Authorization header 全部正常。
- `LID-AC-004`：`/auth/*`、dev auto-login、account deletion routes 未注册。
- `LID-AC-005`：backend 配置为 `0.0.0.0` 或非 loopback 地址时 startup fail closed。
- `LID-AC-006`：WebSocket 在合法 local origin 无 token 工作；非法 origin 被拒绝。
- `LID-AC-007`：legacy 单 learner migration 后关键 owner-owned records 数量/引用保持一致。
- `LID-AC-008`：multiple-real-subject fixture 返回 `LOCAL_OWNER_AMBIGUOUS` 且不执行 destructive cleanup。
- `LID-AC-009`：auth-only secret/session/recovery persistence 被删除或确认无 production references。
- `LID-AC-010`：Settings 无账号/密码/session/recovery/delete-account UI。
- `LID-AC-011`：data export、scoped erasure、Recovery Center 回归通过。
- `LID-AC-012`：DecisionTrace/replay/learning evidence 回归无语义变化。
- `LID-AC-013`：frontend test/build、backend pytest/ruff/mypy、migration tests、browser E2E 全部通过。

## 12. Release Gate

不得以以下方式声明完成：

- 只隐藏 Login 页面；
- 保留 AuthProvider 自动注入 demo token；
- 保留 JWT/session 但称为“本地身份”；
- 硬编码固定 demo user；
- 删除 `user_id` 导致历史学习数据脱离 owner；
- backend 可从 LAN/public interface 访问；
- 删除 data export/erasure/recovery safety 以简化实现。

Engineering 与 Policy/Ownership gate 必须 PASS。Learning Evidence 对本变更为 `NOT_APPLICABLE`；不得借本变更提高学习效果声明。

---

## Workspace / LearningProject / LearningSession Scope Contract

> Spec ID：`WSP-*`  
> 状态：**Canonical Implementation Contract / FROZEN**  
> 版本：v1.0  
> 冻结日期：2026-08-10  
> Governing：`docs/product/PRODUCT-POSITIONING.md`、ADR-0016  
> Linear：XIK-168

### 1. Purpose

本合同把 v1 已冻结的 `LocalOwner → Workspace → Material / LearningProject / LearningGoal / LearningSession` 产品模型转化为可直接实现、迁移和验收的持久化与应用边界。

它是 platform scope contract，不建立第九个 Learning Core system，不修改 SYS01～SYS08 的事实所有权，也不改变 v0.3 Teaching Policy。

### 2. Ownership

#### WSP-001 — Workspace Owner

`Workspace` 唯一 writer 为 **Platform Workspace Registry**。

Workspace Registry 只拥有 Workspace identity、metadata、default marker 与 lifecycle。它 MUST NOT 写 Material content、Goal semantics、LearnerState、TeachingAction、AssessmentResult 或 ReviewSchedule。

#### WSP-002 — LearningProject Owner

`LearningProject` 与 current `ProjectMaterial` membership 唯一 writer 为 **Platform Workspace / Product Organization**。

Project 只组织 canonical refs，不复制 Material/Goal truth。

#### WSP-003 — LearningSession Owner

`LearningSession` 唯一 writer 为 **Platform Learning Session Registry**。

它只拥有 continuous learning interval 的 scope/lifecycle envelope：Workspace、可选 Project/Goal/Material refs、start/end/status。

Transcript/message、TeachingAction、AssessmentResult、LearnerState、LearningPlan、ModelInference 分别继续由既有 owner 管理。

#### WSP-004 — No DialogSession Promotion

Legacy `DialogSession` MUST NOT 被原地改名或解释为 canonical LearningSession。

DialogSession MAY 保存 `workspace_id` 与可选 `learning_session_id` compatibility ref；无法可靠关联的历史 conversation MUST 保持 `learning_session_id = null`，不得猜测。

### 3. Canonical Objects

#### WSP-010 — Workspace

```yaml
workspace:
  workspace_id: uuid
  owner_id: uuid
  version: integer
  display_name: string
  is_default: boolean
  lifecycle: active|trash
  created_at: datetime
  updated_at: datetime
```

Rules:

- 每个 Workspace 属于唯一 LocalOwner；
- 一个 LocalOwner MAY 有多个 Workspace；
- 每个 datastore 在 migration/first bootstrap 完成后 MUST 有 exactly one active default Workspace；
- `display_name` 可修改，不参与 identity；
- `workspace_id` stable；rename MUST NOT change it；
- v1 本合同不要求实现 destructive Workspace Permanent Delete UI；如未来启用，必须先解决 child/reference/no-resurrection contract。

#### WSP-011 — LearningProject

```yaml
learning_project:
  project_id: uuid
  workspace_id: uuid
  version: integer
  title: string
  status: active|paused|archived
  created_at: datetime
  updated_at: datetime
```

Rules:

- Project 必须属于一个 Workspace；
- title MAY 重复，identity 只由 `project_id` 决定；
- status/version changes use optimistic concurrency；
- Project 不拥有 Material bytes/content，不拥有 Goal definition。

#### WSP-012 — ProjectMaterial

```yaml
project_material:
  project_id: uuid
  material_id: uuid
  created_at: datetime
```

Rules:

- `(project_id, material_id)` current membership MUST unique；
- Material 与 Project MUST 属于同一 Workspace；
- add/remove MUST idempotent；
- remove MAY physically delete the relationship row because membership itself is current organization state；
- relationship deletion MUST NOT delete Material/SourceFile or invalidate learning evidence by itself。

#### WSP-013 — LearningSession

```yaml
learning_session:
  session_id: uuid
  workspace_id: uuid
  project_id: uuid|null
  learning_goal_id: uuid|null
  status: active|ended|archived
  started_at: datetime
  ended_at: datetime|null
  created_at: datetime
  updated_at: datetime
```

Optional material context uses a normalized relation:

```yaml
learning_session_material:
  session_id: uuid
  material_id: uuid
  created_at: datetime
```

Rules:

- Session MUST belong to exactly one Workspace；
- Project/Goal/Material refs, when present, MUST belong to the same Workspace；
- Session MAY exist without Project or Goal；
- one active Session MAY span multiple interaction turns and evidence events；
- Session status MUST NOT encode mastery, teaching stage or activity completion；
- `ended_at` required when `status=ended`；archived is presentation/lifecycle state, not deletion。

### 4. Material and SourceFile Migration Boundary

#### WSP-020 — Stable Material Identity

Current `user_documents.id` MUST be adopted as the stable `material_id` compatibility identity for migrated v1 data.

Implementation MUST NOT introduce a parallel `materials` table that becomes a second current metadata/lifecycle truth while `user_documents` remains writable.

The ORM class/table MAY retain the legacy name during the compatibility window. Public/domain naming SHOULD move to Material.

#### WSP-021 — Workspace on Material

Current Material persistence MUST have a durable `workspace_id` column. After legacy backfill/cutover, migrated rows MUST be non-null.

New Material writers MAY create an **unassigned** Material with `workspace_id=null`（`EXP-JOURNEY-001` 上传只创建资料）。Unassigned Material：

- 拥有稳定 `material_id`；
- MUST NOT 被用来启动有依据的 LearningActivity；
- MUST NOT 作为某一 Workspace 的普通 retrieval 成员；
- MUST 通过 owner command 归属到某一 Workspace 之后，才能进入 `马上开始学习` / `继续学习` 的有依据学习。

归属 command（加入学习空间，或马上开始学习所触发的自动建空间）写入 exactly one `workspace_id`。v1 归属后不得用 frontend 改挂到另一 Workspace。

Assigned Material writers MUST require Workspace explicitly or derive it from an exact Workspace-scoped parent command。

#### WSP-022 — Normalized Managed SourceFile

Create normalized managed SourceFile persistence:

```yaml
source_file:
  source_file_id: uuid
  material_id: uuid
  checksum: string
  original_filename: string
  media_type: string|null
  size_bytes: integer
  managed_storage_ref: string
  created_at: datetime
```

Rules:

- Material `1:N` SourceFile；
- import backfill creates one primary SourceFile for each valid existing imported Material from the current managed path/checksum metadata；
- SourceFile belongs to Material and therefore exactly one Workspace；
- `managed_storage_ref` is internal and MUST NOT become a browser/public stable path API；
- storage file existence/hash validation MUST participate in migration verification；
- legacy `storage_path/original_filename/raw_asset_checksum/file_size_bytes` columns become compatibility read/audit after cutover and MUST have a retirement condition；
- permanent dual-write is forbidden。

#### WSP-023 — Existing SourceDocument / MaterialRevision

Existing SYS01 SourceDocument/MaterialRevision/SourceSpan records MUST resolve to Material by stable compatibility refs. New migrations MUST preserve existing revision/span IDs and provenance.

A table rename or ID rewrite is not required for XIK-171 and SHOULD NOT be performed unless it materially reduces risk.

### 5. Workspace Attribution Rules

#### WSP-030 — Direct Workspace Keys

Direct `workspace_id` MUST be persisted on records whose independent query/update could otherwise mix data across Workspaces.

At minimum:

- Material / LibraryTag / LibraryCollection / LibrarySearchProjection / LibraryCommandReceipt；
- LearningProject；
- LearningGoal aggregate/version/control records that are independently queried or written；
- LearningSession；
- LearnerEvidence；
- MasteryEstimate；
- LearnerState；
- ReviewSchedule current/versioned rows；
- local jobs tied to workspace-owned work。

#### WSP-031 — Parent-derived Workspace Is Allowed Only When Lossless

A child record MAY omit a duplicate workspace column only when all are true:

1. it has an immutable/non-null exact parent ref；
2. the parent has direct canonical `workspace_id`；
3. every read/write path validates through that parent；
4. no independent bulk query can cross Workspace without an explicit parent join/filter；
5. architecture tests prove the invariant。

If any condition fails, direct `workspace_id` is required.

#### WSP-032 — LearningGoal

All new LearningGoal definitions/state/drafts/objectives and independently queried control/evaluation rows MUST resolve exact Workspace.

Canonical Goal semantics:

```text
workspace_id = REQUIRED
project_id = OPTIONAL organization association
```

Project association MUST NOT be stored as part of immutable GoalDefinition semantics when changing the association does not change the learning goal itself. The current project association belongs to Goal state/organization binding and changing it creates a new current state/binding, not a new semantic definition.

#### WSP-033 — Learner Evidence and State

Learner evidence/mastery MUST be Workspace-specific.

```text
same LocalOwner + same KnowledgeUnit + different Workspace
≠ same MasteryEstimate stream
```

At minimum uniqueness/identity semantics MUST include Workspace for:

- LearnerEvidence acceptance scope；
- MasteryEstimate stream；
- LearnerState current/version stream；
- workspace-scoped ReviewSchedule where derived from that learning state。

Cross-workspace evidence fusion is forbidden in v1.

#### WSP-034 — Assessment and Decision Records

Attempt/AssessmentResult/TeachingAction/DecisionTrace/Outcome records MUST be attributable to one Workspace through exact Session/Activity/Goal/Material refs.

They MAY avoid duplicate workspace columns only when `WSP-031` is satisfied. Any new application entry that lacks a resolvable Workspace MUST fail closed before creating learning evidence or a TeachingAction.

#### WSP-035 — Knowledge / Retrieval Projections

KnowledgeUnit/SourceSpan/Chunk/index records generated from Material MUST remain attributable to the source Material Workspace. SYS02 retrieval cutover is governed by the separate Workspace-scoped Retrieval implementation issue; no owner-global cache/index may survive as a default v1 path.

### 6. Same-workspace Integrity

#### WSP-040 — ProjectMaterial Constraint

For any ProjectMaterial command:

```text
project.workspace_id == material.workspace_id
```

Otherwise reject before write.

#### WSP-041 — Goal Project Binding

When `project_id` exists:

```text
project.workspace_id == goal.workspace_id
```

Cross-workspace move MUST NOT be implemented as changing `workspace_id` in place. v1 does not define object move-between-workspaces; use explicit copy/import/recreate semantics in a future contract if needed.

#### WSP-042 — Session Scope

For Session refs:

```text
session.workspace_id == project.workspace_id   (if project)
session.workspace_id == goal.workspace_id      (if goal)
session.workspace_id == material.workspace_id  (for every material)
```

Mismatch rejects the command atomically.

#### WSP-043 — No Existence Leakage

Cross-workspace invalid refs MUST return the stable API/domain invalid-scope or not-found behavior selected by the public contract. Response MUST NOT reveal title, owner, project membership or other object metadata from another Workspace.

### 7. Default Workspace Bootstrap and Migration

#### WSP-050 — Bootstrap Preconditions

Workspace migration starts only after ADR-0015 LocalOwner foundation can resolve exactly one durable LocalOwner.

If LocalOwner is missing/ambiguous, startup/migration MUST fail closed; it MUST NOT create multiple owners/workspaces to guess around corrupted identity state.

#### WSP-051 — Default Workspace Depends on Migration State

ADR-0023 / `CWSP-*` amends the original unconditional first-use bootstrap：

- fresh LocalOwner with no legacy data MAY have zero Workspace/default/selection so Welcome empty state is real；
- legacy-data migration MUST ensure exactly one active default Workspace before backfill；
- first explicit Workspace create MUST create the first active default and current selection atomically；
- once any active Workspace exists, DB/application invariants MUST prevent multiple active defaults for the same owner。

Legacy default creation MUST remain idempotent. Rerunning migration resolves the existing default rather than creating a new row。Current selection is a separate Platform Workspace Registry fact governed by `CWSP-*`；`is_default` MUST NOT be used as switch state。

#### WSP-052 — Backfill Scope

All legacy active LocalOwner-global data that participates in current v1 behavior MUST be assigned to the default Workspace before Workspace becomes a required write/read filter.

At minimum migrate/backfill:

- UserDocument/Material and Library tags/collections/assignments/search projections/receipts/suggestions；
- current Goal management definitions/states/drafts/previews/focus/objectives/evaluations/plans/activities where applicable；
- legacy dialog/conversation records for isolation；
- LearnerEvidence/MasteryEstimate/LearnerState streams；
- ReviewSchedule；
- current operational jobs/receipts whose resource is Workspace-scoped；
- material-derived knowledge/index refs needed to enforce later retrieval scope。

#### WSP-053 — Legacy Dialog Migration

All legacy DialogSession records are assigned to the default Workspace for isolation.

A canonical LearningSession is created/backfilled only when the existing record has enough stable canonical refs to establish a real continuous learning activity without guessing. Otherwise DialogSession remains historical/compatibility transcript with `learning_session_id = null`.

#### WSP-054 — SourceFile Backfill

For each active/non-erased existing Material with a managed storage reference:

1. create exactly one normalized SourceFile row if none exists for the legacy primary file fingerprint；
2. preserve checksum/original filename/managed ref；
3. verify managed file availability/hash where practical；
4. do not copy the same file again merely for schema migration；
5. quarantined/failed Material keeps the SourceFile but retains its safety/status semantics。

Missing managed files become an explicit migration/recovery issue, not a silently invented SourceFile.

#### WSP-055 — Migration Phases

Required order:

```text
A. preflight LocalOwner + schema/recovery gate
B. create additive Workspace/Project/Session/SourceFile structures
C. add nullable workspace refs
D. create/resolve default Workspace
E. backfill Workspace refs + SourceFile
F. validate cardinality/FK/same-workspace/integrity
G. switch active writers
H. switch active readers / Library / learning entries
I. make required refs non-null/fail-closed where applicable
J. retire owner-global and embedded-file compatibility writers
```

Do not combine G/I before successful backfill validation.

#### WSP-056 — No Destructive Downgrade

Before writer cutover, additive migration MAY be rolled back if it can prove no new Workspace-aware writes exist.

After cutover or creation of more than one Workspace, a downgrade that collapses Workspace/Project/SourceFile identity is forbidden. Use forward-fix/rescue and current verified recovery point.

### 8. Writer / Reader Cutover

#### WSP-060 — Canonical Writer Cutover

After cutover, every creation/update command for Workspace-scoped business data MUST receive/resolve exact Workspace before owner application logic.

`LocalOwner` alone is not sufficient scope.

#### WSP-061 — Compatibility Endpoints

Legacy owner-global endpoints MAY temporarily adapt to **the canonical default Workspace only**.

They MUST NOT:

- query all Workspaces；
- create data without Workspace assignment；
- become a second writer；
- stay after active frontend/application readers have migrated and retirement tests pass。

#### WSP-062 — Idempotency Scope

Workspace-scoped command receipts SHOULD use:

```text
owner_id + workspace_id + command_type + idempotency_key
```

or an equivalent collision-safe scope. The same client key in two Workspaces MUST NOT accidentally return the other Workspace's receipt/result.

#### WSP-063 — Focus / Current Selection

Current UI-selected Workspace is durable application preference, not ownership truth。Its canonical owner/schema/version/idempotency contract is ADR-0023 / `CWSP-*`。Backend commands MUST still carry/resolve exact Workspace；browser local state、route与 `is_default` MUST NOT become selection truth。

### 9. API/Application Contract

#### WSP-070 — Canonical Workspace Routes

The Local Web API SHOULD expose a narrow canonical surface equivalent to:

```text
GET  /api/v1/workspaces
POST /api/v1/workspaces
GET  /api/v1/workspaces/{workspace_id}
PATCH /api/v1/workspaces/{workspace_id}

GET  /api/v1/workspaces/{workspace_id}/projects
POST /api/v1/workspaces/{workspace_id}/projects
GET  /api/v1/workspaces/{workspace_id}/projects/{project_id}
PATCH /api/v1/workspaces/{workspace_id}/projects/{project_id}
POST /api/v1/workspaces/{workspace_id}/projects/{project_id}/materials/{material_id}
DELETE /api/v1/workspaces/{workspace_id}/projects/{project_id}/materials/{material_id}
```

Exact route naming MAY preserve existing API conventions, but scope semantics are mandatory and schema-versioned.

Course list/create/current/switch and Course-scoped Activity projection use the additive ADR-0023 surface：

```text
GET  /api/v1/workspaces
POST /api/v1/workspaces
GET  /api/v1/workspaces/current
GET  /api/v1/workspaces/{workspace_id}
POST /api/v1/workspaces/{workspace_id}/switch
GET  /api/v1/workspaces/{workspace_id}/activities
```

These routes MUST obey `CWSP-*` and MUST NOT turn GET/deep-link resolution into a hidden command。

#### WSP-071 — Material / Goal / Session Commands

Material, Goal and Session create/write commands MUST include Workspace explicitly through route/body/application context.

Object-by-id reads/writes MUST validate Workspace before returning/mutating the object.

#### WSP-072 — LearningSession Commands

Minimum application commands:

```text
StartLearningSession
EndLearningSession
ArchiveLearningSession
AttachMaterialToLearningSession
DetachMaterialFromLearningSession
```

Start MUST pin Workspace and validate optional Project/Goal/Material refs. These commands only update Session scope/lifecycle; they MUST NOT write learning outcomes or transcript content.

#### WSP-073 — Retrieval Handoff

Every production retrieval request constructed from Workspace/Project/Session context MUST produce the canonical `RetrievalScope` with `workspace_id` required. XIK-172 performs the SYS02/API cutover; XIK-171 MUST provide the durable scope source needed by that work.

### 10. Configuration Scope

#### WSP-080

Application → Workspace → Project configuration inheritance MAY exist only for fields whose owning configuration contract explicitly marks them overrideable.

Workspace/Project rows MUST NOT store API Key/secret material.

### 11. Deletion and Lifecycle Boundaries

#### WSP-090 — Project Removal

Project archive or ProjectMaterial removal MUST NOT delete Material, LearningEvidence or SourceFile.

#### WSP-091 — Material Deletion

Material Trash/Permanent Delete follows `LIB-045/046`, `PERSIST-080..083` and XIK-170/174. Workspace/Project code MUST call those owner commands rather than deleting Material rows/files directly.

#### WSP-092 — Workspace Destruction Not in This Slice

XIK-171 does not implement Workspace Permanent Delete. No generic cascade delete from Workspace to child data is authorized by this contract.

### 12. Security / Privacy

#### WSP-100

Workspace is an isolation boundary inside the single LocalOwner datastore. It is not authentication, but every workspace-scoped query/write MUST filter/validate Workspace to prevent accidental cross-space mixing.

#### WSP-101

Logs/errors MUST NOT expose other Workspace object metadata on invalid refs. Internal managed paths remain sanitized according to security/data-control contracts.

### 13. Observability

At minimum record sanitized:

```text
workspace_id
project_id when relevant
learning_session_id when relevant
command/result code
migration phase/backfill counts
cross-workspace rejection reason code
correlation/idempotency refs
```

Do not log full document content, secret, raw learner response or private managed path merely to diagnose scope.

### 14. Required Tests

#### WSP-110 — Contract / Unit

- Workspace cardinality/default marker；
- ProjectMaterial same-workspace property；
- Goal→Project same-workspace；
- Session→Project/Goal/Material same-workspace；
- command idempotency by Workspace；
- no DialogSession→LearningSession implicit promotion。

#### WSP-111 — Migration

- fresh datastore bootstrap；
- representative LocalOwner-global legacy fixture；
- rerun migration/bootstrap；
- SourceFile backfill preserves Material ID and managed bytes；
- missing managed file explicit recovery issue；
- nullable→strict cutover only after validation；
- post-cutover forward-fix path。

#### WSP-112 — Isolation

Create Workspace A/B with overlapping titles/KU topics and prove:

- Material/tag/collection/Goal/Session queries remain isolated；
- Project A cannot attach Material B；
- Goal/Session A cannot bind Project/Material B；
- LearnerEvidence from A cannot change Mastery/LearnerState in B；
- default compatibility endpoint never aggregates A+B。

#### WSP-113 — Architecture

- one Workspace writer；
- one ProjectMaterial writer；
- one LearningSession writer；
- no UI/localStorage Workspace truth；
- no cross-owner repository writes；
- no second Material truth；
- DialogSession legacy mastery/strategy fields do not feed canonical learner/policy state。

### 15. Acceptance Criteria

- `WSP-AC-001`：fresh local datastore has exactly one LocalOwner and may have zero Workspace until explicit Course create；legacy-data migration has exactly one active default Workspace before backfill.
- `WSP-AC-002`：existing stable Material IDs survive migration.
- `WSP-AC-003`：each migrated valid Material has canonical Workspace and normalized managed SourceFile identity.
- `WSP-AC-004`：one Material can belong to multiple Projects in the same Workspace; cross-workspace membership is impossible.
- `WSP-AC-005`：Goal is Workspace-required and Project-optional without rewriting immutable definition merely for organization changes.
- `WSP-AC-006`：LearningSession is Workspace-required, Project/Goal-optional and not a transcript/teaching/mastery owner.
- `WSP-AC-007`：historical DialogSession can remain unbound; no guessed LearningSession is created.
- `WSP-AC-008`：LearnerEvidence/MasteryEstimate/LearnerState streams are Workspace-specific and cannot mix.
- `WSP-AC-009`：owner-global compatibility endpoints resolve only default Workspace and have explicit retirement tests.
- `WSP-AC-010`：migration is idempotent, additive-first, verified on SQLite and has a non-destructive forward-fix/recovery path.
- `WSP-AC-011`：Workspace Permanent Delete/cascade is not accidentally introduced.
- `WSP-AC-012`：no second Material truth or permanent SourceFile dual-write exists.

### 16. Forbidden Implementations

禁止：

- 只在 frontend 增加 Workspace selector 而后端仍 owner-global；
- 用 LocalOwner 当 RetrievalScope；
- `workspace_id` 只存 JSON payload、没有 relational/application integrity；
- duplicate `materials` + writable `user_documents` current truths；
- 把 DialogSession 当 canonical LearningSession；
- LearningSession 写 mastery/TeachingAction/AssessmentResult；
- Project 拷贝 Material 内容形成第二资料 truth；
- cross-workspace ProjectMaterial/Goal/Session refs；
- owner-global compatibility endpoint 聚合全部 Workspace；
- migration 未验证就将 workspace refs 设 strict；
- downgrade 丢失多 Workspace/Project/SourceFile identity；
- Workspace cascade delete child data；
- browser localStorage 作为唯一 current Workspace truth。
- `Workspace.is_default` 或 route 作为 current selection truth；
- fresh empty owner 在 query/startup 时被隐式创建默认 Course。

### 17. Freeze Result

`WSP-*`：**FROZEN / READY_FOR_EXEC_DECOMPOSITION**；Course selection/default-bootstrap amendment 由 ADR-0023 / `CWSP-*` 优先。

XIK-171 MAY 在本合同下实现 Workspace/Project/Session/SourceFile persistence and migration。Workspace-scoped SYS02 retrieval cutover remains XIK-172。Learner evidence/state schema work MAY be split into a dedicated implementation issue if keeping XIK-171 narrow improves verification, but it MUST complete before Product Positioning Conformance can pass。

---

## Course / Workspace Selection and Activity Projection Contract

> Spec ID：`CWSP-*`
> 状态：Canonical Implementation Contract / Frozen
> 版本：v1.0
> Governing：ADR-0016、ADR-0019、ADR-0022、ADR-0023

### 1. Scope and Ownership

#### CWSP-001 — Single Writer

Platform Workspace Registry 是以下事实的唯一 writer：

- Workspace list/get/create metadata；
- owner-scoped `WorkspaceSelection.current_workspace_id`；
- selection version；
- create/switch idempotency receipts。

UI、route、localStorage、React state、Workspace read assembler、LearningSession、SYS06、LLM 均不得成为第二 writer。

#### CWSP-002 — Owner Boundaries Remain

- Workspace / WorkspaceSelection → Platform Workspace Registry；
- LearningActivity / Plan → SYS06；
- LearningSession interval/scope → Platform Learning Session Registry；
- Material、UserNote、Transcript、Attempt、LearnerState、TeachingAction、ReviewSchedule owner 不变。

Course 是 user-facing vocabulary，不新增 Course table、`course_id` 或第二 DTO identity。

#### CWSP-003 — Non-goals

本合同不授权 Workspace delete/cascade、跨 Workspace move/copy、LearningProject=Course、Goal/Plan editing、Teaching Policy/Mastery/Review 变化或前端实现。

### 2. Durable State

#### CWSP-010 — WorkspaceSelectionV1

```yaml
workspace_selection_v1:
  owner_id: uuid
  version: integer >= 1
  current_workspace_id: uuid
  reason: FIRST_CREATE|LEGACY_MIGRATION|EXPLICIT_SWITCH|RECOVERY_RECONCILIATION
  previous_workspace_id: uuid|null
  correlation_id: uuid
  updated_at: datetime
```

`owner_id` 唯一；version 单调递增。current target MUST 属于同一 owner 且 `lifecycle=active`。selection 是 application preference，不改变 Workspace ownership/default/lifecycle。

#### CWSP-011 — Empty / Default / Current Cardinality

| Owner state | Active Workspace | Active default | Selection |
|---|---:|---:|---:|
| fresh、无 legacy data | 0 | 0 | 0 |
| first Course create 后 | ≥1 | exactly 1 | exactly 1 |
| legacy migration 后 | ≥1 | exactly 1 | exactly 1 |

active Workspace 存在时最多一个 active default。current MAY 与 default 不同。不得用 `is_default` 更新冒充 switch。

#### CWSP-012 — Command Receipt

```yaml
workspace_command_receipt_v1:
  receipt_id: uuid
  owner_id: uuid
  command_type: CREATE_WORKSPACE|SWITCH_WORKSPACE
  idempotency_key: string
  command_digest: string
  response_payload: object
  created_at: datetime
```

唯一性至少为 `(owner_id, command_type, idempotency_key)`。相同 key + 相同 digest 返回原结果；相同 key + 不同 digest 返回 `WORKSPACE_IDEMPOTENCY_CONFLICT`。

### 3. Public Schemas

所有 schema strict、`schema_version="1.0"`，拒绝 unknown major。

#### CWSP-020 — WorkspaceItemV1

```yaml
workspace_item_v1:
  workspace_id: uuid
  workspace_ref: versioned_ref
  display_name: string
  version: integer >= 1
  lifecycle: active|trash
  is_default: boolean
  is_current: boolean
  created_at: datetime
  updated_at: datetime
```

#### CWSP-021 — WorkspaceListResponseV1

```yaml
workspace_list_response_v1:
  schema_version: "1.0"
  generated_at: datetime
  data:
    view_state: EMPTY|READY|STALE
    selection_version: integer|null
    current_workspace_id: uuid|null
    workspaces: [WorkspaceItemV1]
  correlation_id: uuid
```

排序固定为：current first；其余 `updated_at DESC, created_at ASC, workspace_id ASC`。`EMPTY` 必须是真实 0 Workspace/0 selection；不得 query 时 bootstrap。

Default list includes active Workspaces only。Trash lifecycle is returned only by an explicit lifecycle-management/recovery query authorized by its owner contract；the Course sidebar MUST NOT expose trash as a normal Course candidate。

#### CWSP-022 — WorkspaceGetResponseV1

显式 get 必须返回 owner 内 exact WorkspaceItemV1。foreign/inaccessible 与不存在使用同一不可枚举错误；get 不写 selection。

#### CWSP-023 — WorkspaceTransitionGuardV1

```yaml
workspace_transition_guard_v1:
  schema_version: "1.0"
  composer_draft: CLEAR|PRESERVED|DISCARD_CONFIRMED|UNRESOLVED
  stream: CLEAR|BACKGROUND_SAFE|CANCEL_CONFIRMED|UNRESOLVED
  user_note: CLEAR|SAVED|PRESERVED|DISCARD_CONFIRMED|UNRESOLVED
  material_position: PRESERVED|DISCARD_CONFIRMED|UNRESOLVED
  source_refs: [versioned_ref]
```

任何 `UNRESOLVED` 必须在写入前返回 recovery required。`DISCARD_CONFIRMED` 只确认 presentation/transient work；不得删除 durable owner data。frontend 必须从真实页面 state 构造 guard，测试证明不能固定伪报 `CLEAR`。

#### CWSP-024 — CreateWorkspaceV1

```yaml
create_workspace_v1:
  schema_version: "1.0"
  display_name: string
  expected_selection_version: integer|null
  transition_guard: WorkspaceTransitionGuardV1
  idempotency_key: string
```

名称 trim 后 1..120 字符，不允许 control character。fresh create 要求 `expected_selection_version=null`；已有 selection 要求 exact version。

#### CWSP-025 — SwitchWorkspaceV1

```yaml
switch_workspace_v1:
  schema_version: "1.0"
  target_workspace_id: uuid
  expected_selection_version: integer
  transition_guard: WorkspaceTransitionGuardV1
  idempotency_key: string
```

客户端不得提交 owner_id、source_workspace_id、target lifecycle、selection target status 或任何 learning state mutation。

#### CWSP-026 — WorkspaceMutationResultV1

```yaml
workspace_mutation_result_v1:
  schema_version: "1.0"
  outcome: CREATED_AND_SELECTED|SWITCHED|ALREADY_CURRENT|RECOVERY_REQUIRED
  workspace: WorkspaceItemV1|null
  selection_ref: versioned_ref|null
  selection_version: integer|null
  preserved:
    activity_refs: [versioned_ref]
    learning_session_refs: [versioned_ref]
    workflow_run_refs: [versioned_ref]
    note_refs: [versioned_ref]
  blockers: [WorkspaceSwitchBlockerV1]
  correlation_id: uuid
```

`RECOVERY_REQUIRED` 不得伴随 Workspace/selection write。`ALREADY_CURRENT` 为成功幂等结果，不增加 selection version。

#### CWSP-027 — WorkspaceSwitchBlockerV1

```yaml
workspace_switch_blocker_v1:
  kind: COMPOSER_DRAFT|STREAM|USER_NOTE|LEARNING_SESSION|MATERIAL_POSITION
  source_ref: versioned_ref|null
  owner: FRONTEND_PRESENTATION|PLATFORM_SESSION|SYS08|USER_NOTE_OWNER
  allowed_actions: [PRESERVE|SAVE|BACKGROUND|CANCEL|DISCARD|RETURN]
  reason_code: string
```

不返回内容正文、Prompt、other-Workspace metadata 或内部路径。

### 4. Commands and Transactions

#### CWSP-030 — Create-and-select Atomicity

Create 成功必须在一个事务内创建 Workspace、必要的 first-default marker、new selection version、receipt/outbox。任一步失败全部回滚。不得创建 Workspace 后靠 frontend 第二次 switch 补齐。

Create 只证明 Workspace 已创建并选中；Material/Goal/Plan/Activity readiness 保持独立 owner result。

#### CWSP-031 — Switch Atomicity

Switch 顺序：

```text
resolve LocalOwner
→ load current selection FOR UPDATE / equivalent CAS
→ validate expected version
→ resolve target in same owner without existence leakage
→ validate active lifecycle
→ evaluate transition guard + server-known durable/in-flight refs
→ append new selection version + receipt
→ commit
```

不得在 selection commit 前后隐式写其他 owner state。

#### CWSP-032 — Preservation Semantics

| Work | Required behavior |
|---|---|
| composer draft | per-Workspace preserve or explicit discard confirmation |
| streaming run | background/reconnect or explicit cancel；switch does not duplicate completion |
| UserNote | accepted ADR-0021 / `UNSI-*` save/version receipt or preserve/explicit discard；conflict remains owner error |
| active LearningSession | remains source-Workspace scoped；never auto-end；return resumable ref |
| Material tabs/position | preserve keyed by workspace+material or explicit discard |

Server-known source Session/Activity/run refs必须从 owner query读取，不能从 client title/free text 推断。前端 transient safety 与后端 canonical mutation是双层 gate；任何一层 unresolved 都不得显示 switched success。

#### CWSP-033 — Concurrency

stale expected selection version 返回 `WORKSPACE_SELECTION_VERSION_CONFLICT`，包含 current selection version/ref（不含 foreign metadata）。客户端 re-query 后由用户重新确认；不得 blind overwrite/auto retry stale command。

#### CWSP-034 — No Hidden Writes

GET/list/current/activity projection、route resolution、redirect、reload、browser back/forward、deep link validation 全部 side-effect free。不得创建 Workspace/selection/Activity/Session/receipt。

### 5. API Surface

#### CWSP-040 — Canonical Routes

```text
GET  /api/v1/workspaces
POST /api/v1/workspaces
GET  /api/v1/workspaces/current
GET  /api/v1/workspaces/{workspace_id}
POST /api/v1/workspaces/{workspace_id}/switch
GET  /api/v1/workspaces/{workspace_id}/activities
```

`GET /api/v1/workspace/context` 在迁移期适配 current selection；不得继续硬编码 default，也不得聚合全部 Workspace。写 response 使用 `private, no-store`；create/switch 必须携带 idempotency key 与 expected version。

#### CWSP-041 — Explicit Scope

所有 Workspace 子资源请求以 route scope 为 hard filter。`/workspace/**` legacy routes只可解析 current selection；selection missing 时返回 typed missing，不得自动创建 default。

#### CWSP-042 — Deep-link Resolution

Course deep link先 owner-safe get，再加载目标 Course view；与 current selection 不同也可只读展示目标，但 UI 必须标明尚未显式切换，任何写 command 继续携带 exact route Workspace。产品主路径中的 Course item Action 应先 switch success，再 navigation。

### 6. Course-scoped Activity Projection

#### CWSP-050 — WorkspaceActivityIndexResponseV1

```yaml
workspace_activity_index_response_v1:
  schema_version: "1.0"
  generated_at: datetime
  data:
    view_state: EMPTY|READY|PARTIAL|STALE
    workspace_ref: versioned_ref
    resumable_activity_ref: versioned_ref|null
    activities:
      - activity_ref: versioned_ref
        lifecycle_state_ref: versioned_ref
        plan_ref: versioned_ref
        goal_ref: versioned_ref
        display_title: string
        title_source_ref: versioned_ref
        activity_type: string
        status: planned|available|active|completed|skipped|superseded
        launch_state: RESUMABLE|REQUIRES_START_COMMAND|UNAVAILABLE
        latest_transition_at: datetime
        learning_session_refs: [versioned_ref]
    reason_codes: [string]
  source_status: [source_status]
  correlation_id: uuid
```

#### CWSP-051 — Exact SYS06 Source

每项必须通过：

```text
Workspace
← exact LearningGoal.workspace_id
← exact current LearningPlan.learning_goal_id
← immutable LearningActivity.plan_id+plan_version
← latest LearningActivityStateV1
```

任一链不完整、ambiguous、foreign、superseded plan mismatch 时 fail closed或诚实 PARTIAL/STALE；不得用 dialog session、transcript recency、route、title 或 frontend cache补齐。

#### CWSP-052 — Ordering and Resume

- `active` first，按 `started_at DESC, activity_id ASC`；
- `available` next，保持 plan order，activity id tie-break；
- 其余 recent items按 `latest_transition_at DESC, activity_id ASC`；
- `resumable_activity_ref` 只可指向同 Workspace current-plan latest `active`；
- 多个 active 若违反 current invariant，返回 `PARTIAL + MULTIPLE_ACTIVE_ACTIVITIES`，不得任意选择；
- `available` 必须调用 SYS06 start command，不得 GET/navigation 自动 start。

#### CWSP-053 — Title Boundary

`display_title` 使用 LearningActivity typed semantics 与 versioned presentation catalog。Conversation/Dialog title 不得成为 Activity name；LLM 不得在 query 时生成 title。未来 durable user-edited Activity title 需 SYS06 新合同。

#### CWSP-054 — LearningSession Link

new Activity-scoped LearningSession MUST pin `learning_activity_id` and validate activity/goal/project/material are same Workspace。Session link不改变 lifecycle；resume projection只返回 exact valid active/ended session refs，不复制 transcript。

### 7. Stable Errors and Retry

#### CWSP-060 — Codes

```text
WORKSPACE_NOT_FOUND_OR_INACCESSIBLE
WORKSPACE_SELECTION_MISSING
WORKSPACE_SELECTION_VERSION_CONFLICT
WORKSPACE_IDEMPOTENCY_CONFLICT
WORKSPACE_SWITCH_RECOVERY_REQUIRED
WORKSPACE_NAME_INVALID
WORKSPACE_SCHEMA_UNSUPPORTED
WORKSPACE_INTEGRITY_FAILED
WORKSPACE_ACTIVITY_SCOPE_VIOLATION
WORKSPACE_ACTIVITY_PROJECTION_UNAVAILABLE
```

- validation/business/conflict/not-found/security errors non-retryable without changed input/re-query；
- transient DB/projection dependency MAY retry bounded；
- retry必须复用 idempotency key；
- provider/session failure不得写 learner failure或 selection success。

### 8. Migration / Rollback / Forward-fix

#### CWSP-070 — Additive Migration

1. add WorkspaceSelection + Workspace command receipt structures；
2. add nullable `learning_sessions.learning_activity_id`；
3. classify owner：fresh-empty vs legacy-data/existing Workspace；
4. fresh-empty 保持 0 Workspace/selection；
5. legacy-data 幂等 create/resolve default + backfill + selection；
6. existing Workspace missing selection → select active default deterministically；
7. validate owner/target/cardinality/FK；
8. cut over current readers；
9. enable create/switch writers；
10. enforce strict new Session activity link at application boundary。

不得从 filename/title/most-recent timestamp猜测 Workspace/Activity。旧 Session 无 exact activity proof 时保持 nullable compatibility并给 reason code。

#### CWSP-071 — Rollback

writer cutover 前且无新 selection/create writes时可回滚 additive schema。writer cutover、多个 Workspace 或 selection version > 1 后禁止 destructive downgrade；使用 forward-fix、reconciliation 与 verified recovery point。

### 9. Security / Privacy / Observability

#### CWSP-080

Workspace 是 LocalOwner 内隔离边界，不是 auth role。所有 query/write必须同时验证 owner + Workspace；foreign ref与不存在不可枚举。response/log不暴露 other-Workspace name、Activity title、note/transcript/content、secret或local path。

#### CWSP-081

sanitized telemetry至少：`workspace_id`、source/target selection version、command/result/error code、correlation/idempotency/receipt ref、activity/session ref（适用时）。不得记录 transition guard正文或用户内容。

### 10. Required Tests

#### CWSP-090 — Contract / Architecture

- strict v1 / unknown major；
- one Platform writer；no UI/localStorage/default-marker truth；
- API transport-only；Activity assembler read-only；
- command digest/idempotency/version；
- no hidden write on GET/route/refresh/retry。

#### CWSP-091 — Persistence / Migration

- fresh SQLite owner remains 0 Workspace；
- legacy fixture gets exactly one default + selection；
- rerun migration；
- existing single/multiple Workspace missing selection；
- create-and-select atomic rollback；
- upgraded fixture与 fresh `alembic upgrade head`；
- `alembic check` single head；
- PostgreSQL constraints where CI available；
- post-cutover forward-fix。

#### CWSP-092 — Isolation / Recovery

- owner A/B and Workspace A/B list/get/switch isolation；
- foreign ids return same non-enumerable error；
- stale version/no write；
- same/different idempotency digest；
- every transition guard blocker；
- active Session/run/note/material position preserved；
- cross-Workspace Activity/Session chain rejected；
- no negative LearningEvidence on infrastructure failure。

#### CWSP-093 — Activity Projection

- exact goal/plan/activity/lifecycle refs；
- stable grouping/order/tie-break；
- multiple active → PARTIAL；
- available is not auto-started；
- superseded/foreign/ambiguous chains fail closed；
- title catalog versioned、no chat/LLM inference；
- refresh deterministic/no write。

### 11. Acceptance Criteria

- `CWSP-AC-001`：fresh owner真实返回 Welcome empty / zero-Workspace 基础事实，不隐式创建 Workspace。
- `CWSP-AC-002`：legacy data幂等归属 exactly one default Workspace + selection。
- `CWSP-AC-003`：current selection只有 Platform Registry writer，与 default marker分离。
- `CWSP-AC-004`：create-and-select原子、versioned、idempotent，无半成品 Course。
- `CWSP-AC-005`：switch unresolved work不写 selection、不静默丢 draft/stream/note/session/material position。
- `CWSP-AC-006`：deep link/route/read/refresh无 business side effect。
- `CWSP-AC-007`：foreign Workspace/Activity ref fail closed且不可枚举。
- `CWSP-AC-008`：Activity projection只组合 exact SYS06 refs，不形成第二 Activity truth。
- `CWSP-AC-009`：active Activity可恢复、available Activity只经 SYS06 start command启动。
- `CWSP-AC-010`：new Activity-scoped Session pin exact activity；legacy不猜测 backfill。
- `CWSP-AC-011`：migration/rollback/forward-fix与 SQLite/PostgreSQL verification完整。
- `CWSP-AC-012`：Product/UX/Engineering/Quality/Learning Evidence分别报告；工程 PASS 不声称真人学习有效。

### 12. Forbidden Implementations

禁止：browser/route/default marker作为 current truth；GET/redirect自动 switch/create/start；create 与 select非原子；switch静默取消/丢弃 work；foreign existence leakage；owner-global list；Activity title来自 chat/LLM；Activity projection写 SYS06；Session 自动完成 Activity；跨 Workspace refs；destructive downgrade；用 mock Course 声称真实能力可用。

---

## Local SecretStore and Model Configuration Activation Contract

> Spec ID：`LSS-*`  
> 状态：**Canonical Implementation Contract / FROZEN**  
> 版本：v1.0  
> 冻结日期：2026-08-10  
> Governing：`docs/product/PRODUCT-POSITIONING.md`、ADR-0017、`MODEL-CONFIG-*`  
> Linear：XIK-169

### 1. Purpose

本合同冻结 Askora v1 Local Web BYOK 的 production secret persistence、backend selection、secret reference、activation journal、crash recovery 和 clear/restore 行为。

它只实现 `LocalSecretStore` infrastructure + SYS08 model-configuration application boundary，不建立新的 routing owner，不允许 browser/SQLite/Workspace/Project 保存 API Key。

### 2. Production Backend

#### LSS-001 — Supported Production Platforms

v1 production-local persistent secrets support:

```text
Darwin  → keyring.backends.macOS.Keyring
Windows → keyring.backends.Windows.WinVaultKeyring
```

Other platforms are `UNSUPPORTED` for persistent BYOK under this v1 contract unless a later accepted ADR/Spec adds another OS-backed adapter.

#### LSS-002 — Explicit Backend Selection

Application startup MUST construct/select the expected built-in backend directly and verify exact approved backend identity before use.

MUST NOT rely on `keyring.get_keyring()` automatic discovery as the security decision.

#### LSS-003 — Override Rejection

Production-local MUST NOT allow these mechanisms to replace the approved backend:

- `PYTHON_KEYRING_BACKEND`；
- user `keyringrc.cfg` backend selection；
- `keyring-path` injected third-party backend；
- `KEYRING_PROPERTY_*` values that redirect storage away from the approved default OS credential store；
- `KEYCHAIN_PATH` or equivalent alternate-store override unless a later explicit migration/recovery contract approves it。

If such environment/config exists, Askora MUST still explicitly instantiate its approved backend or fail closed; it MUST NOT silently honor the override for API-key persistence.

#### LSS-004 — Disallowed Backends

Production MUST reject Null, file/plaintext, third-party, chainer-to-unapproved and unknown backend implementations.

`recommended` or non-zero priority alone is insufficient evidence of approval.

#### LSS-005 — Windows Local-machine Persistence

Windows production adapter MUST set `WinVaultKeyring.persist = "local machine"` or the exact library-equivalent `CRED_PERSIST_LOCAL_MACHINE` before writing Askora credentials.

It MUST NOT use the backend's enterprise persistence default.

#### LSS-006 — Dependency Governance

`keyring` and required platform binding dependencies MUST be pinned/locked in the repository dependency lock.

Upgrade MUST run LocalSecretStore contract/security tests; a dependency update MUST NOT silently broaden the production backend allowlist.

### 3. LocalSecretStore Port

#### LSS-010 — Internal Port

Required semantic interface:

```text
capability() -> AVAILABLE | LOCKED | UNAVAILABLE | UNSUPPORTED
put(secret_ref, secret_value)
get(secret_ref) -> secret_value | NOT_FOUND | LOCKED | ERROR
delete(secret_ref) -> DELETED | NOT_FOUND | LOCKED | ERROR
```

Implementation MAY use richer typed results, but semantics must remain explicit.

#### LSS-011 — Access Boundary

Only SYS08 model-configuration/runtime application code MAY resolve `get(secret_ref)`.

Browser/public API, SYS01～SYS07, UI read model, analytics and export code MUST NOT have a secret-read capability.

#### LSS-012 — No Enumeration Contract

The canonical LocalSecretStore port MUST NOT require listing all stored secrets. Cleanup/reconciliation uses exact secret refs from durable activation operations/profile history.

An adapter MAY use private enumeration only when necessary for verified recovery, but enumeration results MUST NOT leave the infrastructure boundary.

### 4. Secret Identity

#### LSS-020 — Namespace

Production credentials use:

```text
service_name = "askora.local-model-secret.v1"
username/account = secret_ref UUID string
secret value = provider API key/token
```

#### LSS-021 — Opaque Reference

`secret_ref` MUST:

- be random/unguessable-enough UUID identity generated by Askora；
- contain no API-key fragment；
- contain no provider/model/routing semantics；
- remain backend-internal and absent from ordinary public profile summaries/logs/exports/diagnostics。

#### LSS-022 — Multiple Provider Credentials

The store MAY hold multiple active secret refs because task routes MAY use more than one provider.

`ModelRouteProfileV1` owns which credential binding is used by each configured provider/route. SecretStore presence alone NEVER activates a provider.

### 5. Browser and API Boundary

#### LSS-030 — Candidate Secret Input

Browser MAY submit a candidate key only in the write command body over the loopback Local Web boundary.

Frontend MUST NOT place the candidate key in URL/query params, localStorage, sessionStorage, IndexedDB, durable Redux/query cache, analytics or crash-report payloads.

#### LSS-031 — No Secret Readback

No API route may return a stored API key, secret ref, key fragment, fingerprint or reversible secret representation.

Settings displays only configured/verified/degraded state.

#### LSS-032 — Request Handling

Secret-bearing request bodies MUST NOT be copied into request logs, tracing attributes, generic error context, retry payload persistence or diagnostics.

Application code SHOULD minimize lifetime of plaintext candidate values and drop references after operation completion/failure.

### 6. Durable Activation Operation

#### LSS-040 — Journal Is Required

Every model apply/clear MUST create a durable SQLite operation before external/secret-store side effects.

Minimum fields:

```yaml
operation_id: uuid
operation_type: APPLY|CLEAR
expected_profile_revision: integer|null
prior_profile_ref: versioned_ref|null
candidate_profile_fingerprint: string|null
candidate_secret_refs: [uuid]
phase: PREPARED|PROBE_VERIFIED|SECRET_STORED|PROFILE_COMMITTED|RUNTIME_VERIFIED|COMPLETED|ROLLING_BACK|FAILED
idempotency_key: string
error_code: string|null
created_at: datetime
updated_at: datetime
```

#### LSS-041 — Journal Contains No Secret

Operation payload MUST NOT contain:

- API key/token；
- Authorization/header；
- encrypted/ciphertext copy of the key；
- provider raw request/response body；
- any value from which the key can be reconstructed。

#### LSS-042 — Idempotency

Operation idempotency scope MUST include model-config command type + canonical LocalOwner/application scope + idempotency key.

Repeating a completed operation returns the same non-sensitive result and MUST NOT repeat probe, secret write/delete or profile activation.

### 7. Apply State Machine

#### LSS-050 — Apply Order

Canonical order:

```text
1 validate schema / expected revision / command fingerprint
2 persist PREPARED operation
3 probe candidate using in-memory credential
4 persist PROBE_VERIFIED
5 persist candidate secret(s) in LocalSecretStore
6 persist SECRET_STORED
7 publish + atomically switch active ModelRouteProfile revision in SQLite
8 persist PROFILE_COMMITTED in that SQLite transaction where practical
9 refresh runtime from exact active revision and secret binding
10 verify exact runtime revision/readiness
11 persist RUNTIME_VERIFIED then COMPLETED
12 retire superseded secret refs only after completed activation
```

#### LSS-051 — Probe Failure

Probe failure MUST:

- not create a new persistent secret；
- not switch active profile；
- persist only sanitized failure metadata/reason code；
- preserve prior active configuration exactly。

#### LSS-052 — Reuse Existing Credential

A configuration edit MAY reuse an existing secret internally when:

- current active profile already has a valid binding；
- provider identity for that binding is unchanged；
- command explicitly requests reuse or UI semantics unambiguously mean “keep saved credential”；
- browser never receives the key。

Changing to a provider with no existing binding requires a replacement candidate secret.

#### LSS-053 — New Secret Retirement

A superseded prior secret MUST NOT be deleted before the new active profile is runtime-verified.

After successful completion, unreferenced prior secrets SHOULD be deleted. Deletion failure becomes a recoverable orphan-secret issue without reverting the active routing truth.

### 8. Clear / Disable State Machine

#### LSS-060 — Clear Order

Canonical clear:

```text
validate expected revision + confirmation + idempotency
→ PREPARED journal
→ publish DISABLED/UNCONFIGURED profile revision
→ refresh runtime so no prior secret is routable
→ delete retired secret refs
→ verify disabled runtime
→ COMPLETED
```

#### LSS-061 — Secret Deletion Failure

If old secret deletion fails after disabled profile commit:

- canonical routing remains DISABLED/UNCONFIGURED；
- secret is classified as orphan cleanup work；
- UI/API may report cleanup/recovery issue without exposing secret ref/material；
- system MUST NOT reactivate the old provider。

### 9. Startup Recovery

#### LSS-070 — Reconcile Before Ready

Incomplete model-config operations MUST be reconciled before model configuration reports `runtime_ready=true`.

#### LSS-071 — Pre-commit Phases

`PREPARED|PROBE_VERIFIED` with no secret/profile side effect MAY be marked interrupted/failed and safely retried by a new idempotent command.

`SECRET_STORED` without profile commit MUST preserve prior profile and delete candidate orphan secrets when exact ownership is provable.

#### LSS-072 — Post-profile Commit Recovery

For `PROFILE_COMMITTED` without runtime verification:

1. load exact active profile revision；
2. resolve its exact approved secret binding；
3. refresh/verify runtime；
4. if successful, complete operation；
5. if unsuccessful, restore exact prior active profile when reconstructible；
6. only after durable rollback delete candidate secret(s)。

If prior/candidate state cannot be proven, enter `DEGRADED` and surface stable recovery action. No environment fallback is allowed.

#### LSS-073 — Orphan Cleanup Safety

A secret MAY be deleted as orphan only when no current/historical recovery-needed profile or incomplete operation references it.

Ambiguous reference state fails closed and keeps the secret until explicit recovery/repair.

### 10. Runtime Secret Resolution

#### LSS-080

Provider adapters receive plaintext API key only from the internal runtime/application resolution path and only for the duration necessary for provider calls/configuration.

#### LSS-081

Provider/router singleton/global state MUST NOT cache a stale key indefinitely across profile revision changes. Runtime refresh must bind exact `ModelRouteProfileV1` revision and invalidate prior credential-bearing provider instances.

#### LSS-082

Runtime health may report:

```text
configured
verified
runtime_ready
profile_revision
provider/model
reason_codes
```

It MUST NOT reveal secret metadata.

### 11. Backup / Export / Restore

#### LSS-090 — Exclusion

Default backup/export/diagnostic packages MUST NOT copy OS credential material or a recoverable encrypted secret blob.

SQLite may contain non-sensitive profile/operation refs required for audit/recovery, but no secret.

#### LSS-091 — Restore Missing Secret

After restore/move to another machine, if active profile references a missing credential:

```text
profile → DEGRADED
reason → SECRET_MISSING (or exact stable equivalent)
runtime_ready → false
required action → re-enter credential
```

MUST NOT silently use `.env` or another secret discovered on the restored machine.

### 12. Error Semantics

At minimum map infrastructure failures to stable model-config errors:

| Condition | Required semantic outcome |
|---|---|
| unsupported OS/backend | `MODEL_CONFIG_STORAGE_UNAVAILABLE` |
| backend locked/denied | storage unavailable/locked recovery code |
| secret missing for active profile | `DEGRADED + SECRET_MISSING` |
| secret write failure | no profile switch |
| profile commit failure after secret write | orphan cleanup + prior profile preserved |
| runtime verify failure | rollback or explicit degraded recovery |
| secret delete failure after clear | disabled remains authoritative + cleanup issue |

Raw OS/keyring exceptions MUST NOT cross the public API.

### 13. Security Tests

#### LSS-100 — Backend Allowlist

On production-mode tests/mocks prove:

- macOS exact built-in backend accepted；
- Windows exact built-in backend accepted；
- Null rejected；
- third-party backend rejected；
- config/env backend override cannot redirect storage；
- unsupported OS fails closed。

#### LSS-101 — Leakage

Search/inspect browser persistence, API responses, logs, trace attributes, SQLite tables, export, backup and diagnostics; candidate/stored key MUST NOT appear.

#### LSS-102 — Crash Matrix

Inject process interruption after each phase in LSS-050/LSS-060 and prove restart reconciliation reaches one of:

```text
exact prior active config
exact new verified config
explicit DEGRADED/recovery state
```

Never silent split-brain.

#### LSS-103 — Provider E2E

Release evidence must include at least one real provider configuration through Local Web Settings followed by a real-model-required Askora flow, restart and re-use, with secret redaction verified.

### 14. Acceptance Criteria

- `LSS-AC-001`：production macOS/Windows use only explicitly approved OS-backed keyring backend.
- `LSS-AC-002`：Windows Askora credential uses local-machine persistence, not enterprise roaming mode.
- `LSS-AC-003`：no persistent plaintext fallback exists.
- `LSS-AC-004`：browser/public API cannot read or enumerate stored credentials.
- `LSS-AC-005`：SQLite profile/journal contains no secret material.
- `LSS-AC-006`：probe failure leaves prior active config exact and writes no new secret.
- `LSS-AC-007`：every crash phase has deterministic reconciliation and no silent profile/runtime split-brain.
- `LSS-AC-008`：clear remains disabled even when old secret cleanup fails.
- `LSS-AC-009`：restore with missing secret requires re-entry and never falls back to environment config.
- `LSS-AC-010`：real Local Web BYOK flow survives Local Server restart with exact profile/runtime revision and no leakage.

### 15. Forbidden Implementations

禁止：

- automatic/unverified keyring backend discovery in production；
- accepting any “recommended”/third-party backend without exact allowlist；
- Windows enterprise roaming persistence for Askora BYOK；
- plaintext file/SQLite/browser secret persistence；
- secret/key fragment/fingerprint readback；
- profile activation driven by secret presence；
- deleting prior secret before new runtime verification；
- pretending SQLite + OS Keychain is one atomic transaction without journal/recovery；
- `.env` resurrection after explicit user clear；
- backup/export carrying recoverable credentials；
- arbitrary same-user code threat being described as solved by this contract。

### 16. Freeze Result

`LSS-*`：**FROZEN / READY_FOR_IMPLEMENTATION**。

XIK-173 MAY implement Local Web BYOK against `MODEL-CONFIG-* + ADR-0017 + LSS-*`. If implementation requires a different secure-storage backend, remote secret service, browser-side secret persistence, or a new application security boundary, it MUST stop as `BLOCKED_BY_SPEC_GAP` and return upstream.
