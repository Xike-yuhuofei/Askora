# Askora Interactive Element System Specification

> Spec ID：`UI-IES-*`  
> 状态：`FROZEN`  
> Governing：`ADR-0014`、`IES-CD-001..018`  
> Scope：semantic interaction primitives、interaction hierarchy、pattern qualification、cross-platform mapping

## 1. Governing Principle

### UI-IES-001 — Design Derivation Order

所有新增或重构交互 MUST 按以下顺序证明合理性：

```text
User Job
→ Domain Meaning
→ Information Architecture
→ Interaction Semantics
→ Interaction Pattern
→ Visual Component
```

实现 PR/EXEC 不得以“已有 Card/Button/Page”作为新增交互的主要理由。

### UI-IES-002 — Domain Object Is Not Interaction

`LearningGoal`、`LearningPlan`、`LearningActivity`、`Document`、`Evidence`、`ReviewSchedule` 等 domain object 不自动成为：

- page；
- entry；
- navigation item；
- button；
- card。

必须先定义用户 intent。

## 2. Canonical Semantic Primitives

Askora 只允许以下 7 类顶层 semantic interaction primitives：

```text
Navigation
Action
Control
Selection
Disclosure
InteractiveContent
StatusFeedback
```

### UI-IES-010 — Navigation

改变用户当前所处的信息空间，不直接执行业务 command。

允许：

- global destination；
- local facet；
- back；
- object detail navigation。

禁止：

- 用 Navigation 伪装 create/delete/start command；
- route change 同时产生业务写入；
- 把普通 status 当 navigation。

### UI-IES-011 — Action

执行明确 command 或产生可观察副作用。

例如：

- 开始学习；
- 创建目标；
- 导入资料；
- 删除；
- 导出；
- 重试 owner command。

Action 必须有：

- 可预测结果；
- pending/disabled/error state（适用时）；
- destructive confirmation（适用时）；
- idempotency/version boundary（由后端合同要求时）。

### UI-IES-012 — Control

修改当前对象、presentation preference 或 App preference 的值。

例如 Toggle、Slider、editable preference field。

Control 不得直接冒充 navigation destination。

### UI-IES-013 — Selection

从明确候选集合选择一个或多个值。

例如：

- focused goal picker；
- provider/model picker；
- document multi-selection。

Selection 与业务 command 分离：选择本身不等于提交，除非后端/产品合同明确采用 immediate apply。

### UI-IES-014 — Disclosure

显示或隐藏附加信息，不改变用户核心任务空间。

例如：

- Inspector；
- disclosure group；
- technical details；
- citation details。

关键任务唯一信息、安全错误、validation obligation 不得只存在于默认不可发现的 disclosure 中。

### UI-IES-015 — InteractiveContent

Domain content 本身作为可选择/打开对象。

例如：

- document row；
- goal row；
- activity row；
- history row。

默认使用 row/list，而不是为每个对象建立 Card。

### UI-IES-016 — StatusFeedback

表达状态、进度、结果、加载、错误、置信度或系统反馈。

StatusFeedback 默认不应可点击。若需要进入解释页面，应把可点击行为建模为独立 Navigation/Disclosure，并保持视觉 affordance 明确。

## 3. Non-primitive Vocabulary

### UI-IES-020 — Entry

`Entry` 只作为分析/组合术语，不属于 canonical primitive。

任何 Entry 必须最终落到：

```text
Navigation | Action | InteractiveContent
```

禁止把 Entry 作为工程组件 semantic type 长期扩张。

### UI-IES-021 — Contextual Action

Contextual Action 定义为：

```text
Action + Contextual Visibility/Availability Rule
```

不新增第八类 primitive。

### UI-IES-022 — Presentation Patterns

以下均为 pattern/component，不是 semantic role：

```text
Button
Card
Row
List
Toolbar
Menu Item
Context Menu
Shortcut
Popover
Sheet
Modal
Inspector
Tab
Sidebar Item
```

组件 API SHOULD 显式接受 intent/role，而不是通过视觉 variant 推断 semantic role。

## 4. Interaction Hierarchy

### UI-IES-030 — L0 Product Domain Navigation

只允许：

```text
今天
学习
资料库
```

Settings / Recovery / Search 属于 App Utility，不计入 L0 Product Domains。

### UI-IES-031 — L1 Domain Facet

Learning domain 的 canonical facets：

```text
目标
路径
进展
历史
```

其他页面新增 L1 facet 必须证明存在稳定、重复的 user job，不得因后端新增 read model 自动增加。

### UI-IES-032 — L2 Primary Task / Action

每个主任务区域 SHOULD 只有一个 Primary Action。

若存在两个同等 primary intent，必须先重新审查 user job / task boundary；不得仅通过并列蓝色按钮解决。

### UI-IES-033 — L3 Secondary Action

支持主任务但非完成主任务必要的动作使用 secondary/quiet pattern。

### UI-IES-034 — L4 Object Contextual Action

对象级低频动作 SHOULD 在 selection、hover、context menu、More menu 或 inspector 中暴露。

### UI-IES-035 — L5 Advanced / Overflow

以下默认属于 L5：

- audit refs；
- correlation details；
- advanced model settings；
- export；
- destructive data commands；
- developer diagnostics。

L5 不得长期占据页面首屏。

## 5. Pattern Qualification

### UI-IES-040 — Card Qualification

Card 只在下列情况使用：

- 独立主任务容器；
- typed rich response；
- evidence summary；
- recovery issue；
- 少量 mutually exclusive option。

普通 collection MUST 优先 row/list。

禁止：

- 因“能点”而做成 Card；
- 每个 section 都套独立 Card；
- 用 Card 数量表达 IA。

### UI-IES-041 — Button Qualification

Button MUST 表达 Action 或 Control。

