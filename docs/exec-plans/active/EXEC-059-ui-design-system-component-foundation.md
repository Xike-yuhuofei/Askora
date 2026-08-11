# EXEC-059 — UI Design System & Component Foundation

> Status: **FROZEN / BLOCKED_BY_DEPENDENCY_GATE**  
> Priority: P1 UI Engineering  
> Product Traceability: `PD-NFR-005` + applicable current UI capabilities  
> Governing: `docs/design/experience/INTERACTION-MODEL.md`, `docs/specs/ui/design-system.md`, `docs/specs/ui/quality-and-regression.md`, `docs/specs/ui/screen-and-navigation-contracts.md`, ADR-0014/0018  
> Depends on: **EXEC-046 DONE**

## Objective

把 current Askora Design System Contract 落地为最小、统一、可测试的前端样式与 reusable component foundation，消除页面级重复基础视觉规则与核心状态漂移。

本 EXEC：

- 不重做页面 IA / UX；
- 不建立独立 Design System 产品或 npm package；
- 优先沿用当前 React + CSS 架构；
- 只有存在明确复用/行为收益时才新增 shared component；
- 不要求实现 Product Definition 未承诺的主题或新 UI capability。

## Dependency Gate

执行前必须满足：

- `EXEC-046 DONE`；
- UI-04 current Workspace/Learning/Library surfaces 已完成对应 release acceptance，避免在结构仍变动时先做大范围 token/component normalization；
- current `docs/specs/ui/design-system.md` 与 `quality-and-regression.md` 为实现合同；
- frontend tests/build baseline 已记录；
- 无 active EXEC 同时修改目标 style/component files。

否则返回 `BLOCKED_BY_DEPENDENCY`。

## Required Sources

- `AGENTS.md`
- `docs/product/PRODUCT-DEFINITION.md`
- `docs/design/experience/INTERACTION-MODEL.md`
- `docs/design/experience/EXPERIENCE-ARCHITECTURE.md`
- `docs/specs/ui/design-system.md`
- `docs/specs/ui/quality-and-regression.md`
- `docs/specs/ui/screen-and-navigation-contracts.md`
- `docs/specs/ui/learning-interaction-contracts.md`（仅需理解 learning-specific component semantics）
- ADR-0014 / ADR-0018

历史 `visual-system.md` / `component-state-contracts.md` / `interactive-element-system.md` 只用于 clause trace，不是 current implementation Authority。

## Current Reality

开始前必须 inventory current `apps/frontend/src/styles/**` 与 shared components，不能把历史 Gap 列表当作 current code fact。

重点核对：

- semantic token 是否集中；
- page-local hard-coded semantic colors/spacing/radius/focus 是否漂移；
- Button/Nav/Selection/Input/Row/Disclosure/Tab/Status 状态是否一致；
- loading single-flight、focus、disabled、error/empty/partial/stale semantics；
- contextual action 是否 keyboard/touch 可发现；
- 360/200% zoom / reduced motion；
- `.design_library` 与 runtime code 是否形成第二套事实源。

### Theme rule

`design-system.md` 中的 dark tokens 是**条件性规范**：

- 如果 current Product/UI 已正式提供 dark theme，则实现必须完整满足；
- 如果 current Product 未提供 dark theme，不得仅为完成本 EXEC 新增主题设置、系统 preference behavior 或产品 capability。

## Implementation Strategy

遵循：

```text
已有 global/shared CSS 可收敛
→ 优先扩展现有基础
→ repeated semantic rules 使用统一 token
→ 只有存在真实复用/行为收益才抽 React primitive
→ 不建立 package / Storybook / token compiler
```

原则上不要以固定“跨 3 个使用点”作为抽象硬门槛；是否抽象由重复成本、语义一致性、测试收益和维护性共同决定。

## Allowed Files

```text
apps/frontend/src/styles/**
apps/frontend/src/components/ui/**                 # new only when justified
apps/frontend/src/components/**/*.css              # design-token/state normalization only
apps/frontend/src/pages/**/*.css                   # replace duplicated base visual literals only
apps/frontend/src/test/**DesignSystem**
apps/frontend/src/test/**ComponentState**
apps/frontend/src/test/**accessibility**
apps/frontend/src/test/**navigation**
docs/exec-plans/active/EXEC-059-ui-design-system-component-foundation.md
docs/exec-plans/completed/EXEC-059-ui-design-system-component-foundation.md
docs/exec-plans/README.md
docs/exec-plans/completed/README.md
```

