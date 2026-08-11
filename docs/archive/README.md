# Askora Archive

> 状态：Historical Evidence Index
> 权威性：Non-current；所有结论受 current Product / Design / ADR / Spec 与 current `main` 覆盖

`docs/archive/` 保存仍有审计、迁移、决策演进或交付证据价值，但不应继续占用 current 文档入口的材料。

| 目录 | 内容 | 使用边界 |
|---|---|---|
| [`audits/`](audits/) | Gap Analysis、conformance snapshot、历史测试分类 | 只对记录的 SHA / 时间有效 |
| [`design/`](design/) | 已被吸收或 supersede 的 Design / Design Delta | 用于解释演进，不直接指导新实现 |
| [`specs/`](specs/) | 已被 current contract 取代的 UI Spec / Vertical Slice | 仅供迁移与追溯 |
| [`exec-plans/`](exec-plans/) | DONE、canceled、superseded EXEC 与执行报告 | 不代表实时 backlog 或 current acceptance |
| [`releases/`](releases/README.md) | Release / completion evidence | 不代表 current checkout 已重新验证 |

Archive 文件原则上保持历史内容不改写；路径迁移导致的链接修复除外。任何历史结论要重新成为 current requirement，必须按当前 Product → Design → ADR → Spec 治理链重新接受，不能直接“移回去”。
