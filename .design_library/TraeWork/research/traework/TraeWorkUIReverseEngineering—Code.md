# TraeWork Light Mode UI Reverse Engineering
# TraeCode + FigJam + Figma 执行任务

你是一名资深：

- Product Design Lead
- UX Architect
- Interaction Designer
- Design System Architect
- Desktop App UI Architect
- Figma Design System Expert
- Frontend Architect

你的任务是基于：

1. TraeWork Design System 素材目录 `/Users/xike/Documents/Docs/Askora/TraeWork/TraeWork`
2. TraeWork Light Mode UI 截图 PNG `/Users/xike/Documents/Docs/Askora/TraeWork/截图/`

对 TraeWork 进行系统性的 UI Reverse Engineering。

目标不是简单“照截图临摹”，而是恢复 TraeWork 背后的：

- Information Architecture
- Application Shell
- Layout System
- Panel System
- Design Tokens
- Typography
- Icon System
- Component System
- Interaction Model
- State Model
- Resize Rules
- Desktop Workspace Architecture
- Figma Design System

最终形成一套：

「可以被理解、复用、维护、继续开发的 UI Design System」。

---

# 一、核心原则

必须遵循：

1. 先分析，后绘制
2. 先 Design System，后 Screen
3. 先 Tokens，后 Components
4. 先 Components，后 Patterns
5. 先 Application Shell，后具体页面
6. 使用 Auto Layout，而不是大量绝对定位
7. 不根据单张截图静默脑补交互
8. 设计系统素材优先于肉眼猜测
9. 截图用于验证真实组合、尺寸、层级与视觉效果
10. 所有结论保留 Evidence

禁止直接：

截图 → Figma 临摹完整页面

正确流程：

Design Library
+
Screenshot

↓

Design System Analysis

↓

Information Architecture

↓

Application Shell

↓

Tokens

↓

Components

↓

Patterns

↓

Figma

↓

Screen Reconstruction

↓

Pixel Validation

---

# 二、输入素材

首先扫描以下素材目录：

Design System 素材目录：
`/Users/xike/Documents/Docs/Askora/TraeWork/TraeWork`

Screenshot 目录：
`/Users/xike/Documents/Docs/Askora/TraeWork/截图/`

素材目录结构：
- `assets/icons/` — SVG 图标库
- `components/` — Component JSON Contracts
- `preview/` — Component Preview HTML
- `ui_kits/` — UIKit Pattern HTML
- `css.json` — Design Token JSON
- `components.css` — Component 样式
- `colors_and_type.css` — 颜色与字体样式
- `library-consumption.json` — 库消费契约
- `uikit-plan.json` — UIKit 规划
- `README.md` / `SKILL.md` — 文档

以及最新的：

TraeWork Light Mode PNG Screenshot

不要继续使用任何已经删除的 Dark Mode 截图。

不要假定旧 PNG 仍然有效。

必须确认：

当前分析使用的 PNG 是最新 Light Mode 版本。

记录：

- 文件名
- 文件路径
- 文件大小
- PNG 分辨率
- 目录内容清单
- 修改时间

如果存在多个 TraeWork PNG：

根据文件时间和内容识别最新 Light Mode 截图。

无法判断时才报告 Unknown。

---

# 三、建立工作目录

不要修改原始素材目录。

创建：

reverse-engineering/traework/

建议：

source/
analysis/
measurements/
exports/
figjam/
figma/
reports/

素材目录引用（不复制，直接读取原目录）：

source/design-library/ → 符号链接或引用 `/Users/xike/Documents/Docs/Askora/TraeWork/TraeWork`

原始素材目录保持不变。

---

# 四、审计 Design Library

先扫描整个素材目录。

生成：

analysis/01-library-inventory.md

记录：

## Files

## Tokens

## Components

## Icons

## UI Kits

## Preview Pages

## CSS

## JSON Contracts

## Documentation

必须实际验证：

- Component 数量
- Icon 数量
- UIKit 数量

不要依赖已有描述直接假定数量。

---

# 五、优先阅读顺序

按照：

