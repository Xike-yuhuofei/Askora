# P1-02 — Secure Model Settings Vertical Slice

> 状态：FROZEN
> 日期：2026-08-09
> Governing：ADR-0013、`MODEL-CONFIG-*`
> Decision authority：user-delegated Codex

## 1. Objective

在 packaged macOS private App 中闭合：

```text
Settings → provider/model/Key → synthetic real probe
→ encrypted vault revision → backend restart/revision verify
→ canonical real-model learning → App relaunch recovery
```

失败路径必须保留旧配置并提供可行动错误；secret 不进入不允许的边界。

## 2. Scope

### Included

- `ModelRouteProfileV1`、desktop vault、narrow IPC；
- connection probe/local control auth；
- router exact active configuration；
- apply/clear/restart/rollback；
- Settings 完整状态与文案；
- provider/model catalog 仅覆盖已有 adapter；
- data/cost/fallback disclosure；
- automated + packaged macOS real provider E2E；
- release report、gap register DONE。

### Excluded

- arbitrary base URL/custom provider；
- embedding credential；
- provider billing/balance；
- multi-provider automatic failover；
- onboarding P1-06；
- backup/export P1-03；
- recovery center P1-07 umbrella；
- learning efficacy。

## 3. User Journey

1. 用户打开 Settings，看见当前来源/状态而不是泛化 `llm_ready`。
2. 选择已有 provider/model 组合，输入新 Key；旧 Key 永不回显。
3. UI 在提交前说明 fixed synthetic probe 与可能的极小费用。
4. 点击“验证并使用”；显示 VALIDATING/APPLYING。
5. probe 成功后 App 自动重启本地 backend，token/session 保持可用。
6. Settings 显示 provider/model/revision/verified_at/READY。
7. 用户启动真实 canonical learning，model metadata 与 active route 一致。
8. 退出并重开 App，配置仍可用。
9. 更新失败时 UI 明确旧配置已保留；清除后重启仍未配置。

## 4. Execution Split

```text
EXEC-040: contracts + vault + probe + activation/recovery foundation
→ independent commit/gate
EXEC-041: Settings UX + real acceptance + gap closure
→ independent commit/gate
```

EXEC-041 MUST NOT 在 EXEC-040 未 DONE 前实施。

## 5. Acceptance Criteria

- `P102-AC-001`：`MODEL-CONFIG-AC-001..009` 全部有当前证据。
- `P102-AC-002`：Settings 在 Electron 内完成 apply/update/reverify/clear，无 `.env` 编辑要求。
- `P102-AC-003`：401/403、model unavailable、429、timeout、5xx、storage、revision、apply/rollback 分支可区分。
- `P102-AC-004`：probe 不含私人资料；Key 不在 frontend persistence、普通 API、日志、Prompt、export。
- `P102-AC-005`：apply failure old revision remains usable；clear tombstone prevents environment resurrection。
- `P102-AC-011`：unreadable vault 只能经显式 recovery confirmation 重置为 DISABLED；普通 clear/revision 与 Keychain fail-closed 不被绕过。
- `P102-AC-012`：apply/clear/recovery 产生 sanitized local audit；audit/error/log 中无 secret/ciphertext/control token/raw provider body。
- `P102-AC-013`：每个 App process 使用独立且 restart-stable 的 loopback port；只有当前 backend start token 认证的私有 readiness 才能确认 child identity，其他 Askora `/ready` 不可误通过。
- `P102-AC-006`：当前 route 不 silent failover，不以 mock/local fallback 冒充 connected。
- `P102-AC-007`：1440/1024/768/360、200% zoom、keyboard、live status/error 通过。
- `P102-AC-008`：packaged macOS App 用真实 provider 完成 configure→learn→relaunch；provider availability 以本次执行为准。
- `P102-AC-009`：full applicable backend/frontend/electron/security/docs gates PASS。
- `P102-AC-010`：gap register 仅在 release report、两份 EXEC、独立 commits 和所有 AC 完成后标 `DONE`。

## 6. Claim Boundary

Engineering Gate、Security/Ownership Gate、Real Provider Product Gate 分开报告。Learning Evidence 保持 `LEARNING_EVIDENCE_INSUFFICIENT`。

## 7. Blocking Conditions

以下任一项阻断 DONE：明文 secret、无 sender validation、Mock-only、只测 API 不测 App、apply 无 rollback、clear 后 `.env` 复活、无真实 provider、错误显示成 learner failure、未知 schema 被猜测、未验证 restart/relaunch。
