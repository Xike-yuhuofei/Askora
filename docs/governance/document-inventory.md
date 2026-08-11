# Askora 全量文档 Inventory 与迁移映射

> 状态：Current Documentation Inventory
> 盘点基线：GitHub `main` / `c293f5697bbff4bf050626d3c38addb9d78c3b4e`
> 校准日期：2026-08-11
> 判定方法：逐文件读取标题、状态、职责声明、规范性结构、历史/研究/执行证据信号与链接，并与 current Product/Design/ADR/Spec indexes、Git history、Linear 状态和字节级重复检查交叉验证。

本表的 `Current Path` 指迁移前路径；`Target Path` 指本次重构后的路径。重要但未进入仓库治理链的用户工作稿只标记 `REVIEW`，不移动、不删除。

建议动作只使用：`KEEP`、`MOVE`、`RENAME`、`MERGE`、`SPLIT`、`ARCHIVE`、`DELETE`、`REVIEW`。

## Summary

| Action | Count |
|---|---:|
| `KEEP` | 86 |
| `MOVE` | 78 |
| `RENAME` | 1 |
| `MERGE` | 0 |
| `SPLIT` | 0 |
| `ARCHIVE` | 122 |
| `DELETE` | 3 |
| `REVIEW` | 4 |

没有发现需要安全执行的 `MERGE` 或 `SPLIT`：相似文件除唯一字节级重复外，都保留独立的研究、决策、迁移或交付证据。

## Product / Design / Architecture / Specs

