# Askora 文档处置清单

> 状态：Current  
> 校准日期：2026-08-08  
> 基线提交：`33f938b85a3eba446db30b1598768311a79629fc`  
> 范围：受 Git 跟踪或本次新增的 Markdown/RST 文件；生成产物中的复制文件不作为独立权威来源。

处置代码：

- `CURRENT-UPDATED`：当前说明，已按稳定代码基线更新；
- `CANONICAL-RETAIN`：冻结合同或正式设计，保留语义；
- `HISTORICAL-RETAIN`：保留为历史、研究或发布证据，不作为当前状态；
- `SUPPORT-RETAIN`：工具、构建或设计辅助资产；
- `EXCLUDED`：测试夹具，不属于项目说明；
- `DELETED`：已确认无持续维护价值并删除。

## 1. 根目录与应用说明

| 文件 | 处置 | 说明 |
|---|---|---|
| `AGENTS.md` | CANONICAL-RETAIN | Codex 强制执行合同 |
| `README.md` | CURRENT-UPDATED | 当前产品、实现、运行和验证入口 |
| `apps/backend/README.md` | CURRENT-UPDATED | 后端模块与命令已对齐 v0.3/CI |
| `apps/frontend/README.md` | CURRENT-UPDATED | 本次新增前端/Electron 当前说明 |
| `apps/frontend/resources/backend/README.md` | SUPPORT-RETAIN | Electron 后端资源目录说明 |
| `apps/backend/.trae/documents/seed_data_plan.md` | DELETED | 一次性计划已实现；旧策略分类会误导当前语义 |
| `apps/backend/tests/fixtures/malicious_document.md` | EXCLUDED | 安全测试输入，不是说明文档 |
| `.design_library/Askora/README.md` | SUPPORT-RETAIN | UI 设计资产，不是 Canonical Design |
| `.design_library/Askora/SKILL.md` | SUPPORT-RETAIN | 设计工具指令，不是项目实现合同 |

## 2. 文档索引、ADR 与 Release

| 文件 | 处置 | 说明 |
|---|---|---|
| `docs/README.md` | CURRENT-UPDATED | 权威层级、目录状态和质量门禁 |
| `docs/document-inventory.md` | CURRENT-UPDATED | 本清单 |
| `docs/product-gap-register-p1-p2.md` | CURRENT-UPDATED | 当前 P1/P2 产品缺口登记；P1-02/P1-07 保持 OPEN 直至各自门禁完成 |
| `docs/adr/README.md` | CANONICAL-RETAIN | ADR 治理与索引 |
| `docs/adr/ADR-0001-teaching-strategy-ontology.md` | CANONICAL-RETAIN | Accepted decision record |
| `docs/adr/ADR-0002-constrained-deterministic-teaching-policy-architecture.md` | CANONICAL-RETAIN | Accepted decision record |
| `docs/adr/ADR-0003-policy-runtime-profile-source-and-activation.md` | CANONICAL-RETAIN | Accepted production profile source / activation resolution decision |
| `docs/adr/ADR-0004-guided-book-learning-and-durable-transcript.md` | CANONICAL-RETAIN | User-delegated guided flow and SYS08 transcript decision |
| `docs/adr/ADR-0005-policy-bound-real-model-rendering.md` | CANONICAL-RETAIN | User-delegated production real-model rendering and E2E decision |
| `docs/adr/ADR-0006-workspace-read-model-scope-and-missing-objective-metadata.md` | CANONICAL-RETAIN | UI-02B read scope、objective missing semantics 与 owner-safe evidence label 决策 |
| `docs/adr/ADR-0007-sys06-activity-lifecycle-and-completion.md` | CANONICAL-RETAIN | SYS06 activity lifecycle、completion 与迁移决策 |
| `docs/adr/ADR-0012-unified-recovery-control-plane.md` | CANONICAL-RETAIN | P1-07 统一恢复控制面与 bootstrap diagnostics 决策 |
| `docs/adr/ADR-0013-desktop-model-credential-and-activation.md` | CANONICAL-RETAIN | P1-02 desktop credential、probe、activation、rollback 与 clear 决策 |
| `docs/adr/ADR-0103-local-data-recovery-portability-erasure.md` | CANONICAL-RETAIN | P1-03 local recovery、portability 与 owner erasure decision |
| `docs/releases/README.md` | CURRENT-UPDATED | 本次新增历史证据索引 |
| `docs/releases/v0.2-first-vertical-learning-loop.md` | HISTORICAL-RETAIN | v0.2 release evidence snapshot |
| `docs/releases/v0.3-governance-preconditions.md` | HISTORICAL-RETAIN | EXEC-007 durable evidence snapshot |
| `docs/releases/v0.3-adaptive-teaching-loop.md` | HISTORICAL-RETAIN | v0.3 release evidence；补充快照边界和准确 commit |
| `docs/releases/ui-01-learning-shell-workspace.md` | HISTORICAL-RETAIN | UI-01 completion evidence snapshot |
| `docs/releases/ui-02a-library-knowledge-map.md` | HISTORICAL-RETAIN | UI-02A completion evidence snapshot |
| `docs/releases/ui-02b2-guided-book-learning.md` | HISTORICAL-RETAIN | UI-02B2 guided learning completion evidence snapshot |

