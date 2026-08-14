# Askora 页面元素规划（Page Element Planning）

> 状态：**规划草稿（Planning）— 非 Canonical Spec**
> 创建日期：2026-08-13
> 上游：
> - 体验架构：[`../../design/experience/EXPERIENCE-ARCHITECTURE.md`](../../design/experience/EXPERIENCE-ARCHITECTURE.md)（空间中心 IA + 4 条核心旅程）
> - 交互语义：[`../../design/experience/INTERACTION-MODEL.md`](../../design/experience/INTERACTION-MODEL.md)（7 类原语 + 交互层级）
> - 学习体验：[`../../design/experience/LEARNING-EXPERIENCE.md`](../../design/experience/LEARNING-EXPERIENCE.md)
> - 设计系统与屏幕契约：[`../ui.md`](../ui.md)
> 语言约定：**界面文案统一简体中文**（`EXP-ARCH §10`）

---

## 1. 本规划是什么

本目录按「一个页面一份文档」组织，规划 Askora 前端**全部现有页面**上应呈现的元素：

- **文字**：标题、正文、按钮 label、placeholder、空态/错误态文案、tooltip 微文案
- **按钮**：每个 Action / Navigation / Control 及其层级（primary / secondary / contextual）
- **Icon**：lucide 图标名、语义与 accessible name
- **状态**：LOADING / EMPTY / READY / PARTIAL / STALE / ERROR / UNAUTHORIZED / CONFLICT / SAVING / SAVED / RECOVERABLE / DISABLED 的逐元素表达
- **无障碍**：aria-label、键盘路径、focus 返回、live region

每一页的每个元素都标注：

```text
交互语义（7 原语之一）→ 组件/模式 → 设计系统 token → 状态覆盖
```

遵守 [`UI-DS-002 Semantic Before Component`](../ui.md)：先定语义，再定组件，禁止反推。

## 2. 规划依据（已梳理的用户行为）

页面元素必须服务于以下已冻结的用户侧主路径（`EXP-JOURNEY-001 ~ 004`）：

| 旅程 | 用户做 | 规划约束 |
|---|---|---|
| 001 用资料开始学习 | 上传 → 处理 → 选「加入学习空间 / 马上开始学习」→ 进入对话 | 处理状态诚实；目标管理不出现 |
| 002 回来继续 | 打开 App 先到 Welcome → 点已有对话恢复，或选空间「继续学习」 | 打开即 Welcome；恢复不新开；「继续学习」必须新开 |
| 003 在对话里学习 | 定向 → 作答 → 反馈 → 帮助/看原文 → 再试/独立验证 → 可恢复 | 学习画布；帮助/暴露/待验证可读 |
| 004 建立或扩充空间 | ＋新建空间 → 空空间 → 加资料 → 现在学/不学 | 空空间诚实；后补资料弹窗同 001 |

顶层交互原语（`INT-001~007`）：`Navigation / Action / Control / Selection / Disclosure / InteractiveContent / StatusFeedback`。

交互层级（`INT-H-001~004`）：`Primary Task / Secondary Action / Contextual Action / Advanced-Audit`。

## 3. 页面分组与文件索引

### A. 欢迎与空间入口（Journey 001/002/004 的起点）
| 页面 | 文件 | 状态 |
|---|---|---|
| 欢迎页（默认目的地） | [`welcome.md`](welcome.md) | 规划 |
| 新建空间 | [`course-create.md`](course-create.md) | 规划 |

### B. 资料与入库（Journey 001/004 的「放入资料」）
| 页面 | 文件 | 状态 |
|---|---|---|
| 资料库 | [`library.md`](library.md) | 规划 |
| 资料去向（加入空间/马上开始学习） | [`material-destination.md`](material-destination.md) | 规划 |
| 用资料开始学习（Launch） | [`book-learning-launch.md`](book-learning-launch.md) | 规划 |

