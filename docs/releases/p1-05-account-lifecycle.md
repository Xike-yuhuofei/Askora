# P1-05 Account Lifecycle Release Evidence

> 当前阶段：EXEC-034～035 DONE / EXEC-036 ACTIVE
> P1-05 总状态：OPEN
> 证据日期：2026-08-09

## EXEC-034 Engineering

- 新密码 Argon2id 写入；历史 bcrypt 成功认证后同一 identity transaction rehash。
- durable `AuthSession` 与 token family 绑定 `sid/fam/cv/sv`；旧 token fail closed 要求重新登录。
- refresh compare-and-swap、并发/重放整族撤销、数据库 session limit、cross-user 不可枚举。
- 修改密码递增 credential version、撤销其他 sessions、轮换当前 family；Settings 可操作并可恢复失败。
- migration `f34a91b807d1` 已验证 SQLite upgrade/downgrade/forward-fix、Alembic drift check 与 PostgreSQL offline DDL。

当前机器证据：

```text
Identity backend targeted: 15 passed
Frontend full: 52 passed
Frontend build: PASS
npm audit high: 0 vulnerabilities
ruff app/tests: PASS
mypy app: PASS
SQLite alembic check: PASS
Backend full: 342 passed, 1 skipped, 2 failed
  - P1-05 introduced historical migration fixture: fixed and separately PASS
  - remaining failure: pre-existing Book Learning non-UUID fixture outside EXEC-034 scope
```

## Policy / Ownership

`AuthSession` 数据库是唯一 session truth。Redis/进程内 blacklist 不参与 EXEC-034 的认证放行、撤销、refresh single-use 或 session limit。Identity 不写 SYS01～SYS08 业务 truth。

## Learning Evidence

```text
LEARNING_EVIDENCE_INSUFFICIENT
```

本阶段只证明账号安全与工程行为，不能证明 Askora 改善真人学习效果。

## EXEC-035 Engineering

- 新注册与 recovery credential 原子创建；Settings 读取状态并通过 current password 创建/轮换，旧 credential 立即撤销。
- recovery 成功 consume 旧 credential、Argon2id 写新密码、递增 credential version、撤销全部 sessions、签发只显示一次的新 kit，并要求重新登录。
- 登录、current-password、recovery 采用数据库 durable 5 次失败/15 分钟冷却；SQLite/PostgreSQL 原子 upsert 覆盖并发失败，不丢计数。
- unknown login 执行 Argon2id dummy verify；unknown/existing recovery 执行同 credential lookup、keyed digest compare、稳定文案和 throttle path。
- `Retry-After` 由统一 AppError handler 透传；恢复 secret 不进入数据库明文、receipt、日志或前端普通 localStorage/user cache。
- migration `f35b91b807d2` 已验证 SQLite upgrade/downgrade/forward-fix/check 与 PostgreSQL offline DDL。

当前机器证据：

```text
Identity/recovery targeted backend: 19 passed
Frontend full: 57 passed
Frontend build: PASS
npm audit high: 0 vulnerabilities
ruff app/tests: PASS
mypy app: PASS
SQLite migration/check: PASS
PostgreSQL offline DDL: PASS
Backend full before final EXEC-035 commit: 353 passed, 1 skipped, 1 failed
  - remaining failure: pre-existing Book Learning legacy non-UUID fixture outside EXEC-035 scope
Real browser: registration v1 → rotate v2 → old kit invalid → recover v3 → old sessions revoked → new login
Browser console: 0 error / 0 warning
```

## EXEC-035 Policy / Ownership

Identity 是 recovery credential、credential version、认证限流与 session revoke 的唯一 writer。没有新增第二 identity/session truth，没有写入 SYS01～SYS08 业务状态，也没有引入短信、邮件、第三方身份服务或安全问题。

## EXEC-035 Learning Evidence

```text
LEARNING_EVIDENCE_INSUFFICIENT
```

本阶段只证明账号恢复的工程、安全和交互行为，不能证明 Askora 改善真人学习效果。

## Remaining Before P1-05 DONE

- EXEC-036：删除 preview/pending/cancel、owner erasure、reconciliation、tombstone、restore barrier。
- P1-05 最终真实浏览器、360px/200% zoom/keyboard、restart 与零残留总验收。
