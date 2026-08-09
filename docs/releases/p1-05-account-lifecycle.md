# P1-05 Account Lifecycle Release Evidence

> 最终状态：DONE
> 执行范围：EXEC-034～037
> 证据日期：2026-08-09

## 结论

```text
Engineering Gate: PASS
Policy / Ownership Gate: PASS
Learning Evidence: NOT_APPLICABLE_TO_ACCOUNT_LIFECYCLE
Blocking SPEC GAP: NONE
```

本报告只证明账号生命周期的工程、安全、所有权与交互合同，不证明 Askora 改善真人学习效果；项目整体学习证据状态不因此改变。

## Engineering

### EXEC-034 — Credential 与 durable session

- 新密码写入 Argon2id；历史 bcrypt 只在成功认证后 rehash。
- 数据库 `AuthSession` 是 session/token-family 唯一 truth；token 绑定 `sid/fam/cv/sv`。
- refresh single-use、并发/重放整族撤销、数据库 session limit、修改密码后的 credential version 与 session rotation 已覆盖。

### EXEC-035 — 本地恢复套件

- 注册、设置轮换和恢复都使用一次性离线 recovery credential；明文只显示一次。
- recovery 成功后 consume 旧 credential、写入 Argon2id 新密码、递增 credential version、撤销全部 session 并签发新 kit。
- login/current-password/recovery 使用 durable throttle；unknown/existing 路径不枚举账号。

### EXEC-036 — 删除、清除与恢复屏障

- strict v1 preview/request/status/cancel/retry API；request 固定 preview digest、重新认证、精确确认短语与幂等键。
- `deletion_pending` 立即冻结普通认证并保留独立 deletion-control；pending 可取消，purging 后不可取消。
- 显式 subject registry 分类所有当前表；迭代 manifest 覆盖直接 owner、引用链、JSON payload、文件、outbox 和 projection，未知表或跨用户歧义 fail closed。
- owner erasure 按冻结顺序执行：

```text
IDENTITY_FREEZE → SYS08_TASKS → SYS01 → SYS02 → SYS03 → SYS04
→ SYS05 → SYS06 → SYS07 → SYS08_LEDGER → PROJECTIONS → IDENTITY_FINALIZE
```

- bounded retry、blocked 状态和显式 retry 从 durable workflow/step/receipt/checkpoint 恢复；进程重启自动继续 pending/purging。
- reconciliation 非零不得完成；最终清除 identity PII、credential、session、recovery、业务数据、文件、任务与缓存，并保留最小无 PII tombstone。
- Redis 可用时按冻结 manifest 立即清除；Redis 不可用时，外部 restore barrier 保存不可逆 HMAC cache scope，后续启动先于模型/文档 worker 清理恢复出的缓存。
- 旧数据库快照命中外部 barrier 后，在业务 worker 启动前重新清除；已删除账号不能登录或继续处理旧任务。
- Settings 提供修改密码、会话、恢复套件与删除账号四区；删除状态在刷新和后端重启后保持，用户显式完成后才清除本地 deletion-control。

### EXEC-037 — P1-05 与 P1-03 擦除事实源收敛

- ADR-0107 接受单一事实源：P1-03 `DataErasureWorkflowV1` 及其 step、receipt、checkpoint 是唯一擦除执行 truth。
- P1-05 只拥有 preview、重新认证、24 小时宽限、取消、session 撤销与 deletion-control token；到期后通过受限内部桥调用固定 `ALL_PERSONAL_DATA`，不保留第二套 owner receipt。
- P1-05 request 仅保存 canonical workflow/receipt/checkpoint 引用、恢复屏障摘要和最小 tombstone 投影；通用数据控制 API 禁止直接请求 `ALL_PERSONAL_DATA`。
- exhaustive subject manifest 继续由 P1-05 提供给 canonical coordinator；未知表、未分类 owner、跨用户歧义与 reconciliation 非零均 fail closed。
- SQLite 在验证后的 `POST_ERASURE` 恢复基线完成前保持 `PURGING`；PostgreSQL/非桌面环境必须由显式运维防复活屏障完成 canonical workflow。
- P1-03/P1-05 migration heads 已合并为单一 `f36c91b807d3` head；已移除 P1-05 legacy owner receipt 表与模型。

## P1-05 Acceptance Matrix

