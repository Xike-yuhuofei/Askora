# EXEC-047 — LocalOwner Foundation & Migration

> Status：FROZEN / ACTIVE  
> Governing：ADR-0015、`LID-*`、Local Single-User Authentication Removal Vertical Slice  
> Dependency：EXEC-1062 DONE（satisfied 2026-08-10）  
> Next：EXEC-048

## Objective

在不删除任何现有 auth runtime/schema 的前提下，建立唯一 durable `LocalOwner` truth、`LocalOwnerContext` 与 legacy single-learner migration，使后续 backend cutover 有稳定 ownership 基线。

## Dependencies

- EXEC-1062 DONE；
- ADR-0015 accepted；
- `LID-*` v2 FROZEN；
- 当前 DB migration heads clean；
- 工作树无未归属 identity migration。

`EXEC-1062` dependency 已由 completed archive + P1-06 release evidence 满足。执行开始时仍必须重新确认其余 runtime/migration 前置条件；若不满足，返回 `BLOCKED_BY_DEPENDENCY`。

## Required Specs

- `docs/design/features/Local-Single-User-Identity-Authentication-Removal-Canonical-Design-Delta.md`
- `docs/architecture/decisions/ADR-0015-local-single-user-identity-without-authentication.md`
- `docs/specs/platform/identity-privacy-lifecycle.md`
- `docs/specs/vertical-slices/local-single-user-authentication-removal.md`
- persistence / data-control / learner ownership相关 Specs

## Current Reality

- business API 仍通过 `get_current_user` + `User` 解析 owner；
- `users` 同时混合 credential 与 learner ownership；
- `canonical_user_id()` 已提供 legacy string→UUID compatibility projection；
- auth/session/recovery/account-deletion schema 尚存在。

## Allowed Files

```text
apps/backend/app/models/**
apps/backend/app/infrastructure/**
apps/backend/app/services/**local*identity*.py
apps/backend/app/services/auth/canonical_identity.py
apps/backend/app/core/database.py
apps/backend/alembic/versions/**
apps/backend/tests/**local*identity*
apps/backend/tests/**migration*
apps/backend/tests/conftest.py
docs/specs/vertical-slices/local-single-user-authentication-removal.md
docs/planning/**
```

若真实 repo 路径与上述 glob 不同，可在同一职责边界内使用等价文件；不得借机修改 frontend 或业务算法。

## Forbidden Changes

- 不停止注册 `/auth/*`；
- 不删除 JWT/session/recovery/account schema；
- 不改 Settings/Login；
- 不重命名全部 `user_id` 外键；
- 不修改 Teaching Policy / Learner Model / Assessment 算法；
- 不把 device fingerprint/machine id 当 LocalOwner。

## Implementation Tasks

1. inventory 所有真实 learner ownership subjects 与关键 owner references；
2. 建立 canonical `LocalOwner` persistence，cardinality=1；
3. 实现 atomic `ensure_local_owner()` / `get_local_owner_context()`；
4. 新空 datastore 自动创建 LocalOwner；
5. legacy datastore 若唯一真实 learner subject，复用稳定 UUID或明确 deterministic mapping；
6. multiple ambiguous real subjects 返回 `LOCAL_OWNER_AMBIGUOUS`，不做 destructive cleanup；
7. 为 owner mapping 建 migration/replay integrity tests；
8. 记录 compatibility boundary：旧 User MAY 暂时投影到 LocalOwner，但不得新建第二 identity truth。

## Acceptance Criteria

- `E047-AC-001`：空 DB 首次 bootstrap 原子产生且仅产生一个 LocalOwner；
- `E047-AC-002`：重复启动 owner_id 稳定；
- `E047-AC-003`：单 legacy learner 的 documents/goals/dialogs/learning/decision owner refs 可映射且数量不变；
- `E047-AC-004`：多真实 subject fixture fail closed=`LOCAL_OWNER_AMBIGUOUS`；
- `E047-AC-005`：migration 不读取/输出 password/token/recovery secret 作为 owner 选择依据；
- `E047-AC-006`：现有 auth flow 仍可运行，证明本 EXEC 只建立 foundation；
- `E047-AC-007`：无第二 canonical owner truth。

## Required Tests

- LocalOwner unit tests；
- migration upgrade test（empty + legacy single learner + ambiguous multi-subject）；
- owner reference integrity test；
- existing identity/auth smoke tests 保持通过；
- `ruff check` / `mypy app` 针对改动范围通过。

## Completion Report Format

报告必须包含：

- LocalOwner schema / owner resolution algorithm；
- legacy mapping evidence；
- ambiguous fixture evidence；
- migrations；
- tests；
- known compatibility residue；
- commit SHA；
- `E047 DONE` 或 blocking reason。
