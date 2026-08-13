# 02 — Design Tokens Canonical Model

**Phase**: 1 · **Generated**: 2026-08-12 · **Evidence**: `css.json` + `colors_and_type.css` [L]

配套机器文件：`analysis/design-tokens.json`（270 个 token 叶子）。

原则：**复用 TraeWork 原始 Semantic Token，不创建第二套命名体系**。[L]

---

## 1. Color

### Background / Surface

| Token | Value | 用途推断 |
|---|---|---|
| `--bg-base-default` | `#ffffff` | App 主背景 |
| `--bg-base-secondary` | `#f5f5f5` | Sidebar / 次级 surface |
| `--bg-base-tertiary` | `#e5e5e5` | 三级 surface / hover 容器 |
| `--bg-overlay-l1..l4` | `#737373` @ 0.08/0.12/0.16/0.20 | hover / active / 按压叠加层 |
| `--bg-white` / `--bg-menu` / `--bg-tooltip` | `#ffffff` | 浮层 |
| `--bg-invert` | `#262626` | 反色底（dark controls） |
| `--bg-invert-hover` | `#404040` | |
| `--bg-invert-active` | `#171717` | |

### Brand

| Token | Value |
|---|---|
| `--bg-brand` / `--text-brand` / `--icon-brand` | `#4b3fe3` |
| `--bg-brand-hover` | `#6a6fff` |
| `--bg-brand-active` | `#3f31c6` |
| `--bg-brand-disabled` | `#4b3fe3` @ 0.22 |
| `--bg-brand-popup` | `#aab7ff` @ 0.36 |

### Text

| Token | Value |
|---|---|
| `--text-default` | `#171717` |
| `--text-secondary` | `#404040` |
| `--text-tertiary` | `#737373` |
| `--text-disabled` | `#a1a1a1` |
| `--text-onbrand` / `--text-onaccent` / `--text-white` | `#ffffff` |

### Icon

| Token | Value |
|---|---|
| `--icon-default` | `#262626` |
| `--icon-secondary` | `#404040` |
| `--icon-tertiary` | `#737373` |
| `--icon-disabled` | `#a1a1a1` |
| `--icon-onbrand` / `--icon-white` | `#ffffff` |

### Border

| Token | Value | 实际合成 |
|---|---|---|
| `--border-neutral-l1` | `#737373` @ 0.12 | 标准分隔线 |
| `--border-neutral-l2` | `#737373` @ 0.18 | 输入框边框 |
| `--border-neutral-l3` | `#737373` @ 0.36 | 强调边框 |
| `--border-contrast` | `#000000` | 强对比 |
| `--border-brand` | `#4b3fe3` | focus / 选中 |

### Status（5 语义 × 3 层）

`primary` `success` `alert` `warning` `error`，每色含 `-default / -hover / -active / -surface-l1..l3`。

| status | default | surface-l1 |
|---|---|---|
| primary | `#2f74ff` | `#2f74ff` @ 0.12 |
| success | `#15a877` | `#40b08b` @ 0.12 |
| alert | `#fea900` | `#fea900` @ 0.14 |
| warning | `#e27900` | `#e27900` @ 0.12 |
| error | `#d9382b` | `#d9382b` @ 0.12 |

### Brand ramp

`brand-50..950` 完整梯度 + 多色系 ramp（grey / green / red / yellow / blue / purple / neutral-grey / blue-grey / green-grey 各 100..1000）。核心品牌色阶 `brand-600 = #4b3fe3`。

### 其他

- `code/*`：11 个代码语法色
- `accent/*`：9 个强调色（teal/coral/amber/lime/cyan/blue/magenta/violet/slate）
- `viz/*`：23 个图表系列色
- `special/*`：4 个特殊色

## 2. Typography

### Body（主 UI 文字）

| Style | Size | Weight | LH | LS |
|---|---|---|---|---|
| body-xs | 10px | 400 | 14px | 0 |
| body-xs-strong | 10px | 500 | 14px | 0 |
| body-sm | 11px | 400 | 16px | 0 |
| body-sm-strong | 11px | 500 | 16px | 0 |
| body-md | 12px | 400 | 18px | 0 |
| body-md-strong | 12px | 500 | 18px | 0 |
| **body-base** | **14px** | **400** | **20px** | -0.02em |
| body-base-strong | 14px | 500 | 20px | -0.02em |
| body-lg | 18px | 400 | 28px | -0.02em |

### Heading（600 权重为主）

| Style | Size | LH |
|---|---|---|
| heading-3xs | 11px | 16px |
| heading-2xs | 12px | 18px |
| heading-xs | 13px | 20px |
| heading-sm | 16px | 24px |
| heading-md | 20px | 28px |
| heading-lg | 22px | 30px |
| heading-xl | 24px | 32px |
| heading-2xl | 28px | 36px |
| heading-3xl | 32px | 40px |
| heading-display-sm | 40px | 48px |
| heading-display | 52px | 60px |

### Code / Terminal

| Style | Font | Size | Weight | LH |
|---|---|---|---|---|
| code-editor | JetBrains Mono | 13px | 450 | 20px |
| code-terminal | JetBrains Mono | 12px | 450 | 18px |

### Font family

| Token | Value |
|---|---|
| default/body | "SF Pro Text", "PingFang SC", … |
| heading | "SF Pro", "PingFang SC", … |
| metric | "Inter", "SF Pro Text", … |
| mono | "JetBrains Mono", ui-monospace, "SF Mono", Menlo, Consolas |

> 注意：`SF Pro` / `JetBrains Mono` 需确认当前 Mac 是否安装。[U] 若缺失，Figma 构建时用 system fallback 并记录 Font Missing，不得静默替换。

## 3. Dimension

### Spacing（spacer 阶梯）

`0, 2, 3, 4, 6, 8, 10, 12, 16, 20, 24, 32, 40, 48, 64` px

### Radius

| Token | Value | 语义 |
|---|---|---|
| radius-sm/xs | 2/4px | 小控件 |
| radius-md | 6px | 常规控件 |
| **radius-lg** | **8px** | 卡片/按钮 |
| radius-xl | 10px | 大卡片 |
| radius-12 / -16 | 12/16px | 容器 |
| radius-20/-24/-32 | 20/24/32px | 大面板 |
| radius-full | 999px | pill/圆形 |

### Size

- `--icon-size-12/14/16/20/24` px
- `--border-width-default` = 1px

## 4. Effects（Shadow）

- `css.json` 的 shadow 分组为**空**。[L]
- 组件级 shadow 以组件内联形式存在（如 card-template hover `0 2px 8px rgba(0,0,0,.08)`，ai-input focus ring）。
- **缺失 canonical shadow token 是 Phase 2 需新增项**：`--shadow-1..N`。[U]

---

## Token 消费热点（来自组件契约）

- buttons 48、code-editor 42、alert 37 消费 token 最多。
- status-bar 引用了非标准 `--brand-grey-700`（需核对，可能是待新增 token）。[U]
- reverse-engineered 组件共提出 ~46 个 `newTokensProposed`（shell/ai-input/task-tree/status-bar/card-template/code-editor），Phase 2 需决策是否纳入 canonical。[U]
