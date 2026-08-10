# SYS03 — Learner Model

> Spec ID：`SYS03-*`  
> 对应设计：4.3 学习者建模与状态估计  
> 状态：Canonical Implementation Contract  
> 版本：v0.3 + v1 Workspace/Rebuildability Alignment  
> 上位约束：`docs/product/PRODUCT-POSITIONING.md`

## 1. Responsibility

### SYS03-001

SYS03 的唯一职责是把同一 Workspace 内、跨时间的有效学习证据融合为可版本化、带不确定性的 `LearnerState` 与 `MasteryEstimate`。

### SYS03-002

SYS03 是 `LearnerEvidence` accepted/rejected/invalidated 状态、`MasteryEstimate`、`LearnerState` 与 `MisconceptionHypothesis` 的唯一 owner。

SYS03 MUST NOT 判分 AssessmentResult、选择 TeachingAction、拥有 TeachingStage、修改 LearningPlan/ReviewSchedule，或把 LLM/Conversation/用户自述直接写成 mastery truth。

### SYS03-003 — Canonical Rebuildable Projection

`MasteryEstimate` / `LearnerState` 是当前 authoritative **canonical derived projection**，不是不可替代的原始事实。

其 reconstruction truth MUST 是：

```text
accepted durable LearningEvidence
+ exact projector/algorithm version
+ exact parameter/config version
→ MasteryEstimate / LearnerState
```

因此：

- 只有 SYS03 可以写当前 projection；
- projection 被删除、失效或算法升级后 MUST 可从 durable evidence 重建；
- 删除/纠正输入 evidence 后 MUST supersede/invalidate 受影响 projection，再重建；
- MUST NOT 因 cache/index/model provider failure 丢失 learner truth source。

### SYS03-004 — Workspace Isolation

LearnerEvidence、MasteryEstimate、LearnerState、MisconceptionHypothesis MUST 有明确 `workspace_id` 或能通过 exact owner refs 无歧义解析到 Workspace。

默认：

```text
Workspace A evidence
MUST NOT update
Workspace B LearnerState
```

LocalOwner 相同不构成跨 Workspace 融合许可。未来跨 Workspace learner model 若被产品允许，必须通过新的上位产品/架构决策。

## 2. Existing v0.2 Contracts Retained

### SYS03-010 — Mastery Is Inference

MasteryEstimate 是推断，不是客观事实。MUST 同时保存 confidence/evidence sufficiency，并可追溯算法、Workspace 与证据。

### SYS03-011 — No SetMastery

SYS03 MUST NOT 接受来自 SYS04/SYS08/UI/LLM 的 `SetMastery`、`SetMasteryProbability` 或等价越权命令。

### SYS03-020 — Learner State Dispute

用户争议状态时 MUST 进入 dispute/retest/recompute 流程，MUST NOT 提供通用直接改 mastery probability 的命令。

### SYS03-030 — MVP Baseline

v0.3 canonical projector SHOULD 使用透明、可解释、可版本化的 evidence eligibility/weighting + BKT 或等价简单概率/证据投影 baseline；必须保留可比较的简单 baseline。Deep KT MUST NOT 成为 canonical truth。

### SYS03-031 — Evidence Weighting

Evidence weighting 至少 MUST 考虑：correctness/score、assessment confidence、`assistance_state`、`scaffold_control`、`hint_specificity`、`answer_exposure`、delay、novelty/transfer distance、item difficulty（若可靠）、重复 item 与 error/misconception evidence。

SelfAssessmentEvidence MAY 被接纳为低权 evidence，但其权重/用途 MUST 低于受控独立作答、延迟提取与迁移评估，不得直接覆盖行为证据。

### SYS03-032 — Mastery Labels

稳定掌握至少 SHOULD 需要足够的独立成功证据、延迟提取证据、无高置信活跃误区、足够 confidence/evidence sufficiency；迁移能力必须额外要求足够新颖的独立迁移证据。具体阈值属于版本化 policy/config，不得硬编码为科学定律。