## 3. Canonical Design 与 Research

| 文件 | 处置 | 说明 |
|---|---|---|
| `docs/design/README.md` | CURRENT-UPDATED | 本次新增 Design 层索引 |
| `docs/design/个人AI辅助学习平台设计方案.md` | CURRENT-UPDATED | Canonical Design 语义保留，阶段状态更新 |
| `docs/design/AI学习系统算法与教学内核设计.md` | CURRENT-UPDATED | Canonical Design 语义保留，Spec/EXEC 状态更新 |
| `docs/design/p1-03-data-control-and-recovery.md` | CURRENT-UPDATED | P1-03 data protection additive Canonical Design |
| `docs/design/p1-02-model-settings.md` | CANONICAL-RETAIN | P1-02 App 内模型配置产品与安全设计闭环 |
| `docs/design/research/README.md` | CURRENT-UPDATED | Research Delta 改为已完成历史输入 |
| `docs/design/research/evidence/八类技术系统-教育科学证据.md` | HISTORICAL-RETAIN | 独立研究证据 |
| `docs/design/research/evidence/八类技术系统-ITS与学习者建模证据.md` | HISTORICAL-RETAIN | 独立研究证据 |
| `docs/design/research/evidence/八类技术系统-检索与知识架构证据.md` | HISTORICAL-RETAIN | 独立研究证据 |
| `docs/design/research/evidence/八类技术系统-教学策略与序列决策证据.md` | HISTORICAL-RETAIN | 独立研究证据 |
| `docs/design/research/evidence/八类技术系统-记忆与复习调度证据.md` | HISTORICAL-RETAIN | 独立研究证据 |
| `docs/design/research/evidence/八类技术系统-LLM-Agent与可信治理证据.md` | HISTORICAL-RETAIN | 独立研究证据 |
| `docs/design/research/evidence/八类技术系统-参考资料索引.md` | HISTORICAL-RETAIN | 外部证据索引；本轮未重新验证外部网页存续 |
| `docs/design/research/synthesis/4.1-内容解析与知识建模-系统设计研究.md` | HISTORICAL-RETAIN | 分系统研究设计 |
| `docs/design/research/synthesis/4.2-检索与知识供给-系统设计研究.md` | HISTORICAL-RETAIN | 分系统研究设计 |
| `docs/design/research/synthesis/4.3-学习者建模-系统设计研究.md` | HISTORICAL-RETAIN | 分系统研究设计 |
| `docs/design/research/synthesis/4.4-评估与错误诊断-系统设计研究.md` | HISTORICAL-RETAIN | 分系统研究设计 |
| `docs/design/research/synthesis/4.5-教学策略选择-系统设计研究.md` | HISTORICAL-RETAIN | 分系统研究设计 |
| `docs/design/research/synthesis/4.6-学习路径与任务调度-系统设计研究.md` | HISTORICAL-RETAIN | 分系统研究设计 |
| `docs/design/research/synthesis/4.7-记忆保持与复习调度-系统设计研究.md` | HISTORICAL-RETAIN | 分系统研究设计 |
| `docs/design/research/synthesis/4.8-LLM生成Agent编排与可信控制-系统设计研究.md` | HISTORICAL-RETAIN | 分系统研究设计 |
| `docs/design/research/synthesis/DR-03-01-教学策略与支架转换研究.md` | HISTORICAL-RETAIN | v0.3 Research Delta evidence |
| `docs/design/research/synthesis/DR-03-02-错误诊断到教学补救研究.md` | HISTORICAL-RETAIN | v0.3 Research Delta evidence |
| `docs/design/research/synthesis/DR-03-03-Teaching-Policy-决策算法与数据契约研究.md` | HISTORICAL-RETAIN | v0.3 Research Delta evidence |
| `docs/design/research/synthesis/DR-03-04-学习效果验证与产品实验研究.md` | HISTORICAL-RETAIN | v0.3 Research Delta evidence |
| `docs/design/research/synthesis/v0.3-Research-Synthesis-Adaptive-Teaching-Loop.md` | HISTORICAL-RETAIN | v0.3 frozen research input |
| `docs/design/research/synthesis/v0.3-候选范围分析.md` | HISTORICAL-RETAIN | 已标明 completed pre-design input |
| `docs/design/research/synthesis/v0.3-深度研究议程.md` | HISTORICAL-RETAIN | 已标明 completed research agenda |
| `docs/design/research/synthesis/八类技术系统-公共架构冻结稿.md` | HISTORICAL-RETAIN | 已由 Canonical Design/Specs 吸收 |
| `docs/design/research/synthesis/八类技术系统-现状诊断.md` | HISTORICAL-RETAIN | 已标明 pre-v0.2 snapshot |
| `docs/design/research/synthesis/八类技术系统-系统设计研究综合与溯源.md` | HISTORICAL-RETAIN | 研究拆分与溯源入口 |

