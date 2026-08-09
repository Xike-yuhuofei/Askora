# EXEC-040 — P1-02A Secure Model Configuration Foundation

> Status：FROZEN / ACTIVE
> Priority：P1 Product Reliability
> Governing：ADR-0012、`MODEL-CONFIG-*`、P1-02 Vertical Slice
> Decision authority：user-delegated Codex

## Objective

实现 P1-02 的安全基础：desktop encrypted vault、versioned IPC、真实 synthetic probe、exact runtime projection、atomic apply/clear 与 restart rollback；不先实现完整 Settings 视觉交付。

## Dependencies

- UI-02B2/UI-02B3 durable transcript + policy-bound real-model baseline：commit `773edb3`；
- legacy canonical owner compatibility stabilization：commit `3423687`；
- EXEC-030 仍可保持独立，不与本 EXEC 共享产品文件。

## Allowed Files

```text
docs/design/p1-02-model-settings.md
docs/product-gap-register-p1-p2.md
docs/adr/ADR-0012-desktop-model-credential-and-activation.md
docs/adr/README.md
docs/document-inventory.md
docs/specs/README.md
docs/specs/architecture/state-ownership.md
docs/specs/architecture/system-architecture.md
docs/specs/architecture/dependency-rules.md
docs/specs/domain/lifecycle-state-machines.md
docs/specs/systems/08-ai-orchestration.md
docs/specs/systems/08-model-configuration.md
docs/specs/interfaces/api-contract.md
docs/specs/interfaces/error-contract.md
docs/specs/interfaces/schema-versioning.md
docs/specs/quality/security-standard.md
docs/specs/quality/observability-standard.md
docs/specs/quality/testing-standard.md
docs/specs/quality/definition-of-done.md
docs/specs/ui/screen-contracts.md
docs/specs/ui/data-contracts.md
docs/specs/ui/quality-and-migration.md
docs/specs/vertical-slices/p1-02-model-settings.md
docs/exec-plans/README.md
docs/exec-plans/active/EXEC-040-p1-02a-model-configuration-foundation.md
docs/exec-plans/completed/EXEC-040-p1-02a-model-configuration-foundation.md
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
- 不自动跨 provider fallback；
- 不修改 P1-03/P1-04/P1-05/P1-06/P1-07 文件。

## Tasks

1. 完成治理文件、索引与 architecture traceability。
2. 定义 strict profile/apply/clear/probe/result/error contracts。
3. refactor provider construction 支持 isolated explicit candidate，不修改 global settings。
4. 实现 local/private token-auth probe 与 sanitized error mapping。
5. 实现 async safeStorage vault、atomic revision、rotation、disabled tombstone。
6. 实现 narrow sender-validated IPC、backend environment projection、graceful restart/rollback。
7. 覆盖 contract/integration/security/node recovery tests。
8. 运行本 EXEC gates，归档并独立 commit。

## Acceptance Criteria

- `EXEC040-AC-001`：`MODEL-CONFIG-001..080/100` 代码和测试可追踪。
- `EXEC040-AC-002`：probe fail 无写入；apply restart fail exact rollback；clear writes DISABLED。
- `EXEC040-AC-003`：safeStorage unavailable/rotation/corrupt/atomic write 有测试，无 plaintext fallback。
- `EXEC040-AC-004`：IPC sender/schema/revision/secret boundaries 有 security tests。
- `EXEC040-AC-005`：所有 provider probe error 分类稳定；no raw error/secret echo。
- `EXEC040-AC-006`：runtime provider/model/revision 与 active vault exact 一致。
- `EXEC040-AC-007`：targeted/full applicable backend + electron tests、ruff、mypy、build、docs/diff gates 有当前结果。

## Required Tests

```bash
cd apps/backend
pytest tests/contracts/test_model_configuration_contract.py tests/integration/test_model_configuration_probe.py tests/security/test_model_configuration_security.py tests/unit/test_model_router.py
ruff check app tests
mypy app

cd apps/frontend
npm run test:electron
npm test -- --run
npm run build

cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

## Completion Report

归档时必须记录 config truth/source、secret boundary、probe matrix、rollback/clear/restart evidence、测试、commit、未完成项和 SPEC GAP。EXEC-040 DONE 不得单独关闭 P1-02。
