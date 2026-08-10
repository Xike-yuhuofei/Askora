# EXEC-052 — CI Governance & Test Oracle Classification

> Status：FROZEN / READY  
> Governing：PRODUCT-POSITIONING、CI-*、QUAL-V1-*  
> Dependency：None；MAY run as documentation/governance work beside current implementation chains  
> Next：EXEC-053

## Objective

在修改 runtime 或大规模删除测试前，先建立 CI v2 的治理真值：同步文档生命周期、识别 stale test oracle、冻结 Required / Optional / Historical 分类，并保证后续 Codex 不会用旧测试恢复已经退出 v1 的产品能力。

测试 oracle reconciliation 不只针对旧 auth/PostgreSQL/native desktop。凡与最新 PRODUCT-POSITIONING 冲突或已明确退出 v1 核心范围的行为，都必须分类，包括：跨 Workspace Global Material Library、Project-as-learning-gate、完整 OCR Pipeline、非 v1 核心输入格式/媒体 pipeline 等。

## Dependencies

- 当前 `main` 可读取；
- 不要求 EXEC-047～051 或 UI-03 完成；
- 本任务不得修改 production runtime 或 UI。

## Required Product Positioning

必须读取 `docs/product/PRODUCT-POSITIONING.md`，尤其：Local Web、single-user、SQLite/local files、no-auth、no Redis/PostgreSQL/Docker runtime、Chromium、BYOK、Workspace/Project/Material、v1 import formats、OCR boundary、migration/recovery/test/replay 边界。

至少按以下上位事实审查 test oracle：

```text
single-user / no account
Workspace != Tenant / Organization
no cross-Workspace Global Material Library
Material belongs to Workspace
Material <-> LearningProject = many-to-many
LearningProject is not required for direct Material learning
core formats = EPUB / PDF / Markdown / TXT
complete OCR pipeline is not v1 core
Podcast / YouTube / RSS / native audio/video / DOCX / PPTX / XLSX are not v1 core
Redis/PostgreSQL/Docker/native desktop are not v1 production requirements
```

## Required Specs

- `docs/specs/quality/ci-infrastructure-standard.md`
- `docs/specs/quality/v1-local-web-quality-reconciliation.md`
- `docs/specs/quality/testing-standard.md`
- `docs/specs/quality/security-standard.md`
- `docs/specs/quality/definition-of-done.md`
- ADR-0015 / LID-* current identity contract
- current Workspace / Material / Project / Content Ingestion contracts
- `docs/design/CI-Test-Infrastructure-Gap-Analysis.md`

## Current Reality

- `document-inventory.md` 尚未登记最新 Product Positioning / ADR-0015 / CI quality delta，并仍有旧账号/desktop canonical 描述；
- Required suite 中存在 auth/account/cross-user/PostgreSQL/native-desktop 历史 oracle；
- 还可能存在把跨 Workspace/global library、完整 OCR、非 v1 核心 importer/media capability 当作 release truth 的旧测试；
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
- 不把 PostgreSQL/Docker/real-provider compatibility 重新定义为 v1 Required truth；
- 不把完整 OCR、Podcast/YouTube/RSS/native media、DOCX/PPTX/XLSX 等非 v1 核心能力重新定义为 Required release truth；
- 不把 Global Material Library / default cross-Workspace retrieval 定义为 Required behavior；
- 不把 Project 必填/必建定义为 Material 学习启动前提；
- 不因为某测试名称含 OCR/global/cross-user 就机械删除；必须先判断是否仍有 migration/security/compatibility 价值。

## Implementation Tasks

