# EXEC-007 — v0.3 Governance Preconditions

> Priority：P0 Blocker  
> Status：READY  
> Depends on：v0.2 Release Gate PASS、v0.3 Vertical Slice Gate PASS

## Objective

在任何 v0.3 adaptive-policy canonical writer 上线前，关闭 v0.2 收口报告中的两个治理前置债务：

1. `/users/profile` 不再直接读取 legacy `UserProfile` persistence model；
2. v0.3 candidate commit 必须有可查询、可持久化的 CI evidence。

本 EXEC 不实现 Teaching Policy 新功能。

## Dependencies

- `docs/archive/releases/v0.2-first-vertical-learning-loop.md`
- `docs/specs/vertical-slices/v0.3-adaptive-teaching-loop.md`

## Required Specs

Codex 开始前 MUST 读取根 `AGENTS.md`，并至少读取：

- `docs/specs/README.md`
- `docs/specs/architecture/dependency-rules.md`
- `docs/specs/architecture/state-ownership.md`
- `docs/specs/quality/testing-standard.md`
- `docs/specs/quality/definition-of-done.md`
- `docs/specs/quality/observability-standard.md`
- `docs/specs/vertical-slices/v0.3-adaptive-teaching-loop.md`

## Current Reality

已确认当前 `main`：

- `apps/backend/app/api/v1/users.py` 的 `GET /users/profile` 在 API handler 内直接 import/query `app.models.profile.UserProfile`；
- profile 返回值包含 legacy `mastery_summary`、`metacognition`、`affective` 等字段；
- `.github/workflows/ci.yml` 已存在，并包含 backend tests、ruff/black/mypy、Alembic、frontend build、dependency audit、container build；
- 当前 v0.3 Spec/Vertical Slice head 没有可查询的 commit status evidence，因此不能仅以“workflow 文件存在”视为 VSLICE-301 已完成。

## Allowed Files

优先只允许：

```text
apps/backend/app/api/v1/users.py
apps/backend/app/**/queries/**
apps/backend/app/**/read_models/**
apps/backend/app/**/repositories/**
apps/backend/app/contracts/**
apps/backend/tests/architecture/**
apps/backend/tests/integration/**
apps/backend/tests/contracts/**
.github/workflows/ci.yml
.github/workflows/**                 # 仅为 CI evidence 必要调整
docs/archive/releases/**                     # 仅保存非敏感 gate evidence 时按现有治理使用
```

如仓库现有目录有等价 query/application boundary，优先复用，不为目录美观大规模搬迁代码。

## Forbidden Changes

- 不新增 v0.3 StrategyFamily / TeachingContext / PolicyBundle runtime；
- 不改变 canonical learner truth ownership；
- 不把 legacy `UserProfile.mastery_summary` 宣称为 SYS03 canonical `MasteryEstimate`；
- 不通过复制 legacy profile 数据建立第二事实源；
- 不删除用户资料中的非学习偏好字段，除非已有明确替代来源；
- 不弱化 CI 检查来制造绿色结果；
- 不提交任何 API key、token、secret；
- 不修改 Design、ADR、Spec 语义。

## Implementation Tasks

### T1 — Establish Canonical Profile Query Boundary

建立 application/query/read-model boundary，使 API handler 只依赖稳定 query contract，而不是直接依赖 ORM persistence model。

要求：

- canonical learning/mastery 数据从正确 owner/read projection 读取；
- legacy-only 字段若暂时保留，必须被明确标记为 compatibility projection；
- handler 不再 import `app.models.profile.UserProfile`；
- API response 尽量保持前端兼容；如公共 response contract 必须变化且 Spec 未定义，停止并报告 `SPEC GAP`。

### T2 — Remove Architecture Debt

更新 architecture tests/allowlist：

- 删除 `/users/profile` direct persistence read 的既有例外；
- 增加回归，禁止 API 层重新直接查询 learner/profile canonical persistence truth；
- 如仍有 compatibility adapter，必须给出准确 retirement condition，不得沿用已经完成的 `EXEC-004`。

### T3 — Make CI Evidence Auditable

核对并修复 `.github/workflows/ci.yml`，使当前仓库在 GitHub 上能够形成至少以下持久化 checks：

```text
backend tests
ruff / formatting / type baseline
alembic migration validation
frontend build
dependency audit
```

如果现有 workflow 已满足代码层要求，只修复导致 workflow 无法产生 status/check 的真实问题；不要为了本 EXEC 重写 CI 平台。

### T4 — Preserve Non-sensitive Evidence

完成后记录：

- candidate commit SHA；
- workflow/check names；
- PASS/FAIL；
- 如 GitHub 权限/平台配置导致无法产生 status，精确报告外部 blocker。

不得伪造 CI PASS。

## Acceptance Criteria

- `EXEC007-AC-001`：`GET /users/profile` handler 不再 import/query `UserProfile` ORM。
- `EXEC007-AC-002`：canonical mastery/progress 信息只来自 canonical query/read projection；legacy summary 不成为第二事实源。
- `EXEC007-AC-003`：architecture test 阻止 API 层恢复 direct learner/profile persistence read。
- `EXEC007-AC-004`：前端依赖的 profile API 核心字段兼容，或明确给出受 Spec 支持的迁移。
- `EXEC007-AC-005`：candidate commit 有可查询的 CI checks/status；若外部平台阻塞则本 EXEC 不能标 DONE。
- `EXEC007-AC-006`：backend test/quality、migration、frontend build、dependency audit 对 candidate commit 全部有明确结果。
- `EXEC007-AC-007`：没有引入 v0.3 adaptive-policy 功能或新的事实源。
- `EXEC007-AC-008`：无 blocking `SPEC GAP`。

## Required Tests

至少新增/更新：

```text
architecture: API -> query/read-model boundary
integration: GET /users/profile canonical/compatibility response
regression: legacy mastery cannot override canonical projection
CI workflow/check verification
```

本地最低命令：

```bash
cd apps/backend
uv run pytest tests/architecture tests/integration
uv run ruff check app tests
uv run mypy app --no-error-summary
uv run alembic upgrade head
uv run alembic check

cd ../frontend
npm run build
```

最终仍以 GitHub candidate commit 的持久化 CI evidence 为 AC-005/006 的发布证据。

## Completion Report Format

```text
Status: DONE | PARTIAL | BLOCKED_BY_SPEC_GAP | BLOCKED_BY_EXTERNAL_CI

Changed files:
- ...

Profile boundary:
- API dependency before/after
- canonical source
- compatibility fields
- architecture debt removed

CI evidence:
- candidate commit
- checks
- result

AC Matrix:
- EXEC007-AC-001 ... EXEC007-AC-008

Tests:
- command -> result

SPEC GAP:
- none / details

External blocker:
- none / details
```

只有 `Status: DONE` 才允许开始 EXEC-008 的 canonical v0.3 writer cutover。