### C. 学习画布（Journey 003）
| 页面 | 文件 | 状态 |
|---|---|---|
| 学习空间（三栏画布） | [`learning-workspace.md`](learning-workspace.md) | 规划 |
| 学习活动 | [`activity-learning.md`](activity-learning.md) | 规划 |
| 导师工作台（兼容 Tutor） | [`tutor-workspace.md`](tutor-workspace.md) | 规划 |
| 对话 | [`chat.md`](chat.md) | 规划 |

### D. 学习管理与兼容页（不构成 L0，仅明确 user job 下可达）
| 页面 | 文件 | 状态 |
|---|---|---|
| 目标列表 / 详情 / 编辑 | [`goals.md`](goals.md)、[`goal-detail.md`](goal-detail.md)、[`goal-editor.md`](goal-editor.md) | 规划 |
| 学习路径 | [`learning-path.md`](learning-path.md) | 规划 |
| 学习证据 | [`evidence.md`](evidence.md) | 规划 |
| 学习历史 | [`history.md`](history.md) | 规划 |
| 今天（兼容） | [`today.md`](today.md) | 规划 |
| 学习（兼容） | [`learning.md`](learning.md) | 规划 |
| 知识 | [`knowledge.md`](knowledge.md) | 规划 |
| 个人档案 | [`profile.md`](profile.md) | 规划 |

### E. 工具（App Utility，不与产品域等权）
| 页面 | 文件 | 状态 |
|---|---|---|
| 设置 | [`settings.md`](settings.md) | 规划 |
| 恢复中心 | [`recovery-center.md`](recovery-center.md) | 规划 |
| 不可用页 | [`unavailable.md`](unavailable.md) | 规划 |

### F. 全局组件
| 组件 | 文件 | 状态 |
|---|---|---|
| 侧栏（Left = Where） | [`sidebar.md`](sidebar.md) | 规划 |
| 工作区上下文 | [`workspace-context.md`](workspace-context.md) | 规划 |

## 4. 每页文档的统一模板

每份页面文档包含以下章节：

1. **页面职责**：该页承担的用户 job、对应旅程与契约 ID
2. **布局区划**：页面拆成哪些区域（顶部 / 主体 / 侧栏 / 弹窗）
3. **元素清单**：表格列出每个元素的
   - 类型（文本 / 按钮 / icon / 输入 / 状态标签）
   - 中文文案（含 icon-only 的 aria-label）
   - 交互语义（7 原语）
   - 层级（Primary / Secondary / Contextual / Advanced）
   - 组件模式与 token（映射 ui.md）
   - 适用状态
4. **状态矩阵**：该页各区域在 LOADING / EMPTY / READY / PARTIAL / STALE / ERROR / 特殊态下的文案与行为
5. **无障碍要求**：icon-only accessible name、键盘路径、focus 返回、live region
6. **禁止事项**：该页不得出现什么（对齐 ui.md Forbidden Implementations）

## 5. 文案撰写原则（规划统一采用）

依据 `EXP-ARCH §10` 与 `LEARNING-EXPERIENCE §11`：

- **界面统一简体中文**；工程/诊断层保留 canonical 英文 naming（`Workspace` / `LearningActivity`）
- 用户界面用「空间」「对话」「资料」，不用「课程」「Chat 1/2/3」「LearningGoal」
- 状态词必须诚实：区分「建议 / 估计 / 已验证 / 已使用帮助 / 已暴露答案 / 待独立验证」
- 错误表达三要素：发生了什么 / 数据是否安全 / 现在能做什么
- 系统/模型故障不得显示成「你答错了」
- 空态必须同时回答「缺什么」与「能做什么」
- 不用游戏化奖励替代真实学习证据

## 6. 与现状的关系

每份文档记录该页**现状元素**（当前 .jsx 实际文案/按钮/icon）与**规划目标**（应当呈现的元素）。规划目标是本目录的决策结果；现状仅作迁移基准。两者冲突时，以体验合同与规划为准，冲突点标注 `GAP` 供实现阶段处理。

## 7. 落地路径（后续）

```text
本规划
→ 屏幕/导航契约（ui.md）对齐校验
→ Learning Interaction Contract 细化（ui.md 交互契约章节）
→ 前端组件实现 + 测试
→ 全量质量门禁（UI-QR-*）
```
