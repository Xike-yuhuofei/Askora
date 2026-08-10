# P1-05 Account Lifecycle Vertical Slice

> Status：SUPERSEDED / HISTORICAL IMPLEMENTED BASELINE  
> Superseded by：ADR-0015 + `docs/specs/platform/identity-privacy-lifecycle.md` v2.0 (`LID-*`)  
> Historical governing decisions：ADR-0009 + ADR-0107

## 1. Historical Purpose

P1-05 曾实现以下本地账号闭环：

```text
register → login → password/session management → recovery kit
→ account deletion preview/pending/purge
```

该闭环已经完成过工程实现与验收，但其产品前提已被 Askora 的 local single-user 定位正式 supersede。

## 2. Current Authority

从 ADR-0015 起，P1-05 **不得再作为当前实现合同**。

当前身份合同唯一入口：

- `docs/design/Local-Single-User-Identity-Authentication-Removal-Canonical-Design-Delta.md`
- `docs/adr/ADR-0015-local-single-user-identity-without-authentication.md`
- `docs/specs/platform/identity-privacy-lifecycle.md` v2.0

## 3. Retired Product Semantics

以下能力必须退役：

- register/login/logout；
- password/change-password/recover-password；
- JWT access/refresh token；
- durable auth session；
- recovery kit；
- account deletion lifecycle；
- Login/Settings 中所有账号安全 UI。

## 4. Preserved Semantics

P1-05 历史实现中如果存在下列可复用原则，只能通过当前 `LID-*` / P1-03 合同继续使用：

- destructive action preview；
- idempotency；
- durable erasure receipt/checkpoint；
- owner-safe data erasure；
- no-resurrection safety。

它们不再属于 Account Lifecycle。

## 5. Migration Rule

Codex MUST NOT 通过重新启用 P1-05 的旧 auth/session/recovery code 来解决兼容问题。

旧实现仅作为 migration/history reference。当前实现必须 forward-migrate 到 LocalOwnerContext，并按 `LID-*` acceptance criteria 验收。
