# Askora 文档中心

> 状态：Current Documentation Authority Index（唯一入口）
> 定位：**人的**导航入口；agent 的机械入口（权威链、命令、GAP 协议）在仓库根 `AGENTS.md`，两者不互相复制
> 最近校准：2026-08-13

## 1. 从问题出发导航

| 我想知道…… | 入口 |
|---|---|
| Askora 为什么存在、服务谁、成功是什么 | [Product Strategy](product/PRODUCT-STRATEGY.md) |
| Askora 是什么、不是什么、v1 的硬边界 | [Product Positioning](product/PRODUCT-POSITIONING.md) |
| Askora 必须具备哪些能力、规则与产品验收 | [Product Definition](product/PRODUCT-DEFINITION.md) |
| **当前有效架构决策**（某系统为什么这样设计） | [Decision Log](decisions/DECISIONS.md) |
| 决策原文 / 备选方案 / 历史废止 | [archive/adr/](archive/adr/)（按 `ADR-XXXX` 查找） |
| 系统如何组织、single-writer、依赖边界 | [System Architecture & Rules](specs/architecture.md) |
| 领域对象、事件、生命周期状态机 | [Domain Model & Contracts](specs/domain.md) |
| SYS01–SYS08 教学内核规范（每系统 1 份） | [specs/systems/](specs/systems/) |
| API、错误、持久化、恢复、内容接口 | [specs/interfaces/](specs/interfaces/) |
| 身份 / Workspace / LocalSecretStore / Course 平台 | [Platform Contracts](specs/platform.md) |
| 测试、安全、可观测性、Definition of Done | [Quality Standards](specs/quality.md) |
| UI / UX 实现合同 | [UI Specs](specs/ui.md) |
| 体验设计（IA、交互、学习体验） | [design/experience/](design/experience/) |
| 产品/学习的研究依据 | [research/](research/README.md) |
| 外部 Desktop UI 逆向证据 | [ui-reverse-engineering/](ui-reverse-engineering/00-overview.md) |
| 历史设计、旧规范、旧 EXEC | [archive/](archive/README.md) |

## 2. Authority Chain

```text
PRODUCT-STRATEGY → PRODUCT-POSITIONING → PRODUCT-DEFINITION
→ Canonical Design (design/)
→ 决策权威视图 (decisions/DECISIONS.md，原文在 archive/adr/)
→ Implementation / Quality Specs (specs/)
→ Code / Tests
```

Research 是所有层级的证据输入，不是并列 authority。冲突处理（STRATEGY GAP / POSITIONING GAP / PRODUCT DEFINITION GAP / SPEC GAP）见 `AGENTS.md`。

## 3. 当前文档清单（唯一 truth）

以下即全部 current 文档；除此之外的旧文档一律在 `archive/`，不作为 current truth。

| 层 | 文档 | 职责 |
|---|---|---|
| Product | `product/PRODUCT-STRATEGY.md` | Why / Who / Problem / Value / Success |
| Product | `product/PRODUCT-POSITIONING.md` | Category / Product Shape / Hard Boundaries |
| Product | `product/PRODUCT-DEFINITION.md` | Capabilities / Rules / Requirements / Acceptance |
| Decision | `decisions/DECISIONS.md` | 当前有效决策（decision log） |
| Design | `design/experience/EXPERIENCE-ARCHITECTURE.md` | 体验架构、导航模型 |
| Design | `design/experience/LEARNING-EXPERIENCE.md` | 学习体验语义 |
| Design | `design/experience/INTERACTION-MODEL.md` | 交互原语与层级 |
| Spec | `specs/architecture.md` | 系统架构、state ownership、依赖规则 |
| Spec | `specs/domain.md` | 领域模型、决策/事件契约、状态机 |
| Spec | `specs/systems/01-content-knowledge.md` | SYS01 内容与知识 |
| Spec | `specs/systems/02-retrieval.md` | SYS02 检索 |
| Spec | `specs/systems/03-learner-model.md` | SYS03 学习者建模 |
| Spec | `specs/systems/04-assessment.md` | SYS04 评估 |
| Spec | `specs/systems/05-teaching-policy.md` | SYS05 教学策略 |
| Spec | `specs/systems/06-learning-planner.md` | SYS06 学习规划（含 Goal/Activity/诊断） |
| Spec | `specs/systems/07-review-scheduler.md` | SYS07 复习调度 |
| Spec | `specs/systems/08-ai-orchestration.md` | SYS08 AI 编排（含 Model Configuration） |
| Spec | `specs/interfaces/api.md` | API / 错误 / schema 版本 |
| Spec | `specs/interfaces/content.md` | 内容摄取 / 渲染 |
| Spec | `specs/interfaces/persistence-and-data-control.md` | 持久化 / Material 生命周期 / 数据控制 |
| Spec | `specs/interfaces/message-and-note.md` | 学习会话消息 / UserNote |
| Spec | `specs/interfaces/recovery-and-onboarding.md` | 恢复 / 首次引导 |
| Spec | `specs/platform.md` | 身份 / Workspace / Course / LSS |
| Spec | `specs/quality.md` | 测试 / 安全 / 可观测 / DoD |
| Spec | `specs/ui.md` | UI / UX 实现合同 |

> 维护规则：新增 current 文档必须进入本清单；移除时必须先归档并更新本清单与相关链接。

## 4. 目录树

```text
docs/
├── README.md                 # 本入口
├── product/                  # [CURRENT] 产品权威（3 文件）
├── design/experience/        # [CURRENT] 体验设计（3 文件）
├── decisions/                # [CURRENT] 决策权威视图
├── specs/                    # [CURRENT] 规范（architecture/domain/platform/quality/ui + systems/ + interfaces/）
├── research/                 # [SUPPORTING] 证据输入
├── ui-reverse-engineering/   # [SUPPORTING] 外部 UI 逆向证据
├── archive/                  # [ARCHIVE] 历史（adr/、design/、specs/）
└── REFACTOR-PLAN.md / REFACTOR-MAPPING.md   # 本次重构方案与映射（完成后归档）
```

## 5. 生命周期

| Lifecycle | 含义 | 位置 |
|---|---|---|
| CURRENT | 当前唯一正式事实源 | product/ design/ decisions/ specs/ |
| SUPPORTING | 决策输入，允许不确定 | research/ ui-reverse-engineering/ |
| ARCHIVE | 历史证据，不再 current | archive/ |

临时/证据文档（EXEC、release report、audit）必须携带 `Integrates-into` + `Delete-by` 元数据，集成进 canonical 后即归档。
