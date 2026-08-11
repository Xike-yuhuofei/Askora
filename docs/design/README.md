# Askora Design 文档索引

> 状态：Canonical Design Index  
> 最近校准：2026-08-11

所有 Canonical Design 在形成或修改前，必须先读取：

1. [`../product/PRODUCT-STRATEGY.md`](../product/PRODUCT-STRATEGY.md) — Why / User / Value / Success；
2. [`../product/PRODUCT-POSITIONING.md`](../product/PRODUCT-POSITIONING.md) — Category / Product Shape / Hard Boundaries；
3. [`../product/PRODUCT-DEFINITION.md`](../product/PRODUCT-DEFINITION.md) — Product Objects / Capabilities / Rules / Requirements / Product Acceptance / v1 Scope。

Design 可以细化**已定义产品能力如何成立**，但不得自行改变 Target User、核心 Problem、Success Definition、Product Category、Capability taxonomy、v1 Feature Scope 或 Product Acceptance。

## 1. Current Canonical Design

`docs/design/` 当前主要正式设计：

### Product / Learning System

- [个人 AI 辅助学习平台设计方案](learning/个人AI辅助学习平台设计方案.md)：整体产品语义、学习闭环与系统级设计基线；其中上位 Problem / Vision / Success 语义服从当前 Product Strategy，Product Capability / Requirement 语义服从 Product Definition；
- [AI 学习系统算法与教学内核设计](learning/AI学习系统算法与教学内核设计.md)：学习科学、八系统边界、Teaching Policy 与学习效果验证；
- [v0.3 Canonical Design Delta](learning/v0.3-Canonical-Design-Delta.md)：DR-03-01～04 到 Adaptive Teaching Loop 的 Canonical Decision Register、breaking change 与 change-control；
- [Learning Conversation Message System Canonical Design Delta](features/Learning-Conversation-Message-System-Canonical-Design-Delta.md)：LearningActivity-scoped SYS08 message/transcript artifact、six typed blocks、capability dispatch 与跨 owner 状态拆分；
- [Course-centric Information Architecture Canonical Design Delta](features/course-centric-information-architecture-canonical-design-delta.md)：用户侧「课程」词汇、Course-centric L0、Course/Activity switching、default entry、creation journey 与 route migration；canonical Workspace identity 保持不变；
- [Local Single-User Identity & Authentication Removal Canonical Design Delta](features/Local-Single-User-Identity-Authentication-Removal-Canonical-Design-Delta.md)：LocalOwner、无 Account/Login/JWT/AuthSession 与 loopback identity boundary；
- [P1-03 Data Control and Recovery](features/p1-03-data-control-and-recovery.md)：本地数据恢复、导出、删除与 no-resurrection 设计；
- [P1-06 事实驱动的首次学习旅程设计](features/p1-06-fact-driven-first-use-journey.md)：first-use readiness、presentation preference 与首次学习闭环。

### Experience & Interface Design

当前 Experience Design 的长期 Authority 集中在：

- [Experience Architecture](experience/EXPERIENCE-ARCHITECTURE.md)：Experience Principles、user-facing IA、Workspace Experience、Navigation Model、Core Journeys 与 surface responsibility；
- [Learning Experience](experience/LEARNING-EXPERIENCE.md)：LearningActivity、Learning Conversation、Attempt、Feedback、Remediation、Assistance、Evidence/Provenance、Notes 与长期学习连续性；
- [Interaction Model](experience/INTERACTION-MODEL.md)：7 类 semantic interaction primitives、interaction hierarchy、progressive disclosure 与 component boundary。

这三份文件保存**当前有效体验模型**。实现与 UI Spec 不应再通过历史 Delta + Supersession Matrix 自行推断 current truth。

## 2. Historical / Superseded Design Records

以下文件继续保留作为设计演进记录，但不再作为新的 UI/UX 实现入口：

