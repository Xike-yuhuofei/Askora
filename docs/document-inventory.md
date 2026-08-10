# Askora 文档处置清单

> 状态：Current  
> 校准日期：2026-08-10  
> 基线提交：`80436354a9a7ef9043113f8b4356b8b2818c2301`  
> 目的：为当前受跟踪 Markdown/RST 文档声明 lifecycle/disposition；实时执行状态仍以对应索引、Linear 和 current `main` 为准。

处置代码：

- `CURRENT-UPDATED`：当前说明/审计/索引；
- `CANONICAL-RETAIN`：当前冻结产品/设计/ADR/Spec 合同；
- `HISTORICAL-RETAIN`：历史 EXEC/Release/Research/已 supersede 基线；
- `SUPPORT-RETAIN`：提示词、工具、设计辅助说明；
- `EXCLUDED`：测试夹具/数据，不是项目说明；
- `DELETED`：历史清理记录，文件本身不应继续作为当前说明。

## 1. Root / Application / Support

| 文件 | 处置 |
|---|---|
| `AGENTS.md` | CANONICAL-RETAIN |
| `README.md` | CURRENT-UPDATED |
| `Askora EXEC-042 执行提示词.md` | SUPPORT-RETAIN |
| `Askora EXEC-1062 执行提示词.md` | SUPPORT-RETAIN |
| `Askora EXEC-047 执行提示词.md` | SUPPORT-RETAIN |
| `Askora EXEC-042 剩余收口执行提示词.md` | SUPPORT-RETAIN |
| `Askora CI v2 + Local Web Baseline 全链路自主执行提示词.md` | SUPPORT-RETAIN |
| `apps/backend/README.md` | CURRENT-UPDATED |
| `apps/frontend/README.md` | CURRENT-UPDATED |
| `apps/frontend/resources/backend/README.md` | SUPPORT-RETAIN |
| `apps/backend/.trae/documents/seed_data_plan.md` | DELETED |
| `apps/backend/tests/fixtures/malicious_document.md` | EXCLUDED |
| `apps/backend/data/documents/user_pseudo_001/6dcb2a02-322a-4e35-b33a-54708b8d5904_3673b0a7.md` | EXCLUDED |
| `.design_library/Askora/README.md` | SUPPORT-RETAIN |
| `.design_library/Askora/SKILL.md` | SUPPORT-RETAIN |

## 2. Product / ADR / Release Index

