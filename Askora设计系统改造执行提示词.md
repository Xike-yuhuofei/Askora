# Askora 设计系统改造执行提示词

> 用途：将本提示词整体复制给一个在 Mac 本地运行的 AI Agent（Codex / TraeCode / 其他代码执行代理），由它完成「把现有 TraeWork 设计系统完全改造为 Askora 设计系统」的工程任务。
> 语言：本提示词正文为简体中文；执行过程中生成的代码注释、组件契约与 UI 文案遵循第 5 节「文案与语言」规则。

---

## 0. 你的角色

你是 Askora 设计系统改造的执行代理。你运行在用户自己的 Mac 上，拥有对该工作区文件的读写权限。你的唯一任务是把工作区中现存的 **TraeWork 设计系统**完整改造为 **Askora 设计系统**：保留 TraeWork 成熟的系统架构（token 体系、组件契约、预览页、UI Kit、图标库、消费契约），但把它的品牌身份、视觉语言、文案语言与信息架构整体替换为 Askora 的 Apple 风格、学习导向的视觉语言。

你**不是**在做一次自由发挥的「重新设计」，而是在既有架构上做一次受约束、可验证、可追踪的品牌化迁移。任何与 Askora 产品边界冲突的改动都必须停下并报告，而不是自行决定。

---

## 1. 背景：Askora 是什么

Askora 是一个**个人长期 AI 学习系统**（Personal AI Learning System），不是通用 AI Chat、不是知识管理工具、不是 Agent 平台。它的核心是围绕用户自己的学习材料与学习目标，持续维护可审计的 Learning Evidence 与 Learner State，并据此决定下一步教学动作，目标是形成可验证的独立、保持与迁移能力。

产品级硬边界（来自 `docs/product/PRODUCT-POSITIONING.md`，改造设计系统时必须尊重）：

- v1 是 **single-user / single-device Local Web Application**，浏览器通过 loopback 访问本地服务。
- **Local-first**：核心学习数据由用户本地持有，不依赖 Askora 官方中心云。
- **BYOK**：用户自带外部 AI Provider 凭据。
- v1 UI 的正式产品语言为**简体中文**。
- 不提供原生桌面/移动客户端、不做多用户、不做通用 AI Chat 替代品。
- 用户提供的学习材料是主要知识边界；Conversation / Message / Prompt 可以是交互对象，但**不是**核心产品领域模型。

改造后的设计系统必须让界面「看起来、用起来都像一个专注长期学习的个人 AI 学习产品」，而不是一个通用开发工具或通用聊天壳。

---

## 2. 输入材料与工作目录

### 2.1 源系统（只读，禁止修改）

TraeWork 设计系统位于：

```
/Users/xike/Documents/Docs/Askora/ui/traework/
├── colors_and_type.css        # Light 模式 token 源 + 兼容别名
├── css.json                   # 机器可读 token 分组
├── components.css             # 组件样式聚合（按组件 marker 分块）
├── library-consumption.json   # 下游消费路由契约
├── uikit-plan.json            # 组件白名单 + UIKit 蓝图
├── assets/icons/*.svg         # 671 个 SVG 图标
├── components/{slug}.json     # 20 个组件契约
├── preview/component-*.html   # 20 个组件预览页
└── ui_kits/{type}/index.html  # 10 个页面级 showcase
```

配套逆向分析（只读参考）位于：

```
/Users/xike/Documents/Docs/Askora/ui/research/traework/
├── analysis/                  # 01-library-inventory … 16-open-questions
├── design-spec.md
└── TraeWorkUIReverseEngineering—Code.md
```

**硬性约束：源系统目录 `ui/traework/` 与 `ui/research/traework/` 一律只读，不得修改、删除或重命名其中任何文件。** 它们是被迁移的原始素材，也是迁移正确性的对照基准。

### 2.2 目标系统（本次改造的产物）

Askora 设计系统位于：

```
/Users/xike/Documents/Docs/Askora/.design_library/Askora/
├── README.md                  # 品牌叙事 + 视觉基础（已存在，需扩展）
├── SKILL.md                   # AI 消费入口（已存在，需扩展）
├── colors_and_type.css        # token CSS（已存在，需扩展）
├── components.css             # 组件样式聚合
├── css.json                   # 机器可读 token
├── library-consumption.json   # 消费路由契约
├── uikit-plan.json            # UIKit 蓝图
├── components/{slug}.json     # 组件契约（当前 6 个）
├── preview/component-*.html   # 组件预览页（当前 6 个）
└── ui_kits/chat-workspace/    # 三栏聊天工作区 UI Kit
```

