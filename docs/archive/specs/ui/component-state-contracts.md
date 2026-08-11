# Askora UI Component State Contracts

> Spec ID：`UI-COMP-*`
> 状态：`FROZEN`
> Governing：`ADR-0014`、`UI-IES-*`、`UI-IA-*`、`UI-SCREEN-*`、`UI-VIS-*`、`UI-QUAL-*`
> Scope：核心交互组件状态、pointer/keyboard 行为、异步与数据区域状态

## 1. 基本原则

### UI-COMP-001 — State Is Semantic

组件状态必须表达真实交互或数据事实，不得仅作为视觉 variant。

核心交互状态词汇冻结为：

```text
DEFAULT
HOVER
FOCUS
PRESSED
SELECTED
DISABLED
LOADING
```

数据区域状态继续使用：

```text
LOADING
EMPTY
READY
PARTIAL
STALE
ERROR
UNAUTHORIZED
```

交互状态与数据区域状态不得混为同一枚举。例如 Button 的 `LOADING` 表示该 Action 正在执行；页面的 `LOADING` 表示数据尚未就绪。

### UI-COMP-002 — No Visual-only Truth

`selected`、`disabled`、`loading`、`error` 等状态必须可由 DOM/accessibility semantics 或明确状态属性识别，禁止只依靠颜色、透明度、阴影或 CSS class 表达。

### UI-COMP-003 — State Precedence

当多个状态同时成立时，行为优先级冻结为：

```text
DISABLED
→ LOADING
→ PRESSED
→ SELECTED
→ FOCUS
→ HOVER
→ DEFAULT
```

该优先级只决定交互可用性与视觉冲突处理，不意味着低优先级状态必须完全不可见。例如 selected navigation item 仍必须显示 keyboard focus ring。

## 2. 通用状态合同

| State | 触发 | 行为 | 视觉/无障碍要求 |
|---|---|---|---|
| DEFAULT | 无临时交互 | 使用正常行为 | 基准样式与可访问语义完整 |
| HOVER | pointer 位于可交互目标 | 不触发业务副作用 | 与 DEFAULT、FOCUS、SELECTED 可区分；不得成为唯一发现路径 |
| FOCUS | keyboard/programmatic focus | 可通过标准键盘激活 | 必须有清晰 focus indicator；不得仅依赖浏览器默认被全局移除 |
| PRESSED | pointer down 或键盘激活中的瞬时状态 | 尚未等于 command 成功 | 必须与 SELECTED 区分；释放/取消后恢复 |
| SELECTED | Navigation/Selection/InteractiveContent 当前选择 | 表达稳定选择，不自动等于业务 command | 使用 `aria-current`、`aria-selected`、checked 等匹配语义；允许同时 FOCUS |
| DISABLED | 当前 action/control 不可执行 | 禁止触发 command；不得进入重复提交 | 必须有语义 disabled；若原因对用户重要，应可理解地说明原因 |
| LOADING | action/control 的异步提交正在进行 | 默认 single-flight；阻止重复提交 | 显示可感知 pending 状态并保留 label/context；完成后恢复 focus |

## 3. Pointer 与 Keyboard 一致性

### UI-COMP-010 — Activation Equivalence

同一 Action 在 pointer 与 keyboard 下必须产生相同业务意图：

- Button/Action：pointer click 与 `Enter`/`Space`（按平台语义）等价；
- Navigation link/item：pointer activation 与 `Enter` 等价；
- Checkbox/Toggle：pointer 与 `Space` 等价；
- Menu/Listbox：按对应 ARIA/platform pattern 支持 Arrow、Enter/Space、Escape。

不得维护 pointer-only command path。

### UI-COMP-011 — Pressed Is Transient

`PRESSED` 是输入设备层面的瞬时反馈，不得被用作持久业务状态。

