# Askora Architecture Decision Records

> 状态：决策流程入口（不再是 ADR 索引）
> 当前有效决策的唯一视图：[`../decisions/DECISIONS.md`](../decisions/DECISIONS.md)
> 历史 ADR 原文：`../archive/adr/`（26 份，immutable）

## 0. 入口导航

| 我想知道…… | 去哪里 |
|---|---|
| 当前有效决策（某个系统现在为什么这样设计） | [`../decisions/DECISIONS.md`](../decisions/DECISIONS.md) |
| 决策原文、备选方案、决策时的后果 | [`../archive/adr/`](../archive/adr/)（按 `ADR-XXXX` 查找） |
| 某个旧决策是否还有效、被什么替代 | DECISIONS.md Part B 历史废止索引 |
| 如何提交一个新架构决策 | 按下方 §1/§3 流程 |

## 1. 何时必须建立 ADR

以下变化通常必须先有 ADR，再改 Spec 和代码，且不得突破已冻结 Product Positioning / Product Definition：

- 八类技术系统职责/所有权变化；
- 公共技术领域对象语义变化；
- 新的核心状态事实源；
- 模块化单体 → 微服务等部署架构变化；
- 数据库/事件基础设施重大替换；
- baseline 算法被新的生产主算法替换；
- 新增高权限 Agent/tool 执行模型；
- 破坏性公共 Schema/API 演进策略；
- 对安全、隐私、重放或审计不变量的改变；
- Local Web / Workspace / LocalOwner / local-first runtime 等已定义产品边界的重大实现方式变化；
- 多个 Design / Spec 方案都会满足同一个 Product Requirement，但会形成不同长期 architecture ownership / migration / security consequences。

局部实现细节、私有重构、等价性能优化通常不需要 ADR。

若拟议变化会：

- 突破 `PRODUCT-POSITIONING.md` 的 Category / Product Shape / Hard Constraints / Non-goals → 先处理 `POSITIONING GAP`；
- 新增/删除 Product Capability、改变 v1 Feature inclusion、Product Rule、Product Requirement 或 Product Acceptance → 先处理 `PRODUCT DEFINITION GAP`；
- 只是在已定义 Product WHAT 下选择新的 architecture / ownership / migration 方案 → 才由 ADR 拥有该决策。

不得创建下位 ADR 绕过 Product Positioning / Product Definition。

## 2. ADR 生命周期

```text
proposed → accepted → superseded
```

- ADR 正文 immutable；只有 `Status` 可变；
- 被 supersede 后，ADR 原文保留在 `../archive/adr/`，状态与替代链记录在 `DECISIONS.md` Part B；
- 禁止历史 ADR 反向覆盖当前上位产品定义；current truth 以 `DECISIONS.md` + current Spec 为准。

## 3. 文件模板

```markdown
# ADR-XXXX — Title

Status: proposed | accepted | partially superseded | superseded | rejected
Date: YYYY-MM-DD
Decision owners: ...
Upper authority:
  - docs/product/PRODUCT-POSITIONING.md
  - docs/product/PRODUCT-DEFINITION.md
Product trace: CAP-* / PD-REQ-* / PD-RULE-* | N/A — infrastructure-only
Current design input: ...
Affected specs: ...

## Current Supersession / Authority Interpretation (if any)
## Context
## Decision
## Alternatives Considered
## Consequences
## Migration / Rollback
## Validation
## Supersedes / Superseded By
```

`Product trace` 的目的只是说明 ADR 服务哪个已定义 Product Requirement；不得在 ADR 中自行创造新的 `CAP-* / PD-REQ-* / PD-AC-*`。

ADR 接受后：更新 `DECISIONS.md` 对应条目（Status / 结论 / 指向），并同步受影响 current Spec（适用时）。

## 4. Codex 权限

Codex 可以指出需要 ADR 的 `DESIGN GAP` / `SPEC GAP`。当用户已明确授权目标或明确委托架构自治时，Codex 可以为该目标创建并接受**下位架构 ADR**，并继续同步 Design/Spec、EXEC、代码和测试；不再要求另一次顶层人工批准。

由 Codex 接受的 ADR 必须记录：

- `Decision authority: user-delegated Codex`；
- 对应用户目标/任务范围；
- applicable Product trace；
- 至少一个真实备选方案与未采用原因；
- 状态所有权、重复 truth 风险、迁移/回滚或 forward-fix；
- 安全、隐私、replay、idempotency 与验证门禁；
- 对 Product / UX / Engineering / Policy / Learning Evidence 声明边界的影响。

Codex 的架构自治权限只作用于下位设计/架构，**不得自行突破 Frozen Product Positioning 或 Product Definition**。若发现目标本身需要改变 Product Scope，必须先报告正确的上游 GAP，而不是用 accepted ADR 制造既成事实。
