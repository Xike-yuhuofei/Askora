# Askora Learning Experience

> 状态：**Canonical Learning Experience Baseline**  
> 冻结日期：2026-08-13  
> 适用范围：Askora v1 Learning Workspace、Learning Conversation、Attempt / Feedback / Evidence / Provenance Experience  
> 上游：[`../../product/PRODUCT-DEFINITION.md`](../../product/PRODUCT-DEFINITION.md)、[`EXPERIENCE-ARCHITECTURE.md`](EXPERIENCE-ARCHITECTURE.md)、历史设计基线见 [`archive/design/`](../../archive/design/)
> 交互语义：[`INTERACTION-MODEL.md`](INTERACTION-MODEL.md)  
> 资料解析模式：[`../../archive/adr/ADR-0029-local-and-hybrid-material-parse.md`](../../archive/adr/ADR-0029-local-and-hybrid-material-parse.md)
> 下游：Learning Interaction / Screen / Render / UI Data Specs

---

## 1. Purpose

本文件定义 Askora 最核心的用户体验：

> **用户如何从材料和目标进入主动学习，如何思考与作答，如何得到反馈与补救，如何理解帮助与来源，并如何进入下一轮独立验证、复习和长期掌握。**

它把 Askora 与普通 AI Chat、知识库阅读器、笔记工具或题库区分开来。

本文件定义的是 learning experience semantics，不拥有 Teaching Policy 算法、Assessment schema、Mastery estimator、LLM prompt、数据库消息结构或 API。

---

## 2. Core Experience Unit

### LEXP-001 — LearningActivity Is the Primary Unit

Askora 的主要体验单元是 `LearningActivity`，不是单条 message、prompt 或 chat session。

一项 LearningActivity 应具有明确学习目的，并能够包含：

- 教学解释；
- 问题或任务；
- 学习者 Attempt；
- Feedback；
- Hint / Scaffold；
- Remediation；
- Source / Citation；
- Validation obligation；
- 结束或下一步方向。

Conversation 可以承载这些行为，但界面不得因此把“聊天轮次”当作学习结构。

### LEXP-002 — Session Is Continuity, Not Identity

LearningSession 服务连续学习过程与恢复；它不是登录 Session，也不应成为用户必须管理的主要对象。

跨 session 的真实学习连续性来自 Workspace、Goal/Activity、Evidence 与可恢复状态，而不是无限长的聊天线程。

### LEXP-003 — Space Organizes Multiple Conversations

用户界面以「空间」表达 canonical Workspace，以「对话」表达该空间内一次可恢复的 `LearningActivity`。一个空间可以包含多段对话；恢复入口必须用学习目的组织，而不是用 Chat thread 命名或 conversation turn count 组织学习。

---

## 3. Canonical Learning Experience Loop

用户侧主路径见 Experience Architecture `EXP-JOURNEY-003`。本节冻结该路径内部的学习语义。

Askora 的体验必须支持以下闭环：

```text
Orientation
→ Engage with material / task
→ Think / Retrieve
→ Attempt
→ Feedback / Diagnosis
→ Remediation or Scaffold when needed
→ Retry / Independent Validation
→ Learning Evidence
→ Continue / Review / Replan
```

### LEXP-010 — Orientation

进入学习时，用户至少应知道：

- 当前在哪个空间中学习（canonical Workspace）；
- 当前要完成什么（当前对话 / task）；
- 为什么现在做这一步（存在可靠 reason 时）；
- 完成任务所需的关键上下文或来源。

不要求用户理解完整 LearningPlan、LearnerState 或内部 policy。主路径不要求用户看见或管理 Learning Goal；Goal 由系统按 `PD-RULE-004` 维护。

### LEXP-011 — Active Processing

Askora 不应把“看完解释”视为学习完成。只要上游 Teaching Policy / Activity contract 要求主动 retrieval、生成、比较、推理或应用，Experience 必须为用户留出真实思考与作答空间。

UI 不得为了减少步骤而自动替用户完成需要形成 Learning Evidence 的 Attempt。

### LEXP-012 — Attempt Before Evidence

Learning Evidence 必须基于真实 learner behavior。AI 生成的答案、用户只读内容、点击“懂了”或单纯 conversation completion 不能在体验上被包装为独立掌握证据。

