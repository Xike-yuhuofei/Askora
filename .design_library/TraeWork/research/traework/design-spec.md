# Mac 桌面 AI IDE 界面设计审计

> 基于所提供的 1145 × 1299 px
> 截图进行视觉审计。截图可能经过缩放，因此以下尺寸为截图坐标系下的估算值，不能直接等同于
> macOS 的 pt。\
> 原则：无法从截图可靠确认的颜色、尺寸或交互均标记为「不确定」或「需补截图」。

## 1. 整体信息架构

### 1.1 一级结构

整个窗口可以拆成两个主要区域：

``` text
┌──────────────────────────────────────────────────────┐
│                    App Window                        │
├───────────────┬──────────────────────────────────────┤
│               │                                      │
│ Left Sidebar  │          Main Workspace              │
│               │                                      │
│ ≈ 302 px      │          弹性填充                    │
│               │                                      │
└───────────────┴──────────────────────────────────────┘
```

截图中没有出现传统 IDE 常见的右侧 Inspector / AI Panel / Terminal
Panel。

### 1.2 左侧 Sidebar

从上到下约分成 6 层。

#### A. Window / Global Controls

顶部约 50--55 px：

``` text
● ● ●    [布局]    [搜索]
```

职责：

-   macOS Window Controls
-   Sidebar / Layout 控制
-   全局搜索

这里同时承担了一部分传统 Title Bar / Toolbar 职责。

#### B. Workspace Mode Switcher

``` text
Work    Code    Design
```

属于一级工作模式导航。

当前：

-   `Code` Active
-   Work / Design Inactive

从产品架构看，它不是普通 Tab，而更接近 **Workspace-level Mode
Switcher**。切换后预计会改变整个左栏和主工作区的信息架构。

#### C. Primary Actions

包括：

-   新建任务
-   插件市场
-   自动化
-   办公助理
-   模板库

这里属于全局功能入口。

`新建任务`具有明显的 Hover / Active Surface，同时显示快捷键
`⌘ ^ N`，说明支持快捷键。

#### D. Pinned

``` text
置顶
  └─ 生成 Askora 学习消息系统 HTML 预...
```

职责：用户主动固定的高频任务 / 会话。

与下面的任务列表在信息模型上分离。

#### E. Task List

``` text
任务列表
  ├─ Askora
  │   ├─ 上传可复用资产到 Figma
  │   ├─ Figma MCP 像素级复制图片
  │   ├─ 截取 TraeWork 应用界面
  │   └─ ...
  │
  ├─ 默认
  │   └─ ...
  │
  ├─ DeepTutor
  │   └─ ...
  │
  └─ Nexus
      └─ ...
```

这是明显的 **Folder → Task / Conversation** 两级树结构。

这里实际上同时承担：

-   项目导航
-   会话历史
-   Task Manager

三个职责。

#### F. Account / Utility

左下：

``` text
Avatar   稀客  Pro                     [Device?]
```

属于固定 Footer，不随中间任务列表滚动。

### 1.3 Main Workspace

Main 可以拆成：

``` text
┌─────────────────────────────────────┐
│                                     │
│          Flexible Empty Space       │
│                                     │
│        Code with TRAE               │
│                                     │
│     ┌─────────────────────────┐     │
│     │ Composer                │     │
│     │                         │     │
│     ├─────────────────────────┤     │
│     │ Context Bar             │     │
│     └─────────────────────────┘     │
│                                     │
│       Suggestion Chips              │
│                                     │
│          Flexible Space             │
│                                     │
└─────────────────────────────────────┘
```

主内容没有顶栏，而是直接把 Composer 作为视觉焦点。

------------------------------------------------------------------------

## 2. 布局模型

截图左侧分界线约位于 `x = 301–302 px`。

  区域               截图估算 模型
  ---------------- ---------- -------------
  Sidebar             ≈302 px 固定/可调宽
  Main                ≈843 px Flex `1fr`
  Sidebar : Main     ≈26 : 74 ---

### Sidebar

视觉上更接近：

``` text
width: ≈ 300px
min-width: 不确定
max-width: 不确定
```

是否存在可拖拽分割条：**需补截图**。

目前只能看到背景边界，没有看到明确 Drag Handle。

### Main Workspace

Composer：

-   左边约 x=320
-   右边约 x=1119
-   宽约 799 px
-   相对 Main 两侧约 18--20 px margin

所以这里很可能是：

``` text
Main
 └─ Content Container
      width: calc(100% - 32/40px)
```