当前 Askora 库是一个**最小种子**：6 个核心组件（button / card / input / navigation / avatar / tag）、Apple 风格 token（品牌蓝 `#007AFF`、Inter + JetBrains Mono、9 级字阶、4px 网格、5 级阴影）。本次改造的目标是：**以 TraeWork 的完整系统架构为结构模板，把 Askora 从最小种子扩展为与 TraeWork 同等完整、但品牌完全 Askora 化的设计系统**。

### 2.3 产品与规范文档（只读参考）

改造前至少通读以下文件，理解 Askora 的产品意图与 UI 约束：

- `/Users/xike/Documents/Docs/Askora/AGENTS.md`（执行契约，必须遵守）
- `/Users/xike/Documents/Docs/Askora/docs/product/PRODUCT-STRATEGY.md`
- `/Users/xike/Documents/Docs/Askora/docs/product/PRODUCT-POSITIONING.md`
- `/Users/xike/Documents/Docs/Askora/docs/product/PRODUCT-DEFINITION.md`
- `/Users/xike/Documents/Docs/Askora/docs/specs/ui.md`
- `/Users/xike/Documents/Docs/Askora/docs/specs/ui-pages/*.md`（与本次改造相关的页面）

---

## 3. 权威与冲突处理

执行代理必须遵守以下权威顺序（与 `AGENTS.md` 一致）：

```text
PRODUCT-STRATEGY → PRODUCT-POSITIONING → PRODUCT-DEFINITION
  → Experience Design（仅体验）
  → Specs（ui.md / ui-pages / systems / architecture / platform / interfaces / quality）
  → Code / Tests
```

- 本任务只允许改动 `.design_library/Askora/` 目录及其产物。
- **不得**修改 Product 三份文档、Specs、Experience Design、`AGENTS.md`。
- 若改造过程中发现「Askora 现有最小库」与「Askora 产品文档」冲突，以产品文档为准，并在交付说明中报告该冲突。
- 若发现需要新增一级产品 Capability 或改变产品边界，停止并报告 `PRODUCT DEFINITION GAP`，不要自行决定。
- 若发现现有 `ui/traework/` 中某个组件/模式与 Askora 产品语义冲突（例如「代码编辑器」「任务调度」「插件市场」这类 TraeWork 开发工具语义），不得机械照搬；应判断其是否属于 Askora 学习产品语义，不属于则剔除或改造为学习语境等价物，并在报告中说明取舍理由。

---

## 4. 改造范围：TraeWork → Askora 映射

这是本次改造的核心。你必须在动手前先产出**一份完整的映射表**（见第 6 节 Phase 1），把 TraeWork 的每一层映射到 Askora 的对应层。

### 4.1 品牌与视觉语言

| 维度 | TraeWork（源） | Askora（目标） |
|---|---|---|
| 品牌色 | 绿色 `--bg-brand` | 系统蓝 `#007AFF`（Apple 风格，10 级 `askora-primary-50..900`） |
| 语义色 | `--status-*` 绿/橙/红/警示 | success `#34C759` / warning `#FF9500` / error `#FF3B30` / info `#00B2B2` |
| 中性色 | TraeWork 灰阶 | Apple 分层灰：`#F2F2F7` 画布、`#E5E5EA` 发丝线、`#8E8E93` 弱化文字、`#3A3A3C` 深色表面 |
| 字体 | TraeWork 字体栈 | Inter（SF Pro 替代）+ JetBrains Mono，9 级字阶（Display 56 → Caption 12） |
| 正文基线 | `body-base` 14px/20px | Body 16px/1.6，工作界面以 h3–caption 为主 |
| 间距 | `--spacer-*` | 4px 基准、8pt 网格、`--space-1..8` |
| 圆角 | `--radius-*` | 8/12/16/20/9999px，无直角 |
| 阴影 | 组件内 shadow | 5 级 whisper-quiet 阴影 |
| 表面分层 | `--bg-base-*` / `--bg-overlay-*` | Canvas / Surface / Surface container / Surface container high，侧栏 `#F7F7FA` |
| 图标 | 671 个 TraeWork SVG | 沿用本地 SVG 资产，但仅保留与 Askora 学习语义相关的；缺失时选语义相近本地图标或移除，不引入外部图标库 |

