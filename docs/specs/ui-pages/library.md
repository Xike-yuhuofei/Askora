# 资料库（`/library`）

> **页面职责**：管理当前产品支持的 Material：导入、搜索/筛选、理解来源与解析状态，并从资料进入 material-grounded 学习。
> **对应旅程**：`EXP-JOURNEY-001`（放入资料→决定去向）、`EXP-JOURNEY-004`（往已有空间加资料）
> **对应契约**：`UI-LIB-001~005`、`UI-DS-COMP-020/021/022`、`UI-ROUTE-001`
> **现状基准**：`apps/frontend/src/pages/Library.jsx`（已中文、已空间语义；存在 OCR / 内部 code 暴露等冲突，见 §6 GAP）

---

## 1. 页面目标

1. 用户能**导入资料**（只创建 `Material`），看清处理状态（`仅本机解析 / 已用模型增强 / 本机已就绪·模型增强失败`）。
2. 用户能**搜索、筛选、批量管理**资料；选择后出现**上下文操作**（加入空间、归档、从这份资料开始学习）。
3. 处理完成后引导「资料去向」（`MaterialDestination`，见 material-destination.md）。

**不做什么**：不暴露 OCR action/状态/复核（v1 normal UI，`UI-LIB-003`）；不给大纲/知识图谱管理/错题本/Flashcards 建常驻 tab（`UI-LIB-004`）；不做成多 Dashboard。

## 2. 布局区划（`UI-LIB-002` 默认层级）

```
┌───────────────────────────────────────────────┐
│ eyebrow「资料库」+ h1「资料库」+ 一句说明            │
│ [导入资料 · primary]                            │
├───────────────────────────────────────────────┤
│ 搜索框 · 学科/状态/标签/集合/排序/视图 筛选           │
├───────────────────────────────────────────────┤
│ 资料列表（row/list）：                             │
│   标题 · 状态 pill · 解析模式标签                    │
│   行内：从这份资料开始学习 · 用模型再解析 · 归档       │
│ 已选 N 份 → 批量操作条                              │
├───────────────────────────────────────────────┤
│ 分页 · 总数「共 N 份资料」                          │
└───────────────────────────────────────────────┘
知识地图 / 原文检查 = 行内 Disclosure，不常驻。
「资料去向」= 上传后弹层（MaterialDestination）。
```

## 3. 元素清单

### 3.1 顶部与导入区

| # | 元素 | 类型 | 文案 | 交互语义 | 层级 | 组件/Token | 状态 |
|---|---|---|---|---|---|---|---|
| L-01 | eyebrow | 文本 | 资料库（移除现状英文「Canonical 资料投影」） | — | — | text-muted | — |
| L-02 | 主标题 | 文本 h1 | 资料库 | — | — | text-primary | — |
| L-03 | 说明 | 文本 | 导入私人学习资料。上传只创建资料，不会自动加入空间或开对话。 | — | — | text-secondary | — |
| L-04 | 导入资料 | 按钮（Upload icon） | 导入资料 / 上传中「正在上传…」 | **Action**（只创建 Material） | Primary | Button primary | DEFAULT/DISABLED(上传中)/LOADING |
| L-05 | 上传后去向 | 弹层 | 处理完成后自动唤起「资料去向」（加入学习空间 / 马上开始学习 / 稍后决定） | Action/Selection | Contextual | Sheet/Disclosure | 见 material-destination.md |

### 3.2 搜索 / 筛选区

| # | 元素 | 类型 | 文案 | 交互语义 | 层级 | 组件/Token | 状态 |
|---|---|---|---|---|---|---|---|
| L-10 | 搜索 | 输入（Search icon） | placeholder「输入资料中的关键词」 | Control | — | Input | DEFAULT/FOCUS/ERROR |
| L-11 | 学科筛选 | select | 学科（可选）· placeholder「精确筛选学科」 | Control | — | Select | — |
| L-12 | 处理状态 | select | 全部状态 / 等待处理 / 正在处理 / 处理完成 / 处理失败 / 已拒绝 / 已隔离 | Control | — | Select | — |
| L-13 | 标签 / 集合 | select | 按标签筛选 / 按集合筛选 | Control | — | Select | — |
| L-14 | 视图 / 排序 | select | 视图 · 排序 | Control | — | Select | — |

### 3.3 资料列表区

| # | 元素 | 类型 | 文案 | 交互语义 | 层级 | 组件/Token | 状态 |
|---|---|---|---|---|---|---|---|
| L-20 | 资料行 | row | 标题 + 类型 + 大小 + 时间 | InteractiveContent（打开/查看） | — | Row（`UI-DS-COMP-020/023`） | DEFAULT/HOVER/FOCUS/SELECTED |
| L-21 | 处理状态 pill | 状态标签 | 等待处理 / 正在处理 / 处理完成 / 处理失败 / 已拒绝 / 已隔离 | StatusFeedback | — | Badge（`UI-DS-COMP-040`） | 文本+语义，非仅颜色 |
| L-22 | 解析模式标签 | 状态标签 | 仅本机解析 / 已用模型增强 / 本机已就绪·模型增强失败 | StatusFeedback | — | Badge | `UI-LIB-005` 三态 |
| L-23 | 从这份资料开始学习 | 按钮 | 从这份资料开始学习 | Navigation（→ `/book-learning/:id`） | Secondary | Button secondary | DEFAULT/LOADING |
| L-24 | 用模型再解析 | 按钮 | 用模型再解析 | **Action**（同一 Material 的增强 run，`INT-MAP-004`） | Contextual | Button ghost | 仅「仅本机解析」且模型就绪时出现 |
| L-25 | 归档 / 恢复 | 按钮 | 归档 / 恢复 | Action（destructive/undo） | Contextual | Button ghost（danger 语义保留） | DISABLED/LOADING |
| L-26 | 总数 | 文本 | 共 N 份资料 | — | — | text-muted | — |