而不是固定 `max-width: 800px`。

------------------------------------------------------------------------

## 3. Design Token

### 3.1 Color

以下 Hex 是根据截图像素表现进行的近似归纳，不代表源码 Token。

  Token              估算值                    用途                          可信度
  ------------------ ------------------------- ----------------------------- --------
  `bg.window`        `#F5F5F5` 附近            Sidebar / App 外层背景        中
  `bg.main`          `#FFFFFF` 附近            Main Workspace                高
  `bg.surface`       `#FFFFFF`                 Composer                      高
  `bg.subtle`        `#F5F5F5` 附近            Composer Context Bar          中
  `bg.hover`         `#E7E7E7` 附近            新建任务 Hover/Active         中
  `text.primary`     `#1F1F1F` 附近            主文字                        中
  `text.secondary`   `#666666` 附近            次级文字                      中
  `text.tertiary`    `#8A8A8A` 附近            Placeholder / Section Label   中
  `text.disabled`    不确定                    禁用态                        低
  `border.default`   `#E1E1E1` 附近            Composer / Chip               中
  `accent.primary`   紫色，约 `#5B3FF5` 一带   Send / AI 主操作              低
  `accent.soft`      淡紫                      Pro / AI icon                 低
  `hover.generic`    不确定                    普通导航 Hover                低
  `active.generic`   `#E7E7E7` 附近            Selected item                 中

色彩体系判断：

> **Neutral Gray + White Surface + Purple Accent**

整体强调色使用非常克制，紫色基本只用于 AI、Send、Pro、特殊能力入口。

### 3.2 Typography

中文表现很像 macOS 系统 UI 字体栈，但仅凭截图无法确认具体
`font-family`。

  Token                  估算
  ---------------------- --------------------------------
  UI Font                系统无衬线；具体字体不确定
  Code Font              截图没有足够代码文本，需补截图
  Sidebar Body           ≈14 px
  Section Label          ≈13--14 px
  Shortcut               ≈11--12 px
  Composer Placeholder   ≈14 px
  Hero Title             ≈34 px
  Hero Title Weight      500--600
  Sidebar Weight         400
  Active Tab             500 左右
  常规 Line Height       ≈20--22 px
  Hero Line Height       ≈40 px

`Code with TRAE` 有明显字号层级，其中 `Code with` 更粗，`TRAE`
稍轻，形成同一标题内部的视觉层级。

### 3.3 Spacing System

从大量间距关系判断：

> **基础 Grid 很可能是 4 px，而主要布局大量使用 8 px 倍数。**

  Token      推测
  ------- -------
  XS         4 px
  S          8 px
  M         12 px
  L         16 px
  XL        24 px
  2XL       32 px

尤其明显的是：

-   Icon → Label：约 8 px
-   Sidebar 左 Padding：约 20 px
-   Tree indent：约 24 px
-   Chip 内 Padding：约 12--16 px
-   Section vertical gap：约 16--24 px

因此不建议简单定义成"纯 8pt Grid"。

更准确是：

> **4pt primitive grid + 8pt dominant rhythm。**

### 3.4 Radius / Border / Shadow / Icon

  Token                                     估算
  ------------------------ ---------------------
  Window Radius                       ≈14--16 px
  Composer 外层 Radius                    ≈16 px
  Button Radius                        ≈8--10 px
  Suggestion Chip Radius              ≈10--12 px
  Send Button Radius                   ≈9--10 px
  Border                                   ≈1 px
  Divider                                  ≈1 px
  Sidebar Active Radius                 ≈7--8 px
  常规 Icon                               ≈16 px
  小 Icon                             ≈12--14 px
  Send Icon/Button                 Button ≈34 px
  Window Shadow                     截图无法判断
  Composer Shadow            基本没有明显 Shadow

一个重要特征：

> **该 UI 主要依赖 Border + Background Layering，而不是 Shadow
> 建立层级。**

------------------------------------------------------------------------

## 4. 组件清单

### 4.1 Window Controls

**Variants**

-   Close
-   Minimize
-   Zoom

关键尺寸：

-   Dot ≈14 px
-   间距 ≈9--10 px

状态：

-   Default
-   Hover
-   Pressed

Hover 状态：**需补截图**。

### 4.2 Mode Segmented Control

``` text
Work | Code | Design
```

Variants：

-   Text-only
-   Active Surface

States：

-   Default
-   Hover
-   Active
-   Pressed

关键尺寸：

-   高约 32 px
-   Horizontal padding ≈10--12 px
-   Radius ≈7--8 px