## 4. Implementation Specs

| 文件 | 处置 | 说明 |
|---|---|---|
| `docs/specs/README.md` | CURRENT-UPDATED | v0.3 + Book-to-Learning implemented baseline 与 SPEC-D01～D06 freeze index |
| `docs/specs/architecture/state-ownership.md` | CANONICAL-RETAIN | v0.3 canonical contract |
| `docs/specs/architecture/system-architecture.md` | CANONICAL-RETAIN | v0.3 canonical contract |
| `docs/specs/architecture/dependency-rules.md` | CANONICAL-RETAIN | v0.3 canonical contract |
| `docs/specs/domain/domain-model.md` | CANONICAL-RETAIN | v0.3 canonical contract |
| `docs/specs/domain/decision-contract.md` | CANONICAL-RETAIN | v0.3 canonical contract |
| `docs/specs/domain/event-contract.md` | CANONICAL-RETAIN | v0.3 canonical contract |
| `docs/specs/domain/lifecycle-state-machines.md` | CANONICAL-RETAIN | 仍适用的 lifecycle contract |
| `docs/specs/interfaces/api-contract.md` | CANONICAL-RETAIN | 仍适用的 API contract |
| `docs/specs/interfaces/content-ingestion-contract.md` | CANONICAL-RETAIN | SPEC-D01；结构保真 ingestion / source locator / replay 冻结合同 |
| `docs/specs/interfaces/recovery-contract.md` | CANONICAL-RETAIN | P1-07 strict recovery issue/action/result contract |
| `docs/specs/interfaces/data-control-contract.md` | CANONICAL-RETAIN | P1-03 recovery/export/erasure frozen contract |
| `docs/specs/interfaces/error-contract.md` | CANONICAL-RETAIN | 仍适用的 error contract |
| `docs/specs/interfaces/persistence-contract.md` | CANONICAL-RETAIN | 仍适用的 persistence contract |
| `docs/specs/interfaces/render-content-contract.md` | CANONICAL-RETAIN | v0.3.1 rich response rendering contract |
| `docs/specs/interfaces/schema-versioning.md` | CANONICAL-RETAIN | 仍适用的 versioning contract |
| `docs/specs/quality/testing-standard.md` | CANONICAL-RETAIN | v0.3 quality contract |
| `docs/specs/quality/observability-standard.md` | CANONICAL-RETAIN | v0.3 quality contract |
| `docs/specs/quality/definition-of-done.md` | CANONICAL-RETAIN | v0.3 release gates |
| `docs/specs/quality/security-standard.md` | CANONICAL-RETAIN | v0.3 security contract |
| `docs/specs/systems/01-content-knowledge.md` | CANONICAL-RETAIN | SYS01 contract |
| `docs/specs/systems/01-content-granularity.md` | CANONICAL-RETAIN | SPEC-D02；多粒度内容模型冻结合同 |
| `docs/specs/systems/01-knowledge-publish-pipeline.md` | CANONICAL-RETAIN | SPEC-D03；知识候选验证/发布冻结合同 |
| `docs/specs/systems/02-retrieval.md` | CANONICAL-RETAIN | SYS02 contract |
| `docs/specs/systems/03-learner-model.md` | CANONICAL-RETAIN | SYS03 contract |
| `docs/specs/systems/04-assessment.md` | CANONICAL-RETAIN | SYS04 contract |
| `docs/specs/systems/05-teaching-policy.md` | CANONICAL-RETAIN | SYS05 contract |
| `docs/specs/systems/06-learning-planner.md` | CANONICAL-RETAIN | SYS06 contract |
| `docs/specs/systems/06-activity-lifecycle.md` | CANONICAL-RETAIN | SYS06 versioned activity start/resume/completion contract |
| `docs/specs/systems/06-goal-knowledge-mapping.md` | CANONICAL-RETAIN | SPEC-D04；LearningGoal→Knowledge mapping 冻结合同 |
| `docs/specs/systems/06-prerequisite-diagnostic-bootstrap.md` | CANONICAL-RETAIN | SPEC-D05；prerequisite diagnostic bootstrap 冻结合同 |
| `docs/specs/systems/07-review-scheduler.md` | CANONICAL-RETAIN | SYS07 contract |
| `docs/specs/systems/08-ai-orchestration.md` | CANONICAL-RETAIN | SYS08 contract |
| `docs/specs/systems/08-model-configuration.md` | CANONICAL-RETAIN | SYS08 ModelRouteProfile、desktop vault、probe 与 activation 合同 |
| `docs/specs/vertical-slices/v0.2-learning-loop.md` | HISTORICAL-RETAIN | v0.2 frozen baseline；已补充生命周期 |
| `docs/specs/vertical-slices/v0.3-adaptive-teaching-loop.md` | CURRENT-UPDATED | 冻结合同；已更新 EXEC 完成状态 |
| `docs/specs/vertical-slices/v0.3.1-rich-response-rendering.md` | CANONICAL-RETAIN | v0.3.1 additive presentation slice |
| `docs/specs/vertical-slices/book-to-adaptive-learning.md` | CANONICAL-RETAIN | SPEC-D06；Book-to-Adaptive-Learning E2E 冻结合同，EXEC-017～024 已实现 |
| `docs/specs/ui/README.md` | CANONICAL-RETAIN | 已批准冻结的 UI 重设计合同入口 |
| `docs/specs/ui/information-architecture.md` | CANONICAL-RETAIN | 导航、路由与页面层级合同 |
| `docs/specs/ui/screen-contracts.md` | CANONICAL-RETAIN | 页面状态与交互合同 |
| `docs/specs/ui/data-contracts.md` | CANONICAL-RETAIN | 只读查询接口与来源语义合同 |
| `docs/specs/ui/visual-system.md` | CANONICAL-RETAIN | 视觉系统与无障碍合同 |
| `docs/specs/ui/quality-and-migration.md` | CANONICAL-RETAIN | 三阶段执行、质量门禁与迁移合同 |
| `docs/specs/vertical-slices/ui-01-learning-shell-workspace.md` | CANONICAL-RETAIN | 冻结 UI-01 Vertical Slice；EXEC-015 已完成 |
| `docs/specs/vertical-slices/ui-02a-library-knowledge-map.md` | CANONICAL-RETAIN | 冻结 UI-02A Vertical Slice；EXEC-016 已完成 |
| `docs/specs/vertical-slices/ui-02b1-material-learning-launch.md` | CANONICAL-RETAIN | 冻结 UI-02B1 Vertical Slice；EXEC-025 已完成 |
| `docs/specs/vertical-slices/ui-02b2-guided-book-learning.md` | CANONICAL-RETAIN | 冻结 UI-02B2 system-guided launch 与 durable transcript Slice |
| `docs/specs/vertical-slices/ui-02b3-real-model-guided-learning.md` | CANONICAL-RETAIN | 冻结 production real-model guided learning 与真实 E2E Slice |
| `docs/specs/vertical-slices/ui-02b-goals-path-evidence.md` | CANONICAL-RETAIN | 冻结并完成 UI-02B Goals/Path/Evidence read-only Slice；EXEC-029 DONE |
| `docs/specs/vertical-slices/ui-02c-canonical-activity-lifecycle.md` | CANONICAL-RETAIN | UI-02C activity start/resume/complete/next Slice；EXEC-030 DONE |
| `docs/specs/vertical-slices/p1-07-error-recovery-center.md` | CANONICAL-RETAIN | P1-07 双入口统一恢复 Vertical Slice |
| `docs/specs/vertical-slices/p1-03-data-control-recovery.md` | CANONICAL-RETAIN | 冻结 P1-03 backup/restore/export/erasure Slice |
| `docs/specs/vertical-slices/p1-02-model-settings.md` | CANONICAL-RETAIN | 冻结 P1-02 configure→probe→activate→relaunch 产品闭环 |

