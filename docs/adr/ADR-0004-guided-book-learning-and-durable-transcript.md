# ADR-0004 — Guided Book Learning and Durable Transcript

Status: accepted
Date: 2026-08-08
Decision authority: user-delegated Codex
Authorized objective: 使 EPUB 上传到真实学习的产品流程达到 Apple 级清晰度、连续性与可信度
Affected specs: `SPEC-D04`、`SPEC-D05`、`SYS08`、`UI-02B2`

## Context

UI-02B1 已把单份资料接入 canonical Goal、诊断、计划与教学链，但仍把
`MapGoalToKnowledge`、`GeneratePrerequisiteDiagnosis`、`GenerateLearningPlan`、
`SelectNextLearningActivity` 暴露为用户按钮。用户必须理解内部系统步骤，刷新后教学消息也无法恢复，
而首轮教学必须先由用户自行组织问题。这些行为在工程上真实，但没有形成安静、连续、由系统带领的产品体验。

## Decision

1. 用户只负责不可替代的意图与证据动作：表达并确认学习目标、回答诊断、开始/继续一节课、提交真实学习回答。
2. readiness 已明确授权且不需要用户输入的 owner command，由 Book Learning application façade 每次最多推进一步；
   façade 只协调现有 SYS06/SYS04/SYS08 owner，不复制其算法或状态。
3. `GoalKnowledgeMapping.selected_target_ids` 的稳定排序正式具有 rank 语义；rank 1 是首轮 prerequisite diagnostic
   的 primary target。该选择由 SYS06 deterministic mapper 产生，不由 UI 或 SYS08 猜测。
4. SYS08 新增 append-only Book Learning transcript projection，按 current user + exact activity 保存已接受的教学回合。
   它可保存 learner-visible text、accepted reply、TeachingAction/EvidenceBundle refs 与安全渲染所需 payload，
   但不是 LearnerState、Assessment、Plan、TeachingAction 或消息之外的新学习 truth。
5. 第一轮 MAY 使用 `system_start` turn。它只触发已选 activity 的 canonical TeachingAction/EvidenceBundle/SYS08
   执行，不伪造 learner answer，也不产生 Assessment/Mastery evidence；客户端不得提供隐藏的 system-start 文本。
6. API 重试必须先按 idempotency key/session turn 读取已接受 transcript；不得重复模型调用、事件或 assistant completion。
7. UI 主层只显示学习者语言、一个当前主动作和可理解进度；readiness code、owner ref 与 trace 收入可展开的“技术详情”。

## Alternatives Considered

- 继续由前端展示全部 pipeline 按钮：拒绝，因为把系统实现模型转嫁给用户，且错误恢复路径分散。
- 让前端循环调用现有 endpoints 并自行挑选 multi-target：拒绝，因为 UI 会获得隐式业务选择权。
- 复用 legacy `DialogSession/DialogMessage` 作为 canonical transcript：拒绝，因为会模糊 compatibility dialog 与
  exact LearningActivity 的身份，并形成第二条默认教学主链。
- 自动连续执行所有命令直到教学：拒绝，因为单请求长事务难以恢复，也会跨越用户确认/诊断边界。
- 只存浏览器 local/session storage：拒绝，因为跨重启不可恢复，且客户端状态会冒充已接受 execution record。

## Ownership and Invariants

- SYS06 继续独占 Goal、mapping、diagnostic need、plan、activity 与 activity selection。
- SYS04 继续独占 Attempt/AssessmentResult；SYS03 继续独占 LearnerState/Mastery；SYS05 继续独占 TeachingAction。
- SYS08 transcript 仅记录已执行呈现，不得成为上述 owner 的输入替代品。
- EvidenceBundle 只向 UI 返回 `learner_visible` items；grader-only/internal-only 保持结构性隔离。
- Engineering/UI Contract PASS 不构成真人学习效果；Learning Evidence 继续为
  `LEARNING_EVIDENCE_INSUFFICIENT`，直至独立真人研究门禁满足。

## Migration / Rollback

- 新增 append-only transcript turn table；不回填或改写 legacy dialog history。
- Upgrade 创建表与 unique/index 约束；downgrade 可删除纯 projection 表，不改变 canonical learning facts。
- 已有 UI-02B1 客户端继续可发送 learner turn；新字段使用 additive default。
- 回滚 UI 后 transcript 数据可保留；旧客户端忽略新 query，不形成双写。

## Validation

- 自动推进只接受 allowlist command，且每次最多一步；user-input state fail closed。
- broad mapping 使用 SYS06 rank-1 primary target，固定输入可 replay。
- transcript current-user scope、append-only、idempotent retry、跨应用实例恢复与 SQLite/PostgreSQL migration 测试。
- `system_start` 不记录 learner answer/Assessment/Mastery evidence。
- 360px、键盘、reduced motion、loading/error、刷新恢复与 evidence disclosure 组件测试。

## Supersedes / Superseded By

本 ADR additive supersede UI-02B1 中“manual system buttons、single-target dead end、非 durable teaching display”的限制；
不修改 ADR-0001/0002/0003 或 Book-to-Learning 的状态所有权。
