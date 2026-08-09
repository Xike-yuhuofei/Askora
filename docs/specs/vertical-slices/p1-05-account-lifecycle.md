# P1-05 Account Lifecycle Vertical Slice

> Status：FROZEN
> Governing decision：ADR-0009 + ADR-0107
> Governing spec：`IDP-*`
> Product target：真正关闭 P1-05 账号生命周期

## 1. Journey

```text
register → save one-time recovery kit → login
→ change password → old sessions revoked/current family rotated
→ view/revoke App sessions
→ recover password with offline kit → all sessions revoked/new kit issued
→ preview account deletion → re-auth + typed confirmation
→ pending/cancel OR durable purge
→ P1-03 ALL_PERSONAL_DATA workflow/receipt/checkpoint + zero-residual reconciliation
→ PII/credential cleared + tombstone/restore barrier
```

## 2. Scope

- strict v1 identity/session/recovery/deletion contracts and stable errors；
- durable SQLite/PostgreSQL auth sessions and refresh-family rotation；
- Argon2id new writes + bcrypt read/rehash migration；
- `/settings` password、recovery、sessions、data/deletion UI；
- Login registration recovery-kit result and offline password recovery；
- deletion preview、pending/cancel、P1-03 canonical owner erasure、reconciliation、tombstone projection、restore barrier；
- automatic resume after backend restart；
- real browser and database/file acceptance。

## 3. Out of Scope

- SMS/email/social login/MFA/passkey；
- public SaaS tenant administration；
- complete P1-03 backup/export UI；
- deleting global deployment model keys unless a future user-scoped secret contract marks them as owned；
- changing learning truth or teaching policy；
- claiming learning efficacy。

## 4. Dependencies and Cutover

EXEC-034 may proceed while EXEC-030 remains dependency-blocked because the user explicitly reprioritized P1-05 and the allowed files do not overlap activity lifecycle product files. EXEC-035 depends on EXEC-034 DONE；EXEC-036 originally supplied an account-deletion erasure foundation before P1-03 landed。ADR-0107 + EXEC-037 supersede that execution ownership：P1-05 preserves account orchestration and MUST call the completed P1-03 `ALL_PERSONAL_DATA` workflow without retaining a second owner receipt stream。

Existing pre-`sid` refresh tokens are rejected after cutover and the UI returns to login. This is an intentional security migration, not a permanent compatibility path。

## 5. Product Copy Invariants

- “退出当前 App”只撤销当前 session，不删除学习数据；
- “删除全部学习数据”保留账号；若该 command 尚未完整开放，UI 只能标为 P1-03 尚未完成，不得伪造；
- “删除账号”包含学习数据与身份清除；
- pending 可取消，purging 不可取消；
- 本地 App 关闭会延后本地 worker 执行，重启后自动继续；
- restore barrier 能防止 App 管理的旧快照静默恢复，但不能控制用户手工替换整个 App 数据目录。

## 6. Acceptance Criteria

- `P105-AC-001`：`IDP-AC-001..012` 全部满足。
- `P105-AC-002`：Settings 四区和 Login recovery journey 在 360px/desktop、keyboard、200% zoom 可完成。
- `P105-AC-003`：logout/revoke/password/recovery/delete 的 UI 文案、API effect 和 durable state 完全一致。
- `P105-AC-004`：SQLite、PostgreSQL、Redis-unavailable、restart、concurrent refresh/deletion 全部有自动化证据。
- `P105-AC-005`：代表性 fixture 覆盖 SYS01～SYS08、legacy dialog/profile、P1-04/P1-06/activity/auth、文件与未提交 outbox；P1-03 canonical receipt/checkpoint 存在且删除后其他用户/全局 policy 保留。
- `P105-AC-006`：真实浏览器执行 change-password → re-login → recovery → re-login → delete preview/request/purge；刷新/重启状态一致。
- `P105-AC-007`：P1-05 gap register 标 `DONE` 只发生在三份 EXEC、release report、full gates 和 reconciliation 全部通过后。
- `P105-AC-008`：Engineering、Policy/Ownership PASS 单独报告；Learning Evidence 保持 `NOT_APPLICABLE_TO_ACCOUNT_LIFECYCLE`，不改写整体学习证据状态。

## 7. Release Gate

任何 placeholder、只清 localStorage、只软删 User、仅 Mock 删除、未测试 restore barrier、未覆盖其他用户保护或未完成真实页面验收都会阻断 P1-05 DONE。