1. README.md
2. library-consumption.json
3. uikit-plan.json
4. css.json
5. colors_and_type.css
6. components.css
7. components/index.json
8. components/*.json
9. preview/component-*.html
10. ui_kits/*/quality-report.json
11. ui_kits/*/index.html
12. assets/icons/*.svg

进行分析。

优先级：

Design Tokens
↓
Component Contracts
↓
Component Preview
↓
UIKit Composition
↓
Real TraeWork Screenshot

注意：

UIKit 主要作为 Pattern / Showcase Evidence。

不要直接把 UIKit 页面当成正式 App Shell。

---

# 六、证据等级

所有关键结论标记：

[C] Confirmed
素材直接确认

[I] Inferred
根据多个证据合理推导

[U] Unknown
证据不足

[L] Library
来自 TraeWork Design Library

[S] Screenshot
来自当前 Light Mode Screenshot

例如：

Button height = 28px [C][L]

Sidebar observed width ≈ 268px [C][S]

Sidebar min width = Unknown [U]

Prompt Composer radius = 8px [I][L][S]

---

# 七、Design Token Reverse Engineering

解析：

css.json
colors_and_type.css
components.css

恢复：

## Color

bg/*
text/*
icon/*
border/*
brand/*
status/*

## Typography

body/*
heading/*
code-editor/*
code-terminal/*

## Dimension

spacing/*
radius/*
icon-size/*
border-width/*

## Shadow

shadow/*

不要创建第二套没有必要的命名体系。

优先复用 TraeWork 原始 Semantic Token。

---

# 八、建立 Token Canonical Model

创建：

analysis/02-design-tokens.md

以及：

analysis/design-tokens.json

结构建议：

Color
├── Background
├── Surface
├── Text
├── Icon
├── Border
├── Brand
└── Status

Typography
├── Body
├── Heading
├── Code Editor
└── Terminal

Dimension
├── Spacing
├── Radius
├── Icon Size
├── Border Width
└── Component Size

Effects
└── Shadow

---

# 九、Light Mode Token 验证

由于：

Design Library
+
Screenshot

现在均为 Light Mode，

重点不再是 Theme Mapping，而是：

Library Token ↔ Actual Product Screenshot Validation

建立：

analysis/03-light-theme-validation.md

对比：

Design Library Token

和

Screenshot Observed Color

验证：

bg/app

bg/sidebar

bg/workspace

bg/input

bg/hover

text/primary

text/secondary

text/tertiary

border/default

border/subtle

brand/default

status/*

如果截图实际颜色与 Token 存在轻微差异：

记录：

Token Value
Observed Value
Delta
Possible Cause

可能原因包括：

- Transparency
- Overlay
- Anti-aliasing
- Color blending
- Screenshot compression
- OS rendering

不要因为 1~2 个 RGB 差值重新创建 Token。

---

# 十、Component Contract Analysis

解析：

components/*.json

重点读取：

tokensConsumed
domAnatomy
assetsConsumed
coverageMatrix
provenance
states
variants

建立：

analysis/04-component-inventory.md

记录：

Component
Category
Variants
States
Size
Tokens
Icons
Anatomy
Evidence
Confidence

分类：

Actions

Navigation

Inputs

Feedback

Data Display

Layout

Overlay

Desktop / IDE

AI / Agent

---

# 十一、Component Preview

通过浏览器 / Playwright 渲染：

preview/component-*.html

输出截图：

exports/component-previews/

验证：

Default

Hover

Active

Pressed

Focus

Selected

Disabled

Loading

Error

重点分析：

Button

Input

Menu

Tabs

Dialog

Alert

Card

Table

Tag

Breadcrumb

Progress

Skeleton

如果：

JSON Contract

与：

Preview

存在冲突，

记录冲突，不要自行覆盖。

---

# 十二、Icon System

扫描：

assets/icons/*.svg

通过脚本生成：

analysis/05-icon-inventory.md

统计：

- 总数量
- SVG viewBox
- 常用尺寸
- Stroke / Fill
- Monochrome
- Multicolor

进一步分类：

Navigation

Action

File

Folder

Editor

Agent

Search

Status

Device

Social

Other

不要人工逐个打开几百个 SVG。

使用脚本自动 Inventory。

---

# 十三、UIKit Pattern Mining

渲染：

ui_kits/*/index.html

重点分析与 Desktop App 接近的 UIKit。

例如：

dev-explorer
dashboard
settings
skills-library

提取：

Navigation Pattern

Sidebar Pattern

Tree Pattern

Toolbar Pattern

Tabs Pattern

List Pattern

Card Pattern

Settings Pattern

Panel Pattern

Search Pattern

Command Pattern

AI Pattern

输出：

analysis/06-ui-patterns.md

目标是：

提取设计模式

而不是：

复制 UIKit 页面。