### 4.2 组件层

TraeWork 有 20 个组件契约。改造时按以下三类处理：

1. **直接迁移并品牌化**：与 Askora 学习产品语义兼容的通用组件（Button、Card、Input、Tag、Avatar、Navigation、Tabs、Dialog、Popover、Notif、Alert、Skeleton、Progress、Menu、Breadcrumb、Pagination、Table、Code、Kbd、Switch、Check、Radio、Slider、Select 等）。保留其 DOM 结构与状态机，仅替换 token、字体、圆角、阴影与文案。
2. **语义改写**：TraeWork 特有但可映射到学习语境的组件（如「任务/自动化」→「学习目标/复习计划」，「代码编辑器」→「学习材料/笔记编辑器」，「插件市场」→「知识库/材料库」）。保留交互骨架，替换为 Askora 学习语义的命名与内容。
3. **剔除**：与 Askora 产品边界冲突、且无学习语义等价物的组件/模式（如开发工具专属的 debug、部署、扩展市场等）。在报告中说明剔除理由。

改造后 Askora 组件契约必须至少覆盖：button、card、input、navigation、avatar、tag（现有 6 个）+ 由 TraeWork 迁移并品牌化的组件。每个组件契约保持 TraeWork 的 schema 结构（`tokensConsumed` / `domAnatomy` / `assetsConsumed` / `coverageMatrix` / `provenance`），`sourceKind` 标注为 `migrated-from-traework` 或 `askora-native`，`confidence` 如实标注。

### 4.3 UI Kit 层

TraeWork 有 10 个页面级 UI Kit。改造后 Askora 至少保留并重建：

- `chat-workspace`（三栏：左侧导航 + 中央对话画布 + 右侧检查器）—— Askora 的核心工作区，必须重点打磨。
- 学习语境页面：学习目标、今日学习、知识库/材料库、学习路径、对话记录、设置等（对应 `docs/specs/ui-pages/` 中已定义的页面）。

每个 UI Kit 页面的 `quality-report.json` 如实记录 `previewClassReuseRate` 与 `componentUsageBasis`。

### 4.4 文档层

- `README.md`：扩展为完整品牌叙事 + 视觉基础 + 组件索引 + 消费契约，语言为简体中文为主。
- `SKILL.md`：更新组件清单与快速映射，保持 AI 可消费。
- `css.json` / `library-consumption.json` / `uikit-plan.json`：与改造后的 token、组件、UI Kit 同步。
- `metadata.json`：更新 `version`（+1）。

---

## 5. 文案与语言规则

Askora 的正式产品语言是**简体中文**，文案风格为「专业、克制、技术准确」。

- 按钮用 2–4 字动作动词：发送、收藏、搜索、开始学习。
- 导航项 2–3 字：知识库、笔记、目标、今日。
- 状态标签用名词形式：已收藏（不是「收藏成功」）。
- 界面**不使用 emoji**，视觉系统承担情感表达，文案保持中性。
- 术语偏好：提示词（不用 prompt template）、引用（不用 citation anchor）、智能助手、文档库、历史会话、快捷指令。
- 错误态是诊断性的，空态是说明性的，加载态用精确进度语言。
- 代码注释、组件契约字段名、CSS 类名保持英文（工程语言），UI 可见文案用简体中文。

---

## 6. 执行步骤（Phase）

按顺序执行，每阶段完成即产出可验证产物，不要跳步。

### Phase 1 — 审计与映射（先冻结，再动手）

1. 通读第 2.3 节列出的产品与规范文档。
2. 审计源系统 `ui/traework/`：完整列出 token 分组、20 个组件契约、10 个 UI Kit、图标清单。
3. 审计目标系统 `.design_library/Askora/`：列出当前 6 个组件与 token 现状。
4. 产出**一份完整的 TraeWork → Askora 映射表**，覆盖：token 层、组件层（迁移/改写/剔除三分类）、UI Kit 层、图标层、文档层。
5. 将映射表保存为 `.design_library/Askora/migration-map.md`，作为后续所有改动的依据。

**交付物**：`migration-map.md`。此阶段不写任何 CSS/HTML/JSON 产物。

### Phase 2 — Token 层改造

