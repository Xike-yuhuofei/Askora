# Askora 文档中心

> 状态：Current Documentation Authority Index（人的唯一入口）
> 定位：**人的**导航入口；agent 的机械入口（读取顺序、冲突处理、GAP 协议）在仓库根 `AGENTS.md`，两者不互相复制
> 最近校准：2026-08-13（Core Journey：001–004）

## 1. 从问题出发导航

| 我想知道…… | 入口 |
|---|---|
| Askora 为什么存在、服务谁、成功是什么 | [Product Strategy](product/PRODUCT-STRATEGY.md) |
| Askora 是什么、不是什么、v1 的硬边界 | [Product Positioning](product/PRODUCT-POSITIONING.md) |
| Askora 必须具备哪些能力、规则与产品验收 | [Product Definition](product/PRODUCT-DEFINITION.md) |
| 用户如何理解、导航和操作 | [design/experience/](design/experience/) |
| 系统如何组织、single-writer、依赖边界 | [System Architecture & Rules](specs/architecture.md) |
| 领域对象、事件、生命周期状态机 | [Domain Model & Contracts](specs/domain.md) |
| SYS01–SYS08 教学内核如何成立 | [specs/systems/](specs/systems/) |
| API、错误、持久化、恢复、内容接口 | [specs/interfaces/](specs/interfaces/) |
| 身份 / Workspace / LocalSecretStore / Course 平台 | [Platform Contracts](specs/platform.md) |
| 测试、安全、可观测性、Definition of Done | [Quality Standards](specs/quality.md) |
| UI / UX 实现合同 | [UI Specs](specs/ui.md) |
| 为什么当年这样设计（索引，不是合同） | [Decision Log](decisions/DECISIONS.md) |
| 决策原文 / 备选方案 / 历史废止 | [archive/adr/](archive/adr/)（按 `ADR-XXXX` 查找） |
| 产品/学习的研究依据 | [research/](research/README.md) |
| 可复用 UI 视觉源（foundation 已吸收进 `specs/ui.md`） | [`../ui/`](../ui/README.md) |
| 历史设计、旧规范、旧过程文档 | [archive/](archive/README.md) |

## 2. Authority

现行合同（唯一权威，自上而下）：

```text
PRODUCT-STRATEGY
→ PRODUCT-POSITIONING
→ PRODUCT-DEFINITION
  → Experience Design（仅体验）
  → Specs（systems / domain / architecture / platform / interfaces / ui / quality）
  → Code / Tests
```

旁路（不能推翻上面任何一层）：

```text
Decision Log / ADR     为什么选这个方案（索引 + 不可变原文）
research/              证据，吸收前不是合同
ui/                    视觉源与 UI 研究；Light foundation 已吸收进 specs/ui.md
Linear / EXEC          现在做什么，不是长期事实
```

冲突处理见 `AGENTS.md`。同一事实只在一处拥有正文；Decision Log 与 Spec 冲突时以 Spec 为准。

## 3. 当前文档清单（唯一 truth）

以下即全部 current 正文；除此之外的旧文档一律在 `archive/`，不作为 current truth。各层 `README.md` 只做导航，不充当第二份合同。

| 层 | 文档 | 职责 |
|---|---|---|
| Product | `product/PRODUCT-STRATEGY.md` | Why / Who / Problem / Value / Success |
| Product | `product/PRODUCT-POSITIONING.md` | Category / Product Shape / Hard Boundaries |
| Product | `product/PRODUCT-DEFINITION.md` | Capabilities / Rules / Requirements / Acceptance |
| Design | `design/experience/EXPERIENCE-ARCHITECTURE.md` | 体验架构、空间/对话导航、Core Journeys |
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
| Index | `decisions/DECISIONS.md` | 决策索引（非现行合同） |

> 维护规则：新增 current 文档必须进入本清单；移除时必须先归档并更新本清单与相关链接。`check_docs.py` 校验本清单与磁盘一致。

## 4. 目录树

```text
docs/
├── README.md                 # 本入口
├── product/                  # [CURRENT] 产品权威（3 文件）
├── design/experience/        # [CURRENT] 体验设计（3 文件）
├── specs/                    # [CURRENT] 规范（跨切面 + systems/ + interfaces/）
├── decisions/                # [INDEX] 决策索引，不是合同
├── research/                 # [SUPPORTING] 证据输入
└── archive/                  # [ARCHIVE] 历史（adr/、design/、specs/、过期过程文档）
```

仓库根 `ui/` 是 UI 视觉源与研究（SUPPORTING），不在本目录。

## 5. 生命周期

| Lifecycle | 含义 | 位置 |
|---|---|---|
| CURRENT | 现行合同 | product/ design/experience/ specs/ |
| INDEX | 决策索引与溯源，不能覆盖 Spec | decisions/ |
| SUPPORTING | 决策输入，允许不确定 | research/；仓库根 `ui/` |
| ARCHIVE | 历史证据，不再 current | archive/ |

临时/证据文档（EXEC、release report、audit）必须携带 `Integrates-into` + `Delete-by` 元数据，集成进 canonical 后即归档。