### SYS03-033 — BKT Baseline

BKT MAY 作为可解释 baseline；参数必须版本化。简单加权证据模型 MUST 保留为可比较 baseline。

### SYS03-034 — Challenger Boundary

PFA MAY 作为离线 challenger；IRT 只有在题库稳定且有校准数据后 MAY 用于难度/能力校正；DKT/SAKT/SAINT/AKT/Deep KT 只能作为 challenger/auxiliary feature，MUST NOT 作为 canonical truth source。

### SYS03-035 — No RL Mastery Update

Learner modeling 是状态估计问题。MUST NOT 引入 RL 来“更新 mastery”。

### SYS03-040 — Logical Separation

`LearnerEvidence`、`MasteryEstimate` 与 `LearnerState` MUST 逻辑分离。

### SYS03-041 — Version Stream

MasteryEstimate/LearnerState 更新 MUST append/version；历史估计必须可查询，除非明确 data-erasure contract 要求删除。

### SYS03-042 — Provenance

每个 MasteryEstimate MUST 关联：

```text
workspace_id
source evidence ids
algorithm/version
parameter bundle version
created_at
```

### SYS03-043 — Recompute / Replay

Recompute MUST 支持从同一 Workspace 的 accepted durable evidence/event 重新投影，MUST NOT 依赖在线 LLM。

### SYS03-044 — Evidence Deletion Reprojection

若用户删除/永久删除某条曾影响当前 MasteryEstimate/LearnerState 的 LearningEvidence：

```text
remove/invalidate evidence
→ identify affected KU / projection range
→ recompute from remaining valid evidence
→ publish new current projection
```

MUST NOT 继续保留包含已删除 evidence 影响的旧 current state；replay MUST consume erasure/no-resurrection constraints where applicable。

### SYS03-050 — Uncertainty

低质量/不完整证据的正确语义是“不确定”，MUST NOT 伪造精确 mastery。

### SYS03-060 — Evidence Idempotency

同一 LearnerEvidence/source result 只能被 canonical projector 接纳一次。

### SYS03-061 — Event Idempotency

重复事件消费 MUST NOT 再次增加 evidence_count 或重复更新 mastery。

### SYS03-062 — Deterministic Projection

固定 Workspace + ordered evidence set + exact algorithm/config version MUST 得到相同 semantic state content。

## 3. v0.3 Assistance-aware Evidence

### SYS03-200 — Assistance-aware Evidence

Evidence eligibility/weight MUST 基于 SYS04 记录的实际：

```text
assistance_state
scaffold_control
hint_specificity
answer_exposure
```

不得基于 SYS05 allowed envelope 假定实际经历，也不得继续使用全局 integer `hint_level/scaffold_level/answer_exposure_max` 作为 canonical 语义。

### SYS03-201 — Independence Rules

`ANSWER_EXPOSED` success MUST NOT 成为 independent mastery evidence；`ASSISTED` success MUST 与 independent evidence 分离并按 versioned rules 降权/限制用途。只有 fresh `INDEPENDENT` Attempt 可形成新的 independent success evidence。

### SYS03-202 — Missing Assistance

assistance/exposure 不可确定时 MUST conservative：降低 eligibility/weight 或标记 uncertain；MUST NOT 默认 `INDEPENDENT`。

### SYS03-203 — Conversation Is Not Evidence

以下均 MUST NOT 直接增加 mastery/evidence count：

- Conversation turn；
- 用户说“我懂了”；
- thumbs up/down；
- 使用时长；
- 阅读百分比；
- LLM 判断“看起来会了”。

它们 MAY 产生 FeedbackSignal、自评候选或下一次 Assessment request，但只有结构化 owner contract 接纳后才可能影响 LearnerState。

## 4. Misconception Boundary

### SYS03-210

