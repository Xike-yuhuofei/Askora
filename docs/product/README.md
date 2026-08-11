# Askora Product 文档索引

> 状态：Current Product Authority Index  
> 适用范围：Askora 产品战略、定位、定义与下游设计治理

`docs/product/` 只保存长期稳定、需要被后续 Design / ADR / Spec / EXEC 共同遵守的产品级事实。它不保存临时研究过程、实时 backlog、页面级 UX、系统实现合同或工程执行细节。

## 1. Canonical Product Documents

```text
docs/product/
├── README.md
├── PRODUCT-STRATEGY.md
├── PRODUCT-POSITIONING.md
└── PRODUCT-DEFINITION.md
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

它必须服从 `PRODUCT-STRATEGY.md`，并继续作为 Product Definition / Canonical Design / ADR / Spec / EXEC / Code 的**最高可执行产品边界**。

### `PRODUCT-DEFINITION.md`

回答：

> **为了履行已经冻结的 Strategy / Positioning，Askora 具体必须具备什么产品能力和用户可观察行为？**

它拥有：

- Product Actors；
- Core Product Objects；
- Product Capability Model；
- Capability / Feature / Scenario / Requirement 层级；
- Product Rules；
- Product-level Functional Requirements；
- Product-level NFR boundary；
- Product Acceptance Model；
- v1 Current / Deferred / Experimental / Retired scope semantics；
- GitHub Product Definition ↔ Linear work mapping。

它不拥有页面布局、导航实现、Teaching Policy 算法、API、SQLite schema、class/module 或实时 backlog。

复杂且长期独立演进的 Feature MAY 以后拆入 `docs/product/features/`；在第一份真实 Feature Spec 出现前不预建空目录或占位文件。

## 2. Authority Chain

```text
PRODUCT-STRATEGY.md
        ↓ strategic intent
PRODUCT-POSITIONING.md
        ↓ enforceable product boundary
PRODUCT-DEFINITION.md
        ↓ capabilities / observable product behavior / product acceptance
Canonical Design / Design Delta
        ↓
Accepted ADR
        ↓
Implementation / Quality Specs
        ↓
Vertical Slice / EXEC / Linear Issue
        ↓
Code / Tests / Release Evidence
```

解释：

- `PRODUCT-STRATEGY` 决定为什么、为谁、什么结果值得优化；
- `PRODUCT-POSITIONING` 把战略转化为产品类别、Scope、Non-goals 与 Hard Boundaries；
- `PRODUCT-DEFINITION` 冻结产品必须具备的能力、对象、规则、要求与 Product Acceptance；
- 下游 Design / ADR / Spec 决定这些产品能力如何在人机体验、教学系统和软件系统中具体成立；
- Linear 负责当前工作状态，不成为长期产品 truth。

如果 Strategy 与 Positioning 冲突，先解决 Strategy/Positioning；如果 Definition 突破 Positioning，必须回到 Product 层重新冻结；如果 Definition 与下游 Design / ADR / Spec 冲突，下游必须收敛，不能反向用实现覆盖产品定义。

## 3. Product Definition Boundary

### 属于 Product Definition

例如：

- Workspace / LearningProject / Material / Goal / Activity / Evidence 在**产品语义上是什么**；
- Product Capability taxonomy；
- 一个 capability 应产生什么用户可观察结果；
- v1 是否承诺某个 feature；
- Business / Product Rule；
- Product Requirement；
- Product Acceptance Criteria；
- Product-level NFR；
- Product vocabulary。

### 不属于 Product Definition

以下继续由下位设计与合同拥有：

- exact cardinality / DB schema / ORM；
- API payload；
- state machine implementation；
- RetrievalScope fields；
- SecretStore adapter；
- retry / concurrency；
- background job state；
- schema migration algorithm；
- logging / replay implementation；
- Teaching Policy scoring / mastery estimation algorithm。

产品文档可以引用这些技术合同，但不得复制维护第二份 implementation truth。

## 4. Experience / Interface Design Boundary

以下由 `docs/design/` 与 `docs/specs/ui/` 管理：

- 顶层导航；
- 页面职责；
- 页面布局；
- User Flow；
- Interactive Elements；
- Design System；
- route / screen / drawer / right rail；
- progressive disclosure。

Askora 中 `Information Architecture` 专指**用户如何看到、找到和操作信息**。Product Definition 中的 Workspace / Material / Goal / Evidence 等属于 Product Object / Information Model，不再与 Experience IA 混用。

## 5. Teaching / Architecture / Quality Boundary

### Teaching / AI Design

Product Definition 可以要求：

> 系统应根据新的学习证据调整下一步学习活动。

但具体 TeachingStage、StrategyFamily、PolicyBundle、anti-oscillation、mastery estimation 等由 Teaching Canonical Design / Specs 定义。

### Architecture / Technical Design

Product Definition 可以要求：

> 普通 Material 删除后必须可恢复。

但 tombstone、SQLite transaction、command、file deletion order、migration 与 API 属于 ADR / Specs。

### Quality

Product Definition 可以冻结用户可感知的 durability / privacy / failure honesty 等产品级 NFR；具体 threshold、test oracle、CI、security / performance / accessibility 验证由 `docs/specs/quality/**` 管理。

## 6. Research Boundary

Research 回答“为什么相信这个结论”，可以保存证据、反例、竞争分析和实验结果，但不能形成第二套产品规范。当前 Product Discovery 研究位于 [`../research/product-discovery/`](../research/product-discovery/)，Learning Core 研究位于 [`../research/learning-core/`](../research/learning-core/README.md)。Research 只有被 Strategy / Positioning / Product Definition / Canonical Design 正式吸收后，才成为下游约束。

## 7. Current Work Status

Issue、Project、Milestone、优先级、依赖与执行状态以 Linear 为工作管理事实源。GitHub 不维护第二套实时 Feature Backlog。

推荐映射：

```text
CAP-* / PD-REQ-* / PD-AC-*
        ↓ reference
Linear Initiative: Askora
→ workflow-specific Project
→ Milestone
→ Issue
→ EXEC when needed
→ implementation / verification
```

## 8. Change Control

任何 Product 层变化必须先判断变化属于哪一层：

- Primary User / Problem / JTBD / Value / Success → `PRODUCT-STRATEGY.md`；
- Category / Product Shape / Hard Boundary / Non-goal → `PRODUCT-POSITIONING.md`；
- Capability / Product Object / Product Rule / Requirement / Product Acceptance / v1 feature scope → `PRODUCT-DEFINITION.md` 或明确 Product Feature Spec。

Product Definition 变化必须：

1. 说明上游依据或触发它的新证据；
2. 明确受影响的 Capability / Requirement / Product AC；
3. 评估对 Experience / Teaching / Architecture / Quality 的 downstream impact；
4. 明确 supersession / migration consequence；
5. 再转化为 Linear 工作。

Codex / AI Agent 不得因为某种实现更方便，就自行修改 Product Strategy、Product Positioning 或 Product Definition。