| Current Path | 文档性质 | 生命周期归属 | 长期/临时 | 是否重复 | 建议动作 | Target Path |
|---|---|---|---|---|---|---|
| `docs/README.md` | Documentation Authority Index | Current / Supporting | 长期维护 | 否 | `KEEP` | `docs/README.md` |
| `docs/adr/README.md` | Architecture 与 ADR Index | Canonical / Current | 长期维护 | 否 | `MOVE` | `docs/architecture/README.md` |
| `docs/adr/ADR-0001-teaching-strategy-ontology.md` | Architecture Decision Record | Canonical / Current | 长期维护 | 否 | `MOVE` | `docs/architecture/decisions/ADR-0001-teaching-strategy-ontology.md` |
| `docs/adr/ADR-0002-constrained-deterministic-teaching-policy-architecture.md` | Architecture Decision Record | Canonical / Current | 长期维护 | 否 | `MOVE` | `docs/architecture/decisions/ADR-0002-constrained-deterministic-teaching-policy-architecture.md` |
| `docs/adr/ADR-0003-policy-runtime-profile-source-and-activation.md` | Architecture Decision Record | Canonical / Current | 长期维护 | 否 | `MOVE` | `docs/architecture/decisions/ADR-0003-policy-runtime-profile-source-and-activation.md` |
| `docs/adr/ADR-0004-guided-book-learning-and-durable-transcript.md` | Architecture Decision Record | Canonical / Current | 长期维护 | 否 | `MOVE` | `docs/architecture/decisions/ADR-0004-guided-book-learning-and-durable-transcript.md` |
| `docs/adr/ADR-0005-policy-bound-real-model-rendering.md` | Architecture Decision Record | Canonical / Current | 长期维护 | 否 | `MOVE` | `docs/architecture/decisions/ADR-0005-policy-bound-real-model-rendering.md` |
| `docs/adr/ADR-0006-workspace-read-model-scope-and-missing-objective-metadata.md` | Architecture Decision Record | Canonical / Current | 长期维护 | 否 | `MOVE` | `docs/architecture/decisions/ADR-0006-workspace-read-model-scope-and-missing-objective-metadata.md` |
| `docs/adr/ADR-0007-sys06-activity-lifecycle-and-completion.md` | Architecture Decision Record | Canonical / Current | 长期维护 | 否 | `MOVE` | `docs/architecture/decisions/ADR-0007-sys06-activity-lifecycle-and-completion.md` |
| `docs/adr/ADR-0008-library-management-deduplication-and-ocr.md` | Architecture Decision Record | Canonical / Current | 长期维护 | 否 | `MOVE` | `docs/architecture/decisions/ADR-0008-library-management-deduplication-and-ocr.md` |
| `docs/adr/ADR-0009-local-first-identity-privacy-lifecycle.md` | Architecture Decision Record | Canonical / Current | 长期维护 | 否 | `MOVE` | `docs/architecture/decisions/ADR-0009-local-first-identity-privacy-lifecycle.md` |
| `docs/adr/ADR-0010-goal-definition-state-draft-and-replan.md` | Architecture Decision Record | Canonical / Current | 长期维护 | 否 | `MOVE` | `docs/architecture/decisions/ADR-0010-goal-definition-state-draft-and-replan.md` |
| `docs/adr/ADR-0011-goal-achievement-measurement-and-evidence-gate.md` | Architecture Decision Record | Canonical / Current | 长期维护 | 否 | `MOVE` | `docs/architecture/decisions/ADR-0011-goal-achievement-measurement-and-evidence-gate.md` |
| `docs/adr/ADR-0012-unified-recovery-control-plane.md` | Architecture Decision Record | Canonical / Current | 长期维护 | 否 | `MOVE` | `docs/architecture/decisions/ADR-0012-unified-recovery-control-plane.md` |
| `docs/adr/ADR-0013-desktop-model-credential-and-activation.md` | Architecture Decision Record | Canonical / Current | 长期维护 | 否 | `MOVE` | `docs/architecture/decisions/ADR-0013-desktop-model-credential-and-activation.md` |
| `docs/adr/ADR-0014-user-job-driven-interaction-architecture.md` | Architecture Decision Record | Canonical / Current | 长期维护 | 否 | `MOVE` | `docs/architecture/decisions/ADR-0014-user-job-driven-interaction-architecture.md` |
| `docs/adr/ADR-0015-local-single-user-identity-without-authentication.md` | Architecture Decision Record | Canonical / Current | 长期维护 | 否 | `MOVE` | `docs/architecture/decisions/ADR-0015-local-single-user-identity-without-authentication.md` |
| `docs/adr/ADR-0016-workspace-project-and-learning-session-scope-ownership.md` | Architecture Decision Record | Canonical / Current | 长期维护 | 否 | `MOVE` | `docs/architecture/decisions/ADR-0016-workspace-project-and-learning-session-scope-ownership.md` |
| `docs/adr/ADR-0017-os-backed-local-secret-store-and-crash-consistent-model-activation.md` | Architecture Decision Record | Canonical / Current | 长期维护 | 否 | `MOVE` | `docs/architecture/decisions/ADR-0017-os-backed-local-secret-store-and-crash-consistent-model-activation.md` |
| `docs/adr/ADR-0018-ux-workspace-context-architecture.md` | Architecture Decision Record | Canonical / Current | 长期维护 | 否 | `MOVE` | `docs/architecture/decisions/ADR-0018-ux-workspace-context-architecture.md` |
| `docs/adr/ADR-0019-ui-workspace-read-projections.md` | Architecture Decision Record | Canonical / Current | 长期维护 | 否 | `MOVE` | `docs/architecture/decisions/ADR-0019-ui-workspace-read-projections.md` |
| `docs/adr/ADR-0020-learning-conversation-message-presentation-and-interaction-boundary.md` | Architecture Decision Record | Canonical / Current | 长期维护 | 否 | `MOVE` | `docs/architecture/decisions/ADR-0020-learning-conversation-message-presentation-and-interaction-boundary.md` |
| N/A (new) | Architecture Decision Record | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/architecture/decisions/ADR-0022-course-centric-information-architecture.md` |
| N/A (new) | Architecture Decision Record | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/architecture/decisions/ADR-0023-course-workspace-selection-and-activity-projection.md` |
| `docs/adr/ADR-0103-local-data-recovery-portability-erasure.md` | Architecture Decision Record | Canonical / Current | 长期维护 | 否 | `MOVE` | `docs/architecture/decisions/ADR-0103-local-data-recovery-portability-erasure.md` |
| `docs/adr/ADR-0106-fact-driven-onboarding-readiness-and-preferences.md` | Architecture Decision Record | Canonical / Current | 长期维护 | 否 | `MOVE` | `docs/architecture/decisions/ADR-0106-fact-driven-onboarding-readiness-and-preferences.md` |
| `docs/adr/ADR-0107-account-deletion-erasure-workflow-integration.md` | Architecture Decision Record | Canonical / Current | 长期维护 | 否 | `MOVE` | `docs/architecture/decisions/ADR-0107-account-deletion-erasure-workflow-integration.md` |
| `docs/design/README.md` | Canonical Design Index | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/design/README.md` |
| `docs/design/experience/EXPERIENCE-ARCHITECTURE.md` | Experience 与 Interaction Design | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/design/experience/EXPERIENCE-ARCHITECTURE.md` |
| `docs/design/experience/INTERACTION-MODEL.md` | Experience 与 Interaction Design | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/design/experience/INTERACTION-MODEL.md` |
| `docs/design/experience/LEARNING-EXPERIENCE.md` | Experience 与 Interaction Design | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/design/experience/LEARNING-EXPERIENCE.md` |
| `docs/design/Learning-Conversation-Message-System-Canonical-Design-Delta.md` | Feature Canonical Design | Canonical / Current | 长期维护 | 否 | `MOVE` | `docs/design/features/Learning-Conversation-Message-System-Canonical-Design-Delta.md` |
| N/A (new) | Feature Canonical Design | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/design/features/course-centric-information-architecture-canonical-design-delta.md` |
| `docs/design/Local-Single-User-Identity-Authentication-Removal-Canonical-Design-Delta.md` | Feature Canonical Design | Canonical / Current | 长期维护 | 否 | `MOVE` | `docs/design/features/Local-Single-User-Identity-Authentication-Removal-Canonical-Design-Delta.md` |
| `docs/design/p1-03-data-control-and-recovery.md` | Feature Canonical Design | Canonical / Current | 长期维护 | 否 | `MOVE` | `docs/design/features/p1-03-data-control-and-recovery.md` |
| `docs/design/p1-06-fact-driven-first-use-journey.md` | Feature Canonical Design | Canonical / Current | 长期维护 | 否 | `MOVE` | `docs/design/features/p1-06-fact-driven-first-use-journey.md` |
| `docs/design/AI学习系统算法与教学内核设计.md` | Learning Core Canonical Design | Canonical / Current | 长期维护 | 否 | `MOVE` | `docs/design/learning/AI学习系统算法与教学内核设计.md` |
| `docs/design/v0.3-Canonical-Design-Delta.md` | Learning Core Canonical Design | Canonical / Current | 长期维护 | 否 | `MOVE` | `docs/design/learning/v0.3-Canonical-Design-Delta.md` |
| `docs/design/个人AI辅助学习平台设计方案.md` | Learning Core Canonical Design | Canonical / Current | 长期维护 | 否 | `MOVE` | `docs/design/learning/个人AI辅助学习平台设计方案.md` |
| `docs/product/PRODUCT-DEFINITION.md` | Product Definition | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/product/PRODUCT-DEFINITION.md` |
| `docs/product/PRODUCT-POSITIONING.md` | Product Positioning | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/product/PRODUCT-POSITIONING.md` |
| `docs/product/PRODUCT-STRATEGY.md` | Product Strategy | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/product/PRODUCT-STRATEGY.md` |
| `docs/product/README.md` | Product Index | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/product/README.md` |
| `docs/specs/README.md` | Implementation Spec Index | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/README.md` |
| `docs/specs/architecture/dependency-rules.md` | Architecture Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/architecture/dependency-rules.md` |
| `docs/specs/architecture/state-ownership.md` | Architecture Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/architecture/state-ownership.md` |
| `docs/specs/architecture/system-architecture.md` | Architecture Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/architecture/system-architecture.md` |
| `docs/specs/domain/decision-contract.md` | Domain Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/domain/decision-contract.md` |
| `docs/specs/domain/domain-model.md` | Domain Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/domain/domain-model.md` |
| `docs/specs/domain/event-contract.md` | Domain Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/domain/event-contract.md` |
| `docs/specs/domain/lifecycle-state-machines.md` | Domain Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/domain/lifecycle-state-machines.md` |
| `docs/specs/frontend/ui-read-model-contracts.md` | Frontend Technical Contract | Canonical / Current | 长期维护 | 否（唯一保留副本） | `KEEP` | `docs/specs/frontend/ui-read-model-contracts.md` |
| `docs/specs/ui/data-contracts.md` | 重复 Frontend Read-model Contract | Historical duplicate | 无独立保留价值 | 是（字节级完全重复） | `DELETE` | `docs/specs/frontend/ui-read-model-contracts.md` |
| `docs/specs/interfaces/api-contract.md` | Interface 与 Data Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/interfaces/api-contract.md` |
| `docs/specs/interfaces/content-ingestion-contract.md` | Interface 与 Data Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/interfaces/content-ingestion-contract.md` |
| `docs/specs/interfaces/data-control-contract.md` | Interface 与 Data Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/interfaces/data-control-contract.md` |
| `docs/specs/interfaces/error-contract.md` | Interface 与 Data Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/interfaces/error-contract.md` |
| `docs/specs/interfaces/learning-conversation-message-system-spec-delta.md` | Interface 与 Data Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/interfaces/learning-conversation-message-system-spec-delta.md` |
| `docs/specs/interfaces/material-lifecycle-contract.md` | Interface 与 Data Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/interfaces/material-lifecycle-contract.md` |
| `docs/specs/interfaces/onboarding-contract.md` | Interface 与 Data Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/interfaces/onboarding-contract.md` |
| `docs/specs/interfaces/persistence-contract.md` | Interface 与 Data Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/interfaces/persistence-contract.md` |
| `docs/specs/interfaces/recovery-contract.md` | Interface 与 Data Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/interfaces/recovery-contract.md` |
| `docs/specs/interfaces/render-content-contract.md` | Interface 与 Data Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/interfaces/render-content-contract.md` |
| `docs/specs/interfaces/schema-versioning.md` | Interface 与 Data Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/interfaces/schema-versioning.md` |
| `docs/specs/interfaces/user-note-source-inspection-contract.md` | Interface 与 Data Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/interfaces/user-note-source-inspection-contract.md` |
| `docs/specs/platform/identity-privacy-lifecycle.md` | Platform Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/platform/identity-privacy-lifecycle.md` |
| `docs/specs/platform/local-secret-store.md` | Platform Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/platform/local-secret-store.md` |
| `docs/specs/platform/workspace-project-session-scope.md` | Platform Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/platform/workspace-project-session-scope.md` |
| N/A (new) | Platform Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/platform/course-workspace-selection.md` |
| `docs/specs/quality/ci-infrastructure-standard.md` | Quality 与 Risk Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/quality/ci-infrastructure-standard.md` |
| `docs/specs/quality/definition-of-done.md` | Quality 与 Risk Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/quality/definition-of-done.md` |
| `docs/specs/quality/observability-standard.md` | Quality 与 Risk Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/quality/observability-standard.md` |
| `docs/specs/quality/security-standard.md` | Quality 与 Risk Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/quality/security-standard.md` |
| `docs/specs/quality/testing-standard.md` | Quality 与 Risk Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/quality/testing-standard.md` |
| `docs/specs/quality/v1-local-web-quality-reconciliation.md` | Quality 与 Risk Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/quality/v1-local-web-quality-reconciliation.md` |
| `docs/specs/systems/01-content-granularity.md` | Learning System Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/systems/01-content-granularity.md` |
| `docs/specs/systems/01-content-knowledge.md` | Learning System Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/systems/01-content-knowledge.md` |
| `docs/specs/systems/01-knowledge-publish-pipeline.md` | Learning System Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/systems/01-knowledge-publish-pipeline.md` |
| `docs/specs/systems/01-library-management.md` | Learning System Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/systems/01-library-management.md` |
| `docs/specs/systems/02-retrieval.md` | Learning System Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/systems/02-retrieval.md` |
| `docs/specs/systems/03-learner-model.md` | Learning System Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/systems/03-learner-model.md` |
| `docs/specs/systems/04-assessment.md` | Learning System Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/systems/04-assessment.md` |
| `docs/specs/systems/05-teaching-policy.md` | Learning System Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/systems/05-teaching-policy.md` |
| `docs/specs/systems/06-activity-lifecycle.md` | Learning System Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/systems/06-activity-lifecycle.md` |
| `docs/specs/systems/06-goal-knowledge-mapping.md` | Learning System Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/systems/06-goal-knowledge-mapping.md` |
| `docs/specs/systems/06-goal-management.md` | Learning System Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/systems/06-goal-management.md` |
| `docs/specs/systems/06-learning-planner.md` | Learning System Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/systems/06-learning-planner.md` |
| `docs/specs/systems/06-prerequisite-diagnostic-bootstrap.md` | Learning System Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/systems/06-prerequisite-diagnostic-bootstrap.md` |
| `docs/specs/systems/07-review-scheduler.md` | Learning System Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/systems/07-review-scheduler.md` |
| `docs/specs/systems/08-ai-orchestration.md` | Learning System Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/systems/08-ai-orchestration.md` |
| `docs/specs/systems/08-model-configuration.md` | Learning System Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/systems/08-model-configuration.md` |
| `docs/specs/ui/README.md` | UI 或 UX Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/ui/README.md` |
| `docs/specs/ui/design-system.md` | UI 或 UX Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/ui/design-system.md` |
| `docs/specs/ui/learning-interaction-contracts.md` | UI 或 UX Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/ui/learning-interaction-contracts.md` |
| `docs/specs/ui/quality-and-regression.md` | UI 或 UX Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/ui/quality-and-regression.md` |
| `docs/specs/ui/screen-and-navigation-contracts.md` | UI 或 UX Contract | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/ui/screen-and-navigation-contracts.md` |
| `docs/specs/vertical-slices/book-to-adaptive-learning.md` | Current Vertical Slice Spec | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/vertical-slices/book-to-adaptive-learning.md` |
| `docs/specs/vertical-slices/learning-conversation-message-system.md` | Current Vertical Slice Spec | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/vertical-slices/learning-conversation-message-system.md` |
| `docs/specs/vertical-slices/local-single-user-authentication-removal.md` | Current Vertical Slice Spec | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/vertical-slices/local-single-user-authentication-removal.md` |
| `docs/specs/vertical-slices/p1-01a-goal-definition-draft-replan.md` | Current Vertical Slice Spec | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/vertical-slices/p1-01a-goal-definition-draft-replan.md` |
| `docs/specs/vertical-slices/p1-01b-goal-lifecycle-achievement.md` | Current Vertical Slice Spec | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/vertical-slices/p1-01b-goal-lifecycle-achievement.md` |
| `docs/specs/vertical-slices/p1-03-data-control-recovery.md` | Current Vertical Slice Spec | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/vertical-slices/p1-03-data-control-recovery.md` |
| `docs/specs/vertical-slices/p1-06-first-use-onboarding.md` | Current Vertical Slice Spec | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/vertical-slices/p1-06-first-use-onboarding.md` |
| `docs/specs/vertical-slices/p1-07-error-recovery-center.md` | Current Vertical Slice Spec | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/vertical-slices/p1-07-error-recovery-center.md` |
| `docs/specs/vertical-slices/ui-04-ux-workspace-context.md` | Current Vertical Slice Spec | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/vertical-slices/ui-04-ux-workspace-context.md` |
| `docs/specs/vertical-slices/v0.3-adaptive-teaching-loop.md` | Current Vertical Slice Spec | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/vertical-slices/v0.3-adaptive-teaching-loop.md` |
| `docs/specs/vertical-slices/v0.3.1-rich-response-rendering.md` | Current Vertical Slice Spec | Canonical / Current | 长期维护 | 否 | `KEEP` | `docs/specs/vertical-slices/v0.3.1-rich-response-rendering.md` |

