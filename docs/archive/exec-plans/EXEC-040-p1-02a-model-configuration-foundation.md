# EXEC-040 — P1-02A Secure Model Configuration Foundation

> Status：DONE
> Priority：P1 Product Reliability
> Governing：ADR-0013、`MODEL-CONFIG-*`、P1-02 Vertical Slice
> Decision authority：user-delegated Codex
> Implementation commits：`0da63a7`、`7964ebd`、`d59837d`

## Objective

实现 P1-02 的安全基础：desktop encrypted vault、versioned IPC、真实 synthetic probe、exact runtime projection、atomic apply/clear 与 restart rollback；不先实现完整 Settings 视觉交付。

## Dependencies

- UI-02B2/UI-02B3 durable transcript + policy-bound real-model baseline：commit `773edb3`（集成等价提交 `6172928`）；
- legacy canonical owner compatibility stabilization：commit `3423687`（集成等价提交 `354e895`）；
- EXEC-030 保持独立，不与本 EXEC 共享产品文件。

## Allowed Files

```text
docs/archive/design/p1-02-model-settings.md
docs/archive/audits/product-gap-register-p1-p2.md
docs/architecture/decisions/ADR-0013-desktop-model-credential-and-activation.md
docs/architecture/README.md
docs/governance/document-inventory.md
docs/specs/** (P1-02 additive updates only)
docs/planning/README.md
docs/planning/execs/EXEC-040-p1-02a-model-configuration-foundation.md
docs/archive/exec-plans/EXEC-040-p1-02a-model-configuration-foundation.md
apps/backend/app/contracts/model_configuration.py
apps/backend/app/core/config.py
apps/backend/app/main.py
apps/backend/app/orchestration/model_configuration.py
apps/backend/app/services/llm/model_router.py
apps/backend/tests/contracts/test_model_configuration_contract.py
apps/backend/tests/integration/test_model_configuration_probe.py
apps/backend/tests/security/test_model_configuration_security.py
apps/frontend/electron/main.cjs
apps/frontend/electron/preload.cjs
apps/frontend/electron/model-settings.cjs
apps/frontend/electron/model-settings.test.cjs
apps/frontend/package.json
apps/frontend/package-lock.json
```

## Forbidden Changes

- 不建立数据库 credential table；
- 不返回或记录 secret/ciphertext/token；
- 不修改 SYS03～SYS07 truth；
- 不引入 keytar/cloud secret dependency；
- 不实现任意 base URL/custom provider；
- 不自动跨 provider fallback。

## Acceptance Results

- `EXEC040-AC-001..006`：strict profile/probe/error、safeStorage encrypted vault、atomic revision、DISABLED tombstone、sender-validated IPC、exact runtime route 与 rollback 均由自动化测试覆盖；
- `EXEC040-AC-007`：model configuration backend 30 tests、Electron 31 tests、frontend 73 tests、build、Ruff、Mypy、docs/diff gates PASS；同一 backend 产品基线全量 448 passed / 3 skipped；
- 真实 provider gate 已有 DeepSeek `deepseek-chat` controlled canonical inference PASS；Zhipu 当次 429 被稳定分类并 fail closed；packaged Settings/relaunch 属 EXEC-041，不由本 EXEC 单独宣称。

## Completion Boundary

```text
Engineering Gate: PASS
Security / Ownership Gate: PASS
P1-02 Product Gate: NOT YET CLOSED (EXEC-041)
Learning Evidence: LEARNING_EVIDENCE_INSUFFICIENT
```

未形成数据库 credential truth、明文 fallback、跨 provider silent failover 或 learner-state 副作用。EXEC-041 现在获准实现 Settings 与 packaged App 产品验收。
