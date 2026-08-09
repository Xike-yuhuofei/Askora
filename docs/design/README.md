# Askora Design 文档索引

> 状态：v0.3 Canonical Design 索引

`docs/design/` 保留三份正式设计基线：

- [个人 AI 辅助学习平台设计方案](个人AI辅助学习平台设计方案.md)：产品范围、总体架构、学习闭环和发布证据边界；
- [AI 学习系统算法与教学内核设计](AI学习系统算法与教学内核设计.md)：学习科学、八系统边界、Teaching Policy 和学习效果验证。
- [账号与隐私生命周期设计](账号与隐私生命周期设计.md)：本地优先 Identity、durable session、离线恢复与 owner-safe 数据删除。
- [P1-06 事实驱动的首次学习旅程设计](p1-06-fact-driven-first-use-journey.md)：presentation-only preference、owner-fact readiness、首次 activity completion 与恢复/路由边界。

这些设计分别通过 ADR-0001/0002、ADR-0009 与 ADR-0106 转换为实现合同。实现时仍以 [`../specs/README.md`](../specs/README.md) 为直接权威来源。

[`research/`](research/README.md) 保存设计证据、历史诊断和研究推导。Research 不是第三份 Canonical Design，也不能覆盖 Spec。
