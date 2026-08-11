# Askora Primary Discovery Protocol

> 状态：Execution Protocol / Supporting Research  
> Issue：XIK-182  
> 日期：2026-08-11  
> 基线：`main@a4e682a9bd23288ce3b383c70a143ffe67666bf7`  
> 权威性：Research Execution Protocol，不是 Canonical Product / Design / Spec

## 1. 目的

直接验证以下未解决问题，而不是从 Askora 现有设计反推需求：

1. Primary User 是否真实存在且边界是否合理；
2. J1 Capability Verification 是否有真实用户价值；
3. J2 Learning Coordination 是否有真实用户价值；
4. no-hint / delayed / transfer verification 的可接受摩擦；
5. persistent Learner State 是否比 ordinary Chat Memory 有可感知增量价值；
6. Local-first / BYOK 的控制收益是否抵得过首次配置摩擦；
7. 不同 domain / task 的 Assessment evidence boundary。

本协议本身不能修改 `PRODUCT-STRATEGY.md`、`PRODUCT-POSITIONING.md`、Design、ADR、Specs 或实现。

如 Primary Evidence 要求改变上位结论：

```text
Primary Evidence
→ anonymized synthesis
→ explicit Strategy / Positioning / Design Delta
→ user accepts
→ canonical update
```

## 2. Evidence Hierarchy

### E0 — Not evidence

不能用来验证用户需求：

- Askora 已实现某功能；
- 用户只说“听起来不错”；
- feature preference 排序；
- message count / session length；
- Engineering PASS；
- AI 对用户需求的推断。

### E1 — Retrospective evidence

参与者对最近真实学习事件的具体复述，必须包含时间、行为、工具、困难、结果，而不是假设回答。

### E2 — Observed behavior

直接观察参与者完成学习、验证、恢复或配置任务。

### E3 — Repeated behavior

同一参与者跨 session 或延迟后重复出现的行为。

### E4 — Outcome evidence

能够连接到：

- independent success；
- delayed retention；
- transfer；
- coordination burden；
- false-mastery risk；
- time-to-capability。

## 3. Research Data Boundary

GitHub 只保存匿名化 Research Synthesis，不保存原始个人研究资料。

禁止进入 GitHub：

- 姓名与联系方式；
- 原始录音、视频、完整逐字稿；
- 未匿名截图；
- 私有学习材料；
- 任何可识别个人或访问外部服务的敏感信息。

GitHub 允许保存：

- anonymous Case ID；
- 去标识化 workflow facts；
- 聚合行为模式；
- assumption status；
- decision rationale；
- 不可反推出个人身份的必要摘要。

## 4. Core Hypotheses

### H1 — Capability Verification Need

AI 帮助产生的当前表现不能可靠代表用户独立能力；对一部分长期学习者而言，确认“撤除帮助后仍会”具有足够价值。

### H2 — Delayed / Transfer Value

对高价值学习目标，一部分用户认为延迟保持与迁移能力比“当前刚做对”更接近真正掌握。

### H3 — Learning Coordination Burden

多 session、多材料、多能力缺口学习中，用户需要付出显著成本维护“学到哪、哪里不会、下一步、何时复习”。

### H4 — Persistent State Incremental Value

Evidence-backed Learner State + next action 比 ordinary Chat Memory 更能降低重复解释、错误恢复与 next-action 决策负担。

### H5 — Friction Budget

用户只愿意接受与学习价值相称、可解释、可跳过的验证摩擦；频率过高会破坏净价值。

### H6 — Local-first / BYOK Trade-off

本地控制与模型自主权可能有价值，但首次配置与模型选择成本可能抵消该价值。

### H7 — Assessment Is Domain-bounded

Assessment 可靠性依赖 task type、rubric、ambiguity 与 grader agreement；高歧义任务不能依赖单次 LLM judgment 形成强 mastery evidence。

## 5. Participant Segments

### Segment A — Likely-fit

优先满足：

- 最近 3 个月存在持续数周以上的自主学习目标；
- 目标需要真正形成能力，而非一次性查答案；
- 使用过 AI、课程、书籍、文档、笔记或练习工具；
- 存在中断后继续学习场景；
- 能描述自己如何判断“学会”。

### Segment B — Convenience-first contrast

典型行为：

- 主要使用 AI 快速解决眼前任务；
- 很少主动延迟复习或验证；
- 对额外学习流程摩擦敏感。

该组用于判断 Askora 是否应该明确排除该 segment。

### Segment C — Domain contrast

至少覆盖：

1. 较客观可验证 domain，例如编程、数学、语言基础、规则性知识；
2. 高歧义 domain，例如设计判断、开放写作、复杂分析、策略问题。

## 6. Initial Sampling Rule

本阶段是 Product Discovery，不做总体统计推断。

初始覆盖目标：

