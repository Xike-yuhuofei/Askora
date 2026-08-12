# Askora Learning Conversation Message System — Canonical Design

> 文档状态：**LOCAL WORKING DRAFT / NOT CANONICAL / SPEC FREEZE BLOCKED**
> 本轮核验：2026-08-11
> GitHub 基线：`origin/main@db963d75adade6e8fe3c52d828ac1c4c27bc2dda`
> 阻塞结论：`BLOCKED_BY_DESIGN_IMPLEMENTATION_GAP`
> 说明：本文件保留原 Prototype 设计记录；以下 Delta 只记录当前正式治理链与 Prototype/实现之间的差异，**不接受、不冻结本文件后续的 Message / Block / Learning Action 方案**。

## 2026-08-11 Spec Freeze Delta：停止结论

本轮目标原计划把 Learning Conversation Message System 从 Prototype 推进到 Spec Freeze。核对 GitHub 当前 `main`、正式 Product Positioning、Canonical Design、ADR、Specs、EXEC 与实现后，已满足任务约定的停止条件：

1. 正式 `EXEC-069` 与本文件所称 Prototype 验证不是同一任务；
2. `EXEC-070` 编号已被正式 UI-04 执行链占用；
3. Prototype 交互直接模拟或决定 SYS04、SYS05、SYS06、SYS07 拥有的业务语义；
4. 当前正式 `RenderPayloadV1` 明确是非交互呈现产物，而 Prototype 需要新的公共 Block / Command / Event 合同；
5. Prototype 把 UI interaction state、Assessment、LearnerState 与 Review scheduling 混入一条生命周期，违反 single-writer ownership。

因此本轮不得把下方工作稿提升为 Canonical Design 或 Implementation Spec，也不得据此修改产品代码。

### 1. 当前 main 的正式事实

#### 1.1 EXEC 身份

GitHub 当前 `main` 的正式执行链是：

```text
EXEC-068 — Workspace Context / Shell / Route Migration
→ EXEC-069 — Learning Context Drawer Query and UI（DONE / ARCHIVED）
→ EXEC-070 — UserNote + Current Material Right Rail（ACTIVE / BLOCKED）
```

`EXEC-069` 的 current-main commit 是 `4907cb808d48066c358008e2f97aa5c994c65de0`，修改内容是 Learning Context Drawer query/UI，不是 Learning Conversation Message System Prototype。

因此：

- “EXEC-069 已完成 Message System Prototype 验证”不能作为 current-main 正式事实；
- 本地 `.design_library/Askora/preview/learning-message-system.html`、本文件与 `design-recommendations.md` 只能作为未进入治理链的 SUPPORT/Prototype 证据；
- 新任务不得继续使用 `EXEC-070` 编号，否则会与 current-main 的 UI-04C 合同冲突。

#### 1.2 当前消息/呈现实现

current main 存在两条不同历史边界：

```text
Legacy compatibility dialog
→ DialogSession / DialogMessage
→ content + optional RenderPayloadV1

Canonical activity learning
→ LearningActivity
→ BookLearningTranscriptTurnV1
→ reply_text + TeachingAction/EvidenceBundle refs
```

其中正式 `RenderPayloadV1` 只允许：

```text
MarkdownBlockV1
CardBlockV1（non-interactive presentation card）
CitationBlockV1
```

它明确禁止 executable card、模型指定组件、跨领域 command、mastery、next action 或 canonical decision 字段。当前 `ActivityLearning` 仍直接显示 transcript `reply_text`，尚未形成统一的 typed interactive message contract。

### 2. Design–Implementation Gap Register

