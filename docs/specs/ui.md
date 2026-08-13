# Askora Design System

> 状态：**Canonical UI Design System Contract — Current Only**  
> 冻结日期：2026-08-11  
> 上游产品定义：`PD-NFR-005` 及适用 Product Requirements  
> Governing Experience：`docs/design/experience/EXPERIENCE-ARCHITECTURE.md`、`docs/design/experience/INTERACTION-MODEL.md`、`docs/design/experience/LEARNING-EXPERIENCE.md`  
> 下游：frontend component implementation / tests  
> Supporting assets：`ui/traework/`（TraeWork Light foundation source；semantic roles 的 authority 仍是本文件）；`.design_library/Askora/**`（旧本地库，reference only, not authority）；`ui/prototypes/shell-replica/`（构图证据，不是 token 源）

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

当前 Light foundation 采用 TraeWork Light（`ui/traework/colors_and_type.css` / `css.json`）。Askora 保留本文件的 semantic role 名；业务代码 MUST 使用这些 role，不得直接散落 TraeWork 内部名或页面级 hex。

```text
accent              #4B3FE3
accent-subtle       #E0E5FF
canvas              #F5F5F5
surface             #FFFFFF
surface-subtle      #E5E5E5
surface-elevated    #FFFFFF
text-primary        #171717
text-secondary      #404040
text-muted          #737373
border              rgba(115, 115, 115, 0.12)
border.strong       rgba(115, 115, 115, 0.36)
success             #0F7A56
warning             #A85A00
error               #C9382F
info                #4B3FE3
focus               #4B3FE3
```

`accent-subtle` 是 TraeWork `--bg-brand-popup`（`#AAB7FF` @ 0.36）叠在白色上的合成值；实现 MAY 使用 `rgba(170, 183, 255, 0.36)`。

`success` / `warning` 相对 TraeWork `--status-*-default` 做了 text-on-canvas WCAG AA 微调（见 `UI-DS-TOK-005`）。`error` 使用 TraeWork `--status-error-active`，因 `--status-error-default` 作正文对比不足。颜色 MAY 因 WCAG 再微调，但 semantic role 不得漂移。

状态色作 fill/icon 时 MAY 使用 TraeWork 原始 `--status-*-default`，但不得把对比不足的 fill 配白色正文。`UI-DS-TOK-004` 仍然要求非颜色表达。

### UI-DS-TOK-003 — Dark Theme

v1 **不采用** Dark theme。TraeWork 官方库是 Light-only；`ui/prototypes/shell-replica/` 的测量 Dark hex **不得**写入本文件或生产 CSS。

若未来产品提供 dark theme，必须定义完整 semantic mapping，不得简单反转 Light，也不得把复刻页当 Dark foundation。没有正式 dark capability 时，不得新增主题设置。

### UI-DS-TOK-004 — State Colors

任何 state color 都必须同时有非颜色表达：文本、icon、shape、border 或 accessible state。

### UI-DS-TOK-005 — TraeWork Light Foundation Mapping

每个 Askora semantic role 必须能回溯到 TraeWork token 名。本表是 foundation 溯源，不是第二套 role 体系。

| Askora role | TraeWork token | TraeWork 源值 | Askora 采用值 |
|---|---|---|---|
| `color.accent` / `color.info` / `color.focus` | `--bg-brand` / `--border-brand` | `#4B3FE3` | `#4B3FE3` |
| `color.accent.subtle` | `--bg-brand-popup` | `#AAB7FF` @ 0.36 | `#E0E5FF`（合成） |
| `color.canvas` | `--bg-base-secondary` | `#F5F5F5` | `#F5F5F5` |
| `color.surface` / `color.surface.elevated` | `--bg-base-default` | `#FFFFFF` | `#FFFFFF` |
| `color.surface.subtle` | `--bg-base-tertiary` | `#E5E5E5` | `#E5E5E5` |
| `color.text.primary` | `--text-default` | `#171717` | `#171717` |
| `color.text.secondary` | `--text-secondary` | `#404040` | `#404040` |
| `color.text.muted` | `--text-tertiary` | `#737373` | `#737373` |
| `color.border` | `--border-neutral-l1` | `#737373` @ 0.12 | 同源 |
| `color.border.strong` | `--border-neutral-l3` | `#737373` @ 0.36 | 同源 |
| `color.success` | `--status-success-default` | `#15A877` | `#0F7A56`（AA 微调） |
| `color.warning` | `--status-warning-default` | `#E27900` | `#A85A00`（AA 微调） |
| `color.error` | `--status-error-default` | `#E8463A` | `#C9382F`（`--status-error-active`） |

消费顺序见 `ui/traework/library-consumption.json`。`ui_kits/` 不可 copyable，不得当生产页面模板。

---

## 4. Typography

### UI-DS-TYPE-001 — Font Stack

对齐 TraeWork `--font-family-default`，不引入远程 webfont：

```css
"SF Pro Text", "PingFang SC", system-ui, -apple-system, "Segoe UI",
"Microsoft YaHei", "Helvetica Neue", Arial, sans-serif
```

代码/标识继续使用系统等宽。不得为对齐 TraeWork `--font-family-metric` / `--font-family-mono` 而加载 Inter 或 JetBrains Mono 远程字体。