### 4.3 Sidebar Navigation Item

结构：

``` text
[Icon] Label                [Shortcut]
```

Variants：

-   Icon + Label
-   Icon + Label + Shortcut
-   Selected
-   普通

关键尺寸：

-   Row height ≈38--40 px
-   Icon ≈16 px
-   左右 Padding ≈12 px

### 4.4 Section Header

例如：

``` text
置顶⌄
任务列表⌄                [Action][Filter]
```

Variants：

-   Label + Chevron
-   Label + Chevron + Actions

状态：

-   Expanded
-   Collapsed
-   Hover

### 4.5 Tree Folder

``` text
[Folder] Askora
```

Variants：

-   Expanded
-   Collapsed

子项使用 indentation 表达层级。

估算：

``` text
Level 0 ≈20px
Level 1 ≈44px
```

即约 **24 px / level**。

### 4.6 Task / Conversation Item

Variants：

-   Normal
-   Pinned
-   Selected
-   Hover
-   Truncated

当前大量项目使用：

``` text
single-line + ellipsis
```

没有 secondary metadata。这是明显的高密度历史记录设计。

### 4.7 Composer

这是整个页面最重要的复合组件。

内部：

``` text
Composer
├── Text Input
│
├── Action Row
│   ├── Add
│   ├── Attachment / Context Icons
│   ├── Model Selector
│   ├── Voice
│   └── Send
│
└── Context Bar
    ├── Environment Selector
    └── Project Selector
```

估算：

-   Width ≈800 px
-   总 Height ≈173 px
-   上层输入区 ≈127 px
-   Context Bar ≈45 px
-   Radius ≈16 px

States：

-   Empty
-   Typing
-   Focus
-   Generating
-   Disabled
-   Drag-over

其中只有 **Empty** 能从当前截图确认。

### 4.8 Icon Button

用于：

-   Search
-   Layout
-   Add
-   Voice
-   Send
-   Filter
-   List action

Variants：

-   Ghost
-   Subtle
-   Primary

Primary = 紫色 Send。

建议在逆向 Design System 中不要把这些分别建组件，应统一：

``` text
IconButton
 ├─ appearance
 ├─ size
 ├─ state
 └─ icon
```

### 4.9 Select / Dropdown Trigger

例如：

``` text
Kimi-K2.7-Code ⌄
本地 ⌄
Askora ⌄
```

Variants：

-   Text + Chevron
-   Icon + Text + Chevron

状态：

-   Default
-   Hover
-   Open
-   Disabled

### 4.10 Suggestion Chip

``` text
[icon] 应用开发
[icon] 项目理解
[icon] 游戏创意
[icon] 工具脚本
```

关键尺寸：

-   Height ≈38 px
-   Radius ≈11 px
-   Horizontal padding ≈13 px
-   Gap ≈8 px

States：

-   Default
-   Hover
-   Pressed

### 4.11 Account Badge

``` text
Avatar + Name + Pro Badge
```

独立固定于 Sidebar Footer。

------------------------------------------------------------------------

## 5. 交互与动效

这里只能从界面结构推导合理的交互模型，不能确认具体 duration / easing。

### Sidebar 展开 / 折叠

至少存在两个层级：

``` text
任务列表
    ↓
Folder
    ↓
Task
```

Chevron 明确暗示：

``` text
Expanded ↔ Collapsed
```

预计使用高度/内容 Reveal，而非页面跳转。

具体动效：**需补截图或录屏**。

### Folder 展开

例如：

-   Askora
-   默认
-   DeepTutor
-   Nexus

应支持：

-   点击 Folder row
-   Chevron rotate
-   Children reveal/hide

是否支持以下行为均无法确认：

-   Drag reorder
-   Drag task between folder
-   Context Menu

### Sidebar Resize

从桌面 IDE 产品惯例判断存在较高可能性，但截图没有 Resize Handle 证据。

**需补截图。**

### Mode Tab

`Work / Code / Design`

预计属于 Workspace-level transition。

切换时可能：

``` text
Sidebar IA
+
Main Workspace
```

一起改变。

不能把它理解成普通网页 Tab。

### Composer

预计存在：

``` text
Empty
↓
Focus
↓
Typing
↓
Submit
↓
Generating
↓
Response
```

发送后首页 Hero：

``` text
Code with TRAE
Suggestion Chips
```

很可能退出或消失，进入 Conversation Workspace，但当前截图无法证明。

### 消息出现

当前完全没有消息态。

无法判断：

