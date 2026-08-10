# EXEC-052 — CI Governance & Test Oracle Classification

> Status：FROZEN / READY  
> Governing：PRODUCT-POSITIONING、CI-*、QUAL-V1-*  
> Dependency：None；MAY run as documentation/governance work beside current implementation chains  
> Next：EXEC-053

## Objective

在修改 runtime 或大规模删除测试前，先建立 CI v2 的治理真值：同步文档生命周期、识别 stale test oracle、冻结 Required / Optional / Historical 分类，并保证后续 Codex 不会用旧测试恢复已经退出 v1 的产品能力。

## Dependencies

- 当前 `main` 可读取；
- 不要求 EXEC-047～051 或 UI-03 完成；
- 本任务不得修改 production runtime 或 UI。

## Required Product Positioning

必须读取 `docs/product/PRODUCT-POSITIONING.md`，尤其：Local Web、single-user、SQLite/local files、no-auth、no Redis/PostgreSQL/Docker runtime、Chromium、BYOK、migration/recovery/test/replay 边界。

## Required Specs

- `docs/specs/quality/ci-infrastructure-standard.md`
- `docs/specs/quality/v1-local-web-quality-reconciliation.md`
- `docs/specs/quality/testing-standard.md`
- `docs/specs/quality/security-standard.md`
- `docs/specs/quality/definition-of-done.md`
- ADR-0015 / LID-* current identity contract
- `docs/design/CI-Test-Infrastructure-Gap-Analysis.md`

## Current Reality

- `document-inventory.md` 尚未登记最新 Product Positioning / ADR-0015 / CI quality delta，并仍有旧账号/desktop canonical 描述；
- Required suite 中存在 auth/account/cross-user/PostgreSQL/native-desktop 历史 oracle；
- `check_docs.py` 使用硬编码阶段文本识别 stale claims；
- `main` 尚无 Required Status protection。

## Allowed Files

```text
docs/document-inventory.md
docs/specs/README.md
docs/specs/quality/**
docs/design/CI-Test-Infrastructure-Gap-Analysis.md
.github/**
apps/backend/tests/**
apps/backend/pyproject.toml
apps/frontend/package.json
```

本任务只允许治理、分类、marker/manifest 与文档一致性调整；不得改变 production behavior。

## Forbidden Changes

- 不删除或弱化仍有效的学习内核测试；
- 不修改 backend production code；
- 不修改 frontend product UI；
- 不通过 skip/xfail 大量旧测试制造绿色；
- 不新增临时 hash/filename baseline；
- 不把 PostgreSQL/Docker/real-provider compatibility 重新定义为 v1 Required truth。

## Implementation Tasks

1. 更新 `document-inventory.md`：登记 PRODUCT-POSITIONING、ADR-0015、CI Infrastructure Standard、Quality Reconciliation、Gap Analysis，并把已 superseded Account/native-desktop 文档标为 historical/superseded where applicable；
2. 审查 `testing-standard.md` / `security-standard.md` / `observability-standard.md` / `definition-of-done.md`，确保 `QUAL-V1-*` supersession 可被索引发现；
3. 对现有测试建立明确分类：`KEEP_REQUIRED` / `REWRITE_REQUIRED` / `OPTIONAL_COMPATIBILITY` / `HISTORICAL_MIGRATION` / `DELETE_CANDIDATE`；
4. stale auth/account/password/JWT/cross-user/PostgreSQL/native desktop tests 必须有逐文件或稳定 pattern 分类；
5. 保留 Teaching Policy、Assessment、Learner State、Review、Retrieval、Content、Replay、OPVE、security core tests 的 Required 身份；
6. 将 `check_docs.py` 的阶段性硬编码规则设计为可退休/通用 lifecycle 检查；若本任务直接修改，必须保证不降低 broken-link / active EXEC / inventory gate；
7. 输出后续 EXEC-053～058 可直接消费的分类证据。

## Acceptance Criteria

- `E052-AC-001`：最新 Product/ADR/CI docs 均在 document inventory 有明确 disposition；
- `E052-AC-002`：P1-05 Account Lifecycle / desktop-native clauses 不再被 inventory 描述为当前 v1 release truth；
- `E052-AC-003`：stale auth/account/cross-user/PostgreSQL/native-desktop tests 全部有分类；
- `E052-AC-004`：任何 `DELETE_CANDIDATE` 都有“无 migration/security/audit value”理由；
- `E052-AC-005`：核心学习正确性 tests 未被降级；
- `E052-AC-006`：文档 link / active EXEC / inventory 检查仍可执行；
- `E052-AC-007`：没有新增永久例外 baseline。

## Required Tests

- `python .github/workflows/check_docs.py`；
- 对新增 marker/manifest 做 schema/parse test（若有）；
- 不要求运行全量 backend suite，除非修改测试执行配置。

## Completion Report Format

报告：document lifecycle changes、test oracle classification counts、仍需 rewrite/delete 的路径、docs gate 结果、commit SHA、`E052 DONE` 或 blocker。