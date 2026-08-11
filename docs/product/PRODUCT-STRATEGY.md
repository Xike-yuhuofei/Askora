# Askora PRODUCT-STRATEGY

> 文档状态：Canonical Product Strategy Baseline  
> 冻结日期：2026-08-11  
> 适用范围：Askora 产品战略与后续 Product Positioning / Canonical Design / ADR / Spec  
> 文档职责：回答 Why / Who / Problem / Value / Success  
> 不包含：功能规格、页面 UX、领域 schema、架构 mechanics、实现细节

---

## 1. 文档目的与证据语义

Askora 的 Product Strategy 必须先回答：

> **为什么 Askora 值得存在、它为谁解决什么问题、真正创造什么价值、怎样才算成功？**

本文件不是为了把所有产品想法写成“已确认事实”。当前 Askora 仍是单用户、自用优先阶段，缺少广泛外部用户研究。因此本文件明确区分：

- **FROZEN DECISION**：已经由当前正式产品/设计基线冻结，后续工作必须服从；
- **REPOSITORY-SUPPORTED CONCLUSION**：当前 Research / Design / Release Evidence 已有充分内部支撑；
- **ASSUMPTION**：当前战略选择，但仍需真实用户/产品证据验证；
- **RESEARCH GAP**：尚不能可靠判断，不得由实现自行补答案。

研究证据解释“为什么这样判断”；Product Strategy 保存当前被采纳的上位结论。Research 不能作为第二套产品规范。

---

## 2. Strategic Thesis

### 2.1 核心战略命题 — FROZEN DECISION

> **Askora 不应成为“更适合学习的 AI Chat”，而应成为一个以长期独立能力为最终结果、以 Learning Evidence 为事实基础、持续维护 Learner State，并据此控制教学、评估、复习和重规划的个人 AI 学习系统。**

Askora 的核心价值不是让 AI 在当前一轮“回答得更好”，而是持续回答：

1. 用户真正想掌握什么？
2. 用户当前真正会什么，证据是什么，不确定性是什么？
3. 当前最合适的教学动作是什么？
4. 帮助撤除以后，用户是否仍能独立完成？
5. 能力经过延迟以后是否仍保留？
6. 是否能够迁移到新的任务与情境？
7. 下一步应该学习、补救、复习还是验证什么？

因此 Askora 的战略重心是：

```text
answer generation
<
learning-state understanding
<
teaching decision quality
<
independent capability
<
retention and transfer
```

---

## 3. Opportunity / Why Now

### 3.1 Opportunity Hypothesis — ASSUMPTION

通用 AI 已经显著降低了“获得解释、摘要、答案和例子”的成本，但**获得信息不等于形成长期能力**。

Askora 的机会不在于继续降低答案获取成本，而在于解决一类更难的问题：

> **如何把大量离散、即时、受助的 AI 交互，转化为一个跨时间连续、可验证、可调整的个人学习闭环。**

### 3.2 Why Now — ASSUMPTION

当前产品方向基于三个假设：

1. AI 已经足够擅长生成解释、问题、反馈与练习，使“教学表达”不再是唯一瓶颈；
2. 真正未被解决的高价值问题逐渐转向状态、证据、教学控制、长期保持和迁移；
3. 本地数据、BYOK 与个人长期状态可以构成一种不同于中心化 AI SaaS 的可信个人学习环境。

这些是战略机会判断，不等同于已经验证的市场需求。

### 3.3 Current Research Gap

当前仓库没有独立完成的市场规模、系统竞争研究或多用户 Discovery Research，因此不得声称：

- Askora 已经证明存在广泛市场需求；
- 当前差异化已经被真实用户验证；
- 当前 Local-first / BYOK 取舍对大多数用户都是优势。

这些应进入后续 Product Discovery，而不是由实现反向证明。

---

## 4. Problem Space

### 4.1 表层需求

长期学习者可能表现为：

- 阅读资料并提问；
- 需要解释陌生概念；
- 练习、测验和复习；
- 记录笔记；
- 跟踪学习进度；
- 请求 AI 帮助完成困难任务。

这些只是表层交互需求，不是 Askora 的根本 Problem Definition。

### 4.2 核心 Problem Statement — FROZEN DECISION

