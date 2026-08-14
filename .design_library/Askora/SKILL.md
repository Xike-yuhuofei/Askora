# Askora Design Library — SKILL

本技能指导如何为 Askora（个人长期 AI 学习系统）使用与扩展设计系统。

## 何时使用

- 需要为 Askora 产品页面编写/修改 UI 时
- 需要新增组件、token 或 UI Kit 时
- 需要保证视觉与 Askora 设计语言一致时

## 核心原则

1. **Token 优先**：所有颜色、间距、圆角、字号、阴影一律引用 `colors_and_type.css` 中的 token，禁止硬编码原始色值。
2. **组件复用**：优先复用 `components/` 中的 `.ak-*` 组件；页面级自定义样式保持在页面内，不进入共享 CSS。
3. **学习语义**：Askora 是学习系统，文案用简体中文、专业克制、无 emoji；组件语义面向学习（目标、今日、知识库、对话、复习）。
4. **品牌一致**：品牌主色系统蓝 `#007AFF`，Apple 分层灰，Inter + JetBrains Mono，4px 网格，5 级阴影。
5. **范围克制**：只构建学习产品实际需要的组件，不追求与参考系统同等完整度。

## 工作流

1. 读取 `README.md` 了解结构，读取 `colors_and_type.css` 了解可用 token。
2. 检查 `components/index.json` 是否已有可复用组件。
3. 编写页面：引入 `colors_and_type.css` + `components.css`，从 `preview/component-{slug}.html` 复制组件标记。
4. 新增组件时：写 `components/{slug}.json` 契约 + `preview/component-{slug}.html` 预览 + 在 `components.css` 加 `@component-css-start/end` 标记块，并更新 `components/index.json`。
5. 新增页面时：在 `ui_kits/{type}/index.html` 构建，并生成 `quality-report.json`。

## 契约字段

组件契约沿用 schemaVersion 2：`slug`、`name`、`category`、`variantDimensions`、`coverageMatrix`、`stateCoverage`、`representativeVariants`、`tokensConsumed`、`domAnatomy`、`assetsConsumed`、`provenance`、`usageHints`、`doNotInvent`、`unknowns`。

## 禁止

- 不引入外部图标库/图标字体/CDN；图标仅用本地 SVG，`currentColor` mask。
- 不硬编码 token 值；不新增一级组件而不更新契约与索引。
- 不把页面级样式混入共享组件 CSS。
- 不突破 Askora 产品边界（Local Web、单用户、Local-first、BYOK、中文）。
