# Askora Design System

> 状态：**Canonical UI Design System Contract — Current Only**  
> 冻结日期：2026-08-11  
> 上游产品定义：`PD-NFR-005` 及适用 Product Requirements  
> Governing Experience：`docs/design/experience/EXPERIENCE-ARCHITECTURE.md`、`docs/design/experience/INTERACTION-MODEL.md`、`docs/design/experience/LEARNING-EXPERIENCE.md`  
> 下游：frontend component implementation / tests  
> Supporting assets：`.design_library/Askora/**`（reference only, not authority）

---

## 1. Purpose

本文件是 Askora reusable presentation foundation 的唯一长期 Design System Authority。

它管理：

```text
Semantic Tokens
Typography
Spacing
Radius / Elevation
Motion
Reusable UI Components / Patterns
Component States
Visual Accessibility
```

它明确**不管理**：

```text
Product Capability
Information Architecture
Navigation Decision
Learning / Task Flow
Screen Contract
Domain Object / State Ownership
API / Persistence
```

组件实现不得反向创造新的 Product Capability、页面职责或 interaction primitive。

---

## 2. Governing Principles

### UI-DS-001 — Calm, Precise, Focused

视觉目标是安静、精确、聚焦，优先支持阅读、推理、作答、反馈和来源核对。

默认避免大面积装饰、游戏化奖励、彩色学科卡片、重阴影、霓虹、无意义渐变或庆祝动画。

### UI-DS-002 — Semantic Before Component

正式推导顺序：

```text
Interaction Semantic
→ Hierarchy
→ Platform/Web Pattern
→ Component
→ Token / Visual Treatment
```

禁止：先决定 Card/Button/Badge，再寻找功能。

### UI-DS-003 — Data Honesty

视觉不得夸大确定性。Unknown、MISSING、PARTIAL、STALE、low confidence、assisted、answer exposed、error 必须有文本/结构语义，不能只靠颜色。

### UI-DS-004 — Local Web, Desktop-first

Askora v1 是 Local Web Application。组件应优先服务桌面浏览器信息密度与键盘操作，同时保持窄屏可用。

历史 native macOS/iOS 映射可以作为未来参考，但不属于 v1 Design System 必实现范围。

---

## 3. Semantic Token Model

Token 分三层：

```text
Foundation value
→ Semantic token
→ Component token / usage
```

业务代码 SHOULD 使用 semantic token，不应大范围硬编码具体 hex / spacing 值。

### UI-DS-TOK-001 — Color Roles

至少定义：

```text
color.canvas
color.surface
color.surface.subtle
color.surface.elevated
color.text.primary
color.text.secondary
color.text.muted
color.border
color.border.strong
color.accent
color.accent.subtle
color.success
color.warning
color.error
color.info
color.focus
```

`success / warning / error / info` 只表达对应语义，不用于装饰。

### UI-DS-TOK-002 — Current Light Baseline

当前推荐 baseline：

```text
accent              #007AFF
accent-subtle       #EAF3FF
canvas              #F2F2F7
surface             #FFFFFF
surface-subtle      #F7F7FA
surface-elevated    #FFFFFF
text-primary        #1C1C1E
text-secondary      #636366
text-muted          #8E8E93
border              #E5E5EA
success             #248A3D
warning             #C93400
error               #D70015
info                #007AFF
```

颜色 MAY 因 WCAG 对比度验证微调，但 semantic role 不得漂移。

### UI-DS-TOK-003 — Dark Theme

如果当前产品提供 dark theme，必须定义完整 semantic mapping；不得简单反转 light colors。

建议 baseline：

```text
canvas              #0B0B0D
surface             #1C1C1E
surface-subtle      #2C2C2E
surface-elevated    #2C2C2E
text-primary        #F5F5F7
text-secondary      #D1D1D6
text-muted          #98989D
border              #3A3A3C
accent              #0A84FF
```