- 3 个 Likely-fit case；
- 2 个 Convenience-first contrast case；
- 至少 2 种 domain 类型；
- 至少 2 个 case 有 delayed observation。

这是最低研究覆盖，不代表市场验证。

继续研究，如果：

- 新 case 持续出现关键新 failure mode；
- J1/J2 在 segment 间方向冲突；
- Local-first/BYOK 行为差异无法解释；
- Assessment boundary 仍高度不确定。

一轮可以收口，如果：

- 关键 workflow pattern 开始重复；
- 已主动寻找反例；
- 每项 assumption 都能给出 evidence status；
- 下一步产品决策不再依赖继续增加同类访谈。

## 7. Stage A — Retrospective JTBD Interview

只问最近真实发生的学习事件。

避免：

- “如果有一个 AI 自动帮你……”；
- “你觉得这个功能有用吗？”；
- 先展示 Askora feature list 再问偏好。

核心问题：

1. 最近一次持续至少数周的自主学习任务是什么？
2. 什么事件让你开始？
3. 必须做到什么才算成功？
4. 实际用了哪些材料和工具？
5. 最近一次 AI 直接帮助你完成本来想自己掌握的任务是什么？
6. AI 帮助后，你如何判断自己真的会了？
7. 有没有发生过“当时看懂/做对，后来自己不会”？最近一次是什么？
8. 有没有主动用新题、隔天重做、向别人解释等方式确认？为什么？
9. 中断几天后恢复学习时，你怎么知道从哪里继续？
10. 哪些信息需要自己维护？
11. 最近一次忘记“学到哪里/哪里不会/下一步”的具体后果是什么？
12. 你如何决定什么时候复习？
13. 有没有知道应该复习但最终没做？具体为什么？
14. 最终如何判断学习目标成功或失败？
15. 哪类证据最可信？

每个 case 输出：

```text
Trigger
→ Desired capability
→ Materials
→ Tools
→ Independent attempt
→ Assistance
→ Evidence / no evidence
→ Interruption
→ Recovery
→ Review
→ Final success judgment
```

## 8. Stage B — Capability Verification Behavior Test

流程：

```text
T0 independent attempt
→ optional AI assistance
→ classify assistance / answer exposure
→ T1 fresh no-hint item
→ confidence + perceived value
→ delayed return
→ T2 no-hint retention item
→ optional transfer item
```

观察：

- 何时主动请求帮助；
- 帮助程度；
- assistance 后主观 confidence；
- T1 independent performance；
- 是否愿意完成 T2；
- T2 真实完成情况；
- transfer 是否与目标相关；
- 用户认为哪次结果最能代表“我会了”。

如果参与者跳过验证，这本身就是 evidence。不要劝服、隐藏 Skip 或用 guilt copy 提高完成率。

## 9. Stage C — Learning Coordination Comparison

### Condition A — Ordinary workflow

参与者使用其当前真实方式：AI chat、notes、browser history、manual TODO 或其他工具。

### Condition B — Persistent learning-state workflow

只提供必要状态：

- current learning goal；
- latest evidence-backed state；
- unresolved gaps；
- next recommended action；
- review due reason；
- uncertainty / missing evidence。

记录：

- 恢复学习到开始有效活动所需步骤；
- 是否重复解释上下文；
- 是否重复学习已掌握内容；
- 是否漏掉 weak area；
- next action 是否被采纳；
- state 是否被纠正。

Strong evidence 不是“喜欢 dashboard”，而是重复出现：更快恢复、更少上下文重建、更少错误 next action、更准确识别 weak area 或更低 manual coordination burden。

## 10. Stage D — Learning-loop Friction Test

每个 friction event 记录：

```text
reason_shown
user_understood_reason
user_completed
user_skipped
skip_reason
perceived_value_after_result
would_accept_again
behavioral_cost
```

分类：

- **Useful friction**：结果改变 mastery judgment、next action、confidence 或 study plan；
- **Tolerated friction**：完成但感知价值弱；
- **Harmful friction**：明显导致绕过、放弃或认为系统阻碍正常学习。

## 11. Stage E — Local-first / BYOK First-value Test

不先问抽象的 privacy preference；观察真实首次配置：

- 是否理解为什么需要模型服务；
- 是否能独立完成必要配置；
- 是否理解可能产生的模型使用成本；
- 模型选择是否造成 decision paralysis；
- 从启动到 first learning value 的阻塞点；
- 是否需要研究者帮助；
- 完成一次后是否愿意再次主动使用。

Verdict：

- **Value**：控制权真实影响选择，并完成配置与再次使用；
- **Neutral constraint**：能接受，但不是选择产品的重要原因；
- **Adoption friction**：配置复杂度明显阻断 first-value 或 reuse。

## 12. Stage F — Assessment Calibration

任务分层：