| ID | 主题 | Prototype / 工作稿现状 | 正式合同 / current main | 结论 |
|---|---|---|---|---|
| `LCMS-GAP-001` | EXEC 依据 | 把 Message Prototype 归因于 EXEC-069 | EXEC-069 是 Learning Context Drawer；EXEC-070 已用于 Right Rail | `BLOCKING_GOVERNANCE_GAP` |
| `LCMS-GAP-002` | Message 定位 | `Message = Learning Turn`，并描述为可转化为学习证据 | Product Positioning/ARCH/DOMAIN 冻结 Conversation/Message 不是核心领域模型或 LearningEvidence；canonical activity transcript 只是 SYS08 presentation projection | 必须先决定 Message 是 presentation artifact、transcript view，还是新 aggregate；不得默认升级为核心 domain truth |
| `LCMS-GAP-003` | Block 公共 Schema | 工作稿提出 Prose/Knowledge/EvidenceQuote/Render/LearningPrompt/Feedback 六类 | `RenderPayloadV1` 只有 markdown/card/citations，且 card 非交互 | 新类型属于公共 schema 变化；必须版本化、定义兼容/回退/迁移并经 ADR/Spec 接受 |
| `LCMS-GAP-004` | 动态理解测试 | `Test Understanding` 在 DOM 中生成/插入 Prompt Block | 测试什么、为什么现在测试、允许多少帮助由 SYS05 TeachingAction 和 SYS06 LearningActivity 约束；UI 不得创建 semantic TeachingAction | Prototype 行为越过 Teaching Policy / Planner boundary |
| `LCMS-GAP-005` | Feedback | Prototype 根据本地 demo state 直接显示 partial/correct 与补救动作 | 一次评分、correctness、diagnosis、actual assistance 属 SYS04；系统/模型失败不得成为 learner error | FeedbackBlock 只能呈现 exact AssessmentResult/执行事实或明确的非评估体验反馈，不能自判 |
| `LCMS-GAP-006` | Next Learning Action | Prototype 在 partial/correct 后由前端切换 retry/test/apply | SYS05 决定当前 TeachingAction；SYS06 决定 activity/sequence；SYS08/UI 只执行/呈现且不得扩大语义 | 前端动态 next-action selector 被禁止 |
| `LCMS-GAP-007` | Review | Prototype 本地 `reviewAdded=true` 并显示“已加入复习”；工作稿新增 `ReviewItem` | SYS07 拥有 ReviewSchedule/next_due；SYS06 决定是否实例化 DELAYED_REVIEW；当前正式 Domain Spec 未定义 ReviewItem owner | 新 ReviewItem 属 unresolved public domain/ownership decision；UI success 不得冒充 durable owner success |
| `LCMS-GAP-008` | Apply / Transfer | Prototype 本地插入 Apply Block 并声称后续评估迁移能力 | TRANSFER_TASK 属 TeachingAction move；transfer Attempt/AssessmentResult 属 SYS04，LearnerEvidence 由 SYS03 接纳 | 必须走 frozen owner command/event chain，不能是 presentation-only state |
| `LCMS-GAP-009` | Interaction lifecycle | 计划使用 `created → presented → opened → attempted → evaluated → mastered/needs-review` | `mastered` 属 SYS03 projection label；`needs-review/next_due` 属 SYS07；attempt/evaluated 属 SYS04；presented/opened 是 execution/UI facts | 单一 Interaction 状态机跨越四个 owner，必须拆分，当前不能冻结 |
| `LCMS-GAP-010` | Learning Evidence | 工作稿图示容易被理解为 Block action 直接更新 LearnerState | 正式链是 Attempt → AssessmentResult → LearnerEvidence acceptance → LearnerState projection；Conversation/Message/Prompt、点赞、“我理解了”、阅读完成均非直接证据 | Message/Block 只能保存 refs、command receipt 或 UI state，不能成为 evidence writer |
| `LCMS-GAP-011` | Notes / Anchors | Prototype 在前端生成 Message/Block/TextRange anchor 与 notes success | UserNote owner/command 仍是 current UI-04 明确 SPEC GAP；浏览器内存/localStorage 不是 durable truth | Anchoring 可保留为候选输入模型，但 Note success/版本冲突/恢复必须等待 owner contract |
| `LCMS-GAP-012` | Frontend component | 工作稿期望 BlockRenderer + interactive block components | 当前 `RichMessage` 是 typed safe-render allowlist，`WorkspaceMessage` 只有 copy utility；`ActivityLearning` 未消费 RenderPayloadV1 | 可以设计 presentation component hierarchy，但任何业务 action 必须依赖正式 command capability，不得进入 renderer 内部规则 |
| `LCMS-GAP-013` | Legacy / canonical 双线 | DialogMessage 与 BookLearningTranscriptTurn 同时存在 | ADR-0004 明确 legacy Dialog 不得冒充 exact LearningActivity transcript；ARCH 禁止第二生产主链 | Spec 必须先选 canonical target 与 legacy retirement/adapter 条件，不能对两条路径永久双写 |

### 3. 与正式设计一致、可保留为候选的部分

以下 Prototype 发现没有被接受为 Spec，但与现有上位合同方向一致，可在后续治理中继续作为设计输入：

- Message 不是 Markdown editor，也不是 Notion 式 block editor；
- block 数量应小、typed、allowlisted、可安全回退；
- SourceSpan / citation / locator 必须可追溯，grader-only 与 learner-visible 必须隔离；
- 追问、笔记、测试、复习、应用应通过可寻址 anchor 指向具体上下文，而不是把整条 AI 回复当学习事实；
- UI 不得因“我理解了”、点赞、阅读或 message turn 直接提升 mastery；
- frontend 组件可以采用 `ConversationView → MessageRenderer → BlockRenderer → SpecificBlockComponent`，但该层级只负责呈现、可访问性、capability 显示与 command dispatch。

这些内容仍需服从 `RenderPayload` 安全合同、七类 UI semantic primitives、TeachingAction envelope、owner command 与 schema-versioning 规则。

### 4. Spec Freeze 前必须由正式治理关闭的决定

下列决定会产生不同业务结果，当前不能由本工作稿或 UI Preview 隐式选择：

