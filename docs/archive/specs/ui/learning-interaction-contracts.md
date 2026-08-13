# Askora Learning Interaction Contracts

> 状态：**Canonical UI/UX Implementation Contract — Current Only**  
> 冻结日期：2026-08-11  
> 上游产品定义：`CAP-04`、`CAP-05`、`CAP-06`、`CAP-07`  
> Governing Experience：`docs/design/experience/LEARNING-EXPERIENCE.md`、`docs/design/experience/INTERACTION-MODEL.md`  
> Governing ADR：ADR-0018、ADR-0019、ADR-0022
> 技术上游：Assessment / Teaching Policy / Activity Lifecycle / Render / Workspace Read Projection current Specs

---

## 1. Purpose

本文件把 Askora 的 Learning Experience 转化为可实现、可测试的 UI interaction contract。

它定义：

- Learning Canvas composition；
- learning conversation / learning unit 的呈现语义；
- Question / Attempt / Feedback / Hint / Remediation；
- assistance / answer exposure / validation obligation；
- streaming；
- citation / SourceSpan / Current Material；
- Learning Notes；
- Learning Context Drawer；
- long-session continuity；
- keyboard / screen-reader order。

本文件不拥有 TeachingAction、AssessmentResult、LearningEvidence、MasteryEstimate、ReviewSchedule、LLM prompt 或 persistence schema。

---

## 2. LearningActivity Is the UI Context

### UI-LRN-001

LearningActivity 是 Learning Workspace 的主要体验上下文。单条 message、prompt 或 session 不得成为独立产品主对象。

### UI-LRN-002

进入/切换 Course/Activity presentation、展开 Drawer、打开 Material、隐藏 Right Rail 不得生成新的：

```text
LearningActivity
Attempt
TeachingAction
AssessmentResult
transcript truth
```

### UI-LRN-003

兼容 `/quick/:sessionId` 或历史 dialog 必须明确 compatibility source；缺少 canonical activity/policy/evidence data 时显示“当前记录不可用”，不得补造。

### UI-LRN-004 — Course Scope

Learning Workspace 必须显示用户可理解的当前课程，并解析同一 canonical `workspace_id`。Course route、Activity ref 与 Workspace query 不一致时 fail closed，不得用 route 覆盖 owner truth。

### UI-LRN-005 — Activity Switcher / Recent Learning

Activity Switcher 只读取当前 Course 内 exact Activity refs：

- current/active/resumable/available state 来自 SYS06 owner；
- title 描述学习目的，不使用 Chat 1/2/3；
- 打开 active/resumable Activity 不复制 Activity、Session 或 transcript；
- 启动 available Activity 调用正式 lifecycle Action；
- conversation/message count 不参与排序或学习优先级推断。

---

## 3. Learning Canvas Composition

中央 Learning Canvas 按以下优先级组织：

```text
Current learning task / teaching content
→ learner thinking / input
→ feedback / remediation
→ necessary assistance / validation state
→ necessary citation / source context
→ lightweight orientation
```

### UI-LRN-010 — Required Regions

适用时至少包含：

- 当前 Activity / task identity；
- teaching / question content；
- learner response input；
- feedback/result；
- Composer / submit action；
- streaming/error/recovery status；
- validation obligation；
- citation / source affordance。

### UI-LRN-011 — No Dashboard Competition

Goal/Plan/Progress/Evidence chart、Knowledge Graph、system diagnostics 不得与当前学习任务形成等权 permanent region。

---

## 4. Learning Conversation / Unit Semantics

### UI-LRN-020 — Required Learning Roles

UI 必须能让用户区分以下语义角色：

```text
Teaching / Explanation
Question / Task
Learner Attempt
Feedback
Hint / Scaffold
Remediation
Source / Evidence Context
Status / Recovery
```

这些是 Experience roles，不要求形成新的 backend enum；当 backend 提供 typed render payload 时应优先使用 canonical payload。

### UI-LRN-021 — Message Identity

无论使用开放内容、bubble、card 或其他 pattern，都必须保持：

- origin / role；
- message/event order；
- Activity/session association；
- durable content fallback；
- structured payload validity；
- citation/provenance；
- assistance / validation state（存在时）。

### UI-LRN-022 — No Bubble-only Model