- pointer down 后移出目标并取消，应恢复到原状态；
- keyboard press 不得在 keydown 与 keyup 之间重复提交；
- command 成功后的稳定状态必须来自 owner/query re-read，而不是把 `PRESSED` 留作成功状态。

### UI-COMP-012 — Focus Preservation

异步操作完成后：

- 若触发元素仍存在，focus SHOULD 回到触发元素或流程中下一个合理目标；
- modal/sheet 关闭后 focus MUST 返回触发入口；
- route navigation 后 focus MUST 移至新页面语义起点，而不是遗留在不可见节点。

## 4. 核心组件状态矩阵

### UI-COMP-020 — Button / Action

必须支持：

```text
DEFAULT / HOVER / FOCUS / PRESSED / DISABLED / LOADING
```

规则：

- Button 不使用 `SELECTED` 表达 toggle/choice；需要持续选择时改用 Control/Selection pattern；
- `LOADING` 时默认视为不可重复提交；
- Danger Action 在 disabled/loading 状态不得丢失其 destructive 语义；
- icon-only button 必须始终有 accessible name。

### UI-COMP-021 — Navigation Item

必须支持：

```text
DEFAULT / HOVER / FOCUS / PRESSED / SELECTED / DISABLED(仅确有不可达语义时)
```

规则：

- 当前 route/facet 使用 `SELECTED` / `aria-current`；
- navigation selection 本身不得产生业务 write；
- Product Domain、Learning Facet、App Utility 必须保持层级差异；
- selected item 仍必须显示 focus。

### UI-COMP-022 — Selection Control

Checkbox、radio、segmented selection、listbox、picker、multi-select 必须支持：

```text
DEFAULT / HOVER / FOCUS / PRESSED / SELECTED / DISABLED
```

若选择会立即提交 owner command，必须由对应产品合同明确；否则 selection 与 submit 分离。

### UI-COMP-023 — Text Input / Editable Control

必须支持：

```text
DEFAULT / HOVER(适用时) / FOCUS / DISABLED / ERROR / LOADING(仅异步校验或提交适用时)
```

规则：

- label 不得由 placeholder 替代；
- validation error 必须有文本/语义关联；
- loading/validation 不得静默覆盖用户输入；
- disabled 与 read-only 必须区分。

### UI-COMP-024 — Interactive Row / List Item

必须支持：

```text
DEFAULT / HOVER / FOCUS / PRESSED / SELECTED(适用时) / DISABLED(适用时)
```

规则：

- row 的主点击区域只表达一个可预测 intent；
- trailing contextual action 必须拥有独立 focus target；
- selection 与 open/navigation 不得通过不明确的同一 click 隐式混合；
- contextual action 不得只在 hover 下可发现。

### UI-COMP-025 — Menu / Context Menu / Overflow

必须支持：

```text
DEFAULT / HOVER(or ACTIVE DESCENDANT) / FOCUS / PRESSED / SELECTED(适用时) / DISABLED
```

必须支持 keyboard traversal、Escape close、focus return。Destructive item 必须保持 danger semantics 与 confirmation contract。

### UI-COMP-026 — Disclosure / Inspector Trigger

必须支持：

```text
DEFAULT / HOVER / FOCUS / PRESSED / SELECTED(or EXPANDED) / DISABLED
```

展开状态使用 `aria-expanded` 等匹配语义。关键任务唯一信息、安全错误、citation 或 validation obligation 不得只藏在默认关闭的 Disclosure 中。

## 5. Loading / Empty / Error 合同

### UI-COMP-030 — Action Loading

Action `LOADING`：

- 使用 single-flight；
- 禁止重复 command；
- label/context 不应因 spinner 完全消失；
- pending 状态必须可被 assistive technology 感知；
- success/failure 后必须 re-query 或使用正式返回值更新，不得长期依赖 optimistic fake truth。

### UI-COMP-031 — Data-region Loading

页面或数据区域 `LOADING`：

