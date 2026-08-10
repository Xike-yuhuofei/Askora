# EXEC-059 — UI Design System & Component Foundation

> Status: **FROZEN / BLOCKED_BY_DEPENDENCY_GATE**  
> Priority: P1 UI Engineering  
> Governing: `PRODUCT-POSITIONING`, ADR-0014, `UI-IES-*`, `UI-VIS-*`, `UI-COMP-*`, `UI-QUAL-*`  
> Depends on: **UI-03 / EXEC-046 DONE**

## Objective

把已经冻结的 Askora Visual System 与 Component State Contracts 落地为一个最小、统一、可测试的前端样式与交互基础，消除页面级重复定义的基础视觉规则和核心状态漂移。

本 EXEC **不是**重做页面 UI，也不是建立独立 Design System 产品/包。优先沿用当前 React + CSS 架构，在现有 `global.css` / shared components 上收敛；只有存在真实复用与行为收益时才新增基础组件。

## Dependencies

执行前必须满足：

- `EXEC-043 → 044 → 045 → 046` 已完成验收并归档；
- UI-03 Release Evidence 已形成；
- `docs/specs/ui/component-state-contracts.md` 为 FROZEN；
- 当前 frontend tests/build baseline 已记录；
- 无 active EXEC 同时修改本 EXEC 的目标 frontend style/component files。

否则返回 `BLOCKED_BY_DEPENDENCY`。

## Required Product Positioning

必须读取 `docs/product/PRODUCT-POSITIONING.md` 并确认：

- v1 是 single-user Local Web Application；
- UI foundation 不引入远程运行依赖、云主题服务、analytics 或 design-system SaaS；
- 不通过视觉组件创建新的 Product Domain、owner state 或学习语义；
- Learning Evidence / mastery / recommendation truth 继续来自 canonical owner，不由组件推断。

## Required Specs

- `AGENTS.md`
- `docs/product/PRODUCT-POSITIONING.md`
- `docs/adr/ADR-0014-user-job-driven-interaction-architecture.md`
- `docs/specs/ui/interactive-element-system.md`
- `docs/specs/ui/information-architecture.md`
- `docs/specs/ui/screen-contracts.md`
- `docs/specs/ui/visual-system.md`
- `docs/specs/ui/component-state-contracts.md`
- `docs/specs/ui/quality-and-migration.md`
- UI-03 Release Evidence

## Current Reality

当前 `apps/frontend/src/styles/global.css` 已存在一部分有效基础：

- Apple/system font stack；
- Light-theme color variables；
- shared button intents；
- focus-visible ring；
- status pill；
- loading/error/empty helpers；
- `prefers-reduced-motion`。

但它仍是部分实现，不能等同于 FROZEN Design System。已知需要核对的 Gap 至少包括：

- `UI-VIS-021` dark-theme token/application 是否缺失；
- spacing/radius/elevation/typography 是否仍大量以 page-local literal 重复；
- `UI-COMP-*` 的 PRESSED / SELECTED / LOADING / DISABLED precedence 是否一致；
- Navigation/Selection persistent state 是否有 semantic attribute + stable visual treatment；
- loading single-flight、focus return、error/empty semantics 是否由真实组件/页面行为落实；
- hard-coded semantic colors 是否在页面 CSS 中产生漂移；
- shared style primitive 与真正需要复用的 React behavior 是否有重复实现。

开始实现前必须先形成实际 inventory；不得把上述“已知检查项”当成未经验证的代码事实。

## Implementation Strategy

遵循奥卡姆剃刀：

```text
已有 global/shared CSS 可收敛
→ 优先扩展现有基础
→ 只有跨 3+ 使用点且包含真实行为/语义时才抽 React primitive
→ 不建立独立 package / Storybook / token compiler
```

主题策略优先使用本地、零服务依赖的 CSS custom properties；若当前产品没有显式主题设置，dark theme SHOULD 先遵循系统 preference，不为本 EXEC新增设置业务。

## Allowed Files

```text
apps/frontend/src/styles/**
apps/frontend/src/components/ui/**                 # new only when reuse/behavior threshold is met
apps/frontend/src/components/**/*.css              # only design-token/state normalization
apps/frontend/src/pages/**/*.css                   # only replace duplicated base visual literals with frozen tokens
apps/frontend/src/test/**DesignSystem**
apps/frontend/src/test/**ComponentState**
apps/frontend/src/test/**accessibility**
apps/frontend/src/test/**navigation**
docs/exec-plans/active/EXEC-059-ui-design-system-component-foundation.md
docs/exec-plans/completed/EXEC-059-ui-design-system-component-foundation.md
docs/exec-plans/README.md
docs/exec-plans/completed/README.md
```

