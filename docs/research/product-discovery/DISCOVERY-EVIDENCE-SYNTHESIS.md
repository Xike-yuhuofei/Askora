# Askora Product Discovery Evidence Synthesis

> 状态：Supporting Product Discovery Evidence  
> Issue：XIK-181  
> 日期：2026-08-11  
> 基线：`main@2521c9e1371afc20068669c413599700166cdc85`  
> 权威性：Supporting Evidence，不是 Canonical Product Decision  
> 目的：校准 `PRODUCT-STRATEGY.md` 中 Primary User / JTBD / Learning-loop Friction 等假设的证据状态，并明确下一轮 Primary Discovery 必须回答什么

---

## 1. 研究边界

本研究只回答：

1. 外部经验研究是否支持 Askora 所关注的问题确实存在；
2. 当前替代产品已经覆盖哪些学习能力；
3. 哪些 Strategy assumption 可以降低不确定性，哪些仍缺真实目标用户证据；
4. 哪些问题必须通过真人行为、纵向使用或产品实验继续验证。

本研究**不能**证明：

- Askora 已经找到 Product-Market Fit；
- 当前 Primary User 已被真实用户研究验证；
- 用户愿意为严格学习闭环承担额外摩擦；
- Local-first / BYOK 对目标用户一定是净价值；
- 当前 Teaching Policy 已经优于其他 AI Tutor；
- 当前 Learner State 的产品价值已经超过普通 Chat Memory。

证据等级：

```text
A. Direct empirical evidence
B. Official product capability evidence
C. Repository-supported inference
D. Anecdotal / qualitative signal
E. Product assumption / unresolved question
```

只有 A/B 可以用于描述外部事实；C 用于连接 Askora 设计；D 只能生成研究问题；E 不得升级为事实。

---

## 2. Executive Findings

### F1 — “受助表现 ≠ 独立学习”得到较强外部支持

**状态：Partially validated at problem-existence level**

2026 年一项随机实验让 196 名大学生完成创造性任务。自由使用 ChatGPT 的组在有 AI 的第一项任务中表现更好，但 AI 撤除后的独立任务优势消失；“先自己思考、再与 ChatGPT 协作”的受约束组在后续独立任务中表现更好。

这支持 Askora 的核心语义：

```text
assisted performance
!=
independent capability
```

但该研究领域是创造性任务，不能直接外推到所有学习领域，也不能证明用户愿意长期接受 Askora 的验证流程。

### F2 — GenAI 可能放大初学者的“能力错觉”

**状态：Source-backed risk signal**

ICER 2024 对 21 名初学编程者进行观察、访谈与眼动研究。20/21 完成任务，但困难学习者更容易让 GenAI 放大既有元认知问题，并出现对自身表现的错误判断与 competence illusion。

这支持 Askora 将 `False Mastery` 与 `Assistance Dependency` 作为高优先级风险，但不证明 Askora 当前解决方案已经有效。

### F3 — “更强 pedagogical prompt”本身不能证明更好的学习

**状态：Strong challenge to simplistic tutoring differentiation**

ICER 2026 的预注册真实 CS1 研究比较 pedagogically constrained baseline tutor 与加入 Self-Regulated Learning scaffold 的 AI tutor。研究覆盖 1,059 名学习者、六周课程环境；SRL tutor 改变了参与行为，但没有在预注册的主要学习结果上形成显著优势。

因此：

> Askora 不能把“更苏格拉底、更会支架、更复杂的 system prompt”当作战略差异化或学习效果证据。

Askora 必须验证的是**跨时间状态、Learning Evidence、assistance/exposure semantics、独立/延迟/迁移验证与下一步控制**是否带来增量价值。

### F4 — 独立/延迟验证有学习科学依据，但“用户愿意做”仍未验证

**状态：Mechanism supported; product willingness insufficient**

现有 Learning Core research 已支持 retrieval / delayed retention / transfer 等 outcome；外部学习研究也长期支持 testing effect 与 spaced retrieval。

但 Product Discovery 需要回答的是另一个问题：

> 用户是否愿意在真实产品中持续完成这些动作，以及多大强度开始变成不可接受的 workload？

Anki 官方 FSRS 文档明确展示 retention 与 workload 的快速增长 trade-off：更高 retention 会增加复习负担，默认 90% 被作为平衡点，接近 100% 时 workload 急剧上升。

