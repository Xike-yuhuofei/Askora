# Askora Learning Conversation Message System — Canonical Design Delta

> 状态：**FROZEN — Canonical Design Delta Record**
> 冻结日期：2026-08-11
> 决策权限：user-delegated Codex；用户于 2026-08-11 明确“采纳你的建议，开始执行”
> 上位约束：`PRODUCT-POSITIONING.md`、`PRODUCT-DEFINITION.md`、v0.3 Adaptive Teaching Loop、ADR-0004/0005/0014/0018/0019
> 下游：ADR-0020、`LCMS-*` Formal Spec、Learning Conversation Message System Vertical Slice、EXEC-075
> 基线：`origin/main@a192b54ee0fcfd0d13c213f6c25a65db3eb92e9d`

## 1. Purpose

本 Delta 把本地 Learning Conversation Message System Prototype 中可保留的交互发现，收敛为不突破 Askora Learning Core owner 边界的正式设计。

它回答：

> 在 Conversation / Message 不是核心学习领域模型、也不是 Learning Evidence 的前提下，Askora 如何用少量 typed blocks 呈现教学内容、暴露合法交互，并把用户操作送入真正的 owner command/evidence chain？

本 Delta 不修改 Product Capability taxonomy，不建立第九个 learning owner，不设计 SQLite 表，也不接受 Prototype 的前端业务状态作为实现合同。

## 2. Current Reality and Trigger

### 2.1 Governance identity gap

正式仓库中的 `EXEC-069` 是 Learning Context Drawer Query and UI，不是 Message System Prototype；正式 `EXEC-070` 已被 UI-04C UserNote + Current Material Right Rail 占用。

本地以下资产只能作为 Prototype / Design Evidence：

```text
.design_library/Askora/preview/learning-message-system.html
askora-learning-conversation-message-system-canonical-design.md
design-recommendations.md
```

因此本工作使用新的治理身份：ADR-0020 + EXEC-075。

### 2.2 Implementation reality

当前 main 存在两个不同边界：

```text
legacy compatibility dialog
→ DialogSession / DialogMessage
→ content + optional RenderPayloadV1

canonical activity learning
→ LearningActivity
→ BookLearningTranscriptTurnV1
→ learner_text / reply_text + exact owner refs
```

`RenderPayloadV1` 只有 `markdown`、non-interactive `card`、`citations`，并明确禁止 arbitrary command、tool、mastery、next action 或 canonical decision 字段。`ActivityLearning` 仍直接渲染 `reply_text`。

### 2.3 Prototype conflicts that must not be promoted

Prototype 中以下行为仅证明了视觉/交互可能性，不能升格为产品语义：

- DOM 动态插入理解测试并隐式决定“现在测试什么”；
- 前端根据 `partial/correct` 选择 retry/test/apply；
- 前端生成 feedback/diagnosis；
- 本地 `reviewAdded=true` 后显示“已加入复习”；
- 本地插入 Apply Block 并暗示迁移能力已被评估；
- 新建没有 owner 的 `ReviewItem`；
- block interaction 直接更新 LearnerState/mastery；
- 浏览器状态显示 UserNote 已保存。

这些行为分别越过 SYS03、SYS04、SYS05、SYS06、SYS07 或尚未冻结的 UserNote owner contract。

## 3. Design Principles

### LCMS-CD-001 — Message is a presentation/transcript artifact

`LearningMessage` 是 LearningActivity-scoped、SYS08-owned 的版本化呈现/转录产物。它可以保存 learner-visible content、blocks、exact owner refs、trace refs 与当时发布的 capability descriptor；它不是 LearningActivity、Attempt、AssessmentResult、LearningEvidence、LearnerState、TeachingAction、ReviewSchedule 或 LearningSession 的替代品。

### LCMS-CD-002 — Conversation is a view, not a product domain

`LearningConversation` 是对同一 canonical LearningActivity transcript 的排序读取视图。它不是新的核心 aggregate、顶层产品域或 LearningSession 同义词。

### LCMS-CD-003 — Block is typed presentation semantics

`MessageBlock` 表达一段可安全渲染、可寻址的 learner-visible 语义。Block type 不等于领域对象类型，也不取得其引用对象的写权限。

只有满足至少一个条件的内容才应成为独立 Block：

1. 需要独立 provenance；
2. 需要独立交互；
3. 需要专门 renderer；
4. 需要稳定引用或审计；
5. 需要呈现来自不同 owner 的状态，且能保留 exact ref。

### LCMS-CD-004 — Interaction is a capability, not embedded business logic