- [UX Architecture Canonical Design Delta](../archive/design/UX-Architecture-Canonical-Design-Delta.md)：ADR-0018 前后的 UX Architecture 增量冻结记录；其当前有效结论已吸收到 `experience/EXPERIENCE-ARCHITECTURE.md` 与 `experience/LEARNING-EXPERIENCE.md`；
- [Interactive Element System Canonical Design Delta](../archive/design/Interactive-Element-System-Canonical-Design-Delta.md)：ADR-0014 交互体系增量记录；其当前有效语义已吸收到 `experience/INTERACTION-MODEL.md`；
- [账号与隐私生命周期设计](../archive/design/账号与隐私生命周期设计.md)：Account/Login/AuthSession 等语义已被 Local Single-User Identity Delta + ADR-0015 supersede；
- [P1-02 Model Settings](../archive/design/p1-02-model-settings.md)：Desktop/Electron 实现语义属于历史基线；当前 Local Web BYOK 服从最新 ADR / Specs。

历史 Design Delta 的目的为回答“为什么发生变化”，而不是继续与 current Canonical Design 形成双重事实源。

## 3. Design Boundary

Canonical Design 负责：

- 将 Product Capability / Requirement 转化为清晰的产品/领域/学习语义；
- Learning Core 的教学、证据和状态模型；
- UX Architecture / user flow / interaction semantics；
- shared semantic decisions 在进入 ADR / Spec 前的冻结；
- 在 ADR 已接受后，将增量设计 consolidation 为 current canonical model。

Canonical Design 不负责：

- 重新定义 Product Strategy；
- 突破 Product Positioning；
- 新增/删除 Product Capability 或决定 v1 Feature inclusion；
- 将 Product Requirement 重新写成第二套产品规范；
- 把市场/用户假设写成已验证事实；
- 保存当前 Linear backlog；
- 直接定义数据库 schema、API payload、retry、job queue、migration、logging 等 implementation mechanics；
- 用历史 Gap Analysis 代替 current `main` 检查。

如果 Design 发现 Capability / Feature Scope / Product Rule / Product Acceptance 缺失，应报告 `PRODUCT DEFINITION GAP`，而不是在 Design 中永久承担该产品定义职责。

## 4. Product Information Model vs Experience Information Architecture

Product Definition 拥有：

```text
Workspace / LearningProject / Material / Goal / Plan / Activity / Evidence / History
是什么、为什么存在、应满足什么产品行为
```

Experience Design 拥有：

```text
用户在哪里看到它
如何导航
如何形成 Task Flow
是否 page / drawer / rail
如何 progressive disclose
```

Askora 中 `Information Architecture` 专指后者。页面结构不能反向定义 Product Object / Capability taxonomy。

具体 route / URL / deep-link compatibility 属 UI Spec；`current_workspace_id`、read projection、revision、persistence 属 Architecture / Interface Spec。

## 5. Formation Chain

Askora 当前形成链：

```text
PRODUCT-STRATEGY
→ PRODUCT-POSITIONING
→ PRODUCT-DEFINITION
→ Canonical Design / Design Delta
→ Accepted ADR
→ Current Canonical Design Consolidation（适用时）
→ Canonical Specs
→ Vertical Slice / EXEC / Linear Issue
→ Implementation
→ Verification / Product Evidence / Learning Evidence
```

下游实现不得反向覆盖 Product 文档。

### Experience / UI

```text
PRODUCT-STRATEGY
→ PRODUCT-POSITIONING
→ PRODUCT-DEFINITION
→ Learning / Domain Canonical Design
→ Experience Canonical Design
   ├─ experience/EXPERIENCE-ARCHITECTURE.md
   ├─ experience/LEARNING-EXPERIENCE.md
   └─ experience/INTERACTION-MODEL.md
→ Accepted UI/UX ADR（已有决策继续约束 current design）
→ docs/specs/ui/**
→ Frontend Technical Specs
→ EXEC / Linear
→ Frontend Implementation
```

顶层导航、页面布局、页面级 IA、Interaction semantics 与具体 UX Flow 由 Experience Design / UI Specs 冻结；但“某能力是否属于 v1”必须来自 Product Definition，而不是 UI 自己决定。