1. **任务身份**：为本工作分配未占用的 EXEC/Linear 身份，并明确它是 Design/ADR/Spec 任务，不是 current EXEC-069/070。
2. **Message canonical target**：决定新 Message 是否只是 SYS08-owned、LearningActivity-scoped 的 presentation/transcript view；是否以及如何替代 legacy `DialogMessage`。推荐优先评估 presentation/transcript artifact，而不是建立第九 learning owner。
3. **Schema evolution**：决定扩展 `RenderPayloadV1`、发布新的 major `RenderPayloadV2`，或建立独立的 interactive activity payload；必须给出旧消息 fallback、HTTP/history/SSE 等价、migration 与 rollback/forward-fix。
4. **Block taxonomy**：解决本任务提出的 Explanation/Knowledge/Evidence/Learning Activity/Feedback/Review-Apply 与本工作稿 Prose/Knowledge/EvidenceQuote/Render/LearningPrompt/Feedback 两套分类；不得把视觉 variant、领域对象和交互 command 混成同级 type。
5. **Action contracts**：为 Ask / Inspect Source / Capture / Retrieve / Review / Apply 分别指定 semantic primitive、command owner、input/output、idempotency、稳定错误、actual result ref 与 unavailable semantics。
6. **状态拆分**：至少分离 presentation/execution state、user command state、SYS04 Attempt/Assessment state、SYS03 learner projection、SYS05 action/obligation、SYS07 schedule state；禁止单一跨 owner enum。
7. **Review 领域模型**：决定是否需要新 `ReviewItem`；若需要，必须先确定与 SYS06 LearningActivity、SYS07 ReviewSchedule、SYS03 evidence 的唯一 owner 和迁移语义。
8. **Dynamic prompt/next action**：冻结由 SYS05 TeachingAction、SYS06 activity 还是其他已存在 owner 输出 exact capability/ref；UI 只能 dispatch，不得从 block 内容或 feedback 文案本地决定。
9. **UserNote**：等待或建立 narrow UserNote owner/command/anchor/version/conflict/recovery contract；在此之前不得把 prototype notes 视为可实现 Spec。
10. **测试与 Gate**：分别定义 Engineering、Policy/Ownership 与 Learning Evidence 验收；UI/Mock/Prototype PASS 不得声明真实 assessment、review 或学习效果闭环已接通。

### 5. 推荐治理路径（未接受）

```text
确认新的任务身份
→ 把本地 Prototype 归类为 Design Evidence，而非 EXEC-069 正式输出
→ 形成 narrow Canonical Design Delta
→ 若引入公共 Message/Block/Command/Event/ReviewItem 语义，创建并接受 ADR
→ 更新 domain/interface/UI/system Specs
→ 冻结新的 Vertical Slice / EXEC
→ 才允许产品代码与迁移实现
```

推荐的最小方向是：

```text
LearningActivity-scoped transcript/message presentation artifact
+ exact owner refs
+ typed safe blocks
+ capability-driven command dispatch

而不是

Message JSON 同时持有 TeachingAction、Assessment、Mastery、ReviewSchedule 与 UI interaction truth
```

该推荐仅用于缩小后续决策空间，**本轮未被接受为 Canonical Design 或 Spec**。

### 6. 本轮验收状态

- [x] 已读取 GitHub 当前 `origin/main` 代码与治理文档；
- [x] 已核对正式 Canonical Design、v0.3 Adaptive Teaching Loop、ADR、Specs；
- [x] 已确认 current-main EXEC-069 的真实输出；
- [x] 已检查本地 Message Prototype / recommendations / HTML preview；
- [x] 已记录 Design–Implementation Gap；
- [x] 未修改产品代码、数据库、API 或公共 Schema；
- [ ] 未形成 Message System Spec Freeze：被 `LCMS-GAP-001..013` 阻塞；
- [ ] 未接受 Block 类型、Domain Data Contract、Interaction State Model 或 Frontend command boundary；
- [ ] 未满足本任务原始 Spec Freeze 验收，不得标记 DONE。

**Freeze Result：`BLOCKED_BY_DESIGN_IMPLEMENTATION_GAP`**

## 先给结论

**Askora 不应该把 Message 建模成 Markdown，也不应该把它建模成几十种 Notion Block。**

更合适的定义是：

> **Askora Message 是一次可寻址、可追溯、可转化为学习行为与学习证据的 Learning Turn。**

Markdown 只负责**表现**；真正的信息模型应负责：

**语义 → 来源 → 上下文 → 学习行为 → 学习产物 → Learning Evidence。**

这与 Askora 当前 `main` 的方向是一致的：现有 UI Contract 已要求 Assistant 使用 `RichMessage` typed allowlist，并要求资料型回答能够追踪到 `SourceSpan`，明确不允许模型任意指定组件。

更重要的是，Askora 当前 Product Positioning 已冻结：

> **Conversation ≠ Learning Evidence。用户说“我懂了”不能直接证明掌握。**

所以消息系统的核心不是“给 AI 内容增加更多按钮”，而是：