- 使用与最终布局一致的最小 skeleton 或明确进度；
- 不显示假数据；
- 局部数据加载不得无条件阻断不相关区域。

### UI-COMP-032 — Empty

`EMPTY` 必须同时回答：

1. 当前缺少什么；
2. 用户现在可以做什么。

不得使用模拟 Goal、Activity、Evidence、Document 填充空态。

### UI-COMP-033 — Error

`ERROR` 必须：

- 使用结构化 error code/category/retryable；
- 仅在 retryable 时提供 Retry Action；
- 显示用户可理解信息；
- 必要时通过 Disclosure 提供 correlation/detail；
- 不暴露 raw traceback、secret、绝对路径或内部敏感上下文。

### UI-COMP-034 — Partial / Stale / Unauthorized

`PARTIAL`、`STALE`、`UNAUTHORIZED` 不得伪装成 READY。

可继续使用的区域保持可用，但必须在对应数据区域准确说明状态与限制。

## 6. Disabled Contract

### UI-COMP-040

只有以下情况可以 disabled：

- owner/canonical state 明确禁止；
- 当前 command 正在 single-flight；
- 必需输入不完整；
- 安全/权限/版本冲突合同要求阻断。

不得因为实现未完成而在正式产品中长期展示无解释 disabled control；此类能力应隐藏、延期或明确标记 unavailable。

### UI-COMP-041

Disabled 不得作为错误恢复替代方案。若用户需要知道“为什么不能做”，必须提供相邻说明、tooltip/help text 或可访问描述。

## 7. Selected Contract

### UI-COMP-050

`SELECTED` 只表达以下稳定语义之一：

- 当前 Navigation destination；
- Selection 的当前值；
- 当前 selected domain object；
- Disclosure 的 expanded/open state（使用对应 semantic attribute）。

不得用 selected 表示“command 已执行成功”。

### UI-COMP-051

Selected、focused、hovered 可以同时成立；视觉系统必须保证：

- selected 状态稳定；
- focus ring 始终可识别；
- hover 不覆盖 selected identity。

## 8. UX Architecture Component State Contracts (ADR-0018)

本节冻结 `UX-Architecture-Canonical-Design-Delta.md` 经 `ADR-0018` 吸收后的三栏/Workspace/Drawer/右栏/笔记相关组件状态。

### UXA-COMP-070 — Workspace Selection

左栏 Workspace selection 使用 `SELECTED` / `aria-current`。切换 Workspace 本身是用户显式 Action，不是 Navigation 的副作用。切换触发持久化时使用 `LOADING`（single-flight）与 `saved / saving / failed / recoverable` 的可感知状态。单一 Workspace 不得显示虚假 selector。

### UXA-COMP-071 — Drawer Disclosure

Learning Context Drawer 使用 Disclosure pattern：`aria-expanded` 表达展开态，`SELECTED` 仅表达展开，不表达业务 command 成功。expanded/collapsed 只改变 presentation state，不得触发 owner command。

Drawer 内容状态区分 `LOADING / READY / MISSING / PARTIAL / STALE / ERROR`。`MISSING` 不得转换为空或默认内容；`PARTIAL`/`STALE` 不得冒充 READY。

### UXA-COMP-072 — Right Rail Hide / Show

右栏 hide/show 是 Control（presentation preference），使用 `aria-expanded` 表达可见性。隐藏 MUST NOT 移除完成任务所需的唯一引用、帮助状态或 validation obligation。重新打开 MUST 恢复上下文。

### UXA-COMP-073 — Tab Semantics

Current Material tabs 使用 `Tablist/Tab/Tabpanel` 语义。tab 打开/切换/关闭是 Navigation/Disclosure，不产生业务 write，不改变中栏学习内容。跨 Workspace 引用 fail closed。

### UXA-COMP-074 — Autosave Feedback