| 文件 | 处置 |
|---|---|
| `docs/README.md` | CURRENT-UPDATED |
| `docs/CODE_WIKI.md` | CURRENT-UPDATED |
| `docs/document-inventory.md` | CURRENT-UPDATED |
| `docs/product/PRODUCT-POSITIONING.md` | CANONICAL-RETAIN |
| `docs/product-gap-register-p1-p2.md` | CURRENT-UPDATED |
| `docs/adr/README.md` | CANONICAL-RETAIN |
| `docs/adr/ADR-0001-teaching-strategy-ontology.md` | CANONICAL-RETAIN |
| `docs/adr/ADR-0002-constrained-deterministic-teaching-policy-architecture.md` | CANONICAL-RETAIN |
| `docs/adr/ADR-0003-policy-runtime-profile-source-and-activation.md` | CANONICAL-RETAIN |
| `docs/adr/ADR-0004-guided-book-learning-and-durable-transcript.md` | CANONICAL-RETAIN |
| `docs/adr/ADR-0005-policy-bound-real-model-rendering.md` | CANONICAL-RETAIN |
| `docs/adr/ADR-0006-workspace-read-model-scope-and-missing-objective-metadata.md` | CANONICAL-RETAIN |
| `docs/adr/ADR-0007-sys06-activity-lifecycle-and-completion.md` | CANONICAL-RETAIN |
| `docs/adr/ADR-0008-library-management-deduplication-and-ocr.md` | CANONICAL-RETAIN |
| `docs/adr/ADR-0009-local-first-identity-privacy-lifecycle.md` | CANONICAL-RETAIN |
| `docs/adr/ADR-0010-goal-definition-state-draft-and-replan.md` | CANONICAL-RETAIN |
| `docs/adr/ADR-0011-goal-achievement-measurement-and-evidence-gate.md` | CANONICAL-RETAIN |
| `docs/adr/ADR-0012-unified-recovery-control-plane.md` | CANONICAL-RETAIN |
| `docs/adr/ADR-0013-desktop-model-credential-and-activation.md` | CANONICAL-RETAIN |
| `docs/adr/ADR-0014-user-job-driven-interaction-architecture.md` | CANONICAL-RETAIN |
| `docs/adr/ADR-0015-local-single-user-identity-without-authentication.md` | CANONICAL-RETAIN |
| `docs/adr/ADR-0016-workspace-project-and-learning-session-scope-ownership.md` | CANONICAL-RETAIN |
| `docs/adr/ADR-0017-os-backed-local-secret-store-and-crash-consistent-model-activation.md` | CANONICAL-RETAIN |
| `docs/adr/ADR-0103-local-data-recovery-portability-erasure.md` | CANONICAL-RETAIN |
| `docs/adr/ADR-0106-fact-driven-onboarding-readiness-and-preferences.md` | CANONICAL-RETAIN |
| `docs/adr/ADR-0107-account-deletion-erasure-workflow-integration.md` | CANONICAL-RETAIN |
| `docs/releases/README.md` | CURRENT-UPDATED |
| `docs/releases/v0.2-first-vertical-learning-loop.md` | HISTORICAL-RETAIN |
| `docs/releases/v0.3-governance-preconditions.md` | HISTORICAL-RETAIN |
| `docs/releases/v0.3-adaptive-teaching-loop.md` | HISTORICAL-RETAIN |
| `docs/releases/ui-01-learning-shell-workspace.md` | HISTORICAL-RETAIN |
| `docs/releases/ui-02a-library-knowledge-map.md` | HISTORICAL-RETAIN |
| `docs/releases/p1-03-data-control-recovery.md` | HISTORICAL-RETAIN |
| `docs/releases/ui-02b2-guided-book-learning.md` | HISTORICAL-RETAIN |
| `docs/releases/p1-04-library-management.md` | HISTORICAL-RETAIN |
| `docs/releases/p1-01a-goal-definition-draft-replan.md` | HISTORICAL-RETAIN |
| `docs/releases/p1-01b-goal-lifecycle-achievement.md` | HISTORICAL-RETAIN |

## 3. Canonical Design / Research

