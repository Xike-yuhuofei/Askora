# Askora Design 文档索引

> 状态：设计层导航（完整清单与权威顺序见 [`../README.md`](../README.md)）
> 当前有效设计 = `design/experience/` 3 份

## Current Experience Design

| 文档 | 职责 |
|---|---|
| [experience/EXPERIENCE-ARCHITECTURE.md](experience/EXPERIENCE-ARCHITECTURE.md) | 体验原则、空间/对话 IA、Workspace Experience、导航模型、四条 Core Journeys |
| [experience/LEARNING-EXPERIENCE.md](experience/LEARNING-EXPERIENCE.md) | LearningActivity、Learning Conversation、Attempt、Feedback、Evidence、Notes |
| [experience/INTERACTION-MODEL.md](experience/INTERACTION-MODEL.md) | 语义交互原语、交互层级、progressive disclosure、component boundary |

本目录只拥有**用户如何看到、找到和操作**。教学算法、Learner Model、Assessment mechanics 的现行合同在 `docs/specs/systems/`，不在本目录。视觉 foundation 的现行合同在 [`../specs/ui.md`](../specs/ui.md)；可复用源在 [`../../ui/traework/`](../../ui/traework/)，不是本目录的体验合同。

## 边界

- Design 不重新定义 Product Strategy / Positioning；
- Design 不新增/删除 Product Capability 或决定 v1 Feature inclusion；
- 历史 Learning Core 设计基线已归档至 [`../archive/design/`](../archive/design/)，只作溯源，不覆盖 current；
- 若 Design 发现 Capability / Feature Scope / Product Rule 缺失，报告 `PRODUCT DEFINITION GAP`；
- 学习语义或状态所有权缺口属于 `SPEC GAP`，回到 `docs/specs/systems/` 或相关 Spec。
