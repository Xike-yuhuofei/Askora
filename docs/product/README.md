# Askora Product 文档索引

> 状态：Current Product Authority Index  
> 适用范围：Askora 产品战略、定位与下游设计治理

`docs/product/` 只保存长期稳定、需要被后续 Design / ADR / Spec / EXEC 共同遵守的产品级事实。它不保存临时研究过程、实时 backlog、页面级 UX、系统实现合同或工程执行细节。

## 1. Canonical Product Documents

```text
docs/product/
├── README.md
├── PRODUCT-STRATEGY.md
└── PRODUCT-POSITIONING.md
```

### `PRODUCT-STRATEGY.md`

回答：

> **为什么做、为谁做、解决什么问题、创造什么价值、如何判断成功？**

它拥有：

- Opportunity / Problem Space；
- Primary User / Non-target User；
- JTBD / Unmet Need；
- Product Vision；
- Value Proposition；
- Strategic Differentiation；
- Product Principles；
- Strategic Assumptions / Risks；
- Product / Learning Success Definition。

它是 Askora 的**最高产品战略意图来源**，但不是直接实现合同。尚未验证的判断必须显式标记为 `ASSUMPTION` / `RESEARCH GAP`，不得伪装成已验证用户事实。

### `PRODUCT-POSITIONING.md`

回答：

> **Askora 是什么、不是什么、允许成为什么、哪些产品边界不能被下位设计突破？**

它拥有：

- Category Definition；
- What Askora Is / Is Not；
- v1 Product Shape；
- Strategic Constraints；
- Non-goals；
- Deferred Strategic Decisions；
- Product-boundary Change Control。

它必须服从 `PRODUCT-STRATEGY.md`，并继续作为 **Canonical Design / ADR / Spec / EXEC / Code 的最高可执行产品边界**。

## 2. Authority Chain

```text
PRODUCT-STRATEGY.md
        ↓ strategic intent
PRODUCT-POSITIONING.md
        ↓ enforceable product boundary
Canonical Design / Design Delta
        ↓
Accepted ADR
        ↓
Implementation Specs
        ↓
Vertical Slice / EXEC / Linear Issue
        ↓
Code / Tests / Release Evidence
```

解释：

- `PRODUCT-STRATEGY` 决定为什么、为谁、什么结果值得优化；
- `PRODUCT-POSITIONING` 把战略转化为产品类别、Scope、Non-goals 与 Hard Boundaries；
- 下游 Design / ADR / Spec 决定产品行为和软件行为如何具体成立；
- Linear 负责当前工作状态，不成为长期产品 truth。

如果 Strategy 与 Positioning 冲突，先解决 Strategy/Positioning 冲突；如果 Positioning 与下游文档冲突，下游必须收敛，不能反向用实现覆盖产品边界。

## 3. 明确不属于 `docs/product/`

以下内容不得因为“很重要”就继续上提到 Product 文档：

### Product Definition / Domain

例如：

- Workspace / Project / Material 的精确关系；
- Goal 层级；
- capability/state machine；
- acceptance criteria；
- 具体 import formats / lifecycle mechanics。

这些应进入 Canonical Design / ADR / Specs。

### Experience / Interface Design

例如：

- 顶层导航；
- 页面职责；
- 页面布局；
- User Flow；
- Interactive Elements；
- Design System。

这些由 `docs/design/` 与 `docs/specs/ui/` 管理。

### Architecture / Technical Design

例如：

- database schema；
- SQLite mechanics；
- API payload；
- RetrievalScope fields；
- SecretStore adapter；
- retry / concurrency；
- background job state；
- schema migration algorithm；
- logging / replay implementation。

这些由 `docs/adr/` 与 `docs/specs/` 管理。

### Research

Research 回答“为什么相信这个结论”，可以保存证据、反例、竞争分析和实验结果，但不能形成第二套产品规范。当前 Learning Core 研究仍位于 [`../design/research/`](../design/research/README.md)；未来若建立顶层 `docs/research/`，迁移本身不得改变 research authority。

### Current Work Status

Issue、Project、Milestone、优先级、依赖与执行状态以 Linear 为工作管理事实源。GitHub 只保存长期有效的产品决策、合同与历史证据。

## 4. Change Control

任何 Product Strategy 或 Product Positioning 变更都必须：

1. 说明触发它的新证据或新约束；
2. 明确哪些原结论被 supersede；
3. 评估对 Design / ADR / Specs / implementation 的影响；
4. 由用户明确接受后重新冻结；
5. 再进入下游设计与工程任务。

Codex / AI Agent 不得因为某种实现更方便，就自行修改 Product Strategy 或 Product Positioning。