如必须修改 JSX 来接入一个新 shared primitive，只允许修改使用该 primitive 的直接调用点；不得借此改变页面信息架构、业务 action 或 data query。

## Forbidden Changes

- Product Positioning / IA / Screen Contract 改动；
- backend/domain/API/schema；
- 新建独立 design-system npm package；
- 引入 Storybook、CSS-in-JS framework、Tailwind 或大型 UI framework，仅为完成本 EXEC；
- 将所有现有 HTML element 强制包装成 React primitive；
- 为“统一”而创建第二套 Button/Card/Status abstraction；
- 页面重排、Today/Library/Settings hierarchy 重设计；
- 用颜色单独表达 error/selected/disabled；
- 隐藏 focus outline；
- hover-only action；
- 通过 frontend 计算 mastery/progress/recommendation truth；
- 为 dark mode 新建账号/云同步/远程 preference。

## Implementation Tasks

1. 记录 base commit、git status、frontend tests/build baseline。
2. Inventory 当前 CSS variables、shared classes、重复 base literals、core interactive state implementation；输出 Gap matrix，对应 `UI-VIS-*` / `UI-COMP-*`。
3. 保留并扩展单一 semantic token source：颜色、typography、spacing、radius、elevation、focus/motion；避免同语义多命名。
4. 补齐 light/dark semantic tokens 与系统主题映射；对 code/formula/citation/status/focus/disabled 做必要验证。
5. 统一 Button/Action 的 DEFAULT/HOVER/FOCUS/PRESSED/DISABLED/LOADING visual contract；loading 必须 single-flight 语义可验证。
6. 统一 Navigation/Selection 的 SELECTED 与 FOCUS 共存规则，使用 `aria-current` / `aria-selected` / checked 等匹配语义。
7. 统一 Row/List、Status、Empty/Loading/Error 的基础表现；不得把所有 domain object 变成 Card。
8. 将页面 CSS 中明显重复的基础颜色、spacing、radius、focus/state literal 替换为 frozen semantic token；页面特有布局允许保留 local CSS。
9. 仅在真实复用且含行为语义时新增 minimal React primitives；每个新增 primitive 必须说明至少 3 个使用点或不可由 CSS/原生元素安全表达的行为理由。
10. 增补 automated tests：keyboard/pointer activation 等价、selected+focus、disabled no-command、loading single-flight、accessible role/name/state、non-hover-only contextual action。
11. 验证 360/768/1024/1440、200% zoom、light/dark、reduced-motion；不要求像素级 snapshot。
12. 运行 Required Tests；全部 AC PASS 后归档 EXEC-059 并独立 commit。

## Acceptance Criteria

- `EXEC059-AC-001`：`UI-VIS-*` 与 `UI-COMP-*` 有明确 implementation mapping，无未解释的高优先级 Gap；
- `EXEC059-AC-002`：semantic token source 唯一，页面不重复定义基础品牌/状态/focus tokens；
- `EXEC059-AC-003`：light/dark theme 的关键 surface/text/border/action/status/focus 均可用且满足适用对比度要求；
- `EXEC059-AC-004`：Button/Navigation/Selection/Input/Interactive Row 的适用状态满足 DEFAULT/HOVER/FOCUS/PRESSED/SELECTED/DISABLED/LOADING 合同；
- `EXEC059-AC-005`：LOADING/EMPTY/ERROR/PARTIAL/STALE 不冒充 READY，也不使用 fake canonical data；
- `EXEC059-AC-006`：pointer 与 keyboard 对同一 Action 产生相同 intent，contextual action 不依赖 hover-only；
- `EXEC059-AC-007`：focus indicator、focus return、reduced motion、200% zoom、360px minimum path 不回归；
- `EXEC059-AC-008`：没有新增无收益的 UI framework/package/Storybook/token compiler；
- `EXEC059-AC-009`：页面 IA、owner truth、backend/public schema 均无语义变化；
- `EXEC059-AC-010`：核心 state/component behavior 有自动化测试。

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
- light/dark screenshots or equivalent local verification evidence；
- 360/768/1024/1440 + 200% zoom evidence；
- keyboard-only primary interaction evidence；
- 新增 primitive 的复用理由（如有）。

## Completion Report Format

报告：

1. base/final commit；
2. Gap matrix before/after；
3. 修改文件；
4. token mapping；
5. component state mapping；
6. 新增 shared primitive 及理由；
7. responsive/theme/keyboard/accessibility evidence；
8. tests/build/audit/docs/diff 结果；
9. Acceptance Criteria matrix；
10. remaining SPEC GAP / deferred visual polish。
