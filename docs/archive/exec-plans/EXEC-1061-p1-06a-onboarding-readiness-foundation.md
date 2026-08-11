# EXEC-1061 — P1-06A Onboarding Readiness Foundation

> Status：DONE（2026-08-09）
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
docs/design/features/p1-06-fact-driven-first-use-journey.md
docs/architecture/decisions/ADR-0106-fact-driven-onboarding-readiness-and-preferences.md
docs/architecture/README.md
docs/governance/document-inventory.md
docs/archive/audits/product-gap-register-p1-p2.md
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
docs/specs/frontend/ui-read-model-contracts.md
docs/specs/vertical-slices/p1-06-first-use-onboarding.md
docs/planning/README.md
docs/planning/execs/EXEC-1061-p1-06a-onboarding-readiness-foundation.md
docs/archive/exec-plans/EXEC-1061-p1-06a-onboarding-readiness-foundation.md
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

### Delivered

- migration `f1061a0b9c01` 新增 presentation-only preference 与 command receipt；迁移时 existing
  users backfill 为 `DISMISSED / LEGACY_EXISTING_USER_BACKFILL`，迁移后新用户首次读取为
  `ACTIVE v1`；唯一约束、条件版本更新与 receipt 防止并发 last-write-wins 和重复副作用；
- `Platform Experience Preference` repository/service 是唯一 writer；表和公共 preference 均不含
  document/goal/plan/activity/transcript ref 或 step completion；
- journey 的 MODEL/MATERIAL/GOAL/FIRST_ACTIVITY 分别读取 SYS08、SYS01、SYS06 与 SYS06 exact
  lifecycle/transcript owner facts；依赖 query 不可用返回 PARTIAL 且不强制 welcome；
- first completion 只接纳 `active -> completed`、
  `LEARNER_FINISHED_TRANSCRIPT_BACKED_ACTIVITY`、learner actor 与同 owner/activity 的 exact
  `BookLearningTranscriptTurn`；ModelInference、错误 transition、缺失/跨 owner transcript 均不能完成；
- API 已 current-user scoped、strict v1、`private, no-store`，并有 cross-user、secret、path、prompt、
  domain-ref leakage 负面证据。

### Verification

- 定向 P1-06A：原 20 项通过；追加 SQLite migration/new-user restart 与 PostgreSQL DDL compatibility
  用例后为 22 passed / 1 live-PostgreSQL skipped；
- commit `604144c` 的隔离工作树完整后端：398 passed / 3 skipped；新增 migration tests 只扩展测试，
  产品实现未变化；
- 隔离工作树：`ruff check app tests` PASS；`mypy app` PASS；
  `alembic upgrade head` PASS；`alembic check` = No new upgrade operations detected；
- PostgreSQL schema 使用原生 `TIMESTAMP WITH TIME ZONE`、FK cascade 与 frozen unique constraints
  编译通过；当前机器未提供 `ASKORA_POSTGRES_TEST_URL`，live PostgreSQL gate 显式 skip，未伪报执行；
- 治理提交的隔离 docs check：154 files / 0 broken links；candidate 与 staged diff check PASS；
- 实现 commit：`4747000`（amend 后最终 hash）。

### Remaining outside this EXEC

- P1-02、P1-03、P1-07 的 owner contracts/queries/actions 仍须在 EXEC-1062 精确集成；
- `/welcome`、默认入口 guard、deep-link 保留、Settings REOPEN、responsive/a11y/browser/real-provider/
  App restart 产品门禁属于 EXEC-1062；
- shared worktree 的未提交 P1-01 migration 与本 migration 暂时形成两个 Alembic heads；本提交的隔离
  单-head 全量 migration 已通过，集成 P1-01 时必须线性化或增加治理后的 merge revision；
- `SPEC GAP`：无。依赖尚未完成不等于 P1-06 完成，EXEC-1061 DONE 不得单独关闭 P1-06。