Assistant 长解释、Question、Feedback 或 structured learning content 不要求统一套聊天气泡。视觉选择应服务阅读、推理和学习角色识别。

User short Attempt 可以使用紧凑 presentation，但不得因视觉样式丢失 Attempt identity。

### UI-LRN-023 — Grouping

连续消息 MAY 按同一 teaching turn / task context 进行视觉分组，但不得：

- 重排 durable event order；
- 合并不同 Attempt；
- 把历史 Feedback 冒充当前 Feedback；
- 因分组隐藏 citation / assistance / validation semantics。

长历史可以分页/虚拟化，但当前 task、最近 Attempt、当前 Feedback 与 active streaming state 必须稳定可达。

---

## 5. Question / Task

### UI-LRN-030

Question / Task 必须具有明确视觉起点，不能埋在长 explanation 末尾而无可识别 task boundary。

### UI-LRN-031

当 activity 要求 active retrieval / generation / reasoning 时，UI 必须提供真实 learner input opportunity；不得自动填充 AI answer 并把其视为 learner response。

### UI-LRN-032

任务所需 source / constraints / expected response form 应在用户作答前可理解；内部 grader-only rubric 不得泄露。

---

## 6. Learner Attempt

### UI-LRN-040 — Attempt Integrity

用户提交后的 Attempt 必须保留其原始内容与 identity。Feedback、AI rewrite 或 retry 不得静默覆盖历史 Attempt。

### UI-LRN-041 — Submit Semantics

Submit 是 `Action`：

- pending 时 single-flight；
- 不允许重复 accidental submit；
- success/failure 必须来自正式 command/result；
- `pressed`/local optimistic state 不等于成功；
- 提交失败不得把用户输入静默清空。

### UI-LRN-042 — Retry

Retry / “再试一次”产生新的 learner behavior。是否形成新的 LearningEvidence 以及证据权重由 Assessment/Evidence owner 决定，frontend 不推断。

---

## 7. Feedback & Remediation

### UI-LRN-050 — Feedback Anatomy

Feedback 应在可用数据范围内表达：

- 哪部分成立；
- 哪部分需要修正；
- 关键原因；
- 当前合法下一步。

不得只依赖绿色/红色、score 或 emoji 表达正确性。

### UI-LRN-051 — Learner Error vs System Error

以下故障不得显示成“你答错了”：

- model/provider failure；
- tool failure；
- retrieval/source failure；
- network/runtime error；
- invalid structured payload；
- stale/version conflict。

### UI-LRN-052 — Remediation

Remediation 应保持当前 Workspace / Activity / source context。UI 不应因为一次错误自动把用户送往全局知识库、独立 chat 或无限分支。

### UI-LRN-053 — Recovery

retryable system failure 可以提供 Retry Action；不可 retry 的状态应给出对应 owner-defined RecoveryAction / next step。不得通过重新创建 Activity/Session 假装恢复。

---

## 8. Assistance / Answer Exposure

### UI-LRN-060 — Planned vs Actual

UI 必须区分：

```text
allowed / planned assistance envelope
actual assistance already used
```

缺 actual data 时不得复制 planned data 作为事实。

### UI-LRN-061 — User-readable Assistance State

存在 canonical data 时，使用学习者可理解表达，例如：

```text
独立作答
已使用帮助
已看到关键步骤
已暴露答案
待独立验证
```

UI 不得根据 message length、card variant、click count 或文本内容推断 canonical assistance state。

### UI-LRN-062 — Help Controls Are Requests

“给一点提示”“解释概念”“给例子”“拆成步骤”“直接告诉我”等控件是用户 request `Action`，不是 TeachingAction editor。

### UI-LRN-063 — Autonomy Without Evidence Corruption

用户可以请求完整答案。UI 不得用交互阻止合法用户自主选择；但答案暴露后的表现不能被文案/视觉包装为无提示独立掌握。

### UI-LRN-064 — Validation Obligation

需要 fresh independent validation 时必须呈现“待独立验证”或等价用户文案。它不是 error，也不是惩罚状态。

---

## 9. Streaming Contract

### UI-LRN-070 — Streaming State Machine

至少区分：

```text
RUN_STARTING
STREAMING_CONTENT
FINAL_PAYLOAD_VALIDATING
COMPLETED
FAILED
RECOVERABLE
```