Interactive Element 只描述“当前 UI 可以向哪个已冻结 command/query port 提交什么 intent”。它不能携带任意 tool name、任意 URL、SQL/ORM target、mastery value、next_due 或 next TeachingAction。

```text
Block
→ server-issued capability descriptor
→ frontend semantic primitive
→ narrow application/owner command
→ owner receipt/ref
→ owner query refresh
```

前端不得根据 block type、文案、正确率、点击次数或 local state 自行选择教学策略或下一学习活动。

### LCMS-CD-005 — Learning Action remains owner-owned

Message hierarchy 只负责把用户 intent 送入真实 owner：

```text
Conversation view
→ Message artifact
→ Message Block
→ Interactive Element / capability
→ owner-owned Learning Action / command
```

最后一层不是 Message JSON 的内部状态。它可能形成 SYS04 Attempt、SYS05 new TeachingAction、SYS06 activity transition、SYS07 schedule update 或普通 read query，取决于 command owner。

### LCMS-CD-006 — Exact refs, not copied truths

Block/Message 可以引用：

- SYS01 KnowledgeUnit/SourceSpan revision；
- SYS02 EvidenceBundle；
- SYS03 LearnerEvidence/MasteryEstimate（read-only presentation）；
- SYS04 AssessmentItem/Attempt/AssessmentResult；
- SYS05 TeachingAction/DecisionTrace/validation obligation；
- SYS06 LearningActivity/LearningPlan；
- SYS07 ReviewSchedule/ReviewDue；
- SYS08 WorkflowRun/ModelInference/transcript record。

引用必须包含 owner、entity type、id/version、availability/freshness；不得复制成可写第二 truth。

## 4. Frozen Message Architecture

```text
LearningConversationViewV1       SYS08 read projection
└── LearningMessageV1            SYS08 accepted presentation/transcript artifact
    ├── content                  mandatory safe fallback
    ├── context_refs             exact owner references
    ├── trace_refs               correlation / decision / execution refs
    └── MessageBlockV1[]         ordered typed presentation
        └── InteractiveElementV1[]
            └── capability dispatch
                └── owner command/query and canonical result refs
```

分类边界：

| Layer | Owns | Must not own |
|---|---|---|
| Conversation view | scope、ordering、cursor、availability | LearningSession/Plan/State truth |
| Message | accepted learner-visible transcript/presentation | teaching or assessment decision |
| Block | typed content/presentation + refs | canonical owner state |
| Interactive Element | semantic role、capability、availability | business rule or arbitrary tool |
| Learning Action | owner command/result | UI/renderer local inference |

## 5. Frozen Block Taxonomy

一等 Block 类型固定为六类：

```text
EXPLANATION
KNOWLEDGE
EVIDENCE
LEARNING_ACTIVITY
FEEDBACK
REVIEW_APPLY
```

视觉 variant、heading、list、bold、formula、code、table、quote style 不新增一等领域/消息类型；它们属于安全 payload/renderer composition。

### 5.1 Explanation Block

呈现讲解、例子、类比、总结或步骤说明。它必须保留 source-grounded / external-model / mixed provenance classification；不得把模型常识伪装成资料事实。

### 5.2 Knowledge Block

呈现一个结构化概念、原则、关系或关键点。若声称 canonical knowledge，必须引用 SYS01 published revision；否则必须标记 `presentation_only`，不能借 Message 发布新 KnowledgeUnit。

### 5.3 Evidence Block

呈现 EvidenceBundle 中 learner-visible 的 SourceSpan/citation/locator。它只用于来源验证与上下文查看，不包含 grader-only/rubric/answer-only content。

### 5.4 Learning Activity Block

呈现 exact SYS06 LearningActivity + SYS05 TeachingAction 允许的 prompt/task；需要测量时还必须引用 SYS04 AssessmentItem。用户响应经 command 形成 Attempt，Block 本身不判分。

### 5.5 Feedback Block

呈现 exact SYS04 AssessmentResult/diagnosis 与实际 assistance/exposure，或明确标记为 non-assessment execution feedback。它不得显示或写入 `mastered`，不得由 LLM 文本替代 AssessmentResult。

### 5.6 Review / Apply Block

同一 presentation family 使用 `mode=review|apply`：

- `review` 只能呈现/start exact SYS06 `delayed_review` activity，并可引用 SYS07 ReviewDue/Schedule；
- `apply` 只能呈现/start exact SYS06 `transfer_check|practice` activity，并引用允许的 SYS05 Transfer Task action；
- 缺 exact owner refs 时只能显示 information/unavailable，不能由 UI 创建 ReviewItem、修改 `next_due_at` 或插入新 activity。