---

# 十四、分析最新 Light Mode Screenshot

创建：

analysis/07-screen-analysis.md

确认截图：

Resolution

Window Bounds

Sidebar Bounds

Main Workspace Bounds

Prompt Composer Bounds

Center Content Bounds

Top Controls

Bottom Controls

---

# 十五、Screenshot Geometry Measurement

使用：

Python

必要时：

OpenCV

辅助测量。

至少分析：

Window Width

Window Height

Sidebar Width

Main Surface X/Y

Outer Border

Outer Radius

Sidebar Padding

Sidebar Row Height

Icon Size

Section Gap

Prompt Composer Width

Prompt Composer Height

Prompt Composer Padding

Quick Action Button Width

Quick Action Button Height

Content Center X

Content Center Y

Vertical Rhythm

不要全部依赖肉眼估计。

---

# 十六、生成 Measurement Overlay

不要修改原始截图。

创建：

exports/measurements/

生成：

code-welcome-overlay.png

标记：

X

Y

Width

Height

Spacing

Alignment Guides

Major Boundaries

使用该图作为后续 Figma Build Evidence。

---

# 十七、Information Architecture

分析截图中的：

Work

Code

Design

以及：

新建任务

插件市场

自动化

办公助理

模板库

Pinned

Task List

Workspace / Project Group

Account

进一步识别：

Global Navigation

Mode Navigation

Task Navigation

Workspace Navigation

Contextual Navigation

建立：

analysis/08-information-architecture.md

不要把所有内容简单统称 Sidebar。

---

# 十八、Application Shell Reverse Engineering

恢复 App Shell。

例如可能为：

Application Window
├── Sidebar
│   ├── Window Controls
│   ├── Global Controls
│   ├── Mode Switcher
│   ├── Primary Actions
│   ├── Pinned
│   ├── Workspace Navigation
│   └── Account
│
└── Workspace
    └── Welcome Surface

但：

必须以真实 Screenshot 为准。

输出：

analysis/09-application-shell.md

---

# 十九、Sidebar Architecture

Sidebar 是本轮重点。

拆解：

Sidebar
├── Window Controls
├── Top Utilities
├── Mode Switcher
├── Global Actions
├── Pinned Section
├── Task / Workspace Navigation
├── Project Groups
└── Account

进一步分析：

Fixed

Scrollable

Resizable

Collapsible

Sticky

Selected State

Hover State

Section Collapse

Tree Expand

记录：

Observed Width

Default Width

Min Width

Max Width

Resize Rule

如果只有 Screenshot 能确认当前宽度：

只将：

Observed Width

标记为 Confirmed。

不要把它自动视为 Default Width。

---

# 二十、Main Workspace

分析当前：

Code Mode / Welcome Page

拆分：

Workspace
├── Welcome Content
│   ├── Hero
│   ├── Prompt Composer
│   └── Quick Actions
│
└── Background Surface

判断：

哪些属于：

App Shell

哪些属于：

Code Mode

哪些属于：

Welcome Page

哪些属于：

AI Composer Pattern

---

# 二十一、Prompt Composer

这是高优先级 Composite Component。

拆解：

PromptComposer
├── Editor
├── Context Add
├── Attachment
├── Tool / Context Controls
├── Model Selector
├── Voice
├── Submit
└── Context Bar

分析状态：

Default

Hover

Focused

Typing

Attachment

Context Added

Model Open

Submitting

Running

Disabled

Error

不要把 Prompt Composer 当普通 Textarea。

输出：

analysis/10-prompt-composer.md

---

# 二十二、Component Taxonomy

从：

Library
+
UIKit
+
Screenshot

三类证据建立：

Primitive

↓

Component

↓

Composite

↓

Pattern

↓

Screen

例如：

Primitive

Icon
Text
Divider

Component

Button
IconButton
Tab
Input
ListItem
TreeItem

Composite

ModeSwitcher
SidebarSection
PromptComposer

Pattern

Sidebar
WorkspaceNavigation
WelcomeContent

Screen

CodeWelcomePage

创建：

analysis/11-component-taxonomy.md

---

# 二十三、Interaction Model

建立：

analysis/12-interaction-model.md

覆盖：

Mode Switching

New Task

Sidebar Selection

Workspace Expand

Workspace Collapse

Task Selection

Prompt Focus

Add Context

Attachment

Model Selection

Voice

Submit

Quick Action

Hover

Focus

Pressed

Selected

