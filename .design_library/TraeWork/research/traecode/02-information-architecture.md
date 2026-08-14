# Information Architecture

> 状态：Research / Supporting  
> 目标：恢复当前截图中的信息域、导航层级与上下文关系，不从静态画面推导产品范围

## 1. 一级信息域

| 信息域 | 当前内容 | 证据 | 边界说明 |
|---|---|---|---|
| Workspace Identity | `Askora` workspace、SOLO 状态、workspace dropdown | `[C]` | workspace 切换后的数据隔离与生命周期 `[U]` |
| Task / Agent | 新任务、历史任务、运行结果、变更审阅、Composer | `[C]` | Task 与 Agent Run 是否一对一 `[U]` |
| Product Mode | Editor、Browser、Settings、Code Changes | `[C]` | 模式切换是否替换整个 Workbench `[I]` |
| Editor | 文档 Tab、Breadcrumb、Edit / Preview / Markdown、内容视图 | `[C]` | 多编辑器组、split 与 pinned tab `[U]` |
| Resource | Resource Manager、文件树、Outline、Timeline、Cue-Pro | `[C]` | 辅助区与当前 editor context 的同步方式 `[I]` |
| Diagnostics | Problems、Output、Terminal、Ports、Debug Console、Filter、Server selector | `[C]` | 各 Tab 是否支持独立实例和拆分 `[U]` |
| Global Status | branch/worktree 线索、error/warning count、分析进度、Cue 状态 | `[C]` | 状态来源、刷新与错误契约 `[U]` |

## 2. 当前 IA 树

```text
TraeCode Window [C]
├── Workspace Context [C]
│   ├── macOS Window Controls [C]
│   ├── Workspace Selector: Askora [C]
│   └── SOLO / account-or-mode indicator [C role, I semantics]
├── Agent Domain [C]
│   ├── Task Rail [C]
│   │   ├── New Task [C]
│   │   └── Task History [C]
│   └── Agent Main [C]
│       ├── Conversation / Result Stream [C]
│       ├── Change Summary [C]
│       ├── Review Decision Bar [C]
│       └── Prompt Composer [C]
└── Workbench Domain [C]
    ├── Product Mode Navigation [C]
    │   ├── Editor [C]
    │   ├── Browser [C]
    │   ├── Settings [C]
    │   └── Code Changes [C]
    ├── Editor Workspace [C]
    │   ├── Document Tabs [C]
    │   ├── Breadcrumb + View Controls [C]
    │   ├── Document Content [C]
    │   └── Bottom Diagnostics Panel [C]
    ├── Resource Sidebar [C]
    │   ├── Resource Tool Strip [C]
    │   ├── File Tree [C]
    │   ├── Outline [C]
    │   ├── Timeline [C]
    │   └── Cue-Pro [C]
    └── Workbench Status Bar [C]
```

## 3. 导航层级

### 3.1 Global / Workspace

Workspace selector 位于左上标题区，产品模式位于 Workbench 顶部 `[C]`。两者作用域不同：前者看起来决定项目上下文 `[I]`，后者看起来决定 Workbench 的主要工作模式 `[I]`。

### 3.2 Task / Agent

Task Rail 不是普通全局导航：每个条目包含任务标题、完成状态和时间，选中任务在 Agent Main 展示对应运行输出 `[C]`。因此更合理的 IA 是 `Task History → Agent Run Context`，而不是 `Activity Bar → Feature Page` `[I]`。

### 3.3 Editor / Resource

Editor Tab、Breadcrumb 与 Resource Tree 同时指向当前 Markdown 文件 `[C]`，表明至少存在“资源选择—编辑器上下文”关联 `[I]`。关系是单向打开、双向 selection sync，还是仅当前巧合 `[U]`。

### 3.4 Diagnostics

Bottom Panel 作为 Editor Workspace 的下方 dock 存在，而不是 Resource Sidebar 的子级 `[C]`。Status Bar 跨越 Editor 与 Resource Sidebar 的底部 `[C]`，因此其作用域更接近 Workbench 而不是当前文档 `[I]`。

## 4. Contextual Actions

| Context | 可见动作 | 状态证据 | 推断边界 |
|---|---|---|---|
| Workspace | dropdown、窗口动作、全局新建 | `[C]` | workspace management flow `[U]` |
| Task | 新任务、选中历史任务 | `[C]` | rename/delete/context menu `[U]` |
| Agent Result | 查看变更、反馈、刷新/重试类图标、待审查决策 | `[C]` | 图标精确语义部分 `[U]` |
| Composer | mention、context、image/attachment、security-like affordance、mode/model、voice、send | `[C]` | 每个 action 的数据与权限语义 `[U]` |
| Editor | close tab、Edit/Preview/Markdown、split/more actions | `[C]` | split 结果与 persistence `[U]` |
| Resource | new/search/source-control/grid/testing/debug 等工具图标 | `[C]` | 各图标是否全局或 sidebar-local `[I]` |
| Bottom Panel | tab switching、filter、server selection、panel actions | `[C]` | 多实例、pin、move panel `[U]` |

## 5. 信息架构原则假设

1. `Agent Dock` 与 `Workbench` 是两个并行一级上下文 `[I]`，允许用户在 Agent 任务与代码/资源证据之间持续交叉验证。
2. `Task Rail` 保存跨运行的历史上下文，`Agent Main` 保存当前运行的纵向上下文 `[I]`。
3. `Product Mode` 在 Workbench 内切换 Editor / Browser / Settings / Code Changes，而不替换 Agent Dock `[I]`。
4. `Resource Sidebar` 与 `Bottom Panel` 都辅助 Editor，但一个按资源组织，一个按诊断/运行信号组织 `[I]`。
5. `Status Bar` 汇总 Workbench 级状态，不应被实现为 Editor document 的子组件 `[I]`。

以上原则必须由模式切换、panel collapse 与 workspace switching 证据验证后，才可转成设计合同。

