# ADR-0026 — Close Core Journey Goal and Unassigned-Material Gaps

Status: accepted
Date: 2026-08-13
Decision owners: user-authorized Askora product governance
Decision authority: 用户要求更新 Core Journey 并解决所有文档冲突；此前已冻结「目标由系统维护、上传不创建空间」
Upper authority:

- `docs/product/PRODUCT-STRATEGY.md`
- `docs/product/PRODUCT-POSITIONING.md`
- `docs/product/PRODUCT-DEFINITION.md`

Product trace: amends Positioning §10.3 / Strategic Constraint 11、`CAP-02`、`PD-RULE-004`、`PD-REQ-0101`、`PD-REQ-0201..0203`、CAP-02 Product Acceptance；does not add/remove a Capability
Affected specs: `docs/specs/domain.md` DOMAIN-010、`docs/specs/systems/06-learning-planner.md`、`docs/specs/platform.md` WSP-021、`docs/specs/interfaces/persistence-and-data-control.md`、`docs/specs/interfaces/content.md`、`docs/specs/interfaces/recovery-and-onboarding.md`、current Experience / UI
Closes: Experience `EXP-JOURNEY-GAP-001`、`EXP-JOURNEY-GAP-002`
Does not amend: Conversation ≠ Evidence、LLM 非 canonical owner、Workspace 是真实 scope

## Context

ADR-0025 把用户侧 Journey 写成：上传只创建资料；开始学习不经过确认目标。当时 Product Definition 仍要求用户确认/纠正高层目标，Platform `WSP-021` 仍要求新 Material 必须带 Workspace。Experience 只能标 GAP，合同互相打架。

用户要求关掉这些冲突，而不是继续并存两套 truth。

## Decision

### 1. Goals are system-maintained planning facts

`PD-RULE-004` 改为：系统根据材料与学习过程生成并维护 Goal；开始学习不以用户确认目标为前置；目标不是主路径管理对象。这就是 DOMAIN-010 的「显式产品规则」。

SYS06 从材料处理采纳的 Goal 可以直接 `active`。LLM 草稿仍不能成为 planning fact。

### 2. Material may be unassigned

`PD-REQ-0101` 与 `WSP-021` 允许 `workspace_id=null` 的 unassigned Material。归属某一 Workspace 之前，不得启动有依据的学习，也不得当作该空间的普通 retrieval 成员。

### 3. Core Journeys stay four

`001` 用资料开始、`002` 回来继续、`003` 在对话里学习、`004` 建立或扩充空间。不再保留「确认目标」步骤，也不再把「上传必须先有空间」写成现行合同。

## Alternatives Considered

### A. Keep Product / Platform unchanged and leave Experience GAPs

Rejected。用户要求解决文档冲突。

### B. Force user confirmation back onto Journey 001

Rejected。与已冻结用户故事相反。

### C. Invent a hidden default Workspace on every upload

Rejected。用户明确说上传不创建空间。

## Consequences

- Product / Experience / SYS06 / Platform 对「要不要确认目标、资料能不能先无空间」只有一套现行说法；
- 实现必须支持 unassigned Material 与归属 command；
- 旧「用户必须确认目标才能学」的测试与 onboarding 步骤必须改，不得再当 current AC。

## Validation

- Product Definition 不再要求开始学习前确认 Goal；
- Experience 不再存在 GAP-001 / GAP-002；
- WSP-021 允许 unassigned，并禁止未归属资料进入有依据学习；
- SYS06 / DOMAIN-010 / onboarding 与上述规则一致。
