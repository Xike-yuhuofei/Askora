# UI-02B2 — Guided Book Learning

> 状态：**FROZEN / EXEC-026 DONE**
>
> 冻结日期：2026-08-08
>
> 决策权限：user-delegated Codex（ADR-0004）
>
> 上游：UI-02B1、SPEC-D04/D05、SYS08、ADR-0004

## 1. Objective

把已真实接通但偏工程化的 Book Learning launch 收敛为系统带领的连续体验：

```text
资料已准备 → 说出目标 → 确认系统理解 → 必要诊断
→ 系统自动准备计划与下一活动 → 一个动作开始课程
→ 可恢复的 canonical 教学记录 + 学习依据
```

## 2. Product Principles

- 一屏只有一个主要动作；不向学习者展示 pipeline command 名称。
- 目标确认和真实作答不能被自动化；纯系统准备步骤不要求用户点击。
- 默认给结论与下一步；owner refs、reason codes、schema/version 只在技术详情中出现。
- 进度文案使用“正在准备学习范围 / 正在安排第一节”等用户语言，不虚构百分比。
- 刷新、重启和网络重试必须回到已接受状态，不重复命令或教学回合。

## 3. Safe Auto-advance Contract

### UI02B2-010

`POST /api/v1/book-learning/{document_id}/advance` 每次 MUST：

1. current-user 查询 exact readiness；
2. 只接受以下单个 command：`MapGoalToKnowledge`、`BuildGoalKnowledgeSubgraph`、
   `GeneratePrerequisiteDiagnosis`、`GenerateLearningPlan`、`SelectNextLearningActivity`；
3. 调用对应 owner application command；
4. 同事务提交并返回新的 readiness。

`CreateLearningGoalCandidate`、`ConfirmLearningGoal`、`ContinuePrerequisiteDiagnosis`、
`StartCanonicalTeachingRound` MUST NOT 由该 endpoint 自动执行。非 allowlist state 返回 stable
`BOOK_LEARNING_USER_INPUT_REQUIRED`，不得猜测。

### UI02B2-011

UI 只在 readiness `next_commands` 恰好包含可自动推进 command 时调用 advance；每次响应后重新读取 readiness，
并使用 bounded loop（最多 6 步）。冲突/未知状态立即停止并显示可恢复错误。

### UI02B2-012

广义 Goal 的多个 `selected_target_ids` 不再是 UI 死路。SYS06 mapping 的顺序是稳定 rank；
rank 1 是 `primary_diagnostic_target_id`。所有 selected targets 仍进入 goal subgraph/plan，
首轮 diagnostic 只从 primary target 开始。UI/SYS08 不得重排。

## 4. Durable Teaching Transcript

### UI02B2-020

SYS08 MUST 按 current user + exact `LearningActivity` 提供：

`GET /api/v1/book-learning/activities/{activity_id}/transcript`

响应至少包含 `session_id`、`activity_ref`、ordered accepted turns、`next_turn_number`。
每个 turn 可含 learner message（`learner` turn）与必须含 assistant message、created time、
learner-visible evidence citations、TeachingAction/EvidenceBundle refs。

### UI02B2-021

accepted turn MUST append-only；unique `(session_id, turn_number)`、`idempotency_key`。
重复 start 请求返回已保存的 exact response，不重复调用模型、写事件或追加消息。

### UI02B2-022

`system_start` turn：

- 客户端只声明 kind，不传 system prompt/learner answer；
- 服务端使用 versioned bounded start intent；
- 不显示伪造的 learner 消息；
- 不创建 Attempt/AssessmentResult/Mastery evidence；
- 仍完整经过 SYS05/SYS02/SYS08 canonical path。

### UI02B2-023

Transcript 是 SYS08 execution/presentation projection，不是 activity completion、mastery、plan progression 或
dialog compatibility truth。删除/rebuild transcript 不得改变其他领域状态。

## 5. Learner-visible Evidence

- assistant turn 展示简短“依据资料”区域，来源由 exact `EvidenceBundle.items[].source_span_ids` 生成；
- 只允许 `allowed_use=learner_visible`；unknown/grader/internal 字段 fail closed；
- 资料不足时明确说明，不以模型常识伪装书中事实；
- 技术 ID 默认折叠，不进入回答正文。

## 6. Screen Contract

- Header：资料学习 + 当前用户目标；不显示 `UI-02B2` 或 canonical/SYS 编号。
- Progress：`目标`、`基础检查`、`本次学习` 三段，当前段清晰，非百分比。
- Goal：聚焦一个问题与可选“用于什么”；时间预算/日期收入“更多选项”。
- Preparation：自动推进时显示单一 status，禁止可重复点击的内部动作按钮。
- Diagnostic：一次一题，明确“这用于调整起点，不计分”。
- Ready：显示活动名称、目的、预计分钟数，一个“开始本次学习”按钮。
- Teaching：先由 Askora 发起；历史跨刷新恢复；composer 使用“写下你的想法或问题”。
- Error：说明发生什么、数据是否已保存、唯一可恢复动作；技术详情可展开。

## 7. Acceptance Criteria

- `UI02B2-AC-001`：Goal 确认后到 diagnostic/ready 之间没有手动 pipeline 按钮。
- `UI02B2-AC-002`：auto-advance allowlist、单步、bounded、idempotent，用户输入状态不被跨越。
- `UI02B2-AC-003`：multi-target mapping 使用 SYS06 persisted rank-1 primary target，不由 UI 选择。
- `UI02B2-AC-004`：开始课程后由 system_start 产生第一条 canonical assistant teaching turn。
- `UI02B2-AC-005`：刷新/重启恢复 exact session、turn order、reply 与 citations。
- `UI02B2-AC-006`：重复 teaching request 不重复模型执行、事件或 transcript。
- `UI02B2-AC-007`：grader/internal evidence 零泄漏；来源可映射 SourceSpan。
- `UI02B2-AC-008`：UI 不显示 readiness/SYS/canonical/schema 等内部术语作为主内容。
- `UI02B2-AC-009`：360px、键盘、focus、reduced motion、loading/error/live region 通过。
- `UI02B2-AC-010`：既有 UI-02B1 auth、ownership、Goal confirmation、diagnostic、Policy envelope 不回归。
- `UI02B2-AC-011`：migration SQLite/PostgreSQL compatible，upgrade/downgrade/empty/duplicate 通过。
- `UI02B2-AC-012`：Engineering/UI/Policy 与 Learning Evidence 分层报告。

## 8. Out of Scope

- 完整 Goals/Path/Evidence 顶层页面；
- activity completion 与下一活动推进语义；
- 笔记、书签、Focus 模式、复习编辑；
- 新教学策略、阈值、外部依赖或学习效果宣称。

## 9. Freeze Decision

`UI-02B2`：**FROZEN / EXEC-026 DONE**。实现不得用 transcript 推断 mastery/completion，
不得把自动推进扩展到任何需要用户确认或真实作答的 command。