普通 destination SHOULD 使用 platform navigation pattern；可点击 domain object SHOULD 使用 InteractiveContent pattern。

### UI-IES-042 — Toolbar Qualification

Toolbar 只允许：

- 页面高频动作；
- search/view control；
- current selection contextual actions。

低频/高级操作进入 overflow/context menu。

### UI-IES-043 — Modal / Sheet Qualification

Modal/Sheet 只用于短暂决策、compact selection、destructive confirmation、窄屏 inspector。

复杂、可返回、可 deep-link 的流程 MUST 使用 destination route/page。

### UI-IES-044 — Status Qualification

Badge/Chip 只表达短状态。长解释进入正文、Inspector 或 Disclosure。

Status 不得只用颜色编码，也不得通过看似 button 的样式暗示不可用点击行为。

## 6. Product-specific Mapping

### UI-IES-050 — LearningGoal

```text
Goal object         → Domain Object
查看 Goal           → Navigation / InteractiveContent
创建 Goal           → Action
编辑 Goal           → Action
生命周期 command    → Action
切换 focused Goal   → Selection
Goal status         → StatusFeedback
```

### UI-IES-051 — LearningPlan

```text
Plan                → Domain Projection
查看 Plan           → Navigation / Disclosure
Activity row        → InteractiveContent
开始/继续 Activity  → Action
Plan reason detail  → Disclosure
```

前端拖拽/排序不得在没有 owner command 时成为 Control。

### UI-IES-052 — Learning Evidence / Progress

```text
Evidence summary      → Content/StatusFeedback
查看来源/理由          → Disclosure/Navigation
申请复测              → Action（仅 command contract 存在时）
直接修改 probability  → FORBIDDEN
```

### UI-IES-053 — Material

```text
Document row        → InteractiveContent
导入资料            → Action
Search/filter       → Control
Multi-select        → Selection
归档/标签/OCR       → Contextual Action
Processing state    → StatusFeedback
```

### UI-IES-054 — Tutor Workspace

```text
Conversation         → LearningActivity interaction mode
发送作答/问题         → Action
请求帮助              → Action
Assistance state     → StatusFeedback
Citation detail      → Disclosure
History rail         → Navigation
```

Tutor/Chat 不得成为独立 L0 domain。

## 7. Progressive Disclosure

### UI-IES-060

界面新增能力时按以下优先顺序处理：

```text
Delete
→ Merge
→ Contextual Reveal
→ Secondary Action
→ Overflow
→ 新增稳定 Navigation
```

新增 L0/L1 navigation 是最后手段。

### UI-IES-061 — Delete Test

任何常驻 interactive element 在冻结前必须回答：

> 删除它是否会阻断主要 User Job？

若不会，默认必须降级、合并或 contextualize，除非存在明确 discoverability / safety requirement。

## 8. Cross-platform Mapping

### UI-IES-070 — Semantic Stability

同一 intent 在 macOS/iOS/Web 的 semantic primitive MUST 一致；只允许 presentation pattern 改变。

### UI-IES-071 — macOS

目标优先：Sidebar/NavigationSplitView、Toolbar、Context Menu、Inspector、keyboard commands。

Settings SHOULD 通过 App command / `⌘,` 进入；Web 开发态可保留 utility entry。

### UI-IES-072 — iOS

目标优先：Tab Bar（今天/学习/资料库）、Navigation Stack、Toolbar、Sheet、Context/Swipe Action。

### UI-IES-073 — Keyboard

至少：

- Tab/Shift+Tab：focus traversal；
- Arrow：适用的 list/menu/picker；
- Enter/Space：激活；
- Esc：关闭 transient surface；
- `⌘,`：Settings（native shell 支持时）；
- `⌘K`：Search/Command（实现该能力时）。

## 9. Accessibility

### UI-IES-080

Semantic role 必须可通过 accessibility tree 理解；不得依赖 Card visual、hover 或颜色表达交互性。

### UI-IES-081

Icon-only control 必须有 accessible name。Status 不得只靠颜色。主要 touch target SHOULD ≥44×44 CSS px；桌面 compact control MAY ≥36px，但必须键盘可达且有足够间距。

### UI-IES-082

Contextual action 在 touch/keyboard 下必须有等价发现路径；禁止只依赖 hover。

## 10. Acceptance Criteria

- `UI-IES-AC-001`：所有核心 interactive element 可归入 7 个 primitive 之一；
- `UI-IES-AC-002`：没有把 Card/Button/Entry 当作顶层 semantic role；
- `UI-IES-AC-003`：L0 Product Domain 只有 Today/Learning/Library；
- `UI-IES-AC-004`：Goal/Plan/Progress/History 为 Learning L1 facets；
- `UI-IES-AC-005`：canonical activity 可用时 Today 只有一个 primary learning task；
- `UI-IES-AC-006`：Library 批量/高级动作只有在 selection/context 下出现；
- `UI-IES-AC-007`：Settings 不与三个 Product Domain 等权；
- `UI-IES-AC-008`：contextual action 有 keyboard/touch fallback；
- `UI-IES-AC-009`：普通 repeated domain object 默认 row/list，而不是 card ocean；
- `UI-IES-AC-010`：route/navigation change 本身不产生业务副作用。

## 11. Forbidden Implementations

禁止：

- Domain Object → automatic Page/Nav；
- feature count → navigation count；
- 所有内容 Card 化；
- 可点击 Card 但用户无法预测行为；
- 状态 chip 同时承担 command；
- 用隐藏控件绕过 hard rule；
- Settings 收纳所有无法分类功能；
- Chat-first global navigation；
- 为 Web Sidebar 实现便利反向改变目标 App IA；
- 为 Quiet UI 隐藏 error、citation、uncertainty、assistance 或 validation obligation。
