# P1-05 Account Lifecycle Release Evidence

> 当前阶段：EXEC-034 DONE / EXEC-035 ACTIVE / EXEC-036 WAITING
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

## Remaining Before P1-05 DONE

- EXEC-035：离线恢复套件、单次使用、轮换、限流与不枚举恢复。
- EXEC-036：删除 preview/pending/cancel、owner erasure、reconciliation、tombstone、restore barrier。
- P1-05 最终真实浏览器、360px/200% zoom/keyboard、restart 与零残留总验收。