### LEXP-013 — Feedback Is Instructional

Feedback 的目的不是只告诉用户“对/错”，而是帮助用户理解：

- 哪部分表现成立；
- 哪部分需要修正；
- 为什么；
- 下一步应该重新思考、补充概念、查看提示还是重新尝试。

精确诊断与补救选择由 Teaching / Assessment contract 决定；UI 只负责诚实呈现。

### LEXP-014 — Remediation Returns to Learning

错误或知识缺口不应把用户送入与原任务无关的内容中心。补救应尽可能保持当前 Activity / Material / Workspace 上下文，并在适当时回到新的 Attempt。

### LEXP-015 — Independent Validation Matters

受助成功、部分答案暴露、完整答案暴露与独立成功在体验中必须可区分。

当 canonical contract 要求 fresh independent validation 时，界面必须诚实说明“仍需独立验证”，不得把受助后的即时正确表现包装为已掌握。

---

## 4. Learning Conversation Model

### LEXP-CONV-001 — Conversation Is an Interaction Mode

Conversation / Tutor 是 `LearningActivity` 的 interaction mode，而不是 Askora 的产品结构。

用户可以通过自然语言：

- 请求解释；
- 提问；
- 作答；
- 请求提示；
- 要求举例；
- 要求直接答案；
- 要求测试或挑战；
- 要求总结当前理解。

这些请求进入既有 Teaching / Request / Constraint contracts；UI 不得暗示一枚按钮可以绕过 Teaching Policy、Evidence 或 Assessment 规则直接修改 canonical state。

### LEXP-CONV-002 — Do Not Flatten Learning into Bubbles

消息呈现必须优先表达学习角色与内容层级，而不是统一套用聊天气泡。

长解释、问题、反馈、引用、结构化学习内容可以采用开放内容布局；用户短回答可以更紧凑。无论视觉形式如何，都必须保留：

- message / event 顺序；
- learner vs assistant origin；
- 当前 Activity 上下文；
- structured content fallback；
- citation / provenance；
- assistance / validation semantics（适用时）。

exact component anatomy 由 Learning Interaction Spec 定义。

### LEXP-CONV-003 — Semantic Learning Roles

Learning Conversation 至少需要能够让用户区分以下体验角色，而不要求这些角色成为新的 backend schema：

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

一个视觉单元可以组合多个角色，但不得把关键 Feedback、Question 或 learner Attempt 淹没在连续 prose 中。

### LEXP-CONV-004 — Streaming Must Preserve Meaning

Streaming 是 delivery state，不是学习语义。

半完成的 structured response 不应被当作最终 Question / Feedback / Assessment。断线或重连也不得制造重复 assistant message、Attempt 或 Evidence。

---

## 5. Assistance and Learner Autonomy

### LEXP-AST-001 — User May Ask for More Help

用户可以明确要求更多帮助甚至直接答案。Askora 不应通过 UI 强迫“只能苏格拉底式教学”。

但用户选择更多帮助不会改变 evidence semantics：

> 用户有权看答案；系统没有权把答案暴露后的成功伪装成独立成功。

### LEXP-AST-002 — Assistance Must Be Understandable

当 canonical data 可用时，Experience 应以用户可理解方式说明当前帮助状态，例如：

```text
独立作答
已使用帮助
已看到关键步骤
已暴露答案
待独立验证
```

UI 不得通过消息长度、按钮点击次数、card type 或前端猜测生成 assistance truth。

### LEXP-AST-003 — Help Controls Are Requests

“给一点提示”“解释概念”“给例子”“直接告诉我”等控件表达用户 request，而不是直接修改 TeachingAction / policy envelope。

不可用帮助必须来自真实 hard rule，并提供可理解原因；不得用 CSS 隐藏后仍可触发。

---

## 6. Feedback and Remediation Experience

### LEXP-FB-001 — Separate Learner Error from System Error

模型失败、工具失败、检索失败、来源不可用、网络问题不能显示为“你答错了”。

学习反馈与系统错误必须在语言、视觉和恢复动作上明确区分。

### LEXP-FB-002 — Correction Should Preserve Agency

当用户回答存在问题时，优先帮助其再次思考，而不是立即覆盖原回答或自动替用户重写。