1. 以 Askora 现有 `colors_and_type.css` 与 `css.json` 为基底，扩展为与 TraeWork 同等完整的 token 体系（color / font / radius / spacing / size / shadow）。
2. 品牌色替换为 `#007AFF` 10 级蓝，语义色替换为 Apple 语义色，中性色替换为 Apple 分层灰。
3. 字阶替换为 Askora 9 级字阶，正文基线 16px/1.6。
4. 保留 Askora 现有 token 的兼容别名（若下游已消费），不破坏现有消费方。
5. 同步更新 `css.json` 与 `colors_and_type.css`，两者必须一致。

**交付物**：更新后的 `colors_and_type.css`、`css.json`。

### Phase 3 — 组件层改造

1. 按映射表逐组件处理：迁移并品牌化 / 语义改写 / 剔除。
2. 每个组件：更新 `components/{slug}.json` 契约、`preview/component-{slug}.html` 预览、`components.css` 中的对应 marker 块，三者必须一致。
3. 更新 `components/index.json`。
4. 组件预览页必须可直接用 `file://` 打开，不依赖远程资源。

**交付物**：全部组件契约、预览页、`components.css`、`components/index.json`。

### Phase 4 — UI Kit 层改造

1. 重建 `ui_kits/chat-workspace/` 为 Askora 三栏学习工作区。
2. 按 `docs/specs/ui-pages/` 重建学习语境页面 UI Kit。
3. 每个 UI Kit 页生成 `quality-report.json`，如实记录组件复用率。

**交付物**：UI Kit 页面 + `quality-report.json` + `uikit-plan.json`。

### Phase 5 — 文档与元数据

1. 扩展 `README.md`、`SKILL.md`。
2. 同步 `library-consumption.json`、`uikit-plan.json`、`metadata.json`（version +1）。
3. 更新 `migration-map.md` 的完成状态。

**交付物**：全部文档与元数据。

### Phase 6 — 验证与收尾

1. 逐项核对第 7 节验收标准。
2. 用浏览器（或 `file://`）打开全部 preview 与 UI Kit 页面，人工核对视觉一致性。
3. 生成一份改造完成报告，保存为 `.design_library/Askora/migration-report.md`，包含：改动文件清单、组件迁移/改写/剔除清单、未完成项、与产品文档的任何冲突、候选 SHA。

---

## 7. 验收标准（Completion Definition）

只有全部满足才算完成：

- 未违反 `PRODUCT-STRATEGY.md` / `PRODUCT-POSITIONING.md` / `PRODUCT-DEFINITION.md`。
- 源系统 `ui/traework/` 与 `ui/research/traework/` 未被修改。
- 所有改动限定在 `.design_library/Askora/` 内。
- token / 组件契约 / 预览页 / components.css / index.json 五者一致，无漂移。
- 品牌视觉完全 Askora 化：系统蓝 `#007AFF`、Apple 分层灰、9 级字阶、4px 网格、5 级阴影、无直角。
- UI 可见文案为简体中文，符合第 5 节文案规则，无 emoji。
- 组件契约 `sourceKind` / `confidence` 如实标注，无伪造证据。
- 所有 preview 与 UI Kit 页面可用 `file://` 直接打开，无远程依赖、无布局错乱。
- 图标仅使用本地 SVG 资产，未引入外部图标库/图标字体/CDN。
- 与产品文档的任何冲突都已显式报告，未用代码制造既成事实。
- 未留下占位实现、TODO 伪完成或仅 Mock 的「已完成」结论。

---

## 8. 默认验证命令

在 Mac 本地按需执行：

```bash
# 检查目标目录结构完整性
find /Users/xike/Documents/Docs/Askora/.design_library/Askora -type f | sort

# 校验 JSON 合法性
python3 -c "import json,glob; [json.load(open(f)) for f in glob.glob('/Users/xike/Documents/Docs/Askora/.design_library/Askora/**/*.json', recursive=True)]; print('JSON OK')"

# 校验 css.json 与 colors_and_type.css 的 token 一致性（自行编写校验脚本）
# 校验源系统未被修改（与改造前快照对比，或 git status 确认 ui/traework 无变更）
```

若命令失败，必须区分「本次改造新增失败」与「与本次改造无关的既有失败」，不得删除测试或弱化断言来伪造 PASS。

---

## 9. 报告要求

完成后，向用户交付一份简洁总结，包含：

- 改造范围与最终组件/UI Kit 清单。
- 迁移 / 改写 / 剔除的组件分别有哪些。
- 与产品文档的冲突（如有）与取舍理由。
- 未完成项与下一步建议。
- 产物位置：`.design_library/Askora/`。