> **长期自主学习的核心困难不是缺少解释和答案，而是学习过程缺乏一个跨时间持续运行、以行为证据为基础的闭环，能够可靠判断“我真正掌握了什么、下一步应该发生什么、帮助撤除后是否仍能独立完成、经过延迟是否仍能保持、能否迁移到新情境”。**

### 4.3 根本问题

当前一次性 AI 交互天然容易出现：

```text
看懂了
≠
会做

有提示时做对
≠
无提示独立成功

刚学完会做
≠
延迟后仍然会

同构任务成功
≠
能够迁移
```

Askora 因此不把“回答完成”“对话结束”“课程浏览完成”视为学习成功的充分证据。

### 4.4 Product Job — FROZEN DECISION

> **把用户对知识的“接触过、看懂了、在 AI 帮助下做过”，转化为可验证、可保持、可迁移的独立能力，并持续决定下一步最有价值的学习行动。**

---

## 5. Target User

### 5.1 Primary User — STRATEGIC TARGET / ASSUMPTION

Askora 当前优先服务：

> **持续数周至数月自主学习高认知负荷主题、拥有自己的学习材料、重视真正掌握而非快速获得答案，并愿意接受本地工具与 BYOK 模型的个人学习者。**

典型特征：

- 自主决定学习目标，而不是由学校 LMS 强制安排；
- 学习内容存在概念依赖、技能增长或长期记忆要求；
- 愿意进行练习、无提示验证、延迟复习和迁移任务；
- 需要 AI，但不希望 AI 的流畅回答被误认为掌握；
- 重视个人学习数据长期可控。

该 Primary User 是当前战略聚焦，不是已经通过大样本用户研究验证的人群定义。

### 5.2 Primary Context — ASSUMPTION

Askora 最适合：

- 一本书、课程资料、论文集合或个人材料驱动的长期学习；
- 需要形成可迁移理解或技能，而不是只找某个事实；
- 学习目标能够被拆成若干可观察能力；
- 可以在不同时间点重新验证学习结果。

### 5.3 Non-target Users — FROZEN BOUNDARY

Askora v1 不以以下用户为首要目标：

- 只需要一次性事实查询或即时答案的人；
- 只需要 AI 写作、编码或通用 Agent 的人；
- 主要需求是笔记、文件整理或个人知识库的人；
- 团队、学校、企业的多人协作与管理场景；
- 需要 SaaS、多设备实时同步或零配置云服务作为首要前提的人。

---

## 6. Jobs To Be Done

### 6.1 Primary JTBD — STRATEGIC HYPOTHESIS

> **当我需要真正掌握一项复杂知识或能力，而不是只是获得答案时，我希望有一个系统持续理解我的学习目标和真实能力状态，决定下一步最合适的学习行动，并在帮助撤除、时间延迟和任务变化以后验证我是否真的学会。**

### 6.2 Supporting Jobs

用户还需要：

- 把自己的材料转化为可学习、可引用的知识供给；
- 在不知道自己缺什么时获得诊断；
- 在卡住时得到足够而不过量的帮助；
- 在“我懂了”与“我真的会了”之间获得可靠区分；
- 知道今天最值得继续什么；
- 在长期积累后仍能理解自己的学习历史和状态变化。

### 6.3 Research Requirement

Primary JTBD 仍需要真实用户行为与任务研究验证。在验证前，不应进一步把用户群扩张为“所有学习者”。

---

## 7. Product Vision

### 7.1 Vision — FROZEN DECISION

> **让个人拥有一个能够跨时间理解其学习目标、学习证据和能力变化，并持续做出可解释教学决策的 AI 学习系统。**

长期方向不是建立最大的内容库、最长的聊天记录或最复杂的 AI Agent，而是让系统越来越可靠地回答：

> **“这个人接下来做什么，最有可能形成真正、持久、可迁移的能力？”**

### 7.2 Vision Boundary

“个人学习操作系统”可以作为设计隐喻，但不得据此无限扩大产品 Scope。任何新 capability 仍必须证明它直接服务长期学习闭环。

---

## 8. Value Proposition

### 8.1 Core Value Proposition — FROZEN DECISION

> **Askora 把 AI 从“即时回答者”转变为一个受约束、以证据驱动的长期学习控制系统，使用户不仅能得到帮助，还能知道自己是否真正学会，以及下一步最值得做什么。**

