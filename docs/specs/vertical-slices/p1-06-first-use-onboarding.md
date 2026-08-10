# P1-06 — Fact-driven First-use Onboarding Vertical Slice

> 状态：FROZEN / v2 Local Web Alignment  
> 日期：2026-08-10  
> Governing：`PRODUCT-POSITIONING`、ADR-0015、ADR-0106、`LID-*`、`ONBOARD-*`、`MODEL-CONFIG-*`  
> Supersedes：2026-08-09 v1 macOS App / login / Electron acceptance wording  
> Decision authority：existing frozen higher-level product/identity decisions

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

路径可 dismiss/reopen/restart，步骤完全由 owner facts 派生，错误使用 P1-07 恢复动作。

本 slice 不再包含 registration、login、relogin、AuthSession、Electron 或 packaged macOS App 产品语义；这些旧语义已被 Product Positioning + ADR-0015 / `LID-*` supersede。

## 2. Scope

### Included

- presentation-only onboarding preference；
- LocalOwner-scoped journey query、single next action、strict API/error schema；
- SYS06 first accepted-transcript activity completion projection；
- `/welcome`、default-entry/deep-link rules、Settings reopen；
- SYS08 canonical **public non-sensitive model configuration summary** 集成；
- P1-03 data-control route/capability、P1-07 recovery action 集成；
- 真实 Library / Goal / Book Learning / Activity / Today 主链；
- refresh、Local Server/App restart、accessibility、首次用户验收；
- release report 与当前 product-gap / evidence 状态对齐。

### Excluded

- register/login/logout/password/recovery-kit/session/device/account deletion；
- Electron/safeStorage/packaged macOS mechanics 作为 v1 runtime prerequisite；
- 多资料 Goal/完整 Goal 编辑与 replan；
- 新 planner/mastery/review/policy 逻辑；
- 样例资料；
- learning efficacy claim。

## 3. Execution and Dependency State

历史执行：

```text
EXEC-1061 → EXEC-1062
```

两份 EXEC 与对应 Release Evidence 保留为生成时的历史证据快照；它们不能覆盖之后冻结的 Local Web / no-auth 产品定位。

当前 Local Web closure 仍依赖：

```text
MODEL-CONFIG Local Web capability
→ canonical revisioned SYS08 profile
→ explicit fixed-probe verification
→ activation / runtime_revision / restart-safe recovery
→ public non-sensitive summary
→ onboarding MODEL owner-query integration
```

在上述能力缺失时，production onboarding MUST fail/degrade safely：

- journey 对该 dependency 报告 `PARTIAL` / stable unavailable reason；
- MUST NOT 从 API key 是否存在、provider private collection、environment variable、模型回复或 health boolean 推断 `ACTIVE` / `verified_at`；
- MUST NOT 强制默认入口进入一个无法完成的 `/welcome` journey；
- Settings MAY 显示当前运行状态，但不能把非 canonical runtime observation 提升为模型配置完成事实。

## 4. Acceptance Criteria

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

## 5. Dependency Gate

- Product Positioning：Local Web / single-user / no-login / loopback / BYOK truth 已冻结；
- ADR-0015 / `LID-*`：LocalOwner bootstrap 与 no-auth business dependency 已冻结；
- UI/Activity baseline：exact activity 可 start/resume/complete；
- SYS08 `MODEL-CONFIG-*`：App 内模型配置、真实 probe verification、activation、restart recovery 与 public summary 必须形成可集成的当前证据；
- P1-03：current data-control capability/route 可用且不暴露内部绝对路径；
- P1-07：稳定 RecoveryAction 对本路径错误有真实 owner action。

若 SYS08 model configuration dependency 尚未满足，P1-06 current product closure MUST 保持 reopened/partial，不得引用历史 EXEC-1062 release snapshot 宣称当前 Local Web 完整 DONE。

## 6. Completion Rule

Mock、只读页面、frontend wizard、API-key presence、`bool(api_key)`、只看到模型回复、无真实 dependency action、无 restart/deep-link/首次用户证据均不能关闭当前 P1-06。

完成声明必须固定 candidate SHA，并分别报告：

- Engineering Evidence；
- Security / Privacy Evidence；
- Product / Usability Evidence；
- Learning Evidence。

Engineering PASS 不自动提升 Product 或 Learning Evidence；除非存在满足学习实验合同的真实证据，Learning Evidence 保持 `LEARNING_EVIDENCE_INSUFFICIENT`。
