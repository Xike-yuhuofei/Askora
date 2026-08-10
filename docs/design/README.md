# Askora Design 文档索引

> 状态：Canonical Design 索引

`docs/design/` 保留正式设计基线与经用户授权形成的增量 Canonical Design：

- [Interactive Element System Canonical Design Delta](Interactive-Element-System-Canonical-Design-Delta.md)：冻结 Askora 的 Interactive Element Taxonomy、Zero-Based Home、L0/L1 信息架构、Interaction Hierarchy、Semantic → Interaction 映射、Settings/Library progressive disclosure，以及现有 `UI-IA/UI-SCREEN/UI-VIS` 的 supersession 输入；在对应 ADR + Spec 更新完成前，它不是直接实现合同；
- [v0.3 Canonical Design Delta](v0.3-Canonical-Design-Delta.md)：DR-03-01～04 / Research Synthesis 到 v0.3 Canonical Design 的冻结变更记录、Canonical Decision Register、breaking change、migration 与 change-control 边界；
- [个人 AI 辅助学习平台设计方案](个人AI辅助学习平台设计方案.md)：产品范围、总体架构、学习闭环和发布证据边界；
- [AI 学习系统算法与教学内核设计](AI学习系统算法与教学内核设计.md)：学习科学、八系统边界、Teaching Policy 和学习效果验证。
- [账号与隐私生命周期设计](账号与隐私生命周期设计.md)：本地优先 Identity、durable session、离线恢复与 owner-safe 数据删除。
- [P1-03 Data Control and Recovery](p1-03-data-control-and-recovery.md)：私人桌面恢复包、导出、删除与防复活边界。
- [P1-06 事实驱动的首次学习旅程设计](p1-06-fact-driven-first-use-journey.md)：presentation-only preference、owner-fact readiness、首次 activity completion 与恢复/路由边界。

当前实现一致性审计：

- [v0.3 Current Main Conformance Gap Analysis](v0.3-Current-Main-Conformance-Gap-Analysis.md)：基于指定 `main` commit 对 frozen v0.3 Design/Spec 与真实 production path 的一致性快照；它不是新的 Canonical Design 或实现合同。

Interactive Element System Delta 的后续形成链固定为：

```text
Interactive Element System Canonical Design Delta
→ Accepted UI Information / Interaction Architecture ADR
→ 更新 docs/specs/ui/**
→ Vertical Slice / EXEC
→ Frontend Implementation
```

在上述 ADR + Spec 更新完成前，当前 `docs/specs/ui/**` 仍是 UI 实现的直接合同，不得先修改 React 再用 Design Delta 追认。

其他既有设计分别通过 ADR-0001/0002、ADR-0009、ADR-0103、ADR-0106 与 ADR-0107 等转换为实现合同。实现时仍以 [`../specs/README.md`](../specs/README.md) 为直接权威来源。

[`research/`](research/README.md) 保存设计证据、历史诊断和研究推导。Research 不是第三份 Canonical Design，也不能覆盖 Spec。