若当前产品没有正式 dark theme capability，不得仅因 Design System 存在 token 而强制新增产品设置。

### UI-DS-TOK-004 — State Colors

任何 state color 都必须同时有非颜色表达：文本、icon、shape、border 或 accessible state。

---

## 4. Typography

### UI-DS-TYPE-001 — Font Stack

```css
-apple-system, BlinkMacSystemFont, "SF Pro Text", "PingFang SC",
"Microsoft YaHei", "Helvetica Neue", Arial, sans-serif
```

代码/标识：

```css
"SF Mono", Menlo, Monaco, Consolas, monospace
```

### UI-DS-TYPE-002 — Reading Range

主要工作界面正文以 12–16px 为常用范围；关键正文/状态/交互 label 不得为追求密度缩小至难以阅读。

正文 line-height SHOULD ≥ 1.5；长教学解释优先可读性而不是压缩高度。

### UI-DS-TYPE-003 — Semantic Headings

Heading 必须使用语义结构；页面/主要 surface 有清晰 h1/region heading。不得只用视觉尺寸模拟 heading hierarchy。

---

## 5. Spacing / Radius / Elevation

### UI-DS-SP-001

采用 4px 基础节奏，常用 spacing：

```text
4 / 8 / 12 / 16 / 24 / 32
```

优先用 spacing、section、surface 层次分组，不给每个 section 套 Card + border + shadow。

### UI-DS-SP-002

推荐 radius：

```text
8px   compact input/control
12px  bounded standard surface/card
16px  message/primary task container where needed
full  avatar / short status
```

radius 是 presentation token，不表达 semantic role。

### UI-DS-SP-003

Elevation 只用于真正浮动的 popover/modal/sheet/temporary surface。常规内容区默认不用重阴影。

---

## 6. Motion

### UI-DS-MOT-001

Motion 只服务状态连续性，例如：

- navigation/surface transition；
- Drawer / Right Rail 展开；
- list/context change；
- streaming/pending state。

常规 motion SHOULD 约 150–250ms，并遵守 `prefers-reduced-motion`。

禁止循环闪烁、庆祝动画或用 mastery/gamification 驱动高干扰 motion。

---

## 7. Component State Model

### UI-DS-STATE-001 — Interaction States

核心 reusable interactive component 至少按适用语义支持：

```text
DEFAULT
HOVER
FOCUS
PRESSED
SELECTED
DISABLED
LOADING
```

输入/数据型 component 还可有：

```text
ERROR
READ_ONLY
```

### UI-DS-STATE-002 — Data Region States

数据区域状态独立于 component interaction state：

```text
LOADING
EMPTY
READY
PARTIAL
STALE
ERROR
UNAUTHORIZED
```

特定 projection MAY 增加 `MISSING` / `LOW_CONFIDENCE`。

### UI-DS-STATE-003 — State Precedence

交互可用性冲突优先级：

```text
DISABLED
→ LOADING
→ PRESSED
→ SELECTED
→ FOCUS
→ HOVER
→ DEFAULT
```

这不意味着低优先级视觉必须完全消失；例如 selected navigation 仍必须显示 keyboard focus。

### UI-DS-STATE-004 — No Visual-only Truth

Selected、disabled、loading、expanded、error 等必须可通过 DOM/accessibility semantics 或明确 state 属性识别，不能只依赖 CSS color/opacity。

---

## 8. Button / Action

### UI-DS-COMP-001

Button 只承载 `Action` 或适用 `Control`。

至少支持 intent：

```text
primary
secondary
quiet/ghost
danger
```

### UI-DS-COMP-002

一个局部任务区域最多一个 primary intent。若两个按钮同等级，应先审查 task boundary。

### UI-DS-COMP-003

Action LOADING：

- single-flight；
- 保留用户可理解 label/context；
- pending 可被 assistive technology 感知；
- 完成后使用正式 result/re-query，不把 pressed/optimistic state 当 canonical success。

### UI-DS-COMP-004

