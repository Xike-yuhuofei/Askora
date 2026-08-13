# P1-06 — Fact-driven First-use Onboarding Vertical Slice

> 状态：FROZEN / v2 Local Web Alignment  
> 日期：2026-08-10  
> Product Traceability：`CAP-01`、`CAP-02`、`CAP-03`、`CAP-07`、`CAP-08`；`PD-REQ-0101`、`PD-REQ-0201..0203`、`PD-REQ-0301..0303`、`PD-REQ-0701`、`PD-REQ-0801..0803`；`PD-RULE-004/008/010/011`  
> Governing：`PRODUCT-DEFINITION.md`、`PRODUCT-POSITIONING`、ADR-0015、ADR-0106、`LID-*`、`ONBOARD-*`、`MODEL-CONFIG-*`  
> Supersedes：2026-08-09 v1 macOS App / login / Electron acceptance wording

## 0. Acceptance Ownership

本 Slice 冻结 first-use journey 的跨能力编排与 UX / technical acceptance，但不创建新的 Product Capability。

- `Included / Excluded` 只表示 onboarding implementation-slice scope，不等同 v1 总体 Feature Scope；
- `P106-AC-*` 包含 technical / UX / usability acceptance，不自动成为 `PD-AC-*`；
- model → material → goal → activity → Today 的产品意义来自适用 `CAP-* / PD-REQ-*`；
- 若 onboarding 需要改变 Product Scope、Goal 用户控制权、LocalOwner/no-login 产品规则或 Product Acceptance，必须先报告 `PRODUCT DEFINITION GAP` / `POSITIONING GAP`；
- Engineering / Product Usability / Learning Evidence 必须继续分层。

## 1. Objective

在 Askora v1 Local Web Application 内闭合：

```text
LocalOwner bootstrap
→ 数据与外部模型边界说明
→ SYS08 模型配置真实验证 / activation
→ 私人资料
→ confirmed Goal / diagnostic / plan
→ canonical activity start / resume / complete
→ Today next action
```

路径可 dismiss/reopen/restart，步骤完全由 owner facts 派生，错误使用 current RecoveryAction。

本 slice 不再包含 registration、login、relogin、AuthSession、Electron 或 packaged macOS App 产品语义；这些旧语义已被 Product Positioning + Product Definition + ADR-0015 / `LID-*` supersede。

## 2. Scope

本节只定义 P1-06 onboarding slice scope。

### Included

- presentation-only onboarding preference；
- LocalOwner-scoped journey query、single next action、strict API/error schema；
- SYS06 first accepted-transcript activity completion projection；
- `/welcome`、default-entry/deep-link rules、Settings reopen；
- SYS08 canonical **public non-sensitive model configuration summary** 集成；
- data-control route/capability、recovery action 集成；
- 真实 Library / Goal / Book Learning / Activity / Today 主链；
- refresh、Local Server/App restart、accessibility、首次用户验收；
- release report 与 current product / evidence 状态对齐。

### Excluded

- register/login/logout/password/recovery-kit/session/device/account deletion；
- Electron/safeStorage/packaged macOS mechanics 作为 v1 runtime prerequisite；
- 多资料 Goal/完整 Goal 编辑与 replan；
- 新 planner/mastery/review/policy 逻辑；
- 样例资料；
- learning efficacy claim。

Excluded 仅说明本 Slice 不实现；其中 Account/Desktop 等总体边界仍由 Product Positioning / Product Definition 拥有。

## 3. Historical Execution and Current Dependency Semantics

历史执行：

```text
EXEC-1061 → EXEC-1062
```

两份 EXEC 与对应 Release Evidence 保留为生成时的历史证据快照；它们不能覆盖之后冻结的 Local Web / no-auth 产品定位，也不承担当前任务状态。

任何 current onboarding implementation / conformance 判断都必须重新读取：

```text
PRODUCT-DEFINITION
→ current MODEL-CONFIG / owner contracts
→ current main code + tests
→ Linear dependency/status
```

对模型配置依赖，production onboarding MUST fail/degrade safely：

