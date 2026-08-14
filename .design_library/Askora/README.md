# Askora Design Library

Askora 设计系统 —— 面向个人长期 AI 学习系统的 Apple 风格设计语言。

## 定位

Askora 是个人长期 AI 学习系统（Local Web、单用户、Local-first、BYOK、中文优先）。本设计库为其提供统一、可执行的设计契约，范围以学习产品实际需要为准，不追求与任何参考系统同等完整度。

## 目录结构

```text
.design_library/Askora/
├── colors_and_type.css      # 设计 token（Askora 品牌值 + TraeWork 兼容别名）
├── css.json                 # 机器可读 token（color/font/shadow/radius/spacing/size）
├── components.css           # 聚合组件样式（@component-css-start/end 标记块）
├── components/              # 组件契约（schemaVersion 2）
│   └── index.json           # 组件索引
├── preview/                 # 组件预览页（可 file:// 直接打开）
├── ui_kits/                 # 页面级 UI Kit
│   └── learning-workspace/  # 三栏学习工作区
└── README.md / SKILL.md
```

## Token

- 品牌主色：系统蓝 `#007AFF`（`--bg-brand` / `--askora-primary-500`）
- 语义色：success `#34C759`、warning `#FF9500`、error `#FF3B30`、info `#00B2B2`
- 中性色：Apple 分层灰（`--askora-neutral-50..900`）
- 字体：Inter（正文/标题）+ JetBrains Mono（代码），简体中文优先
- 网格：4px 基准；圆角 8/12/16/20/9999；阴影 5 级

### TraeWork 兼容别名

本库保留 TraeWork 的 token 别名并直接复用，值指向 Askora 新 token：
`--bg-*`、`--text-*`、`--icon-*`、`--border-*`、`--status-*`、`--brand-*`、`--bg-layout-*`、`--spacer-*`、`--radius-*` 等。组件类前缀为 `.ak-`（区别于 TraeWork 的 `.ds-`）。

## 组件

共 19 个组件，见 `components/index.json`。分类：

- action：buttons
- layout：cards、learning-workspace
- input：forms、learning-input
- navigation：menu、pagination、tabs、breadcrumb、goal-tree
- feedback：alert、dialog、progress、skeleton、status-bar、tag
- data-display：avatar、table、knowledge-card

## 使用

1. 引入 `colors_and_type.css` + `components.css`
2. 从 `preview/component-{slug}.html` 复制组件标记
3. 页面级样式（非组件契约）保持在页面内，不进入共享 CSS
4. 图标仅用本地 SVG 资产，`currentColor` mask 随 token 变色

## 验证

- JSON 契约：`python3 -c "import json; json.load(open('components/index.json'))"`
- 预览页可直接 `file://` 打开