## Research

| Current Path | 文档性质 | 生命周期归属 | 长期/临时 | 是否重复 | 建议动作 | Target Path |
|---|---|---|---|---|---|---|
| `docs/research/README.md` | Research Index | Supporting Research | 长期研究资产 | 否 | `KEEP` | `docs/research/README.md` |
| `docs/design/research/README.md` | Learning Research Index | Supporting Research | 长期研究资产 | 否 | `MOVE` | `docs/research/learning-core/README.md` |
| `docs/design/research/evidence/八类技术系统-ITS与学习者建模证据.md` | Learning Research Evidence | Supporting Research | 长期研究资产 | 否 | `MOVE` | `docs/research/learning-core/evidence/八类技术系统-ITS与学习者建模证据.md` |
| `docs/design/research/evidence/八类技术系统-LLM-Agent与可信治理证据.md` | Learning Research Evidence | Supporting Research | 长期研究资产 | 否 | `MOVE` | `docs/research/learning-core/evidence/八类技术系统-LLM-Agent与可信治理证据.md` |
| `docs/design/research/evidence/八类技术系统-参考资料索引.md` | Learning Research Evidence | Supporting Research | 长期研究资产 | 否 | `MOVE` | `docs/research/learning-core/evidence/八类技术系统-参考资料索引.md` |
| `docs/design/research/evidence/八类技术系统-教学策略与序列决策证据.md` | Learning Research Evidence | Supporting Research | 长期研究资产 | 否 | `MOVE` | `docs/research/learning-core/evidence/八类技术系统-教学策略与序列决策证据.md` |
| `docs/design/research/evidence/八类技术系统-教育科学证据.md` | Learning Research Evidence | Supporting Research | 长期研究资产 | 否 | `MOVE` | `docs/research/learning-core/evidence/八类技术系统-教育科学证据.md` |
| `docs/design/research/evidence/八类技术系统-检索与知识架构证据.md` | Learning Research Evidence | Supporting Research | 长期研究资产 | 否 | `MOVE` | `docs/research/learning-core/evidence/八类技术系统-检索与知识架构证据.md` |
| `docs/design/research/evidence/八类技术系统-记忆与复习调度证据.md` | Learning Research Evidence | Supporting Research | 长期研究资产 | 否 | `MOVE` | `docs/research/learning-core/evidence/八类技术系统-记忆与复习调度证据.md` |
| `docs/design/research/synthesis/4.1-内容解析与知识建模-系统设计研究.md` | Learning Research Synthesis | Supporting Research | 长期研究资产 | 否 | `MOVE` | `docs/research/learning-core/synthesis/4.1-内容解析与知识建模-系统设计研究.md` |
| `docs/design/research/synthesis/4.2-检索与知识供给-系统设计研究.md` | Learning Research Synthesis | Supporting Research | 长期研究资产 | 否 | `MOVE` | `docs/research/learning-core/synthesis/4.2-检索与知识供给-系统设计研究.md` |
| `docs/design/research/synthesis/4.3-学习者建模-系统设计研究.md` | Learning Research Synthesis | Supporting Research | 长期研究资产 | 否 | `MOVE` | `docs/research/learning-core/synthesis/4.3-学习者建模-系统设计研究.md` |
| `docs/design/research/synthesis/4.4-评估与错误诊断-系统设计研究.md` | Learning Research Synthesis | Supporting Research | 长期研究资产 | 否 | `MOVE` | `docs/research/learning-core/synthesis/4.4-评估与错误诊断-系统设计研究.md` |
| `docs/design/research/synthesis/4.5-教学策略选择-系统设计研究.md` | Learning Research Synthesis | Supporting Research | 长期研究资产 | 否 | `MOVE` | `docs/research/learning-core/synthesis/4.5-教学策略选择-系统设计研究.md` |
| `docs/design/research/synthesis/4.6-学习路径与任务调度-系统设计研究.md` | Learning Research Synthesis | Supporting Research | 长期研究资产 | 否 | `MOVE` | `docs/research/learning-core/synthesis/4.6-学习路径与任务调度-系统设计研究.md` |
| `docs/design/research/synthesis/4.7-记忆保持与复习调度-系统设计研究.md` | Learning Research Synthesis | Supporting Research | 长期研究资产 | 否 | `MOVE` | `docs/research/learning-core/synthesis/4.7-记忆保持与复习调度-系统设计研究.md` |
| `docs/design/research/synthesis/4.8-LLM生成Agent编排与可信控制-系统设计研究.md` | Learning Research Synthesis | Supporting Research | 长期研究资产 | 否 | `MOVE` | `docs/research/learning-core/synthesis/4.8-LLM生成Agent编排与可信控制-系统设计研究.md` |
| `docs/design/research/synthesis/DR-03-01-教学策略与支架转换研究.md` | Learning Research Synthesis | Supporting Research | 长期研究资产 | 否 | `MOVE` | `docs/research/learning-core/synthesis/DR-03-01-教学策略与支架转换研究.md` |
| `docs/design/research/synthesis/DR-03-02-错误诊断到教学补救研究.md` | Learning Research Synthesis | Supporting Research | 长期研究资产 | 否 | `MOVE` | `docs/research/learning-core/synthesis/DR-03-02-错误诊断到教学补救研究.md` |
| `docs/design/research/synthesis/DR-03-03-Teaching-Policy-决策算法与数据契约研究.md` | Learning Research Synthesis | Supporting Research | 长期研究资产 | 否 | `MOVE` | `docs/research/learning-core/synthesis/DR-03-03-Teaching-Policy-决策算法与数据契约研究.md` |
| `docs/design/research/synthesis/DR-03-04-学习效果验证与产品实验研究.md` | Learning Research Synthesis | Supporting Research | 长期研究资产 | 否 | `MOVE` | `docs/research/learning-core/synthesis/DR-03-04-学习效果验证与产品实验研究.md` |
| `docs/design/research/synthesis/v0.3-Research-Synthesis-Adaptive-Teaching-Loop.md` | Learning Research Synthesis | Supporting Research | 长期研究资产 | 否 | `MOVE` | `docs/research/learning-core/synthesis/v0.3-Research-Synthesis-Adaptive-Teaching-Loop.md` |
| `docs/design/research/synthesis/v0.3-候选范围分析.md` | Learning Research Synthesis | Supporting Research | 长期研究资产 | 否 | `MOVE` | `docs/research/learning-core/synthesis/v0.3-候选范围分析.md` |
| `docs/design/research/synthesis/v0.3-深度研究议程.md` | Learning Research Synthesis | Supporting Research | 长期研究资产 | 否 | `MOVE` | `docs/research/learning-core/synthesis/v0.3-深度研究议程.md` |
| `docs/design/research/synthesis/八类技术系统-公共架构冻结稿.md` | Learning Research Synthesis | Supporting Research | 长期研究资产 | 否 | `MOVE` | `docs/research/learning-core/synthesis/八类技术系统-公共架构冻结稿.md` |
| `docs/design/research/synthesis/八类技术系统-现状诊断.md` | Learning Research Synthesis | Supporting Research | 长期研究资产 | 否 | `MOVE` | `docs/research/learning-core/synthesis/八类技术系统-现状诊断.md` |
| `docs/design/research/synthesis/八类技术系统-系统设计研究综合与溯源.md` | Learning Research Synthesis | Supporting Research | 长期研究资产 | 否 | `MOVE` | `docs/research/learning-core/synthesis/八类技术系统-系统设计研究综合与溯源.md` |
| `docs/research/product-strategy/ALTERNATIVES-OPPORTUNITY-RESEARCH.md` | Product Discovery Research | Supporting Research | 长期研究资产 | 否 | `MOVE` | `docs/research/product-discovery/ALTERNATIVES-OPPORTUNITY-RESEARCH.md` |
| `docs/research/product-strategy/DISCOVERY-EVIDENCE-SYNTHESIS.md` | Product Discovery Research | Supporting Research | 长期研究资产 | 否 | `MOVE` | `docs/research/product-discovery/DISCOVERY-EVIDENCE-SYNTHESIS.md` |
| `docs/research/product-strategy/PRIMARY-DISCOVERY-PROTOCOL.md` | Product Discovery Research | Supporting Research | 长期研究资产 | 否 | `MOVE` | `docs/research/product-discovery/PRIMARY-DISCOVERY-PROTOCOL.md` |
| `docs/research/product-strategy/USER-PROBLEM-JTBD-RESEARCH.md` | Product Discovery Research | Supporting Research | 长期研究资产 | 否 | `MOVE` | `docs/research/product-discovery/USER-PROBLEM-JTBD-RESEARCH.md` |