```text
Information
↓
Interaction
↓
Learner Action
↓
Observable Evidence
↓
Learner State Update
```

---

## 设计依据：为什么这样做

学习科学给出的方向相当一致：

- **Retrieval Practice** 对长期保持的价值明显高于单纯重复阅读；而且优势可延伸到理解和推理任务。
- 学习者主动生成 **Self-explanation** 有助于形成不依赖示例的理解，而不仅是看懂 AI 的解释。
- 作答后的**反馈**能够纠错，并降低错误答案被保留下来的风险。
- **Spacing / Distributed Practice** 对长期保持有稳定证据，因此“加入复习”有价值，但不意味着产品必须成为 Anki。
- Working Memory / Cognitive Load 研究意味着交互本身也消耗认知资源，因此“更多工具栏”并不等于“更好的学习工具”。

因此 Askora 的 Message UI 应优先促进：

> **追问 → 回忆 → 作答 → 反馈 → 纠错 → 沉淀 → 延迟复习 → 迁移**

而不是：

> 阅读 → 点击更多 AI 功能 → 阅读更多。

---

# A. Message System Mental Model

## Canonical Definition

> **Message 是 Learning Turn 的呈现容器；Block 是其中可寻址的学习语义单元；Learning Action 将这些单元转化为学习行为和学习证据。**

需要严格区分三层：

```text
Message
≠ Markdown Document
≠ Block Editor
≠ Knowledge Base

Message
= Learning Turn
```

进一步：

```text
Markdown
→ Presentation

Semantic Block
→ Meaning

Provenance
→ Where it came from

Learning Action
→ What learner can do with it

Learning Evidence
→ What learner actually demonstrated
```

---

## 什么才是最小语义单元？

我建议引入一个内部概念：

### Addressable Learning Unit（ALU，可寻址学习单元）

只有满足以下至少一个条件，内容才值得成为独立 Block：

1. 有**独立来源 / Provenance**
2. 有**独立交互**
3. 有**独立学习状态**
4. 需要**专门 Renderer**
5. 需要被稳定引用、保存或复用

例如：

- 一段普通解释：通常不是特殊 Block。
- 一个 Definition：可能值得成为 `KnowledgeBlock`。
- 一段教材原文：必须是 `EvidenceQuoteBlock`。
- 一个 Retrieval Question：必须是 `LearningPromptBlock`。
- 一个公式：因为需要专用 renderer，可以独立。
- Bold：绝不需要成为 Block。

这是防止 Askora Block Taxonomy 失控的核心规则。

---

# B. Message Anatomy

我建议最终结构收敛为：

```text
Message
│
├── Content Flow
│   ├── ProseBlock
│   ├── KnowledgeBlock
│   ├── EvidenceQuoteBlock
│   └── RenderBlock
│       ├── Math
│       ├── Code
│       ├── Table
│       ├── Media
│       └── Visualization
│
├── Learning Flow
│   ├── LearningPromptBlock
│   └── FeedbackBlock
│
├── Provenance
│   ├── SourceRef
│   ├── SourceSpan
│   └── Locator
│
├── Anchors
│   ├── BlockRef
│   └── TextRangeRef
│
└── Optional Pedagogical Suggestion
    └── One Next Learning Action
```

**真正的一等 Block Family 只有 6 类：**

1. `ProseBlock`
2. `KnowledgeBlock`
3. `EvidenceQuoteBlock`
4. `RenderBlock`
5. `LearningPromptBlock`
6. `FeedbackBlock`

不是 30 类。

---

## 一个非常重要的架构决定

不要：

```text
Message
└─ Block
   └─ actions:
      ["explain", "quiz", "save", "why", ...]
```

让 LLM 随意生成 UI。

应该：

```text
AvailableActions
=
InteractionPolicy(
    BlockSemantic,
    Selection,
    Provenance,
    LearningState
)
```

也就是：

> **AI 决定内容语义；Askora 决定允许什么交互。**

---

# C. Block Taxonomy