### 8.2 用户价值

Askora 试图提供四类结果，而不是功能堆叠：

1. **更可信的掌握判断**：不把自评、阅读完成或受助成功直接当作掌握；
2. **更合适的下一步**：根据目标、证据和状态决定解释、练习、补救、复习或迁移验证；
3. **更少的 AI 依赖假象**：显式区分 assisted / answer-exposed / independent；
4. **更长期的学习连续性**：跨 session 保存材料、目标、证据、状态和复习义务。

### 8.3 Value Boundary

Askora 不承诺：

- AI 永远比教师更会教；
- 所有领域都能被可靠自动评估；
- 使用 Askora 本身就代表学习有效；
- 当前 deterministic Teaching Policy 已经证明普遍优于其他教学方式。

这些只能由真实 Learning Evidence 支持。

---

## 9. Strategic Differentiation

### 9.1 Differentiation Thesis — FROZEN DECISION

Askora 的差异化不建立在任何单一功能上，例如：

- AI Chat；
- RAG；
- 苏格拉底提问；
- Quiz；
- Flashcard；
- Spaced Repetition；
- Notes；
- Knowledge Graph。

这些都可以作为系统能力，但不能单独定义产品。

真正的差异化必须来自闭环：

```text
Persistent Learning Goal
+
Evidence-backed Learner State
+
Explicit Teaching Policy
+
Assistance / Exposure Tracking
+
Independent Validation
+
Delayed Validation
+
Transfer Validation
+
Review / Replan
```

### 9.2 Alternative Categories

Askora 与其他产品范式的边界是：

- **通用 AI Chat**：主要优化当前请求的高质量响应；
- **知识库 / 笔记工具**：主要优化知识保存、组织、检索与创作；
- **闪卡 / 记忆工具**：主要优化记忆条目与复习调度；
- **LMS / Courseware**：主要优化课程、内容、班级或学习流程交付；
- **Askora**：主要优化个人长期学习闭环中的状态判断与下一教学决策。

这是一种产品范式定义，不是完整竞争研究。具体产品比较必须由独立 Research 支持。

---

## 10. Product Principles

以下原则只有在能够排除错误方案时才保留。

### P1 — Learning Outcome > Engagement

如果一个方案增加对话时长、消息数量或满意度，却降低独立能力、保持或迁移，则它不是更好的 Askora。

### P2 — Evidence > Impression

“看懂了”“感觉会了”“AI 认为会了”不能覆盖结构化学习证据。

### P3 — Assistance Must Eventually Withdraw

帮助的目标不是让当前任务永远成功，而是支持后续无提示独立成功。允许直接答案，但必须保留 exposure 语义并重新建立独立验证机会。

### P4 — Next Action Comes From Learning State, Not Chat Continuation

对话只是交互形式。下一步教学动作必须由目标、状态、评估、历史帮助与约束共同决定，而不是因为“聊天还在继续”。

### P5 — User Autonomy Must Not Corrupt Evidence

用户可以请求解释、答案、跳过或调整学习方式；系统必须尊重选择，但不能追溯性把受助表现改写成独立掌握。

### P6 — Provenance and Uncertainty Must Remain Visible

来源事实、AI 外部知识、AI 提取结果、用户笔记与 Learning Evidence 必须保持语义边界；不确定不能伪装成确定。

### P7 — Local Personal Simplicity > Premature Platform Complexity

Askora 服务个人长期学习，不为尚不存在的多租户、云同步、企业规模或开放插件生态提前支付系统复杂度。

### P8 — Explainable, Testable Control > Opaque Autonomy

高影响学习决策优先采用可解释、可回放、可测试的规则和受约束 AI，而不是把核心学习状态或教学控制直接交给自由 LLM/Agent。

---

## 11. Strategic Constraints

具体产品边界由 [`PRODUCT-POSITIONING.md`](PRODUCT-POSITIONING.md) 冻结。Strategy 层只冻结以下上位意图：

- Personal-use first；
- single-user v1；
- Local-first / locally operated，而不是 Offline-only；
- user-owned core learning data；
- BYOK AI；
- user-provided materials as the primary knowledge boundary；
- no mandatory Askora central cloud for core use；
- LLM is not canonical business-state authority；
- learning claims require Learning Evidence；
- system complexity must remain proportional to personal-use value。

