# EXEC-057 — CI Workflow, Quality & Supply-chain Realignment

> Status：FROZEN / BLOCKED_BY_DEPENDENCY_GATE  
> Governing：PRODUCT-POSITIONING、CI-*、QUAL-V1-*  
> Dependency：EXEC-055 DONE  
> Next：EXEC-058

## Objective

把 GitHub Actions 和静态质量基础设施重构成稳定、低脆弱、可维护的 CI v2：Required 与 Optional 分离，永久 legacy baseline 退休，Actions/runtime/dependency 自动更新，减少无价值重复矩阵和过期 run。

## Dependencies

- EXEC-054 Required test commands 已稳定；
- EXEC-055 migration/recovery commands 已稳定；
- 不要求 EXEC-056 已完成，可并行准备 workflow，但最终 aggregate 由 EXEC-058 收口。

## Required Product Positioning

必须读取 PRODUCT-POSITIONING 的 Testing、Local Web、Non-goals 与最终工程判断标准。

## Required Specs

- `CI-600..604`
- `CI-700..804`
- `CI-900..905`
- `QUAL-V1-500..502`
- current Testing / Security / DoD retained contracts

## Current Reality

- `ci.yml` 使用单一 workflow 混合 Required-like 与 Optional technology compatibility；
- Python 3.11/3.12 对 tests 和 quality 全量重复；
- `develop` trigger 已无真实分支治理意义；
- `check_black_baseline.py` 永久冻结 EXEC-007 时期文件 hash；
- mypy 排除多个高风险目录；
- frontend 无 lint script；
- dependency audits 已存在，但 dependency update automation 不完整；
- GitHub Actions major/runtime 需要按执行时官方支持状态更新。

## Allowed Files

```text
.github/**
apps/backend/pyproject.toml
apps/backend/uv.lock
apps/backend/**/*.py
apps/frontend/package.json
apps/frontend/package-lock.json
apps/frontend/**/eslint*
apps/frontend/**/vite*
apps/frontend/**/vitest*
.gitignore
README.md
docs/specs/quality/**
docs/exec-plans/**
```

生产代码只允许 formatter/type fixes，不允许改变领域行为。

## Forbidden Changes

- 不通过降低 lint/type/test assertions 制造通过；
- 不永久保留 `check_black_baseline.py` 形式的 hash exception；
- 不把 Optional PostgreSQL/Docker/real-provider failure 聚合进 v1 Required；
- 不锁死会快速过时的 GitHub Actions major 到 Spec 文档；
- 不启用自动 dependency merge 绕过 Required Gate；
- 不让 path filter 导致 Required status 永久 pending；
- 不增加 Safari/Firefox browser matrix。

## Implementation Tasks

1. 将 Required workflow 与 Optional/Scheduled/Manual compatibility workflow 分离；
2. 删除无效 `develop` trigger；
3. 引入 `concurrency` + `cancel-in-progress`；
4. 在可证明安全的范围引入 path-aware execution；
5. Required Python runtime 只跑 canonical supported version；secondary runtime 移 scheduled/optional；
6. 格式化 legacy baseline 文件并删除 `check_black_baseline.py` 与对应 exception；
7. 逐步减少 mypy exclusions；本 EXEC 至少关闭可安全关闭的历史 blind spot，剩余必须有明确 debt entry；
8. 为 frontend 建立 lint/static-quality command；
9. 保留 Vitest + build + audits；
10. 引入 Actions/Python/npm dependency update automation；
11. GitHub Actions/setup majors 必须在执行时依据 GitHub 官方当前支持版本升级；
12. dependency audit 区分 confirmed vulnerability 与 audit infrastructure outage；
13. Required workflow 不要求 Docker/PostgreSQL/real AI keys；
14. Optional workflow 可保留 Docker build/PostgreSQL compatibility/real-provider smoke，但状态名称必须清晰。

## Acceptance Criteria

- `E057-AC-001`：Required 与 Optional workflows 语义分离；
- `E057-AC-002`：无 `develop` 无效 trigger；
- `E057-AC-003`：同 branch/PR stale runs 可取消；
- `E057-AC-004`：`check_black_baseline.py` 退休且全仓适用 formatter gate PASS；
- `E057-AC-005`：mypy blind spots 不增加，并有实际收缩；
- `E057-AC-006`：frontend lint + test + build 可独立执行；
- `E057-AC-007`：dependency update automation 覆盖 Actions/Python/npm；
- `E057-AC-008`：Required workflow 不依赖 Redis/Postgres/Docker/real AI key；
- `E057-AC-009`：Optional failure 不影响 Required job graph；
- `E057-AC-010`：Actions versions 使用执行时官方支持 major，无 deprecated runtime warning。

## Required Tests

- workflow syntax validation；
- backend lint/formatter/type；
- backend Required suite；
- migration/recovery gate；
- frontend lint/test/build；
- dependency audits；
- docs gate。

## Completion Report Format

报告：workflow topology、Required/Optional jobs、removed baseline、type coverage change、frontend quality、dependency automation、official Actions version evidence、commit SHA、`E057 DONE` 或 blocker。