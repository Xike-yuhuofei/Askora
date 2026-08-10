# Askora UI Visual System Specification

> Spec ID：`UI-VIS-*`
> 状态：`FROZEN`
> Governing：`ADR-0014`、`UI-IES-*`、`UI-IA-*`
> 参考资产：`.design_library/Askora/`（supporting asset，不是实现合同）

## 1. 视觉目标

### UI-VIS-001 — Calm, Precise, Focused

Askora 的工作界面应安静、精确、聚焦，优先支持阅读、推理、作答和证据审查。视觉不能用大面积装饰、游戏化奖励或情绪化文案抢占学习任务注意力。

### UI-VIS-002 — Native-feeling macOS

桌面目标 SHOULD 接近 macOS 原生应用的信息密度与层级：系统字体、轻量分隔、克制阴影、清晰 focus 和稳定窗口区域。MUST NOT 伪装成系统设置或使用未经授权的 Apple 商标资产。

### UI-VIS-003 — Data Honesty

视觉层次不得夸大数据确定性。估计、置信度、证据不足、兼容数据与系统失败必须通过文案和结构明确表达，而不是只改变颜色。

### UI-VIS-004 — Semantic Before Component

任何视觉组件选择 MUST 先满足 `UI-IES-*` semantic role。

禁止：

```text
先选择 Card/Button/Badge
→ 再为其寻找功能
```

正式顺序：

```text
Semantic Primitive
→ Hierarchy
→ Platform Pattern
→ Visual Component
```

## 2. 产品语言

### UI-VIS-010 — Voice

界面语言使用简洁中文，语气专业、克制、可行动。Action 优先使用明确动词，例如：继续学习、开始复习、查看证据、重试、退出。

### UI-VIS-011 — Terminology

用户界面 SHOULD 使用：

| 内部术语 | 用户文案 |
|---|---|
| LearningActivity | 学习活动 |
| ReviewDue / next_due_at | 复习建议 / 建议复习时间 |
| Evidence sufficiency | 证据充分度 |
| Independent validation obligation | 待独立验证 |
| Assistance state | 独立作答 / 使用帮助 / 已看到答案 |
| Confidence | 估计置信度 |
| SourceSpan | 引用位置 / 原文位置 |
| Evidence workspace | 进展 |

工程标识 MAY 出现在审计详情，不得成为主页面文案。

### UI-VIS-012 — No Decorative Emoji

正式产品 UI 不使用 emoji 作为导航、学科、状态或空态主图标。统一使用 Lucide outline icon 或纯文本。用户生成内容中的 emoji 不受此限制。

## 3. Color Tokens

### UI-VIS-020 — Light Theme

建议基础 token：

```text
brand-primary            #007AFF
brand-primary-soft       #EAF3FF
canvas                   #F2F2F7
surface                  #FFFFFF
surface-container        #F7F7FA
surface-container-high   #E5E5EA
text-primary             #1C1C1E
text-secondary           #636366
text-muted               #8E8E93
border                   #E5E5EA
success                  #248A3D
warning                  #C93400
error                    #D70015
info                     #007AFF
```

颜色值 MAY 经对比度验证微调，但 semantic mapping 不得改变。

### UI-VIS-021 — Dark Theme

目标 dark tokens：

```text
canvas                   #0B0B0D
surface                  #1C1C1E
surface-container        #2C2C2E
surface-container-high   #3A3A3C
text-primary             #F5F5F7
text-secondary           #D1D1D6
text-muted               #98989D
border                   #3A3A3C
brand-primary            #0A84FF
```

暗色模式不得只反转颜色；公式、代码、引用、状态色、hover、focus 与 disabled 均需独立验证。

### UI-VIS-022 — Color Use

系统蓝只用于主要交互、active navigation 和必要 focus。Success/warning/error 只表达相应语义，不用于装饰。大面积渐变、霓虹、彩色学科卡片与每节点不同颜色默认禁止。

## 4. Typography

### UI-VIS-030

字体栈：

```css
-apple-system, BlinkMacSystemFont, "SF Pro Text", "PingFang SC",
"Microsoft YaHei", "Helvetica Neue", Arial, sans-serif
```