## 6. State Decomposition

Prototype 的单一：

```text
created → presented → opened → attempted → evaluated → mastered / needs-review
```

被明确拒绝，因为它跨越多个 owner。正式设计拆分为：

| State family | Owner | Example | Learning impact |
|---|---|---|---|
| Workflow execution | SYS08 | pending/running/succeeded/failed | 无直接 learner impact |
| Accepted message | SYS08 | immutable accepted revision | transcript/presentation only |
| Delivery/view telemetry | UI/SYS08 telemetry | presented/opened | process metric only，非 evidence |
| Capability invocation | frontend transient + owner receipt | idle/submitting/succeeded/failed | 以 owner result 为准 |
| Activity lifecycle | SYS06 | available/active/completed | completion != mastery |
| Attempt lifecycle | SYS04 | started/submitted/scored | may produce measurement |
| Assessment result | SYS04 | immutable result revisions | single-attempt measurement |
| Evidence acceptance | SYS03 | candidate/accepted/rejected/invalidated | may affect projection |
| Learner projection | SYS03 | version stream / labels | mastery state truth |
| Validation obligation | SYS05 | none/required/satisfied-by-ref | policy control，非 mastery |
| Review schedule | SYS07 | immutable version stream | next_due/retrievability truth |

`presented`、`opened`、阅读时长、copy、hover、thumbs-up 与 conversation turn 不能直接影响 LearnerState、MasteryEstimate 或 ReviewSchedule。

## 7. Teaching System Boundary

| Question | Decision owner | Message/UI role |
|---|---|---|
| 教什么 | SYS06 selects Objective/Activity；SYS01 supplies canonical knowledge | 呈现 exact refs |
| 为什么现在教 | SYS06 explains activity priority/sequence；SYS05 explains current TeachingAction；SYS07 only supplies due context | 显示 reason/DecisionTrace summary |
| 当前怎么教 | SYS05 creates TeachingAction/envelope；SYS08 executes within/tighter envelope | typed rendering only |
| 如何评价 | SYS04 creates Attempt/AssessmentResult/diagnosis | submit response，呈现 result |
| 是否形成 evidence/掌握 | SYS03 accepts LearnerEvidence and updates projection | 只读呈现，不推断 |
| 何时复习 | SYS07 owns ReviewSchedule/next_due；SYS06 decides actual activity | start exact activity only |
| 如何展示 | SYS08 accepts safe Message/Blocks；frontend allowlisted renderer | accessibility + dispatch |

## 8. Frontend Boundary

冻结建议层级：

```text
ConversationView
→ MessageRenderer
→ BlockRenderer
→ SpecificBlockComponent
→ InteractiveElementRenderer
→ capability dispatch adapter
```

稳定组件：`ConversationView`、`MessageRenderer`、`BlockRenderer`、safe Markdown/math/citation primitives、capability dispatch adapter。

可扩展组件：六类 `SpecificBlockComponent` 的 payload renderer，以及在现有七类 UI semantic primitives 内的 presentation pattern。

禁止进入组件的逻辑：

- TeachingAction/StrategyFamily/next activity selection；
- scoring/diagnosis/mastery threshold；
- review scheduling/next_due calculation；
- evidence eligibility；
- answer exposure expansion；
- owner command success inference；
- generic arbitrary command/tool execution。

## 9. Public Schema Evolution Direction

### LCMS-CD-007 — Do not mutate RenderPayloadV1 semantics

`RenderPayloadV1` 保持现有 non-interactive contract。不得在 `schema_version=1.0` 下静默新增 executable block 或改变 `card` 语义。

### LCMS-CD-008 — Introduce LearningMessageV1

正式目标是新的 `LearningMessageV1`，以 `message.content` / `reply_text` 为 mandatory fallback，以六类 MessageBlock 和 capability descriptor 为 additive structured payload。

它与 `RenderPayloadV1` 的关系是迁移/compatibility，而不是永久双写：

- legacy dialog history 保持 read-only compatibility；
- existing RenderPayloadV1 可经 deterministic adapter 映射为无业务交互的 Message blocks；
- 映射缺 exact refs 时标 `LEGACY_COMPAT/PARTIAL`，不能补造 capability；
- canonical LearningActivity 新 writer 最终只产生一个 accepted LearningMessage envelope；
- HTTP/history/SSE final/replay 必须返回同一 accepted envelope；
- 历史消息不得调用在线 LLM 回填。

### LCMS-CD-009 — No database design in this Delta

