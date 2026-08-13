# ADR-0023 — Course Workspace Selection and Activity Projection

Status: accepted
Date: 2026-08-11
Decision owners: user-authorized Askora architecture governance
Upper authority:

- `docs/product/PRODUCT-STRATEGY.md`
- `docs/product/PRODUCT-POSITIONING.md`
- `docs/product/PRODUCT-DEFINITION.md`
- ADR-0016、ADR-0019、ADR-0022

Product trace: `CAP-01`、`CAP-07`、`PD-RULE-009`、`PD-REQ-0701..0703`
Direct contract: `docs/specs/platform/course-workspace-selection.md` (`CWSP-*`)
Amends: ADR-0016 default bootstrap、ADR-0019 single-default read projection

## Context

ADR-0022 已冻结 Course-centric Experience，但故意没有发明 Course list/create/current/switch 与 Activity Switcher 的技术合同。当前实现只有单一 default Workspace 的只读 projection；route、React state 或 localStorage 不得补成 `current_workspace_id`。

同时发现一个下位冲突：ADR-0016/WSP 的旧 first-use bootstrap 总会创建 default Workspace，而 current Course Empty State 明确要求新 LocalOwner 没有真实 Workspace 时不得生成默认课程。旧数据迁移仍需要 default Workspace 承接历史数据，因此必须区分 fresh empty owner 与 legacy-data owner。

## Decision

### 1. Platform Workspace Registry owns durable current selection

采用 owner-scoped、versioned `WorkspaceSelection`：

```text
LocalOwner
├── 0..N Workspace
└── 0..1 WorkspaceSelection → current active Workspace
```

Workspace identity、default marker 与 current selection 是不同事实：

- `Workspace.is_default` 是迁移/兼容 fallback；
- `WorkspaceSelection.current_workspace_id` 是最近显式选择的 application preference；
- route、frontend store、browser storage、LearningSession 与 Activity 都不是 selection writer。

selection 只有 Platform Workspace Registry 可写，使用单调版本、expected version 与幂等 receipt。

### 2. Fresh empty owner may have zero Workspaces

- fresh LocalOwner 且没有待归属 legacy data：允许 0 Workspace、0 selection；
- 旧数据迁移：幂等创建一个 active default Workspace，并创建指向它的 selection；
- 第一次显式 Course create：原子创建第一个 active/default Workspace 与 selection；
- 已有 Workspace：保持且最多一个 active default；current selection 可不同于 default。

因此 Course Empty State 是真实状态，而不是被 bootstrap 隐藏的前端假状态。

### 3. Create is an explicit create-and-select command

`CreateWorkspaceV1` 是 `＋ 新课程` 提交后的单一 Platform command。成功时同一事务完成：

```text
Workspace row
+ current selection version
+ idempotency receipt/outbox as applicable
```

它不创建 Material、Goal、Plan、Activity 或 LearningSession。若从已有 Course 创建新 Course，必须先通过与 switch 相同的无静默丢失 guard；失败时不得只创建未选择的半成品 Workspace。

### 4. Switch changes only canonical scope preference

`SwitchWorkspaceV1` 只更新 WorkspaceSelection。它不得自动：

- end/archive LearningSession；
- cancel/duplicate streaming run；
- discard composer draft/UserNote/material position；
- create Activity/Session/Evidence；
- move/copy cross-Workspace data。

未解决 transient/durable work 时返回 typed recovery-required result/error，不写 selection。已保存 state 与 active Session/Activity 保留在 source Workspace，后续可恢复。

### 5. Explicit deep links do not write selection

`/courses/:workspaceId`、Activity deep link 与 legacy redirect 先做 owner/scope validation，再 side-effect-free 读取目标。读取 foreign/inaccessible ref fail closed 且不可枚举。只有显式 Course selection Action 调用 switch command；refresh/back/redirect 不改变 selection。

### 6. Course Activity projection remains SYS06-derived

Platform/API query assembler提供 Course-scoped `WorkspaceActivityIndexResponseV1`，但不取得 Activity ownership。每项必须来自 exact SYS06 LearningActivity definition + latest lifecycle state，并通过 Goal/Plan immutable owner chain解析到同一 Workspace。

稳定分组：

- `resumable`：latest lifecycle `active`；
- `available`：latest lifecycle `available`；
- `recent`：有 lifecycle transition 的 current-plan activity，按 transition time 降序与 activity id tie-break；
- `planned/completed/skipped/superseded` 只在合同允许的 presentation filter 中诚实表达，不得变成可执行状态。

