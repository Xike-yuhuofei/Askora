# Askora Docs 重构 — 逐文件迁移映射表

> 状态：Phase 1 交付物（冻结）
> 依据：`docs/REFACTOR-PLAN.md`（推倒重建方案，用户已确认）
> 覆盖范围：当前 `docs/` 全部决策/规范类文档
> 处置类型：`KEEP`（保留不动）| `MERGE`（合并进目标）| `ARCHIVE`（git mv 归档）| `DELETED`（已确认删除，不恢复）

---

## 一、决策层（Phase 2 处理）

### ADR 原文（26 个 → ARCHIVE `docs/archive/adr/`）

| 当前路径（`docs/architecture/decisions/`） | 处置 | 目标路径 |
|---|---|---|
| ADR-0001-teaching-strategy-ontology.md | ARCHIVE | archive/adr/ADR-0001-teaching-strategy-ontology.md |
| ADR-0002-constrained-deterministic-teaching-policy-architecture.md | ARCHIVE | archive/adr/ 同名 |
| ADR-0003-policy-runtime-profile-source-and-activation.md | ARCHIVE | archive/adr/ 同名 |
| ADR-0004-guided-book-learning-and-durable-transcript.md | ARCHIVE | archive/adr/ 同名 |
| ADR-0005-policy-bound-real-model-rendering.md | ARCHIVE | archive/adr/ 同名 |
| ADR-0006-workspace-read-model-scope-and-missing-objective-metadata.md | ARCHIVE | archive/adr/ 同名 |
| ADR-0007-sys06-activity-lifecycle-and-completion.md | ARCHIVE | archive/adr/ 同名 |
| ADR-0008-library-management-deduplication-and-ocr.md | ARCHIVE | archive/adr/ 同名 |
| ADR-0009-local-first-identity-privacy-lifecycle.md | ARCHIVE | archive/adr/ 同名 |
| ADR-0010-goal-definition-state-draft-and-replan.md | ARCHIVE | archive/adr/ 同名 |
| ADR-0011-goal-achievement-measurement-and-evidence-gate.md | ARCHIVE | archive/adr/ 同名 |
| ADR-0012-unified-recovery-control-plane.md | ARCHIVE | archive/adr/ 同名 |
| ADR-0013-desktop-model-credential-and-activation.md | ARCHIVE | archive/adr/ 同名 |
| ADR-0014-user-job-driven-interaction-architecture.md | ARCHIVE | archive/adr/ 同名 |
| ADR-0015-local-single-user-identity-without-authentication.md | ARCHIVE | archive/adr/ 同名 |
| ADR-0016-workspace-project-and-learning-session-scope-ownership.md | ARCHIVE | archive/adr/ 同名 |
| ADR-0017-os-backed-local-secret-store-and-crash-consistent-model-activation.md | ARCHIVE | archive/adr/ 同名 |
| ADR-0018-ux-workspace-context-architecture.md | ARCHIVE | archive/adr/ 同名 |
| ADR-0019-ui-workspace-read-projections.md | ARCHIVE | archive/adr/ 同名 |
| ADR-0020-learning-conversation-message-presentation-and-interaction-boundary.md | ARCHIVE | archive/adr/ 同名 |
| ADR-0021-user-note-and-source-inspection-boundary.md | ARCHIVE | archive/adr/ 同名 |
| ADR-0022-course-centric-information-architecture.md | ARCHIVE | archive/adr/ 同名 |
| ADR-0023-course-workspace-selection-and-activity-projection.md | ARCHIVE | archive/adr/ 同名 |
| ADR-0103-local-data-recovery-portability-erasure.md | ARCHIVE | archive/adr/ 同名 |
| ADR-0106-fact-driven-onboarding-readiness-and-preferences.md | ARCHIVE | archive/adr/ 同名 |
| ADR-0107-account-deletion-erasure-workflow-integration.md | ARCHIVE | archive/adr/ 同名 |

### 决策权威视图（新建）

| 路径 | 处置 |
|---|---|
| `docs/decisions/DECISIONS.md` | 新建：decision log（当前有效决策 + Part B 历史废止索引） |
| `docs/architecture/README.md` | 重写：从 26 条 ADR + supersession matrix 索引，降级为"决策日志入口 + 何时新建 ADR + ADR 模板" |

---

## 二、规范层（Phase 3 处理）

### systems（16 → 8 份，目标在 `docs/specs/systems/`）

| 源文件 | 处置 | 目标 |
|---|---|---|
| 01-content-knowledge.md | MERGE（主文件） | systems/01-content-knowledge.md |
| 01-library-management.md | MERGE 进 01-content-knowledge，原文 ARCHIVE | archive/specs/systems/ |
| 01-content-granularity.md | MERGE 进 01-content-knowledge，原文 ARCHIVE | archive/specs/systems/ |
| 01-knowledge-publish-pipeline.md | MERGE 进 01-content-knowledge，原文 ARCHIVE | archive/specs/systems/ |
| 02-retrieval.md | KEEP（目标同名） | systems/02-retrieval.md |
| 03-learner-model.md | KEEP（目标同名） | systems/03-learner-model.md |
| 04-assessment.md | KEEP（目标同名） | systems/04-assessment.md |
| 05-teaching-policy.md | KEEP（目标同名） | systems/05-teaching-policy.md |
| 06-learning-planner.md | MERGE（主文件） | systems/06-learning-planner.md |
| 06-goal-management.md | MERGE 进 06-learning-planner，原文 ARCHIVE | archive/specs/systems/ |
| 06-goal-knowledge-mapping.md | MERGE 进 06-learning-planner，原文 ARCHIVE | archive/specs/systems/ |
| 06-prerequisite-diagnostic-bootstrap.md | MERGE 进 06-learning-planner，原文 ARCHIVE | archive/specs/systems/ |
| 06-activity-lifecycle.md | MERGE 进 06-learning-planner，原文 ARCHIVE | archive/specs/systems/ |
| 07-review-scheduler.md | KEEP（目标同名） | systems/07-review-scheduler.md |
| 08-ai-orchestration.md | MERGE（主文件） | systems/08-ai-orchestration.md |
| 08-model-configuration.md | MERGE 进 08-ai-orchestration，原文 ARCHIVE | archive/specs/systems/ |

