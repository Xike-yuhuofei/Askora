# Askora Design 文档索引

> 状态：Canonical Design 索引

所有 Canonical Design 在形成或修改前，必须先读取并服从 [`../product/PRODUCT-POSITIONING.md`](../product/PRODUCT-POSITIONING.md)。Product Positioning 是 Design 的上位产品约束；Canonical Design 可以细化产品如何实现，但不得自行扩大 v1 Scope、突破 Non-goals 或改写 Hard Constraints。

若设计任务必须突破 Product Positioning，必须先提出 Product Positioning Delta，并由用户接受后更新、重新冻结上位文档，再继续形成 Canonical Design / ADR / Spec。

`docs/design/` 保留正式设计基线与经用户授权形成的增量 Canonical Design：

- [UX Architecture Canonical Design Delta](UX-Architecture-Canonical-Design-Delta.md)：冻结 Left Where / Center Learn / Right Notes-Reference 三栏式学习架构、真实 Workspace 上下文、默认收起的 Learning Context Drawer、Learning 去 Goal/Plan/Progress 管理化、Library v1 去 OCR 暴露及后续辅助栏候选的 deferred 边界；在对应 ADR + Spec + EXEC 完成前不得直接修改产品代码；
- [Local Single-User Identity & Authentication Removal Canonical Design Delta](Local-Single-User-Identity-Authentication-Removal-Canonical-Design-Delta.md)：冻结 Askora 本地单用户、无 Account/Login/JWT/AuthSession 的身份模型，建立 LocalOwnerContext、loopback-only 安全边界、旧学习数据 ownership migration 与 Settings/Onboarding 去账号化；在身份语义上 supersede 旧账号生命周期设计；
- [Interactive Element System Canonical Design Delta](Interactive-Element-System-Canonical-Design-Delta.md)：冻结 Askora 的 Interactive Element Taxonomy、Zero-Based Home、L0/L1 信息架构、Interaction Hierarchy、Semantic → Interaction 映射、Settings/Library progressive disclosure，以及现有 `UI-IA/UI-SCREEN/UI-VIS` 的 supersession 输入；在对应 ADR + Spec 更新完成前，它不是直接实现合同；
- [v0.3 Canonical Design Delta](v0.3-Canonical-Design-Delta.md)：DR-03-01～04 / Research Synthesis 到 v0.3 Canonical Design 的冻结变更记录、Canonical Decision Register、breaking change、migration 与 change-control 边界；
- [个人 AI 辅助学习平台设计方案](个人AI辅助学习平台设计方案.md)：产品范围、总体架构、学习闭环和发布证据边界；
- [AI 学习系统算法与教学内核设计](AI学习系统算法与教学内核设计.md)：学习科学、八系统边界、Teaching Policy 和学习效果验证；
- [账号与隐私生命周期设计](账号与隐私生命周期设计.md)：**历史设计基线**；其中 Account/Login/AuthSession/Recovery/Account Deletion 语义已由 Local Single-User Identity Delta + ADR-0015 supersede；
- [P1-03 Data Control and Recovery](p1-03-data-control-and-recovery.md)：本地数据导出、删除与防复活边界；账号认证相关语义必须服从 ADR-0015 / `LID-*`；
- [P1-06 事实驱动的首次学习旅程设计](p1-06-fact-driven-first-use-journey.md)：presentation-only preference、owner-fact readiness、首次 activity completion 与恢复/路由边界；首次 journey 不再依赖 register/login。

当前实现一致性审计：

- [v1 Product Positioning — Current Main Conformance Gap Analysis](v1-Product-Positioning-Current-Main-Conformance-Gap-Analysis.md)：基于 `main@da2942e1be69c817d4e2ba36663ef802a61762b1` 对 frozen v1 Product Positioning 与真实 runtime/data/API surface 的一致性快照；结论为 `PRODUCT_POSITIONING_CONFORMANCE = FAIL`，它不是新的 Canonical Design、ADR 或 Spec；
- [v0.3 Current Main Conformance Gap Analysis](v0.3-Current-Main-Conformance-Gap-Analysis.md)：历史上针对 frozen v0.3 Design/Spec 的实现一致性快照；其 Teaching Policy production gap 已由 EXEC-042 关闭，后续状态以 release evidence 与更新审计为准；
- [CI / Test Infrastructure Gap Analysis](CI-Test-Infrastructure-Gap-Analysis.md)：当前 CI/Test Infrastructure 与 v1 Local Web/Product Positioning 对齐审计。

## 上下游形成链

Askora 的标准治理链固定为：

```text
Product Positioning
→ Canonical Design
→ Accepted ADR
→ Canonical Specs
→ Vertical Slice / EXEC
→ Implementation
```

任何下游层级不得反向覆盖 Product Positioning。

Interactive Element System Delta 的后续形成链固定为：

```text
PRODUCT-POSITIONING（只提供产品边界，不冻结页面级 UX）
→ Interactive Element System Canonical Design Delta
→ Accepted UI Information / Interaction Architecture ADR
→ 更新 docs/specs/ui/**
→ Vertical Slice / EXEC
→ Frontend Implementation
```

**顶层导航、首页职责、页面布局、页面级信息架构、按钮/入口与具体 UX Flow 继续在 Interactive Elements 设计系统中冻结，不在 Product Positioning 中冻结。**

Local Single-User Identity formation chain：

```text
PRODUCT-POSITIONING（Single-user / no-login / Local Web boundary）
→ Local Single-User Identity Canonical Design Delta
→ ADR-0015 accepted
→ docs/specs/platform/identity-privacy-lifecycle.md v2.0 (LID-*)
→ Authentication Removal Vertical Slice / EXEC
→ Implementation / Migration / Release Evidence
```

当前身份实现必须服从 Product Positioning + ADR-0015 + `LID-*`；旧 P1-05 Account Lifecycle 只作为历史 implemented baseline，不得作为新代码合同。

v1 Product Positioning 当前实现闭环固定为：

```text
PRODUCT-POSITIONING
→ v1 Current-Main Conformance Audit
→ 必要的 Canonical Design / ADR / Spec Delta
→ v1 Product Architecture Linear Project
→ EXEC
→ Codex Implementation
→ Current Main + Required CI independent acceptance
```

其中 Workspace/LearningProject durable aggregate 仍需要 implementation-ready contract closure；Standalone Local Runtime 已有足够上位合同，可以直接进入 focused EXEC；BYOK 的 `LocalSecretStore` 若实现机制无法由现有 `MODEL-CONFIG-*` 唯一确定，必须先补窄 ADR/Spec，不得让 Codex自行选择安全模型。

其他既有设计分别通过 ADR-0001/0002、ADR-0009、ADR-0103、ADR-0106、ADR-0107、ADR-0014 与 ADR-0015 等转换为实现合同。实现时仍以 [`../product/PRODUCT-POSITIONING.md`](../product/PRODUCT-POSITIONING.md) 为产品级最高约束，并以 [`../specs/README.md`](../specs/README.md) 与各目标 Spec 最新状态为直接实现合同。

[`research/`](research/README.md) 保存设计证据、历史诊断和研究推导。Research 不是第三份 Canonical Design，也不能覆盖 Product Positioning 或 Spec。