这不能直接决定 Askora 阈值，但支持一个产品原则：**学习机制有效不代表应该最大化使用频率。**

### F5 — 当前替代产品已经覆盖“AI Tutor 表层能力”

**状态：Validated competitor capability**

截至 2026-08-11：

- ChatGPT Study Mode 支持 Socratic-style guidance、理解检查、上传学习材料、practice questions / flashcard-style review，以及基于 Memory 的个性化；
- Claude for Education 的 Learning Mode 强调 guided discovery、Socratic questioning 与 thinking partner；
- NotebookLM 支持 source-grounded chat、inline citations、study guides、flashcards / quizzes，并可记录 flashcard/quiz progress；
- Anki / FSRS 已成熟承担 spaced repetition 与 retention/workload scheduling。

因此 Askora 不能把以下能力单独定义为差异化：

```text
Socratic chat
source grounding
quiz
flashcard
spaced repetition
chat memory
```

持续 Learning Goal + Evidence-backed Learner State + explicit Teaching Policy + assistance/exposure tracking + independent/delayed/transfer validation + review/replan 仍是合理的**差异化假设**，但其用户价值尚未被 Primary Discovery 验证。

### F6 — LLM Assessment 可用性明显依赖任务类型与答案质量

**状态：Partially validated / domain-bounded**

BEA 2026 的自动短答案评分研究表明：few-shot LLM 对完全正确和完全错误答案较好，但对部分正确、中间质量答案的 agreement 明显下降；human-human agreement 更稳定，增加 task-specific adaptation 可缓解问题。

这直接反对“跨领域 Assessment 普遍可靠”的宽泛假设。

Askora 必须把 Assessment 可靠性视为**domain / task / response-type / evidence-quality dependent**，并在不可靠时降低 Learning Evidence 权重，而不是强行输出 mastery judgment。

### F7 — Local-first / BYOK 的学习者价值仍无直接证据

**状态：Insufficient evidence**

Local control、privacy、data ownership 在一般 AI 场景具有合理价值，但本轮没有找到足够直接证据证明：

> Askora 的目标学习者愿意承担本地运行、API key、模型费用理解与配置成本，以换取这些控制权。

因此 Local-first / BYOK 当前应继续作为已冻结 Product Shape / owner constraint，而**不能升级为“目标用户已验证的核心购买理由”**。

---

## 3. Evidence Review

## 3.1 Assisted Performance vs Independent Capability

### Evidence A1 — Think First, ChatGPT Later

- Wong, S. S. H., & Qiu, S. X. (2026)
- N = 196 university students
- randomized three-group design
- assisted task followed by an AI-free independent task

主要观察：

1. general-AI group 在 AI 可用时获得即时表现优势；
2. AI 撤除后，该优势没有保持；
3. regulated-AI group 先独立生成想法，再使用 ChatGPT 改进，在后续独立任务中优于其他组；
4. 研究者明确区分 performance 与 learning。

Askora implication：

- `assisted` / `answer-exposed` 必须与 `independent` 分离；
- “当前 turn 做对”不能自动 promotion mastery；
- assistance sequencing 可能影响后续独立能力；
- 必须在 AI 撤除后测能力。

限制：创造性任务；短期实验；不能替代 Askora 多领域纵向验证。

## 3.2 Metacognition / Illusion of Competence

### Evidence A2 — The Widening Gap

- Prather et al. (ICER 2024)
- 21 novice programmers
- observation + interview + eye tracking

研究显示 GenAI 对不同初学者并非同质影响：部分学习者能利用 GenAI 加速既有意图，困难学习者则可能被 GenAI 放大元认知问题并形成 competence illusion。

Askora implication：

- Learner State 不能由“任务完成”或 AI 对话流畅度推断；
- false mastery 是真实风险方向；
- 需要 explicit evidence semantics；
- novice / struggling learner 可能尤其需要谨慎 assistance fading 与独立验证。

限制：小样本、编程领域、质性/观察研究。

## 3.3 Pedagogical Prompting Is Not the Product Moat

### Evidence A3 — Steering AI Tutors Through System Prompts

- Barth et al. (ICER 2026)
- preregistered crossover study
- N = 1,059
- six weeks in authentic CS1 course