AI 可以解释、拆解或给提示，但用户原 Attempt 必须保持可追溯。

### LEXP-FB-003 — Retry Is a New Attempt

重新尝试应作为新的 learner behavior，而不是静默替换历史回答。是否形成新 Evidence、Evidence 权重如何变化由 Assessment / Evidence contract 决定。

### LEXP-FB-004 — Remediation Must Be Bounded

补救内容应服务当前学习缺口。界面不得因为一次错误自动扩张成新的知识库浏览、无限聊天分支或长期独立页面，除非存在新的明确 user job。

---

## 7. Material, Citation and Provenance Experience

### LEXP-SRC-001 — Source-grounded Claims Must Be Traceable

任何声称“来自用户资料”的内容都必须能追溯到真实来源。Experience 必须区分：

```text
Source-grounded content
vs
External model knowledge / explanation
```

### LEXP-SRC-002 — Citation Is Part of Learning Context

引用不只是脚注。用户需要能够：

- 看见可读来源 label / locator；
- 判断回答依据；
- 查看对应原文；
- 返回当前学习而不丢失上下文。

内部 UUID/version 可以用于审计，但不能作为主要用户文案。

### LEXP-SRC-003 — View Source Without Leaving Learning

在 Learning Workspace 中点击 citation / “查看原文”时，优先在当前资料上下文中打开来源，不应迫使中央 Learning Canvas 导航离开当前 Activity。

### LEXP-SRC-004 — No Fabricated Original

缺少真实 SourceSpan / locator 时必须显示不可用或来源不足。不得用 AI Summary、文件名或模型记忆伪装成“原文”。

### LEXP-SRC-005 — From Reading to Active Learning

Material Experience 不以阅读完成为终点。只要当前学习目标需要，界面应提供进入问题、retrieval、比较、解释或练习的自然路径，使“读材料”能够进入主动学习闭环。

### LEXP-SRC-006 — Parse Mode Must Stay Honest

本地解析与「本机 + AI 增强」必须可区分。仅本机解析可以支持打开原文、结构对照和加入空间；不得把它呈现为模型已完成全书理解。需要模型生成讲解 / 出题 / 反馈时，缺模型必须说缺模型，不得用 mock 对话充学习。AI 增强解析失败不得抹掉已成功的本地原文与结构。

---

## 8. Notes Experience

### LEXP-NOTE-001 — Notes Are User-authored Learning Data

Learning Notes 是用户主动沉淀的 durable learning data，不是自动生成的 AI Summary，也不是 canonical knowledge truth。

### LEXP-NOTE-002 — Notes Must Preserve User Text

AI 可以在用户明确请求时帮助整理、改写或总结笔记，但不得无确认覆盖用户原文。

### LEXP-NOTE-003 — Notes Stay in Context

笔记应保持 Workspace scope，并在适用时关联当前 Activity / Material anchor，使用户能够“边学边写”，而不是切换到独立知识管理产品。

### LEXP-NOTE-004 — Save State Must Be Honest

Experience 必须区分 saving / saved / failed / conflict / recoverable。浏览器本地未持久化状态不得显示“已保存”。

exact autosave/version/conflict mechanics 由 technical/UI Spec 定义。

---

## 9. Learning Context and Next-step Orientation

### LEXP-NEXT-001 — Orientation, Not Plan Management

用户需要知道当前阶段和大致下一步，但不需要长期管理完整 LearningPlan。

Learning Context Drawer 只承担：

- 当前阶段；
- 阶段目标；
- 接下来 1–3 个动态学习方向。

### LEXP-NEXT-002 — “Next” Must Stay Honest

“接下来”是当前 canonical context 下的动态教学方向，不等于永不变化的空间目录。

当前数据缺失、partial 或 stale 时必须诚实显示；前端不得根据 chat 文本、heading 顺序或 probability threshold 推断 next knowledge point。

### LEXP-NEXT-003 — End with a Meaningful Next Action

一段学习结束时，用户应理解接下来处于哪种状态：

- 继续当前 Activity；
- 进入新的 Activity；
- 暂停并可恢复；
- 等待延迟复习；
- 需要独立验证；
- 当前没有可靠下一步。