| Block / 内容 | 用途 | 一等公民？ | Canonical 表达 | 主要操作 | 优先级 |
|---|---|---:|---|---|---|
| Paragraph / Heading / List | 阅读结构 | 否 | `ProseBlock` 内部结构 | Selection | Must |
| Bold / Italic | 强调 | 否 | Inline mark | 无 | Must |
| Highlight | 用户标记 | 否 | Annotation | 加入笔记等 | Later |
| Checklist | 任务状态 | 否 | 普通 List；学习任务另建 Prompt | — | Do not genericize |
| Definition / Concept / Key Point / Principle / Claim | 核心知识 | **是** | `KnowledgeBlock(role=...)` | 追问、笔记、测试 | Must |
| Explanation | AI 解释 | 否 | `ProseBlock(role=explanation)` | Selection | Must |
| Example / Counterexample / Analogy / Comparison | 建构理解 | 否 | `ProseBlock(role=illustration)` | Selection / 追问 | Must |
| Cause→Effect / Reasoning / Summary / Conclusion | 内容组织 | 否 | Prose semantic role | Selection | Must |
| 原文 Quote | 证据、出处 | **是** | `EvidenceQuoteBlock` | 查看原文、笔记、追问 | Must |
| Citation / Source / Page / Timestamp | Provenance | **是，但不是视觉 Block** | `SourceRef / SourceSpan` | 打开来源 | Must |
| Formula / Math | 专用表现 | 是：Renderer | `RenderBlock(math)` | Copy/selection | Must |
| Code | 专用表现 | 是：Renderer | `RenderBlock(code)` | Copy | Should |
| Table | 结构化数据 | 是：Renderer | `RenderBlock(table)` | — | Should |
| Image | 媒体证据/解释 | 是：Renderer | `RenderBlock(media)` | 来源/放大 | Should |
| Diagram / Flowchart / Timeline / Visualization | 模型表达 | 是：Renderer | `RenderBlock(visualization)` | 展开 | Later/Should |
| Question / Socratic / Quiz / Exercise / Reflection | 主动学习 | **是** | `LearningPromptBlock(mode=...)` | 作答、提示 | Must |
| User Answer | 学习行为 | **是，但属于 Attempt** | `Attempt` | — | Must |
| AI Feedback | 评估 | **是** | `FeedbackBlock` | 查看解释/再试 | Must |
| Hint / Correction / Misconception | 补救教学 | **是，作为 Feedback subtype** | `FeedbackBlock(mode=...)` | 再试/复习 | Must |
| Knowledge Gap | Learner Model | 否 | State / Evidence metadata | — | Must backend |
| Learning Action | 行为 | **不是内容 Block** | Interaction layer | — | Must |

---

## 被遗漏但真正重要的不是更多 Block

真正缺少的是这些**非视觉领域对象**：

```text
SourceAnchor
TextRangeAnchor
ConceptRef
Attempt
LearningEvidence
UserAnnotation
Note
ReviewItem
ConversationAnchor
```

它们比增加：

```text
AnalogyBlock
ConclusionBlock
KeyTakeawayBlock
CounterExampleBlock
```

重要得多。

---

# D. Interaction Hierarchy

原则：

> **内容始终出现，工具只有在有理由时出现。**

## Always Visible

只显示：

- Message 内容
- 必要的语义标签，例如 `原文`、`理解检查`、`反馈`
- Quote 的 Source + Locator
- Question 的答题入口
- Feedback 的结果
- 必要时一个 AI 推荐的下一学习动作

普通解释段落**零常驻按钮**。

---

## Hover / Focus

Block Hover 时最多：

```text
[追问] [加入笔记] [⋯]
```

而且并非所有 Block 都出现两个。

---

## Selection

默认最多：

```text
[追问] [加入笔记] [Contextual Action] [⋯]
```

第三个根据内容变化。

---

## Contextual

例如：

**Quote**

```text
查看原文
```

**Knowledge**

```text
测试理解
```

**Question**

```text
提交 / 提示
```

**Feedback**

```text
再试一次
```

**Code**

```text
复制代码
```

---

## More

放低频 Utility：

```text
复制
加入复习（符合条件时）
在支线继续（以后）
复制引用
```

---

## AI-generated

AI 最多主动提出 **一个 Next Learning Move**。

例如：

```text
测试一下你的理解 →
```

而不是：

```text
[为什么]
[解释]
[举例]
[测试]
[总结]
[卡片]
[深入]
```

---

# E. Quote Block Canonical Design

Quote 是 Askora 最值得做成 First-class Block 的内容之一。

## 推荐结构

```text
原文

│ 牛顿第一定律指出，当物体所受合外力为零时，
│ 物体将保持静止或匀速直线运动状态。

《大学物理》 · P42

                     加入笔记   追问   ⋯
```

其中：

### 永久可见

```text
原文内容
来源名称
Locator：P42 / §3.2 / 12:42
```

### 点击来源

统一进入：

```text
Open Source Context
```

显示：

```text
上一段
目标原文
下一段

完整 Source Metadata
```

因此不要同时提供：

- 查看来源
- 查看原文
- 查看上下文
- Citation

四个按钮。

它们实际上属于一个用户目标：

> **验证这段内容到底来自哪里。**

Canonical 操作统一为：

### `查看原文`

---

## Quote 一级操作

只需要两个：

```text
加入笔记
追问
```

来源本身可点击，因此不额外占一个按钮。

---

## More

```text
复制原文
复制引用
```

足够。

---

## 不应该直接出现

```text
收藏
高亮
解释
为什么
举例
简单解释
生成 Flashcard
加入复习
```

原因：

- 收藏与 Notes 重复；
- Highlight 与保存知识目的重叠；
- 解释/为什么/举例本质都是 `追问`；
- 原始 Quote 本身不一定值得记忆；
- Flashcard 不应由任意文本直接生成。

---

# F. Text Selection Canonical Design

这是我认为 Askora 非常值得做好的核心 Interaction。

