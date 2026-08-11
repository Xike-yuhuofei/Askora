# Askora User Problem & JTBD Research

> 状态：Product Discovery Research Baseline  
> 日期：2026-08-11  
> 权威性：Supporting Evidence，不是 Canonical Product Decision  
> 目的：把当前 Askora 已经实现/设计的学习闭环与“真实用户为什么需要它”严格分开，明确已知、推论和待验证内容

---

## 1. Research Question

本研究回答：

> **Askora 当前定义的长期学习闭环，究竟对应什么真实用户问题和 Job？哪些只是从系统设计反推出来的假设？**

重要前提：

- 当前仓库对 Learning Science、Teaching Policy、Assessment、Learner State 有大量正式设计与研究；
- 但没有同等成熟的多用户访谈、行为观察或定量 Product Discovery evidence；
- 因此“系统设计很完整”不能被当作“用户问题已经验证”。

---

## 2. Repository-supported Problem Signals

以下问题并不是凭空提出，而是当前 Canonical Design / Research 已持续围绕它们建立约束。

### 2.1 Assisted Performance ≠ Learning

当前设计明确区分：

```text
independent
assisted
answer-exposed
immediate
delayed
transfer
```

并拒绝把 assisted success / answer-exposed success 直接当成 stable mastery。

**Repository-supported conclusion：**

> 当前表现容易制造“已经学会”的假象，因此 Askora 必须在帮助撤除以后重新建立学习证据。

### 2.2 Conversation ≠ Learning Evidence

当前产品与 Learning Core 已明确：

```text
Conversation != LearningEvidence
```

用户说“懂了”、对话很顺畅、活动完成，都不能自动成为掌握事实。

**Repository-supported conclusion：**

> 如果产品只维护聊天历史，它无法可靠承担 Learner State truth。

### 2.3 Immediate Success ≠ Retention

当前 Learning Outcome 明确要求延迟保持，并在 DR-03-04 中把 delayed independent performance 提升为主要 outcome family。

**Repository-supported conclusion：**

> 学习成功必须跨时间重新验证，而不是只测当前 turn。

### 2.4 Familiar Success ≠ Transfer

当前设计明确区分 near / far transfer，并拒绝把同一道或高度熟悉任务上的成功自动解释为迁移。

**Repository-supported conclusion：**

> 如果用户的目标是能力而不是记答案，系统必须验证任务变化后的应用能力。

### 2.5 More Help Can Become Too Much Help

Teaching Policy Research 长期处理 Assistance Dilemma：

- novice 可能需要 explicit modelling；
- 有一定能力后需要 fading；
- full answer 可以被允许，但必须改变 evidence semantics；
- repeated failure 不能永远坚持无提示 Socratic probing。

**Repository-supported conclusion：**

> “AI 多帮一点”不是单调更优，下一步教学动作需要依赖当前状态和历史帮助。

---

## 3. From Signals to Problem Statement

### 3.1 Surface Needs

用户表面上可能说：

- “帮我解释这本书”；
- “考考我”；
- “给我做学习计划”；
- “提醒我复习”；
- “我哪里还不会？”；
- “下一步学什么？”；
- “给我一个提示”；
- “直接告诉我答案”。

这些都是 interaction-level requests。

### 3.2 Underlying Task

系统需要帮助用户完成的不是“发出更多学习请求”，而是：

```text
明确目标
→ 学习
→ 获得帮助
→ 尝试
→ 判断是否真的会
→ 经过时间重新验证
→ 迁移
→ 决定下一步
```

### 3.3 Candidate Root Problem

当前最有支撑的候选根本问题：

> **长期自主学习缺少一个持续维护目标、证据、状态与下一步教学义务的控制闭环；普通一次性 AI 交互容易把理解感、受助成功或即时正确率误认为真正掌握。**

这是 `repository-supported inference`，不是已完成用户研究的结论。

### 3.4 Candidate Product Job

