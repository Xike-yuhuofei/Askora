# UI-02C Canonical Activity Lifecycle Vertical Slice

> 状态：Frozen / BLOCKED_BY_DEPENDENCY
> 实现入口：EXEC-030
> 冻结日期：2026-08-09
> 用户授权：采纳产品完整性审计建议并继续执行
> 架构决定：ADR-0007

## 1. Objective

让用户从 Today/Path 可靠进入 exact LearningActivity，刷新或重启后恢复同一活动，显式完成后由 SYS06 推进下一项。全过程以 canonical lifecycle state 为准，不以对话存在、前端 local state 或模型成功冒充进度。

## 2. Dependency Gate

实现前 MUST 先把当前工作区已有的 durable activity transcript / policy-bound Book Learning baseline 作为独立已审查 commit 落地，或提供语义等价的冻结依赖。UI-02C 治理可以先冻结；依赖未提交前 EXEC-030 不得修改产品代码。

## 3. End-to-End Path

```text
Today / Path current activity
→ StartLearningActivityV1 (available → active)
→ /learn/{activity_id}
→ restore exact owner-scoped transcript/execution
→ learner explicit finish + accepted transcript ref
→ CompleteLearningActivityV1 (active → completed)
→ next planned activity becomes available atomically
→ Today / Path refresh canonical state
```

## 4. Scope

IN：

- lifecycle state migration/backfill/cutover；
- start、resume query、complete commands；
- SYS06 events/outbox/idempotency/concurrency；
- transcript-backed activity completion precondition；
- Today/Path CTA 与 `/learn/:activityId` stable route；
- next activity availability 与 terminal plan completion；
- SQLite/PostgreSQL、restart/replay、360px/desktop/browser E2E。

OUT：

- diagnostic/review/transfer evaluator completion；
- mastery、objective satisfaction、goal achievement；
- plan reordering/replanning；
- completion based on engagement、turn count、model confidence or time spent；
- external service/production dependency。

## 5. Product Semantics

- `available` 显示“开始学习”，`active` 显示“继续学习”，`completed` 只显示“已完成本项”；
- 完成按钮旁必须说明“完成本项不等于已掌握”；
- unsupported activity type 不显示可绕过的完成按钮，显示需要评估/复习结果；
- stale/version conflict 刷新最新状态，不盲重试；
- provider/transcript failure 保留 active 状态与已接纳历史，提供可重试错误；
- duplicate click/reload 不创建第二 transition 或跳过两项活动。

## 6. Acceptance Criteria

- `UI02C-AC-001`：Today/Path CTA 由 latest lifecycle state 驱动，未迁移/不可执行时 fail closed。
- `UI02C-AC-002`：start/complete current-user、strict v1、expected-version、idempotent；API transport-only。
- `UI02C-AC-003`：`/learn/:activityId` 可刷新/重启恢复 exact transcript，不创建第二 session truth。
- `UI02C-AC-004`：completion 与 next availability/outbox 原子；并发或重复请求只推进一次。
- `UI02C-AC-005`：completed 不改变 mastery/objective/goal/review，UI 不暗示掌握。
- `UI02C-AC-006`：evaluator-required activity 与缺 transcript fail closed。
- `UI02C-AC-007`：migration/backfill/reconciliation/forward-fix 在 SQLite/PostgreSQL 验证。
- `UI02C-AC-008`：desktop/360px、keyboard、loading/error/conflict/resume E2E 通过。
- `UI02C-AC-009`：Engineering 与 Policy/Ownership PASS；Learning Evidence 保持 `LEARNING_EVIDENCE_INSUFFICIENT`。

## 7. Gate

依赖未提交时状态为 `BLOCKED_BY_DEPENDENCY`，不是 `SPEC GAP`。只有依赖 commit 明确、`SYS06-ACT-AC-001..007` 与 `UI02C-AC-001..009` 全部满足后才能标 DONE。