Scroll

Resize

对于截图无法确认的行为：

标记 [U]

不要自行发明。

---

# 二十四、State Model

建立：

analysis/13-state-model.md

统一：

Default

Hover

Pressed

Focused

Selected

Disabled

Empty

Typing

Loading

Running

Success

Warning

Error

研究这些状态应该属于：

Global Component State

还是：

Agent-specific State

---

# 二十五、Desktop Resize Model

不要使用传统 Mobile Responsive 思路。

研究：

Window Resize

Sidebar Resize

Workspace Flex

Minimum Content Width

Overflow

Scroll

Collapse

建立：

analysis/14-resize-model.md

定义：

Window Min Width

Sidebar Observed Width

Sidebar Min Width

Sidebar Max Width

Workspace Min Width

Flex Behavior

Collapse Rules

如果截图无法确认：

标记 Unknown。

---

# 二十六、FigJam

完成前面的 Reverse Engineering 后再进入 FigJam。

创建：

TraeWork — UI Reverse Engineering

Board。

---

# 二十七、FigJam Sections

建立：

00 Reverse Engineering Map

01 Source Inventory

02 Screenshot Evidence

03 Information Architecture

04 Application Shell

05 Sidebar Architecture

06 Workspace Architecture

07 Component Taxonomy

08 Prompt Composer Anatomy

09 Design Tokens

10 Interaction Model

11 State Model

12 Resize Model

13 Evidence Matrix

14 Open Questions

15 Figma Build Plan

---

# 二十八、FigJam 使用边界

FigJam 用于：

Architecture

Relationships

Flows

Taxonomy

State Model

Evidence

Hypothesis

Unknown

不要用 FigJam 制作高保真 UI。

---

# 二十九、Figma 文件

完成 FigJam 架构后再建立：

TraeWork Reverse Engineering

Figma Design File。

Pages：

00 Cover

01 Sources

02 Foundations

03 Icons

04 Components

05 Composite Components

06 Patterns

07 App Shell

08 Code Mode

09 Screens

10 Prototype

11 Validation

99 Archive

---

# 三十、Figma Variables

建立：

Core

Semantic

Component

三层 Variables。

例如：

Core
├── Primitive Color
├── Spacing
├── Radius
└── Size

Semantic
├── Background
├── Text
├── Icon
├── Border
├── Brand
└── Status

Component
├── Button
├── Input
├── Sidebar
├── Tab
└── Composer

当前第一阶段只需要：

Light Mode。

但是：

Semantic Token 架构应允许未来增加 Dark Mode。

不要因为现在只有 Light Mode 而把颜色硬编码进 Component。

---

# 三十一、Typography

严格根据 Design Library 重建。

建立：

Body

Heading

Code Editor

Terminal

Label

如果原字体 Mac 不存在：

明确记录：

Font Missing

不要静默换字体后声称完全复刻。

---

# 三十二、Figma Icon Strategy

导入原始 SVG。

不要把所有图标铺满一个页面。

建立：

Icon Component

使用：

Instance Swap

分类组织。

第一阶段优先导入：

当前 Screenshot 实际使用的 Icon。

---

# 三十三、Component Architecture

推荐：

Primitive

Icon
Divider

↓

Base Components

Button
IconButton
Input
Tab
ListItem
TreeItem
SectionHeader
Tooltip

↓

Composite

ModeSwitcher
SidebarAction
SidebarSection
WorkspaceGroup
TaskItem
PromptComposer
QuickAction

↓

Pattern

Sidebar
MainWorkspace

↓

Screen

CodeWelcomePage

实际结构必须结合现有 Component Contract 调整。

---

# 三十四、Auto Layout

Figma 中优先：

Auto Layout

Fill Container

Hug Contents

Min Width

Max Width

Variables

Variants

Component Properties

Boolean Properties

Instance Swap

禁止：

大量独立 Frame

大量复制组件

大量绝对定位

大量 Detached Instance

---

# 三十五、Code Welcome Screen Reconstruction

第一阶段 Figma Screen 只复刻：

TraeWork
→ Code Mode
→ Welcome Page
→ Light Mode

不要马上复刻整个 TraeWork。

目标：

通过这个 Screen 验证：

Design Tokens

Components

App Shell

Sidebar

Prompt Composer

Spacing

Typography

Icon System

---

# 三十六、Pixel Validation

完成后按照原 Screenshot Resolution 导出。

建立：

Reference Screenshot

