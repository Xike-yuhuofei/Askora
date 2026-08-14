# ADR-0027 — Welcome Is the Home Destination, Not a First-use Wizard

Status: accepted
Date: 2026-08-13
Decision owners: user-authorized Askora experience alignment
Upper authority:

- `docs/product/PRODUCT-STRATEGY.md`
- `docs/product/PRODUCT-POSITIONING.md`
- `docs/product/PRODUCT-DEFINITION.md`
- `docs/design/experience/EXPERIENCE-ARCHITECTURE.md`
- ADR-0025 / ADR-0026

Product trace: `EXP-IA-001`、`EXP-JOURNEY-002`、`PD-RULE-004`
Direct contract: `docs/specs/ui.md`（`UI-ROUTE-001` / `UI-WELCOME-001`）、`docs/specs/interfaces/recovery-and-onboarding.md`（`ONBOARD-032` / `ONBOARD-034` / `ONBOARD-040`）
Does not amend: Product Capability taxonomy、Workspace identity、Chat-is-not-L0

## Context

ADR-0025 / ADR-0026 把打开 App 冻成每次先 Welcome，主路径不再确认目标。`docs/specs/ui.md` 已写成 `/` = Welcome。

Onboarding 合同仍把 `/welcome` 当受保护 first-use，完成下一步是 `OPEN_TODAY`，并向导里有用户可见 GOAL。前端 `/` 仍跳 `/today`。这是实现与现行 Experience 的冲突，不是产品未决。

## Decision

1. Welcome 是稳定 destination。`/` 与 `/welcome` 都是回家页；`/today` / `/learning` 只兼容解析到同一页。
2. first-use 只保留用户必须知道的薄提示（边界说明、模型未就绪、还没有资料）。不是「模型 → 资料 → 目标 → 第一节」向导。
3. `next_action` 完成或无唯一步骤时发 `OPEN_WELCOME`。新响应不再发 `OPEN_TODAY`，也不再发「确认目标」。
4. GOAL 投影可留在 API 里作内部 readiness，不得画成用户步骤。

## Alternatives Considered

### A. Keep onboarding wizard, only rename 课程 → 空间

Rejected。用户故事是每次先 Welcome，不是改名后的四步向导。

### B. Split `/` home and `/welcome` wizard

Rejected。`UI-ROUTE-001` 已规定两者都是 Welcome。

## Consequences

- 前端必须改默认路由、侧栏 IA 与 Welcome 表面。
- Onboarding 测试不得再要求 `/today` 或用户确认目标。
- 资料归属 / 「马上开始学习」仍是独立 SPEC，本 ADR 不假装已接通。