## Engineering / Planning / Governance

| Current Path | 文档性质 | 生命周期归属 | 长期/临时 | 是否重复 | 建议动作 | Target Path |
|---|---|---|---|---|---|---|
| `docs/CODE_WIKI.md` | Code Wiki 与 Engineering Guide | Current / Supporting | 长期维护 | 否 | `RENAME` | `docs/engineering/README.md` |
| N/A (new) | Documentation Governance | Current / Supporting | 长期维护 | 否 | `KEEP` | `docs/governance/README.md` |
| `docs/document-inventory.md` | Document Inventory | Current / Supporting | 长期维护 | 否 | `MOVE` | `docs/governance/document-inventory.md` |
| `docs/product-development-process.md` | Product Operations 与 Governance Process | Current / Supporting | 长期维护 | 否 | `MOVE` | `docs/governance/product-development-process.md` |
| `docs/exec-plans/README.md` | Active Planning Index | Current / Supporting | 长期维护 | 否 | `MOVE` | `docs/planning/README.md` |
| `docs/exec-plans/active/EXEC-046-ui-03d-settings-legacy-release-closure.md` | Active EXEC Contract | Active Planning Snapshot | 临时执行资产 | 否 | `MOVE` | `docs/planning/execs/EXEC-046-ui-03d-settings-legacy-release-closure.md` |
| `docs/exec-plans/active/EXEC-054-required-core-test-realignment.md` | Active EXEC Contract | Active Planning Snapshot | 临时执行资产 | 否 | `MOVE` | `docs/planning/execs/EXEC-054-required-core-test-realignment.md` |
| `docs/exec-plans/active/EXEC-055-local-data-migration-recovery-rebuild-gate.md` | Active EXEC Contract | Active Planning Snapshot | 临时执行资产 | 否 | `MOVE` | `docs/planning/execs/EXEC-055-local-data-migration-recovery-rebuild-gate.md` |
| `docs/exec-plans/active/EXEC-056-local-web-chromium-e2e.md` | Active EXEC Contract | Active Planning Snapshot | 临时执行资产 | 否 | `MOVE` | `docs/planning/execs/EXEC-056-local-web-chromium-e2e.md` |
| `docs/exec-plans/active/EXEC-057-ci-workflow-quality-supply-chain.md` | Active EXEC Contract | Active Planning Snapshot | 临时执行资产 | 否 | `MOVE` | `docs/planning/execs/EXEC-057-ci-workflow-quality-supply-chain.md` |
| `docs/exec-plans/active/EXEC-058-required-gate-main-protection-closure.md` | Active EXEC Contract | Active Planning Snapshot | 临时执行资产 | 否 | `MOVE` | `docs/planning/execs/EXEC-058-required-gate-main-protection-closure.md` |
| `docs/exec-plans/active/EXEC-059-ui-design-system-component-foundation.md` | Active EXEC Contract | Active Planning Snapshot | 临时执行资产 | 否 | `MOVE` | `docs/planning/execs/EXEC-059-ui-design-system-component-foundation.md` |
| `docs/exec-plans/active/EXEC-064-local-web-byok-secure-activation.md` | Active EXEC Contract | Active Planning Snapshot | 临时执行资产 | 否 | `MOVE` | `docs/planning/execs/EXEC-064-local-web-byok-secure-activation.md` |
| `docs/exec-plans/active/EXEC-066-v1-noncore-runtime-surface-cleanup.md` | Active EXEC Contract | Active Planning Snapshot | 临时执行资产 | 否 | `MOVE` | `docs/planning/execs/EXEC-066-v1-noncore-runtime-surface-cleanup.md` |
| `docs/exec-plans/active/EXEC-070-ui-04c-usernote-current-material-right-rail.md` | Active EXEC Contract | Active Planning Snapshot | 临时执行资产 | 否 | `MOVE` | `docs/planning/execs/EXEC-070-ui-04c-usernote-current-material-right-rail.md` |
| `docs/exec-plans/active/EXEC-071-ui-04d-learning-management-exposure-removal.md` | Active EXEC Contract | Active Planning Snapshot | 临时执行资产 | 否 | `MOVE` | `docs/planning/execs/EXEC-071-ui-04d-learning-management-exposure-removal.md` |
| `docs/exec-plans/active/EXEC-072-ui-04e-library-v1-no-ocr-exposure.md` | Active EXEC Contract | Active Planning Snapshot | 临时执行资产 | 否 | `MOVE` | `docs/planning/execs/EXEC-072-ui-04e-library-v1-no-ocr-exposure.md` |
| `docs/exec-plans/active/EXEC-073-ui-04f-responsive-accessibility-release-acceptance.md` | Active EXEC Contract | Active Planning Snapshot | 临时执行资产 | 否 | `MOVE` | `docs/planning/execs/EXEC-073-ui-04f-responsive-accessibility-release-acceptance.md` |
| N/A (new) | Active EXEC Contract | Active Planning Snapshot | 临时执行资产 | 否 | `KEEP` | `docs/planning/execs/EXEC-077-course-workspace-selection-platform.md` |
| `docs/exec-plans/CHAIN-A-UI-03-PROMPT.md` | Execution Prompt | Supporting / Transient | 临时执行资产 | 否 | `DELETE` | 用户确认移除，不建立长期目标路径 |
| `docs/exec-plans/CHAIN-B-CI-V2-PROMPT.md` | Execution Prompt | Supporting / Transient | 临时执行资产 | 否 | `DELETE` | 用户确认移除，不建立长期目标路径 |