用户选中：

> 相变潜热是在物质发生相变过程中吸收或释放的能量。

出现：

```text
追问     加入笔记     测试理解     ⋯
```

但第三项动态决定。

---

## 一级操作固定两个

### 1. 追问

这是最重要的 Selection Action。

点击后 Composer 自动获得 Context Anchor：

```text
↳ 关于「相变潜热是在……」
```

用户可以直接输入：

```text
为什么？
```

AI 知道问题所针对的精确 TextRange。

因此不需要：

```text
Explain
Why
Example
Counterexample
Simplify
Deep Dive
```

六个按钮。

它们只是 `追问` 的不同意图。

---

### 2. 加入笔记

把当前选区变成结构化 Note input。

---

## 第三个 Contextual Action

### Source-backed selection

```text
查看原文
```

### Knowledge / Concept

```text
测试理解
```

### 普通文本

**不显示第三个。**

不要为了按钮数量一致而制造功能。

---

## More

```text
复制
加入复习（仅 eligible）
在支线继续（Later）
```

---

## AI 是否理解选中内容？

应该。

但职责边界必须明确：

```text
AI
→ 理解 Selection Semantic

Application
→ 决定允许显示什么操作
```

AI 不应该输出：

```json
"buttons": ["Explain", "Save", "Quiz"]
```

---

# G. Note Integration

这是另一个需要彻底改掉“复制文字”思维的地方。

## Add to Notes ≠ Copy Text

推荐：

```text
Note
├── User Synthesis
├── Evidence[]
│   ├── Original Quote
│   ├── SourceRef
│   └── SourceSpan
├── AI Context[]
├── ConceptRefs[]
├── Origin
│   ├── ConversationId
│   ├── MessageId
│   └── BlockId / TextRange
└── User Annotation
```

---

## 当保存 Quote 时

应该保存：

```text
原文（immutable）
+
Source ID
+
Page / Timestamp / Range
+
Message / Block Anchor
+
用户自己的 annotation（可选）
```

而不是只有：

> 牛顿第一定律指出……

否则几个月后用户已经不知道：

- 谁说的？
- 来自哪里？
- 为什么当时保存？
- AI 有没有改写？
- 当时学习什么？

---

## 当保存 AI Explanation 时

必须明确记录它是：

```text
AI-generated explanation
```

而不能在以后展示时看起来像教材原文。

这是非常重要的 Knowledge Provenance 边界。

---

## 默认不推荐

```text
Add entire Message to Notes
```

Message 通常太粗。

优先：

```text
Selection
KnowledgeBlock
EvidenceQuoteBlock
```

形成知识沉淀。

---

# H. Askora 最核心的 6 个 Learning Actions

我建议最终只冻结 **6 个**。

## 1. 追问 Ask

解决：

> 我没有真正理解。

包含：

- 为什么
- 解释
- 简单一点
- 举例
- 反例
- 比较
- 深入

这些不是 7 个产品功能。

---

## 2. 查看原文 Inspect Source

解决：

> 这是真的吗？来自哪里？上下文是什么？

建立：

**AI Explanation ↔ Evidence**

---

## 3. 加入笔记 Capture

解决：

> 这值得成为我的长期知识。

核心不是保存，而是**知识沉淀**。

---

## 4. 测试理解 Retrieve

解决：

> 我感觉懂了，但我实际上能不能自己说出来？

这是 Askora 从 Chatbot 转向 Learning Product 的关键 Action。

---

## 5. 加入复习 Review

解决：

> 我现在理解了，但以后可能忘。

它创建的是：

```text
ReviewItem
```

不是：

```text
Flashcard
```

---

## 6. 应用一下 Apply

解决：

> 我能不能把它迁移到新的情境？

例如学完：

```text
p = mv
```

Askora 给出一个陌生情境让用户使用，而不是继续解释。

---

## 这 6 个动作对应完整闭环

```text
不理解
→ 追问

需要验证
→ 查看原文

值得沉淀
→ 加入笔记

验证掌握
→ 测试理解

长期保持
→ 加入复习

验证迁移
→ 应用一下
```

足够。

---

# Inline Learning Actions

### 有价值，但必须严格限制。

不应该：

```text
动量是 p = mv

[我理解了] [为什么] [举例] [测试] [笔记]
```

尤其：

### `[我理解了]` 应删除。

Askora 自身 Product Positioning 已经明确自我报告不能构成掌握证据。

应该在一个完整教学单元结束时，最多出现：

```text
测试一下你的理解 →
```

或者：

```text
应用一下 →
```

### Canonical Rule

> **每一个 pedagogical stopping point 最多一个 AI-generated Learning Action。**

而不是每个 Block 一个 CTA。

---

# Message-Level Actions

Message 级别只保留最低限度 Utility。

### 通用聊天工具

进入 Hover / More：

```text
复制
重新生成（仅必要时）
问题反馈
```

### 不做成 Message-level 主操作