### 3.4 批量操作条（Selection 后出现，`INT-H-003` Contextual）

| # | 元素 | 类型 | 文案 | 交互语义 | 层级 | 组件/Token | 状态 |
|---|---|---|---|---|---|---|---|
| L-30 | 已选计数 | 文本 | 已选 N 份资料 | StatusFeedback | — | text-secondary | SELECTED |
| L-31 | 取消选择 | 按钮 | 取消选择 | Control（Selection） | Secondary | Button ghost | — |
| L-32 | 批量加标签/加入集合 | select | 批量加标签 · 加入集合 | Action（批量） | Contextual | Select/Button | DISABLED(未选) |
| L-33 | 归档所选 / 恢复所选 | 按钮 | 归档所选 / 恢复所选 | Action | Contextual | Button ghost | DISABLED(未选) |

### 3.5 知识地图 / 原文检查（上下文 Disclosure，`INT-005`）

| # | 元素 | 类型 | 文案 | 交互语义 | 层级 | 组件/Token | 状态 |
|---|---|---|---|---|---|---|---|
| L-40 | 知识地图展开 | Disclosure | 触发「查看知识地图」 | Disclosure | Contextual | Drawer/Sheet | LOADING「正在读取知识地图…」/EMPTY「暂无可展示的知识候选」/ERROR |
| L-41 | 原文检查 | Disclosure | 触发「查看原文」 | Disclosure | Contextual | Drawer/Sheet | LOADING「原页预览载入中…」/无片段「该节点没有可向学习者展示的原文片段。」 |
| L-42 | 关系说明 | 文本 | 尚无可核验的知识关系。页面不会用装饰性连线冒充先修关系。 | StatusFeedback | — | text-muted | 无关系时不伪装 |

## 4. 状态矩阵

| 区域 | LOADING | EMPTY | READY | PARTIAL | STALE | ERROR |
|---|---|---|---|---|---|---|
| 资料列表 | 骨架「正在读取你的资料库…」 | 「还没有符合条件的资料」+「可导入 Markdown、TXT、PDF、DOCX 或 EPUB。系统不会凭空补造资料事实。」 | 行列表 | 后台处理中：「后台处理进行中，资料状态会自动刷新。」 | — | 「资料库暂时无法读取。」+ 重试 |
| 知识地图 | 骨架 | 无候选 | 候选+依据数 | — | — | 「这份资料的知识地图暂时无法读取。」 |
| 批量操作 | 操作 LOADING | — | 可用 | — | — | 操作失败，保留选择 |

错误三要素：发生了什么 → 数据是否安全（本地资料不受影响）→ 现在能做什么（重试 / 导入）。

## 5. 无障碍

| # | 要求 |
|---|---|
| A-01 | 搜索/筛选输入均有 label 或 aria-label；占位符不替代 label（`UI-DS-COMP-050`）。 |
| A-02 | 资料行主点击区与行内按钮（开始学习/再解析/归档）为独立 focus target（`UI-DS-COMP-021/022`，不依赖 hover）。 |
| A-03 | 解析模式 / 处理状态有文本+语义表达，非仅颜色（`UI-DS-TOK-004`）。 |
| A-04 | 批量选择用 checkbox 语义；分页按钮 aria「上一页」「下一页」。 |
| A-05 | 弹层关闭后 focus 返回触发点（`UI-DS-COMP-072`）。 |

## 6. 禁止事项与现状 GAP

| GAP | 说明 | 处理 |
|---|---|---|
| OCR 暴露 | 现状含「识别扫描 PDF / OCR 复核 / 发布已复核文字」，违反 `UI-LIB-003` | v1 normal UI **移除 OCR action/状态/复核**；扫描 PDF 无可靠文本时显示 `unsupported / partial extraction` + 可行动建议 |
| 内部 code 暴露 | 现状出现 SYS06、OCR run、graph_version 等 | 移除/降级到高级 Disclosure；主文案用用户可读表达 |
| eyebrow 英文 | 「Canonical 资料投影」 | 改为中文「资料库」 |
| 延迟候选 tab | 不得为错题本/Flashcards/大纲建常驻 tab | 不新增 placeholder |

禁止：把处理失败/隔离伪装成已就绪；用文件名伪装原文；跨空间 source 引用泄露存在性（`UI-LRN-084`）；前端推断 mastery。