## Archive

| Current Path | 文档性质 | 生命周期归属 | 长期/临时 | 是否重复 | 建议动作 | Target Path |
|---|---|---|---|---|---|---|
| N/A (new) | Archive Index | Historical / Superseded | 长期历史证据 | 否 | `KEEP` | `docs/archive/README.md` |
| `docs/design/CI-Test-Infrastructure-Gap-Analysis.md` | Historical Audit 或 Gap Analysis | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/audits/CI-Test-Infrastructure-Gap-Analysis.md` |
| `docs/product-gap-register-p1-p2.md` | Historical Audit 或 Gap Analysis | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/audits/product-gap-register-p1-p2.md` |
| `docs/specs/quality/test-oracle-classification.md` | Historical Audit 或 Gap Analysis | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/audits/quality/test-oracle-classification.md` |
| `docs/design/v0.3-Current-Main-Conformance-Gap-Analysis.md` | Historical Audit 或 Gap Analysis | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/audits/v0.3-Current-Main-Conformance-Gap-Analysis.md` |
| `docs/design/v1-Product-Positioning-Current-Main-Conformance-Gap-Analysis.md` | Historical Audit 或 Gap Analysis | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/audits/v1-Product-Positioning-Current-Main-Conformance-Gap-Analysis.md` |
| N/A (new) | Historical Audit 或 Gap Analysis | Historical Snapshot | 长期历史证据 | 否 | `KEEP` | `docs/archive/audits/course-centric-ia-current-state-gap-analysis.md` |
| `docs/design/Interactive-Element-System-Canonical-Design-Delta.md` | Superseded Design Record | Historical / Superseded | 长期历史证据 | 否（保留独立演进证据） | `ARCHIVE` | `docs/archive/design/Interactive-Element-System-Canonical-Design-Delta.md` |
| `docs/design/UX-Architecture-Canonical-Design-Delta.md` | Superseded Design Record | Historical / Superseded | 长期历史证据 | 否（保留独立演进证据） | `ARCHIVE` | `docs/archive/design/UX-Architecture-Canonical-Design-Delta.md` |
| `docs/design/p1-02-model-settings.md` | Superseded Design Record | Historical / Superseded | 长期历史证据 | 否（保留独立演进证据） | `ARCHIVE` | `docs/archive/design/p1-02-model-settings.md` |
| `docs/design/账号与隐私生命周期设计.md` | Superseded Design Record | Historical / Superseded | 长期历史证据 | 否（保留独立演进证据） | `ARCHIVE` | `docs/archive/design/账号与隐私生命周期设计.md` |
| `docs/exec-plans/completed/EXEC-001-contracts-event-outbox-foundation.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-001-contracts-event-outbox-foundation.md` |
| `docs/exec-plans/completed/EXEC-002-canonical-teaching-entry.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-002-canonical-teaching-entry.md` |
| `docs/exec-plans/completed/EXEC-003-content-evidence-bundle.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-003-content-evidence-bundle.md` |
| `docs/exec-plans/completed/EXEC-004-assessment-learner-projection.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-004-assessment-learner-projection.md` |
| `docs/exec-plans/completed/EXEC-005-review-planner-integration.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-005-review-planner-integration.md` |
| `docs/exec-plans/completed/EXEC-006-v0.2-e2e-quality-gate.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-006-v0.2-e2e-quality-gate.md` |
| `docs/exec-plans/completed/EXEC-007-v0.3-governance-preconditions.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-007-v0.3-governance-preconditions.md` |
| `docs/exec-plans/completed/EXEC-008-v0.3-contracts-schema-migration.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-008-v0.3-contracts-schema-migration.md` |
| `docs/exec-plans/completed/EXEC-009-deterministic-teaching-policy-kernel.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-009-deterministic-teaching-policy-kernel.md` |
| `docs/exec-plans/completed/EXEC-010-adaptive-transition-anti-oscillation.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-010-adaptive-transition-anti-oscillation.md` |
| `docs/exec-plans/completed/EXEC-011-cross-system-adaptive-execution.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-011-cross-system-adaptive-execution.md` |
| `docs/exec-plans/completed/EXEC-012-outcome-experiment-opve-foundation.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-012-outcome-experiment-opve-foundation.md` |
| `docs/exec-plans/completed/EXEC-013-v0.3-e2e-release-gate.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-013-v0.3-e2e-release-gate.md` |
| `docs/exec-plans/completed/EXEC-014-rich-response-rendering.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-014-rich-response-rendering.md` |
| `docs/exec-plans/completed/EXEC-015-ui-01-learning-shell-workspace.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-015-ui-01-learning-shell-workspace.md` |
| `docs/exec-plans/completed/EXEC-016-ui-02a-library-knowledge-map.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-016-ui-02a-library-knowledge-map.md` |
| `docs/exec-plans/completed/EXEC-017-structure-preserving-epub-ingestion.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-017-structure-preserving-epub-ingestion.md` |
| `docs/exec-plans/completed/EXEC-018-multi-granularity-content-projections.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-018-multi-granularity-content-projections.md` |
| `docs/exec-plans/completed/EXEC-019-knowledge-verification-publication.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-019-knowledge-verification-publication.md` |
| `docs/exec-plans/completed/EXEC-020-retrieval-projection-sys02-binding.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-020-retrieval-projection-sys02-binding.md` |
| `docs/exec-plans/completed/EXEC-021-learning-goal-knowledge-mapping.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-021-learning-goal-knowledge-mapping.md` |
| `docs/exec-plans/completed/EXEC-022-prerequisite-diagnostic-planner-bootstrap.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-022-prerequisite-diagnostic-planner-bootstrap.md` |
| `docs/exec-plans/completed/EXEC-023-book-learning-orchestration-api.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-023-book-learning-orchestration-api.md` |
| `docs/exec-plans/completed/EXEC-024-book-to-learning-e2e-release-gate.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-024-book-to-learning-e2e-release-gate.md` |
| `docs/exec-plans/completed/EXEC-025-ui-02b1-material-learning-launch.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-025-ui-02b1-material-learning-launch.md` |
| `docs/exec-plans/completed/EXEC-026-ui-02b2-guided-book-learning.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-026-ui-02b2-guided-book-learning.md` |
| `docs/exec-plans/completed/EXEC-027-ui-02b3-real-model-e2e.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-027-ui-02b3-real-model-e2e.md` |
| `docs/exec-plans/completed/EXEC-028-zhipu-development-model.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-028-zhipu-development-model.md` |
| `docs/exec-plans/completed/EXEC-029-ui-02b-goals-path-evidence.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-029-ui-02b-goals-path-evidence.md` |
| `docs/exec-plans/completed/EXEC-030-ui-02c-canonical-activity-lifecycle.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-030-ui-02c-canonical-activity-lifecycle.md` |
| `docs/exec-plans/completed/EXEC-031-p1-04a-library-organization.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-031-p1-04a-library-organization.md` |
| `docs/exec-plans/completed/EXEC-032-p1-04b-library-deduplication.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-032-p1-04b-library-deduplication.md` |
| `docs/exec-plans/completed/EXEC-033-p1-04c-library-ocr-review.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-033-p1-04c-library-ocr-review.md` |
| `docs/exec-plans/completed/EXEC-034-identity-session-foundation.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-034-identity-session-foundation.md` |
| `docs/exec-plans/completed/EXEC-035-local-account-recovery.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-035-local-account-recovery.md` |
| `docs/exec-plans/completed/EXEC-036-account-deletion-erasure.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-036-account-deletion-erasure.md` |
| `docs/exec-plans/completed/EXEC-037-p1-05-p1-03-erasure-integration.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-037-p1-05-p1-03-erasure-integration.md` |
| `docs/exec-plans/completed/EXEC-037-p1-07-error-recovery-center.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-037-p1-07-error-recovery-center.md` |
| `docs/exec-plans/completed/EXEC-038-p1-01a-goal-definition-draft-replan.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-038-p1-01a-goal-definition-draft-replan.md` |
| `docs/exec-plans/completed/EXEC-039-p1-01b-goal-lifecycle-achievement.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-039-p1-01b-goal-lifecycle-achievement.md` |
| `docs/exec-plans/completed/EXEC-040-p1-02a-model-configuration-foundation.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-040-p1-02a-model-configuration-foundation.md` |
| `docs/exec-plans/completed/EXEC-041-p1-02b-model-settings-product-closure.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-041-p1-02b-model-settings-product-closure.md` |
| `docs/exec-plans/completed/EXEC-042-v0.3-production-sequential-teaching-policy-closure.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-042-v0.3-production-sequential-teaching-policy-closure.md` |
| `docs/exec-plans/completed/EXEC-043-ui-03a-shell-routes-learning-domain.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-043-ui-03a-shell-routes-learning-domain.md` |
| `docs/exec-plans/completed/EXEC-044-ui-03b-today-primary-hierarchy.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-044-ui-03b-today-primary-hierarchy.md` |
| `docs/exec-plans/active/EXEC-045-ui-03c-library-progressive-disclosure.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-045-ui-03c-library-progressive-disclosure.md` |
| `docs/exec-plans/completed/EXEC-047-local-owner-foundation-migration.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-047-local-owner-foundation-migration.md` |
| `docs/exec-plans/completed/EXEC-048-backend-no-auth-loopback-cutover.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-048-backend-no-auth-loopback-cutover.md` |
| `docs/exec-plans/completed/EXEC-049-frontend-settings-onboarding-deaccounting.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-049-frontend-settings-onboarding-deaccounting.md` |
| `docs/exec-plans/completed/EXEC-050-auth-persistence-configuration-cleanup.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-050-auth-persistence-configuration-cleanup.md` |
| `docs/exec-plans/completed/EXEC-051-local-identity-release-closure.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-051-local-identity-release-closure.md` |
| `docs/exec-plans/completed/EXEC-052-ci-governance-test-oracle-classification.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-052-ci-governance-test-oracle-classification.md` |
| `docs/exec-plans/completed/EXEC-053-production-local-runtime-cutover.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-053-production-local-runtime-cutover.md` |
| `docs/exec-plans/active/EXEC-060-v1-standalone-local-runtime-closure.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-060-v1-standalone-local-runtime-closure.md` |
| `docs/exec-plans/active/EXEC-061-workspace-project-session-persistence-migration.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-061-workspace-project-session-persistence-migration.md` |
| `docs/exec-plans/completed/EXEC-062-EXECUTION-REPORT.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-062-EXECUTION-REPORT.md` |
| `docs/exec-plans/active/EXEC-062-workspace-scoped-learner-state-projection.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-062-workspace-scoped-learner-state-projection.md` |
| `docs/exec-plans/active/EXEC-063-workspace-scoped-retrieval-cutover.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-063-workspace-scoped-retrieval-cutover.md` |
| `docs/exec-plans/active/EXEC-065-material-trash-restore-permanent-delete.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-065-material-trash-restore-permanent-delete.md` |
| `docs/exec-plans/active/EXEC-067-v1-product-positioning-conformance-release-gate.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-067-v1-product-positioning-conformance-release-gate.md` |
| `docs/exec-plans/completed/EXEC-068-ui-04a-workspace-context-shell-routes.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-068-ui-04a-workspace-context-shell-routes.md` |
| `docs/exec-plans/completed/EXEC-069-ui-04b-learning-context-drawer.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-069-ui-04b-learning-context-drawer.md` |
| `docs/exec-plans/completed/EXEC-074-postgresql-membership-constraint-reconciliation.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-074-postgresql-membership-constraint-reconciliation.md` |
| `docs/exec-plans/completed/EXEC-075-learning-conversation-message-system-vertical-slice.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-075-learning-conversation-message-system-vertical-slice.md` |
| `docs/exec-plans/completed/EXEC-1031-p1-03-recovery-foundation.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-1031-p1-03-recovery-foundation.md` |
| `docs/exec-plans/completed/EXEC-1032-p1-03-verified-restore.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-1032-p1-03-verified-restore.md` |
| `docs/exec-plans/completed/EXEC-1033-p1-03-user-data-export.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-1033-p1-03-user-data-export.md` |
| `docs/exec-plans/completed/EXEC-1034-p1-03-erasure-ui-release.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-1034-p1-03-erasure-ui-release.md` |
| `docs/exec-plans/completed/EXEC-1061-p1-06a-onboarding-readiness-foundation.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-1061-p1-06a-onboarding-readiness-foundation.md` |
| `docs/exec-plans/completed/EXEC-1062-p1-06b-onboarding-product-closure.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/EXEC-1062-p1-06b-onboarding-product-closure.md` |
| `docs/exec-plans/completed/README.md` | Completed 或 Superseded EXEC Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/exec-plans/README.md` |
| `docs/releases/README.md` | Release 或 Conformance Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/releases/README.md` |
| `docs/releases/book-to-adaptive-learning.md` | Release 或 Conformance Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/releases/book-to-adaptive-learning.md` |
| `exec-report-XIK-176-v1-product-positioning-conformance.md` | Release 或 Conformance Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/releases/exec-report-XIK-176-v1-product-positioning-conformance.md` |
| `docs/releases/p1-01a-goal-definition-draft-replan.md` | Release 或 Conformance Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/releases/p1-01a-goal-definition-draft-replan.md` |
| `docs/releases/p1-01b-goal-lifecycle-achievement.md` | Release 或 Conformance Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/releases/p1-01b-goal-lifecycle-achievement.md` |
| `docs/releases/p1-02-model-settings.md` | Release 或 Conformance Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/releases/p1-02-model-settings.md` |
| `docs/releases/p1-03-data-control-recovery.md` | Release 或 Conformance Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/releases/p1-03-data-control-recovery.md` |
| `docs/releases/p1-04-library-management.md` | Release 或 Conformance Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/releases/p1-04-library-management.md` |
| `docs/releases/p1-05-account-lifecycle.md` | Release 或 Conformance Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/releases/p1-05-account-lifecycle.md` |
| `docs/releases/p1-06-first-use-onboarding.md` | Release 或 Conformance Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/releases/p1-06-first-use-onboarding.md` |
| `docs/releases/p1-07-error-recovery-center.md` | Release 或 Conformance Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/releases/p1-07-error-recovery-center.md` |
| `docs/releases/ui-01-learning-shell-workspace.md` | Release 或 Conformance Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/releases/ui-01-learning-shell-workspace.md` |
| `docs/releases/ui-02a-library-knowledge-map.md` | Release 或 Conformance Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/releases/ui-02a-library-knowledge-map.md` |
| `docs/releases/ui-02b-goals-path-evidence.md` | Release 或 Conformance Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/releases/ui-02b-goals-path-evidence.md` |
| `docs/releases/ui-02b1-material-learning-launch.md` | Release 或 Conformance Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/releases/ui-02b1-material-learning-launch.md` |
| `docs/releases/ui-02b2-guided-book-learning.md` | Release 或 Conformance Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/releases/ui-02b2-guided-book-learning.md` |
| `docs/releases/ui-02b3-real-model-guided-learning.md` | Release 或 Conformance Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/releases/ui-02b3-real-model-guided-learning.md` |
| `docs/releases/ui-02c-canonical-activity-lifecycle.md` | Release 或 Conformance Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/releases/ui-02c-canonical-activity-lifecycle.md` |
| `docs/releases/v0.2-first-vertical-learning-loop.md` | Release 或 Conformance Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/releases/v0.2-first-vertical-learning-loop.md` |
| `docs/releases/v0.3-adaptive-teaching-loop.md` | Release 或 Conformance Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/releases/v0.3-adaptive-teaching-loop.md` |
| `docs/releases/v0.3-governance-preconditions.md` | Release 或 Conformance Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/releases/v0.3-governance-preconditions.md` |
| `docs/releases/v0.3-production-sequential-policy-closure.md` | Release 或 Conformance Evidence | Historical / Superseded | 长期历史证据 | 否 | `ARCHIVE` | `docs/archive/releases/v0.3-production-sequential-policy-closure.md` |
| `docs/specs/ui/component-state-contracts.md` | UI 或 UX Contract | Historical / Superseded | 长期历史证据 | 否（保留独立演进证据） | `ARCHIVE` | `docs/archive/specs/ui/component-state-contracts.md` |
| `docs/specs/ui/information-architecture.md` | UI 或 UX Contract | Historical / Superseded | 长期历史证据 | 否（保留独立演进证据） | `ARCHIVE` | `docs/archive/specs/ui/information-architecture.md` |
| `docs/specs/ui/interactive-element-system.md` | UI 或 UX Contract | Historical / Superseded | 长期历史证据 | 否（保留独立演进证据） | `ARCHIVE` | `docs/archive/specs/ui/interactive-element-system.md` |
| `docs/specs/ui/quality-and-migration.md` | UI 或 UX Contract | Historical / Superseded | 长期历史证据 | 否（保留独立演进证据） | `ARCHIVE` | `docs/archive/specs/ui/quality-and-migration.md` |
| `docs/specs/ui/screen-contracts.md` | UI 或 UX Contract | Historical / Superseded | 长期历史证据 | 否（保留独立演进证据） | `ARCHIVE` | `docs/archive/specs/ui/screen-contracts.md` |
| `docs/specs/ui/visual-system.md` | UI 或 UX Contract | Historical / Superseded | 长期历史证据 | 否（保留独立演进证据） | `ARCHIVE` | `docs/archive/specs/ui/visual-system.md` |
| `docs/specs/vertical-slices/p1-02-model-settings.md` | Current Vertical Slice Spec | Historical / Superseded | 长期历史证据 | 否（保留独立演进证据） | `ARCHIVE` | `docs/archive/specs/vertical-slices/p1-02-model-settings.md` |
| `docs/specs/vertical-slices/p1-04a-library-organization.md` | Current Vertical Slice Spec | Historical / Superseded | 长期历史证据 | 否（保留独立演进证据） | `ARCHIVE` | `docs/archive/specs/vertical-slices/p1-04a-library-organization.md` |
| `docs/specs/vertical-slices/p1-04b-library-deduplication.md` | Current Vertical Slice Spec | Historical / Superseded | 长期历史证据 | 否（保留独立演进证据） | `ARCHIVE` | `docs/archive/specs/vertical-slices/p1-04b-library-deduplication.md` |
| `docs/specs/vertical-slices/p1-04c-library-ocr-review.md` | Current Vertical Slice Spec | Historical / Superseded | 长期历史证据 | 否（保留独立演进证据） | `ARCHIVE` | `docs/archive/specs/vertical-slices/p1-04c-library-ocr-review.md` |
| `docs/specs/vertical-slices/p1-05-account-lifecycle.md` | Current Vertical Slice Spec | Historical / Superseded | 长期历史证据 | 否（保留独立演进证据） | `ARCHIVE` | `docs/archive/specs/vertical-slices/p1-05-account-lifecycle.md` |
| `docs/specs/vertical-slices/ui-01-learning-shell-workspace.md` | Current Vertical Slice Spec | Historical / Superseded | 长期历史证据 | 否（保留独立演进证据） | `ARCHIVE` | `docs/archive/specs/vertical-slices/ui-01-learning-shell-workspace.md` |
| `docs/specs/vertical-slices/ui-02a-library-knowledge-map.md` | Current Vertical Slice Spec | Historical / Superseded | 长期历史证据 | 否（保留独立演进证据） | `ARCHIVE` | `docs/archive/specs/vertical-slices/ui-02a-library-knowledge-map.md` |
| `docs/specs/vertical-slices/ui-02b-goals-path-evidence.md` | Current Vertical Slice Spec | Historical / Superseded | 长期历史证据 | 否（保留独立演进证据） | `ARCHIVE` | `docs/archive/specs/vertical-slices/ui-02b-goals-path-evidence.md` |
| `docs/specs/vertical-slices/ui-02b1-material-learning-launch.md` | Current Vertical Slice Spec | Historical / Superseded | 长期历史证据 | 否（保留独立演进证据） | `ARCHIVE` | `docs/archive/specs/vertical-slices/ui-02b1-material-learning-launch.md` |
| `docs/specs/vertical-slices/ui-02b2-guided-book-learning.md` | Current Vertical Slice Spec | Historical / Superseded | 长期历史证据 | 否（保留独立演进证据） | `ARCHIVE` | `docs/archive/specs/vertical-slices/ui-02b2-guided-book-learning.md` |
| `docs/specs/vertical-slices/ui-02b3-real-model-guided-learning.md` | Current Vertical Slice Spec | Historical / Superseded | 长期历史证据 | 否（保留独立演进证据） | `ARCHIVE` | `docs/archive/specs/vertical-slices/ui-02b3-real-model-guided-learning.md` |
| `docs/specs/vertical-slices/ui-02c-canonical-activity-lifecycle.md` | Current Vertical Slice Spec | Historical / Superseded | 长期历史证据 | 否（保留独立演进证据） | `ARCHIVE` | `docs/archive/specs/vertical-slices/ui-02c-canonical-activity-lifecycle.md` |
| `docs/specs/vertical-slices/ui-03-interactive-element-system-refactor.md` | Current Vertical Slice Spec | Historical / Superseded | 长期历史证据 | 否（保留独立演进证据） | `ARCHIVE` | `docs/archive/specs/vertical-slices/ui-03-interactive-element-system-refactor.md` |
| `docs/specs/vertical-slices/v0.2-learning-loop.md` | Current Vertical Slice Spec | Historical / Superseded | 长期历史证据 | 否（保留独立演进证据） | `ARCHIVE` | `docs/archive/specs/vertical-slices/v0.2-learning-loop.md` |

## Repository / Support / Review

| Current Path | 文档性质 | 生命周期归属 | 长期/临时 | 是否重复 | 建议动作 | Target Path |
|---|---|---|---|---|---|---|
| `.design_library/Askora/README.md` | 设计辅助资产 | Supporting Asset | 长期维护 | 否 | `KEEP` | `.design_library/Askora/README.md` |
| `.design_library/Askora/SKILL.md` | 设计辅助资产 | Supporting Asset | 长期维护 | 否 | `KEEP` | `.design_library/Askora/SKILL.md` |
| `.github/PULL_REQUEST_TEMPLATE.md` | Delivery 与 Review 合同 | Current / Supporting | 长期维护 | 否 | `KEEP` | `.github/PULL_REQUEST_TEMPLATE.md` |
| `AGENTS.md` | Agent 执行合同 | Current / Supporting | 长期维护 | 否 | `KEEP` | `AGENTS.md` |
| `Professional App Development Framework.md` | 仓库外工作稿或执行快照 | REVIEW / 未纳入治理链 | 临时或待确认 | 否 | `REVIEW` | `Professional App Development Framework.md` |
| `README.md` | Repository 入口 | Current / Supporting | 长期维护 | 否 | `KEEP` | `README.md` |
| `apps/backend/README.md` | 模块工程指南 | Current / Supporting | 长期维护 | 否 | `KEEP` | `apps/backend/README.md` |
| `apps/backend/data/documents/user_pseudo_001/6dcb2a02-322a-4e35-b33a-54708b8d5904_3673b0a7.md` | 测试夹具或种子数据 | Test Input | 长期维护 | 否 | `KEEP` | `apps/backend/data/documents/user_pseudo_001/6dcb2a02-322a-4e35-b33a-54708b8d5904_3673b0a7.md` |
| `apps/backend/tests/fixtures/malicious_document.md` | 测试夹具或种子数据 | Test Input | 长期维护 | 否 | `KEEP` | `apps/backend/tests/fixtures/malicious_document.md` |
| `apps/frontend/README.md` | 模块工程指南 | Current / Supporting | 长期维护 | 否 | `KEEP` | `apps/frontend/README.md` |
| `askora-learning-conversation-message-system-canonical-design.md` | 仓库外工作稿或执行快照 | REVIEW / 未纳入治理链 | 临时或待确认 | 否 | `REVIEW` | `askora-learning-conversation-message-system-canonical-design.md` |
| `design-recommendations.md` | 仓库外工作稿或执行快照 | REVIEW / 未纳入治理链 | 临时或待确认 | 否 | `REVIEW` | `design-recommendations.md` |
| `docs/adr/ADR-0021-user-note-and-source-inspection-boundary.md` | Architecture Decision Record | Canonical / Current | 长期维护 | 否 | `MOVE` | `docs/architecture/decisions/ADR-0021-user-note-and-source-inspection-boundary.md` |
| `exec-report-XIK-174-EXEC-065.md` | 仓库外工作稿或执行快照 | REVIEW / 未纳入治理链 | 临时或待确认 | 否 | `REVIEW` | `exec-report-XIK-174-EXEC-065.md` |

## 判定说明

- `KEEP`：内容职责与目标路径一致；只可能修复导航或链接。
- `MOVE` / `RENAME`：内容保持原义，通过 `git mv` 迁入唯一职责目录。
- `ARCHIVE`：仍有审计、迁移或演进价值，但不应继续成为 current 实现入口。
- `DELETE`：用于已确认的字节级完全重复，或用户明确确认移除的临时执行资产；重复合同的保留副本是 `docs/specs/frontend/ui-read-model-contracts.md`，删除内容均可由 Git 恢复。
- `REVIEW`：工作稿或本地执行快照未进入正式治理链；本任务不猜测其 authority，也不移动用户资产。

## Maintenance

新增、移动、归档或删除文档时，必须同步本表并运行：

```bash
python3 .github/workflows/check_docs.py
git diff --check
```