| 文件 | 处置 |
|---|---|
| `docs/design/README.md` | CURRENT-UPDATED |
| `docs/design/个人AI辅助学习平台设计方案.md` | CURRENT-UPDATED |
| `docs/design/AI学习系统算法与教学内核设计.md` | CURRENT-UPDATED |
| `docs/design/UX-Architecture-Canonical-Design-Delta.md` | CANONICAL-RETAIN |
| `docs/design/Interactive-Element-System-Canonical-Design-Delta.md` | CANONICAL-RETAIN |
| `docs/design/Local-Single-User-Identity-Authentication-Removal-Canonical-Design-Delta.md` | CANONICAL-RETAIN |
| `docs/design/v0.3-Canonical-Design-Delta.md` | CANONICAL-RETAIN |
| `docs/design/v0.3-Current-Main-Conformance-Gap-Analysis.md` | CURRENT-UPDATED |
| `docs/design/v1-Product-Positioning-Current-Main-Conformance-Gap-Analysis.md` | CURRENT-UPDATED |
| `docs/design/CI-Test-Infrastructure-Gap-Analysis.md` | CURRENT-UPDATED |
| `docs/design/账号与隐私生命周期设计.md` | HISTORICAL-RETAIN |
| `docs/design/p1-03-data-control-and-recovery.md` | CANONICAL-RETAIN |
| `docs/design/p1-02-model-settings.md` | HISTORICAL-RETAIN |
| `docs/design/p1-06-fact-driven-first-use-journey.md` | CANONICAL-RETAIN |
| `docs/design/research/README.md` | CURRENT-UPDATED |
| `docs/design/research/evidence/八类技术系统-教育科学证据.md` | HISTORICAL-RETAIN |
| `docs/design/research/evidence/八类技术系统-ITS与学习者建模证据.md` | HISTORICAL-RETAIN |
| `docs/design/research/evidence/八类技术系统-检索与知识架构证据.md` | HISTORICAL-RETAIN |
| `docs/design/research/evidence/八类技术系统-教学策略与序列决策证据.md` | HISTORICAL-RETAIN |
| `docs/design/research/evidence/八类技术系统-记忆与复习调度证据.md` | HISTORICAL-RETAIN |
| `docs/design/research/evidence/八类技术系统-LLM-Agent与可信治理证据.md` | HISTORICAL-RETAIN |
| `docs/design/research/evidence/八类技术系统-参考资料索引.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/4.1-内容解析与知识建模-系统设计研究.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/4.2-检索与知识供给-系统设计研究.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/4.3-学习者建模-系统设计研究.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/4.4-评估与错误诊断-系统设计研究.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/4.5-教学策略选择-系统设计研究.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/4.6-学习路径与任务调度-系统设计研究.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/4.7-记忆保持与复习调度-系统设计研究.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/4.8-LLM生成Agent编排与可信控制-系统设计研究.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/DR-03-01-教学策略与支架转换研究.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/DR-03-02-错误诊断到教学补救研究.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/DR-03-03-Teaching-Policy-决策算法与数据契约研究.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/DR-03-04-学习效果验证与产品实验研究.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/v0.3-Research-Synthesis-Adaptive-Teaching-Loop.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/v0.3-候选范围分析.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/v0.3-深度研究议程.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/八类技术系统-公共架构冻结稿.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/八类技术系统-现状诊断.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/八类技术系统-系统设计研究综合与溯源.md` | HISTORICAL-RETAIN |

## 4. Implementation Specs

