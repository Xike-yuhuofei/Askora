# 09 — Application Shell Reverse Engineering

**Phase**: 1 · **Generated**: 2026-08-12
**Evidence**: 主截图几何测量 [S] + dev-explorer UIKit 结构 [L] + shell-three-panel contract [L]

---

## 恢复的 App Shell（以真实截图为准）

```
TraeWork Application Window (2291×1299, macOS)
├── Sidebar (301px fixed, bg #f5f5f5 = bg-base-secondary)
│   ├── Window Controls (traffic lights, 顶部)
│   ├── Global Controls (搜索框)
│   ├── Mode Switcher (Work / Code / Design)
│   ├── Primary Actions (新建任务 / 插件市场 / 自动化 / 办公助理 / 模板库)
│   ├── Pinned
│   ├── Workspace Navigation (可展开分组)
│   ├── Task List (Workspace → Project → Task)
│   └── Account (底部用户行)
│
└── Workspace (flex 填充剩余, bg #ffffff = bg-base-default)
    └── Welcome Surface (Code Mode)
        ├── Hero 标题
        ├── Prompt Composer (居中, 800×55 实测)
        └── Quick Actions / 建议行
```

## 关键边界实测 [S]

| 项 | 值 |
|---|---|
| Sidebar 宽 | 301 px |
| Workspace x 起点 | 302 |
| Sidebar 背景 | `#f5f5f5` |
| Workspace 背景 | `#ffffff` |
| 分隔线 | 1px（x=301, `#efefef`） |
| Composer 中心 | x≈1292（= Workspace 几何中心 1296） |

## 系统级布局参考（shell-three-panel contract）[L]

| 区域 | 值 |
|---|---|
| left-panel-width | 200px（折叠 48px） |
| right-panel-width | 360px（折叠 0px） |
| center-panel-min | 480px |
| gutter | 1px border + 4px gap |
| min viewport | 960px |

> 说明：shell-three-panel 是三栏参考，当前 Code Welcome 截图只呈现 Sidebar + 单栏 Workspace（两段式），未见右侧面板。右侧面板属于其他模式（如 Code 编辑器拆分、Design 模式）。[I][U]

## App Shell 分层归属

| 层级 | 归属 | Evidence |
|---|---|---|
| 窗口 chrome | macOS 原生（traffic lights） | [S] |
| Sidebar 骨架 | App Shell | [C][S] |
| Mode Switcher | App Shell / Global | [C][S] |
| 导航项（新建任务等） | Global / Mode Navigation | [C][S] |
| Pinned/任务树 | App Shell 侧栏内容 | [C][S] |
| Workspace 布局 | App Shell（flex 区域） | [C][S] |
| Welcome 内容 | Code Mode 专属 | [C][S] |
| Prompt Composer | AI Composer Pattern（跨模式组件） | [C][S][L] |

## 结论

1. [C][S] TraeWork App Shell = **Sidebar + Workspace 两段式**（当前视图），未来可扩展为三栏（shell-three-panel）。
2. [C][S] Sidebar 固定宽（实测 301），Workspace flex。
3. [C][L] Composer 属于跨模式 AI Pattern，不绑定 Code Welcome。
4. [I][U] 右侧面板在当前 Code Welcome 截图中不存在；是否常驻需更多截图确认。