## 5. EXEC 历史合同

| 文件 | 处置 | 说明 |
|---|---|---|
| `docs/exec-plans/README.md` | CURRENT-UPDATED | EXEC-001～030 已完成；P1-02、P1-03 与 P1-07 EXEC active |
| `docs/exec-plans/completed/README.md` | CURRENT-UPDATED | 完成矩阵；当前包含 EXEC-001～030 |
| `docs/exec-plans/completed/EXEC-001-contracts-event-outbox-foundation.md` | HISTORICAL-RETAIN | 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-002-canonical-teaching-entry.md` | HISTORICAL-RETAIN | 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-003-content-evidence-bundle.md` | HISTORICAL-RETAIN | 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-004-assessment-learner-projection.md` | HISTORICAL-RETAIN | 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-005-review-planner-integration.md` | HISTORICAL-RETAIN | 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-006-v0.2-e2e-quality-gate.md` | HISTORICAL-RETAIN | 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-007-v0.3-governance-preconditions.md` | HISTORICAL-RETAIN | 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-008-v0.3-contracts-schema-migration.md` | HISTORICAL-RETAIN | 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-009-deterministic-teaching-policy-kernel.md` | HISTORICAL-RETAIN | 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-010-adaptive-transition-anti-oscillation.md` | HISTORICAL-RETAIN | 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-011-cross-system-adaptive-execution.md` | HISTORICAL-RETAIN | 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-012-outcome-experiment-opve-foundation.md` | HISTORICAL-RETAIN | 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-013-v0.3-e2e-release-gate.md` | HISTORICAL-RETAIN | 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-014-rich-response-rendering.md` | HISTORICAL-RETAIN | 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-015-ui-01-learning-shell-workspace.md` | HISTORICAL-RETAIN | UI-01 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-016-ui-02a-library-knowledge-map.md` | HISTORICAL-RETAIN | UI-02A 任务合同；保留已解决 CI baseline 授权记录 |
| `docs/exec-plans/completed/EXEC-017-structure-preserving-epub-ingestion.md` | HISTORICAL-RETAIN | Book-to-Learning 结构保真 EPUB ingestion 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-018-multi-granularity-content-projections.md` | HISTORICAL-RETAIN | Book-to-Learning 多粒度内容模型与可重建投影不可变任务合同 |
| `docs/exec-plans/completed/EXEC-019-knowledge-verification-publication.md` | HISTORICAL-RETAIN | Book-to-Learning 知识候选验证与发布流水线不可变任务合同 |
| `docs/exec-plans/completed/EXEC-020-retrieval-projection-sys02-binding.md` | HISTORICAL-RETAIN | Book-to-Learning 发布知识到 SYS02 检索投影绑定不可变任务合同 |
| `docs/exec-plans/completed/EXEC-021-learning-goal-knowledge-mapping.md` | HISTORICAL-RETAIN | Book-to-Learning 自然语言 Goal 到 published KnowledgeUnit 映射不可变任务合同 |
| `docs/exec-plans/completed/EXEC-022-prerequisite-diagnostic-planner-bootstrap.md` | HISTORICAL-RETAIN | Book-to-Learning prerequisite diagnostic 与现有 Planner handoff 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-023-book-learning-orchestration-api.md` | HISTORICAL-RETAIN | Book-to-Learning readiness/additive API 与现有 canonical teaching handoff 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-024-book-to-learning-e2e-release-gate.md` | HISTORICAL-RETAIN | Book-to-Learning E2E、replay、security 与 release gate 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-025-ui-02b1-material-learning-launch.md` | HISTORICAL-RETAIN | 单份资料到 canonical teaching 启动 UI 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-026-ui-02b2-guided-book-learning.md` | HISTORICAL-RETAIN | 系统带领 Book Learning 与 durable transcript 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-027-ui-02b3-real-model-e2e.md` | HISTORICAL-RETAIN | production real-model rendering 与真实 E2E 完成合同 |
| `docs/exec-plans/completed/EXEC-028-zhipu-development-model.md` | HISTORICAL-RETAIN | 智谱开发模型接入、真实模型验证与本机配置边界 |
| `docs/exec-plans/completed/EXEC-029-ui-02b-goals-path-evidence.md` | HISTORICAL-RETAIN | Goals/Path/Evidence 只读产品闭环不可变任务合同 |
| `docs/exec-plans/completed/EXEC-030-ui-02c-canonical-activity-lifecycle.md` | CANONICAL-RETAIN | UI-02C lifecycle 已完成归档 |
| `docs/exec-plans/active/EXEC-037-p1-07-error-recovery-center.md` | CURRENT-UPDATED | P1-07 active execution contract |
| `docs/exec-plans/active/EXEC-1031-p1-03-recovery-foundation.md` | CANONICAL-RETAIN | P1-03 recovery foundation ready |
| `docs/exec-plans/active/EXEC-1032-p1-03-verified-restore.md` | CANONICAL-RETAIN | P1-03 restore blocked by EXEC-1031 |
| `docs/exec-plans/active/EXEC-1033-p1-03-user-data-export.md` | CANONICAL-RETAIN | P1-03 export blocked by EXEC-1032 |
| `docs/exec-plans/active/EXEC-1034-p1-03-erasure-ui-release.md` | CANONICAL-RETAIN | P1-03 erasure/release blocked by EXEC-1033 |
| `docs/exec-plans/active/EXEC-040-p1-02a-model-configuration-foundation.md` | CANONICAL-RETAIN | 已冻结并 active；P1-02 安全基础 |
| `docs/exec-plans/active/EXEC-041-p1-02b-model-settings-product-closure.md` | CANONICAL-RETAIN | 已冻结；等待 EXEC-040 完成 |

## 6. Release Evidence

| 文件 | 处置 | 说明 |
|---|---|---|
| `docs/releases/README.md` | CURRENT-UPDATED | 历史发布与验收证据索引 |
| `docs/releases/book-to-adaptive-learning.md` | CURRENT-UPDATED | Book-to-Learning Engineering/Contract、Policy/Ownership 与 Learning Evidence 分离报告 |
| `docs/releases/ui-02b1-material-learning-launch.md` | CURRENT-UPDATED | UI-02B1 Engineering/UI Contract/Accessibility 与 Learning Evidence 分离报告 |
| `docs/releases/ui-02b2-guided-book-learning.md` | CURRENT-UPDATED | UI-02B2 Engineering/UI/Contract/Ownership/Security 与 Learning Evidence 分离报告 |
| `docs/releases/ui-02b3-real-model-guided-learning.md` | CURRENT-UPDATED | UI-02B3 真实浏览器/provider/PostgreSQL 与 Learning Evidence 分离报告 |
| `docs/releases/ui-02b-goals-path-evidence.md` | CURRENT-UPDATED | UI-02B Goals/Path/Evidence Engineering、Ownership 与 Learning Evidence 分离报告 |
| `docs/releases/ui-02c-canonical-activity-lifecycle.md` | CURRENT-UPDATED | UI-02C Engineering、Ownership、浏览器 lifecycle 与 Learning Evidence 分离报告 |

## 7. 后续维护规则

1. 当前说明必须随稳定代码和可执行命令更新；未提交实验不得写成已交付能力。
2. Canonical Spec/ADR 的语义变化不能借“文档整理”完成。
3. 历史文件保留当时语境；上级索引负责说明其生命周期。
4. 只有完全重复、没有独立证据/设计/审计价值的临时说明才删除。
5. 删除前记录替代来源；删除后运行文档链接门禁。
