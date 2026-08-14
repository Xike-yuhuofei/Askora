# 08 — Information Architecture

**Phase**: 1 · **Generated**: 2026-08-12
**Evidence**: 主截图 [S] + dev-explorer UIKit [L] + 8 张 Light 截图 [S]

---

## 截图可见信息结构

主截图（Code Welcome）与 Work 视图、插件市场等截图共同揭示了 TraeWork 的顶层 IA：

### 顶层模式（截图命名 + dev-explorer 确认）

- **Work** — 工作区（Askora 任务 / Work 视图）
- **Code** — 代码模式（当前截图，Code Welcome）
- **Design** — 设计模式（截图未见，dev-explorer mode-switch 含三项）

### Sidebar 主要区域

| 区域 | 内容（截图+UIKit 综合） | Evidence |
|---|---|---|
| 全局导航 | 新建任务 / 插件市场 / 自动化 / 办公助理 / 模板库 | [S] |
| Pinned | 固定任务/工作区 | [S][L] |
| 任务列表 | Workspace → Project → Task 三级 | [S][L] task-tree |
| 账户 | 用户行（avatar + name + badge） | [L] dev-explorer |

### Workspace（Code Welcome）

- Hero 标题
- Prompt Composer
- Quick Actions / 建议

## 导航层级识别

| 导航类型 | 归属 | Evidence |
|---|---|---|
| Global Navigation | Work/Code/Design 模式切换 | [S][L] mode-switch |
| Mode Navigation | 模式内顶级（新建任务/插件市场/自动化/办公助理/模板库） | [S] |
| Task Navigation | Pinned + 任务列表（Workspace/Project/Task） | [S][L] |
| Workspace Navigation | 工作区/项目分组（可展开） | [S][L] |
| Contextual Navigation | 各模式内部（Code 编辑器、Composer 工具行等） | [S][L] |

## 不要统称 Sidebar

Sidebar 内部是**分区**结构，不能笼统当单列：

```
Sidebar
├── Window Controls (traffic lights)
├── Global Controls (搜索)
├── Mode Switcher (Work/Code/Design)
├── Primary Actions (新建任务/插件市场/自动化/办公助理/模板库)
├── Pinned
├── Workspace Navigation (可展开分组)
├── Task List
└── Account
```

> [I] 具体区域标题文案需放大截图 OCR 或结合插件市场/模板库截图交叉验证；Pinned 与 Workspace Navigation 的分界需确认。[U]

## 结论

1. [C][S] 顶层三分：Work / Code / Design。
2. [C][S] Sidebar 承担 Global + Mode + Task 三类导航叠加。
3. [C][L] 任务树采用 Workspace→Project→Task 三级（task-tree contract 证实）。
4. [I][L] 账户区位于 Sidebar 底部（dev-explorer user-row h56）。
5. [U] 模式切换器在 App 内的确切位置与外观以主截图为准（侧栏顶部区域）。