### UI-LRN-071

partial text MAY 增量显示，但半完成 structured payload 不得被当作 final Question / Feedback / Card contract 渲染。

### UI-LRN-072

最终 structured payload 只有通过 schema / safe-render validation 后才替换或增强 fallback content。

未知/无效 payload 必须安全回退 durable `content`；不得渲染 raw HTML、MDX、executable model-defined component 或未授权 remote image。

### UI-LRN-073

断线/重连/重试不得产生重复 assistant message、Attempt、LearningEvent 或 Evidence。

### UI-LRN-074

stream 进行中离开/切换 Workspace 时必须进入当前 owner/route contract 定义的明确状态，不得仅通过卸载 component 丢弃运行。

---

## 10. Citation / Provenance

### UI-LRN-080 — Traceable Source

资料型回答的引用必须可追踪 SourceSpan / canonical source ref。

主要显示：

- 可读 source label；
- locator / 原文位置；
- “查看原文”等可预测 affordance。

内部 UUID/version 可放 Disclosure，不作为唯一用户信息。

### UI-LRN-081 — Source vs Model Knowledge

当内容不是来自用户 Material 时，不得通过 citation style、标题或措辞假装“来自资料”。

### UI-LRN-082 — View Source In Context

在 Learning Workspace 中查看 source 优先打开 Right Rail Current Material，不使 Center 离开当前 learning context。

### UI-LRN-083 — Missing Source

缺 SourceSpan / 可显示原文时显示不可用/来源不足。禁止使用 AI Summary、filename 或模型记忆伪造原文。

### UI-LRN-084 — Cross-Workspace Fail Closed

Material/source ref 必须属于当前 Workspace scope；跨 Workspace ref 不得通过错误信息泄露对象是否存在。

---

## 11. Current Material Tabs

### UI-LRN-090

Right Rail Current Material 可以由 citation / view-source 打开一个或多个 tabs。

打开、切换、关闭 tab：

- 属 Navigation / Disclosure；
- 不改变 Center Activity；
- 不产生 business write；
- 不创建新的 Activity/TeachingAction；
- tab/source position 是 presentation state，可在合法范围恢复。

### UI-LRN-091

V1 不提供 generic `+` extension host，不为 deferred modules 创建 tab placeholder。

---

## 12. Learning Notes

### UI-LRN-100 — User-authored Truth

Learning Notes 是 Product Definition 中的 `UserNote`，是 user-authored durable data；不是 AI Summary，也不是 canonical Material/Knowledge truth。

### UI-LRN-101 — Scope / Anchor

Notes 必须服从 current Workspace scope，并在 owner contract 支持时保留 Activity / Material anchor。

### UI-LRN-102 — Required Note States

UI 必须区分：

```text
SAVING
SAVED
FAILED
CONFLICT
RECOVERABLE
```

未持久化时不得显示“已保存”。

### UI-LRN-103 — Conflict

version/revision conflict 不得静默覆盖较新 durable note；应重新读取并要求用户明确处理。

### UI-LRN-104 — AI Assistance

AI 可在用户明确请求时辅助整理/改写笔记，但不得无确认覆盖 user-authored original。

### UI-LRN-105 — Source to Note

“引用/加入笔记”类快捷动作只有在 UserNote owner/anchor contract 支持时可出现。

合法实现应保留：

- 用户可编辑文本；
- source/material anchor（若有）；
- Workspace scope；
- saving/conflict feedback。

不得把 AI 自动摘要直接写成用户笔记。

---

## 13. Learning Context Drawer

### UI-LRN-110 — Placement / Default

Drawer 在 Composer 上方，默认收起，不占 Right Rail。

### UI-LRN-111 — Collapsed

只显示一行轻量方向，例如：

```text
当前阶段 · 接下来：……
```

### UI-LRN-112 — Expanded

只允许：

- current stage；
- stage goal；
- next 1..3 dynamic learning directions。

### UI-LRN-113 — Data States

至少区分：

```text
LOADING
READY
MISSING
PARTIAL
STALE
ERROR
```

MISSING/PARTIAL/STALE 不得冒充 READY。

### UI-LRN-114 — No Frontend Inference