```text
Save Message
Add Message to Notes
Generate Summary
Turn into Quiz
Add Message to Review
```

这些粒度太粗。

学习行为应该附着到：

```text
Block
Selection
Concept
Attempt
```

而不是整个 Assistant Message。

---

# 从学习闭环反推 UI

```text
阅读
→ Prose

理解
→ Knowledge / Illustration

产生疑问
→ Anchored Ask

解释 / 举例
→ Scoped Follow-up

主动回忆
→ LearningPrompt

作答
→ Attempt

反馈
→ Feedback

发现错误
→ Misconception / Correction

重新作答
→ Attempt

形成理解
→ Note

延迟复习
→ ReviewItem

迁移
→ Application Prompt
```

因此真正应该冻结的是：

```text
Message.Block
      ↓
Learning Action
      ↓
Learning Artifact / Attempt
      ↓
Learning Evidence
      ↓
Learner State
```

而不是：

```text
Message
↓
Message
↓
Message
↓
Message
```

---

# Conversation Branch

## 这个方向有价值，但不要立即建立“对话树产品”。

真正的问题不是：

> 我们需不需要 Branch？

而是：

> Askora 能否理解“这个问题只针对这里”？

### v1 先解决 Anchoring

用户选中：

```text
工作记忆容量有限
```

点击：

```text
追问
```

Composer：

```text
↳ 工作记忆容量有限

为什么？
```

数据：

```text
ContextAnchor
├─ messageId
├─ blockId
└─ textRange
```

这已经解决大约 80% 的局部追问问题。

---

## Later 再做真正 Branch

之后可以：

```text
KnowledgeBlock
└── Focus Thread
    ├── Why
    ├── Example
    └── Deep Dive
```

用户完成后回到主线。

### 不建议 v1 做

完整树状：

```text
Conversation
├─ Branch A
│  ├─ A1
│  └─ A2
├─ Branch B
...
```

这会引入极高的导航和状态复杂度。

---

# Review / Memory Canonical Model

这里也必须避免 Anki 化。

## 用户操作叫：

### `加入复习`

而不是：

```text
Generate Flashcard
Remember This
```

后台产生：

```text
ReviewItem
├── TargetKnowledge
├── RetrievalPrompt
├── EvaluationCriteria
├── SourceRefs
├── NoteRefs
├── AttemptHistory
└── SchedulingState
```

然后未来它可以呈现为：

- 问答
- Cloze
- 概念解释
- 应用题
- Flashcard

### Flashcard 是 Renderer。

### ReviewItem 才是 Domain Object。

这是一个非常重要的产品边界。

---

# 消息视觉层级

不要 Card Everywhere。

推荐只有四种明显的视觉语义：

### 1. Explanation Flow

最低视觉权重。

```text
普通 AI 解释……
普通 AI 解释……
```

### 2. Knowledge Anchor

稍微强化。

```text
关键概念
━━━━━━━━━━
Working Memory

短期保存并操作信息的认知系统。
```

### 3. Evidence

明显与 AI Voice 区隔。

```text
原文

│ Working memory has limited capacity...

Sweller · P24
```

### 4. Learning Activity

最强交互性。

```text
理解检查

为什么工作记忆限制会影响复杂问题求解？

[回答……]
```

用户因此能视觉上区分：

```text
AI 在解释什么
什么是核心知识
证据是什么
现在轮到我做什么
```

这比给 Definition、Example、Summary 分别设计十种彩色 Card 更重要。

---

# I. v1 删除清单

以下功能看起来合理，但我建议明确 **不进入 v1**：

### 1. `[我理解了]`

不能构成 Learning Evidence。

### 2. Favorite / 收藏

与 Notes / Review 语义重叠。

### 3. AI Message 全局 Highlight 系统

很容易演化成复杂阅读器；Selection + Note 已足够。

### 4. 每个 Paragraph 的 Toolbar

典型 Toolbar Hell。

### 5. `为什么 / 解释 / 举例 / 简单解释 / 深入解释`五个按钮

统一为：

```text
追问
```

### 6. Everywhere “Generate Flashcard”

会快速 Anki 化。

### 7. Auto-generate Flashcards for every Key Point

生成大量低价值复习债务。

### 8. Message → Turn into Quiz

粒度过粗。

应针对明确 `KnowledgeRef` 测试。

### 9. Message → Add All to Notes

形成 AI 内容仓库，而不是用户知识库。

### 10. Message → Add All to Review

制造 Review Queue 垃圾。

### 11. 自动创建 Conversation Branch

用户每个为什么都变成树节点，成本远高于收益。

### 12. Notion 式 Drag / Drop / Reorder Blocks

Askora 不是 Block Editor。

### 13. DefinitionBlock / AnalogyBlock / SummaryBlock / ConclusionBlock 等几十种组件

把语义标签误做成 UI 架构。

### 14. Like / Dislike 常驻

除非以后明确用于模型质量反馈，否则没有核心学习价值。

### 15. AI 自动把内容加入 Review