Notes autosave 使用 `StatusFeedback` + live region，区分 `SAVING / SAVED / FAILED / CONFLICT / RECOVERABLE`。未持久化时不得显示"已保存"。`CONFLICT` 时要求用户确认，不得静默覆盖较新笔记。

### UXA-COMP-075 — Focus Return

Drawer 展开/收起、右栏 hide/show、tab 切换、sheet 关闭后 focus MUST 返回触发点或流程中下一个合理目标。route/deep-link 迁移后 focus 移到新页面语义起点。

### UXA-COMP-076 — Keyboard / Touch Equivalence

左栏切换、Drawer expand/collapse、右栏 hide/show、tab 操作、Workspace switch MUST 有 keyboard 与 touch 等价路径。Drawer/tab/sheet 需 Escape 关闭 transient surface。不得存在 hover-only 或 pointer-only command path。

### UXA-COMP-077 — Narrow-screen Sheet

窄屏右栏/选项 MUST 变为可访问 sheet/section，不得永久消失。Sheet 需要 focus containment、Escape close、focus return，且不隐藏完成任务所需唯一信息。

### UXA-COMP-078 — No Horizontal Scroll / No Critical Nested Scroll

页面/右栏/Drawer 不得出现页面级横向滚动。主要操作区域避免同时出现页面 + 消息 + Drawer 三层关键滚动；任何内部滚动区域须有明确边界与键盘可达。

### UXA-COMP-079 — No Silent Data Loss

Workspace 切换、右栏收起、Drawer 关闭、route 迁移 MUST NOT 静默丢弃未提交 draft、streaming run、未持久化 note、open material tab 或可恢复 active session。未持久化时不得显示"已保存"。

## 9. Test Contract

### UI-COMP-060 — Component Tests

核心组件至少验证：

- DEFAULT → HOVER/FOCUS/PRESSED 状态转换；
- keyboard 与 pointer activation 等价；
- SELECTED 与 FOCUS 可共存；
- DISABLED 不触发 command；
- LOADING single-flight；
- async success/failure 后 focus 与状态恢复；
- accessible name/role/state 正确；
- contextual action 不依赖 hover-only。

### UI-COMP-061 — Data-state Tests

数据页面/区域至少验证：

```text
LOADING / EMPTY / READY / PARTIAL / STALE / ERROR / UNAUTHORIZED
```

并断言 EMPTY/ERROR 不使用假数据，PARTIAL/STALE 不冒充 READY。

### UI-COMP-062 — Integration / E2E

关键路径必须以 keyboard-only 和 pointer 两种方式验证；至少覆盖 Today primary action、Learning facet navigation、Goal/Library list interaction、Workspace submit/help、Settings navigation 与 destructive confirmation。

## 10. Acceptance Criteria

- `UI-COMP-AC-001`：核心组件状态统一使用 DEFAULT/HOVER/FOCUS/PRESSED/SELECTED/DISABLED/LOADING 词汇；
- `UI-COMP-AC-002`：Loading/Empty/Error 与 `UI-SCREEN-*` 数据状态合同一致；
- `UI-COMP-AC-003`：pointer 与 keyboard 产生相同 intent，不存在 hover-only command；
- `UI-COMP-AC-004`：disabled/loading 不产生重复 command；
- `UI-COMP-AC-005`：selected 与 pressed 语义明确分离；
- `UI-COMP-AC-006`：所有 persistent state 均可通过 semantic/accessibility state 识别；
- `UI-COMP-AC-007`：组件测试可直接验证上述状态转换与行为。

## 11. Forbidden Implementations

禁止：

- 用颜色单独表达 selected/error/disabled；
- 把 pressed 当业务成功状态；
- loading 时允许重复 command；
- 通过隐藏 focus outline 换取“干净视觉”；
- hover-only contextual action；
- navigation selected 同时隐式执行业务 write；
- empty/error 页面注入假 canonical data；
- disabled control 永久代替未实现能力；
- 组件自行推断 mastery、assistance、plan 或 owner state。