Icon-only button 必须有 accessible name。Danger state 在 disabled/loading 时不得失去 destructive 语义。

---

## 9. Navigation

### UI-DS-COMP-010

Navigation item 支持：

```text
DEFAULT / HOVER / FOCUS / PRESSED / SELECTED
```

当前 destination 使用匹配的 `aria-current` / semantic state。

### UI-DS-COMP-011

Product Domain 与 Utility 必须视觉分组；Settings / Recovery 不得因同样 row style 被误认为第四/第五 Product Domain。

### UI-DS-COMP-012

Navigation activation 不产生隐藏 business write。

---

## 10. Rows / Lists / Interactive Content

### UI-DS-COMP-020

重复 domain object 默认使用 row/list，例如 Material、Activity、History、contextual Goal。

### UI-DS-COMP-021

Row 主点击区只表达一个可预测 intent。Trailing contextual action 是独立 focus target；Selection 与 open/navigation 不应混成无法预测的一次 click。

### UI-DS-COMP-022

Contextual action 不得只在 hover 出现；keyboard focus、touch、More Menu 或 Context Menu 必须存在等价发现路径。

---

## 11. Card

### UI-DS-COMP-030

Card 只在需要明确独立边界时使用，例如：

- 当前主要任务；
- typed rich response；
- recovery issue；
- 少量 mutually exclusive options；
- 需要独立语义边界的 evidence summary（contextual）。

禁止：

- 所有 section 都 Card 化；
- 所有 domain object 都 Card 化；
- 用 Card 数量表达 IA；
- “能点击”就自动做成 Card。

---

## 12. Status / Badge

### UI-DS-COMP-040

Badge/Chip 只表达短状态，如：

```text
待独立验证
已使用帮助
兼容记录
保存失败
```

长解释进入正文/Disclosure。

Status 默认不是 Action。若需要查看详情，提供独立 Disclosure / Navigation affordance。

---

## 13. Inputs / Composer

### UI-DS-COMP-050

Text input / textarea / Composer 必须：

- label/accessible name 完整；
- placeholder 不替代 label；
- disabled 与 read-only 区分；
- validation/error 与输入语义关联；
- async submit/validation 不静默覆盖用户内容；
- keyboard focus 清晰。

### UI-DS-COMP-051

Learning Composer 的具体 submit/Attempt/streaming semantics 由 `learning-interaction-contracts.md` 管理，Design System 只提供 reusable component state。

---

## 14. Selection

### UI-DS-COMP-060

Checkbox、radio、segmented control、listbox、picker、multi-select 必须按对应 semantic pattern 支持 selected/disabled/focus/keyboard states。

Selection 默认不等于提交 owner command，除非上游 contract 明确 immediate apply。

---

## 15. Disclosure / Drawer / Inspector / Sheet

### UI-DS-COMP-070

Disclosure trigger 使用匹配的 expanded semantic（如 `aria-expanded`）。

### UI-DS-COMP-071

Drawer/Inspector/Sheet 只承担附加上下文，不得成为隐藏关键任务唯一信息的借口。

### UI-DS-COMP-072

Transient sheet/modal：

- focus management 明确；
- Escape close（适用时）；
- close 后 focus 返回触发点；
- keyboard/touch 等价。

### UI-DS-COMP-073

复杂、可 deep-link、可返回的长期流程优先 destination/task flow，不应塞进 oversized modal。

---

## 16. Tabs

### UI-DS-COMP-080

Tab 只用于同一 local context 内的并列 views，不自动代表 Product Domain。

使用标准 tablist/tab/tabpanel semantics、keyboard navigation、selected state。

当前 Learning Right Rail 的 Material tabs 由 Learning Interaction Contract 定义；Design System 不提供通用 extension host。

---

## 17. Loading / Empty / Error

### UI-DS-FB-001 — Loading

使用与最终布局一致的最小 skeleton 或明确 progress；不得显示假数据。

