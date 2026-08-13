# ADR-0025 — Space / Conversation User-facing IA and Core Journeys

Status: accepted
Date: 2026-08-13
Decision owners: user-authorized Askora product governance
Decision authority: 用户确认将已对齐故事写入 Experience Design，替换现行 Core Journey
Upper authority:

- `docs/product/PRODUCT-STRATEGY.md`
- `docs/product/PRODUCT-POSITIONING.md`
- `docs/product/PRODUCT-DEFINITION.md`

Product trace: `CAP-01`、`CAP-04`、`CAP-07`、`PD-REQ-0101`、`PD-REQ-0701`、`PD-RULE-002`、`PD-RULE-009`；**不**关闭 `CAP-02` / `PD-REQ-0203` / `PD-RULE-004`
Current design input: 用户确认的空间 / 对话故事与对象模型
Affected specs: current Experience Design、`docs/specs/ui.md`
Supersedes (partial): ADR-0022 的用户侧「课程 / ＋ 新课程」词汇、五条 Core Journey、以及「有可恢复 Activity 则启动直接进入」的 startup 规则。不 supersede Workspace identity、Course/Workspace 技术合同（ADR-0023 / `CWSP-*`）、三栏职责、Chat 不是 Product Domain。

## Context

ADR-0022 将用户侧长期上下文称为「课程」，并以 `＋ 新课程 → 资料 → 明确 Goal → 首个 Activity` 为第一条 Journey；打开 App 时若有 resumable Activity 则直接恢复。

用户随后冻结了另一套可观察故事：

- 上传只创建资料；
- 用户文案用「空间」替换「课程」；
- 侧栏恢复的是「对话」；
- 打开 App 每次先到 Welcome；
- 对空间「继续学习」新开一段对话，旧对话仍在。

这改变用户如何找到和进入学习，但不改变 Workspace / LearningActivity 的 canonical identity，也不把 Conversation / Message 提升为 Product Object。

## Decision

### 1. User-facing vocabulary

```text
空间  = Workspace
对话  = LearningActivity 的用户侧称呼
资料  = Material
```

正常 UI 不再使用「课程」「＋ 新课程」。不创建 `space_id` / `conversation_id` 第二身份。`/courses/**` 保留为 legacy route vocabulary。

### 2. Object cardinality

```text
空间  1 ── n  资料
空间  1 ── n  对话
```

上传不创建空间或对话。空间来源：显式新建；加入空间时当场新建；「马上开始学习」自动创建。

### 3. Two Core Journeys

只保留：

- `EXP-JOURNEY-001` Materials to First Learning
- `EXP-JOURNEY-002` Return and Continue

进入对话之后的作答闭环仍由 Learning Experience 拥有。

打开 App 必须先到 Welcome，不得自动 resume。点已有对话才恢复同一段；对空间「继续学习」才新开一段。

### 4. Chat remains not a product domain

「对话」不是 Chat thread，不是新的 Product Object。标题使用学习目的。Conversation / Message / Tutor 仍只是 LearningActivity 的交互形式。本 ADR **不**采纳 ADR-0022 已拒绝的 “Conversation threads below Course”。

### 5. Open gaps stay open

- `EXP-JOURNEY-GAP-001` PRODUCT DEFINITION GAP：主路径不出现目标确认/纠正，与 `CAP-02` / `PD-REQ-0203` / `PD-RULE-004` 冲突。本 ADR 不修改 Product Definition。
- `EXP-JOURNEY-GAP-002` SPEC GAP：用户侧允许资料暂未入空间；Platform `WSP-021` 要求 Material 归属 Workspace。实现前必须补 persistence/command 合同。

## Alternatives Considered

### A. Keep 「课程」 vocabulary, only change journeys

Rejected。用户明确要求用户文案全面替换为「空间」。

### B. Treat 「对话」 as Conversation / Session product object

Rejected。违反 Positioning「Conversation 不得成为领域模型」与 `PD-RULE-002`。

### C. Resume last conversation on app start

Rejected。用户明确要求每次先 Welcome。

## Consequences

### Positive

- Journey 与用户讲述的故事一致，可供后续 UX 设计直接使用；
- 用户侧对象关系（空间 / 资料 / 对话）可独立于页面组件被评审；
- Workspace / Activity ownership 不变。

### Cost / Risk

- 与 Product Definition 的目标控制权未对齐，Experience 不能假装已关闭；
- 未入空间 Material 缺少 Platform 合同，frontend 实现仍 BLOCKED；
- 「继续学习」每次新开 Activity，增加 Activity 数量与恢复 IA 复杂度；
- 现有 Course-centric 测试、文案、startup redirect 必须迁移。

## Ownership / Truth / Security

- Workspace writer 保持 Platform Workspace Registry；
- LearningActivity 保持 SYS06；
- LearningSession 保持 Platform Learning Session Registry；
- Transcript/Message 保持 SYS08；
- Material/Notes/Goal/LearnerState/Review owner 不变；
- 不因用户文案变更建立 Space / Conversation table。

## Migration / Rollback

```text
Experience + ADR-0025
→ current UI Spec 对齐
→ 未入空间 Material 的 SPEC
→ frontend Welcome / 空间 / 对话 shell
→ legacy 「课程」文案与 startup redirect 退休
```

Rollback：可暂时保留 `/courses/**` 与兼容 deep link，但不得恢复 Today/Learning L0，不得恢复「课程」为现行用户文案，不得用 mock 空间/对话代替 owner command。

## Validation

至少验证：

- 用户界面使用「空间」「对话」；
- 上传不创建空间或对话；
- Welcome 是打开 App 的默认目的地；
- 点已有对话恢复同一段；对空间「继续学习」新开一段；
- Chat 不成为 L0 / thread manager；
- Product Definition 未被本 ADR 修改；
- 两个 GAP 在合同中显式存在。