- journey 对缺失 dependency 报告 `PARTIAL` / stable unavailable reason；
- MUST NOT 从 API key 是否存在、provider private collection、environment variable、模型回复或 health boolean 推断 `ACTIVE` / `verified_at`；
- MUST NOT 强制默认入口进入一个无法完成的 `/welcome` journey；
- Settings MAY 显示当前运行状态，但不能把非 canonical runtime observation 提升为模型配置完成事实。

## 4. UX / Technical Acceptance Criteria

以下 AC 不创建新的 Product Acceptance：

- `P106-AC-001`：`ONBOARD-AC-001..009` 中仍适用于 Local Web 的合同均有当前候选 SHA 证据；任何旧 auth/Desktop 条款按本 v2 supersession 解释。
- `P106-AC-002`：fresh LocalOwner 完成真实 model→material→goal→activity→Today，refresh/restart 后续接且不重复副作用。
- `P106-AC-003`：MODEL complete 只能来自 SYS08 public summary 的 exact verified `ACTIVE` revision，且 `runtime_revision == revision`；撤销/禁用/验证过期后必须回退。
- `P106-AC-004`：删除资料、归档 Goal、supersede activity 后步骤按 current facts 回退。
- `P106-AC-005`：dismiss/reopen、existing-store migration、并发和 deep link 不失真或泄漏；explicit deep link 不被 onboarding 抢占。
- `P106-AC-006`：dependency unavailable 时 journey 可安全 `PARTIAL`，不得形成 mandatory broken welcome loop。
- `P106-AC-007`：所有错误显示 what/safety/action，且只执行 server-allowed recovery。
- `P106-AC-008`：360/768/1024/1440、200% zoom、keyboard/focus/live region 通过。
- `P106-AC-009`：无内部知识首次用户可说明数据位置、外部模型发送边界、稍后继续和 Today 下一步。
- `P106-AC-010`：Required backend/frontend/security/docs/migration gates PASS；真实 provider / browser evidence 在 frozen gate 要求时单独记录。
- `P106-AC-011`：Engineering、Security/Privacy、Product Usability 与 Learning Evidence 分开报告；Learning Evidence 默认仍为 `LEARNING_EVIDENCE_INSUFFICIENT`。

其中 `P106-AC-009` 可以作为相关 Product Acceptance 的 usability evidence，但不能自行定义 Product Requirement 或学习效果。

## 5. Dependency Gate

执行或重新验收本 Slice 时必须基于 current truth 检查：

- Product Positioning / Product Definition：Local Web / single-user / no-login / loopback / BYOK truth；
- ADR-0015 / `LID-*`：LocalOwner bootstrap 与 no-auth business dependency；
- UI/Activity baseline：exact activity 可 start/resume/complete；
- SYS08 `MODEL-CONFIG-*`：App 内模型配置、真实 probe verification、activation、restart recovery 与 public summary；
- current data-control capability/route；
- stable RecoveryAction 对本路径错误有真实 owner action；
- Linear 中对应 current dependency/status。

若关键 dependency 尚未满足，P1-06 current conformance MUST 保持 partial / blocked，不得引用历史 EXEC/release snapshot 宣称当前 Local Web 完整 DONE。

## 6. Completion Rule

Mock、只读页面、frontend wizard、API-key presence、`bool(api_key)`、只看到模型回复、无真实 dependency action、无 restart/deep-link/首次用户证据均不能关闭当前 P1-06 technical/UX contract。

完成声明必须固定 candidate SHA，并分别报告：

- Product Acceptance evidence（仅适用已定义 PD-REQ / PD-AC）；
- Engineering Evidence；
- Security / Privacy Evidence；
- UX / Product Usability Evidence；
- Learning Evidence。

Engineering PASS、Onboarding AC PASS 或 Product Usability PASS 不自动提升 Product Acceptance 或 Learning Evidence；除非存在满足学习实验合同的真实证据，Learning Evidence 保持 `LEARNING_EVIDENCE_INSUFFICIENT`。