### UI-DS-FB-002 — Empty

Empty 同时回答：

1. 当前没有什么；
2. 用户能做什么。

### UI-DS-FB-003 — Error

Error 显示用户可理解信息、适用 Retry Action 和必要的 safe diagnostic disclosure；不得暴露 raw traceback、secret、绝对路径或敏感环境信息。

### UI-DS-FB-004 — Partial / Stale

保留可用内容，同时明确限制与 freshness；不得伪装 READY。

---

## 18. Rich Learning Content

### UI-DS-RICH-001

继续支持 current Render contract 定义的 safe typed content，例如 Markdown/math/typed learning cards/citations。

未知 structured payload 安全回退 durable text content。

### UI-DS-RICH-002

Assistant message 不强制 bubble。Question、Feedback、Hint、Source 等可使用 semantic block/card/open content pattern，但不得通过 component style 改变 Teaching/Evidence 语义。

### UI-DS-RICH-003

公式、表格、代码、长引用在 200% zoom / 360px 下必须保持关键文字可访问。局部横向滚动可接受，页面整体横向滚动不可接受。

---

## 19. Accessibility

### UI-DS-A11Y-001

普通文字、关键 icon、输入边界、focus indicator 满足适用 WCAG AA。

### UI-DS-A11Y-002

所有 interactive role 在 accessibility tree 中可理解；不得依赖 Card visual、hover、color 表达交互性。

### UI-DS-A11Y-003

主要 touch target SHOULD ≥ 44×44 CSS px；桌面 compact control MAY ≥36px，但必须键盘可达并具有足够间距。

### UI-DS-A11Y-004

Icon-only control 有 accessible name；status/error/save state 有文本/语义冗余表达。

### UI-DS-A11Y-005

reduced motion 必须生效；live region 不得因 streaming token 造成持续语音轰炸。

---

## 20. Code / Asset Source-of-Truth Boundary

`.design_library/Askora/**`、HTML preview、组件 JSON、CSS 资产都是 supporting reference。

正式关系：

```text
Design System Spec
→ frontend component implementation
→ tests / visual regression
```

代码可以实现 Design System，但代码当前样式不能反向改变 Spec；如发现差异，标记 Design–Implementation Gap。

不得维护第二套独立 Design System truth 在：

- `.design_library`；
- page-local CSS conventions；
- Story/demo-only assets；
- screenshots。

---

## 21. Forbidden Implementations

禁止：

- token 名称直接等于页面/feature；
- component variant 定义业务状态 ownership；
- Card/Button/Badge 成为 interaction ontology；
- hover-only core action；
- disabled placeholder 表示未实现 feature；
- color-only status；
- heavy shadow/card ocean；
- page-local repeated hard-coded colors/spacing 替代 semantic token；
- Design System 自动扩张到新 Product Capability；
- 为未来 native/iOS 平台增加 v1 必须维护的额外组件体系。

---

## 22. Acceptance Criteria

- `UI-DS-AC-001`：核心 UI 使用统一 semantic tokens，新增页面不大量硬编码视觉值；
- `UI-DS-AC-002`：7 interaction primitives 与 component/pattern 明确分层；
- `UI-DS-AC-003`：Button/Nav/Row/Input/Selection/Disclosure/Tab/Status 的关键状态完整；
- `UI-DS-AC-004`：loading/empty/partial/stale/error 不通过 fake data 或 visual-only truth 表达；
- `UI-DS-AC-005`：contextual action 有 keyboard/touch fallback；
- `UI-DS-AC-006`：focus、target size、contrast、reduced motion、accessible names 符合合同；
- `UI-DS-AC-007`：360px / 200% zoom / long content 下 reusable components 不导致页面级横向滚动；
- `UI-DS-AC-008`：`.design_library` / code / screenshot 不形成第二 Design System Authority；
- `UI-DS-AC-009`：Design System pass 不被描述为 Product Acceptance 或 Learning Evidence pass。