1. 更新 `document-inventory.md`：登记 PRODUCT-POSITIONING、ADR-0015、CI Infrastructure Standard、Quality Reconciliation、Gap Analysis，并把已 superseded Account/native-desktop 文档标为 historical/superseded where applicable。
2. 审查 `testing-standard.md` / `security-standard.md` / `observability-standard.md` / `definition-of-done.md`，确保 `QUAL-V1-*` supersession 可被索引发现。
3. 对现有测试建立明确分类：`KEEP_REQUIRED` / `REWRITE_REQUIRED` / `OPTIONAL_COMPATIBILITY` / `HISTORICAL_MIGRATION` / `DELETE_CANDIDATE`。
4. stale auth/account/password/JWT/cross-user/PostgreSQL/native desktop tests 必须有逐文件或稳定 pattern 分类。
5. 对 Workspace/Material/Project 相关旧 oracle 分类：
   - cross-user isolation 若真实意图是数据隔离，应 `REWRITE_REQUIRED` 为 LocalOwner + Workspace isolation；
   - Global Material Library/default cross-Workspace retrieval expected behavior 必须 rewrite/delete，不得保留 Required；
   - Project-required-to-learn expected behavior 必须 rewrite/delete。
6. 对内容导入与 OCR tests 分类：
   - EPUB/PDF(text)/Markdown/TXT 核心路径保留 Required；
   - 完整 OCR/layout/table/formula/vision pipeline 不属于 v1 Required，可按实际价值标 `OPTIONAL_COMPATIBILITY` / `DELETE_CANDIDATE`；
   - Podcast/YouTube/RSS/native audio/video/DOCX/PPTX/XLSX 等非 v1 核心 importer tests 不得进入 Required，除非仅验证“明确拒绝/unsupported/partial”当前 contract。
7. 保留 Teaching Policy、Assessment、Learner State、Review、Retrieval、Content core、Replay、OPVE、security core tests 的 Required 身份。
8. 所有 `DELETE_CANDIDATE` 必须说明无 migration/security/audit/compatibility value；有价值但非 v1 release truth 的移到 Optional/Historical。
9. 将 `check_docs.py` 的阶段性硬编码规则设计为可退休/通用 lifecycle 检查；若本任务直接修改，必须保证不降低 broken-link / active EXEC / inventory gate。
10. 输出后续 EXEC-053～058 可直接消费的分类证据，至少能让 EXEC-054 直接筛出 Product Boundary Required suite。

## Acceptance Criteria

- `E052-AC-001`：最新 Product/ADR/CI docs 均在 document inventory 有明确 disposition。
- `E052-AC-002`：P1-05 Account Lifecycle / desktop-native clauses 不再被 inventory 描述为当前 v1 release truth。
- `E052-AC-003`：stale auth/account/cross-user/PostgreSQL/native-desktop tests 全部有分类。
- `E052-AC-004`：任何 `DELETE_CANDIDATE` 都有“无 migration/security/audit value”理由。
- `E052-AC-005`：核心学习正确性 tests 未被降级。
- `E052-AC-006`：文档 link / active EXEC / inventory 检查仍可执行。
- `E052-AC-007`：没有新增永久例外 baseline。
- `E052-AC-008`：Global Material Library / default cross-Workspace retrieval / Project-as-learning-gate 的旧 oracle 已全部分类为 rewrite/delete/optional，不再是 Required truth。
- `E052-AC-009`：完整 OCR 与非 v1 核心 importer/media tests 已分类，不进入 v1 Required release gate；文本型 PDF 与 EPUB/Markdown/TXT 核心路径保持 Required。
- `E052-AC-010`：cross-user isolation 中仍有价值的测试已明确迁移目标为 LocalOwner + Workspace isolation，而不是简单删除隔离覆盖。

## Required Tests

- `python .github/workflows/check_docs.py`；
- 对新增 marker/manifest 做 schema/parse test（若有）；
- test classification manifest/pattern 可解析且无未分类的已知 stale groups；
- 不要求运行全量 backend suite，除非修改测试执行配置。

## Completion Report Format

报告：document lifecycle changes、test oracle classification counts、Workspace/global-library/OCR/importer classification、仍需 rewrite/delete 的路径、docs gate 结果、commit SHA、`E052 DONE` 或 blocker。