加入 SRL / cognitive engagement scaffold 可以改变交互行为与参与方式，但没有改善预注册 confirmatory learning outcomes。

Askora implication：

```text
better tutor persona / prompt
!=
validated learning system
```

因此长期产品价值必须通过 durable learner state、evidence lifecycle、decision policy 与 delayed/transfer outcome 验证，而不是通过 prompt compliance 或 engagement 证明。

## 3.4 Assessment Reliability

### Evidence A4 — Quality-conditioned short-answer scoring

BEA 2026 在开放式 biology short-answer 上比较 multiple LLMs、fine-tuned encoder 与 human expert。结果显示：

- human-human agreement 最高且跨答案质量更稳定；
- AI 对完全正确/错误答案表现较好；
- 对 partially-correct / mid-range responses 明显退化；
- task-specific adaptation 越强，退化越小。

Askora implication：

建议把 Assessment evidence 至少分为：

| Tier | 任务类型 | 默认处理 |
|---|---|---|
| A | objective / syntactically verifiable / deterministic | 可形成较强 evidence |
| B | rubric-grounded short answer with clear criteria | 可形成 conditional evidence，保留 uncertainty |
| C | partially-correct / ambiguous reasoning | 降低 confidence；必要时追加 probe / multiple evidence |
| D | open design / creative / high-ambiguity transfer | 不允许单次 LLM grading 直接 promotion mastery |

该 tiering 是本研究的 Product/Design inference，不是新的 Canonical contract。

---

## 4. Alternative Capability Update

### 4.1 ChatGPT Study Mode

官方能力包括：

- Socratic-style questioning；
- layered explanation；
- open-ended understanding checks；
- uploaded images / PDFs / course materials；
- practice questions / quiz / flashcard-style review；
- Memory-based personalization。

结论：Askora 不能依赖“会问问题、会测验、会记住偏好/学习目标”作为唯一定位。

### 4.2 Claude for Education

官方 Learning Mode 强调：

- guided discovery；
- Socratic questioning；
- principles over direct solutions；
- thinking partner rather than answer machine。

结论：Socratic tutor identity 已经是通用 AI 产品范式的一部分。

### 4.3 NotebookLM

官方产品支持：

- 用户上传/导入 sources；
- source-grounded chat 与 inline citations；
- study guides 等衍生产物；
- flashcards / quizzes；
- 记录 flashcard “Got it / Missed it” 与 quiz progress。

结论：source grounding + study artifact + simple progress memory 也不能单独定义 Askora。

### 4.4 Anki / FSRS

Anki 已成熟处理 spaced repetition；其官方 manual 同时明确 retention 与 workload 之间存在显著 trade-off。

结论：Askora 的复习能力必须与 Learning Evidence / goal / learner state / teaching decision 结合，而不是重新实现一个独立 SRS 作为产品中心。

---

## 5. Assumption Status Matrix

状态定义：

- **Validated**：已有足够直接目标证据，可明显降低战略不确定性；
- **Partially validated**：问题或机制存在有支持，但 Askora 用户价值/行为仍需验证；
- **Challenged**：存在反证或边界证据，原假设必须收窄；
- **Insufficient evidence**：不能可靠判断。

| Strategy Assumption | XIK-181 状态 | 依据 | Strategy action |
|---|---|---|---|
| 目标用户重视“真正学会”而不只是即时便利 | **Partially validated** | performance-learning gap 与 competence illusion 有实证；但付费/持续行为偏好未知 | 保留 assumption，不升级 |
| 用户愿意接受 no-hint / delayed / transfer validation | **Insufficient evidence** | 学习机制有依据；产品接受度、回访率、workload tolerance 未验证 | 必须做行为实验 |
| Learner State 明显优于普通 Chat Memory | **Insufficient evidence** | 现有替代品已有 memory/personalization；缺直接任务结果比较 | 必须做对照任务 |
| 用户自带材料足以成为主要知识边界 | **Partially validated** | NotebookLM 等证明 source-grounded study workflow 可成立；目标用户覆盖范围未知 | 保留，不扩张为 universal claim |
| Local-first + BYOK 的控制收益足以抵消配置摩擦 | **Insufficient evidence** | 缺直接 learner willingness evidence | 不作为已验证 Value Proposition |
| 跨领域 Assessment 能产生足够可靠 Learning Evidence | **Challenged / domain-bounded** | short-answer scoring 在部分正确/高歧义答案明显退化 | 需要 domain tier / confidence degradation |
| 受约束 Teaching Policy 的收益值得系统复杂度 | **Insufficient evidence / challenged** | prompt-level stronger SRL scaffold 未改善预注册 learning outcomes | 必须用 longitudinal outcome 证明复杂度 |
| 单用户 N-of-1 evidence 足以指导早期迭代 | **Repository-supported** | 当前产品阶段与 DR-03-04 治理选择 | 继续用于早期 learning iteration，但不得代替 market/user validation |

