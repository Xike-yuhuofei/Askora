# State Model

> 状态：Research / Supporting  
> 原则：状态“可见”不等于状态 transition、数据 owner 或 persistence 已确认

## 1. Global State Matrix

| State | 当前截图是否可见 | 可见对象 | Evidence | 缺口 |
|---|---|---|---|---|
| Default | 是 | inactive task/mode/tab/tree rows | `[C]` | default 与 idle 的完整定义 `[U]` |
| Hover | 否 | — | `[U]` | pointer screenshot |
| Pressed | 否 | — | `[U]` | pressed-frame screenshot / recording |
| Selected | 是 | task、Editor mode、Markdown tab、Preview、Output、tree file | `[C]` | selection owner / persistence `[U]` |
| Focused | 否 | — | `[U]` | keyboard focus screenshot |
| Disabled | 不可确认 | muted controls 不能等同 disabled | `[U]` | disabled reason / tooltip |
| Loading | 是 | Cue-Pro `分析中...` | `[C]` | loading skeleton / timeout / cancel `[U]` |
| Running | 是 | Workbench `正在分析 50 个文件` | `[C]` | 该状态不等同 Agent Run running |
| Success | 是 | task completed、agent task completed | `[C]` | success duration / dismiss / next action `[U]` |
| Warning | 部分 | pending review amber-like affordance | visual `[C]`；warning semantics `[I]` | warning contract `[U]` |
| Error | 完整 surface 否 | status counters 可能显示 0 error | `[U]` | error message / retry / recovery |
| Empty | 否 | — | `[U]` | empty task/editor/resource/diagnostics |

## 2. Task Item State

| Candidate state | Evidence | Visual cues |
|---|---|---|
| Default + completed | `[C]` | dark card、green completion icon、title、completion time |
| Selected + completed | `[C]` | differentiated background/border + same completion metadata |
| Running | `[U]` | spinner/progress/stop affordance 未见 |
| Failed | `[U]` | error color/message 未见 |
| Cancelled | `[U]` | 未见 |
| Unread / updated | `[U]` | 未见 badge 语义 |
| Hover / Focus | `[U]` | 未见 |

## 3. Agent Run Lifecycle Candidate

```text
Idle [U]
→ Composing [control visible C, active state U]
→ Submitted [U]
→ Planning / Queued [U]
→ Running [U for Agent Run]
   ├── Tool Call [U]
   ├── Awaiting Approval [U]
   └── Streaming Result [U]
→ Completed [C]
→ Changes Pending Review [C]
   ├── Kept / Applied [U]
   ├── Reverted [U]
   └── Partially Reviewed [U]
→ Error / Cancelled [U]
```

截图同时显示 Cue-Pro / file analysis running 与 Agent task completed `[C]`。两者必须作为不同 owner 的并行状态处理 `[I]`；不能因为页面有“分析中”就声称 Agent Run 正在运行。

## 4. Agent Result Substates

| Substate | Visible | Evidence | Needed behavior evidence |
|---|---|---|---|
| Result content available | 是 | `[C]` | streaming vs final boundary |
| Validation evidence available | 是 | `[C]` | expand/copy/open source |
| Change summary available | 是 | `[C]` | partial update / stale result |
| Pending review | 是 | `[C]` | keep/revert outcome |
| Feedback available | 是 | `[C]` | selected feedback state / submission |
| Retry available | icon semantics 不确定 | `[U]` | retry eligibility / idempotency |
| Approval requested | 否 | `[U]` | approve/deny/request changes |
| Error recoverable | 否 | `[U]` | retry / edit prompt / diagnostics |

## 5. Editor / Workbench State

| Object | Confirmed current state | Candidate states needing evidence |
|---|---|---|
| Product Mode | Editor selected `[C]` | Browser / Settings / Code Changes active `[U]` |
| Editor Tab | one Markdown file active `[C]` | inactive / dirty / pinned / preview-tab / split `[U]` |
| Editor View | Preview selected `[C]` | Edit selected / Markdown menu open `[U]` |
| Resource Tree | folders expanded/collapsed + file selected `[C]` | hover/focus/context/drop target/error `[U]` |
| Bottom Panel | Output selected `[C]` | Problems/Terminal/Ports/Debug active、closed/maximized `[U]` |
| Cue-Pro | analyzing `[C]` | idle/result/error/cancelled `[U]` |
| Status Bar | file analysis running + zero counters visible `[C]` | completion/error/offline/overflow `[U]` |

## 6. State Ownership Questions

静态 UI 不能确认 canonical owner，但下一阶段必须避免以下耦合：

- Task selection 是否决定 Agent Main，而不直接改变 Editor selection `[U]`；
- Resource selection 与 Editor Tab selection 谁是 source of truth `[U]`；
- Bottom Panel active tab 是 workspace-local、window-local 还是 global preference `[U]`；
- Panel size/collapse state 是否持久化到 workspace `[U]`；
- pending review 是 Agent Run state、change set state，还是独立 review state `[U]`；
- Cue-Pro analysis 与 global file analysis 是否共享同一 job `[U]`。

这些问题在 Figma 可先用命名隔离表达，不能由 component variant 暗中决定产品数据语义。

## 7. State Component Requirements for Next Phase

1. 每个组件只创建截图确认的基础 state，加 `Unverified` 注释覆盖未确认视觉。
2. Agent state 使用独立 `runStatus`、`reviewStatus`、`composerStatus` 属性候选，避免一个万能 `state` 混合并行状态 `[I]`。
3. Tree、Tab、Task Item 将 `selected` 与 `focused` 分离；当前只实现 selected reference `[I]`。
4. Loading、Running、Progress 与 Success 不共用同一布尔值 `[I]`。
5. Error 与 Empty 在获得截图前只建立 slot/annotation，不绘制假高保真 surface。

