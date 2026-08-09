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
Real Browser Activity Lifecycle Gate: PASS (terminal-plan branch)
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
  一次，冲突事务通过新 snapshot 重放获胜 receipt；即使首次 receipt lookup 早于获胜事务提交，
  version mismatch 分支也会再次读取同一 digest 的 receipt，而不是误报状态冲突；
- completion、下一项 available、event 与 outbox 共享事务；失败回滚后可安全重试；
- completed 不写 mastery、objective、goal 或 review schedule。

## 3. 产品与真实浏览器验收

真实本地前后端和应用内浏览器完成：

```text
available v2 → start → active v3
刷新/重新登录 → 恢复 exact active activity
真实 provider timeout / 429 → 保持 active，未写 transcript 或 completion
canonical fixed-provider accepted transcript → complete → completed v4
terminal plan → plan completed；goal/mastery 不变
```

桌面 `1280px` 与 `360x800` viewport 均无横向溢出，窄屏导航正确收起，主 CTA 可见；
刷新后稳定恢复 v3，完成后刷新稳定恢复 v4，并明确说明不会自动更新掌握度或目标达成状态。
该隔离 fixture 只有一个活动，因此浏览器验证 terminal-plan 分支；下一项 `planned → available`
由 SQLite/PostgreSQL integration tests 验证，不把 terminal fixture 误报成浏览器 next-activity 证据。

浏览器验收中的 accepted transcript 由同一 canonical teaching facade 和固定 provider 创建，
不代表外部 provider 当次成功。真实配置 Zhipu 两次分别返回 ReadTimeout 与 429，均按合同
fail closed；本报告不把 fixed provider 或历史 DeepSeek 证据冒充本次外部连通性 PASS。

## 4. Verification Evidence

| Gate | 结果 |
|---|---|
| targeted lifecycle/backend suite | 12 passed, 1 skipped；PostgreSQL case 在无 URL 时 skip |
| concurrent duplicate start repetition | 5/5 passed；全量套件再通过 1 次 |
| backend full pytest | 379 passed, 3 skipped |
| Ruff `app tests` | PASS |
| mypy `app` | PASS；167 source files，仅既有 untyped-body notes |
| fresh SQLite migration/forward-fix | PASS |
| isolated PostgreSQL migration to lifecycle revision and current head | PASS |
| isolated PostgreSQL `alembic check` | PASS；No new upgrade operations detected |
| PostgreSQL state/event/outbox transaction case | PASS |
| frontend Vitest | 15 files / 57 tests PASS |
| frontend production build | PASS |
| `npm audit --audit-level=high` | PASS；0 vulnerabilities |
| real browser start / refresh / provider failure / complete / terminal plan | PASS |
| desktop 1280px + 360px responsive | PASS；无横向溢出 |
| `git diff --check` | PASS |

全量验证在共享工作区执行，但提交只暂存 EXEC-030 精确文件；P1-04/P1-05 未提交文件保持
未暂存。PostgreSQL 使用固定名称的隔离临时数据库，验证完成后已删除；合成资料目录已移入
macOS 废纸篓，可恢复。默认全量 pytest 因未设置 `ASKORA_POSTGRES_TEST_URL` 显示该 case
为 skip，但同一 case 已在隔离 PostgreSQL URL 下单独 PASS，不把 SQLite 结果冒充 PostgreSQL。

## 5. AC 与证据边界

`SYS06-ACT-AC-001..007`、`UI02C-AC-001..009` 与 `EXEC030-AC-001..007` 均有 contract、
architecture、integration、migration、recovery、frontend 和真实浏览器证据。Blocking SPEC GAP：
none。

本 Slice 证明 Engineering、Policy/Ownership、恢复与产品交互闭环，不证明真人学习效果；
Learning Evidence 继续为 `LEARNING_EVIDENCE_INSUFFICIENT`。