不得为了保持 engagement 自动生成无依据的“继续学习”内容。

### LEXP-NEXT-004 — Conversation Switching Stays Space-scoped

已有对话列表在学习中只显示当前空间内 exact Activity refs。打开已 active/resumable 对话不得创建第二 Activity/Session；对空间「继续学习」或启动 planned/available 对话必须调用 SYS06 owner Action。跨空间 Activity ref 必须 fail closed。

---

## 10. Long-term Continuity

### LEXP-CONT-001 — Preserve Current Learning Identity

切换 presentation mode、空间 / 对话 navigation、隐藏右栏、打开原文、展开 Context Drawer 不得创建第二份 LearningActivity、Attempt、TeachingAction 或 transcript truth。对空间「继续学习」除外，该 Action 必须创建新的 LearningActivity。

### LEXP-CONT-002 — History Is Context, Not Management Burden

LearningHistory 应在用户需要恢复、回顾或审计时可达，但不要求用户通过历史管理中心才能继续学习。

### LEXP-CONT-003 — Welcome First; Resume Only on Explicit Selection

App 启动必须先到 Welcome，不得自动进入上一段对话，也不得自动创建新的对话 / Session。用户点侧栏已有对话时，恢复同一段对话。用户对某空间点「继续学习」时，才允许按 `EXP-JOURNEY-002` 新开一段对话；不得用 frontend 私自新建 quick chat 覆盖旧上下文。

### LEXP-CONT-004 — No Silent Loss

离开、切换 Workspace、刷新或恢复过程中，未完成 Attempt、stream、note 或 source position 不得静默丢失。具体持久化义务服从下游合同。

---

## 11. Cognitive Load and Visual Priority

Experience 应把认知资源留给学习内容本身。

优先级：

```text
Current task / question
→ Learner thinking and answer
→ Feedback / correction
→ Necessary source / assistance / validation
→ Lightweight next-step orientation
→ Optional detail / audit
```

默认避免：

- 多个等权 Dashboard；
- 常驻掌握度图表抢占学习画布；
- 大量彩色 Card；
- 游戏化 streak / points 作为学习效果证明；
- 工程术语进入主要学习文案；
- 每个 domain object 都形成独立管理页面。

---

## 12. Experience Success Criteria

Learning Experience 是否成立，不能只用“页面可用”判断。

体验层至少应验证：

- 用户能识别当前学习任务与上下文；
- 用户能够实际作答而不是被动消费；
- Feedback 与系统错误不会混淆；
- assistance / answer exposure / validation obligation 可理解；
- citation 可以回到真实来源且不破坏当前学习；
- 用户可从阅读自然进入主动练习；
- interrupted learning 可以恢复；
- UI 不要求用户管理内部学习系统对象才能继续学习；
- UI 不通过 engagement 或视觉指标伪装真实 learning outcome。

真实学习效果仍必须由 Learning Evidence / Product Evidence gate 验证，UX 验收不能替代它。

---

## 13. Remaining Design / Spec Gaps

本 Baseline 不重新发明已冻结 Teaching / System 设计。仍需下游明确的主要 Gap 是：

### Spec Gap

- Learning message / learning unit 的 exact visual anatomy；
- Question、Attempt、Feedback、Hint、Source block 的具体组合规则；
- long conversation 中 section/grouping 与 history virtualization；
- source-to-note 快捷交互的 exact contract；
- streaming structured payload 的 exact UI state machine；
- keyboard / screen-reader 读取 Learning Conversation 的 exact order。

这些属于 `Learning Interaction Contracts`，不应写回 Teaching Canonical。

### Implementation Gap

Design System、responsive/a11y、Library v1 exposure、Settings/legacy cleanup 与全量 regression 的剩余工作以当前 Linear UI Redesign Project 为准，不应被解释为新的 Learning Experience 设计问题。

---

## 14. Explicit Non-goals

本文件不定义：

- TeachingStrategy / TeachingAction ontology；
- AssessmentResult / LearningEvidence schema；
- mastery threshold / LearnerState algorithm；
- review scheduling algorithm；
- LLM prompt；
- RAG / retrieval architecture；
- database message model；
- API；
- component CSS；
- route；
- 当前 Linear implementation status。
