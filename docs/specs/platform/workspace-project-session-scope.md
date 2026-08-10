# Workspace / LearningProject / LearningSession Scope Contract

> Spec ID：`WSP-*`  
> 状态：**Canonical Implementation Contract / FROZEN**  
> 版本：v1.0  
> 冻结日期：2026-08-10  
> Governing：`docs/product/PRODUCT-POSITIONING.md`、ADR-0016  
> Linear：XIK-168

## 1. Purpose

本合同把 v1 已冻结的 `LocalOwner → Workspace → Material / LearningProject / LearningGoal / LearningSession` 产品模型转化为可直接实现、迁移和验收的持久化与应用边界。

它是 platform scope contract，不建立第九个 Learning Core system，不修改 SYS01～SYS08 的事实所有权，也不改变 v0.3 Teaching Policy。

## 2. Ownership

### WSP-001 — Workspace Owner

`Workspace` 唯一 writer 为 **Platform Workspace Registry**。

Workspace Registry 只拥有 Workspace identity、metadata、default marker 与 lifecycle。它 MUST NOT 写 Material content、Goal semantics、LearnerState、TeachingAction、AssessmentResult 或 ReviewSchedule。

### WSP-002 — LearningProject Owner

`LearningProject` 与 current `ProjectMaterial` membership 唯一 writer 为 **Platform Workspace / Product Organization**。

Project 只组织 canonical refs，不复制 Material/Goal truth。

### WSP-003 — LearningSession Owner

`LearningSession` 唯一 writer 为 **Platform Learning Session Registry**。

它只拥有 continuous learning interval 的 scope/lifecycle envelope：Workspace、可选 Project/Goal/Material refs、start/end/status。

Transcript/message、TeachingAction、AssessmentResult、LearnerState、LearningPlan、ModelInference 分别继续由既有 owner 管理。

### WSP-004 — No DialogSession Promotion

Legacy `DialogSession` MUST NOT 被原地改名或解释为 canonical LearningSession。

DialogSession MAY 保存 `workspace_id` 与可选 `learning_session_id` compatibility ref；无法可靠关联的历史 conversation MUST 保持 `learning_session_id = null`，不得猜测。

## 3. Canonical Objects

### WSP-010 — Workspace

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

### WSP-011 — LearningProject

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

### WSP-012 — ProjectMaterial

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

### WSP-013 — LearningSession

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

## 4. Material and SourceFile Migration Boundary

### WSP-020 — Stable Material Identity

Current `user_documents.id` MUST be adopted as the stable `material_id` compatibility identity for migrated v1 data.

Implementation MUST NOT introduce a parallel `materials` table that becomes a second current metadata/lifecycle truth while `user_documents` remains writable.

The ORM class/table MAY retain the legacy name during the compatibility window. Public/domain naming SHOULD move to Material.

### WSP-021 — Workspace on Material

Current Material persistence MUST gain direct non-null `workspace_id` after backfill/cutover.

New Material writers MUST require Workspace explicitly or derive it from an exact Workspace-scoped parent command; owner-only creation is forbidden after cutover.

### WSP-022 — Normalized Managed SourceFile

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

### WSP-023 — Existing SourceDocument / MaterialRevision

Existing SYS01 SourceDocument/MaterialRevision/SourceSpan records MUST resolve to Material by stable compatibility refs. New migrations MUST preserve existing revision/span IDs and provenance.

A table rename or ID rewrite is not required for XIK-171 and SHOULD NOT be performed unless it materially reduces risk.

## 5. Workspace Attribution Rules

### WSP-030 — Direct Workspace Keys

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

### WSP-031 — Parent-derived Workspace Is Allowed Only When Lossless

A child record MAY omit a duplicate workspace column only when all are true:

1. it has an immutable/non-null exact parent ref；
2. the parent has direct canonical `workspace_id`；
3. every read/write path validates through that parent；
4. no independent bulk query can cross Workspace without an explicit parent join/filter；
5. architecture tests prove the invariant。

If any condition fails, direct `workspace_id` is required.

### WSP-032 — LearningGoal

All new LearningGoal definitions/state/drafts/objectives and independently queried control/evaluation rows MUST resolve exact Workspace.

Canonical Goal semantics:

```text
workspace_id = REQUIRED
project_id = OPTIONAL organization association
```

Project association MUST NOT be stored as part of immutable GoalDefinition semantics when changing the association does not change the learning goal itself. The current project association belongs to Goal state/organization binding and changing it creates a new current state/binding, not a new semantic definition.

### WSP-033 — Learner Evidence and State

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

### WSP-034 — Assessment and Decision Records

Attempt/AssessmentResult/TeachingAction/DecisionTrace/Outcome records MUST be attributable to one Workspace through exact Session/Activity/Goal/Material refs.

