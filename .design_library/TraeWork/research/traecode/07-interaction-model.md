# Interaction Model

> 状态：Research / Supporting，静态截图驱动的交互假设  
> 限制：截图可确认 control、affordance 与当前 state；不能直接确认 transition、timing、keyboard behavior 或 persistence

## 1. Interaction Layers

```text
Workspace Context [I]
├── Product Mode Navigation [C controls, I transition]
├── Task Selection [C selected state, I transition]
│   └── Agent Run Context [C current result]
│       ├── Inspect Result [C]
│       ├── Review Changes [C controls]
│       └── Compose Next Instruction [C composer]
└── Workbench Context [C]
    ├── Select Resource / Document [C states, I sync]
    ├── Switch Editor View [C states, I transition]
    ├── Inspect Diagnostics [C states, I transition]
    └── Observe Global Status [C]
```

## 2. Interaction Evidence Matrix

| Interaction | Target | 可见证据 | Transition 结论 | Evidence |
|---|---|---|---|---|
| Click / Activate | Task item | selected item 可见 | click 是否唯一触发方式 `[U]` | state `[C]` |
| Click / Activate | Product mode | Editor active，其他 inactive | mode 替换范围 `[I]` | state `[C]` |
| Click / Activate | Editor tab | 当前 Markdown tab active | tab switching、close behavior `[U]` | state `[C]` |
| Click / Activate | Panel tab | Output active | panel content switching `[I]` | state `[C]` |
| Click / Activate | Tree item | 当前文件 selected | 是否单击预览、双击固定 `[U]` | state `[C]` |
| Selection | Edit / Preview | Preview selected | 切换不改变文档状态 `[I]` | state `[C]` |
| Expand / Collapse | Tree folder / auxiliary section | expanded 与 collapsed chevrons 同时可见 | pointer/keyboard behavior `[U]` | state `[C]` |
| Type / Submit | Prompt Composer | input 与 submit control 可见 | multiline、shortcut、disabled rules `[U]` | affordance `[C]` |
| Review Decision | Change Review Bar | `全部撤销` / `全部保留` | confirmation、partial review、undo `[U]` | affordance `[C]` |
| Filter | Output Panel | filter field 可见 | debounce、match、clear `[U]` | affordance `[C]` |
| Dropdown | workspace/server/model/language | trigger 与 chevron 可见 | menu content/placement `[U]` | affordance `[C]` |
| Scroll | task/result/editor/tree/output | 长内容与裁切结构 | scroll container ownership `[I]` | `[I]` |
| Hover | all interactive controls | pointer 不可见 | 所有 hover visuals `[U]` | `[U]` |
| Focus | composer / tabs / buttons / tree | focus ring 不可见 | focus visuals/order `[U]` | `[U]` |
| Pressed | buttons/tabs | 静态图无按下瞬间 | pressed visuals `[U]` | `[U]` |
| Context Menu | task/tree/tab/editor | more icons 存在 | invocation与menu content `[U]` | `[U]` |
| Drag / Resize | panel seams | divider seam 可见 | hit area、limits、cursor、persistence `[U]` | seam `[C]` |
| Drag / Reorder | tab/task/panel | 未见 drag feedback | capability `[U]` | `[U]` |
| Keyboard Navigation | New Task 有 shortcut hint | 单一 shortcut 文案可见 | roving focus、tab order、commands `[U]` | shortcut `[C]` |
| Command Palette | global app | 未见 | trigger、scope、surface `[U]` | `[U]` |

## 3. Agent Workflow Hypothesis

当前静态画面支持以下“结果到下一指令”的连续布局 `[C]`：

```text
Task selected
→ Result content visible
→ Change summary visible
→ Pending review actions visible
→ Composer remains available
```

这表明设计可能允许用户在不离开当前任务的情况下检查结果、处理变更并继续发指令 `[I]`。但真实 transition 仍未知：

- 提交新 prompt 是追加到当前 Task 还是创建新 Run `[U]`；
- 未审查变更是否阻塞下一次提交 `[U]`；
- Agent running 时 Composer 是否 enabled `[U]`；
- approval 是否以内联卡片、modal 或 side panel 呈现 `[U]`；
- tool call 是否可展开、取消、重试或复制 `[U]`。

## 4. Panel Interaction Hypothesis

| Panel | Primary interaction | Secondary interaction | Unknown |
|---|---|---|---|
| Task Rail | select task `[C state]` | create task `[C control]` | rename/delete/reorder/filter |
| Agent Main | read/scroll result `[I]` | review changes / compose `[C controls]` | run cancellation, retry, approval |
| Editor | switch view/tab `[C states]` | close/more/split `[C affordances]` | pinned/dirty/split mechanics |
| Resource Sidebar | browse tree `[C states]` | switch tool/section `[C affordances]` | context menu, drag/drop, selection sync |
| Bottom Panel | switch tab `[C state]` | filter/server select `[C controls]` | resize, maximize, close, multi-instance |
| Status Bar | observe status `[C]` | click-to-open related context `[I]` | overflow and keyboard access |

## 5. Interaction Principles — Inferred

1. **Context persistence**：Agent Dock 与 Workbench 同时存在，减少在结果与代码证据之间切页 `[I]`。
2. **Inline review**：变更审阅动作与 Agent 结果、Composer 同域，避免跳到独立审批流程 `[I]`。
3. **Layered density**：一级 mode、二级 tabs、三级 panel sections 各自承担不同 scope `[I]`。
4. **Status near source**：task completion、agent completion、Cue analysis、workbench analysis 在各自上下文附近出现 `[C pattern, I principle]`。
5. **Progressive disclosure**：大量 icon-only actions、collapsed resource sections 与 more menu 暗示通过二级层控制密度 `[I]`。

## 6. Accessibility Unknowns

以下均不能从截图确认：

- focus order 与 focus-visible style `[U]`；
- icon-only button 的 accessible name / tooltip `[U]`；
- tabs 使用 arrow-key、Home/End 的方式 `[U]`；
- tree 使用 roving tabindex 与展开快捷键的方式 `[U]`；
- resize divider 是否可通过 keyboard 调整 `[U]`；
- selected / success / warning 是否有非颜色冗余编码 `[U]`；
- contrast ratio、text zoom、screen reader announcements `[U]`；
- running / completion / error 的 live region 策略 `[U]`。

## 7. Prototype / Experiment Status

- `07 Prototype` 已完成 Editor Tab selection A/B 往返，只验证官方 tab variant composition 与 click navigation `[C implementation]`；
- `08 Experiments` 已完成 Resize stress test，只验证当前 Figma Auto Layout 的压缩与失效点 `[C implementation]`；
- 两者都不证明 TraeCode 真实应用行为。

剩余 backlog 按证据成熟度排序：

1. Task switching：仅在取得 selected context 前后证据后验证。
2. Resource section expand / collapse：需要 header 与 scroll ownership 的连续证据。
3. Agent completed → pending review → decision：需要补充 outcome screenshot 后再实现。
4. Sidebar / Bottom Panel resize：需要真实 before/after 样本后再实现交互原型。
5. Hover / Focus / Context Menu / Dropdown：需要对应视觉证据。
6. Agent start / running / error：需要完整状态链，不能用猜测补齐。
