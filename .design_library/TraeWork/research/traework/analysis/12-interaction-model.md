# 12 — Interaction Model

**Phase**: 1 · **Generated**: 2026-08-12
**Evidence**: Library contracts states [L] + UIKit 交互脚本 [L] + Screenshot [S]

---

## 交互清单与证据

| 交互 | 判定 | 证据 |
|---|---|---|
| Mode Switching | 存在（Work/Code/Design） | [C][S][L] mode-switch + 滑动指示条 |
| New Task | 存在（Primary Actions） | [C][S] |
| Sidebar Selection | 存在（nav-item 高亮） | [C][L] is-active / --active |
| Workspace Expand/Collapse | 存在（分组折叠） | [I][L] task-tree expanded/collapsed |
| Task Selection | 存在（task-row selected 态） | [C][L] |
| Prompt Focus | 存在（focused 态） | [C][L] ai-input --focused |
| Add Context | 存在（Context Add +） | [I][L] ai-input/attachment |
| Attachment | 存在 | [I][L] |
| Model Selection | 存在（下拉） | [I][L] ai-input model-selector |
| Voice | 存在 | [I][L] dev-explorer voice |
| Submit | 存在（品牌发送按钮） | [C][S][L] |
| Quick Action | 存在 | [C][S] |
| Hover | 存在（bg-overlay-l1） | [C][L] |
| Focus | 存在（border-brand） | [C][L] |
| Pressed | 存在（bg-overlay-l2/l3） | [C][L] |
| Selected | 存在 | [C][L] |
| Scroll | 存在（内容区滚动） | [I][L] |
| Resize | 未知（无截图证据） | [U] |

## 交互细节

### 导航激活标准 [L]
- nav-item：`is-active` / `--active` 类
- tabs：`aria-selected`
- 共用 `#traework-interaction-root` 脚本管理激活态

### Sidebar 分区交互
- 任务树三级：点击 Workspace 展开 → Project → Task（task-tree __level-1/2/3）[L]
- 分组可折叠（expanded/collapsed）[L]

### Prompt Composer 交互 [I][L]
- `focus` → border-brand + focus ring（ai-input-shadow-focus proposed）
- `typing` → textarea 高度自适应（72→300px）
- `submit` → loading 态（发送按钮状态变化）
- `/` → slashes 命令弹出

## 无法从截图确认的行为（标记 Unknown）

- Resize 拖拽细节
- Collapsible sidebar
- 键盘快捷键（Menu shortcut 可见于契约，但 App 级快捷键未验证）
- 拖拽任务重排

## 结论

1. [C][S][L] 交互模型以「分区导航 + 任务树 + Composer」为核心。
2. [C][L] 激活态标准统一（is-active/aria-selected）。
3. [U] 明确保持 Unknown 的交互不做发明。