| 文件 | 处置 |
|---|---|
| `docs/specs/README.md` | CURRENT-UPDATED |
| `docs/specs/architecture/state-ownership.md` | CANONICAL-RETAIN |
| `docs/specs/architecture/system-architecture.md` | CANONICAL-RETAIN |
| `docs/specs/architecture/dependency-rules.md` | CANONICAL-RETAIN |
| `docs/specs/domain/domain-model.md` | CANONICAL-RETAIN |
| `docs/specs/domain/decision-contract.md` | CANONICAL-RETAIN |
| `docs/specs/domain/event-contract.md` | CANONICAL-RETAIN |
| `docs/specs/domain/lifecycle-state-machines.md` | CANONICAL-RETAIN |
| `docs/specs/interfaces/api-contract.md` | CANONICAL-RETAIN |
| `docs/specs/interfaces/content-ingestion-contract.md` | CANONICAL-RETAIN |
| `docs/specs/interfaces/recovery-contract.md` | CANONICAL-RETAIN |
| `docs/specs/interfaces/data-control-contract.md` | CANONICAL-RETAIN |
| `docs/specs/interfaces/error-contract.md` | CANONICAL-RETAIN |
| `docs/specs/interfaces/persistence-contract.md` | CANONICAL-RETAIN |
| `docs/specs/interfaces/material-lifecycle-contract.md` | CANONICAL-RETAIN |
| `docs/specs/interfaces/onboarding-contract.md` | CANONICAL-RETAIN |
| `docs/specs/interfaces/render-content-contract.md` | CANONICAL-RETAIN |
| `docs/specs/interfaces/schema-versioning.md` | CANONICAL-RETAIN |
| `docs/specs/platform/identity-privacy-lifecycle.md` | CANONICAL-RETAIN |
| `docs/specs/platform/workspace-project-session-scope.md` | CANONICAL-RETAIN |
| `docs/specs/platform/local-secret-store.md` | CANONICAL-RETAIN |
| `docs/specs/quality/testing-standard.md` | CANONICAL-RETAIN |
| `docs/specs/quality/test-oracle-classification.md` | CANONICAL-RETAIN |
| `docs/specs/quality/observability-standard.md` | CANONICAL-RETAIN |
| `docs/specs/quality/definition-of-done.md` | CANONICAL-RETAIN |
| `docs/specs/quality/security-standard.md` | CANONICAL-RETAIN |
| `docs/specs/quality/ci-infrastructure-standard.md` | CANONICAL-RETAIN |
| `docs/specs/quality/v1-local-web-quality-reconciliation.md` | CANONICAL-RETAIN |
| `docs/specs/systems/01-content-knowledge.md` | CANONICAL-RETAIN |
| `docs/specs/systems/01-content-granularity.md` | CANONICAL-RETAIN |
| `docs/specs/systems/01-knowledge-publish-pipeline.md` | CANONICAL-RETAIN |
| `docs/specs/systems/01-library-management.md` | CANONICAL-RETAIN |
| `docs/specs/systems/02-retrieval.md` | CANONICAL-RETAIN |
| `docs/specs/systems/03-learner-model.md` | CANONICAL-RETAIN |
| `docs/specs/systems/04-assessment.md` | CANONICAL-RETAIN |
| `docs/specs/systems/05-teaching-policy.md` | CANONICAL-RETAIN |
| `docs/specs/systems/06-learning-planner.md` | CANONICAL-RETAIN |
| `docs/specs/systems/06-activity-lifecycle.md` | CANONICAL-RETAIN |
| `docs/specs/systems/06-goal-management.md` | CANONICAL-RETAIN |
| `docs/specs/systems/06-goal-knowledge-mapping.md` | CANONICAL-RETAIN |
| `docs/specs/systems/06-prerequisite-diagnostic-bootstrap.md` | CANONICAL-RETAIN |
| `docs/specs/systems/07-review-scheduler.md` | CANONICAL-RETAIN |
| `docs/specs/systems/08-ai-orchestration.md` | CANONICAL-RETAIN |
| `docs/specs/systems/08-model-configuration.md` | CANONICAL-RETAIN |
| `docs/specs/ui/README.md` | CANONICAL-RETAIN |
| `docs/specs/ui/interactive-element-system.md` | CANONICAL-RETAIN |
| `docs/specs/ui/information-architecture.md` | CANONICAL-RETAIN |
| `docs/specs/ui/screen-contracts.md` | CANONICAL-RETAIN |
| `docs/specs/ui/data-contracts.md` | CANONICAL-RETAIN |
| `docs/specs/ui/visual-system.md` | CANONICAL-RETAIN |
| `docs/specs/ui/quality-and-migration.md` | CANONICAL-RETAIN |
| `docs/specs/ui/component-state-contracts.md` | CANONICAL-RETAIN |
| `docs/specs/vertical-slices/v0.2-learning-loop.md` | HISTORICAL-RETAIN |
| `docs/specs/vertical-slices/v0.3-adaptive-teaching-loop.md` | CANONICAL-RETAIN |
| `docs/specs/vertical-slices/v0.3.1-rich-response-rendering.md` | CANONICAL-RETAIN |
| `docs/specs/vertical-slices/book-to-adaptive-learning.md` | CANONICAL-RETAIN |
| `docs/specs/vertical-slices/ui-01-learning-shell-workspace.md` | HISTORICAL-RETAIN |
| `docs/specs/vertical-slices/ui-02a-library-knowledge-map.md` | HISTORICAL-RETAIN |
| `docs/specs/vertical-slices/ui-02b1-material-learning-launch.md` | HISTORICAL-RETAIN |
| `docs/specs/vertical-slices/ui-02b2-guided-book-learning.md` | HISTORICAL-RETAIN |
| `docs/specs/vertical-slices/ui-02b3-real-model-guided-learning.md` | HISTORICAL-RETAIN |
| `docs/specs/vertical-slices/ui-02b-goals-path-evidence.md` | HISTORICAL-RETAIN |
| `docs/specs/vertical-slices/ui-02c-canonical-activity-lifecycle.md` | HISTORICAL-RETAIN |
| `docs/specs/vertical-slices/ui-03-interactive-element-system-refactor.md` | CANONICAL-RETAIN |
| `docs/specs/vertical-slices/p1-05-account-lifecycle.md` | HISTORICAL-RETAIN |
| `docs/specs/vertical-slices/p1-04a-library-organization.md` | HISTORICAL-RETAIN |
| `docs/specs/vertical-slices/p1-04b-library-deduplication.md` | HISTORICAL-RETAIN |
| `docs/specs/vertical-slices/p1-04c-library-ocr-review.md` | HISTORICAL-RETAIN |
| `docs/specs/vertical-slices/p1-07-error-recovery-center.md` | CANONICAL-RETAIN |
| `docs/specs/vertical-slices/p1-03-data-control-recovery.md` | CANONICAL-RETAIN |
| `docs/specs/vertical-slices/p1-02-model-settings.md` | HISTORICAL-RETAIN |
| `docs/specs/vertical-slices/p1-06-first-use-onboarding.md` | CANONICAL-RETAIN |
| `docs/specs/vertical-slices/local-single-user-authentication-removal.md` | CANONICAL-RETAIN |
| `docs/specs/vertical-slices/p1-01a-goal-definition-draft-replan.md` | CANONICAL-RETAIN |
| `docs/specs/vertical-slices/p1-01b-goal-lifecycle-achievement.md` | CANONICAL-RETAIN |

