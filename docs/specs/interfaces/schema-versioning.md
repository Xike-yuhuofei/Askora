# Askora Schema Versioning Contract

> Spec ID：`SCHEMA-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.1

## 1. 范围

本规范适用于：

- API request/response；
- Command/Event；
- DecisionTrace；
- 公共 Pydantic/domain schema；
- persisted structured payload；
- Prompt structured output schema；
- tool input/output schema。
- RenderPayload / RenderBlock presentation schema。
- LearningConversation / LearningMessage / MessageBlock / capability / interaction schema (`LCMS-*`)。
- Electron preload IPC request/response schema；
- desktop encrypted `ModelRouteProfile` payload；
- local desktop control adapter request/response schema。
- Course Workspace list/create/current/switch、transition guard、receipt and Activity index schema (`CWSP-*`)。

## 2. 版本规则

### SCHEMA-001

公共协议使用显式版本。不得仅依赖 Git commit 猜测历史语义。

### SCHEMA-002

兼容新增字段可升 minor；删除字段、改类型、改枚举语义、改必填含义等破坏性变化必须升 major。

### SCHEMA-003

消费者必须明确支持版本范围；未知 major 版本必须拒绝或通过显式 upcaster 处理。

## 3. 演进原则

### SCHEMA-010

优先 additive evolution：新增 optional 字段、保留旧字段直到迁移窗口结束。

### SCHEMA-011

字段一旦废弃，必须经历：

```text
mark deprecated
→ dual-read compatibility window
→ backfill/migrate
→ stop writing old field
→ remove in new major
```

### SCHEMA-012

不得改变同一枚举值的既有语义；语义变化使用新值。

## 4. Upcaster

历史 Event/Decision/Domain payload 如需读取到新模型，使用 pure deterministic upcaster；不得调用在线 LLM 推断缺失字段。

## 5. Public vs Internal

内部私有结构可自由演进，但一旦被另一个 bounded context、API、事件消费者、数据库历史 payload 或测试 fixture 依赖，即视为公共合同，必须遵守本规范。

## 6. Prompt Structured Output

模型 structured output schema 必须版本化，并与 Prompt version、ModelInference 关联。Schema 通过只是语法通过，仍需业务验证。

## 7. Tool Schema

Tool definition 的参数或副作用语义破坏性变化必须升 major，并固定到 WorkflowRun；正在运行的 workflow 不得热切换到不兼容 tool schema。

## 8. Acceptance Criteria

- `SCHEMA-AC-001`：旧 event fixture 可通过 upcaster 被当前支持版本读取。
- `SCHEMA-AC-002`：未知 major event/API schema 被明确拒绝。
- `SCHEMA-AC-003`：字段废弃存在兼容窗口和 migration test。
- `SCHEMA-AC-004`：replay 不依赖模型填补历史 schema。
- `SCHEMA-AC-005`：未知 major ModelRouteProfile/desktop IPC/control schema 被明确拒绝，旧 active revision 不被覆盖。

## 9. Forbidden Implementations

禁止：

- 同一 `schema_version=1.0` 改字段语义；
- 未版本化修改公共 Pydantic model 并假设所有历史数据自动兼容；
- LLM 猜测旧事件缺失字段作为 upcaster；
- tool 参数变化但 workflow version 不变。
- 同一 RenderPayload major version 静默改变 block 或 card 语义。
- 同一 LearningMessage major version 静默改变 block、capability、owner routing 或 interaction-result 语义。

## 10. P1-06 Onboarding Schemas

### SCHEMA-100

`OnboardingPreferenceV1`、`OnboardingJourneyViewV1`、`OnboardingNextActionV1` 与 preference command
均遵循 strict v1。新增 step/action enum 必须保持旧值语义；改变完成判定、路由或 preference 字段含义
属于破坏性变化，必须新 major 或显式 migration/upcaster。

## 11. Course Workspace Schemas

### SCHEMA-110

`WorkspaceSelectionV1`、`WorkspaceListResponseV1`、`CreateWorkspaceV1`、`SwitchWorkspaceV1`、`WorkspaceMutationResultV1` and `WorkspaceActivityIndexResponseV1` are strict v1 under `CWSP-*`。Changing current/default semantics、transition guard obligation、idempotency scope、Activity grouping/launch meaning or owner routing is breaking and requires a new major or explicit migration/upcaster。