技术选型、数据 schema、任务状态、adapter 和运行 mechanics 不属于本文件。

---

## 12. Assumptions

当前最重要的战略假设必须被显式管理：

| Assumption | 当前状态 | 如果错误的影响 |
|---|---|---|
| 目标用户重视“真正学会”而不只是即时便利 | ASSUMPTION | 核心价值主张失效 |
| 用户愿意接受无提示验证、延迟复习与迁移任务 | ASSUMPTION | Learning Loop 难以持续 |
| Learner State 能提供明显高于普通 Chat Memory 的价值 | ASSUMPTION | 产品差异化削弱 |
| 用户自带材料足以成为主要知识边界 | ASSUMPTION | 需要扩大 content discovery strategy |
| Local-first + BYOK 的控制权收益足以抵消配置摩擦 | ASSUMPTION | v1 product shape 需要重评 |
| 跨领域 Assessment 能产生足够可靠的 Learning Evidence | ASSUMPTION | 掌握判断与 Teaching Policy 受限 |
| 受约束 Teaching Policy 的收益值得增加的系统复杂度 | ASSUMPTION | 应简化为更轻的 learning workflow |
| 单用户 N-of-1 evidence 足以指导早期迭代 | REPOSITORY-SUPPORTED CONCLUSION | 早期策略改进需要其他验证方法 |

Assumption 不得因为对应功能已经实现就自动升级为 Validated。

---

## 13. Strategic Risks

### R1 — False Mastery

系统给出“已掌握”判断，但后续独立/延迟任务快速失败。

这是最严重的产品风险之一，因为它直接破坏 Askora 的核心价值。

### R2 — Assistance Dependency

AI 使当前表现更好，但帮助撤除以后能力没有增长甚至下降。

### R3 — Assessment Invalidity

开放领域任务无法被稳定、可靠地评估，导致 Learner State 与 Teaching Policy 输入失真。

### R4 — Over-engineering

系统为了“智能、自适应、可扩展”建立远超个人学习价值的架构复杂度。

### R5 — Friction > Learning Value

本地运行、BYOK、目标设置、诊断或验证流程的摩擦超过用户感知到的学习收益。

### R6 — Product Identity Drift

Askora 逐渐退化为 Chat + RAG + Notes + Flashcards 的功能集合，而不再维护明确的学习闭环。

### R7 — Evidence / Source Trust Failure

AI 将模型知识伪装成资料事实、引用错误来源，或把技术失败误判为学习失败。

### R8 — Strategy Without Validation

工程门禁和 Policy Correctness 长期为 PASS，但真人学习效果一直缺乏证据，却被错误解释为产品成功。

---

## 14. Success Definition

### 14.1 Success Hierarchy

Askora 必须保持：

```text
Engineering Metrics
≠
Product Metrics
≠
Learning Metrics
```

任何一层 PASS 都不能自动替代另一层。

### 14.2 Product Outcome

Askora 的产品成功不是“用户发了更多消息”，而是：

> **用户能够围绕真实 Learning Goal 持续进入有效学习闭环，并得到可信的状态、下一步行动和长期学习连续性。**

早期 Product Evidence 可以观察：

- 用户能否从材料/目标进入真实 Learning Activity；
- 是否能够理解当前状态与下一步；
- 是否能够恢复中断学习；
- 是否愿意完成必要的 independent / delayed validation；
- Local-first / BYOK 是否造成不可接受的主流程摩擦。

这些是产品可用性与价值证据，不等于学习效果。

### 14.3 Primary Learning Outcomes — FROZEN DECISION

Askora 的上位 Learning Outcome family 保持为：

1. **无提示独立成功**；
2. **延迟保持**；
3. **独立迁移**；
4. **单位学习时间能力增益**。

当前研究进一步支持使用：

- delayed independent performance；
- near / far transfer 分离；
- independent capability gain；
- time to first clean independent success；
- independent gain per active learning minute。

具体 experiment 必须预先指定 primary outcome，不得事后挑选最有利指标。

### 14.4 Guardrails

至少不得回归：

- false mastery promotion；
- answer leakage / exposure corruption；
- assessment contamination；
- unsupported citation / hallucinated source attribution；
- system failure misclassified as learner failure；
- LLM / Agent override of canonical learning ownership；
- user data loss / privacy boundary violation。

