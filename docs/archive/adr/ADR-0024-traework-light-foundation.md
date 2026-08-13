# ADR-0024 — Adopt TraeWork Light as Askora Visual Foundation

Status: accepted
Date: 2026-08-13
Decision owners: user-authorized Askora design-system adoption
Upper authority:

- `docs/product/PRODUCT-STRATEGY.md`
- `docs/product/PRODUCT-POSITIONING.md`
- `docs/product/PRODUCT-DEFINITION.md`
- `docs/design/experience/EXPERIENCE-ARCHITECTURE.md`
- `docs/design/experience/INTERACTION-MODEL.md`
- `docs/design/experience/LEARNING-EXPERIENCE.md`

Product trace: `PD-NFR-005` and applicable visual/accessibility requirements
Direct contract: `docs/specs/ui.md` (`UI-DS-TOK-*`, `UI-DS-COMP-090`, `UI-DS-AC-001`)
Does not amend: Product Capability taxonomy, Course-centric IA, three-column responsibilities, Chat-is-not-L0

## Context

Askora 的现行 UI 合同原先使用独立 Light baseline（accent `#007AFF`）。仓库随后收入 TraeWork Light 设计库作为唯一可复用视觉源，并有一份 TraeWork 产品窗的 Dark 像素复刻（`ui/prototypes/shell-replica/`）。

上一轮目录治理只记录了 SPEC GAP：`docs/specs/ui.md` Light baseline ≠ TraeWork tokens。若不关闭该 GAP，前端无法声称采用了 TraeWork 设计系统，也容易把复刻页误当成生产源。

Experience Design 已经冻结 Askora 自己的 IA：课程 / 学习画布 / 笔记；Chat 不是 L0。视觉 foundation 的采用不得把 Trae 的 Code·Chat 模式或任务树写成 Askora 导航。

## Decision

### 1. TraeWork Light is the foundation source; Askora keeps semantic roles

Askora 采用 TraeWork Light 的 color / type / spacing / radius foundation 值。Askora 继续拥有 `color.canvas`、`color.accent` 等 semantic roles。业务代码使用 Askora roles，不把 TraeWork 内部名散落到页面。

accent 采用 `--bg-brand` `#4B3FE3`。继续保留 `#007AFF` 只是参考，不能关闭 SPEC GAP。

### 2. Light only

v1 不采用 Dark theme。官方库是 Light-only。`shell-replica` 的测量 Dark hex 不是合同，不得写入 `docs/specs/ui.md` 或 `apps/frontend`。

### 3. Replica is composition evidence, not a production source

两份复刻界面只证明密度与 Composer 解剖。不得把复刻 React、窗框、suggestion chips 或 Trae IA 拷进生产前端。

### 4. WCAG may tune hex, not roles

`success` / `warning` 的 TraeWork default 作 text-on-canvas 不满足 WCAG AA，因此微调；`error` 使用 `--status-error-active`。role 不变。状态仍必须有非颜色表达。

### 5. This decision does not implement components

本 ADR 只关闭 token SPEC GAP。Composer / Button / Icon 的实现对照见 `UI-DS-COMP-090`，留给后续任务。不引入 Inter / JetBrains Mono 远程字体。

## Alternatives considered

### A. Keep `#007AFF`; take only spacing / radius / type

Rejected。这是参考，不是采用。SPEC GAP 会继续存在，组件 preview 的 brand 也无法对齐。

### B. Treat `shell-replica` Dark as the adopted visual language

Rejected。复刻是 Trae 产品窗的 Dark 像素稿，不是官方设计库；也会与 Experience 的课程三栏和 Light 合同冲突。

### C. Copy TraeWork `ui_kits/` or replica shell into `apps/frontend`

Rejected。`library-consumption.json` 明确 `ui_kits/` 不可 copyable；Experience 禁止 Chat-as-L0 与任务树导航。

## Consequences

- `docs/specs/ui.md` `UI-DS-TOK-002` / `UI-DS-TOK-005` 成为现行 Light foundation。
- `apps/frontend` 的 CSS 变量必须跟随这些值；残留硬编码 hex 视为 implementation drift，不反向改 Spec。
- 视觉会从 iOS 蓝变为 Trae 紫。这是 foundation 采用的可见结果，不是 IA 变化。
- 本 ADR 不是现行合同；与 Spec 冲突时以 `docs/specs/ui.md` 为准。