> **把“接触过 / 看懂了 / 在帮助下做过”转化为“可以无提示独立完成、经过延迟仍保持、面对变化仍能迁移”的能力，并持续决定下一步最有价值的学习行动。**

该 Job 已被 Product Strategy 采纳，但用户价值强度仍需验证。

---

## 4. Target User Hypothesis

### 4.1 Candidate Primary User

当前候选：

> **持续数周至数月自主学习高认知负荷主题、拥有自己的学习材料、重视真正掌握而非快速获得答案，并愿意接受本地工具与 BYOK 的个人学习者。**

### 4.2 Why This User

这个用户更可能同时具有：

- 长期目标；
- material continuity；
- prerequisite dependency；
- repeated practice；
- retention requirement；
- transfer requirement；
- 足够高的 learning-value / setup-cost ratio。

### 4.3 Non-target Hypothesis

需求可能较弱的群体：

- 一次性事实查询；
- 只想拿答案；
- 主要需求是写作/编码 productivity；
- 主要需求是知识存档与检索；
- 需要机构管理/团队协作；
- 强依赖多设备、云端零配置体验。

这些边界目前更多来自产品战略聚焦，而不是用户分群研究。

---

## 5. JTBD Hypothesis

### 5.1 Primary Functional Job

> **当我需要真正掌握一项复杂知识或能力，而不是只是获得答案时，我希望有一个系统持续理解我的目标和真实能力状态，决定下一步最合适的学习行动，并在帮助撤除、时间延迟和任务变化以后验证我是否真的学会。**

### 5.2 Supporting Functional Jobs

- 把自己的材料变成可学习、可引用的知识供给；
- 发现先备缺口和持续错误；
- 在卡住时得到足够但不过量的帮助；
- 知道“当前会做”是否只是因为刚刚看过答案；
- 把遗忘风险转化为下一次复习；
- 在多个 session 之间恢复真实学习状态；
- 能解释为什么系统建议下一步这样学。

### 5.3 Emotional / Trust Jobs — ASSUMPTION

可能存在但尚未验证：

- 希望摆脱“我好像懂了”的虚假安全感；
- 希望知道 AI 帮助没有让自己形成依赖；
- 希望长期学习数据可控，不被某个 SaaS 账号锁定；
- 希望系统给出的掌握判断有理由，而不是一个黑盒百分比。

这些必须通过访谈或真实使用观察验证。

---

## 6. Core User Tensions

Askora 的价值可能来自处理以下冲突，而不是单纯增加功能。

### 6.1 Convenience vs Learning

用户可能希望快速拿答案，但长期学习又需要生成、检索和独立尝试。

产品不能简单选择：

```text
always refuse answer
```

也不能选择：

```text
always optimize convenience
```

Askora 当前策略是尊重用户选择，同时改变 evidence semantics。

### 6.2 Guidance vs Independence

太少帮助会造成无效挣扎，太多帮助会掩盖能力。

Askora 的核心 Job 之一可能是动态管理该张力。

### 6.3 Structure vs Friction

Learning Goal、diagnosis、assessment、delayed review 都能提高系统结构性，但也会增加使用成本。

真正问题不是“结构越多越专业”，而是：

> **多少结构能产生用户可感知的额外学习价值？**

### 6.4 Local Control vs Setup Cost

Local-first / BYOK 提供控制权，但可能增加配置和模型成本理解负担。

这是必须真实验证的产品 trade-off。

---

## 7. Assumption Map

