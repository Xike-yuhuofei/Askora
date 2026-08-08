# Askora UI Visual System Specification

> Spec ID：`UI-VIS-*`
> 状态：`FROZEN`
> 参考资产：`.design_library/Askora/`（supporting asset，不是实现合同）

## 1. 视觉目标

### UI-VIS-001 — Calm, Precise, Focused

Askora 的工作界面应安静、精确、聚焦，优先支持阅读、推理、作答和证据审查。视觉不能用大面积装饰、游戏化奖励或情绪化文案抢占学习任务注意力。

### UI-VIS-002 — Native-feeling macOS

桌面版 SHOULD 接近 macOS 原生应用的信息密度与层级：系统字体、轻量分隔、克制阴影、清晰 focus 和稳定窗口区域。MUST NOT 伪装成系统设置或使用未经授权的 Apple 商标资产。

### UI-VIS-003 — Data Honesty

视觉层次不得夸大数据确定性。估计、置信度、证据不足、兼容数据与系统失败必须通过文案和结构明确表达，而不是只改变颜色。

## 2. 产品语言

### UI-VIS-010 — Voice

界面语言使用简洁中文，语气专业、克制、可行动。按钮优先使用 2～4 字动词，例如：继续学习、开始复习、查看证据、重试、退出。

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

颜色值在正式实现前 MAY 经对比度验证微调，但 semantic mapping 不得改变。

### UI-VIS-021 — Dark Theme

UI-03 必须提供对应 dark tokens：

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

代码/标识符使用：

```css
"SF Mono", Menlo, Monaco, Consolas, monospace
```

### UI-VIS-031

工作界面以 12～16px 为主要文字范围；页面标题 SHOULD 20～28px。正文行高至少 1.5。不得为追求信息密度把关键正文、状态或交互标签缩小到 11px 以下。

### UI-VIS-032

标题层级必须语义化，不得只靠字重/尺寸模拟。每个页面只有一个 `h1`；卡片和 Inspector 使用后续 heading level。

## 5. Spacing, Radius and Elevation

### UI-VIS-040

采用 4px 基础网格，常用间距 8/12/16/24/32px。布局 SHOULD 通过 spacing 和 background layers 分组，避免每个区域都加独立边框和阴影。

### UI-VIS-041

建议 radius：

- 8px：输入、紧凑控件；
- 12px：标准 card、列表项；
- 16px：消息、主任务容器；
- full：avatar、短 status tag。

### UI-VIS-042

阴影仅用于窗口内真正浮动的 popover/modal 或 hover elevation。常规卡片默认使用 surface + border，不使用重阴影。

## 6. Core Components

### UI-VIS-050 — Buttons

至少支持 primary、secondary、ghost、danger 四种 intent。每个局部动作组最多一个 primary。Icon-only button 必须有 accessible label；disabled 必须同时有语义属性和视觉状态。

### UI-VIS-051 — Navigation

Active item 使用单一 primary-soft background + primary text/icon。Hover 与 active 必须有区别；不得用渐变 active background。

### UI-VIS-052 — Cards

Card 只用于需要边界的任务、证据摘要、typed rich response 或可选对象。重复列表项 SHOULD 使用 row/list pattern，避免“卡片海洋”。

### UI-VIS-053 — Status and Badges

Badge 只表达短状态，如“待独立验证”“到期复习”“兼容数据”。长解释放在正文/tooltip/Inspector。状态不得只用颜色编码。

### UI-VIS-054 — Empty, Loading and Error

- Loading：与最终布局一致的最小 skeleton 或明确进度；
- Empty：说明缺少对象与可用下一步；
- Error：显示可理解信息、retry action（仅 retryable）和 correlation id 的复制入口（需要时）；
- Partial/Stale：保留可用内容并在数据区域显示来源状态。

## 7. Learning-specific Components

### UI-VIS-060 — Activity Card

Activity card 显示 title、type、预计时间、status 与 reason summary。它不得显示前端计算的“学习价值分”“掌握增益”或未校准百分比。

