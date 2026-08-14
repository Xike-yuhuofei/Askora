# Unknown / Open Questions

> 状态：Research / Supporting  
> 原则：问题保持显式，不用高保真细节静默关闭

## 1. P0 — 阻塞正式 Foundations / Shell Contract

| ID | Question | 当前假设 | 需要的证据 | 影响 |
|---|---|---|---|---|
| `TQ-001` | 截图 image px 与 macOS logical px 的比例是多少？ | 可能为 1:1 `[I]` | Display scale + 原始窗口 logical size | 所有尺寸、字体、border |
| `TQ-002` | Window min width / height 是多少？ | `[U]` | 拖到最小窗口的完整截图/录屏 | Shell constraints |
| `TQ-003` | Task Rail / Agent Main / Resource / Bottom 的 min/default/max 是什么？ | `[U]` | 每个 divider 两端极限与 reset 行为 | Layout tokens |
| `TQ-004` | 窗口缩小时谁先 shrink / collapse？ | Candidate A/B `[U]` | 1920、1717、1440、1280、min width 同场景截图 | Responsive rules |
| `TQ-005` | Top Region 是原生 titlebar、custom chrome 还是混合实现？ | 混合 `[I]` | full-screen / maximized / window controls interaction | window architecture |
| `TQ-006` | Panel size/collapse 是否按 workspace 持久化？ | `[U]` | 切 workspace、重启前后 | state ownership |

`08 Experiments` 已完成当前 Figma implementation stress test，但只暴露 Auto Layout 的压缩与失效点；它没有关闭 `TQ-002`～`TQ-004`。

## 2. P1 — 阻塞 Agent / Interaction Components

| ID | Question | 需要截图/录屏 | 影响 |
|---|---|---|---|
| `TQ-007` | Agent 从 start 到 completed 的完整状态链是什么？ | idle、submitted、planning、running、streaming、completed | Agent variants |
| `TQ-008` | Tool Call / Tool Result 如何折叠、展开、失败与重试？ | default、expanded、running、success、error | Agent component taxonomy |
| `TQ-009` | Approval 的 presentation 与 decision flow 是什么？ | approval request、approve、deny、expired | safety / review pattern |
| `TQ-010` | Pending changes 的 keep/revert 是否支持逐文件与 undo？ | partial review 与 outcome | Change Review state |
| `TQ-011` | Agent error / cancelled / rate-limited / offline 如何呈现？ | 每类 error surface 与 recovery | Error component |
| `TQ-012` | Running 时 Composer 是否可继续输入/提交？ | running + composer interaction | input disabled/queued rules |
| `TQ-013` | Task 与 Agent Run 是一对一、一对多还是 session container？ | 创建后续 prompt / task history变化 | IA 与 data model |

## 3. P1 — 阻塞 Workspace / Panel Components

| ID | Question | 需要截图/录屏 | 影响 |
|---|---|---|---|
| `TQ-014` | Editor 支持 multi-group split 吗？ | split editor、drag tab、close group | Shell / tab architecture |
| `TQ-015` | Resource Sidebar collapse / expand 后放在哪里？ | before/after + tooltip | panel variants |
| `TQ-016` | Bottom Panel close/maximize/resize 规则是什么？ | closed、min、max、drag | vertical layout |
| `TQ-017` | Problems / Terminal / Ports / Debug Console active states？ | 每个 tab 至少一张 | Panel content patterns |
| `TQ-018` | Tree single-click、double-click、preview/pin、context menu 行为？ | interaction recording | tree/tab sync |
| `TQ-019` | Browser / Settings / Code Changes 模式是否替换整个 Workbench？ | 三个 mode active 的完整窗口 | Product Mode IA |
| `TQ-020` | Cue-Pro 与 Resource/Editor/Agent 的 scope 和 job owner？ | idle/result/error + context switch | state ownership |

## 4. P2 — 视觉与可访问性补证

| ID | Question | 需要的证据 |
|---|---|---|
| `TQ-021` | UI 与 Code font family / size / weight？ | DevTools/computed style、Figma source 或 font inspection |
| `TQ-022` | Hover / Pressed / Focus / Disabled 的视觉值？ | pointer 与 keyboard focus screenshots |
| `TQ-023` | Tooltip delay、placement、trigger 与动态内容规则？静态 surface 已由 official atom 确认 `[C]` | icon buttons hover / keyboard recording |
| `TQ-024` | Popover 的 anchor / placement / dismissal，以及 Context Menu / Dropdown / Command Palette 的 surface 与行为？Popover 静态 surface 已确认 `[C]` | 各 overlay open state |
| `TQ-025` | light theme / high contrast / color theme 是否存在？ | theme settings 与代表 screen |
| `TQ-026` | text zoom、UI zoom 与 Retina scale 如何影响 layout？ | 100%/125%/150% 或应用实际 zoom levels |
| `TQ-027` | keyboard order、screen reader labels、live announcements？ | accessibility tree + keyboard walkthrough |
| `TQ-028` | icon source / family / license？ | code/source/design library evidence |

Phase 11 已关闭 Tooltip / Popover / Empty State / Code Block 的静态 visual-contract gap，并建立 source-backed Figma components `[C implementation]`。这不关闭 `TQ-023` / `TQ-024` 的 runtime interaction、focus、keyboard、transition 或真实 scroll affordance。

## 5. 需要补充的截图包

### Pack A — Resize（最高优先）

保持同一 Task、同一文件、同一 Panel 状态，采集：

- 最大化窗口；
- 当前参考宽度；
- 中等宽度；
- 接近最小宽度；
- 最小高度；
- 分别拖到每个 panel 的 min / max；
- 分别 collapse / expand Task Rail、Agent Main、Resource Sidebar、Bottom Panel。

### Pack B — Agent Lifecycle

- new task / empty composer；
- prompt submitted；
- planning / queued；
- tool running；
- tool success / result expanded；
- approval requested；
- completed without changes；
- completed with changes pending review；
- partial review / keep / revert outcome；
- error / retry / cancelled。

### Pack C — Interaction States

- Task Item、Product Mode、Editor Tab、Tree Item、Icon Button、Text Button；Button 已有官方 Default / Hover / Active / Disabled 静态 variants，但仍缺真实 runtime 与 Focus / keyboard / loading 证据；
- 每类采 default / hover / pressed / selected / focused / disabled（如存在）；
- Dropdown、Popover、Context Menu、Tooltip、Command Palette open state；Phase 11 静态 atoms 仅作为视觉基线；
- keyboard focus path 与 resize divider focus。

### Pack D — Workbench Modes

- Browser active；
- Settings active；
- Code Changes active；
- multi-tab / dirty / pinned / split editor；
- Problems / Terminal / Ports / Debug Console；
- Resource Outline / Timeline / Cue-Pro result/error。

## 6. Capture Protocol

每张新增证据应记录：

```text
Screenshot ID
App version / build
macOS version
Display scale / UI zoom
Image pixel size
Window logical size
Workspace / Task / File
Panel open/collapse state
Pointer position or keyboard focus target
State before / action / state after
Timestamp
```

若为录屏，应在关键 transition 处补关键帧，避免只用动画视觉推断最终 state。

## 7. Blocker 判定

- 第一轮研究与 FigJam/Figma 文件结构：无 blocker，已完成。
- 建立 experimental Foundations 与 confirmed primitives：可继续，不需要等待全部问题关闭。
- 冻结正式 resize contract、完整 Agent variants、accessible interaction contract：被对应 P0/P1 证据阻塞。
- 高保真代表 screens：可做 `TC-UI-001` reference reconstruction，但必须标明单截图基线，不能声称代表完整系统。