学习责任和 Review Queue 应由用户掌控。

### 16. Conversation 内 Deck / Tag / Card Management

属于 Anki 产品模型，不属于 Learning Conversation。

---

# 三种方法论审查

## 苏格拉底提问

**为什么 Definition 要独立 Block？**

因为需要独立引用和测试，而不是因为“Definition 看起来应该有卡片”。

因此合并成：

```text
KnowledgeBlock(role=definition)
```

**为什么 Quote 要独立？**

因为它具有独立 Provenance、SourceSpan、验证操作。

因此保留。

**为什么需要 7 个 Quote 按钮？**

不需要。用户的目标实际上只有：

```text
验证
沉淀
继续理解
```

所以收敛为：

```text
查看原文
加入笔记
追问
```

---

# 第一性原理审查

Askora 的目标不是：

> 更方便地操作 AI 内容。

真正目标是：

```text
理解
记忆
纠错
迁移
```

所以：

- Copy 不重要；
- Like 不重要；
- Retry 不重要；
- Flashcard 按钮本身也不重要；

而：

```text
Ask
Retrieve
Feedback
Capture
Review
Apply
```

才是核心。

---

# 奥卡姆剃刀审查

如果：

```text
Explain
Why
Example
Simplify
Counterexample
```

都可以通过：

```text
选中 → 追问
```

完成，就只保留一个。

如果：

```text
Definition
Concept
Principle
Claim
Key Point
```

具有相同的基本状态与交互，则：

```text
KnowledgeBlock(role=...)
```

优于 5 个组件。

如果：

```text
查看来源
查看上下文
打开原文
Citation
```

都服务于 Provenance，则统一：

```text
查看原文
```

---

# J. Askora Learning Conversation Message System — Canonical Design

## Must Have

### 信息模型

```text
Message ≠ Markdown Blob
```

使用 Typed Semantic Message。

### 六类核心 Block

```text
ProseBlock
KnowledgeBlock
EvidenceQuoteBlock
RenderBlock
LearningPromptBlock
FeedbackBlock
```

### Provenance

至少支持：

```text
SourceRef
SourceSpan
Locator
BlockRef
TextRangeRef
```

### Selection

```text
追问
加入笔记
Contextual Third Action
⋯
```

最多三个一级操作。

### Quote

```text
Source + Locator 始终可见
点击来源 → Source Context
Hover → 加入笔记 / 追问 / ⋯
```

### Learning Loop

```text
Prompt
→ Attempt
→ Feedback
→ Learning Evidence
```

必须形成真正的数据闭环。

### 学习状态

绝不能因为：

```text
我理解了
```

直接提高 Mastery。

---

# Should Have

```text
加入复习 → ReviewItem

应用一下 → Transfer Prompt

AI 在合适节点推荐一个 Next Learning Action

结构化 Note + Evidence provenance

错误 / Misconception → Remediation
```

---

# Later

```text
Block-attached Focus Thread
Spaced Review Scheduling
Adaptive Retrieval Difficulty
更丰富 Diagram / Visualization
跨 Conversation Concept Graph
Flashcard 作为 Review Renderer
Source Context Explorer
```

---

# Do Not Build

```text
Notion-style Block Editor

Anki-style Deck Management

几十种 semantic component

每段 Toolbar

自动 Flashcard 工厂

AI 自由生成 UI actions

“I understand” mastery

全局复杂 Conversation Tree

Add entire AI answer to knowledge base

Everywhere Save / Favorite / Highlight
```

---

# 最终 Canonical Mental Model

```text
                    Askora Learning Message

                           Message
                              │
             ┌────────────────┼────────────────┐
             │                │                │
          Content         Provenance       Learning
             │                │                │
     ┌───────┼───────┐   SourceSpan     Prompt / Feedback
     │       │       │        │                │
   Prose  Knowledge Evidence  Source         Attempt
                     │                         │
                     │                  Learning Evidence
                     │                         │
                     └─────────┬───────────────┘
                               ↓
                         Learning Action
                               │
          ┌────────┬────────┬───┴───┬────────┬────────┐
          ↓        ↓        ↓       ↓        ↓        ↓
         追问    查看原文   笔记   测试理解   复习    应用
          │        │        │       │        │        │
          └────────┴────────┴───────┴────────┴────────┘
                               ↓
                       Learner State Update
```

## 最核心的一条产品原则

> **Askora 不应该让 Message 变得“更可操作”，而应该让 Message 更容易产生有学习价值的下一步行为。**

因此我认为这套系统真正需要冻结的核心不是“支持多少种消息格式”，而是三个边界：

```text
1. 什么值得成为可寻址语义单元？
2. 什么学习行为值得从消息直接触发？
3. 什么用户行为有资格更新 Learner State？
```

只要这三个边界冻结，Markdown、视觉样式、Context Menu、Notes、Review、Branch 都可以围绕它们自然展开，而不会逐步膨胀成 ChatGPT + Notion + Anki 的混合体。