### 5.1 结论

本轮没有任何一个原本为 `ASSUMPTION` 的核心 Product Discovery 假设达到足以改成 `VALIDATED USER NEED` 的证据强度。

这是正常结果，不是研究失败。

真正被增强的是：

- Problem existence confidence；
- assessment boundary clarity；
- competitor differentiation clarity；
- 下一轮 Primary Discovery 的可证伪性。

---

## 6. Primary User Recommendation

### 当前建议：KEEP AS CANDIDATE，暂不修改 Canonical Strategy

当前 Primary User：

> 持续数周至数月自主学习高认知负荷主题、拥有自己的学习材料、重视真正掌握而非快速获得答案，并愿意接受本地工具与 BYOK 的个人学习者。

本轮证据不足以把它升级为 validated segment，也不足以推翻它。

下一轮招募必须避免只找“喜欢 Askora 理念”的人，应至少包含：

1. **Likely-fit cohort**：存在真实多周学习目标、个人材料、独立能力要求；
2. **Convenience-first contrast cohort**：主要使用 AI 获取即时解决方案；
3. **domain contrast**：至少覆盖一个可较客观验证领域与一个高歧义开放领域。

研究目标不是证明 likely-fit 更好，而是找到：

> 哪些任务条件下，长期 evidence/control loop 的价值足以覆盖它的摩擦。

---

## 7. JTBD Recommendation

### 当前建议：保留 Primary JTBD，但拆成两个可独立证伪的 Job

现有 Primary JTBD 过于完整，容易把产品解决方案直接写进 Job。

研究层建议拆成：

### J1 — Capability Verification

> **当 AI 已经帮助我理解或完成任务后，我需要知道：如果帮助撤除、时间过去或任务变化，我是否仍然真正会。**

当前证据强度：**Medium / Partially validated**。

### J2 — Learning Coordination

> **当学习跨越多个 session、材料和能力缺口时，我需要减少自己维护“学到哪、哪里不会、该复习什么、下一步做什么”的协调工作。**

当前证据强度：**Low / Insufficient evidence**。

为什么拆分：

- J1 的 performance-learning gap 有较强外部经验支持；
- J2 目前主要来自 Askora 架构推论；
- 如果 J1 强、J2 弱，Askora 可能需要更轻的 validation layer；
- 如果 J1 与 J2 都强，persistent Learner State + Teaching Policy 才更可能形成系统级价值。

这是 Research refinement，不自动修改 `PRODUCT-STRATEGY.md`。

---

## 8. Learning-loop Friction Budget

本轮不能给出“用户最多接受 X 次验证”之类伪精确阈值，但可以冻结研究原则。

### 8.1 No-hint validation

应优先用于：

- 发生了 substantial assistance / answer exposure 之后；
- mastery promotion 前；
- 高价值 Learning Goal 的关键能力点。

不应：

- 每个微小概念都强制测；
- 把“拒绝直接答案”当作 pedagogical virtue；
- 因用户请求帮助而惩罚用户。

用户可以获得答案；系统只改变 evidence semantics 与后续验证义务。

### 8.2 Delayed validation / review

应根据 evidence / forgetting risk / goal importance 调度，而不是最大化 review frequency。

产品必须显式考虑：

```text
expected learning value
/
required user effort
```

Anki 的 retention-workload trade-off 说明：更高 retention target 可以迅速增加 workload。Askora 需要自己的 friction evidence，不能简单追求最高保持率。

### 8.3 Transfer validation

只在目标本身要求 transfer 时作为高权重 outcome。

事实记忆、术语识别与开放设计能力不应使用同一种 transfer obligation。