-   Streaming token animation
-   Loading indicator
-   Thinking state
-   Tool call
-   Diff
-   Code block
-   Artifact
-   Error state

**全部需补截图。**

------------------------------------------------------------------------

## 6. 不确定项 / 需补截图

如果目标是把这个 UI 真正逆向成完整 Design
System，目前这张截图主要只能覆盖 **Home / Empty State**。

优先补以下截图：

1.  **Sidebar Hover / Selected / Context Menu**：确认
    Hover、Active、Menu、拖拽以及 Folder 展开状态。
2.  **Composer Focus + 输入文字**：确认 Focus Border、Caret、输入
    typography、multi-line 高度变化。
3.  **模型下拉菜单展开**：确认 Dropdown/Menu 的
    radius、shadow、spacing、selected state。
4.  **点击「+」后的菜单**：确认 Popover 系统。
5.  **发送消息后的完整 Code Workspace**：确认真正 IDE 的核心 IA。
6.  **AI 正在生成 / Tool Call / 完成状态**：确认
    Streaming、Loading、Stop、错误状态。
7.  **Work / Design 页面**：判断三种 Mode 是否共享 Shell。
8.  **Sidebar 缩窄 / 拉宽**：确认是否 Resize、min/max width。
9.  **Dark Mode**：用于建立完整 Semantic Color Token。
10. **代码编辑器 / Terminal / Diff 页面**：当前截图几乎没有暴露 IDE 的
    Editor Design System。

------------------------------------------------------------------------

## 7. 结论

这张界面的设计逻辑可以概括为：

> **固定 Sidebar + 弹性 Workspace + 中央任务 Composer + Tree-based Task
> Navigation。**

视觉系统明显倾向：

> **4px 基础网格、8px 主节奏、低对比中性灰阶、1px Border
> 建层级、少阴影、中等圆角、紫色单一 Accent、系统级 Typography。**

---

## 8. 深色主题实测附录（2026-08-12，以 DDEA39E7 PNG 为准）

> 前文基于一张浅色截图的审计已作废。以下为深色参考图（1326×1299）的逐像素实测值，
> 复刻实现见 `app/globals.css` 与 `components/trae/*`。

### 8.1 实测色板

| Token | 值 | 用途 |
| --- | --- | --- |
| frame | `#222222` | 窗口框 + 侧边栏背景 + Composer 上下文栏 |
| main | `#171717` | 主工作区卡片 / Composer 输入区 / 模式激活 pill 填充 |
| edge-top | `#595959` | 窗口顶部 1px 高亮线 |
| border-card | `#2c2c2c` | 主卡片描边 / 侧栏分隔线 / 行 hover / 模式轨道 / 设备按钮 |
| border-composer | `#383738` | Composer 与 Chip 描边 |
| border-pill | `#3f3f3f` | 模式激活 pill 描边 / Chip 描边（与 composer 极接近） |
| iconwell | `#252525` + 边 `#383838` | Composer 媒体图标组底板 |
| text-1 | `#dedede` | 导航 / 任务 / 主要文本 |
| text-2 | `#6f6f6f` | 文件夹名 |
| text-3 | `#5c5c5c` | 分组标签（置顶 / 任务列表） |
| text-4 | `#4a4a4a` | 快捷键 glyph |
| placeholder | `#5b5e66` | Composer 占位文本 |
| hero | `#e1e1e1` | 大标题 / 上下文栏文本 |
| model | `#9a9a9a` | 模型选择器文本 |
| send | `#3e36db` | 发送按钮（纯色非渐变） |
| icon-violet / icon-orchid | `#8a63f6` / `#a55ede` | 媒体组视频 / 图片图标 |
| badge | bg `#2c2d47` / text `#8f89f0` | Pro 徽标 |
| 红绿灯 | `#000000` 纯黑圆点 | 非彩色，14px，间距 23px |

### 8.2 实测几何（px，1326×1299 视口）

- 侧边栏：宽 301 + 1px 分隔线；标题栏 62；红绿灯圆心 y≈30
- 模式切换器：轨道 x12 w194 h32 bg `#2c2c2c`；激活 pill 内缩 2px，fill `#171717` + 1px 边
- 主导航行：pitch 40，高亮行 h34（x12–288，radius 7）
- 分组标签 h24；置顶/任务行 h34；文件夹行 h35；任务行 h34；任务文本缩进 x=44
- 账户栏 h58 贴底；头像 24px 白底圆角方块
- 主卡片：内嵌 top 3 / right 8 / bottom 4，1px 边 `#2c2c2c`，radius 10
- Hero：中心 (810, 468)，`</>` 图标约 31px + 文本 33px，色 `#e1e1e1`
- Composer：x410 w800，y537 h172，radius 12，边 `#383738`；
  输入区 127（同主背景）+ 上下文栏 44（`#222222`，顶部分隔线）；
  发送钮 32×32 `#3e36db` radius 8，白色波形图标