代码/标识符：

```css
"SF Mono", Menlo, Monaco, Consolas, monospace
```

### UI-VIS-031

工作界面以 12～16px 为主要文字范围；页面标题 SHOULD 20～28px。正文行高至少 1.5。不得为追求信息密度把关键正文、状态或交互标签缩小到 11px 以下。

### UI-VIS-032

标题层级必须语义化，不得只靠字重/尺寸模拟。每个页面只有一个 `h1`；任务区、Inspector 使用后续 heading level。

## 5. Spacing, Radius and Elevation

### UI-VIS-040

采用 4px 基础网格，常用间距 8/12/16/24/32px。布局 SHOULD 通过 spacing、section 和 background layers 分组，避免每个区域都加独立边框和阴影。

### UI-VIS-041

建议 radius：

- 8px：输入、紧凑控件；
- 12px：必要的标准 card；
- 16px：消息、主任务容器；
- full：avatar、短 status tag。

### UI-VIS-042

阴影仅用于真正浮动的 popover/modal 或必要 hover elevation。常规 content region 默认不使用重阴影。

## 6. Interaction Hierarchy Visualization

### UI-VIS-050 — L0/L1 Difference

L0 Product Navigation（Today/Learning/Library）与 L1 Learning facets（Goal/Plan/Progress/History）MUST 有清晰层级差异。

不得通过相同 Sidebar row weight 把 L1 再伪装成 L0。

### UI-VIS-051 — Primary Task

页面主任务必须通过位置、heading、spacing 和一个 Primary Action 建立层级；不得依赖“大蓝 Card”单独表达重要性。

同一任务区域最多一个 primary intent。

### UI-VIS-052 — Secondary / Contextual

Secondary、Contextual、Advanced action 的视觉权重必须依次降低。

低频 Action SHOULD 使用 ghost/menu/contextual toolbar 等 quiet pattern，而不是大量常驻 secondary buttons。

## 7. Core Components

### UI-VIS-060 — Buttons

至少支持 primary、secondary、ghost、danger intent。

Button 只用于 `Action` 或 `Control`。普通 destination / domain content 不得仅因为可点击就统一做成 Button。

每个局部动作组最多一个 primary。Icon-only button 必须有 accessible label；disabled 必须同时有语义属性和视觉状态。

### UI-VIS-061 — Navigation

Active Product Domain 使用稳定的 active treatment。Hover、focus 与 active 必须有区别；不得使用渐变 active background。

Settings/Recovery 等 App Utility 与 Today/Learning/Library MUST 有视觉分组，不得伪装成第四个 Product Domain。

### UI-VIS-062 — Rows and Lists

重复 domain object 默认使用 row/list：

- goals；
- activities；
- documents；
- history；
- sessions。

Row 可包含 Status 和少量 trailing/contextual action，但不得演变成每行多个永久主按钮。

### UI-VIS-063 — Cards

Card 只用于需要明确边界的：

- 当前主任务；
- typed rich response；
- evidence summary；
- recovery issue；
- 少量 option。

禁止“所有 section 一张 Card”“所有 object 一张 Card”“Card = Entry”的默认映射。

### UI-VIS-064 — Status and Badges

Badge 只表达短状态，如“待独立验证”“到期复习”“兼容数据”。长解释放正文/tooltip/Inspector。状态不得只用颜色编码。

Badge 默认不是 Action；若可交互，必须有独立 Navigation/Disclosure affordance 和 accessible role。

### UI-VIS-065 — Empty, Loading and Error

- Loading：与最终布局一致的最小 skeleton 或明确进度；
- Empty：说明缺少对象与可用下一步；
- Error：显示可理解信息、retry action（仅 retryable）和需要时的 correlation detail；
- Partial/Stale：保留可用内容并在数据区域显示来源状态。

## 8. Today-specific Components

### UI-VIS-070 — Primary Activity

Today 的 canonical activity 是首屏唯一 Primary Task。

推荐呈现应优先使用开放 section 或单一主任务 container；Quick Start、History、完整 Path 不得使用同等尺寸/颜色/按钮等级与其竞争。

### UI-VIS-071 — Activity Summary