| AC | 结果 | 当前证据 |
|---|---|---|
| P105-AC-001 | PASS | `IDP-AC-001..012` 的 session、recovery、删除、跨用户、重启、tombstone 与 UI 测试全部通过 |
| P105-AC-002 | PASS | 360×800 无横向溢出；200% 缩放后结构与控件保留；关键输入、checkbox、tab、button 使用原生语义并在真实浏览器可聚焦 |
| P105-AC-003 | PASS | logout/revoke/password/recovery/delete 分离，API effect、文案与 durable lifecycle 一致 |
| P105-AC-004 | PASS | SQLite、真实 PostgreSQL、Redis-unavailable、restart、concurrent refresh/delete 与 P1-03 canonical bridge 均有自动化或真实运行证据 |
| P105-AC-005 | PASS | all-table representative fixture 通过 P1-03 canonical workflow 覆盖 SYS01～SYS08、legacy、文件、outbox/projection；其他用户与 global policy 保留 |
| P105-AC-006 | PASS | 真实浏览器完成 change-password → re-login → recovery → re-login → preview/request/purge；刷新与后端重启仍为 deleted |
| P105-AC-007 | PASS | EXEC-034～036 独立提交；EXEC-037 在 ADR/Spec/EXEC 冻结后完成 P1-03 集成；full gates、release report 与 reconciliation 通过后才将 register 标 DONE |
| P105-AC-008 | PASS | Engineering 与 Policy/Ownership 分开 PASS；Learning Evidence 为 `NOT_APPLICABLE_TO_ACCOUNT_LIFECYCLE` |

键盘证据边界：真实浏览器确认关键原生控件的语义与焦点可达；浏览器自动化层的按键注入未产生可计入的激活事件，因此未把该次注入单独宣称为端到端键盘操作证据。原生控件、焦点状态和自动化交互共同构成当前 accessibility gate；未发现产品侧阻断。

## 验证证据

```text
EXEC-037 targeted integration pack: 25 passed, 1 PostgreSQL env-gated skipped
Backend full: 474 passed, 5 skipped
ruff app/tests: PASS
mypy app: PASS
Black baseline: PASS
Alembic heads: f36c91b807d3 (single head)
Fresh SQLite upgrade head + alembic check: PASS
PostgreSQL full alembic upgrade head + check: PASS
PostgreSQL representative deletion fixture: 1 passed
Frontend full: 78 passed
Frontend build: PASS
npm audit --audit-level=high: 0 vulnerabilities
Documentation check: 174 files / 0 broken local links
Real browser console: 0 error / 0 warning
360x800: innerWidth 360 / scrollWidth 360
Redis unavailable startup/deletion journey: PASS
Old snapshot + retained restore barrier + backend restart: PASS
```

普通全量测试中的 5 个 skip 包含需要显式 real-model 凭据的学习 eval，以及需要隔离 PostgreSQL URL 的迁移、事务和删除夹具；P1-05/P1-03 当前代表性删除夹具已使用真实临时 PostgreSQL 数据库单独通过。真实模型门控与账号生命周期无关，不能作为本项学习效果证据。

## Policy / Ownership

- Platform Identity 唯一写入 credential、credential version、AuthSession 与 RecoveryCredential。
- Platform Privacy 只写 deletion request、frozen manifest、canonical erasure 引用、tombstone 与 restore barrier，不成为第九学习系统。
- P1-03 Data Control 是 erasure workflow、step、receipt 与 checkpoint 的唯一 owner；P1-05 不再维护平行 receipt。
- SYS01～SYS08 只通过显式注册的删除计划履行其删除责任；canonical coordinator 没有普通 cross-owner write API。
- Redis、前端 storage、tombstone 和 restore barrier 均不是 identity/session/learning truth。
- 未新增短信、邮件、第三方身份服务、生产依赖或永久双写。

## Learning Evidence

```text
NOT_APPLICABLE_TO_ACCOUNT_LIFECYCLE
```

本项不改变项目整体的 `LEARNING_EVIDENCE_INSUFFICIENT` 结论。

## 未完成项与 SPEC GAP

- P1-05 产品范围内未完成项：无；EXEC-037 在 PR CI 通过前保持 active，作为发布流程状态而非产品缺口。
- Blocking SPEC GAP：无。
- `codex/p1-05-account-lifecycle` 已建立 PR #5；EXEC-034～036 保留独立提交边界，EXEC-037 以合并提交吸收当前 `main` 的 P1-03 migration graph 并完成擦除事实源收敛。