## 5. Execution Plans

Active EXEC contracts are additionally governed by `docs/exec-plans/README.md`; listing them here is optional for the checker but retained for audit clarity.

| 文件 | 处置 |
|---|---|
| `docs/exec-plans/README.md` | CURRENT-UPDATED |
| `docs/exec-plans/completed/README.md` | CURRENT-UPDATED |
| `docs/exec-plans/CHAIN-A-UI-03-PROMPT.md` | SUPPORT-RETAIN |
| `docs/exec-plans/CHAIN-B-CI-V2-PROMPT.md` | SUPPORT-RETAIN |
| `docs/exec-plans/active/EXEC-044-ui-03b-today-primary-hierarchy.md` | CANONICAL-RETAIN |
| `docs/exec-plans/active/EXEC-045-ui-03c-library-progressive-disclosure.md` | CANONICAL-RETAIN |
| `docs/exec-plans/active/EXEC-046-ui-03d-settings-legacy-release-closure.md` | CANONICAL-RETAIN |
| `docs/exec-plans/active/EXEC-054-required-core-test-realignment.md` | CANONICAL-RETAIN |
| `docs/exec-plans/active/EXEC-055-local-data-migration-recovery-rebuild-gate.md` | CANONICAL-RETAIN |
| `docs/exec-plans/active/EXEC-056-local-web-chromium-e2e.md` | CANONICAL-RETAIN |
| `docs/exec-plans/active/EXEC-057-ci-workflow-quality-supply-chain.md` | CANONICAL-RETAIN |
| `docs/exec-plans/active/EXEC-058-required-gate-main-protection-closure.md` | CANONICAL-RETAIN |
| `docs/exec-plans/active/EXEC-059-ui-design-system-component-foundation.md` | CANONICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-001-contracts-event-outbox-foundation.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-002-canonical-teaching-entry.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-003-content-evidence-bundle.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-004-assessment-learner-projection.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-005-review-planner-integration.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-006-v0.2-e2e-quality-gate.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-007-v0.3-governance-preconditions.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-008-v0.3-contracts-schema-migration.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-009-deterministic-teaching-policy-kernel.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-010-adaptive-transition-anti-oscillation.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-011-cross-system-adaptive-execution.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-012-outcome-experiment-opve-foundation.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-013-v0.3-e2e-release-gate.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-014-rich-response-rendering.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-015-ui-01-learning-shell-workspace.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-016-ui-02a-library-knowledge-map.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-017-structure-preserving-epub-ingestion.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-018-multi-granularity-content-projections.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-019-knowledge-verification-publication.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-020-retrieval-projection-sys02-binding.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-021-learning-goal-knowledge-mapping.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-022-prerequisite-diagnostic-planner-bootstrap.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-023-book-learning-orchestration-api.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-024-book-to-learning-e2e-release-gate.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-025-ui-02b1-material-learning-launch.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-026-ui-02b2-guided-book-learning.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-027-ui-02b3-real-model-e2e.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-028-zhipu-development-model.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-029-ui-02b-goals-path-evidence.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-030-ui-02c-canonical-activity-lifecycle.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-031-p1-04a-library-organization.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-032-p1-04b-library-deduplication.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-033-p1-04c-library-ocr-review.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-034-identity-session-foundation.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-035-local-account-recovery.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-036-account-deletion-erasure.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-037-p1-07-error-recovery-center.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-037-p1-05-p1-03-erasure-integration.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-038-p1-01a-goal-definition-draft-replan.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-039-p1-01b-goal-lifecycle-achievement.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-040-p1-02a-model-configuration-foundation.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-041-p1-02b-model-settings-product-closure.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-042-v0.3-production-sequential-teaching-policy-closure.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-043-ui-03a-shell-routes-learning-domain.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-047-local-owner-foundation-migration.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-048-backend-no-auth-loopback-cutover.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-049-frontend-settings-onboarding-deaccounting.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-050-auth-persistence-configuration-cleanup.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-051-local-identity-release-closure.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-052-ci-governance-test-oracle-classification.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-053-production-local-runtime-cutover.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-1031-p1-03-recovery-foundation.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-1032-p1-03-verified-restore.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-1033-p1-03-user-data-export.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-1034-p1-03-erasure-ui-release.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-1061-p1-06a-onboarding-readiness-foundation.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-1062-p1-06b-onboarding-product-closure.md` | HISTORICAL-RETAIN |

## 6. Release Evidence

| 文件 | 处置 |
|---|---|
| `docs/releases/book-to-adaptive-learning.md` | HISTORICAL-RETAIN |
| `docs/releases/ui-02b1-material-learning-launch.md` | HISTORICAL-RETAIN |
| `docs/releases/ui-02b2-guided-book-learning.md` | HISTORICAL-RETAIN |
| `docs/releases/ui-02b3-real-model-guided-learning.md` | HISTORICAL-RETAIN |
| `docs/releases/ui-02b-goals-path-evidence.md` | HISTORICAL-RETAIN |
| `docs/releases/ui-02c-canonical-activity-lifecycle.md` | HISTORICAL-RETAIN |
| `docs/releases/p1-07-error-recovery-center.md` | HISTORICAL-RETAIN |
| `docs/releases/p1-05-account-lifecycle.md` | HISTORICAL-RETAIN |
| `docs/releases/p1-02-model-settings.md` | HISTORICAL-RETAIN |
| `docs/releases/p1-06-first-use-onboarding.md` | HISTORICAL-RETAIN |
| `docs/releases/v0.3-production-sequential-policy-closure.md` | HISTORICAL-RETAIN |

## 7. Maintenance Rules

1. `PRODUCT-POSITIONING.md` 是最高产品约束；下位文档不得反向覆盖。
2. Active EXEC 实时状态由 `docs/exec-plans/README.md` 管理；完成后必须归档并进入 inventory。
3. 历史 Desktop/OCR/Account/PostgreSQL evidence 可以保留，但不得解释成 v1 runtime requirement。
4. 新增 Canonical/Current 文档必须在同一治理阶段登记 inventory，并运行文档门禁。
5. Engineering/Product conformance 与 Learning Evidence 必须分开声明。
