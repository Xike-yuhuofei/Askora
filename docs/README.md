# Askora 文档中心

> 状态：当前文档索引
> 当前基线：v0.3 Adaptive Teaching Loop
> 最近校准：2026-08-09

`docs/` 保存 Askora 的实现合同、架构决策、正式设计、研究证据、执行归档和发布证据。同一事实只能有一个权威来源；当前说明、冻结合同和历史记录不得混为一类。

## 1. 权威顺序

发生冲突时按以下顺序处理：

```text
docs/specs/
→ docs/adr/
→ docs/design/ 中的 Canonical Design
→ 当前代码、配置、迁移与可执行测试
→ Research / 历史说明
```

代码与 Spec 冲突时默认属于实现偏差，不得反向修改 Spec 迁就代码。Research 解释“为什么这样设计”，不能直接作为实现接口合同。

## 2. 目录与生命周期

| 路径 | 性质 | 当前状态 | 更新规则 |
|---|---|---|---|
| [`specs/`](specs/README.md) | Canonical Implementation Contract | v0.3 frozen | 语义变化必须遵循 Spec/ADR 流程 |
| [`adr/`](adr/README.md) | 已接受架构决策 | ADR-0001/0002 accepted | 作为决策历史保留，不改写当时理由 |
| [`design/`](design/README.md) | Canonical Design | v0.3 frozen | 保持与已接受 ADR/Spec 的关系说明准确 |
| [`design/research/`](design/research/README.md) | Evidence / Synthesis | historical and supporting | 保留独立证据价值，明确历史阶段 |
| [`exec-plans/`](exec-plans/README.md) | 实施任务合同 | EXEC-030 active；EXEC-1031～1034 completed | completed 文件保持历史原貌 |
| [`releases/`](releases/README.md) | 发布与验收证据 | 含 P1-03 当前收口证据与历史 snapshots | 不把历史测试结果宣称为当前重新验证 |
| [`document-inventory.md`](document-inventory.md) | 文档处置清单 | current | 每次文档治理后更新 |

## 3. 当前项目状态

截至 v0.3 release baseline：

```text
Engineering Gate: PASS
Policy Correctness Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

EXEC-001～013 已完成并归档；`docs/exec-plans/active/` 当前仅保留 EXEC-030。上述结果是发布时证据快照；对当前 checkout 作工程判断时仍需重新运行适用检查。

P1-03 Data Control and Recovery 已于 2026-08-09 通过 Engineering、Policy / Ownership / Security 与真实打包桌面恢复门禁；EXEC-1031～1034 已归档。Learning Evidence 仍为 `LEARNING_EVIDENCE_INSUFFICIENT`。当前仍有 EXEC-030 保留在 active，状态以 [Execution Plans](exec-plans/README.md) 为准。

## 4. 当前说明与历史说明

- 根 [`README.md`](../README.md) 和应用级 README 描述当前稳定代码基线；
- Specs、Canonical Design 和 Accepted ADR 定义系统应满足的语义；
- completed EXEC、Release Report、候选范围和研究议程记录历史形成过程；
- 标记为历史的材料即使包含“下一阶段”“当前缺口”等措辞，也不得被解释为当前项目状态；
- 没有独立证据、设计或审计价值的过时临时说明应删除，而不是长期保留多个“最新版”。

## 5. 文档质量门禁

```bash
python3 .github/workflows/check_docs.py
```

门禁检查受 Git 跟踪的 Markdown/RST 本地链接和已知过时状态措辞。文档中的运行、测试、构建命令还必须在相关变更中实际验证，链接通过不能代替命令验证。