Drawer 内容必须来自 canonical/versioned projection；frontend 不得从 chat、heading sequence、probability threshold 推断 next knowledge point。

### UI-LRN-115 — Presentation Only

expand/collapse 是 Disclosure presentation state，不触发 owner command；Drawer failure 不得无条件阻断当前 Attempt。

---

## 14. Long-session / History Behavior

### UI-LRN-120

当前 active task、最近 learner Attempt、对应 Feedback 和 active streaming state 必须容易定位。

### UI-LRN-121

历史内容可 virtualize/paginate；durable event order 不得因 performance optimization 改变。

### UI-LRN-122

历史 state 必须与 current active state 视觉/语义分离。旧 TeachingAction、Plan、Evidence、DecisionTrace 不得冒充当前 truth。

### UI-LRN-123

恢复历史 session/activity 时优先恢复 durable active/resumable context；不存在 canonical link 时必须保留 compatibility label，不自动创建伪造 link。

---

## 15. Keyboard / Screen Reader Order

### UI-LRN-130 — Reading Order

Learning Canvas 的可访问阅读顺序原则上保持：

```text
Activity/task context
→ current teaching/question
→ learner Attempt/input
→ Feedback/status
→ Composer/actions
→ Context Drawer
→ Right Rail trigger / auxiliary content
```

具体 DOM 可以因 responsive pattern 调整，但 semantic order 不得让辅助栏先于主要学习任务占据读取主线。

### UI-LRN-131

stream/status/save/error 需要适当 live announcement，避免每个 token delta 都造成 screen-reader spam。

### UI-LRN-132

Drawer、Right Rail、Material tabs、transient sheet 必须：

- keyboard 可操作；
- Escape 关闭适用 transient surface；
- 关闭后 focus 返回触发点或合理下一目标；
- Contextual Action 不依赖 hover-only discoverability。

---

## 16. Forbidden Implementations

禁止：

- conversation completion → mastery；
- “我懂了” → LearningEvidence；
- assistant-generated answer → learner Attempt；
- actual assistance 缺失时用 planned assistance 冒充；
- frontend threshold → mastery label；
- 系统错误 → learner incorrect；
- structured streaming 半成品 → final card/assessment；
- raw HTML / executable model-defined UI；
- filename/summary → fabricated original；
- frontend-only note/localStorage → durable UserNote；
- 切换 Workspace / rail / route 静默丢 draft/stream/note；
- Activity Switcher 使用 Chat thread title/count 或跨 Course refs；
- Right Rail 建通用 extension host；
- 无限 chat thread 取代 LearningActivity continuity。

---

## 17. Acceptance Criteria

- `UI-LRN-AC-001`：LearningActivity 而非 chat/message 是主体验上下文；
- `UI-LRN-AC-002`：Question / Attempt / Feedback / Hint / Remediation / Source roles 可识别；
- `UI-LRN-AC-003`：提交 Attempt single-flight，失败不丢输入，retry 不覆盖历史 Attempt；
- `UI-LRN-AC-004`：learner error 与 model/tool/retrieval/runtime error 明确分离；
- `UI-LRN-AC-005`：planned vs actual assistance、answer exposure、validation obligation 不被 frontend 推断；
- `UI-LRN-AC-006`：streaming partial structured payload 不作为 final truth，重连不重复 event/message；
- `UI-LRN-AC-007`：citation 可追踪 SourceSpan，view source 保持当前 learning context；
- `UI-LRN-AC-008`：跨 Workspace source fail closed，缺原文不伪造；
- `UI-LRN-AC-009`：Notes 区分 SAVING/SAVED/FAILED/CONFLICT/RECOVERABLE，未持久化不宣称 saved；
- `UI-LRN-AC-010`：Drawer 只显示 stage/stage goal/next 1..3 且 frontend 不推断；
- `UI-LRN-AC-011`：历史/current state 不混淆，长 session 可扩展而不改 durable order；
- `UI-LRN-AC-012`：keyboard/screen-reader/focus/live-region 行为可自动/人工验证；
- `UI-LRN-AC-013`：UI interaction pass 不被描述成 Product Acceptance 或 Learning Evidence pass。
- `UI-LRN-AC-014`：Course / Activity / Session hierarchy 清晰，Activity Switcher 只使用当前 Course exact refs。