### 跨切面（合并为单文件）

| 源目录 | 源文件 | 目标 |
|---|---|---|
| domain/ | domain-model.md（主）+ decision-contract.md + event-contract.md + lifecycle-state-machines.md | `specs/domain.md`；其余 3 份原文 ARCHIVE → `archive/specs/domain/` |
| architecture/ | system-architecture.md（主）+ state-ownership.md + dependency-rules.md | `specs/architecture.md`；其余 2 份 ARCHIVE → `archive/specs/architecture/` |
| platform/ | identity-privacy-lifecycle.md（主）+ workspace-project-session-scope.md + course-workspace-selection.md + local-secret-store.md | `specs/platform.md`；其余 3 份 ARCHIVE → `archive/specs/platform/` |
| quality/ | testing-standard.md（主）+ ci-infrastructure-standard.md + v1-local-web-quality-reconciliation.md + observability-standard.md + definition-of-done.md + security-standard.md | `specs/quality.md`；其余 5 份 ARCHIVE → `archive/specs/quality/` |
| ui/ | design-system.md（主）+ learning-interaction-contracts.md + quality-and-regression.md + screen-and-navigation-contracts.md + README.md | `specs/ui.md`；其余 4 份 ARCHIVE → `archive/specs/ui/` |
| frontend/ | ui-read-model-contracts.md | MERGE 进 `specs/ui.md`，原文 ARCHIVE → `archive/specs/frontend/` |

### interfaces（12 → 5 份，目标在 `docs/specs/interfaces/`）

| 目标文件 | 吸收源文件（其余原文 ARCHIVE → `archive/specs/interfaces/`） |
|---|---|
| api.md | api-contract.md（主）+ error-contract.md + schema-versioning.md |
| persistence-and-data-control.md | persistence-contract.md（主）+ material-lifecycle-contract.md + data-control-contract.md |
| content.md | content-ingestion-contract.md（主）+ render-content-contract.md |
| message-and-note.md | learning-conversation-message-system-spec-delta.md（主）+ user-note-source-inspection-contract.md |
| recovery-and-onboarding.md | recovery-contract.md（主）+ onboarding-contract.md |

### vertical-slices（11 份 → ARCHIVE）

| 源 | 处置 |
|---|---|
| specs/vertical-slices/*.md（全部 11 份） | ARCHIVE → `archive/specs/vertical-slices/`（current 语义已进 systems/interfaces/ui） |

---

## 三、设计层（Phase 3/4 处理）

| 路径 | 处置 | 目标 |
|---|---|---|
| design/learning/AI学习系统算法与教学内核设计.md | ARCHIVE | archive/design/ 同名 |
| design/learning/v0.3-Canonical-Design-Delta.md | ARCHIVE | archive/design/ 同名 |
| design/learning/个人AI辅助学习平台设计方案.md | ARCHIVE | archive/design/ 同名 |
| design/experience/EXPERIENCE-ARCHITECTURE.md | KEEP | 不动 |
| design/experience/INTERACTION-MODEL.md | KEEP | 不动 |
| design/experience/LEARNING-EXPERIENCE.md | KEEP | 不动 |
| design/README.md | 降级：移除对已归档文件/features 的引用 | 保留为 experience 索引 |

---

## 四、产品层（KEEP）

| 路径 | 处置 |
|---|---|
| product/PRODUCT-STRATEGY.md / PRODUCT-POSITIONING.md / PRODUCT-DEFINITION.md / README.md | KEEP（authority 顶端，不动） |

---

## 五、其他目录

| 路径 | 处置 |
|---|---|
| research/**（全部） | KEEP（支持证据，不动） |
| ui-reverse-engineering/**（全部） | KEEP（外部 UI 逆向证据，不动） |
| planning/README.md + planning/execs/EXEC-0*.md（14 个） | DELETED（用户已确认保留删除，不恢复） |
| engineering/README.md | DELETED（用户已确认保留删除，不恢复） |

---

## 六、新增文件汇总

| 新文件 | 内容 |
|---|---|
| docs/decisions/DECISIONS.md | decision log：当前有效决策（Part A）+ 历史废止索引（Part B） |
| docs/specs/architecture.md / domain.md / platform.md / quality.md / ui.md | 合并后的跨切面规范 |
| docs/specs/interfaces/{api,persistence-and-data-control,content,message-and-note,recovery-and-onboarding}.md | 合并后的接口规范 |
| docs/REFACTOR-MAPPING.md | 本映射表（重构完成后归档或删除） |

## 七、合并纪律

1. 所有移动使用 `git mv`（保留 git 历史），禁止"复制 + 删除"；
2. 合并时保留源文件内的 requirement ID（`LID-* / WSP-* / LSS-* / MATLIFE-* / API-* / UI-*` 等）原样，不改条款编号；
3. 每个合并组只保留 1 份 current 目标文件，其余源文件归档到 `archive/specs/<子目录>/`；
4. 归档目标先创建目录，再 `git mv`；
5. 每完成一组，用 `check_docs.py` 定位遗漏引用。