Activity summary 显示 title、type、预计时间、status 与 reason summary。不得显示前端计算的“学习价值分”“掌握增益”或未校准百分比。

## 9. Learning-specific Components

### UI-VIS-080 — Facet Navigation

Goal/Plan/Progress/History 使用 L1 local navigation pattern。桌面可用 secondary sidebar/segmented/tab；窄屏可用 navigation stack/menu。

四个 facet 不得通过四张等权 Dashboard Cards 作为默认 landing replacement。

### UI-VIS-081 — Evidence Summary

Evidence summary 优先使用有名称的计数与文字：

```text
独立成功 2 次
延迟证据 1 次
迁移证据 暂无
估计置信度 中等
```

若只存在数值 confidence，UI MAY 显示格式化数值，但不得无规则映射为“高/中/低”。

### UI-VIS-082 — Probability Visualization

`competence_probability` 是估计。若用 bar/ring，必须同时显示“估计”与 confidence/evidence context；不得用红黄绿 threshold 表达 mastered/unmastered。

### UI-VIS-083 — Validation Obligation

“待独立验证”使用清晰、非惩罚性的 neutral/warning status。它不是错误、失败或 mastery label。

### UI-VIS-084 — Assistance Control

帮助控件按用户可理解的支持类型命名，例如“方向提示”“解释概念”“拆成子步骤”。不可用状态必须解释规则限制，而不是通过隐藏控件制造不可发现性。

## 10. Library-specific Components

### UI-VIS-090 — Contextual Management

Library 默认视觉应围绕 Search/Filter、Import、Document List、Selected Document/Knowledge Context。

批量 Action 在 selection 后出现 contextual toolbar；OCR、duplicate、metadata advanced action 放在 selected document context / inspector / menu。

禁止永久显示大型 batch management panel 作为默认页面核心。

### UI-VIS-091 — Knowledge Map

Node 默认使用中性 surface。Current、published/candidate、selected 与 evidence status 使用有限的形状、边框和文字组合。关系方向必须可辨；无可靠 relation 时不得绘制装饰性连接线。

## 11. Settings-specific Components

### UI-VIS-100 — Hierarchical Settings

Settings landing 默认使用 category row/list，而不是把数据、删除、恢复、模型、安全全部铺为 Cards。

Destructive action 不得依靠红色大 Card 提升发现性；应在正确 category 内通过清晰文案与 danger action 表达。

### UI-VIS-101 — Runtime Status

正常 runtime state SHOULD 安静呈现或不占主层级；action-required/degraded state 才提升视觉权重。

## 12. Rich Message Integration

### UI-VIS-110

继续使用已冻结 typed card：concept、hint、question、feedback、source。视觉区别 SHOULD 克制，并且不改变 `RENDER-*` schema。

### UI-VIS-111

Assistant message 不强制包裹成聊天气泡。长解释 MAY 使用开放内容列，用户短消息 MAY 使用紧凑 bubble；无论布局如何都必须保持 message identity、顺序与 fallback。

### UI-VIS-112

Citation block 默认显示用户可读 label/locator，内部 source_span_id 可放可复制详情，不作为视觉主标签。

## 13. Motion

### UI-VIS-120

Motion 只用于状态连续性：navigation transition、Inspector 展开、list reordering、stream status。动画 SHOULD 150～250ms，并遵守 `prefers-reduced-motion`。不得使用循环闪烁、庆祝动画或基于 mastery 的游戏化效果。

## 14. Accessibility and Contrast

### UI-VIS-130

普通文字、关键图标、输入边界和 focus 必须满足适用 WCAG AA 对比度。Placeholder 与 disabled 仍需可辨，但不得替代 label。

### UI-VIS-131

Touch target SHOULD 至少 44×44 CSS px；桌面紧凑控件 MAY 36px，但必须有足够间距且键盘可达。

### UI-VIS-132

知识地图、progress、evidence chart 必须提供文本等价信息，不能要求用户仅通过空间位置或颜色理解状态。

### UI-VIS-133 — Contextual Action Discoverability

Hover-only action 禁止。Contextual Action 必须在 keyboard focus / touch / More Menu / Context Menu 中存在等价入口。