They MAY avoid duplicate workspace columns only when `WSP-031` is satisfied. Any new application entry that lacks a resolvable Workspace MUST fail closed before creating learning evidence or a TeachingAction.

### WSP-035 — Knowledge / Retrieval Projections

KnowledgeUnit/SourceSpan/Chunk/index records generated from Material MUST remain attributable to the source Material Workspace. SYS02 retrieval cutover is governed by the separate Workspace-scoped Retrieval implementation issue; no owner-global cache/index may survive as a default v1 path.

## 6. Same-workspace Integrity

### WSP-040 — ProjectMaterial Constraint

For any ProjectMaterial command:

```text
project.workspace_id == material.workspace_id
```

Otherwise reject before write.

### WSP-041 — Goal Project Binding

When `project_id` exists:

```text
project.workspace_id == goal.workspace_id
```

Cross-workspace move MUST NOT be implemented as changing `workspace_id` in place. v1 does not define object move-between-workspaces; use explicit copy/import/recreate semantics in a future contract if needed.

### WSP-042 — Session Scope

For Session refs:

```text
session.workspace_id == project.workspace_id   (if project)
session.workspace_id == goal.workspace_id      (if goal)
session.workspace_id == material.workspace_id  (for every material)
```

Mismatch rejects the command atomically.

### WSP-043 — No Existence Leakage

Cross-workspace invalid refs MUST return the stable API/domain invalid-scope or not-found behavior selected by the public contract. Response MUST NOT reveal title, owner, project membership or other object metadata from another Workspace.

## 7. Default Workspace Bootstrap and Migration

### WSP-050 — Bootstrap Preconditions

Workspace migration starts only after ADR-0015 LocalOwner foundation can resolve exactly one durable LocalOwner.

If LocalOwner is missing/ambiguous, startup/migration MUST fail closed; it MUST NOT create multiple owners/workspaces to guess around corrupted identity state.

### WSP-051 — Exactly One Default Workspace

Migration/first-use bootstrap MUST ensure exactly one active default Workspace for the LocalOwner.

Creation MUST be idempotent. Rerunning bootstrap resolves the existing default rather than creating a new row.

DB/application invariants MUST prevent multiple active default Workspaces for the same owner.

### WSP-052 — Backfill Scope

All legacy active LocalOwner-global data that participates in current v1 behavior MUST be assigned to the default Workspace before Workspace becomes a required write/read filter.

At minimum migrate/backfill:

- UserDocument/Material and Library tags/collections/assignments/search projections/receipts/suggestions；
- current Goal management definitions/states/drafts/previews/focus/objectives/evaluations/plans/activities where applicable；
- legacy dialog/conversation records for isolation；
- LearnerEvidence/MasteryEstimate/LearnerState streams；
- ReviewSchedule；
- current operational jobs/receipts whose resource is Workspace-scoped；
- material-derived knowledge/index refs needed to enforce later retrieval scope。

### WSP-053 — Legacy Dialog Migration

All legacy DialogSession records are assigned to the default Workspace for isolation.

A canonical LearningSession is created/backfilled only when the existing record has enough stable canonical refs to establish a real continuous learning activity without guessing. Otherwise DialogSession remains historical/compatibility transcript with `learning_session_id = null`.

### WSP-054 — SourceFile Backfill

For each active/non-erased existing Material with a managed storage reference:

1. create exactly one normalized SourceFile row if none exists for the legacy primary file fingerprint；
2. preserve checksum/original filename/managed ref；
3. verify managed file availability/hash where practical；
4. do not copy the same file again merely for schema migration；
5. quarantined/failed Material keeps the SourceFile but retains its safety/status semantics。

Missing managed files become an explicit migration/recovery issue, not a silently invented SourceFile.

### WSP-055 — Migration Phases

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

### WSP-056 — No Destructive Downgrade

Before writer cutover, additive migration MAY be rolled back if it can prove no new Workspace-aware writes exist.

After cutover or creation of more than one Workspace, a downgrade that collapses Workspace/Project/SourceFile identity is forbidden. Use forward-fix/rescue and current verified recovery point.

## 8. Writer / Reader Cutover

### WSP-060 — Canonical Writer Cutover

After cutover, every creation/update command for Workspace-scoped business data MUST receive/resolve exact Workspace before owner application logic.

`LocalOwner` alone is not sufficient scope.

### WSP-061 — Compatibility Endpoints

Legacy owner-global endpoints MAY temporarily adapt to **the canonical default Workspace only**.

They MUST NOT:

- query all Workspaces；
- create data without Workspace assignment；
- become a second writer；
- stay after active frontend/application readers have migrated and retirement tests pass。