```text
Misconception definition      → SYS01
MisconceptionEvidence         → SYS04
MisconceptionHypothesis       → SYS03
Remediation decision          → SYS05
```

SYS03 MAY 根据多个 evidence 更新 hypothesis/confidence，但 MUST NOT 把单个 SYS04 evidence 无条件提升为 confirmed learner misconception。

MisconceptionHypothesis 也必须 workspace scoped。

## 5. LearnerState vs TeachingStage

### SYS03-220

`TeachingStage` 属于 SYS05 对当前 TeachingContext 的派生控制语义，MUST NOT 存入 LearnerState 作为 persistent learner stage。

历史 `LearnerState.learning_stage_summary` 在 v0.3 MUST 迁移/重命名为 `learner_progress_summary` 或等价非教学策略摘要，并 MUST 明确与 SYS05 TeachingStage 没有 ownership/inheritance 关系。

## 6. Independent Validation Boundary

### SYS03-230

`INDEPENDENT_VALIDATION_REQUIRED` 是 SYS05 policy-control obligation，不是 MasteryState。SYS03 MUST NOT 创建、完成或清除该 obligation。

### SYS03-231

在 fresh independent Attempt 实际发生并被 SYS04 接纳前，SYS03 MUST NOT 因“已安排独立验证”“时间已过去”或“LLM 判断会做”而假定 obligation 已完成。

### SYS03-232 — Configurable Parameters

mastery threshold、evidence weights、hint-dependency weighting、delay/transfer qualification 等参数 MUST versioned/traceable，MUST NOT 写成不可变科学常数。

## 7. Failure Semantics

必须区分：evidence ineligible、assistance unknown、source result superseded、workspace mismatch、unknown KnowledgeUnit revision、algorithm/parameter unavailable、projection failure、insufficient evidence、state version conflict、reprojection required。

Projector failure MUST 保留 last valid state 并记录 failure/lag；若 last valid state 已被 evidence erasure invalidate，则 MUST 标记 stale/unavailable，而不是继续当 current truth。Challenger failure MUST NOT 影响 canonical baseline。

## 8. Observability

必须记录：workspace/safe learner ref、evidence acceptance/rejection/weight reason、actual assistance snapshot refs、prior/posterior estimate、algorithm/parameter version、projection latency/lag、replay divergence、reprojection reason、misconception hypothesis changes、confidence/effective evidence size。

Metrics MAY 包含 log loss、Brier、ECE/calibration、next-attempt prediction、false mastery promotion、hint-dependency identification 与 replay determinism；这些预测指标不等于学习效果证据。

默认日志不得记录完整 learner answer/history；使用 safe refs/aggregates/reason codes。

## 9. Security / Privacy

LearnerState/MasteryEstimate/LearningEvidence 属个人本地学习数据：

- 默认只在 Local Server/SQLite 本地存储；
- 外部模型不得默认接收完整 learner history；
- 跨 Workspace query 必须 fail closed；
- 用户可查看、导出、删除长期状态所依据的 evidence，具体遵循 privacy/data-control contract；
- Backup/Export/erasure semantics 服从上位 local data contract。

## 10. Tests

### SYS03-240

测试 MUST 覆盖：

- Workspace A evidence 不更新 Workspace B projection；
- independent vs assisted vs answer-exposed eligibility/weight；
- single immediate success 不直接 stable mastery；
- delayed/transfer evidence；
- answer-exposed success 不产生 independent mastery evidence；
- assisted success 不等于 validation complete；
- fresh independent Attempt 才能提供 independent validation evidence；
- low-confidence assessment conservative；
- duplicate evidence/event idempotency；
- invalidated/deleted evidence replay → current LearnerState reproject；
- projection store deleted → rebuild from durable evidence；
- learner dispute 不直接改概率；
- `learning_stage_summary` 不再作为 TeachingStage truth；
- MisconceptionEvidence→Hypothesis 需要 versioned inference；
- same workspace+evidence+algorithm replay deterministic；
- DKT/Deep KT challenger 无 canonical write；
- LLM/engagement/turn count/“我懂了”不能直接提升 mastery。

