# EXEC-1061 — P1-06A Onboarding Readiness Foundation

> Status：FROZEN / ACTIVE
> Priority：P1 Reliable Private Product
> Governing：ADR-0106、`ONBOARD-*`、P1-06 Vertical Slice
> Decision authority：user-delegated Codex

## Objective

实现 presentation preference、existing-user backfill、SYS06 first completion projection 与 strict
journey query foundation；不提前实现 `/welcome` 产品页面。

## Dependencies

- UI-02C independent completion commit `44ed11a`；
- P1-02/P1-03/P1-07 可并行完成，但本 EXEC 只定义 ports/fixtures，不用 placeholder 冒充集成 DONE；
- shared dirty worktree 中 P1-04/P1-05 及其他任务修改必须保留并排除提交。

## Allowed Files

```text
docs/design/p1-06-fact-driven-first-use-journey.md
docs/adr/ADR-0106-fact-driven-onboarding-readiness-and-preferences.md
docs/adr/README.md
docs/document-inventory.md
docs/product-gap-register-p1-p2.md
docs/specs/README.md
docs/specs/architecture/state-ownership.md
docs/specs/architecture/dependency-rules.md
docs/specs/systems/06-activity-lifecycle.md
docs/specs/interfaces/onboarding-contract.md
docs/specs/interfaces/api-contract.md
docs/specs/interfaces/error-contract.md
docs/specs/interfaces/persistence-contract.md
docs/specs/interfaces/schema-versioning.md
docs/specs/quality/security-standard.md
docs/specs/quality/testing-standard.md
docs/specs/quality/definition-of-done.md
docs/specs/ui/data-contracts.md
docs/specs/vertical-slices/p1-06-first-use-onboarding.md
docs/exec-plans/README.md
docs/exec-plans/active/EXEC-1061-p1-06a-onboarding-readiness-foundation.md
docs/exec-plans/completed/EXEC-1061-p1-06a-onboarding-readiness-foundation.md
apps/backend/alembic/versions/<exec1061_onboarding_preferences>.py
apps/backend/app/api/v1/__init__.py
apps/backend/app/api/v1/onboarding.py
apps/backend/app/main.py
apps/backend/app/contracts/onboarding.py
apps/backend/app/models/__init__.py
apps/backend/app/models/onboarding.py
apps/backend/app/queries/onboarding.py
apps/backend/app/repositories/__init__.py
apps/backend/app/repositories/onboarding_preferences.py
apps/backend/app/services/onboarding.py
apps/backend/tests/architecture/test_onboarding_boundary.py
apps/backend/tests/contracts/test_onboarding_contract.py
apps/backend/tests/integration/test_onboarding_journey.py
apps/backend/tests/migrations/test_onboarding_preference_migration.py
apps/backend/tests/security/test_onboarding_security.py
```

## Forbidden Changes

- 持久化 step completion 或领域 ref；
- onboarding 直接写 model/document/goal/plan/activity/transcript/recovery truth；
- 从 message/time/model result 推断 completion；
- 依赖 localStorage、mock owner 或自由文本错误；
- 创建样例资料；
- 修改 P1-02/P1-03/P1-07 owner 实现；
- 混入 shared worktree 的其他任务文件。

## Tasks

1. 提交治理文件与精确索引 hunks。
2. 先写 contract/migration/query/security RED tests。
3. 实现 strict schemas、preference repository/service、idempotency/concurrency。
4. 实现 existing-user backfill/new-user default 与 SQLite/PostgreSQL migration checks。
5. 实现 SYS06 exact first-completion query port 与负面推断测试。
6. 实现 journey assembler、single action、partial/stale/error、current-user API。
7. 运行本 EXEC full applicable gates，归档并独立 commit。

## Acceptance Criteria

- `EXEC1061-AC-001`：`ONBOARD-001..034/050..051` 代码和测试可追踪。
- `EXEC1061-AC-002`：preference 仅含 presentation fields；backfill/new user/concurrency/restart 正确。
- `EXEC1061-AC-003`：first completion exact source，模型回复/message/time 等负面案例不能完成。
- `EXEC1061-AC-004`：journey source/ref/version、single action、ambiguity/partial/stale 稳定。
- `EXEC1061-AC-005`：auth/cross-user/no-store/secret/path/prompt/grader leakage 通过。
- `EXEC1061-AC-006`：migration upgrade/check/representative fixture 与 full applicable backend gates PASS。

## Required Tests

```bash
cd apps/backend
pytest tests/contracts/test_onboarding_contract.py tests/architecture/test_onboarding_boundary.py
pytest tests/integration/test_onboarding_journey.py tests/migrations/test_onboarding_preference_migration.py
pytest tests/security/test_onboarding_security.py
pytest
ruff check app tests
mypy app
alembic check

cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

## Completion Report

归档时记录 migration/backfill、preference owner、每步 source、completion negative evidence、测试、commit、
未完成依赖和 SPEC GAP。EXEC-1061 DONE 不得单独关闭 P1-06。
