# Askora Design 文档索引

> 状态：设计层导航（完整清单见 [`../README.md`](../README.md)）
> 当前有效设计 = `design/experience/` 3 份；历史设计（learning 基线、Delta、features）已归档至 `../archive/design/`

## Current Canonical Design

| 文档 | 职责 |
|---|---|
| [experience/EXPERIENCE-ARCHITECTURE.md](experience/EXPERIENCE-ARCHITECTURE.md) | 体验原则、用户侧 IA、Workspace Experience、导航模型、Core Journeys |
| [experience/LEARNING-EXPERIENCE.md](experience/LEARNING-EXPERIENCE.md) | LearningActivity、Learning Conversation、Attempt、Feedback、Evidence、Notes |
| [experience/INTERACTION-MODEL.md](experience/INTERACTION-MODEL.md) | 语义交互原语、交互层级、progressive disclosure、component boundary |

## 形成链

```text
PRODUCT-DEFINITION (CAP-* / PD-*)
→ Canonical Design（本目录）
→ DECISIONS.md / archive/adr/（决策）
→ specs/（实现合同）
→ Code
```

设计负责"已定义产品能力如何成立"的产品/领域/学习语义，不定义数据库 schema、API payload、retry、migration 等 implementation mechanics。

## 边界

- Design 不重新定义 Product Strategy / Positioning；
- Design 不新增/删除 Product Capability 或决定 v1 Feature inclusion；
- 历史 Learning Core 设计基线（AI学习系统算法与教学内核设计 / 个人AI辅助学习平台设计方案 / v0.3-Canonical-Design-Delta）已归档至 `../archive/design/`，其当前有效语义由 `DECISIONS.md` + `specs/` 承接；
- 若 Design 发现 Capability / Feature Scope / Product Rule 缺失，报告 `PRODUCT DEFINITION GAP`，不在 Design 中永久承担产品定义职责。