## 11. Acceptance Criteria

原有 AC：

- `SYS03-AC-001`：任一 MasteryEstimate 可列出 workspace、全部 source evidence ids 和算法版本。
- `SYS03-AC-002`：ASSISTED 与 INDEPENDENT success 产生不同 evidence eligibility/weight。
- `SYS03-AC-003`：ANSWER_EXPOSED success 不会产生 stable-mastery 高权独立证据。
- `SYS03-AC-004`：相同 Workspace + events/evidence + exact algorithm/config 重放得到相同状态内容。
- `SYS03-AC-005`：Assessment 模块不能直接写 mastery repository。
- `SYS03-AC-006`：用户状态争议可触发复测/重算并保留审计记录。
- `SYS03-AC-007`：DKT/Deep KT challenger 失败不影响 canonical baseline 可用性。

新增：

- `SYS03-AC-201`：LearnerState 没有 persistent SYS05 TeachingStage truth。
- `SYS03-AC-202`：ANSWER_EXPOSED result 无法成为 independent mastery evidence。
- `SYS03-AC-203`：SYS03 不能在 fresh independent Attempt 前假定 validation obligation 完成。
- `SYS03-AC-204`：MisconceptionHypothesis 与 SYS04 MisconceptionEvidence 可独立审计。
- `SYS03-AC-205`：LearnerState/MasteryEstimate 是 single-writer canonical rebuildable projection，而 LearningEvidence 是重建事实基础。
- `SYS03-AC-206`：删除影响当前状态的 evidence 后，旧 current projection 不继续生效。
- `SYS03-AC-207`：默认不存在 cross-workspace learner-state fusion。

## 12. Legacy Mapping

- `learning_stage_summary` → `learner_progress_summary` read migration；旧字段只作 legacy/audit。
- integer hint/scaffold/exposure → v0.3 orthogonal assistance snapshot；无法确定时标记 unavailable/uncertain。
- 历史 `user_id` → LocalOwner/Learner compatibility subject，MUST NOT 解释为 Account principal。
- 历史 learner records 缺 workspace 时，migration MUST 通过 Material/Goal/Session/owner refs 无歧义归属；无法确定则 fail closed，不得默认放入全局 Workspace。
- 历史 mastery 若依赖已失去版本的旧 weighting rule，replayability MUST 标记 partial/non-replayable。

Retirement condition：所有 active writers/readers 切至 v0.3 + workspace-scoped schema，旧记录已迁移或有明确 audit/replay status 后，legacy adapter SHOULD 删除。

## 13. Forbidden Implementations

禁止：

- `mastery = last_score`；
- 连续答对固定 N 次就无条件 stable mastery；
- LLM 输出 mastery_probability 直接入库；
- DKT/KT 各保存一套 canonical truth；
- 用户点赞/engagement/turn count/“我懂了”直接提高 mastery；
- replay 调用在线 LLM；
- SYS03 计算 next_due_at/LearningPlan/TeachingStage；
- answer-exposed correct 直接提升 stable mastery；
- `missing assistance = independent`；
- SYS03 预先完成 SYS05 validation obligation；
- LearnerState 成为不可由 evidence 重建的唯一事实；
- owner_id 代替 workspace_id 做 learner projection 隔离；
- evidence 被永久删除后通过旧 projection/replay 复活其影响。

## P1-01 Achievement Evidence Boundary

SYS03 只从 SYS04 `accepted` AssessmentResult 接纳 criterion evidence。`needs_review/scoring_failed`、低置信、grader disagreement、provider failure 或 Prompt Injection 风险不得形成 learner failure 或 achievement evidence。SYS03 不把 Goal state 写为 achieved。
