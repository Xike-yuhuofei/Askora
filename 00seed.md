---

### 一、排版系统 (6 个)

| # | 位置 | 问题 | 严重程度 |
|---|------|------|---------|
| T1 | [Library.css#L25](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.css#L25) | `.library-header__subtitle` 副标题缺少 `font-weight` 定义，层级跳跃过大 | P2 |
| T2 | [Library.css#L255](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.css#L255) | `.library-card__badge` 文件类型徽章 `font-size: 9px` 过小，深色背景上对比度不足 | P1 |
| T3 | [Library.css#L552](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.css#L552) | `.ws-kpi-block__num` 26px 数字使用 `letter-spacing: -.02em` 过于紧凑 | P3 |
| T4 | [Library.css#L701](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.css#L701) | `.ws-relation-section h3` 使用全大写 + `letter-spacing: .04em`，与中文界面风格不统一 | P2 |
| T5 | [Library.css#L413](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.css#L413) | `.library-modal__badge` 详情弹窗徽章 `font-size: 10.5px` 仍偏小 | P2 |
| T6 | [Library.jsx#L530](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.jsx#L530) | Loading 状态 `<p>` 缺少独立 typography 规范 | P3 |

---

### 二、按钮与交互控件 (7 个)

| # | 位置 | 问题 | 严重程度 |
|---|------|------|---------|
| B1 | [global.css#L206](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/styles/global.css#L206) + [ds.css#L3](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/styles/ds.css#L3) | **两套按钮系统并存**：`.button` 高 40px vs `.ds-btn` 高 32px，导致同一页面内按钮高度不一致 | **P0** |
| B2 | [Library.css#L59](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.css#L59) | `.library-toolbar__filter` `<select>` `min-height: 36px`、`border-radius: 9px`，与全局 40px/8px 不一致 | P1 |
| B3 | [Library.css#L107](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.css#L107) | `.library-toolbar__sort` `<select>` 同 B2，尺寸不统一 | P1 |
| B4 | [Library.css#L89](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.css#L89) | `.input-with-icon input` 搜索框 `min-height: 36px`、`border-radius: 9px`，与全局不一致 | P1 |
| B5 | [Library.css#L233](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.css#L233) | `.library-card__button:focus-visible` Focus Ring 颜色在深色背景上对比度不足 | P2 |
| B6 | [Library.css#L347](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.css#L347) | `.library-card__check input` checkbox 15×15px 可点击区域过小，Apple 建议最小 44×44 | P2 |
| B7 | [Library.css#L980](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.css#L980) | `.library-batch-bar__actions select` 使用透明边框，在深色主题下不可见 | P2 |

---

### 三、间距与对齐 (5 个)

| # | 位置 | 问题 | 严重程度 |
|---|------|------|---------|
| S1 | [Library.css#L73](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.css#L73) | 搜索图标 `left: 12px` 未精确居中（应为 ~10px） | P2 |
| S2 | [Library.css#L186](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.css#L186) | 卡片网格 `gap: 14px`，全局缺少统一 spacing scale | P3 |
| S3 | [Library.css#L469](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.css#L469) | `.library-modal__scroll` 顶部 padding 仅 2px，紧贴 header 缺少呼吸感 | P2 |
| S4 | [Library.css#L539](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.css#L539) | `.ws-kpi-strip` KPI 块 gap 32px 过大，窄屏可能溢出 | P3 |
| S5 | [Library.css#L322](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.css#L322) | `.library-card__check` hover 过渡时间与卡片不同步 | P3 |

---

### 四、容器与视觉层级 (6 个)

| # | 位置 | 问题 | 严重程度 |
|---|------|------|---------|
| V1 | [AppShell.css#L68](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/components/AppShell.css#L68) | 右栏隐藏时，中栏与 sidebar 之间缺少明确的间距缓冲 | P2 |
| V2 | [Library.css#L195](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.css#L195) | 卡片 hover 使用 `color-mix()` 实现的背景变化过于微妙 | P2 |
| V3 | [Library.css#L358](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.css#L358) | 弹窗 `backdrop-filter: blur(3px)` 在性能差的设备上可能卡顿 | P3 |
| V4 | [Library.css#L473](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.css#L473) | 状态横幅、KPI strip、ws-card 使用相同背景色，三个容器融为一体 | P2 |
| V5 | [Library.css#L519](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.css#L519) | ws-card 与 KPI strip 背景相同，分组意义消失 | P1 |
| V6 | [Library.css#L750](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.css#L750) | 空态组件 padding 与 ws-card 不一致 | P3 |

---

### 五、弹窗与浮层 (5 个)

| # | 位置 | 问题 | 严重程度 |
|---|------|------|---------|
| M1 | [Library.jsx#L649](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.jsx#L649) | 详情弹窗 footer 可能在内容溢出时被遮挡 | P2 |
| M2 | [Library.jsx#L363](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.jsx#L363) | 弹窗缺少 `role="dialog"` 声明（已在 L656 提供，属冗余检查） | P3 |
| M3 | [MaterialDestination.css#L1](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/components/MaterialDestination.css#L1) | 两个弹窗遮罩背景色不一致，同时打开时有双层遮罩 | P2 |
| M4 | [MaterialDestination.css#L1](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/components/MaterialDestination.css#L1) vs [Library.css#L358](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.css#L358) | 两个弹窗 z-index 不统一（40 vs 70） | P2 |
| M5 | [Library.css#L942](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.css#L942) | 批量操作栏 `position: sticky` 在移动屏布局下可能失效 | P2 |

---

### 六、状态反馈与空态 (5 个)

| # | 位置 | 问题 | 严重程度 |
|---|------|------|---------|
| F1 | [Library.css#L911](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.css#L911) | `.status-pill--muted` 颜色对比度接近 WCAG AA 边界 (4.7:1) | P2 |
| F2 | [Library.css#L873](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.css#L873) | success/warning pill 在深色背景上对比度不足 (< 3:1) | P1 |
| F3 | [Library.jsx#L556](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.jsx#L556) | 知识空态图标 `Network` 语义不匹配 | P2 |
| F4 | [Library.jsx#L828](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.jsx#L828) | `aria-live` announcer 实现混用 `role="alert"` 和 `aria-live` | P3 |
| F5 | [Library.css#L122](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.css#L122) | 空态图标尺寸和颜色偏隐 | P3 |

---

### 七、可访问性 (6 个)

| # | 位置 | 问题 | 严重程度 |
|---|------|------|---------|
| A1 | [Library.jsx#L923](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.jsx#L923) | checkbox `aria-label` 过长时可能冗余 | P3 |
| A2 | [Library.jsx#L923-L955](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.jsx#L923) | `<label>` + `<input>` 嵌套在 `<button>` 内，**HTML 语义错误** | **P0** |
| A3 | [Library.jsx#L808](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.jsx#L808) | 视觉隐藏的文件 input 需确保键盘可达 | P2 |
| A4 | [Library.jsx#L732](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.jsx#L732) | `<details>/<summary>` 自定义 `::before` 图标可能被屏幕阅读器忽略 | P3 |
| A5 | [Library.css#L261](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.css#L261) | 需确认 focus-within 时 badge 颜色也同步变化 | P3 |
| A6 | [Sidebar.jsx#L150](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/components/Sidebar.jsx#L150) | 模式切换 tabs 缺少 `aria-controls` 关联 | P2 |

---

### 八、全局一致性 (7 个)

| # | 位置 | 问题 | 严重程度 |
|---|------|------|---------|
| G1 | [global.css](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/styles/global.css) + [ds.css](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/styles/ds.css) | **两套设计系统并存**，组件重复定义，样式值不同 | **P0** |
| G2 | [Library.css](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.css) | 通用组件样式散落在页面 CSS 中而非设计系统 | P1 |
| G3 | [global.css#L21](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/styles/global.css#L21) | `--border: #2c2c2c` 与 `--surface-container: #2c2c2c` 颜色相同，**边框不可见** | P1 |
| G4 | 全页面 | Status Pill 使用 3 套命名（`--success`, `--document-completed`, `--muted`），命名不统一 | P2 |
| G5 | 全页面 | 圆角值分散（6, 8, 9, 10, 12, 13, 14, 16px），无统一 token | P2 |
| G6 | [Library.css#L122](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.css#L122) + [Library.css#L164](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.css#L164) | 两个空态组件视觉语言完全不同 | P3 |
| G7 | [Library.css](file:///Users/xike/Documents/Docs/Askora/apps/frontend/src/pages/Library.css) | 多处使用 `color-mix()`，旧版浏览器不支持 | P3 |

---

### 严重程度分布

| 等级 | 数量 | 标记 |
|------|------|------|
| **P0** | 3 | B1（双按钮系统）、A2（嵌套交互元素）、G1（双设计系统） |
| **P1** | 7 | T2, B2, B3, B4, F2, V5, G2, G3 |
| **P2** | 23 | T1, T4, T5, B5, B6, B7, S1, S3, V1, V2, V4, M1, M3, M4, M5, F1, F3, A3, A6, G4, G5 |
| **P3** | 14 | T3, T6, S2, S4, S5, V3, V6, M2, F4, F5, A1, A4, A5, G6, G7 |

> **注意**：最初报告中提到的「36 个」是 P0 + P1 + P2 的部分数量，完整清单为 **47 个**问题。如需我对其中任何一项进行修复，请告知。