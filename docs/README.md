# Askora 文档中心

> 状态：当前文档索引  
> 当前基线：v0.3 Adaptive Teaching Loop  
> 最近校准：2026-08-10

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
| [`adr/`](adr/README.md) | 已接受架构决策 | ADR-0001/0002/0003 accepted | 作为决策历史保留，不改写当时理由 |
| [`design/`](design/README.md) | Canonical Design / current conformance audit | v0.3 frozen + current snapshot | Design 保持与 ADR/Spec 一致；审计不能覆盖合同 |
| [`design/research/`](design/research/README.md) | Evidence / Synthesis | historical and supporting | 保留独立证据价值，明确历史阶段 |
| [`exec-plans/`](exec-plans/README.md) | 实施任务合同 | EXEC-042、EXEC-1062 active | completed 文件保持历史原貌；active 可来自独立任务域 |
| [`releases/`](releases/README.md) | 发布与验收证据 | 当前与历史 snapshots 并存 | 不把历史测试结果宣称为当前重新验证 |
| [`document-inventory.md`](document-inventory.md) | 文档处置清单 | current | 每次文档治理后更新 |

## 3. 当前项目状态

### 3.1 历史 v0.3 Release Snapshot

历史 v0.3 release baseline 曾记录：

```text
Engineering Gate: PASS
Policy Correctness Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

该结论只代表当时 release evidence，不等于当前 checkout 自动继续满足同一门禁。

### 3.2 Current Main Conformance

2026-08-10 的 [`v0.3 Current Main Conformance Gap Analysis`](design/v0.3-Current-Main-Conformance-Gap-Analysis.md) 对审计快照重新判定：

```text
Engineering Gate: ENGINEERING_GATE_FAILED
Policy Correctness Gate: POLICY_CORRECTNESS_GATE_FAILED
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

主要原因：

- production adaptive path 在 second+ decision 上仍直接调用 single-decision `TeachingPolicyKernel`，没有接入已经实现的 `SequentialTeachingPolicy` / Anti-Oscillation Gate；
- Book production `TeachingContext` 对 previous action、recent assessment、actual assistance 与 material evidence 的 hydration 不完整；
- 审计快照 CI 为 red。新增 Canonical Design Delta 的 document-inventory 遗漏已在后续治理提交修复，但 scope 外 Black baseline 仍需单独恢复并重新获得 current CI evidence。

对应实现闭包已经冻结为：

- [`EXEC-042 — v0.3 Production Sequential Teaching Policy Closure`](exec-plans/active/EXEC-042-v0.3-production-sequential-teaching-policy-closure.md)：P0 Policy Correctness closure；
- [`EXEC-1062 — P1-06B Onboarding Product Closure`](exec-plans/active/EXEC-1062-p1-06b-onboarding-product-closure.md)：独立 P1-06 产品任务域。

二者互不构成依赖，不得混合实施。

### 3.3 其他已完成基线

EXEC-001～041、EXEC-1031～1034、EXEC-1061 已按各自历史合同归档。P1-03 Data Control and Recovery 等后续产品任务的历史 release evidence 继续保留其当时结论，但不能覆盖当前 v0.3 policy conformance audit。

Learning Evidence 继续保持 `LEARNING_EVIDENCE_INSUFFICIENT`；Engineering 或 Policy Correctness 的修复不得被描述为已经证明真人 retention / transfer / unit-time capability gain 改善。

## 4. 当前说明与历史说明

- 根 [`README.md`](../README.md) 和应用级 README 描述当前稳定代码基线；
- Specs、Canonical Design 和 Accepted ADR 定义系统应满足的语义；
- current conformance audit 负责指出当前代码相对冻结合同的偏差；
- completed EXEC、Release Report、候选范围和研究议程记录历史形成过程；
- 标记为历史的材料即使包含“下一阶段”“当前缺口”等措辞，也不得被解释为当前项目状态；
- 没有独立证据、设计或审计价值的过时临时说明应删除，而不是长期保留多个“最新版”。

## 5. 文档质量门禁

```bash
python3 .github/workflows/check_docs.py
```

门禁检查受 Git 跟踪的 Markdown/RST 本地链接和已知过时状态措辞。文档中的运行、测试、构建命令还必须在相关变更中实际验证，链接通过不能代替命令验证。