### 8.4 Explainability

任何额外学习摩擦都应该能回答：

- 为什么现在需要做？
- 这次结果会改变什么？
- 跳过会发生什么？
- 系统是否仍保留用户自主权？

无法解释的 friction 默认是 Product Debt，而不是“严谨学习”。

---

## 9. Local-first / BYOK Verdict

### Evidence status: INSUFFICIENT

当前只能确认：

- Askora 已明确选择 personal / local-first / BYOK；
- 这与数据控制、长期可拥有性、降低中心化依赖的产品价值一致；
- 但目标用户是否认为这些收益大于 setup / key / billing / provider choice friction，尚无直接证据。

因此：

1. 不改变当前 Frozen Product Shape；
2. 不在 Strategy 中把 Local-first / BYOK 宣称为“已验证用户优势”；
3. Primary Discovery 必须记录 first-value 前的 setup friction；
4. 测试时区分：
   - “我喜欢控制权”；
   - “我真的愿意完成配置”；
   - “完成配置后我愿意长期继续使用”。

只有第三类行为才足以显著降低该 assumption 的风险。

---

## 10. Assessment Feasibility Verdict

### 当前判断：PARTIALLY VALIDATED, MUST BE DOMAIN-BOUNDED

Strategy assumption 不应再被理解为：

> 一个通用 LLM grader 可以跨所有领域稳定产生 mastery evidence。

更合理的研究假设是：

> **不同任务具有不同的可评估性；Askora 只有在 scoring validity、provenance 与 confidence 足够时才允许 evidence 驱动 mastery / Teaching Policy，高歧义场景必须降级。**

下一轮研究至少记录：

- task type；
- answer format；
- rubric availability；
- expected ambiguity；
- grader agreement；
- repeatability；
- false-positive mastery risk。

---

## 11. Strategy Impact Assessment

### Verdict: NO CANONICAL PRODUCT STRATEGY DELTA YET

本轮证据：

- 支持核心 Problem 的存在；
- 强化 assisted / independent 语义；
- 挑战“pedagogical prompting 就等于 learning effectiveness”；
- 要求收窄 Assessment reliability；
- 进一步证明表层 AI learning features 已商品化；
- 没有足够 Primary Discovery evidence 改写 Primary User / Primary JTBD / Local-first value。

因此当前正确动作是：

```text
Update Supporting Research
→ keep PRODUCT-STRATEGY assumptions explicit
→ run Primary Discovery
→ only then consider Strategy Delta
```

不因为研究“方向吻合”就提前把 `ASSUMPTION` 改成 `VALIDATED`。

---

## 12. Primary Discovery Protocol

下一阶段必须获得原始目标用户证据。

### D1 — Retrospective JTBD Interview

只研究最近发生的真实多周学习任务，不展示 Askora feature list。

至少还原：

```text
trigger
→ desired capability
→ materials
→ tools used
→ assistance
→ evidence of knowing
→ interruption
→ return
→ review
→ final success judgment
```

关键问题：

- 什么时候“AI 帮我做出来”与“我真的会”发生冲突？
- 用户今天如何判断自己学会？
- 谁在维护下一步？
- 哪一步最累、最容易放弃？
- 一周以后如何知道还会不会？

### D2 — Behavior Test: Capability Verification

给用户一个真实学习任务：

1. independent attempt；
2. optional assistance；
3. answer exposure tracked；
4. fresh no-hint item；
5. delayed return；
6. transfer item when domain supports it。

观察：

- 是否理解 assisted / independent distinction；
- 是否愿意继续验证；
- 是否认为验证结果有价值；
- 何时 friction 开始超过价值。

### D3 — Behavior Test: Learning Coordination

让用户在多 session 学习中分别使用：

- ordinary AI chat / user-managed workflow；
- persistent goal + state + next-action workflow。

比较：

- 恢复学习所需时间；
- “下一步做什么”决策负担；
- 状态判断错误；
- 是否真正采纳系统 next action；
- 用户是否认为 state/history 有不可替代价值。

### D4 — Local/BYOK First-value Test

不要问“你重视隐私吗？”；记录：

- 完成 provider / key setup 的成功率；
- 首次价值前步骤与放弃点；
- 对模型成本/选择是否理解；
- 是否愿意第二次主动使用。

### D5 — Assessment Calibration