vs

Figma Reconstruction

进行 Overlay。

检查：

Sidebar Boundary

Workspace Boundary

Background

Border

Radius

Typography

Icon Alignment

Composer

Quick Actions

Spacing

Center Position

---

# 三十七、Visual Validation Report

创建：

analysis/15-visual-validation.md

记录：

Element

Reference

Reconstruction

Delta

Cause

Action

Confidence

目标不是机械做到每个像素一致。

优先级：

Design System Consistency

+

High Visual Fidelity

---

# 三十八、Open Questions

创建：

analysis/16-open-questions.md

分类：

Need More Screenshot

Need Interaction Verification

Need Resize Verification

Need Component Verification

Need Token Verification

不要通过猜测消灭 Unknown。

Unknown 是 Reverse Engineering 的正常结果。

---

# 三十九、最终文档结构

建立：

docs/design/traework-reverse-engineering/

包含：

00-overview.md

01-source-inventory.md

02-design-tokens.md

03-light-theme-validation.md

04-component-inventory.md

05-icon-system.md

06-ui-patterns.md

07-screen-analysis.md

08-information-architecture.md

09-application-shell.md

10-sidebar-architecture.md

11-prompt-composer.md

12-component-taxonomy.md

13-interaction-model.md

14-state-model.md

15-resize-model.md

16-figjam-architecture.md

17-figma-build-spec.md

18-visual-validation.md

19-open-questions.md

---

# 四十、第一轮执行范围

当前只执行 Phase 1。

完成：

1. 定位最新 Light Mode PNG
2. 确认不再使用旧 Dark Screenshot
3. 扫描与审计 Design Library 素材目录
4. 阅读 Design Library
5. Token Inventory
6. Component Inventory
7. Icon Inventory
8. UIKit Inventory
9. Light Mode Token Validation
10. Screenshot Geometry
11. Measurement Overlay
12. Information Architecture
13. Application Shell
14. Sidebar Architecture
15. Prompt Composer Anatomy
16. Component Taxonomy
17. Interaction / State 初步模型
18. Resize Hypothesis
19. FigJam Board Architecture
20. Figma Build Plan

完成后暂停。

不要直接继续制作整个 Figma Design System。

---

# 四十一、Phase 1 Completion Report

输出：

## Completed

## Source Inventory

## Design Library Findings

## Token Findings

## Component Findings

## Screenshot Geometry

## Application Shell

## Sidebar Architecture

## Prompt Composer

## Component Taxonomy

## Confirmed

## Inferred

## Unknown

## Evidence Gaps

## FigJam Plan

## Figma Build Plan

## Recommended Phase 2

---

# 四十二、Agent 执行原则

1. 读取真实文件，不根据文件名猜内容。
2. 不修改原始素材。
3. 最新 Light Mode Screenshot 为唯一 Screenshot Evidence。
4. 不再引用已删除 Dark Mode Screenshot。
5. 优先复用 TraeWork 自己的 Token。
6. 优先复用 TraeWork Component Contract。
7. 使用脚本处理批量 Inventory。
8. 可以使用 Playwright 渲染 Preview/UIKit。
9. 可以使用 Python/OpenCV 辅助 Geometry Measurement。
10. 如果 Figma MCP 可用，可在后续阶段创建实际资产。
11. 如果没有 Figma 写权限，只输出 Build Spec。
12. 不得伪造已经创建的 Figma/FigJam。
13. 每个结论记录 Evidence。
14. Unknown 明确写 Unknown。
15. 不要为了“看起来像”破坏组件一致性。
16. 不要一次性复刻整个 TraeWork。
17. 当前目标是恢复系统，不是画图。

---

# 四十三、Git

如果当前目录属于 Git Repository：

执行前检查：

git status
git branch
git log -5 --oneline

不得覆盖现有未提交修改。

逆向设计资料应独立提交。

建议 Commit：

design: add TraeWork light UI reverse engineering phase 1

---

# 四十四、现在开始

现在执行 Phase 1。

执行顺序：

定位最新素材

↓

审计 Design Library

↓

解析 Tokens

↓

解析 Components

↓

分析 UIKit

↓

分析 Light Screenshot

↓

Geometry Measurement

↓

Information Architecture

↓

Application Shell

↓

Component Taxonomy

↓

FigJam Architecture

↓

Figma Build Plan

不要先问我如何组织项目。

只有遇到真正阻塞执行的问题才停止并报告 Blocker。