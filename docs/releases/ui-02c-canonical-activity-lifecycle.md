# Askora UI-02C Canonical Activity Lifecycle Completion Report

> Status：DONE
>
> 日期：2026-08-09
>
> 实现合同：`EXEC-030` / `SYS06-ACT-AC-001..007` / `UI02C-AC-001..009`
>
> Governing decision：ADR-0007

## 1. Release 结论

```text
Engineering Gate: PASS
Policy / Ownership / Security Gate: PASS
Real Browser Activity Lifecycle Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
Candidate Migration Head: e30c06a1b2c3
```

UI-02C 已将 LearningActivity 的 current status 从 plan payload / `ActivitySelected`
event 推断切换为 SYS06-owned append-only `LearningActivityStateV1`。Today、Path 与
`/learn/:activityId` 现在围绕 exact activity 执行 available→active→completed，完成时在
同一事务发布 event/outbox 并推进下一项 available；transcript、UI 和模型输出均不是
completion truth。

依赖基线：

- `0f4ebb6`：decision trace input version persistence；
- `6172928`：durable transcript / policy-bound Book Learning baseline；
- `ddfdb97`：legacy local user 到 canonical owner 的兼容修复。

## 2. Lifecycle、迁移与恢复

- migration `e30c06a1b2c3` 新增 lifecycle version stream 与 owner-scoped command receipt；
- backfill 只接受 owner-valid completion event、accepted owner transcript 或明确 selection；
  transcript 最多推导 active，绝不单独推导 completed；
- query 在 lifecycle 未迁移时返回 `LEGACY_ACTIVITY_STATE_UNMIGRATED`，不回退到 payload 或
  event recency；
- start / complete 使用 expected version 与 idempotency receipt；并发 duplicate start 只推进
  一次，冲突事务通过新 snapshot 重放获胜 receipt；
- completion、下一项 available、event 与 outbox 共享事务；失败回滚后可安全重试；
- completed 不写 mastery、objective、goal 或 review schedule。

## 3. 产品与真实浏览器验收

真实本地前后端和应用内浏览器完成：

```text
available v1 → start → active v2
刷新 → 恢复 exact active activity
accepted transcript fixture → complete → completed v3
进入下一项 → next activity available v2
```

桌面与 `360x800` viewport 均可操作，窄屏导航正确收起，主 CTA 可见，浏览器 console 无
error/warning。首次 completion 后浏览器发现 completed transcript 读取被错误拒绝；修复后
completed 页面稳定展示“本项已完成”，并明确说明不会自动更新掌握度或目标达成状态。

浏览器验收中的 accepted transcript 是本地验收 fixture，不代表当次浏览器又调用一次外部
模型。真实 production renderer 依赖已由 DeepSeek `deepseek-chat`、
`v03-policy-bound-real-render/1.0` 单独通过；一次 Zhipu 429 按合同 fail closed。

## 4. Verification Evidence

| Gate | 结果 |
|---|---|
| targeted lifecycle/backend suite | 15 passed, 1 skipped |
| concurrent duplicate start repetition | 10/10 passed |
| isolated backend full pytest | 362 passed, 3 skipped |
| isolated Ruff `app tests` | PASS |
| isolated mypy `app` | PASS；164 source files，仅既有 untyped-body notes |
| fresh SQLite migration | `e30c06a1b2c3 (head)` |
| isolated `alembic check` | PASS；No new upgrade operations detected |
| isolated frontend Vitest | 15 files / 55 tests PASS |
| isolated frontend production build | PASS |
| isolated `npm audit --audit-level=high` | PASS；0 vulnerabilities |
| real browser start / refresh / complete / next | PASS |
| desktop + 360px responsive / console | PASS / no errors or warnings |
| `git diff --check` | PASS |

全量验证在 detached 临时 worktree 中只应用 UI-02C 精确候选补丁，未混入共享工作区中的
P1-04/P1-05 未提交文件。PostgreSQL 原子性测试保留为配置 `POSTGRES_TEST_URL` 时执行的门禁；
本次无该测试 URL，因此显示为 skip，不把 SQLite 结果冒充 PostgreSQL 当前运行证据。

## 5. AC 与证据边界

`SYS06-ACT-AC-001..007`、`UI02C-AC-001..009` 与 `EXEC030-AC-001..007` 均有 contract、
architecture、integration、migration、recovery、frontend 和真实浏览器证据。Blocking SPEC GAP：
none。

本 Slice 证明 Engineering、Policy/Ownership、恢复与产品交互闭环，不证明真人学习效果；
Learning Evidence 继续为 `LEARNING_EVIDENCE_INSUFFICIENT`。