```css
ui-monospace, "SF Mono", Menlo, Monaco, Consolas, monospace
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

### UI-DS-COMP-013 — Create Space Action

`＋ 新建空间` 使用既有 primary Action / Button foundation，不创建 Space-specific token 或独立 button family。其层级在 Left / Where 中突出，但仍必须具备 focus、pending、error 与 accessible name；打开 flow 不等于创建成功。

---

## 10. Rows / Lists / Interactive Content

### UI-DS-COMP-020

重复 domain object 默认使用 row/list，例如 Material、Activity、History、contextual Goal。

### UI-DS-COMP-021

Row 主点击区只表达一个可预测 intent。Trailing contextual action 是独立 focus target；Selection 与 open/navigation 不应混成无法预测的一次 click。

### UI-DS-COMP-022

Contextual action 不得只在 hover 出现；keyboard focus、touch、More Menu 或 Context Menu 必须存在等价发现路径。

### UI-DS-COMP-023 — Course Row

Course row 复用 Navigation / InteractiveContent row：

- primary label 使用空间名称；
- selected/current、focus 与 pending switch 状态可同时被识别；
- trailing state/action 是独立 target；
- 不使用统计 Card、彩色学科 token 或 mastery decoration 让空间或对话列表变成 Dashboard。

### UI-DS-COMP-024 — Activity Switcher

Activity Switcher 复用 Row/List + Disclosure/Navigation pattern。Activity title 使用学习语义；current/resumable/available 状态有文本或结构表达。Start/Resume Action 与仅查看/导航的 intent 不得混成不可预测的一次 click。

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

### UI-DS-COMP-090 — TraeWork Component Mapping

本表只冻结下一轮组件消费对照，不授权本轮改组件实现，也不授权从 `shell-replica` 复制 IA。

| Askora 合同 | TraeWork slug / 资产 | 消费规则 |
|---|---|---|
| Button / `＋ 新建空间` | `buttons` | copy `preview/component-buttons.html`；不造 Space-specific button family |
| Course Row / Activity Switcher | `menu` + row/list | 复用既有 Navigation / Row foundation |
| Learning Composer | `ai-input` | 解剖：textarea + control row + send；submit 语义仍听 Learning Interaction Contract |
| Status / Badge | `tag` / `alert` | 短状态；长解释进 Disclosure |
| Dialog / Sheet | `dialog` | focus / Escape / restore 仍听 `UI-DS-COMP-072` |
| 三栏几何 | `shell-three-panel` | 只借宽度/gutter；槽位仍是 Where / Learn / Notes |
| Icons | `assets/icons/` | `currentColor` mask；不得手绘第二套 icon |

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

`ui/traework/` 是 Light foundation source。`.design_library/Askora/**`、`ui/prototypes/**`、HTML preview、组件 JSON 都是 supporting reference，不能覆盖本文件的 semantic roles。

正式关系：

```text
Design System Spec（本文件 semantic roles）
→ TraeWork Light foundation 值（UI-DS-TOK-005）
→ frontend component implementation
→ tests / visual regression
```

代码可以实现 Design System，但代码当前样式不能反向改变 Spec；如发现差异，标记 Design–Implementation Gap。

不得维护第二套独立 Design System truth 在：

- `.design_library`；
- `ui/prototypes/shell-replica` 的 Dark 测量值；
- page-local CSS conventions；
- Story/demo-only assets；
- screenshots。

---

## 21. Forbidden Implementations

禁止：

- token 名称直接等于页面/feature；
- Course-specific color/token/component fork；
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

- `UI-DS-AC-001`：核心 UI 使用统一 semantic tokens，新增页面不大量硬编码视觉值；foundation 值必须能按 `UI-DS-TOK-005` 回溯到 TraeWork token 名；
- `UI-DS-AC-002`：7 interaction primitives 与 component/pattern 明确分层；
- `UI-DS-AC-003`：Button/Nav/Row/Input/Selection/Disclosure/Tab/Status 的关键状态完整；
- `UI-DS-AC-004`：loading/empty/partial/stale/error 不通过 fake data 或 visual-only truth 表达；
- `UI-DS-AC-005`：contextual action 有 keyboard/touch fallback；
- `UI-DS-AC-006`：focus、target size、contrast、reduced motion、accessible names 符合合同；
- `UI-DS-AC-007`：360px / 200% zoom / long content 下 reusable components 不导致页面级横向滚动；
- `UI-DS-AC-008`：`.design_library` / code / screenshot 不形成第二 Design System Authority；
- `UI-DS-AC-009`：Design System pass 不被描述为 Product Acceptance 或 Learning Evidence pass。
- `UI-DS-AC-010`：新建空间、空间/对话 Row 与已有对话列表复用既有 Action/Nav/Row/Disclosure foundation，无 feature-specific token fork。

---

## Askora Learning Interaction Contracts

> 状态：**Canonical UI/UX Implementation Contract — Current Only**  
> 冻结日期：2026-08-11  
> 上游产品定义：`CAP-04`、`CAP-05`、`CAP-06`、`CAP-07`  
> Governing Experience：`docs/design/experience/LEARNING-EXPERIENCE.md`、`docs/design/experience/INTERACTION-MODEL.md`  
> Governing ADR：ADR-0018、ADR-0019、ADR-0022
> 技术上游：Assessment / Teaching Policy / Activity Lifecycle / Render / Workspace Read Projection current Specs

---

### 1. Purpose

本文件把 Askora 的 Learning Experience 转化为可实现、可测试的 UI interaction contract。

它定义：

- Learning Canvas composition；
- learning conversation / learning unit 的呈现语义；
- Question / Attempt / Feedback / Hint / Remediation；
- assistance / answer exposure / validation obligation；
- streaming；
- citation / SourceSpan / Current Material；
- Learning Notes；
- Learning Context Drawer；
- long-session continuity；
- keyboard / screen-reader order。

本文件不拥有 TeachingAction、AssessmentResult、LearningEvidence、MasteryEstimate、ReviewSchedule、LLM prompt 或 persistence schema。

---

### 2. LearningActivity Is the UI Context

#### UI-LRN-001

LearningActivity 是 Learning Workspace 的主要体验上下文。单条 message、prompt 或 session 不得成为独立产品主对象。

#### UI-LRN-002

进入/切换 Course/Activity presentation、展开 Drawer、打开 Material、隐藏 Right Rail 不得生成新的：

```text
LearningActivity
Attempt
TeachingAction
AssessmentResult
transcript truth
```

#### UI-LRN-003

兼容 `/quick/:sessionId` 或历史 dialog 必须明确 compatibility source；缺少 canonical activity/policy/evidence data 时显示“当前记录不可用”，不得补造。

#### UI-LRN-004 — Course Scope

Learning Workspace 必须显示用户可理解的当前空间，并解析同一 canonical `workspace_id`。Space/course route、Activity ref 与 Workspace query 不一致时 fail closed，不得用 route 覆盖 owner truth。

#### UI-LRN-005 — Activity Switcher / Recent Learning

Activity Switcher 只读取当前 Course 内 exact Activity refs：

- current/active/resumable/available state 来自 SYS06 owner；
- title 描述学习目的，不使用 Chat 1/2/3；
- 打开 active/resumable Activity 不复制 Activity、Session 或 transcript；
- 启动 available Activity 调用正式 lifecycle Action；
- conversation/message count 不参与排序或学习优先级推断。

---

### 3. Learning Canvas Composition

中央 Learning Canvas 按以下优先级组织：

```text
Current learning task / teaching content
→ learner thinking / input
→ feedback / remediation
→ necessary assistance / validation state
→ necessary citation / source context
→ lightweight orientation
```

#### UI-LRN-010 — Required Regions

适用时至少包含：

- 当前 Activity / task identity；
- teaching / question content；
- learner response input；
- feedback/result；
- Composer / submit action；
- streaming/error/recovery status；
- validation obligation；
- citation / source affordance。

#### UI-LRN-011 — No Dashboard Competition

Goal/Plan/Progress/Evidence chart、Knowledge Graph、system diagnostics 不得与当前学习任务形成等权 permanent region。

---

### 4. Learning Conversation / Unit Semantics

#### UI-LRN-020 — Required Learning Roles

UI 必须能让用户区分以下语义角色：

```text
Teaching / Explanation
Question / Task
Learner Attempt
Feedback
Hint / Scaffold
Remediation
Source / Evidence Context
Status / Recovery
```

这些是 Experience roles，不要求形成新的 backend enum；当 backend 提供 typed render payload 时应优先使用 canonical payload。

#### UI-LRN-021 — Message Identity

无论使用开放内容、bubble、card 或其他 pattern，都必须保持：

- origin / role；
- message/event order；
- Activity/session association；
- durable content fallback；
- structured payload validity；
- citation/provenance；
- assistance / validation state（存在时）。

#### UI-LRN-022 — No Bubble-only Model

Assistant 长解释、Question、Feedback 或 structured learning content 不要求统一套聊天气泡。视觉选择应服务阅读、推理和学习角色识别。

User short Attempt 可以使用紧凑 presentation，但不得因视觉样式丢失 Attempt identity。

#### UI-LRN-023 — Grouping

连续消息 MAY 按同一 teaching turn / task context 进行视觉分组，但不得：

- 重排 durable event order；
- 合并不同 Attempt；
- 把历史 Feedback 冒充当前 Feedback；
- 因分组隐藏 citation / assistance / validation semantics。

长历史可以分页/虚拟化，但当前 task、最近 Attempt、当前 Feedback 与 active streaming state 必须稳定可达。

---

### 5. Question / Task

#### UI-LRN-030

Question / Task 必须具有明确视觉起点，不能埋在长 explanation 末尾而无可识别 task boundary。

#### UI-LRN-031

当 activity 要求 active retrieval / generation / reasoning 时，UI 必须提供真实 learner input opportunity；不得自动填充 AI answer 并把其视为 learner response。

#### UI-LRN-032

任务所需 source / constraints / expected response form 应在用户作答前可理解；内部 grader-only rubric 不得泄露。

---

### 6. Learner Attempt

#### UI-LRN-040 — Attempt Integrity

用户提交后的 Attempt 必须保留其原始内容与 identity。Feedback、AI rewrite 或 retry 不得静默覆盖历史 Attempt。

#### UI-LRN-041 — Submit Semantics

Submit 是 `Action`：

- pending 时 single-flight；
- 不允许重复 accidental submit；
- success/failure 必须来自正式 command/result；
- `pressed`/local optimistic state 不等于成功；
- 提交失败不得把用户输入静默清空。

#### UI-LRN-042 — Retry

Retry / “再试一次”产生新的 learner behavior。是否形成新的 LearningEvidence 以及证据权重由 Assessment/Evidence owner 决定，frontend 不推断。

---

### 7. Feedback & Remediation

#### UI-LRN-050 — Feedback Anatomy

Feedback 应在可用数据范围内表达：

- 哪部分成立；
- 哪部分需要修正；
- 关键原因；
- 当前合法下一步。

不得只依赖绿色/红色、score 或 emoji 表达正确性。

#### UI-LRN-051 — Learner Error vs System Error

以下故障不得显示成“你答错了”：

- model/provider failure；
- tool failure；
- retrieval/source failure；
- network/runtime error；
- invalid structured payload；
- stale/version conflict。

#### UI-LRN-052 — Remediation

Remediation 应保持当前 Workspace / Activity / source context。UI 不应因为一次错误自动把用户送往全局知识库、独立 chat 或无限分支。

#### UI-LRN-053 — Recovery

retryable system failure 可以提供 Retry Action；不可 retry 的状态应给出对应 owner-defined RecoveryAction / next step。不得通过重新创建 Activity/Session 假装恢复。

---

### 8. Assistance / Answer Exposure

#### UI-LRN-060 — Planned vs Actual

UI 必须区分：

```text
allowed / planned assistance envelope
actual assistance already used
```

缺 actual data 时不得复制 planned data 作为事实。

#### UI-LRN-061 — User-readable Assistance State

存在 canonical data 时，使用学习者可理解表达，例如：

```text
独立作答
已使用帮助
已看到关键步骤
已暴露答案
待独立验证
```

UI 不得根据 message length、card variant、click count 或文本内容推断 canonical assistance state。

#### UI-LRN-062 — Help Controls Are Requests

“给一点提示”“解释概念”“给例子”“拆成步骤”“直接告诉我”等控件是用户 request `Action`，不是 TeachingAction editor。

#### UI-LRN-063 — Autonomy Without Evidence Corruption

用户可以请求完整答案。UI 不得用交互阻止合法用户自主选择；但答案暴露后的表现不能被文案/视觉包装为无提示独立掌握。

#### UI-LRN-064 — Validation Obligation

需要 fresh independent validation 时必须呈现“待独立验证”或等价用户文案。它不是 error，也不是惩罚状态。

---

### 9. Streaming Contract

#### UI-LRN-070 — Streaming State Machine

至少区分：

```text
RUN_STARTING
STREAMING_CONTENT
FINAL_PAYLOAD_VALIDATING
COMPLETED
FAILED
RECOVERABLE
```

#### UI-LRN-071

partial text MAY 增量显示，但半完成 structured payload 不得被当作 final Question / Feedback / Card contract 渲染。

#### UI-LRN-072

最终 structured payload 只有通过 schema / safe-render validation 后才替换或增强 fallback content。

未知/无效 payload 必须安全回退 durable `content`；不得渲染 raw HTML、MDX、executable model-defined component 或未授权 remote image。

#### UI-LRN-073

断线/重连/重试不得产生重复 assistant message、Attempt、LearningEvent 或 Evidence。

#### UI-LRN-074

stream 进行中离开/切换 Workspace 时必须进入当前 owner/route contract 定义的明确状态，不得仅通过卸载 component 丢弃运行。

---

### 10. Citation / Provenance

#### UI-LRN-080 — Traceable Source

资料型回答的引用必须可追踪 SourceSpan / canonical source ref。

主要显示：

- 可读 source label；
- locator / 原文位置；
- “查看原文”等可预测 affordance。

内部 UUID/version 可放 Disclosure，不作为唯一用户信息。

#### UI-LRN-081 — Source vs Model Knowledge

当内容不是来自用户 Material 时，不得通过 citation style、标题或措辞假装“来自资料”。

#### UI-LRN-082 — View Source In Context

在 Learning Workspace 中查看 source 优先打开 Right Rail Current Material，不使 Center 离开当前 learning context。

#### UI-LRN-083 — Missing Source

缺 SourceSpan / 可显示原文时显示不可用/来源不足。禁止使用 AI Summary、filename 或模型记忆伪造原文。

#### UI-LRN-084 — Cross-Workspace Fail Closed

Material/source ref 必须属于当前 Workspace scope；跨 Workspace ref 不得通过错误信息泄露对象是否存在。

---

### 11. Current Material Tabs

#### UI-LRN-090

Right Rail Current Material 可以由 citation / view-source 打开一个或多个 tabs。

打开、切换、关闭 tab：

- 属 Navigation / Disclosure；
- 不改变 Center Activity；
- 不产生 business write；
- 不创建新的 Activity/TeachingAction；
- tab/source position 是 presentation state，可在合法范围恢复。

#### UI-LRN-091

V1 不提供 generic `+` extension host，不为 deferred modules 创建 tab placeholder。

---

### 12. Learning Notes

#### UI-LRN-100 — User-authored Truth

Learning Notes 是 Product Definition 中的 `UserNote`，是 user-authored durable data；不是 AI Summary，也不是 canonical Material/Knowledge truth。

#### UI-LRN-101 — Scope / Anchor

Notes 必须服从 current Workspace scope，并在 owner contract 支持时保留 Activity / Material anchor。

#### UI-LRN-102 — Required Note States

UI 必须区分：

```text
SAVING
SAVED
FAILED
CONFLICT
RECOVERABLE
```

未持久化时不得显示“已保存”。

#### UI-LRN-103 — Conflict

version/revision conflict 不得静默覆盖较新 durable note；应重新读取并要求用户明确处理。

#### UI-LRN-104 — AI Assistance

AI 可在用户明确请求时辅助整理/改写笔记，但不得无确认覆盖 user-authored original。

#### UI-LRN-105 — Source to Note

“引用/加入笔记”类快捷动作只有在 UserNote owner/anchor contract 支持时可出现。

合法实现应保留：

- 用户可编辑文本；
- source/material anchor（若有）；
- Workspace scope；
- saving/conflict feedback。

不得把 AI 自动摘要直接写成用户笔记。

---

### 13. Learning Context Drawer

#### UI-LRN-110 — Placement / Default

Drawer 在 Composer 上方，默认收起，不占 Right Rail。

#### UI-LRN-111 — Collapsed

只显示一行轻量方向，例如：

```text
当前阶段 · 接下来：……
```

#### UI-LRN-112 — Expanded

只允许：

- current stage；
- stage goal；
- next 1..3 dynamic learning directions。

#### UI-LRN-113 — Data States

至少区分：

```text
LOADING
READY
MISSING
PARTIAL
STALE
ERROR
```

MISSING/PARTIAL/STALE 不得冒充 READY。

#### UI-LRN-114 — No Frontend Inference

Drawer 内容必须来自 canonical/versioned projection；frontend 不得从 chat、heading sequence、probability threshold 推断 next knowledge point。

#### UI-LRN-115 — Presentation Only

expand/collapse 是 Disclosure presentation state，不触发 owner command；Drawer failure 不得无条件阻断当前 Attempt。

---

### 14. Long-session / History Behavior

#### UI-LRN-120

当前 active task、最近 learner Attempt、对应 Feedback 和 active streaming state 必须容易定位。

#### UI-LRN-121

历史内容可 virtualize/paginate；durable event order 不得因 performance optimization 改变。

#### UI-LRN-122

历史 state 必须与 current active state 视觉/语义分离。旧 TeachingAction、Plan、Evidence、DecisionTrace 不得冒充当前 truth。

#### UI-LRN-123

恢复历史 session/activity 时优先恢复 durable active/resumable context；不存在 canonical link 时必须保留 compatibility label，不自动创建伪造 link。

---

### 15. Keyboard / Screen Reader Order

#### UI-LRN-130 — Reading Order

Learning Canvas 的可访问阅读顺序原则上保持：

```text
Activity/task context
→ current teaching/question
→ learner Attempt/input
→ Feedback/status
→ Composer/actions
→ Context Drawer
→ Right Rail trigger / auxiliary content
```

具体 DOM 可以因 responsive pattern 调整，但 semantic order 不得让辅助栏先于主要学习任务占据读取主线。

#### UI-LRN-131

stream/status/save/error 需要适当 live announcement，避免每个 token delta 都造成 screen-reader spam。

#### UI-LRN-132

Drawer、Right Rail、Material tabs、transient sheet 必须：

- keyboard 可操作；
- Escape 关闭适用 transient surface；
- 关闭后 focus 返回触发点或合理下一目标；
- Contextual Action 不依赖 hover-only discoverability。

---

### 16. Forbidden Implementations

禁止：

- conversation completion → mastery；
- “我懂了” → LearningEvidence；
- assistant-generated answer → learner Attempt；
- actual assistance 缺失时用 planned assistance 冒充；
- frontend threshold → mastery label；
- 系统错误 → learner incorrect；
- structured streaming 半成品 → final card/assessment；
- raw HTML / executable model-defined UI；
- filename/summary → fabricated original；
- frontend-only note/localStorage → durable UserNote；
- 切换 Workspace / rail / route 静默丢 draft/stream/note；
- Activity Switcher 使用 Chat thread title/count 或跨 Course refs；
- Right Rail 建通用 extension host；
- 无限 chat thread 取代 LearningActivity continuity。

---

### 17. Acceptance Criteria

- `UI-LRN-AC-001`：LearningActivity 而非 chat/message 是主体验上下文；
- `UI-LRN-AC-002`：Question / Attempt / Feedback / Hint / Remediation / Source roles 可识别；
- `UI-LRN-AC-003`：提交 Attempt single-flight，失败不丢输入，retry 不覆盖历史 Attempt；
- `UI-LRN-AC-004`：learner error 与 model/tool/retrieval/runtime error 明确分离；
- `UI-LRN-AC-005`：planned vs actual assistance、answer exposure、validation obligation 不被 frontend 推断；
- `UI-LRN-AC-006`：streaming partial structured payload 不作为 final truth，重连不重复 event/message；
- `UI-LRN-AC-007`：citation 可追踪 SourceSpan，view source 保持当前 learning context；
- `UI-LRN-AC-008`：跨 Workspace source fail closed，缺原文不伪造；
- `UI-LRN-AC-009`：Notes 区分 SAVING/SAVED/FAILED/CONFLICT/RECOVERABLE，未持久化不宣称 saved；
- `UI-LRN-AC-010`：Drawer 只显示 stage/stage goal/next 1..3 且 frontend 不推断；
- `UI-LRN-AC-011`：历史/current state 不混淆，长 session 可扩展而不改 durable order；
- `UI-LRN-AC-012`：keyboard/screen-reader/focus/live-region 行为可自动/人工验证；
- `UI-LRN-AC-013`：UI interaction pass 不被描述成 Product Acceptance 或 Learning Evidence pass。
- `UI-LRN-AC-014`：Course / Activity / Session hierarchy 清晰，Activity Switcher 只使用当前 Course exact refs。

---

## Askora UI/UX Quality & Regression Contract

> 状态：**Canonical UI/UX Quality Contract — Current Only**  
> 冻结日期：2026-08-11  
> 上游：`docs/product/PRODUCT-DEFINITION.md`、`docs/design/experience/**`  
> Governing quality：`docs/specs/quality/testing-standard.md`、`definition-of-done.md`、`security-standard.md`、`v1-local-web-quality-reconciliation.md`  
> Scope：长期有效 UI/UX verification；一次性 migration 执行细节属于 Vertical Slice / EXEC

---

### 1. Purpose

本文件定义 Askora UI/UX 长期必须满足的质量门禁。

它回答：

> **如何证明界面仍然符合当前 Experience / UI contracts，并且没有破坏学习、来源、数据诚实、可访问性与安全边界。**

本文件不维护当前 backlog、EXEC 队列、临时 migration 顺序或已完成 issue 状态。

---

### 2. Acceptance Ownership

必须区分：

```text
Product Acceptance
UX Acceptance
UI Contract / Engineering Acceptance
Accessibility / Security Acceptance
Learning Evidence
```

UI/UX PASS 不能自动满足 Product Acceptance，更不能证明真实 retention / transfer / mastery 改善。

---

### 3. Traceability Gate

#### UI-QR-001

关键 UI test / acceptance evidence 必须可追踪到适用：

- Product `CAP-* / PD-REQ-* / PD-RULE-*`；
- Experience `EXP-* / LEXP-* / INT-*`；
- UI current contract `UI-SN-* / UI-LRN-* / UI-DS-*`；
- technical/security contract（适用时）。

不得只用 screenshot / snapshot 证明业务或学习语义。

#### UI-QR-002

如果实现要求改变 Product Scope，报告 `PRODUCT DEFINITION GAP`；如果 Product 已明确但 Experience/Spec 不足，分别报告 `DESIGN GAP` / `SPEC GAP`。

不得通过 frontend-only state 静默解决上游 gap。

---

### 4. Semantic Regression

必须验证：

- Today / Learning 不再是 L0 或 stable Product Domain；
- `＋ 新建空间`、加入学习空间、马上开始学习、对空间继续学习是 Action；已有对话是 Navigation / InteractiveContent；
- 用户界面使用“空间”“对话”，canonical Workspace / LearningActivity identity 不变；
- Settings/Recovery 是 Utility；
- Chat/Tutor 不成为 Product Domain；「对话」不得做成 Chat thread manager；
- 空间不恢复 Goal/Plan/Progress/History 常驻管理中心；
- 不新增 Today replacement Dashboard；
- route/navigation 不产生隐藏 business write；
- domain object 不因新增 backend projection 自动变成 page/nav/card；
- frontend 不产生第二 canonical truth。

---

### 5. Learning Experience Regression

至少验证：

- current Activity / task 可识别；
- learner 有真实 Attempt 路径；
- Question / Attempt / Feedback / Hint / Remediation / Source 语义可理解；
- learner error 与 model/tool/retrieval/runtime error 分离；
- actual assistance / answer exposure / validation obligation 不由 frontend 推断；
- citation 可回真实 SourceSpan；
- view source 不破坏 current learning context；
- Notes 不静默丢失且 save/conflict 状态真实；
- interrupted learning 可恢复；
- long session/history 不把旧 state 冒充 current state。

---

### 6. Workspace Isolation / Continuity

必须验证：

- Left/Center/Right/Drawer 使用同一 current Workspace；
- Course list/create/current/switch 来自 Platform Workspace Registry owner contract；
- Workspace switch 处理 draft / stream / note / active session / material position；
- cross-Workspace Material/Source/Note access fail closed；
- Activity Switcher 只显示当前 Course exact refs，不使用 Chat thread title/count；
- Workspace switch 不通过清空 frontend state 假装成功；
- browser memory 不被描述为 durable recovery。

---

### 7. Screen State Regression

关键 screen/region 至少测试适用：

```text
LOADING
EMPTY
READY
PARTIAL
STALE
ERROR
UNAUTHORIZED
```

特定 projection：

```text
MISSING
LOW_CONFIDENCE
```

Action / Note 等还需适用：

```text
LOADING/PENDING
SAVED
FAILED
CONFLICT
RECOVERABLE
DISABLED
```

禁止：

- catch 后返回空数组伪装 EMPTY；
- MISSING → 0/false/空进度条；
- stale/partial → READY；
- 未持久化 → SAVED；
- system failure → learner incorrect。

---

### 8. Responsive Gate

每次涉及 shell、核心 screen、Design System foundation 的 substantive UI change，至少验证：

```text
1440×900
1024×768
768×1024
360×800
100% zoom
200% zoom
```

必须证明：

- Primary task 可完成；
- 页面无阻断性横向滚动；
- Right Rail / Drawer / auxiliary surfaces 在窄屏有可访问替代；
- citation/error/assistance/validation obligation 不会因窄屏永久消失；
- 无关键三层嵌套滚动；
- 中文长标题、长公式、长引用、长错误可处理。

---

### 9. Keyboard / Accessibility Gate

至少覆盖：

- keyboard-only primary learning path；
- focus order / visible focus；
- route navigation 后语义起点 focus；
- modal/sheet/drawer close 后 focus return；
- Escape close（适用 transient surface）；
- icon-only accessible name；
- contextual action keyboard/touch fallback；
- status/error/save live announcement；
- screen-reader 能理解 Left/Center/Right/Drawer 与主要 learning roles；
- state 不只靠 color；
- reduced motion；
- WCAG AA 对比度（适用文本/关键 UI）。

streaming 不得对每个 token delta 产生 screen-reader spam。

---

### 10. Design System Regression

必须验证：

- semantic token 使用；
- Button/Nav/Row/Input/Disclosure/Tab/Status states；
- Primary/Secondary/Contextual hierarchy；
- repeated object 默认 row/list；
- 无 Card ocean；
- no hover-only core action；
- page-local CSS 不建立第二 token体系；
- `.design_library` / `shell-replica` / screenshot 不被当作 runtime Authority；foundation 回溯 `UI-DS-TOK-005`。

视觉回归只能证明 presentation regression，不证明 interaction/business semantics。

---

### 11. Route / Deep-link Regression

至少验证：

- `/`、`/courses/new`、`/courses/:workspaceId`、course-scoped Activity destination；
- `/today`、`/learning` compatibility resolution；
- Workspace-scoped routes（存在时）；
- activity/session deep links；
- compatibility goal/plan/progress/history routes；
- back/reload；
- legacy redirect no side effect；
- no redirect loop；
- route change 不丢未提交/可恢复状态；
- retirement 前历史 deep link 有明确行为。

---

### 12. Library / Provenance Regression

必须验证：

- import/search/filter/material list 基础路径；
- batch/contextual action 只在正确 context 出现；
- normal v1 UI 无 OCR action/status/review；
- scanned PDF unsupported/partial honest fallback；
- deferred candidates 无 placeholder；
- source label/locator/SourceSpan 真实可追踪；
- 无跨 Workspace source leakage。

---

### 13. Settings / Local Data / Security Regression

设置重构不得弱化上游安全与数据合同。

至少验证：

- BYOK credential 不回填、不进入普通 DOM/web storage/log/backup/export；
- data backup / export / restore / erasure 语义不混淆；
- destructive confirmation / revision conflict / retry 保持；
- Account/Login/AuthSession residue 不重新可达；
- Recovery 只使用正式 owner-defined actions；
- raw traceback、secret、绝对路径、敏感 environment 不在普通 UI 暴露。

---

### 14. Rich Content / Streaming Security

继续覆盖：

- unsafe raw HTML；
- unsafe URL；
- unauthorized remote image；
- invalid structured render payload；
- prompt-injection / grader-only leakage；
- unauthorized source/evidence；
- duplicated stream finalization；
- historical message online LLM re-generation。

Durable historical rendering必须使用已持久化 content/render payload，不为旧消息重新调用在线模型补富文本。

---

### 15. Performance Evidence

涉及性能敏感 UI 时先记录 baseline，再定义不回归或明确 budget。

至少关注：

- production bundle；
- first usable shell；
- Workspace switching；
- long learning history；
- Material list；
- RichMessage/Math lazy load；
- memory growth across repeated route/workspace switch。

无 measurement 不得发明硬阈值。

长 History/Conversation SHOULD 评估 pagination/virtualization；不得一次性加载全部私人 message/evidence history。

---

### 16. Required Engineering Gates

前端 UI substantive change 默认至少运行：

```bash
cd apps/frontend
npm test -- --run
npm run build
npm audit --audit-level=high

cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

如果修改 backend query/API，再运行适用 backend targeted + full gates，以及 current Required CI 所要求的质量命令。

全量 gate 因既有问题失败时必须区分：

```text
introduced failure
vs
pre-existing failure
```

不得删除测试、弱化断言、扩大 ignore 来制造 PASS。

---

### 17. Human UX Acceptance

仅自动化通过仍不足以证明复杂学习体验质量。M5 / release acceptance 应至少人工检查：

- 首次进入是否理解该做什么；
- 上传资料 → 加入空间或马上开始学习 → 首段对话是否自然；
- Welcome / 已有对话恢复 / 对空间继续学习是否可理解；
- 对话中作答、反馈、请求帮助、查看原文是否成立；
- 新建空空间、往已有空间补资料是否诚实、不自动假开聊；
- 长解释与 Question boundary 是否清晰；
- Attempt / Feedback 是否容易对应；
- citation / source 查看是否不打断学习；
- assistance / validation 文案是否可理解；
- Workspace switch 风险是否清楚；
- 360/768/1024/1440 下任务层级是否仍成立；
- 错误/partial/stale 是否诚实；
- Settings/Recovery 是否保持次级 utility 角色。

人工 UX Acceptance 仍不能被描述为学习效果证据。

---

### 18. Completion / Claim Boundary

UI / UX 工作完成可以声明：

```text
UX Contract Gate: PASS
UI Engineering Gate: PASS
Accessibility Gate: PASS
Security UI Gate: PASS
```

仅在适用 Product Acceptance 已有独立证据时，才可声明对应 Product Acceptance。

以下永远不能仅由 UI PASS 推导：

```text
Learner mastered
Retention improved
Transfer improved
Adaptive policy superior
Learning Evidence Gate PASS
```

---

### 19. Blocking Conditions

以下任一存在时，不得把相关 UI slice 标 DONE：

- Product / Design / Spec authority conflict 未解决；
- frontend mock 冒充 canonical owner truth；
- Course 恢复常驻管理 dashboard；
- Today / Learning L0 或 replacement Dashboard 回归；
- Workspace scope 不一致；
- Course create/switch 或 Activity Switcher 使用 frontend mock/placeholder；
- Note/source 有静默数据丢失或 leakage；
- Library normal UI 暴露已排除 OCR/deferred candidate；
- 360 / 200% zoom / keyboard / error path 未验证；
- MISSING/PARTIAL/STALE 被伪装 READY；
- UI/spec/API/schema change 未声明；
- 通过删除/弱化测试制造 PASS。

---

### 20. Acceptance Criteria

- `UI-QR-AC-001`：current Experience → UI Contract → test traceability 完整；
- `UI-QR-AC-002`：semantic/nav/learning/workspace regression gates 有自动化证据；
- `UI-QR-AC-003`：1440/1024/768/360 + 200% zoom 验证；
- `UI-QR-AC-004`：keyboard/screen-reader/focus/contextual-action 验证；
- `UI-QR-AC-005`：Library/provenance/Settings/security 边界无回归；
- `UI-QR-AC-006`：long-session / streaming / source / notes failure paths 有验证；
- `UI-QR-AC-007`：一次性 migration status 不进入本长期合同；
- `UI-QR-AC-008`：UI/UX Acceptance、Product Acceptance、Learning Evidence 分开报告。
- `UI-QR-AC-009`：Welcome、空间/对话 navigation、empty/create/switch、「继续学习」与 legacy route migration 有自动化和人工证据。

---

## Askora Screen & Navigation Contracts

> 状态：**Canonical UI/UX Implementation Contract — Current Only**  
> 冻结日期：2026-08-13  
> 上游产品定义：`docs/product/PRODUCT-DEFINITION.md`  
> Governing Experience：`docs/design/experience/EXPERIENCE-ARCHITECTURE.md`、`docs/design/experience/INTERACTION-MODEL.md`  
> Governing ADR：ADR-0014、ADR-0015、ADR-0018、ADR-0022、ADR-0025、ADR-0026
> 技术上游：Workspace / Goal / Activity / Recovery / Onboarding current Specs

---

### 1. Purpose

本文件定义 Askora 当前有效的：

- user-facing Information Architecture；
- Navigation hierarchy；
- route / deep-link behavior；
- shell / screen responsibility；
- page-level loading / empty / error / recovery；
- responsive screen behavior。

本文件只保存**当前有效规则**，不包含已被 ADR-0018 supersede 的旧 Learning four-facet 常驻管理模型。

本文件不拥有 Product Capability、domain ownership、API schema、persistence、Teaching Policy 或 component visual tokens。

---

### 2. Product Definition Traceability

主要映射：

| Area | Product Definition |
|---|---|
| Workspace / Library | `CAP-01`、`CAP-07`、`PD-REQ-0101..0104`、`PD-RULE-006/009/011` |
| Goal / Next Activity | `CAP-02`、`CAP-03`、`CAP-07`、`PD-REQ-0201..0203`、`PD-REQ-0301..0303` |
| Learning Canvas | `CAP-04`、`CAP-05`、`PD-REQ-0401..0403`、`PD-REQ-0501..0503` |
| Review / Validation return | `CAP-06`、`CAP-07`、`PD-REQ-0601..0603`、`PD-REQ-0701..0703` |
| Local data / settings | `CAP-08`、`PD-REQ-0801..0804`、`PD-RULE-008/010/011` |
| Accessibility / usability | `PD-NFR-005` |

UI Acceptance 不自动等同 Product Acceptance 或 Learning Evidence。

---

### 3. Required Screen State Vocabulary

所有依赖 canonical data 的 screen / region 必须区分适用状态：

```text
LOADING
EMPTY
READY
PARTIAL
STALE
ERROR
UNAUTHORIZED
```

附加规则：

- `PARTIAL` / `STALE` 不得显示成完整 READY；
- `MISSING` 可用于特定 optional projection，例如 Context Drawer；
- 局部数据失败优先局部降级，不应无条件让整个学习画布白屏；
- Empty 必须说明“缺什么”和“下一步能做什么”；
- Error 必须基于 stable error / retryability / recovery contract，而不是匹配自由文本；
- 不得用 fake data 填补 Goal、Activity、Evidence、Material 或 Workspace 空态。

---

### 4. Canonical User-facing IA

#### UI-NAV-001 — Space-centric IA

稳定用户侧结构只允许：

```text
Welcome                      Default Destination
已有对话                      Navigation / InteractiveContent
＋ 新建空间                   Action
资料库                        Stable Product Domain Navigation
Settings / Recovery           Utility Navigation
```

Today / Learning 不得作为 stable Product Domain、L0 Navigation 或默认 destination 出现。打开 App 的默认目的地是 Welcome。

#### UI-NAV-002 — Utilities

以下属于 App Utility，不与 Product Domain 等权：

```text
设置
恢复中心
Search / Command（仅正式 capability 存在时）
```

Askora v1 无 Login / Register / Account shell。

#### UI-NAV-003 — Space Is Not a Management Center

空间不提供 Goal / Plan / Progress / History 的常驻管理 navigation。

这些 domain truth 继续存在；主路径不出现目标确认。Goal 由系统按 `PD-RULE-004` 维护。仅在明确 user job 下通过 contextual task flow / Disclosure / compatibility deep link 进入。

#### UI-NAV-004 — Chat Is Not Navigation

Chat / Tutor 不得成为 L0 Product Domain。Conversation / Message 是当前 LearningActivity 的 interaction mode。用户侧「对话」是该 Activity 的称呼，侧栏不得做成 Chat thread manager。

#### UI-NAV-005 — User-facing Space Vocabulary

正常 UI 使用“空间”“当前空间”“切换空间”“对话”。`Workspace`、`current_workspace_id`、`LearningActivity` 只在 engineering/diagnostic/audit context 作为主文案出现。Route id 仍是 canonical `workspace_id` / activity id；不得创建第二 space / conversation identity。

#### UI-NAV-006 — New Space and Start-learning Actions

`＋ 新建空间` 是显式创建 Workspace 的 `Action`。打开创建流程是 Navigation 且无业务副作用；只有提交正式 Workspace create command 才可显示成功。

「马上开始学习」是 Action：自动创建 Workspace、把刚上传资料归属该空间、开第一段对话。  
「加入学习空间」是 Action：把已处理资料归属选定或当场新建的空间。  
对空间「继续学习」是 Action：在该空间新开一段对话。

Owner command 不可用时不得用 disabled placeholder、localStorage 或 React object 冒充已创建空间或对话。

---

### 5. Workspace Shell

#### UI-SHELL-001 — Shared Workspace Context

Workspace variant 中：

```text
Left = Where
Center = Learn
Right = Reference / Notes
```

三部分必须解析同一 canonical current Workspace。

#### UI-SHELL-002 — Left / Where

左侧只承担：

- Welcome destination；
- 已有对话列表；
- `＋ 新建空间` Action；
- 学习中的当前空间上下文；
- Library Navigation；
- Utility group。

不得放置常驻 Goal/Plan/Progress/Evidence 管理结构。不得把左侧做成 Chat thread manager。

#### UI-SHELL-003 — Center / Learn

中央区域是唯一 Primary Learning Canvas。进入真实学习后不得同时呈现多个等权 Dashboard 或第二套 Tutor surface。

#### UI-SHELL-004 — Right / Reference & Notes

右栏可隐藏；v1 只允许：

- Learning Notes；
- Current Material / citation source context。

隐藏后必须仍能完成主任务；重新打开时恢复当前可恢复上下文。

#### UI-SHELL-005 — Learning Context Drawer

Drawer 固定在 Composer/输入区域上方，默认收起。

收起：当前阶段 + 接下来的一行方向信息。  
展开：仅 stage / stage goal / next 1..3。

不得加入 Goal editor、完整 Plan、Progress Dashboard、Evidence 管理、mastery / ReviewSchedule / TeachingAction 控制。

---

### 6. Route Contract

#### UI-ROUTE-001 — Stable Destinations

稳定用户侧目的地：

```text
/                       # Welcome，打开 App 的默认目的地
/welcome                # Welcome 的显式 route
/courses/new            # 新建空间；courses 为 legacy route vocabulary
/courses/:workspaceId
/courses/:workspaceId/activities/:activityId
/library
/settings
/settings/recovery
```

兼容 Workspace route 可以提供：

```text
/workspaces/:workspaceId
/workspaces/:workspaceId/learn
/workspaces/:workspaceId/library
```

其中 `:workspaceId` 保持 canonical Workspace identity；`courses` 是 legacy route vocabulary，用户文案是「空间」，不得据此恢复「课程」用词。

具体 router implementation（hash/history/native bridge）不是本合同 Authority。

#### UI-ROUTE-002 — Learning Activity Deep Links

现有 activity/session deep link 可以保留兼容：

```text
/learn/:activityId
/quick/:sessionId
```

但必须进入对应空间 scope 下同一 canonical LearningActivity / dialog facade，不得创建第二 transcript / Attempt / TeachingAction truth。无法证明 Activity 属于目标空间时 fail closed。

#### UI-ROUTE-003 — Legacy Today / Learning Compatibility

`/` 必须进入 Welcome，side-effect-free，不得自动创建或自动进入对话。

`/today`、`/learning` 只作为 compatibility entry，解析到 Welcome，UI/analytics/Sidebar 不再把它们描述为 Product Domain。不得用它们恢复 Today / Learning L0，也不得自动 resume 上一段对话。

#### UI-ROUTE-004 — Contextual Learning Management Routes

以下旧/兼容路径可以在迁移期保留：

```text
/learning/goals/**
/learning/plan
/learning/progress
/learning/history
/goals/**
/path
/evidence
/history
/profile
```

它们不得再构成 Learning 常驻管理 IA。

允许用途：

- explicit goal create / correction / audit；
- plan explanation；
- evidence/progress explanation；
- history recovery / audit；
- bounded compatibility deep link。

#### UI-ROUTE-005 — No-side-effect Navigation

Redirect / route change / facet-like presentation change不得自动：

- 创建 Goal / Activity / Session；
- 修改 focused/persisted business state；
- 写 Evidence；
- 触发 replan；
- 清空未提交工作。

#### UI-ROUTE-006 — Deep-link Preservation

历史 deep link 在 retirement condition 满足前必须可解释地迁移。删除兼容 route 前需有测试证明：

- no business side effect；
- back / reload 行为正确；
- active/resumable learning 不丢失；
- focus 落到新页面语义起点。

---

### 7. Space Entry / Welcome / Creation Contract

#### UI-COURSE-001 — Welcome / Empty State

`/` 与 `/welcome` 显示 Welcome。没有 canonical Workspace 时：

- 明确当前还没有空间；
- 用户可以上传资料，或 `＋ 新建空间`；
- 不生成默认空间、Goal、Plan、对话或示例数据。

有空间或对话时，Welcome 仍是打开 App 的第一屏：侧栏列出已有对话；Welcome 上可选空间并「继续学习」。

#### UI-COURSE-002 — First Learning Flow

服从 `EXP-JOURNEY-001`：

```text
上传资料
→ 系统处理
→ 「加入学习空间」或「马上开始学习」
→ 进入对话，或回到 Welcome
```

不得把「明确 Learning Goal」写成用户步骤。每一步必须表达 LOADING/READY/PARTIAL/ERROR/RECOVERABLE 等真实状态。Workspace create success 只来自 Platform Workspace Registry command result；Material、Activity readiness 分别来自其 owner，不得打包成 frontend fake transaction。未入空间 Material 服从 `WSP-021`：`workspace_id` 可为 null，归属前不得开始有依据的学习。

#### UI-COURSE-005 — Create or Extend Space

服从 `EXP-JOURNEY-004`。`＋ 新建空间` 只创建 Workspace，不自动开对话、不编造资料。空空间必须诚实显示还不能开始有依据的学习。往已有空间加入资料的处理完成弹窗与 `UI-COURSE-002` 相同。

#### UI-COURSE-003 — Space-scoped Landing

`/courses/:workspaceId` 展示当前空间上下文。存在可恢复对话时，打开它们是 Navigation。对空间「继续学习」是 Primary Action，必须新开对话。无对话时显示缺失原因和真实可用的下一步，不生成假对话。

#### UI-COURSE-004 — Existing Conversation List

- Welcome 侧栏可列出可恢复对话；
- 学习中只显示当前空间内 exact LearningActivity refs；
- title 使用学习语义，不使用 Chat 1/2/3；
- current/active state 明确；
- 打开已 active/resumable 对话是 Navigation / InteractiveContent；
- 对空间「继续学习」或启动 available Activity 使用 `StartLearningActivity` Action；
- 切换 presentation 不复制 transcript、Attempt 或 TeachingAction。

#### UI-COURSE-GAP-001 — Technical Command/Query Gate

**CLOSED by ADR-0023 / `CWSP-*`**。Course list/create/current/switch、switch conflict recovery 与 Course-scoped recent/resumable Activity projection 的 owner、strict v1 schema、version、idempotency、error、migration 与 recovery 已冻结。Frontend implementation MUST consume that contract and remains blocked only by XIK-189 platform implementation dependency；不得重新发明 schema/owner。

---

### 8. Space-scoped Learning Contract

#### UI-LEARN-001 — Learning Workspace Under Space

Learning Workspace 位于空间 context 之下，不再由 `/learning` L0 拥有。中央画布服从 `EXP-JOURNEY-003`：用户必须能真实作答，而不是只消费解释。没有可恢复对话时返回 Welcome 或空间 landing；对空间「继续学习」才可新开对话，不得前端自行创建 Session/Goal/Plan。

#### UI-LEARN-002 — Same Activity Across Presentation Changes

空间内的 Learning Workspace、兼容 Tutor、Focus/窄屏 presentation 只允许改变呈现，不得重新生成 canonical Activity / Attempt / TeachingAction / transcript。对空间「继续学习」除外，该 Action 必须创建新的 LearningActivity。

#### UI-LEARN-003 — Required Learning State

中央学习画布必须能够呈现：

- current task / teaching content；
- learner input / Attempt；
- feedback；
- streaming / completed / failed / recoverable state；
- 必要 citation / assistance / validation obligation。

学习消息与具体行为由 `learning-interaction-contracts.md` 管理。

---

### 9. Library Contract

#### UI-LIB-001 — Purpose

Library 让用户管理当前产品支持的 Material、理解来源状态，并进入 material-grounded learning。

#### UI-LIB-002 — Default Hierarchy

默认优先：

```text
Import
Search / Filter
Material list
Selected material context
```

重复 Material 默认 row/list；批量/低频操作只在 selection/context 下出现。

#### UI-LIB-003 — No OCR Exposure in v1 Normal UI

正常 v1 UI 不暴露：

- OCR action；
- OCR engine/status；
- OCR candidate / review / publish；
- OCR confidence/bbox/hash 等实现细节。

扫描 PDF 无可靠文本时显示 `unsupported / partial extraction` 和可行动建议。

#### UI-LIB-004 — Deferred Candidates

大纲、Evidence 管理中心、知识图谱管理 UI、Progress Dashboard、AI Summary、Flashcards、错题本不得建立 placeholder/disabled tab。

若 Product Definition 未来纳入，先更新上游 Product/Experience，再进入 UI Spec。

---

### 10. Settings / Recovery Contract

#### UI-SET-001 — Utility Hierarchy

Settings 使用 category navigation / secondary destination，而不是 giant control grid。

#### UI-SET-002 — Current Product Boundary

不得恢复已退役的 Account/Login/Password/AuthSession UI。

Local data、BYOK、Recovery 的用户行为必须服从 current Product Definition 与 security/data-control contracts。

#### UI-SET-003 — Recovery Presentation

Recovery 不新增 Product Domain。存在 action-required issue 时可显示紧凑全局状态/入口；恢复 action 必须使用 owner 提供的合法 RecoveryAction，不得由 frontend 发明 command。

---

### 11. First-use / Welcome

#### UI-WELCOME-001

`/` 与 `/welcome` 是打开 App 的默认目的地，不是 Today / Dashboard，也不是 L0 Product Domain。

Welcome 承担：上传资料、选择空间并「继续学习」、看到已有对话入口。first-use 只呈现用户必须完成/理解的事实步骤（模型能力、资料、空间、开始学习）；内部 diagnostic/planner/system stage 与 Learning Goal 管理不得成为用户必须学习的工程流程。不再固定跳转 `/today`，也不自动 resume 上一段对话。

#### UI-WELCOME-002

显式 deep link 应尽量保留；Welcome redirect / dismiss 不产生额外业务副作用，也不得依赖 localStorage 冒充 readiness truth。

---

### 12. Responsive / Input Screen Rules

至少验证：

```text
1440×900
1024×768
768×1024
360×800
200% zoom
```

#### UI-RESP-001

窄屏允许：Sidebar → drawer/compact rail；Right Rail → accessible sheet/section；Drawer → compact disclosure/sheet。

语义职责不得改变。

#### UI-RESP-002

页面不得出现阻断任务的横向滚动。公式/代码等局部内容 MAY 自身滚动，但页面整体必须保持可用。

#### UI-RESP-003

避免页面 + conversation + drawer 三层关键嵌套滚动。

#### UI-RESP-004

关键 Navigation、Drawer、Right Rail、Workspace switch、Material tabs 必须有 keyboard/touch 等价路径；关闭 transient surface 后恢复合理 focus。

---

### 13. Forbidden Implementations

禁止：

- Domain object count → navigation count；
- 恢复 Goal/Plan/Progress/History 常驻管理中心；
- 恢复 Today / Learning L0 或用新 Dashboard 替代；
- `/`、`/today` 或 `/learning` 直接退化为无空间归属的 chat-first picker；
- 用 frontend/localStorage 创建或切换 Course/Workspace；
- route change 产生隐藏 business write；
- 用 frontend state 冒充 Workspace/Plan/Evidence/UserNote truth；
- 新增第二 Tutor / transcript；
- 为 deferred capability 建空页面/disabled tab；
- 用 OCR pipeline 复杂度占据 v1 Library；
- 用 Account/Auth UI 反向改变 Local Single-User 产品定义；
- 因窄屏隐藏完成任务所需唯一 citation/error/assistance/validation 信息。

---

### 14. Acceptance Criteria

- `UI-SN-AC-001`：Today / Learning 不再是 L0；Welcome、已有对话、`＋ 新建空间`、Library 与 Utility 语义分组正确；
- `UI-SN-AC-002`：空间无常驻 Goal/Plan/Progress/History 管理导航；
- `UI-SN-AC-003`：Workspace shell 三栏解析同一 current 空间 / Workspace；
- `UI-SN-AC-004`：Welcome、新建空间、加入空间、马上开始学习与对话列表无 fake data/placeholder；
- `UI-SN-AC-005`：`/`、`/today`、`/learning` 与 deep links 无业务副作用且不会创建第二 truth；打开 App 先到 Welcome；
- `UI-SN-AC-006`：Library normal v1 UI 无 OCR 暴露且 deferred candidates 无 placeholder；
- `UI-SN-AC-007`：Settings/Recovery 保持 Utility 语义且无 Account/Auth residue；
- `UI-SN-AC-008`：LOADING/EMPTY/PARTIAL/STALE/ERROR 等不会伪装 READY；
- `UI-SN-AC-009`：1440/1024/768/360 与 200% zoom 下主要用户任务可完成；
- `UI-SN-AC-010`：keyboard/touch/focus/deep-link/back/reload 的关键路径可验证；
- `UI-SN-AC-011`：无静默丢失 draft/stream/note/session/material context；
- `UI-SN-AC-012`：UI Acceptance 不被描述为 Product Acceptance 或 Learning Evidence。
- `UI-SN-AC-013`：用户界面使用“空间”“对话”，但 route/API/domain/persistence 仍解析同一 Workspace / LearningActivity identity。
- `UI-SN-AC-014`：空间切换改变真实 scope，并在 draft/stream/note/session/material 冲突时使用 owner-defined recovery。
- `UI-SN-AC-015`：一个空间下多段对话可恢复；点已有对话不新开；对空间「继续学习」新开对话；Conversation 不成为 thread manager。

---

## Askora UI Data and Query Specification

> Spec ID：`UI-DATA-*`
> 状态：`FROZEN`
> 依赖：`DOMAIN-*`、`STATE-*`、`DEP-*`、`API-*`、`SCHEMA-*`

### 1. 原则

#### UI-DATA-001 — UI Is Not an Owner

UI、frontend store、API handler 与 UI read-model assembler 均不是新的业务状态 owner。它们只可读取、组合和呈现 owner 已发布的 exact-version state 或明确标记的 compatibility projection。

#### UI-DATA-002 — Query Composition Does Not Change Ownership

面向页面的聚合 Query MAY 组合 SYS01、SYS03、SYS05、SYS06、SYS07、SYS08 的只读投影，但每个字段必须保留 `source_system`、version/ref、availability/freshness。聚合 response 不得成为第二 LearningPlan、LearnerState、TeachingAction 或 ReviewSchedule truth。

#### UI-DATA-003 — No Frontend Domain Inference

前端 MUST NOT：

- 从 score/session/message 推导 mastery；
- 从 `next_due_at` 推导已进入今日计划；
- 从章节顺序推导 prerequisite；
- 从 RichMessage card 推导 TeachingAction/assistance；
- 从聊天轮数或持续时间推导进度/学习效果；
- 用固定 threshold 生成 canonical product label。

#### UI-DATA-004 — Missing and Source Semantics

跨系统 UI 字段 SHOULD 使用：

```yaml
value: any|null
availability: AVAILABLE|MISSING|STALE|LOW_CONFIDENCE|NOT_APPLICABLE
source_system: SYS01|SYS02|SYS03|SYS04|SYS05|SYS06|SYS07|SYS08|LEGACY_COMPATIBILITY
source_ref: versioned_ref|null
observed_at: datetime|null
```

`MISSING` MUST NOT 转换为 0、空字符串、false 或空进度条。

### 2. 当前接口分类

#### UI-DATA-010 — Existing and Reusable

| 能力 | 当前接口 | UI 用途 | 限制 |
|---|---|---|---|
| 会话与消息 | `/api/v1/dialog/**` | 导师工作台、历史记录 | session 中部分字段仍为 legacy compatibility |
| 富文本回答 | `message.render_payload` | Markdown/math/cards/citations | 必须继续保留 `content` fallback |
| 学习画像 | `/api/v1/users/profile` | 学习证据迁移入口 | 仅 `profile.mastery` 为 canonical SYS03；其余多为 legacy |
| 文档 | `/api/v1/documents/**` | 资料库列表、上传、状态 | 当前不等于 canonical KnowledgeUnit map query |
| 本地运行状态 | `/health/config` | 设置 | 只返回 mode/ready 与 sanitized provider/model/source/revision；不返回 credential |

#### UI-DATA-013 — Desktop Model Settings Bridge

Electron preload 只暴露版本化窄 bridge：`getModelSettings()`、`applyModelSettings(ModelConfigApplyCommandV1)`、`clearModelSettings(ModelConfigClearCommandV1)`。成功 response 的 `settings` MUST 直接复用 `MODEL-CONFIG-010`，不得定义第二套 UI truth：

```yaml
schema_version: "1.0"
state: ACTIVE|DISABLED|EXTERNAL_READ_ONLY|UNCONFIGURED|DEGRADED
provider: string|null
model: string|null
source: DESKTOP_VAULT|EXTERNAL_ENVIRONMENT|NONE
revision: integer|null
verified_at: datetime|null
runtime_ready: boolean
runtime_revision: integer|null
reason_codes: [string]
```

bridge 使用 strict envelope：成功为 `{ok: true, settings: ModelRouteProfileSummaryV1}`；失败为 `{ok: false, error: StableError, rollback_succeeded?: boolean, settings?: ModelRouteProfileSummaryV1}`。`APPLYING / APPLY_FAILED_RESTORED / ROLLBACK_FAILED` 是 renderer transaction display state，不得写回或伪装成 SYS08 profile state。

```yaml
ModelConfigApplyCommandV1:
  schema_version: "1.0"
  provider: qwen|deepseek|doubao|zhipu
  model: string
  api_key: string
  expected_revision: integer|null

ModelConfigClearCommandV1:
  schema_version: "1.0"
  expected_revision: integer|null
  recovery_confirmation: "RESET_UNREADABLE_VAULT"  # 仅显式不可读 vault 恢复时存在
```

bridge response、frontend store、DOM、analytics 与普通 HTTP client MUST NOT 包含 credential/ciphertext/control token。candidate credential 只在用户提交时从当前表单传给 Electron main，不得写 localStorage/sessionStorage/indexedDB。

#### UI-DATA-011 — Frozen Additive Query Plan

以下 read-only endpoints 已冻结，并按 Vertical Slice 串行实现：

| Endpoint | Slice | 当前实施状态 |
|---|---|---|
| `GET /api/v1/workspace/today` | UI-01 | REQUIRED |
| `GET /api/v1/workspace/activities/{activity_id}` | future activity-link slice | DEFERRED_BY_ACTIVITY_LINK_CONTRACT |
| `GET /api/v1/workspace/library` | UI-02A | REQUIRED |
| `GET /api/v1/workspace/knowledge-map` | UI-02A | REQUIRED |
| `GET /api/v1/workspace/goals` | UI-02B / EXEC-029 | IMPLEMENTED |
| `GET /api/v1/workspace/path` | UI-02B / EXEC-029 | IMPLEMENTED |
| `GET /api/v1/workspace/evidence` | UI-02B / EXEC-029 | IMPLEMENTED |

这些 endpoint MUST 由 application/query layer 调用 owner query ports；API handler 只做 auth、validation、serialization 与 error mapping。

#### UI-DATA-012 — Commands Remain Out of Scope Except Frozen Additive Slices

本基础 Spec Set 不新增：

```text
Create/Confirm/Pause/Resume LearningGoal
Reorder/Edit/Replan LearningPlan
SetNextReviewAt
SetMastery / EditEvidence
SetTeachingAction / SetHintLevel
StartLearningActivity canonical command
```

现有 dialog/document/auth commands 可继续使用。UI-02B1 通过独立冻结 Slice 复用 SPEC-D06 已实现的单资料 Goal/diagnostic/plan/activity/teaching commands，并冻结 learner-visible diagnostic payload；这不授权完整 Goal/Plan 编辑或 durable activity/session link。未来其他 goal/activity command 仍必须单独冻结公共 schema、idempotency、version conflict 与 ownership contract。

UI-02C 通过 ADR-0007、`SYS06 Activity Lifecycle and Completion` 与独立 Vertical Slice 单独
冻结 `StartLearningActivityV1`、`CompleteLearningActivityV1` 和 activity query。该授权仅在
EXEC-030 dependency gate 满足后生效，不扩大 Goal/Plan/mastery 编辑范围。

P1-03 通过 ADR-0103 与 `interfaces/data-control-contract.md` 单独冻结 data-control status、export、erasure preview/confirm/report 以及 desktop typed backup/verify/restore IPC。该协调层不成为 UI 或第九业务 state owner。

#### UI-DATA-013 — DataControlStatusV1

```yaml
schema_version: "1.0"
protection_state: NOT_PROTECTED|READY|IN_PROGRESS|PARTIAL|ERROR|UNSUPPORTED
supported_mode: PRIVATE_DESKTOP_SQLITE|UNSUPPORTED
last_verified:
  backup_id: uuid|null
  reason: string|null
  created_at: datetime|null
  verified_at: datetime|null
  size_bytes: integer|null
automatic_backup:
  enabled: boolean
  next_due_at: datetime|null
  last_error_code: string|null
erasure_checkpoint: integer
reason_codes: [string]
```

Frontend 不得把文件存在推断为 VERIFIED，也不得缓存 Recovery Key、confirmation token 或 restore success 作为 canonical status。

### 3. Common Response Envelope

#### UI-DATA-020

所有新 workspace query 使用 additive v1 envelope：

```yaml
schema_version: "1.0"
generated_at: datetime
data: object|null
source_status:
  - source_system: string
    availability: AVAILABLE|MISSING|STALE|LOW_CONFIDENCE|NOT_APPLICABLE
    source_ref: versioned_ref|null
    reason_codes: [string]
correlation_id: string
```

未知 major version MUST 明确拒绝或进入安全页面级 fallback；不得猜测字段语义。

#### UI-DATA-023 — Model Settings Revision Conflict

apply/clear 必须携带最后读取的 `expectedRevision`。`MODEL_CONFIG_REVISION_CONFLICT` 时 UI 重新读取脱敏状态并要求用户确认，不得自动覆盖较新配置。

#### UI-DATA-021 — Partial Success

若一个聚合 Query 的非关键 owner source 失败，response MAY 返回 `data` 的可用部分及 `source_status`。若主实体（例如 requested activity）不存在或无权限，必须返回 stable error，而不是 `200 + empty`。

#### UI-DATA-022 — Stable Ordering

Activity、goal、evidence 和 node 列表必须有服务端定义的稳定排序与 tie-break。前端 MAY 做 presentation-only filter/sort，但不得把本地顺序保存为 canonical plan/map truth。

### 4. TodayWorkspaceViewV1

#### UI-DATA-030 — Contract

```yaml
today_workspace:
  local_date: YYYY-MM-DD
  timezone: string
  active_goal:
    goal_ref: versioned_ref
    title: string
    status: string
    target_capabilities: [string]
  current_activity:
    activity_ref: versioned_ref
    objective_ref: versioned_ref
    type: string
    title: string
    estimated_duration_minutes: integer|null
    reason_codes: [string]
    status: string
    launch_state: ACTIVE|RESUMABLE|REQUIRES_START_COMMAND|UNAVAILABLE
  planned_activities:
    - activity_ref: versioned_ref
      objective_ref: versioned_ref
      type: string
      title: string
      estimated_duration_minutes: integer|null
      reason_codes: [string]
      status: string
  review_due_candidates:
    - knowledge_unit_ref: versioned_ref
      schedule_ref: versioned_ref
      next_due_at: datetime|null
      review_priority: float|null
      evidence_quality: float|null
      included_activity_ref: versioned_ref|null
  current_evidence_summary:
    knowledge_unit_ref: versioned_ref|null
    confidence: float|null
    independent_success_count: integer|null
    delayed_recall_evidence_count: integer|null
    transfer_evidence_count: integer|null
    validation_obligation: NONE|INDEPENDENT_VALIDATION_REQUIRED|UNKNOWN
  compatibility_quick_start:
    source_label: LEGACY_COMPATIBILITY
    recent_sessions:
      - session_id: uuid
        title: string|null
        subject: string
        knowledge_point_id: string|null
        status: active|ended|archived
        updated_at: datetime
```

#### UI-DATA-031 — Ownership

- goal/objective/activity/plan inclusion → SYS06；
- review candidate / next_due_at → SYS07；
- evidence counts/confidence → SYS03；
- validation obligation → SYS05。

Query assembler MUST NOT locally decide activity priority, review inclusion or validation completion.

#### UI-DATA-032 — Local Date

今日视图 MAY 使用用户时区分组展示，但 canonical timestamps 保持 timezone-aware。客户端日期变化不得自动创建新 plan/version。

### 5. Goal and Path Views

#### UI-DATA-040 — GoalListViewV1

```yaml
goals:
  - goal_ref: versioned_ref
    title: string
    topic: string
    target_capabilities: [string]
    success_criteria: [string]
    deadline_at: datetime|null
    weekly_time_budget_minutes: integer|null
    status: string
    confirmed_by_user: boolean
```

只返回当前授权用户的数据。历史 version MAY 通过独立 detail query 后续补充，不在首个 query 强制范围。

#### UI-DATA-041 — LearningPathViewV1

```yaml
learning_path:
  plan_ref: versioned_ref
  goal_ref: versioned_ref
  status: active|superseded|completed|paused
  created_from_learner_state_version: integer
  knowledge_graph_version: string
  review_schedule_version: string|null
  assumptions: object
  reason_codes: [string]
  objectives:
    - objective_ref: versioned_ref
      capability: string|null
      cognitive_process: string|null
      status: string|null
      activity_refs: [versioned_ref]
      reason_codes: [string]
  activities:
    - activity_ref: versioned_ref
      objective_ref: versioned_ref
      type: string
      title: string
      estimated_duration_minutes: integer
      priority: float
      reason_codes: [string]
      status: string
```

前端不得根据 priority 重新排序并称为 canonical plan；服务端 response order 是展示基线。

#### UI-DATA-042 — Path Scope and Missing Objective Metadata

`GET /workspace/path` MAY 接受 `goal_id` scope。未提供 scope 时：零个 current plan 返回 EMPTY；
恰好一个可返回该 plan；多个 current plan MUST 返回
`MULTIPLE_CURRENT_PLANS_REQUIRE_GOAL_SCOPE`，不得以创建时间、priority 或前端选择
隐式定义业务上的唯一 current plan。

当前 SYS06 未发布 durable LearningObjective metadata stream。Query MUST 保留 exact objective ref，
并将 capability/cognitive_process/status 返回为 null，附
`OBJECTIVE_METADATA_UNAVAILABLE`。不得从 Goal title、Activity type、KnowledgeUnit 或 legacy
字段推断。未来 SYS06 发布 versioned Objective 时 MAY additive 填充这些 nullable 字段。

### 6. ActivityWorkspaceViewV1

#### UI-DATA-050 — Contract

```yaml
activity_workspace:
  activity_ref: versioned_ref
  objective_ref: versioned_ref
  plan_ref: versioned_ref
  title: string
  activity_type: string
  status: string
  session_ref: versioned_ref|null
  teaching_action:
    action_ref: versioned_ref|null
    strategy_family: string|null
    teaching_stage: string|null
    scaffold_control: NONE|LOW|MEDIUM|HIGH|null
    hint_specificity: NONE|ORIENTATION|CONCEPTUAL_STRATEGIC|SUBGOAL|PARTIAL_STEP|BOTTOM_OUT|null
    answer_exposure: NONE|PARTIAL|COMPLETE|null
    validation_obligation: NONE|INDEPENDENT_VALIDATION_REQUIRED|UNKNOWN
    reason_codes: [string]
  actual_assistance:
    assistance_state: INDEPENDENT|ASSISTED|ANSWER_EXPOSED|null
    scaffold_control: string|null
    hint_specificity: string|null
    answer_exposure: string|null
    source_ref: versioned_ref|null
  evidence_sources:
    - label: string
      source_span_id: uuid
      document_id: uuid|null
      locator: object|null
```

#### UI-DATA-051 — Planned vs Actual

`teaching_action` 表示 allowed/planned envelope；`actual_assistance` 表示已经发生的实际体验。UI 必须明确区分，缺 actual data 时不得复制 planned envelope 作为事实。

#### UI-DATA-052 — Session Link

在 canonical activity launch command 未冻结前，`session_ref` MAY 为 null：

- `ACTIVE` / `RESUMABLE` MUST 携带可打开的 canonical `session_ref`；
- `REQUIRES_START_COMMAND` 表示 activity 已存在，但当前 Spec Set 不授权启动；
- `UNAVAILABLE` 必须带稳定 reason code；
- UI 不得通过创建 legacy session 自动写回虚构 activity/session link；
- 兼容入口产生的 session 必须标记来源，且不得改变该 activity 的 `launch_state`。

### 7. LibraryViewV1 / KnowledgeMapViewV1

#### UI-DATA-059 — Library Contract

```yaml
library:
  view_state: READY|PARTIAL|STALE|EMPTY
  total: integer
  page: integer
  page_size: integer
  documents:
    - document_ref: versioned_ref
      document_id: uuid
      title: string
      media_type: string
      file_size_bytes: integer
      subject: string|null
      processing_status: pending|processing|completed|failed|rejected|quarantined
      moderation_status: pending|approved|requires_review|rejected
      current_revision_ref: versioned_ref|null
      knowledge_status: NOT_MODELED|CANDIDATES|PUBLISHED|LEGACY_COMPATIBILITY
      knowledge_unit_count: integer
      relation_count: integer
      reason_codes: [string]
      created_at: datetime
      updated_at: datetime
```

Library response MUST NOT 返回 storage path、raw parser/security details 或完整本地文件内容。

#### UI-DATA-060 — Contract

```yaml
knowledge_map:
  scope:
    document_refs: [versioned_ref]
    subject: string|null
    graph_version: string
  nodes:
    - knowledge_unit_ref: versioned_ref
      kind: string
      canonical_name: string
      description: string
      provenance_type: string
      confidence: float|null
      status: candidate|verified|published|rejected|superseded
      evidence_span_refs: [versioned_ref]
      learner_evidence_summary: object|null
  edges:
    - relation_ref: versioned_ref
      prerequisite_ref: versioned_ref
      target_ref: versioned_ref
      strength: hard|soft|contextual
      confidence: float|null
      status: candidate|published|rejected|superseded
      evidence_span_refs: [versioned_ref]
  source_spans:
    - source_span_ref: versioned_ref
      source_span_id: uuid
      document_id: uuid
      page: integer|null
      chapter: string|null
      start_offset: integer|null
      end_offset: integer|null
      excerpt: string
```

#### UI-DATA-061 — Query Source

Node/relation truth 来自 SYS01；learner evidence summary 来自 SYS03，只读拼接。Map response MUST NOT 把 learner evidence 写回 node，或把 node status 当 learner mastery。

#### UI-DATA-062 — Pagination / Scope

Knowledge map query MUST 要求明确 scope，并对 node/edge 数量设置上限或分页。前端不得默认加载所有文档和全部图谱到一个 canvas。

UI-02A 首个实现 MUST 使用单一 `document_id` scope，默认上限 nodes 100、edges 200、source spans 300。`minimal-binding-v1` 必须标为 compatibility/pending rebuild；不得以文件名节点伪装 mature published map。无可靠 relation 时返回空 edges 与 reason code，不得从章节顺序推断 prerequisite。

### 8. EvidenceProfileViewV1

#### UI-DATA-070 — Contract

```yaml
evidence_profile:
  knowledge_units_assessed: integer
  entries:
    - knowledge_unit_ref: versioned_ref
      label: string|null
      competence_probability: float|null
      confidence: float|null
      independent_success_count: integer|null
      delayed_recall_evidence_count: integer|null
      transfer_evidence_count: integer|null
      evidence_count: integer|null
      effective_evidence_weight: float|null
      active_misconception_ids: [uuid]|null
      algorithm_id: string|null
      algorithm_version: string|null
      product_label: string|null
      product_label_rule_version: string|null
  legacy_compatibility:
    visible_by_default: false
    fields: object
    source_label: LEGACY_COMPATIBILITY
```

#### UI-DATA-071 — Product Label Gate

`product_label` 只有在 SYS03 canonical query 返回稳定 label 与 rule version 时才可非 null。UI/API assembler MUST NOT 从 `competence_probability` 自行派生。

#### UI-DATA-072 — Current `/users/profile` Migration

首个实现 MAY 直接消费当前 `profile.mastery.entries` 作为 canonical source，并忽略 legacy fields。新增 `/workspace/evidence` SHOULD 提供 KnowledgeUnit label/ref 与统一 availability/source semantics；切换完成后旧 profile learning aggregates 有明确 retirement condition。

### 9. Security, Privacy and Caching

#### UI-DATA-080

所有 workspace query 必须绑定当前授权用户。Knowledge/document query 也必须执行 resource ownership；仅凭 object id 不得跨用户读取。

#### UI-DATA-081

响应不得包含密码、token、API key、内部 Prompt、grader-only answer、未经授权的全文文档或本地绝对路径。

#### UI-DATA-082

Frontend cache 只能是可失效 read cache。resource deletion 或 schema major change 时必须清除相关缓存。Local storage 不得成为 LearningPlan/LearnerState/ReviewSchedule truth。

#### UI-DATA-083

含个人学习数据的 Query 默认不得被共享代理缓存；transport cache policy 与 Electron 本地 cache 必须遵循当前 local privacy mode。

### 10. Errors

#### UI-DATA-090

除既有 stable error code 外，workspace query 如需新增 code，正式 API Spec 至少应覆盖：

```text
WORKSPACE_SOURCE_PARTIAL
WORKSPACE_ACTIVITY_NOT_FOUND
WORKSPACE_PLAN_NOT_AVAILABLE
WORKSPACE_KNOWLEDGE_SCOPE_REQUIRED
WORKSPACE_SCHEMA_UNSUPPORTED
```

对应 endpoint 进入实现前必须复核这些 code 是否应复用现有 `PLAN_NO_FEASIBLE_ACTIVITY`、`SCHEMA_VERSION_UNSUPPORTED` 等稳定语义，避免重复错误协议。

### 11. UX Architecture Data and Query Contracts (ADR-0018)

本节冻结 `UX-Architecture-Canonical-Design-Delta.md` 经 `ADR-0018` 吸收后的数据/查询边界。前端不得推断 domain truth；所有字段保留 `source_system`、version/ref、availability/freshness。ADR-0019 已关闭 current Workspace 与 Drawer query 的 owner/API gap；对应 strict v1 read projection 不新增 state writer。

#### 11.1 Workspace Query Boundaries

#### UXA-DATA-200 — Workspace List / Current Query

ADR-0023 / `CWSP-*` closes the prior multi-Course gap。`GET /api/v1/workspaces` 从 Platform Workspace Registry 返回 strict `WorkspaceListResponseV1`；`GET /api/v1/workspaces/current` 返回同一 versioned selection/current item。每个 Workspace 项至少携带：

```yaml
workspace_ref: versioned_ref
workspace_id: uuid
name: string
version: integer
status: READY|PARTIAL|STALE|ERROR
```

current Workspace 由服务端 versioned `WorkspaceSelection` 解析，返回 selection version/ref、`source_system` 与 `source_ref`。前端 MUST NOT 用 route/subject/session/localStorage/`is_default` 当作 Workspace truth。`MISSING` 不得转换为空 Workspace 或"默认 Workspace"。

fresh LocalOwner 可合法返回真实 `EMPTY`（0 Workspace/0 selection），且 query 不得 bootstrap。`GET /api/v1/workspace/context` 在迁移期只是 current-selection compatibility adapter；旧 `SINGLE_WORKSPACE` 不再是目标能力合同。

#### UXA-DATA-201 — Workspace Switch Query / Command

Workspace 切换是用户显式 Action。前端调用 `SwitchWorkspaceV1`，携带 expected selection version、idempotency key 与真实 `WorkspaceTransitionGuardV1`；只有 Platform Workspace Registry `WorkspaceMutationResultV1` 可确认成功。前端不得 PATCH Workspace、切换 `is_default` 或写本地 state 冒充。

切换结果的持久化状态 MUST 来自 canonical response，前端只呈现 `saving / switched / failed / recoverable`。stale version 必须 re-query并要求重新确认，不得 blind overwrite。

#### UXA-DATA-202 — Workspace Switch Conflict / Recovery

切换遇：未提交 draft、streaming run、未持久化/conflict note、open Material tabs/position、active LearningSession 时，MUST 使用 `CWSP-023/026/027/032` 返回可恢复状态与显式呈现。前端不得静默丢弃、固定伪报 `CLEAR` 或将 browser memory称为 durable save。active Session/Activity 保留在 source Course；switch不自动 end/cancel/complete。

#### UXA-DATA-203 — Course Activity Index

`GET /api/v1/workspaces/{workspace_id}/activities` 返回 strict `WorkspaceActivityIndexResponseV1`。items保留 exact Workspace/Goal/Plan/Activity/latest lifecycle refs与稳定 title catalog source；active 可 Navigation resume，available 只能触发 SYS06 `StartLearningActivityV1`。前端不得从 Conversation title、chat recency、route或 local state推断 Activity/current/resume。

#### 11.2 UserNote Durable Object

#### UXA-DATA-210 — UserNote Scope / Anchor / Version

UserNote 是 user-authored durable object，MUST 是 Workspace-scoped 且 anchored（绑到当前阶段/内容/材料位置）。每条笔记至少携带：

```yaml
note_ref: versioned_ref
note_id: uuid
workspace_id: uuid
anchor:
  kind: STAGE|SOURCE_SPAN|MATERIAL|FREE
  ref: versioned_ref|null
version: integer
```

UserNote owner 已由 ADR-0021 / `UNSI-*` 冻结为 Platform Workspace Notes。Frontend只可调用 strict owner query/save/recovery command；不得 create 全局 note、写 localStorage事实源或在 Workspace switch guard 中把未接受的 autosave冒充 `SAVED`。

#### UXA-DATA-211 — Autosave / Conflict / Recovery

- autosave 提交使用 version/expected_revision 边界；`CONFLICT` 时要求用户确认，不得静默覆盖较新笔记；
- 保存状态区分 `SAVING / SAVED / FAILED / CONFLICT / RECOVERABLE`；
- 未持久化时不得显示"已保存"；浏览器内存不构成 durable recovery。

#### 11.3 Learning Context Drawer Query

#### UXA-DATA-220 — Drawer Query

Drawer 内容来自 canonical/versioned query，返回：

```yaml
stage_ref: versioned_ref|null
stage_name: string|null
stage_goal: string|null
next_directions:   # 1..3
  - kind: KNOWLEDGE_POINT|TEACHING_DIRECTION
    ref: versioned_ref|null
    label: string|null
```

Transport contract 为 `GET /api/v1/workspace/learning-context?activity_id=<optional UUID>`，response 使用 strict `schema_version=1.0`、`generated_at`、`correlation_id`、`data.view_state` 与 `source_status` envelope。

#### UXA-DATA-221 — Provenance / Version

stage / stage goal / next direction 必须有 `source_system` 与 `source_ref`。前端 MUST NOT 从 chat 文本、heading 顺序或 probability threshold 推断 next knowledge point；LLM 输出不得作为 canonical next knowledge point。

- stage：exact SYS05 `TeachingAction` ref；
- stage goal：同一 TeachingAction ref + versioned server presentation catalog；
- next direction：exact ordered SYS06 `LearningActivity` ref；
- query assembler 只组合，不取得 SYS05/SYS06 writer ownership。

#### UXA-DATA-222 — MISSING / PARTIAL / STALE

Drawer query MUST 能表达：

```text
MISSING
PARTIAL
STALE
```

`MISSING` 不得转换为假 stage / "无内容"；`PARTIAL`/`STALE` 不得显示为 READY。

#### UXA-DATA-223 — Query Freshness and Failure

- 无 current activity/direction → `MISSING`；
- 有 SYS06 direction、尚无 exact SYS05 TeachingAction → `PARTIAL`；
- action/activity version 非 current 或 activity 已 completed/superseded → `STALE`；
- exact SYS05 stage + 至少一项 exact SYS06 direction → `READY`；
- transport/dependency failure → frontend `ERROR`，不得白屏或阻断 composer。

Query MUST side-effect free、current Workspace scoped、no LLM call、no transcript parsing、no database write。

#### 11.4 Current Material / SourceSpan

#### UXA-DATA-230 — Current Material Tabs Query

Current Material tab 打开来自 citation / "view source" 的当前 Workspace 资料。tab 内容 MUST 来自 canonical current-Workspace refs：

```yaml
material_ref: versioned_ref
document_id: uuid
source_span_ref: versioned_ref|null
locator: object|null
```

#### UXA-DATA-231 — Cross-Workspace Fail-closed

跨 Workspace 引用 MUST fail closed，不泄露外部对象是否存在。缺失 SourceSpan 显示不可用状态，不得伪造 summary 或用 filename-as-original。

#### 11.5 Right-rail Presentation Boundary

#### UXA-DATA-240 — Presentation vs Canonical Data

右栏 tab 顺序、打开/关闭、右栏可见性、Drawer 展开态均为 presentation state，可本地保存。canonical data（笔记内容、材料、SourceSpan、stage/goal/next）必须来自 owner query。前端本地 state 不得成为第二 truth。

#### 11.6 State Matrix

适用于 UXA 引入的加载区域。`—` 表示该区域不适用，不得机械添加。

| 区域 | LOADING | EMPTY | READY | PARTIAL | STALE | ERROR | UNAUTHORIZED | CONFLICT | SAVING | SAVED | RECOVERABLE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Workspace list/current | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | — | — | — |
| Workspace switch | ✓ | — | ✓ | — | — | ✓ | ✓ | — | ✓ | ✓ | ✓ |
| Course Activity index | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | — | — | — |
| Context Drawer | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | — | — | — | — |
| Notes | — | ✓ | ✓ | — | — | ✓ | — | ✓ | ✓ | ✓ | ✓ |
| Material tabs | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | — | — | — |
| Library scanned-PDF | ✓ | — | ✓ | ✓ | — | ✓ | — | — | — | — | — |
| Route compatibility | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | — | — | — |

#### 11.7 Acceptance Criteria

- `UXA-DATA-AC-001`：Workspace current/list 来自 canonical query，前端不冒充 Workspace truth；
- `UXA-DATA-AC-002`：Workspace switch 不静默丢弃 draft/stream/note/session/material；
- `UXA-DATA-AC-003`：UserNote 为 Workspace-scoped、anchored、versioned durable object，冲突需确认；
- `UXA-DATA-AC-004`：Drawer 内容来自 canonical/versioned query，前端不推断 next；
- `UXA-DATA-AC-005`：MISSING/PARTIAL/STALE 不被转成 0/READY；
- `UXA-DATA-AC-006`：Current Material / SourceSpan 为 canonical Workspace refs，跨 Workspace fail closed；
- `UXA-DATA-AC-007`：右栏/Drawer presentation state 与 canonical data 边界清晰；
- `UXA-DATA-AC-008`：Workspace switch 必须使用 ADR-0023 owner command；UserNote必须使用 ADR-0021 / `UNSI-*` owner receipt，不以前端 mock 绕过。
- `UXA-DATA-AC-009`：Workspace create/current/switch 只接受 ADR-0023 Platform owner result；fresh EMPTY 不被隐式 bootstrap。
- `UXA-DATA-AC-010`：Course Activity index exact SYS06-derived、稳定排序、side-effect free；available 不被 Navigation 自动 start。

### 12. Acceptance Criteria

- `UI-DATA-AC-001`：每个聚合字段可追踪 owner/system 与 exact ref/version 或明确 compatibility source。
- `UI-DATA-AC-002`：MISSING/STALE/LOW_CONFIDENCE 不被前端转成 0 或 READY。
- `UI-DATA-AC-003`：today query 不把 ReviewDue candidate 自动变成计划活动。
- `UI-DATA-AC-004`：activity query 分离 planned envelope 与 actual assistance。
- `UI-DATA-AC-005`：knowledge map 不合并 KnowledgeUnit truth 与 learner evidence truth。
- `UI-DATA-AC-006`：evidence query 不从 probability 派生无版本 mastery label。
- `UI-DATA-AC-007`：API handler 不含 planner、review、mastery、policy 或 knowledge algorithm。
- `UI-DATA-AC-008`：LocalOwner 切换后 frontend cache 不泄漏上一 owner 学习数据。
- `UI-DATA-AC-009`：未冻结的新 commands 不会以假按钮或 frontend-only state 出现。
- `UI-DATA-AC-010`：只有 ACTIVE/RESUMABLE activity 才携带可进入工作台的 canonical session link。
- `UI-DATA-AC-011`：data-control status 来自 catalog/report exact refs；frontend 不自行判断 backup integrity 或 erasure completion。

### 12. Forbidden Implementations

禁止：

- 新建 `workspace_state` JSON 作为多个 owner 的第二事实源；
- API 为页面方便直接 join ORM 后重新判断业务语义；
- 在前端复制 planner/review/policy thresholds；
- 把 `/users/profile` legacy 字段改名后伪装成 canonical；
- 为知识地图读取 vector index/graph projection 后当作唯一 truth；
- 用 current mutable state 补齐历史 plan/action/evidence refs；
- 为了 UI 完整直接开放未定义的 SetMastery/SetNextReviewAt/SetTeachingAction。

### 13. OnboardingJourneyViewV1

#### UI-DATA-100

`GET /api/v1/onboarding/journey` MUST 复用 `ONBOARD-*` strict view。前端只呈现四个 steps 与一个
`next_action`，不得依据 owner arrays、localStorage、message、duration 或 model result 重算完成、排序
业务对象或生成恢复动作。

#### UI-DATA-101

Preference 与 journey cache 必须 current-user scoped 且可失效；logout/switch/dismiss/reopen/owner
mutation 后重查。MISSING/STALE/PARTIAL 不得转换为 false/READY；dismissed 不得转换为 completed。