### WSP-062 — Idempotency Scope

Workspace-scoped command receipts SHOULD use:

```text
owner_id + workspace_id + command_type + idempotency_key
```

or an equivalent collision-safe scope. The same client key in two Workspaces MUST NOT accidentally return the other Workspace's receipt/result.

### WSP-063 — Focus / Current Selection

Current UI-selected Workspace is presentation/application preference, not ownership truth. Backend commands MUST still carry/resolve exact Workspace; browser local state MUST NOT be the only source of Workspace identity.

## 9. API/Application Contract

### WSP-070 — Canonical Workspace Routes

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

### WSP-071 — Material / Goal / Session Commands

Material, Goal and Session create/write commands MUST include Workspace explicitly through route/body/application context.

Object-by-id reads/writes MUST validate Workspace before returning/mutating the object.

### WSP-072 — LearningSession Commands

Minimum application commands:

```text
StartLearningSession
EndLearningSession
ArchiveLearningSession
AttachMaterialToLearningSession
DetachMaterialFromLearningSession
```

Start MUST pin Workspace and validate optional Project/Goal/Material refs. These commands only update Session scope/lifecycle; they MUST NOT write learning outcomes or transcript content.

### WSP-073 — Retrieval Handoff

Every production retrieval request constructed from Workspace/Project/Session context MUST produce the canonical `RetrievalScope` with `workspace_id` required. XIK-172 performs the SYS02/API cutover; XIK-171 MUST provide the durable scope source needed by that work.

## 10. Configuration Scope

### WSP-080

Application → Workspace → Project configuration inheritance MAY exist only for fields whose owning configuration contract explicitly marks them overrideable.

Workspace/Project rows MUST NOT store API Key/secret material.

## 11. Deletion and Lifecycle Boundaries

### WSP-090 — Project Removal

Project archive or ProjectMaterial removal MUST NOT delete Material, LearningEvidence or SourceFile.

### WSP-091 — Material Deletion

Material Trash/Permanent Delete follows `LIB-045/046`, `PERSIST-080..083` and XIK-170/174. Workspace/Project code MUST call those owner commands rather than deleting Material rows/files directly.

### WSP-092 — Workspace Destruction Not in This Slice

XIK-171 does not implement Workspace Permanent Delete. No generic cascade delete from Workspace to child data is authorized by this contract.

## 12. Security / Privacy

### WSP-100

Workspace is an isolation boundary inside the single LocalOwner datastore. It is not authentication, but every workspace-scoped query/write MUST filter/validate Workspace to prevent accidental cross-space mixing.

### WSP-101

Logs/errors MUST NOT expose other Workspace object metadata on invalid refs. Internal managed paths remain sanitized according to security/data-control contracts.

## 13. Observability

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

## 14. Required Tests

### WSP-110 — Contract / Unit

- Workspace cardinality/default marker；
- ProjectMaterial same-workspace property；
- Goal→Project same-workspace；
- Session→Project/Goal/Material same-workspace；
- command idempotency by Workspace；
- no DialogSession→LearningSession implicit promotion。

### WSP-111 — Migration

- fresh datastore bootstrap；
- representative LocalOwner-global legacy fixture；
- rerun migration/bootstrap；
- SourceFile backfill preserves Material ID and managed bytes；
- missing managed file explicit recovery issue；
- nullable→strict cutover only after validation；
- post-cutover forward-fix path。

### WSP-112 — Isolation

Create Workspace A/B with overlapping titles/KU topics and prove:

- Material/tag/collection/Goal/Session queries remain isolated；
- Project A cannot attach Material B；
- Goal/Session A cannot bind Project/Material B；
- LearnerEvidence from A cannot change Mastery/LearnerState in B；
- default compatibility endpoint never aggregates A+B。

### WSP-113 — Architecture

- one Workspace writer；
- one ProjectMaterial writer；
- one LearningSession writer；
- no UI/localStorage Workspace truth；
- no cross-owner repository writes；
- no second Material truth；
- DialogSession legacy mastery/strategy fields do not feed canonical learner/policy state。

## 15. Acceptance Criteria

- `WSP-AC-001`：fresh local datastore has exactly one LocalOwner and one active default Workspace after bootstrap.
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

## 16. Forbidden Implementations

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

## 17. Freeze Result

`WSP-*`：**FROZEN / READY_FOR_EXEC_DECOMPOSITION**。

XIK-171 MAY 在本合同下实现 Workspace/Project/Session/SourceFile persistence and migration。Workspace-scoped SYS02 retrieval cutover remains XIK-172。Learner evidence/state schema work MAY be split into a dedicated implementation issue if keeping XIK-171 narrow improves verification, but it MUST complete before Product Positioning Conformance can pass。