### UI-VIS-061 — Evidence Summary

Evidence summary 优先使用有名称的计数与文字：

```text
独立成功 2 次
延迟证据 1 次
迁移证据 暂无
估计置信度 中等
```

若只存在数值 confidence，UI MAY 显示格式化数值，但不得无规则映射为“高/中/低”。高/中/低 label 必须来自后端 versioned product rule。

### UI-VIS-062 — Probability Visualization

`competence_probability` 是估计。若用 bar/ring 呈现，必须同时显示“估计”与 confidence/evidence context；不得用红黄绿阈值表达 mastered/unmastered。

### UI-VIS-063 — Validation Obligation

“待独立验证”使用清晰、非惩罚性的 neutral/warning status。它不是错误、失败或 mastery label。

### UI-VIS-064 — Assistance Control

帮助控件按用户可理解的支持类型命名，例如“方向提示”“解释概念”“拆成子步骤”。不可用状态必须解释是当前学习/评估规则限制，而不是通过隐藏控件制造不可发现性。

### UI-VIS-065 — Knowledge Map

Node 默认使用中性 surface。Current、published/candidate、selected 与 evidence status 使用有限的形状、边框和文字组合。关系方向必须可辨；无可靠 relation 时不得绘制装饰性连接线。

## 8. Rich Message Integration

### UI-VIS-070

继续使用五类 typed card：concept、hint、question、feedback、source。它们的视觉区别 SHOULD 保持克制，并且不改变 `RENDER-*` schema。

### UI-VIS-071

Assistant message 不强制包裹成聊天气泡。长解释 MAY 使用开放内容列，用户短消息 MAY 使用紧凑 bubble；无论布局如何都必须保持 message identity、顺序与 fallback。

### UI-VIS-072

Citation block 默认显示用户可读 label/locator，内部 source_span_id 可放在可复制详情，不作为视觉主标签。

## 9. Motion

### UI-VIS-080

Motion 只用于状态连续性：navigation transition、Inspector 展开、list reordering、stream status。动画 SHOULD 150～250ms，并遵守 `prefers-reduced-motion`。不得使用循环闪烁、庆祝动画或基于 mastery 的游戏化效果。

## 10. Accessibility and Contrast

### UI-VIS-090

普通文字、关键图标、输入边界和 focus 必须满足适用 WCAG AA 对比度。Placeholder 与 disabled 仍需可辨，但不得替代 label。

### UI-VIS-091

Touch target SHOULD 至少 44×44 CSS px；桌面紧凑控件 MAY 36px，但必须有足够间距且键盘可达。

### UI-VIS-092

知识地图、progress、evidence chart 必须提供文本等价信息，不能要求用户仅通过空间位置或颜色理解状态。

## 11. Acceptance Criteria

- `UI-VIS-AC-001`：正式 UI 不使用装饰性 emoji、active gradient 或彩色卡片堆叠。
- `UI-VIS-AC-002`：系统蓝和 semantic colors 用途稳定且不作为唯一编码。
- `UI-VIS-AC-003`：light/dark 下正文、状态、focus、公式、代码和引用满足对比度要求。
- `UI-VIS-AC-004`：Evidence/Probability component 不通过任意 threshold 暗示 mastery。
- `UI-VIS-AC-005`：RichMessage 五类 typed card 和 fallback 保持安全、可读、一致。
- `UI-VIS-AC-006`：360px、200% zoom 和 reduced motion 下核心页面可完成任务。
- `UI-VIS-AC-007`：所有 icon-only action 有 accessible name，关键 touch target 合理。

## 12. Forbidden Implementations

禁止：

- emoji 学科卡、玻璃拟态堆叠、大面积蓝紫渐变；
- 每个状态/节点使用随机类别色；
- 用动画、连续天数或徽章制造未被学习证据支持的成就；
- 为简洁移除 error、source、confidence 或帮助状态文字；
- 直接复制 `.design_library` preview 后宣称完成响应式/暗色/可访问验收；
- 使用 raw HTML、远程 tracking image 或模型指定视觉组件。
