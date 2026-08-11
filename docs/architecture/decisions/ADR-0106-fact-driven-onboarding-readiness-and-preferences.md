# ADR-0106 — Fact-driven Onboarding Readiness and Presentation Preferences

> Status: accepted
> Date: 2026-08-09
> Decision authority: user-delegated Codex
> Authorized objective: 真正关闭 P1-06 首次使用引导并通过相关测试
> IA amendment: ADR-0022 supersedes `/today` as a default entry；onboarding completion now returns through Course-centric startup resolution

## Context

Askora 已有资料、Goal、Plan、真实模型和 canonical activity lifecycle，但首次用户需要自行发现
这些入口。一次性 frontend wizard 会复制状态、在刷新后失真，并可能把“看到模型回复”误写成
完成学习；中央 onboarding service 若直接写多个 owner，又会形成第九个业务 truth。

P1-06 还依赖正在独立交付的 P1-02 模型配置、P1-03 数据控制和 P1-07 恢复动作。Onboarding 必须
消费它们的稳定查询/动作，而不是复制其 secret、路径、错误或写入逻辑。

## Decision

1. 采用事实驱动、可恢复的 journey，不采用一次性前端勾选 wizard。
2. `Platform Experience Preference` 唯一拥有 presentation-only `OnboardingPreferenceV1`；该记录只
   保存 active/dismissed、boundary notice version 和 dismiss metadata，不保存步骤完成或领域 ref。
3. `OnboardingJourneyViewV1` 是 current-user read projection。assembler 只能读取 owner query ports，
   每个步骤保留 availability/source/version，不取得业务写入权。
4. 第一节完成只由 SYS06 `FirstActivityCompletionProjectionV1` 返回 exact completed activity state 和
   accepted transcript source ref；不从消息、时间、模型结果或 UI action 推断。
5. 一个 response 只返回一个 server-selected `next_action`。存在多个合理业务对象时返回选择页面，
   不按时间或数组顺序隐式选择。
6. `/welcome` 受保护；只有默认 `/` 入口可在 active+incomplete 时重定向。`/today`、`/learning`
   作为 legacy aliases 先按 ADR-0022 做无副作用兼容解析，再应用同一 onboarding guard；所有明确
   Course / Activity deep link 保持原目标。
7. dismiss 只改变展示偏好；reopen 从 Settings 发起；finish 必须在同一 command 内重查 current
   completion 后才能 dismiss。
8. 迁移时现有用户 backfill 为 dismissed，不猜测历史完成；迁移后新用户默认 active。
9. P1-07 提供 recovery action；P1-06 不基于自由文本或 HTTP status 自定义修复。P1-03 只提供数据
   控制入口/能力，不向 onboarding 暴露绝对路径。
10. v1 明确不提供样例资料，直到来源、license、checksum、copy/delete 合同独立冻结。

## Alternatives Considered

### 一次性全屏 Wizard + localStorage 勾选

拒绝。它不能证明模型验证、资料 owner state、Goal、activity completion，也无法安全处理删除、回退、
换用户和重启。

### 只增强各页面空态

拒绝作为 P1-06 完成方案。它没有跨页面 resume、single next action、首次完成投影和统一信任说明。
页面空态可作为后续补充。

### 新建中央 OnboardingProgress 领域表保存每步完成

拒绝。它会复制模型、资料、Goal、Activity 和 transcript truth，并要求长期 reconciliation。

### 自动创建样例资料和目标

拒绝 v1。当前没有冻结样例来源、许可、用户副本、删除与长期标记合同，自动创建也违背默认使用
用户私人资料的产品选择。

## Ownership and Invariants

- Platform Experience Preference 只写展示偏好；SYS01～SYS08 继续拥有全部业务事实。
- read-model assembler、API handler、React store、router 和 localStorage 均不是 owner。
- `COMPLETE` 可随 current owner facts 回退；dismissed 不等于 complete。
- system/provider failure 不等于 learner failure；onboarding 不写 Assessment、Mastery、Review 或
  Activity completion。
- no secret、credential fragment、Prompt、grader-only data、raw provider body 或绝对路径进入 view、
  preference、日志或普通错误详情。

## Migration / Rollback

- additive 创建 `onboarding_preferences`，唯一键 `(user_id, journey_id)`，optimistic version 与
  idempotency receipt；SQLite/PostgreSQL 语义一致。
- migration transaction 内将现有用户 backfill 为 dismissed/legacy-existing-user；不写领域表。
- migration 后无 row 的用户首次查询创建 active v1；并发创建以唯一约束 fetch-existing。
- rollback 可停止路由和 API，并保留无害的 preference rows；不得删除或回写领域事实。数据库优先
  forward-fix。
- P1-02/P1-07 的 ADR 编号冲突必须在依赖集成时重编号/协调；P1-06 使用独立 ADR-0106，不引用冲突
  编号作为唯一语义标识。

## Security and Privacy Consequences

- view 为 current-user、`private, no-store`；cross-user resource 不可枚举。
- boundary acknowledgment 记录 notice version，只证明展示确认，不证明合规理解或外部 provider 安全。
- preference 随 ALL_PERSONAL_DATA 删除，并可在 PROFILE 导出中以非敏感 presentation preference
  表示；不进入 recovery secret 或模型 Prompt。

## Validation

- strict schema、unknown major/field、source/version、single next action；
- SQLite/PostgreSQL migration、backfill、新用户、concurrent create/update、idempotency/restart；
- owner query partial/stale/ambiguous、配置/资料/Goal/activity 回退；
- SYS06 exact completion + accepted transcript，负面测试覆盖模型回复/消息/时间不能完成；
- auth/cross-user/cache/secret/path/prompt/grader leakage；
- default route、deep link、refresh/relogin/App restart、dismiss/reopen；
- 360/768/1024/1440、200% zoom、keyboard/focus/live region；
- deterministic E2E、真实 provider 主路径与无内部知识首次用户体验；
- Engineering、Security/Privacy、Product Usability、Learning Evidence 分开报告。

## Supersedes / Superseded By

本 ADR additive 建立 P1-06 presentation/read-model 边界，不改变 P1-02、P1-03、P1-07 或 SYS01～SYS08
的 owner、command、错误和生命周期语义。ADR-0022 仅 supersede 本 ADR 中 `/today` 作为默认入口的
route mental model；事实驱动 readiness、presentation preference、deep-link preservation 与 owner
边界继续有效。
