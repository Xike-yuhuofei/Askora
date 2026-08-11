# Askora Design 文档索引

> 状态：Canonical Design Index  
> 最近校准：2026-08-11

所有 Canonical Design 在形成或修改前，必须先读取：

1. [`../product/PRODUCT-STRATEGY.md`](../product/PRODUCT-STRATEGY.md) — Why / User / Value / Success；
2. [`../product/PRODUCT-POSITIONING.md`](../product/PRODUCT-POSITIONING.md) — Category / Product Shape / Hard Boundaries。

Design 可以细化产品应该如何工作，但不得自行改变 Target User、核心 Problem、Success Definition，也不得突破 Product Positioning 的 v1 Scope / Non-goals。

## 1. Current Canonical Design

`docs/design/` 当前主要正式设计：

- [个人 AI 辅助学习平台设计方案](个人AI辅助学习平台设计方案.md)：整体产品语义、学习闭环与系统级设计基线；其中上位 Problem / Vision / Success 语义服从当前 Product Strategy；
- [AI 学习系统算法与教学内核设计](AI学习系统算法与教学内核设计.md)：学习科学、八系统边界、Teaching Policy 与学习效果验证；
- [v0.3 Canonical Design Delta](v0.3-Canonical-Design-Delta.md)：DR-03-01～04 到 Adaptive Teaching Loop 的 Canonical Decision Register、breaking change 与 change-control；
- [UX Architecture Canonical Design Delta](UX-Architecture-Canonical-Design-Delta.md)：用户任务驱动的 UX Architecture、Workspace 学习工作台及页面职责边界；
- [Interactive Element System Canonical Design Delta](Interactive-Element-System-Canonical-Design-Delta.md)：Interactive Element Taxonomy、Interaction Hierarchy、页面级信息与交互模型；
- [Local Single-User Identity & Authentication Removal Canonical Design Delta](Local-Single-User-Identity-Authentication-Removal-Canonical-Design-Delta.md)：LocalOwner、无 Account/Login/JWT/AuthSession 与 loopback identity boundary；
- [P1-03 Data Control and Recovery](p1-03-data-control-and-recovery.md)：本地数据恢复、导出、删除与 no-resurrection 设计；
- [P1-06 事实驱动的首次学习旅程设计](p1-06-fact-driven-first-use-journey.md)：first-use readiness、presentation preference 与首次学习闭环。

历史设计：

- [账号与隐私生命周期设计](账号与隐私生命周期设计.md)：Account/Login/AuthSession 等语义已被 Local Single-User Identity Delta + ADR-0015 supersede；
- [P1-02 Model Settings](p1-02-model-settings.md)：Desktop/Electron 实现语义属于历史基线；当前 Local Web BYOK 服从最新 ADR / Specs。

## 2. Design Boundary

Canonical Design 负责：

- 产品与领域语义如何组织；
- Learning Core 的教学、证据和状态模型；
- UX Architecture / user flow / interaction semantics；
- shared semantic decisions 在进入 ADR / Spec 前的冻结。

Canonical Design 不负责：

- 重新定义 Product Strategy；
- 把市场/用户假设写成已验证事实；
- 保存当前 Linear backlog；
- 直接定义数据库 schema、API payload、retry、job queue、migration、logging 等 implementation mechanics；
- 用历史 Gap Analysis 代替 current `main` 检查。

## 3. Formation Chain

Askora 当前形成链：

```text
PRODUCT-STRATEGY
→ PRODUCT-POSITIONING
→ Canonical Design / Design Delta
→ Accepted ADR
→ Canonical Specs
→ Vertical Slice / EXEC / Linear Issue
→ Implementation
→ Verification / Product Evidence / Learning Evidence
```

下游实现不得反向覆盖 Product 文档。

### UI / Interactive Elements

```text
PRODUCT-STRATEGY（User / Job / Success）
→ PRODUCT-POSITIONING（产品边界，不冻结页面 UX）
→ UX / Interactive Element Canonical Design
→ ADR-0014 / current UI ADR
→ docs/specs/ui/**
→ EXEC
→ Frontend Implementation
```

顶层导航、页面布局、页面级 IA、按钮/入口与具体 UX Flow 继续由 Design / UI Specs 冻结，不回填到 Product Positioning。

### Local Identity

```text
PRODUCT-POSITIONING
→ Local Single-User Identity Canonical Design Delta
→ ADR-0015
→ docs/specs/platform/identity-privacy-lifecycle.md
→ EXEC / Migration / Implementation
```

### Learning Core

```text
Research Evidence / Synthesis
→ AI 学习系统算法与教学内核设计
→ v0.3 Canonical Design Delta
→ ADR-0001 / ADR-0002
→ docs/specs/systems/**
→ EXEC / Implementation / OPVE / Learning Evidence
```

## 4. Research Boundary

[`research/`](research/README.md) 保存：

- evidence；
- Deep Research；
- synthesis；
- historical diagnosis；
- experiment design。

Research 回答“为什么相信这个设计”，但：

> **Research 不是第三套 Canonical Design，也不是直接实现合同。**

Product Strategy 可以引用 Research 的结论；Design 可以吸收 Research 后重新冻结；实现不得直接从历史 Research 自行创造新语义。

## 5. Conformance / Gap Analysis Lifecycle

Gap Analysis 是**带 commit/time 边界的审计快照**，不是永久 current truth。

当前已存在：

- [v1 Product Positioning — Current Main Conformance Gap Analysis](v1-Product-Positioning-Current-Main-Conformance-Gap-Analysis.md)：**Historical Snapshot**，审计基于 `main@da2942e1be69c817d4e2ba36663ef802a61762b1`。其 `PRODUCT_POSITIONING_CONFORMANCE = FAIL` 只代表该 SHA；后续 Workspace / Retrieval / Material lifecycle / runtime conformance closure 已进入更新后的 `main`，不得继续把该 FAIL 描述为当前事实；
- [v0.3 Current Main Conformance Gap Analysis](v0.3-Current-Main-Conformance-Gap-Analysis.md)：Historical Snapshot；其 Teaching Policy production gap 已由后续 closure 处理；
- [CI / Test Infrastructure Gap Analysis](CI-Test-Infrastructure-Gap-Analysis.md)：Quality / CI 审计文档，判断 current 状态时仍需核对其 audited SHA 与最新 main。

规则：

```text
Gap Analysis conclusion
valid only for audited SHA/time
```

如果要声称 current conformance，必须重新读取 current `main`、当前 Specs、测试与 CI。

## 6. Current Implementation Contract

Design 不是最终代码接口合同。实现时必须继续读取：

- [`../adr/README.md`](../adr/README.md)；
- [`../specs/README.md`](../specs/README.md)；
- 目标系统/接口/UI 的当前 Spec；
- 对应 Linear Issue / EXEC。

如果 Design 与 current Accepted ADR / Spec 存在真实冲突，应先按 authority chain 处理，而不是让 Codex自行选择其中一套。