- Tier A — Deterministic：objective / verifier / exact calculation；
- Tier B — Clear rubric：short answer / explicit criteria；
- Tier C — Partial / ambiguous：partially-correct reasoning / quality continuum；
- Tier D — Open / creative：design / strategy / creative / high ambiguity。

每个 sampled item 记录：

```text
case_id
domain
task_tier
rubric_available
llm_grade_1
llm_grade_2
reference_or_human_grade
agreement
false_positive_mastery_risk
recommended_evidence_weight
```

如果某类任务重复出现 high false-positive mastery：不得依赖单次 LLM judgment 形成 strong evidence；应降级并进入 Design/Spec review。

## 13. Anonymous Case Template

```markdown
# Case PD-XXX

## Segment
- fit: likely-fit / convenience-first
- domain: ...
- duration_of_real_goal: ...

## Workflow Reconstruction
- Trigger:
- Desired capability:
- Materials:
- Existing tools:
- Independent attempt:
- Assistance:
- Evidence of knowing:
- Interruption:
- Recovery:
- Review:
- Final success judgment:

## J1 Capability Verification
- observed need:
- no-hint behavior:
- delayed behavior:
- transfer behavior:
- friction response:

## J2 Learning Coordination
- current coordination burden:
- recovery behavior:
- ordinary workflow failure:
- persistent-state behavior:
- incremental value:

## Local-first / BYOK
- setup behavior:
- first-value friction:
- reuse behavior:

## Assessment
- task tier:
- grader agreement:
- false mastery risk:

## Contradictory Evidence
- ...

## Researcher Interpretation
- observed:
- inference:
- competing explanation:
- unresolved:
```

禁止填写可识别个人身份的信息。

## 14. Assumption Status Rubric

### Validated

需要目标 segment 中出现重复真实行为，有行为证据，主动寻找反例后仍成立，并足以支持当前产品决策。

### Partially validated

Problem/mechanism 存在，但 segment breadth、willingness、frequency 或 product value 仍不确定。

### Not validated

真实行为与假设明显不一致，或 contrast condition 表明现有替代已经足够。

### Insufficient evidence

case 太少、只有 stated preference、行为冲突无法解释或尚未发生必要 delayed observation。

禁止把 `Insufficient evidence` 自动升级为 `Partially validated`。

## 15. Decision Matrix

| J1 | J2 | Product implication |
|---|---|---|
| Strong | Strong | 支持当前 evidence-driven learning control loop 范式 |
| Strong | Weak | 考虑更轻量 capability-verification 产品形态 |
| Weak | Strong | 重新审视是否更接近 learning planning/state coordinator |
| Weak | Weak | 重新打开 Product Strategy，不继续扩大当前架构 |

## 16. Analysis Rules

每条关键 finding 都必须写：

```text
Observed
→ Interpretation
→ Competing explanation
→ Evidence status
```

主动寻找反例：

- 不在意独立验证的人；
- 认为 ordinary Chat Memory 已足够的人；
- 本地/BYOK 配置导致放弃的人；
- persistent state 增加管理负担的人；
- Assessment 与可信参考明显冲突的任务。

不同 domain 不得盲目合并结论。

禁止用 session length、turn count、completion count、like/dislike、prompt compliance 代替 J1/J2 或 learning outcome。

## 17. Synthesis Output

一轮 Primary Discovery 后创建：

`docs/research/product-discovery/PRIMARY-DISCOVERY-SYNTHESIS.md`

至少包含：

1. anonymous participant coverage；
2. workflow patterns；
3. disconfirming evidence；
4. J1 verdict；
5. J2 verdict；
6. friction findings；
7. Learner State vs Chat Memory verdict；
8. Local-first / BYOK verdict；
9. Assessment domain matrix；
10. assumption status matrix；
11. Strategy impact assessment；
12. recommendation：Keep / Refine / Reject。

证据不足时必须写 `Insufficient evidence`。

## 18. Exit Criteria for XIK-182

XIK-182 只有在以下条件满足时可以 Done：

- 已产生真实 Primary Evidence，而非只完成研究方案；
- 存在 likely-fit 与 contrast evidence；
- 至少有 delayed observation；
- J1 / J2 分别有明确 evidence status；
- Local-first/BYOK 有真实首次配置行为证据；
- Assessment 覆盖不同 task/domain tier；
- 反例被主动记录；
- 匿名 synthesis 已进入 GitHub；
- 没有原始个人数据进入公开仓库；
- 如需 Canonical Strategy Delta，已明确提出但没有擅自修改。

完成 protocol 本身**不等于完成 XIK-182**。

## 19. Immediate Next Action

第一步是获得第一个真实 case：

```text
real multi-week learning goal
→ retrospective workflow reconstruction
→ observable capability-verification task
→ delayed follow-up when applicable
```

在真实 case 出现之前，Primary User / JTBD / willingness 继续保持当前 evidence status。