显示标题来自 activity semantics + versioned server presentation catalog，不从 Conversation title/chat text/LLM 临时推断。打开 active Activity 是 Navigation；启动 available Activity 仍调用 SYS06 `StartLearningActivityV1`。

### 7. LearningSession may pin exact Activity

新 Course-scoped LearningSession 增加 optional-at-migration / required-for-new-activity-session 的 `learning_activity_id` exact ref。Platform Learning Session Registry 只保存 interval/scope link；SYS06 仍是 Activity writer。旧记录只有能无猜测证明 activity ref 时才 backfill，否则保持 nullable compatibility。

## Alternatives Considered

### A. Durable WorkspaceSelection owned by Platform Workspace Registry

**Accepted.** 它提供重启可恢复、并发可检测、跨页面一致的 current scope，同时不改变 Workspace identity，也不让 UI 成为第二 truth。

### B. Every navigation carries explicit Workspace scope; no global current selection

Rejected for current Product Experience。它可保持纯 URL scope，但不能独立回答启动时的最近 Course，也会让 Library、Utilities 返回与 cross-surface continuity 依赖各客户端自行保存选择。若由 browser 保存，就形成多个不一致 preference truth；若完全不保存，则不满足 ADR-0022 的 durable startup/resume expectation。

### C. Store current selection in browser localStorage / React state

Rejected。它无法参与 owner-side isolation、expected-version、migration、recovery 与多窗口并发，并直接违反 ADR-0019/0022。

### D. Reuse `Workspace.is_default` as current selection

Rejected。default 是迁移/fallback marker，current 是频繁变化的显式 preference。复用会把每次导航变成 default migration state mutation，并混淆 rollback 与兼容 endpoint 语义。

## Consequences

### Positive

- current Course 在重启、多页面与 API query 中一致；
- fresh Course Empty State 可达，legacy 数据仍安全归属；
- create/switch 有单一 writer、并发和幂等边界；
- Activity Switcher 不复制 SYS06 truth；
- deep link/redirect 可严格保持无副作用。

### Cost / Risk

- 新增 selection/receipt persistence 与 migration；
- default-Workspace resolver 必须拆成 legacy compatibility 与 current selection resolver；
- 所有 course-scoped query 需显式 workspace scope；
- frontend 必须实现 transient work guard，不能只依赖 server 检测浏览器内未保存内容；
- LearningSession activity link 需要 additive migration 与 strict-writer cutover。

## Migration / Compatibility / Recovery

```text
add selection + receipt + optional session activity ref
→ classify fresh-empty vs legacy-data owner
→ legacy data: create/resolve default + selection
→ existing Workspace: create selection to active default when missing
→ switch active readers from default resolver to selection resolver
→ enable create/switch writers
→ retire default-only UI projection
```

迁移必须 additive、idempotent，并在 SQLite fresh/legacy/upgraded fixture 上验证。writer cutover 后或存在多个 Workspace 后禁止 destructive downgrade；使用 forward-fix 与 verified recovery point。compatibility endpoints 只可解析 active selection，若旧合同明确要求 default 则只解析 default，二者不得聚合全部 Workspace。

## Security / Observability

- 所有 list/get/create/switch/activity query 先解析 LocalOwner；
- foreign Workspace/activity ref 统一不可枚举；
- log 只记录 owner-safe workspace/activity/selection version、result/error、correlation/idempotency refs；
- 不记录 draft/note正文、transcript、Prompt、secret 或本地路径；
- request refresh/retry 不产生第二 Workspace、selection version、Session 或 Activity fact。

## Validation

- fresh owner returns empty list/selection without implicit create；
- legacy data receives exactly one default + selection idempotently；
- create-and-select is atomic/idempotent；
- stale expected selection version fails without write；
- same key/different payload conflicts；
- unresolved draft/stream/note/material state blocks mutation；
- switch preserves source Session/Activity and returns resumable refs；
- deep link/read/redirect never writes selection；
- cross-Workspace refs do not leak existence；
- Activity projection uses exact SYS06 refs and stable ordering；
- SQLite/PostgreSQL schema and current app tests pass。

## Supersedes / Superseded By

- **amends ADR-0016**：fresh first-use no longer unconditionally creates default Workspace；legacy migration/default fallback semantics retained；
- **supersedes ADR-0019 target limitation**：`SINGLE_WORKSPACE` remains migration compatibility only；current Course query uses `WorkspaceSelection`；
- **implements ADR-0022 technical gate**：closes Course list/create/current/switch and Activity projection `SPEC GAP`。

Superseded by: none.