- Chips：h38，px≈14，gap 12，边 `#3f3f3f`，整体居中于 x=810
- 正文字号：侧栏 13.5px（实测 CJK 宽度反推），分组标签 12，Chip 13，模型选择器 12

### 8.3 复刻验证

Playwright headless 截图（1326×1299, dsf=1）+ PIL 像素 diff：
整体 meanErr ≈ 2.1，badPx ≈ 2.7%，残差集中在文本抗锯齿光栅化（字体栈无法与原生完全一致）。
产物：`outputs/replica.png`、`outputs/side_by_side.png`、`outputs/diff_heatmap.png`。

---

## 9. Chat 会话界面实测附录（2026-08-13，以 `TraeWork-chat.png` 为准）

> 这是一张与首页不同的界面：同一 shell 下的「chat 会话视图」。以下为 1326×1299
> 逐像素实测值，复刻实现见 `components/trae/chat/*` 与 `lib/trae-chat-data.ts`。

### 9.1 与首页的差异

- Sidebar、红绿灯、模式切换器、任务树、账户栏：与 §8 **完全一致**，直接复用。
- main card 内嵌：top **8** / right **8** / bottom **8**（首页为 top 3 / right 8 / bottom 4）。
- Composer 底部 context bar 背景：**#2c2c2c**（首页为 #222222）。

### 9.2 主区结构（自上而下）

1. **标题栏**：任务名「上传可复用资产到 Figma」（y≈26，#e1e1e1）+ 时间「昨天 18:45」（灰）
   + 右侧按钮「在 [app 图标] 中打开」（x 1109..1258，1px 边框 #29292b，radius≈6）。
2. **消息流**（AI 内容左对齐 x≈444，行高≈22）：
   - AI 消息：文字 #e1e1e1；上方常带元信息行（灰 #5f5f5f，如「已读取2个文件，搜索1次文件」「已调用8次 MCP」）。
   - 工具调用块：绿色图标 **#59b589**（x≈450）+ 文字 #e1e1e1，行尾「＞」。
   - 状态行：灰图标 #777777 + 文字（如「任务暂停，正在处理新请求」「已切换到新请求」「思考过程」）。
   - 用户消息：右侧气泡 bg **#222222**（x≈816 起，radius≈8，文字 #e1e1e1）；
     被新请求覆盖的旧用户消息显示为灰文字 #a9a9a9、无气泡。
   - 引用块：「TraeWork」「参考内容」。
3. **底部 Composer**（x 420..1199，顶部边框 y=1136 #383738）：
   - 占位文字「帮你编写代码、调试 Bug、优化性能等开发工作，交付生产级代码产物。」（#5b5f69）。
   - action 行：+ 按钮、媒体图标组（视频 #8a63f6 / 图片 #a55ede，well bg #252525 边 #383838）、
     模型选择器「Kimi-K2.7-Code」（#979797）、发送按钮 32×32 **#3e36db**（x 1155..1186）。
   - context bar #2c2c2c（y=1290）。
4. **消息区底部**：「手动终止输出」按钮 + 右下角「由AI生成」标注（#3f3f3f）。

### 9.3 新增 / 变更 token

| Token | 值 | 用途 |
| --- | --- | --- |
| tool-green | #59b589 | 工具调用完成图标 |
| user-bubble | #222222 | 用户消息气泡背景 |
| ctxbar-chat | #2c2c2c | Composer context bar |
| btn-border | #29292b | 标题栏「在…中打开」按钮边框 |
| placeholder-chat | #5b5f69 | 输入框占位文字 |

### 9.4 复刻验证

chromium headless（1326×1299）+ PIL 像素 diff：
整体 meanErr ≈ 5.5，badPx ≈ 5.8%。残差主要为中文文本抗锯齿光栅化（与 §8 首页一致，
sidebar 单独 badPx 与首页复刻完全相同 ≈6.6%）；主区结构与配色已逐像素对齐。
产物：`outputs/replica.png`、`outputs/side_by_side.png`、`outputs/diff_heatmap.png`（已覆盖 chat 视图）。