Domain/public contract 先冻结；SQLite table/column/index/migration 由后续 implementation planning 根据现有 append-only transcript projection 映射。不得因当前表结构反向改变 Message 语义。

## 10. Capability Boundary

V1 capability vocabulary 只允许：

```text
ASK_FOLLOW_UP
INSPECT_SOURCE
SUBMIT_ATTEMPT
REQUEST_HINT
REQUEST_EXPLANATION
START_ACTIVITY
```

语义：

- `ASK_FOLLOW_UP` / request actions 记录 user intent，经 canonical façade 触发新的 SYS05 decision；不直接改旧 TeachingAction；
- `INSPECT_SOURCE` 是 read query；
- `SUBMIT_ATTEMPT` 必须进入 SYS04 Attempt/Assessment contract；
- `START_ACTIVITY` 只接受 server-issued exact SYS06 activity ref，mode 可为 review/apply；
- 任何 capability dispatch 都由 server 重验 scope、version、availability、idempotency 与 action envelope；
- frontend success 只表示收到 owner receipt，随后必须 re-query canonical owner state。

`CAPTURE_NOTE` 不进入本 Delta 的 V1 capability vocabulary。它等待 UI-04C UserNote owner/anchor/version/conflict/recovery contract；Message System 可以以后 additive 接入，但不能在当前 Spec 中伪造。

## 11. Alternatives Considered

### A. 把 Message 建成新的核心 learning aggregate

未采用。它会复制 LearningActivity、Attempt、Assessment、TeachingAction、Mastery 和 Review truth，建立第九 owner。

### B. 直接给 RenderPayloadV1 card 增加 command/action 字段

未采用。它会在相同 major version 下改变公共 schema/security 语义，并使 renderer 成为 command router。

### C. 让前端根据 block type 和 feedback 决定下一步

未采用。它把 SYS05/SYS06/SYS07 业务规则移入 UI，无法 replay，也会制造 local success truth。

### D. LearningActivity-scoped transcript artifact + exact refs + typed blocks + capabilities

采用。它复用 ADR-0004 的 SYS08 append-only transcript 方向，保持八系统单一写入者，并允许安全扩展呈现与交互。

## 12. Gap Disposition

此前 `LCMS-GAP-001..013` 的处理结果：

| Gap | Disposition |
|---|---|
| 001 task identity | ADR-0020 / EXEC-075 关闭 |
| 002 Message position | SYS08 presentation/transcript artifact 关闭 |
| 003 Block schema | new LearningMessageV1 + six blocks 关闭 |
| 004 dynamic test | only owner-issued LearningActivity/TeachingAction capability 关闭 |
| 005 Feedback | exact SYS04 result or non-assessment label 关闭 |
| 006 Next action | SYS05/SYS06 owner refs only 关闭 |
| 007 ReviewItem | 不新增；start exact activity only 关闭 |
| 008 Apply/transfer | exact SYS06/SYS05/SYS04 chain 关闭 |
| 009 single lifecycle | state families split 关闭 |
| 010 learning evidence | Attempt→Assessment→Evidence→Projection 关闭 |
| 011 UserNote | 显式 deferred to UI-04C；不阻塞 LCMS core |
| 012 frontend boundary | stable renderer + dispatch adapter 关闭 |
| 013 dual line | canonical activity target + bounded legacy adapter/retirement 关闭 |

## 13. Invariants and Claim Boundary

- Conversation/Message/Block 不自动形成 LearningEvidence。
- UI/renderer 不直接决策 teaching、assessment、mastery、plan 或 review。
- LLM/Model output 仍是 untrusted candidate；SYS08 validation 后才可成为 accepted presentation。
- grader-only、answer-only、secret、raw Prompt、跨 Workspace refs 不得进入 learner-visible block。
- Engineering/Policy-Ownership/Learning Evidence 必须分别验收。
- 本 Delta 冻结的是架构与交互合同，不产生“学习有效”证据；Learning Evidence 状态保持 `LEARNING_EVIDENCE_INSUFFICIENT`。

## 14. Formation Chain

```text
Product Positioning / Product Definition CAP-04..07
→ v0.3 Adaptive Teaching Loop + ADR-0004/0005
→ Prototype / Design–Implementation Gap
→ Learning Conversation Message System Canonical Design Delta（本文件）
→ ADR-0020
→ LCMS Formal Spec
→ LCMS Vertical Slice
→ EXEC-075
→ implementation / tests / current evidence
```

**Freeze Result：FROZEN / PASS。冻结当时 downstream implementation 尚未开始；当前实现状态由已归档 EXEC-075 与 LCMS Spec 记录。**