### 14.5 Non-primary Metrics

以下可以作为体验、诊断、成本或过程指标，但不得成为核心学习 KPI：

- DAU；
- session length；
- message count；
- conversation turns；
- likes；
- token usage；
- reading percentage；
- activity completion alone；
- immediate assisted correctness。

### 14.6 North Star Policy

Askora 当前不强行冻结单一 scalar North Star Metric。

原因：

- 单一指标容易把 retention、transfer 和 efficiency 压缩成错误代理；
- 当前仍处于单用户、小样本阶段；
- Learning Effect 尚未达到 population-level validation。

在证据成熟前，优先维护**Outcome Hierarchy + Guardrails**，而不是制造一个容易被优化偏的单值指标。

---

## 15. Technical Feasibility

### 15.1 Current Verdict — REPOSITORY-SUPPORTED CONCLUSION

当前仓库已经具备：

- Local Web / LocalOwner / Workspace 基础；
- Material / Retrieval；
- Learning Goal / Activity；
- Learner Evidence / Learner State；
- Assessment；
- deterministic Teaching Policy；
- Review Scheduler；
- BYOK / LocalSecretStore contracts；
- replay / testing / release evidence 基础。

因此 Askora 的核心产品范式在工程上已经表现出**可实现性**。

但：

> **Technical Feasibility ≠ Product Value Validation ≠ Learning Effectiveness。**

实现越完整，越不能用工程完成度替代真实产品和学习证据。

---

## 16. Product Discovery Priorities

在进一步扩大 Product Scope 前，P0 Discovery 应优先验证：

1. **Problem / JTBD**：目标用户是否真的把“独立、保持、迁移”视为值得持续付出成本的问题；
2. **Primary User**：当前定义是否过宽，最强需求出现在哪类长期学习任务；
3. **Alternative Behavior**：用户现在如何组合 Chat、笔记、搜索、闪卡、课程等方式解决同一 Job；
4. **Value Proposition**：Learner State + Teaching Policy 是否提供用户能明显感知的额外价值；
5. **Learning-loop Friction**：用户愿意接受多少验证、延迟复习、目标结构化和 BYOK 配置；
6. **Assessment Feasibility by Domain**：哪些领域适合可靠自动评估，哪些必须降级；
7. **Learning Effect**：对同一真实用户，Askora 的策略是否改善后续无提示表现，而不仅改善当前体验。

新 Discovery 应优先改变 Assumption 的证据状态，而不是继续增加功能。

---

## 17. Supporting Sources

当前 Strategy 的主要内部依据：

- [`PRODUCT-POSITIONING.md`](PRODUCT-POSITIONING.md)；
- [`../design/learning/个人AI辅助学习平台设计方案.md`](../design/learning/个人AI辅助学习平台设计方案.md)；
- [`../design/learning/AI学习系统算法与教学内核设计.md`](../design/learning/AI学习系统算法与教学内核设计.md)；
- [`../research/learning-core/synthesis/DR-03-01-教学策略与支架转换研究.md`](../research/learning-core/synthesis/DR-03-01-教学策略与支架转换研究.md)；
- [`../research/learning-core/synthesis/DR-03-04-学习效果验证与产品实验研究.md`](../research/learning-core/synthesis/DR-03-04-学习效果验证与产品实验研究.md)；
- [`../governance/product-development-process.md`](../governance/product-development-process.md)。

研究材料用于支持或挑战 Strategy，不自动拥有本文件的产品决策权。

---

## 18. Change Control

Product Strategy 只应在以下情况重新打开：

- 出现新的真实用户证据，推翻当前 Problem / JTBD / User 定义；
- 学习效果证据表明当前核心教学范式无效或产生显著伤害；
- 产品运行模式造成不可接受的价值/摩擦冲突；
- Askora 的目标用户、产品类别或核心价值发生有意改变。

修改流程：

```text
New Evidence / Strategic Constraint
→ Product Strategy Delta
→ 用户明确接受
→ 更新并重新冻结 PRODUCT-STRATEGY
→ 必要时更新 PRODUCT-POSITIONING
→ 再同步 Design / ADR / Specs / Linear / Implementation
```

禁止由下游实现便利性反向改写 Strategy。
