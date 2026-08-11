# P1-07 Error Recovery Center Completion Report

> Date: 2026-08-09
> Status: DONE
> Scope: EXEC-037 / ADR-0012 / P107-AC-001..009
> Candidate branch: `codex/p1-07-recovery-center`

## 1. Final gate

```text
Engineering Gate: PASS
Policy / Ownership Gate: PASS
Security / Privacy Gate: PASS
Product Usability Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

P1-07 已关闭。该结论证明统一恢复控制面、owner command、故障隔离与真实本地恢复体验成立；
不证明真人学习效果得到改善，也不把 P1-02B 或 P1-03 各自更宽的独立产品门禁标为完成。

## 2. Delivered behavior

- `/settings/recovery` 汇总 provider、document、OCR、outbox 与 data recovery owner facts；全局
  indicator 只在 active/waiting issue 存在时显示；
- 每张卡固定表达发生了什么、数据是否安全、现在能做什么和重复副作用语义，技术详情只显示
  stable code、correlation 与 resource ref；
- `RecoveryIssueViewV1/RecoveryActionV1/RecoveryResultV1` 为单一 strict/versioned contract；
  command current-user scoped、expected-version、幂等、bounded 且 append-only audited；
- failed document 只创建带 `recovery_of` lineage 的 replacement task，原 DLQ、attempt 与历史不变；
  quarantine 只有 scanner policy 变更后才能复检，OCR 只导航 exact owner document/run；
- provider failure 在失败事务外记录；成功后 resolve。失败不创建 accepted transcript、Attempt、
  mastery、review failure 或 activity completion；
- Electron 在业务 API 不可用时投影 backend missing、database integrity、migration 与 readiness
  诊断，并提供 single-flight retry；
- model settings、data recovery 与 OCR review 均路由到真实 owner surface，不存在 disabled placeholder
  冒充集成完成。

## 3. Current automated evidence

| Gate | Result |
|---|---|
| backend full pytest | 467 passed, 3 skipped |
| backend Ruff `app tests alembic` | PASS |
| backend mypy `app` | PASS；187 source files，仅既有 untyped-body notes |
| SQLite fresh/representative migration + `alembic check` | PASS |
| PostgreSQL head + `alembic check` | PASS；No new upgrade operations detected |
| PostgreSQL lifecycle / decision-trace integration | 2 passed |
| concurrent duplicate activity start | deterministic PASS + 20/20 repeated PASS |
| frontend Vitest | 22 files / 85 tests PASS |
| Electron Node tests | 41 passed |
| frontend production build | PASS |
| npm audit high | PASS；0 vulnerabilities |
| current backend binary + macOS directory package | PASS |

裸跑 `alembic check` 会使用仓库默认的 `postgres` 账号；本机不存在该角色。门禁改用隔离真实
PostgreSQL URL 执行并通过。测试库随后删除。macOS 包因本机唯一 Apple Development 证书已过期，
没有有效 Developer ID，故只作为未签名本地验收包，不作为可分发签名证据。

## 4. Real browser and desktop evidence

### Runtime recovery

隔离 SQLite、真实 FastAPI 与 Vite 页面显示 provider timeout、document failed 与 exhausted outbox
三类问题。点击“重新处理”后：

- 原 task 保持 `dead_letter`、`attempt_count=5`；
- 只创建一条带原 issue lineage 的 replacement，最终 `completed`；
- issue indicator 从 3 收敛到 1，刷新与后端重启后保持一致；
- provider timeout 只提供等待与返回 exact canonical activity，不在导航时重放模型调用；
- 页面 360px 实测 `scrollWidth < innerWidth`，控制台 0 warning/error。

真实 provider 边界复用当前候选祖先的 UI-02B3 证据：Zhipu 成功 UI 调用、DeepSeek production
renderer 成功，以及 Zhipu 429 fail-closed。当前 packaged Settings 另以合成无效 Qwen key 发起实际
provider probe，得到 `MODEL_CREDENTIAL_REJECTED`；候选未保存、表单清空、vault 文件未创建。
这些证据证明 provider 连通/失败恢复，不是学习效果证据。

### Bootstrap and migration recovery

当前及前序本地包完成：

- 缺失 backend binary → `BOOTSTRAP_BACKEND_BINARY_MISSING`，无不可执行重试；
- corrupt active DB → `BOOTSTRAP_DATABASE_INTEGRITY_FAILED`，原 corrupt bytes 不变且不创建恢复点；
- representative old DB → verified PRE_MIGRATION/staging/activation/readiness，重复启动幂等；
- 当前候选 fresh create-all DB 二次启动 → `schema_before=null`、`schema_after=p103c5a0d003`、
  `DATA_MIGRATION_STAGED_AND_ACTIVATED`、`DATA_RESTORE_READINESS_CONFIRMED`，最终 report
  `COMPLETED` 且 activation journal 清除。

真实 Electron 还验证标准 Actual Size/Zoom In/Zoom Out 菜单；200% zoom 下导航响应式收起，
状态、错误码与 CTA 保持可读可操作，Tab/Enter 可触发“重新检查”。

## 5. Acceptance criteria

| AC | Result | Evidence |
|---|---|---|
| P107-AC-001 | PASS | RECOVERY-AC-001..007 contract/query/action/restart/security tests |
| P107-AC-002 | PASS | 六类 provider stable mapping；negative learning side-effect regressions |
| P107-AC-003 | PASS | failed/quarantine/missing/OCR/outbox owner-fact projections |
| P107-AC-004 | PASS | scope/version/idempotency/budget/audit/lineage tests |
| P107-AC-005 | PASS | real backend missing、corrupt DB、migration shell |
| P107-AC-006 | PASS | reload、backend/App restart、duplicate action/start replay |
| P107-AC-007 | PASS | real provider/document/bootstrap paths；P1-04 real OCR decoded preview evidence |
| P107-AC-008 | PASS | 360px、Electron 200%、keyboard/focus/live status |
| P107-AC-009 | PASS | gates separated；Learning Evidence remains insufficient |

Blocking SPEC GAP: none.

## 6. Dependency and repository boundary

P1-07 集成以下真实 owner capabilities，但不替它们声明独立 gap closure：

- UI-02C lifecycle：`0029270`，并发 duplicate receipt 回放由 `0c9ca28` 收敛；
- P1-02 model control：`d59837d`、`7795b27` 与 IPC sender 修复 `4ea3611`；
- P1-03 data control：`c1549db`、`27e74bf`、`3f7ee08` 与 consent migration `fb898e5`；
- P1-04 Library/OCR：`c368ad2`、`d735919`、`9198172`；
- P1-07 control plane：`c4a5928`、`354e895`，以及当前 release fixes。

实现位于独立 worktree `/Users/xike/Documents/Docs/Askora-p1-07`。原 Askora 工作区的并发、未提交
内容未被修改；本任务未 push。