### Local Identity

```text
PRODUCT-POSITIONING
→ PRODUCT-DEFINITION CAP-08 / PD-RULE-008 / PD-REQ-0801..
→ Local Single-User Identity Canonical Design Delta
→ ADR-0015
→ docs/specs/platform/identity-privacy-lifecycle.md
→ EXEC / Migration / Implementation
```

### Learning Core

```text
PRODUCT-DEFINITION CAP-02..07 / Product Rules
+
Research Evidence / Synthesis
→ AI 学习系统算法与教学内核设计
→ v0.3 Canonical Design Delta
→ ADR-0001 / ADR-0002
→ docs/specs/systems/**
→ EXEC / Implementation / OPVE / Learning Evidence
```

### Learning Conversation Message System

```text
PRODUCT-DEFINITION CAP-04..07
+ v0.3 Learning Core / ADR-0004/0005
→ Learning Conversation Message System Canonical Design Delta
→ ADR-0020
→ LCMS Interface Spec / Vertical Slice
→ EXEC-075
→ Implementation / Verification
```

Message/Conversation 在该链中仍是 LearningActivity-scoped presentation/transcript artifact，不成为核心学习领域模型或 Learning Evidence。

## 6. Research Boundary

[`../research/learning-core/`](../research/learning-core/README.md) 保存：

- evidence；
- Deep Research；
- synthesis；
- historical diagnosis；
- experiment design。

Research 回答“为什么相信这个设计”，但：

> **Research 不是第三套 Canonical Product Definition，也不是直接实现合同。**

Product Strategy / Definition 可以引用 Research 的结论；Design 可以吸收 Research 后重新冻结；实现不得直接从历史 Research 自行创造新产品范围或新语义。

## 7. Conformance / Gap Analysis Lifecycle

Gap Analysis 是**带 commit/time 边界的审计快照**，不是永久 current truth。

当前已存在：

- [v1 Product Positioning — Current Main Conformance Gap Analysis](../archive/audits/v1-Product-Positioning-Current-Main-Conformance-Gap-Analysis.md)：Historical Snapshot；判断 current conformance 必须重新读取 current `main`；
- [v0.3 Current Main Conformance Gap Analysis](../archive/audits/v0.3-Current-Main-Conformance-Gap-Analysis.md)：Historical Snapshot；其 Teaching Policy production gap 已由后续 closure 处理；
- [CI / Test Infrastructure Gap Analysis](../archive/audits/CI-Test-Infrastructure-Gap-Analysis.md)：Quality / CI 审计文档，判断 current 状态时仍需核对其 audited SHA 与最新 main。
- [Course-centric IA Current-state Gap Analysis](../archive/audits/course-centric-ia-current-state-gap-analysis.md)：`origin/main@6a94cf7b` 的变更前审计快照；current IA 以 ADR-0022 + current Experience/UI contracts 为准。

规则：

```text
Gap Analysis conclusion
valid only for audited SHA/time
```

Product Definition 建立后，新的 current conformance 审查还应明确区分：

- `DESIGN–DEFINITION GAP`；
- `DEFINITION–SYSTEM GAP`；
- `DEFINITION–IMPLEMENTATION GAP`；
- `DESIGN–IMPLEMENTATION GAP`。

## 8. Current Implementation Contract

Design 不是最终代码接口合同。实现时必须继续读取：

- [`../product/PRODUCT-DEFINITION.md`](../product/PRODUCT-DEFINITION.md)；
- [`../architecture/README.md`](../architecture/README.md)；
- [`../specs/README.md`](../specs/README.md)；
- 目标 Experience Canonical Design；
- 目标系统/接口/UI 的当前 Spec；
- 对应 Linear Issue / EXEC。

如果 Design 与 current Product Definition / Accepted ADR / Spec 存在真实冲突，应先按 authority chain 处理，而不是让 Codex 自行选择其中一套。