| Hypothesis | Evidence today | Confidence | Validation need |
|---|---|---|---|
| 用户会遭遇“受助表现被误认为掌握” | Learning research / system design 强支撑 | Medium for Askora users | 观察真实 AI 学习行为 |
| 用户重视延迟保持与迁移 | Learning goal 强支撑，用户证据不足 | Medium-Low | 访谈 + longitudinal use |
| 用户愿意接受 no-hint checks | 未验证 | Low | prototype / live use |
| 用户愿意接受 delayed review | 一般学习机制有依据，产品接受度未验证 | Low-Medium | return / completion behavior |
| Learner State 比普通 chat memory 更有价值 | 产品推论 | Low | compare user task outcomes |
| “下一步应该学什么”是强痛点 | 当前设计假设 | Low | JTBD interview |
| Local-first / BYOK 是目标用户优势 | 产品选择 | Low | willingness / friction study |
| 用户自带材料是主要学习入口 | 当前产品方向 | Medium-Low | usage diary / import behavior |
| 单用户长期学习比机构场景更适合早期 Askora | scope decision | Medium | user fit research |

---

## 8. What Is Missing

当前最缺的不是新的 Product Spec，而是以下原始 Discovery Evidence：

### 8.1 User Interview Evidence

需要收集：

- 最近一次持续两周以上的自主学习任务；
- 实际使用的工具组合；
- 什么时候 AI 帮助反而让用户不确定自己是否真的会；
- 如何判断“学会”；
- 如何复习；
- 如何决定下一步；
- 哪些流程最容易中断。

### 8.2 Behavioral Observation

比“你想不想要 Learner State？”更有价值的是观察：

- 用户是否主动回到旧内容；
- 是否愿意做 fresh no-hint item；
- full answer 后是否愿意重新验证；
- delayed review 是否被持续完成；
- 哪类系统建议会被采纳/忽略；
- 用户是否理解 assistance / mastery distinction。

### 8.3 Value / Friction Evidence

必须测：

```text
additional learning value
vs
additional structure / setup / assessment friction
```

否则 Askora 很可能成为“理论上正确但用户不持续使用”的学习系统。

---

## 9. Recommended Discovery Protocol

### D1 — Retrospective JTBD Interview

优先研究用户最近真实完成或失败的长期学习任务，不讨论 Askora 功能列表。

核心问题：

1. 你最近一次真正想“学会”而不是“查一下”的东西是什么？
2. 你怎么知道自己学会了？
3. 你在哪里卡住？
4. 你用了哪些 AI / notes / course / flashcard 工具？
5. 哪一步最需要自己维护状态或做判断？
6. AI 最容易让你产生什么错误感觉？
7. 一周后你通常还能记住多少？你怎么知道？
8. 你什么时候会重新练习或复习？

### D2 — Workflow Reconstruction

把真实任务还原为：

```text
trigger
→ material
→ goal
→ actions
→ assistance
→ evidence
→ interruption
→ return
→ success/failure judgment
```

寻找用户自己承担、但现有工具没有持续承担的 coordination work。

### D3 — Prototype Validation

不是问“你喜欢这个功能吗”，而是测试：

- 是否愿意创建/确认目标；
- 是否愿意完成 fresh no-hint check；
- 是否理解“受助成功不算独立掌握”；
- 是否愿意回来做 delayed validation；
- 下一步建议是否减少认知负担；
- Local/BYOK setup 是否阻断首次价值。

### D4 — N-of-1 Learning Evidence

对于当前单用户阶段，继续使用现有 DR-03-04 的原则：

- immediate assisted performance 与 learning 分离；
- primary outcome 在帮助撤除后测；
- delayed independent performance 优先；
- transfer 独立记录；
- Engineering / Policy Correctness / Learning Effect 分开。

---

## 10. Exit Criteria for Stronger Strategy Confidence

以下条件满足前，不建议把 Primary User / JTBD 从 `ASSUMPTION` 升级为“validated”：

- 至少出现多个真实长期学习任务中重复的问题模式；
- 用户在没有被产品术语引导的情况下自然描述相似 Job；
- 用户实际愿意为 independent / delayed validation 付出一定成本；
- Askora 的状态/下一步价值能够明显替代用户原有的手工 coordination work；
- Local-first / BYOK friction 不阻断核心学习价值；
- 至少一部分学习领域能产生可信 Assessment / Learning Evidence。

如果这些条件不成立，应允许 Product Strategy 被推翻或收窄，而不是通过增加功能维持原命题。