按 domain / task tier 抽样，比较：

- LLM grade；
- deterministic oracle / rubric；
- human/user adjudication；
- repeated grading stability。

任何 high false-positive mastery 场景都必须触发降级，而不是扩大自动化。

---

## 13. Exit Criteria

XIK-181 的“Secondary Evidence Synthesis”可在本文件形成后关闭该子阶段，但以下结论仍不得标记 Validated，直到出现 Primary Evidence：

- Primary User；
- Primary JTBD 的用户价值强度；
- no-hint / delayed / transfer 的真实接受度；
- Learner State 对 Chat Memory 的增量价值；
- Local-first / BYOK 的净用户价值。

Primary Discovery 完成后，必须对每项 assumption 给出：

```text
Validated
Partially validated
Not validated
Insufficient evidence
```

如出现反证，优先修改 Strategy，而不是修改实验解释来保护现有产品设计。

---

## 14. Sources

### External empirical evidence

1. Wong, S. S. H., & Qiu, S. X. (2026). *Think First, ChatGPT Later: Guiding Human–AI Collaboration for Learning Gains in Independent Human Creativity*. Educational Psychology Review, 38, 45. https://doi.org/10.1007/s10648-026-10118-7
2. Prather, J., Reeves, B. N., Leinonen, J., MacNeil, S., Randrianasolo, A. S., Becker, B. A., Kimmel, B., Wright, J., & Briggs, B. (2024). *The Widening Gap: The Benefits and Harms of Generative AI for Novice Programmers*. ICER 2024. https://doi.org/10.1145/3632620.3671116
3. Barth, M., Thorgeirsson, S., Etemadi, K., Leinonen, J., Cotrini, C., & Su, Z. (2026). *Steering AI Tutors Through System Prompts: A Crossover Study on Self-Regulated Learning and Cognitive Engagement Scaffolds in CS1*. ICER 2026. https://icer2026.acm.org/details/icer-2026-papers/18/When-More-Engagement-Doesn-t-Mean-More-Learning-LLM-Tutors-and-Self-Regulated-Learni
4. Gurin Schleifer, A., Ariely, M., Beigman Klebanov, B., Salman, A., & Alexandron, G. (2026). *Quality-Conditioned Agreement in Automated Short Answer Scoring: Mid-Range Degradation and the Impact of Task-Specific Adaptation*. BEA 2026. https://doi.org/10.18653/v1/2026.bea-1.29

### Official alternative-product evidence

5. OpenAI. *Using Study Mode in ChatGPT*. https://help.openai.com/en/articles/11780217-chatgpt-study-mode-faq
6. Anthropic. *Claude for Education*. https://www.anthropic.com/education
7. Google. *Learn about NotebookLM*. https://support.google.com/notebooklm/answer/16164461
8. Google. *Generate Flashcards or Quizzes in NotebookLM*. https://support.google.com/notebooklm/answer/16958963
9. Anki. *Deck Options / FSRS / Desired Retention*. https://docs.ankiweb.net/deck-options.html

### Internal Askora evidence

10. `docs/product/PRODUCT-STRATEGY.md`
11. `docs/research/product-discovery/USER-PROBLEM-JTBD-RESEARCH.md`
12. `docs/research/product-discovery/ALTERNATIVES-OPPORTUNITY-RESEARCH.md`
13. `docs/research/learning-core/synthesis/DR-03-04-学习效果验证与产品实验研究.md`
14. `docs/design/learning/AI学习系统算法与教学内核设计.md`

---

## 15. Final Research Recommendation

当前最值得验证的不是：

> “用户喜欢不喜欢 AI Tutor？”

而是两个可证伪问题：

> **J1：用户是否愿意为“知道自己真的会了”承担适量 independent / delayed / transfer verification？**

> **J2：跨 session 的 goal / state / next-action coordination 是否足够痛，以至于 persistent Learner State + Teaching Policy 比普通 Chat Memory 明显更有价值？**

如果 J1 成立、J2 不成立，应考虑更轻量的 capability-verification product。

如果 J1 与 J2 都成立，Askora 当前“长期 evidence-driven learning control loop”的产品范式才获得真正的 Product Discovery 支撑。

如果两者都不成立，应重新打开 Product Strategy，而不是继续扩展现有架构。