## 15. UX Architecture Visual System (ADR-0018)

本节冻结 `UX-Architecture-Canonical-Design-Delta.md` 经 `ADR-0018` 吸收后的三栏/Workspace/Drawer/右栏视觉约束。

### UXA-VIS-00 — Three-Column Hierarchy

三栏职责（Where / Learn / Reference）在视觉上 MUST 可辨且稳定：

- 左栏（Where）为稳定产品导航 + Workspace 上下文，视觉层级低于中栏；
- 中栏（Learn）是唯一 Primary Learning Canvas，视觉权重最高，不得被 Dashboard widget 竞争；
- 右栏（Reference/Notes）为可隐藏辅助栏，视觉安静，不承担主任务。

单一 Workspace 不得显示虚假 selector/dropdown affordance。

### UXA-VIS-01 — Workspace Switching Feedback

Workspace switch / autosave 状态（`saved / saving / failed / recoverable`）使用 `StatusFeedback` + live region，区分于普通 navigation active state。未持久化时不得显示"已保存"。

### UXA-VIS-02 — Context Drawer

Drawer 收起时只显示一行方向信息；展开时显示 stage / stage goal / next 1..3。视觉上它归属中栏 composer，不是第四条栏，也不占右栏。展开/收起只反映 presentation state。`MISSING / PARTIAL / STALE` 使用诚实 unavailability 表达，不得伪装 READY。

### UXA-VIS-03 — Right Rail Honesty

右栏隐藏时不得隐藏完成任务所需的唯一引用、帮助状态或 validation obligation。已存/未存笔记状态视觉可辨。Current Material 缺失 SourceSpan 时诚实显示不可用，不得用 filename-as-original 冒充。

### UXA-VIS-04 — Library No-OCR

Library v1 正常 UI 不出现 OCR 入口/状态/review/confidence/bbox/hash 视觉元素。扫描 PDF 诚实显示 `unsupported / partial extraction` 与建议，不显示 OCR 进度或候选。

### UXA-VIS-05 — Deferred Candidates

大纲、Evidence、知识图谱、Progress、AI Summary、Flashcards、错题本不建立可见 placeholder / disabled tab。视觉上不得制造"即将上线"的永久空位。

## 16. Acceptance Criteria

- `UI-VIS-AC-001`：正式 UI 不使用装饰性 emoji、active gradient 或彩色 card stack；
- `UI-VIS-AC-002`：L0 Product Domain 与 L1 facet / App Utility 层级可辨；
- `UI-VIS-AC-003`：系统蓝和 semantic colors 用途稳定且不作为唯一编码；
- `UI-VIS-AC-004`：普通 repeated objects 默认 row/list，不形成 card ocean；
- `UI-VIS-AC-005`：Today canonical activity 的 Primary hierarchy 不被 Quick Start/History 等竞争；
- `UI-VIS-AC-006`：Evidence/Probability component 不通过任意 threshold 暗示 mastery；
- `UI-VIS-AC-007`：RichMessage typed cards 和 fallback 保持安全、可读、一致；
- `UI-VIS-AC-008`：light/dark 下正文、状态、focus、公式、代码和引用满足对比度要求；
- `UI-VIS-AC-009`：360px、200% zoom 和 reduced motion 下核心页面可完成任务；
- `UI-VIS-AC-010`：所有 icon-only/contextual action 有 accessible name 与非 hover-only 入口。

## 17. Forbidden Implementations

禁止：

- emoji 学科卡、玻璃拟态堆叠、大面积蓝紫渐变；
- 每个状态/节点使用随机类别色；
- 用动画、连续天数或徽章制造未被学习证据支持的成就；
- 为简洁移除 error、source、confidence 或帮助状态文字；
- 使用 Card 数量表达 Information Architecture；
- 把 Goal/Plan/Progress/History 做成四个等权首页卡片来替代正确 L1 Navigation；
- Settings giant card grid；
- Library permanent batch control panel；
- 使用 raw HTML、远程 tracking image 或模型指定视觉组件；
- 直接复制 `.design_library` preview 后宣称完成响应式/暗色/可访问验收。