如必须修改 JSX 以接入 shared primitive，只允许直接调用点；不得借此改变页面 IA、business action 或 data query。

## Forbidden Changes

- Product Definition / Experience / Screen Contract 改动；
- backend/domain/API/schema；
- 新建独立 design-system npm package；
- 引入 Storybook、CSS-in-JS framework、Tailwind 或大型 UI framework，仅为完成本 EXEC；
- 将所有原生 HTML 强制包装为 React primitive；
- 为“统一”创建第二套 Button/Card/Status abstraction；
- 页面重排 / navigation redesign；
- 用 color-only 表达状态；
- 隐藏 focus outline；
- hover-only core action；
- frontend 计算 mastery/progress/recommendation truth；
- 为主题新增 Account/cloud/remote preference；
- Product 未承诺 dark theme 时顺带新增 dark mode capability。

## Implementation Tasks

1. 记录 base commit、git status、frontend tests/build baseline。
2. Inventory current CSS variables、shared classes、base literals、core states；输出 Gap matrix，对应 `UI-DS-*` / `UI-QR-*`。
3. 收敛单一 semantic token source：color、typography、spacing、radius、elevation、focus、motion。
4. 仅在 current product 已存在主题 capability 时补齐相应 theme mapping；否则不新增主题能力。
5. 统一 Button/Action 的 DEFAULT/HOVER/FOCUS/PRESSED/DISABLED/LOADING；loading single-flight 可验证。
6. 统一 Navigation/Selection 的 SELECTED + FOCUS 规则，使用匹配 semantic attributes。
7. 统一 Row/List、Input、Disclosure/Sheet、Tab、Status、Empty/Loading/Error 的 reusable baseline。
8. 将页面 CSS 中重复的基础 semantic literals 替换为 tokens；页面特有布局可保留 local CSS。
9. 新增 shared primitive 必须写明：复用点、语义一致性收益、为何原生元素 + CSS 不足（适用时）。
10. 增补 tests：keyboard/pointer activation、selected+focus、disabled no-command、loading single-flight、accessible role/name/state、non-hover-only contextual action。
11. 验证 360/768/1024/1440、200% zoom、reduced-motion；主题验证只覆盖 current 正式主题。
12. 运行 Required Tests；AC PASS 后归档。

## Acceptance Criteria

- `EXEC059-AC-001`：`UI-DS-*` 有明确 implementation mapping，无未解释高优先级 Gap；
- `EXEC059-AC-002`：semantic token source 唯一，页面不重复定义基础品牌/状态/focus tokens；
- `EXEC059-AC-003`：current 正式主题的 surface/text/border/action/status/focus 满足合同；未承诺主题不被新增；
- `EXEC059-AC-004`：Button/Navigation/Selection/Input/Row/Disclosure/Tab 的适用状态满足 current Design System；
- `EXEC059-AC-005`：LOADING/EMPTY/ERROR/PARTIAL/STALE 不冒充 READY，不使用 fake canonical data；
- `EXEC059-AC-006`：pointer/keyboard 对同一 intent 等价，contextual action 不 hover-only；
- `EXEC059-AC-007`：focus、reduced motion、200% zoom、360px primary path 不回归；
- `EXEC059-AC-008`：无无收益 UI framework/package/Storybook/token compiler；
- `EXEC059-AC-009`：页面 IA、Product capability、owner truth、public schema 无语义变化；
- `EXEC059-AC-010`：核心 reusable state/component behavior 有自动化测试；
- `EXEC059-AC-011`：`.design_library` / screenshots / page-local CSS 不形成第二 Design System Authority。

## Required Tests

```bash
cd apps/frontend
npm test -- --run
npm run build
npm audit --audit-level=high

cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

另外提供：

- token/state Gap matrix；
- current theme verification evidence；
- 360/768/1024/1440 + 200% zoom evidence；
- keyboard-only primary interaction evidence；
- 新增 primitive 的抽象理由（如有）。

## Completion Report Format

报告：base/final commit、Gap before/after、修改文件、token mapping、component state mapping、新增 shared primitive 及理由、responsive/theme/keyboard/a11y evidence、gates、AC matrix、remaining gap。