# Askora UI Redesign Specification Set

> 状态：`FROZEN`
> 权威性：Canonical UI Implementation Contract
> 需求确认：2026-08-08，用户确认“全部按推荐”
> 冻结批准：2026-08-08，用户明确批准冻结并授权从 UI-01 开始串行实施
> UI-02 拆分批准：2026-08-08，用户采纳 Canonical 资料库 MVP；UI-02A Library/Knowledge Map 已完成

## 1. 目的

本目录把已确认的 UI 方向整理为一套可审查、可冻结、可拆分 Vertical Slice 的实现前规格。目标不是给现有聊天页面换皮，而是让 UI 与 Askora 已冻结的长期学习闭环一致：

```text
今日学习 / 学习目标 / 学习路径
→ LearningActivity
→ 学习工作台或沉浸学习
→ 实际作答与帮助记录
→ 学习证据 / 复习建议 / 下一活动
```

本 Spec Set 只细化产品呈现、信息架构、交互状态、只读 Query DTO 和质量门禁。它不得改变八系统状态所有权、TeachingAction、AssessmentResult、MasteryEstimate、LearningPlan 或 ReviewSchedule 的既有语义。

## 2. 已确认的产品决策

以下决策已经由用户确认，本 Spec Set 不再保留平行候选：

1. 组合使用四个 UI 方向：
   - “学习驾驶舱”作为全局框架；
   - “导师工作台”作为 LearningActivity 的主要交互页；
   - “知识地图”作为资料库中的结构化视图；
   - “沉浸学习”作为同一 LearningActivity 的专注呈现模式。
2. 全局信息架构采用：今天、学习目标、学习路径、资料库、学习证据、历史记录、设置。
3. “对话学习”不再作为顶层产品入口；对话是活动执行手段。
4. 允许新增必要的只读 Query/API，但不得借 UI 改造修改教学策略、算法或状态所有权。
5. 学习画像优先显示独立、延迟、迁移、提示依赖、证据充分度与置信度；legacy compatibility 指标默认不进入主视觉层。
6. macOS 桌面端优先，同时保证 360px 窄屏可用；沿用克制的 Apple 风格、系统蓝、系统字体与 Lucide 图标。
7. 保留正式手机号登录；开发自动登录只能由本地开发配置显式启用。
8. 先冻结 Spec，再生成 Vertical Slice 与 EXEC；未冻结前不执行产品代码修改。

## 3. 文件索引

- [信息架构与导航合同](information-architecture.md)：产品模式、路由、全局 Shell、桌面与窄屏布局。
- [页面与交互状态合同](screen-contracts.md)：各页面内容、状态、动作、空态与失败语义。
- [UI 数据与 Query 合同](data-contracts.md)：领域来源、UI Read Model、提议的 additive Query/API 与兼容边界。
- [视觉系统合同](visual-system.md)：品牌语言、色彩、排版、组件、数据可视化与暗色模式。
- [质量、迁移与验收合同](quality-and-migration.md)：分阶段交付、测试、兼容迁移、DoD 与阻断条件。

## 4. 权威关系

本 Spec Set 必须服从：

1. `docs/specs/**` 已冻结 Canonical Implementation Contracts；
2. `docs/adr/ADR-0001`、`ADR-0002`；
3. `docs/design/个人AI辅助学习平台设计方案.md` 第 10 章产品体验设计；
4. 当前代码和测试只用于描述迁移起点，不得反向改变上游语义。

若本 Spec Set 与其他已冻结 Spec 冲突，以更高层的领域、系统与接口合同为准，并登记 `SPEC GAP`。实现只能通过已冻结 Vertical Slice 与 active EXEC 进入代码。

### 4.1 上游追踪矩阵

| Spec area | 主要上游合同 | 本 Spec Set 只允许细化的内容 |
|---|---|---|
| Information Architecture / Screens | `architecture/system-architecture.md`、Canonical Design 10.1～10.4 | 导航、页面层级、呈现模式与交互状态 |
| Today / Goals / Path | `systems/06-learning-planner.md`、`systems/07-review-scheduler.md` | owner 已发布状态的只读组合与解释 |
| Tutor / Focus | `systems/04-assessment.md`、`systems/05-teaching-policy.md`、`systems/08-ai-orchestration.md` | 同一 activity/execution 的呈现与用户请求入口 |
| Library / Knowledge Map | `systems/01-content-knowledge.md`、`systems/02-retrieval.md` | 文档、知识节点、关系与来源的只读呈现 |
| Evidence | `systems/03-learner-model.md`、`architecture/state-ownership.md` | canonical projection、置信度、证据充分度与 legacy 标注 |
| Rich Response | `interfaces/render-content-contract.md`、`quality/security-standard.md` | 已冻结 typed payload 的布局复用与安全回退 |
| Quality / Migration | `quality/testing-standard.md`、`quality/definition-of-done.md` | UI-specific gates、迁移次序与声明边界 |

## 5. 当前实现事实边界

当前前端已存在：

- 登录/注册；
- 对话会话、消息历史和非流式/流式 transport client；
- `RenderPayloadV1` 的 Markdown、公式、typed cards 与 citations 渲染；
- 基于 `/users/profile` 的学习画像页面；
- 账号与本地运行状态页面；
- “知识点”占位页面。

当前后端已公开：

- `/api/v1/dialog/**`；
- `/api/v1/users/profile`；
- `/api/v1/documents/**`；
- `/health/config`。

当前 UI-02A 已公开资料库/知识地图 Query；Book-to-Learning baseline 已公开单资料 Goal、mapping、diagnostic、plan、activity selection 与 teaching façade。完整 Goals/Path/Evidence Query 仍未实施。UI-02B1 只冻结单资料 launch 路径，不把它描述为完整 UI-02B。

## 6. 明确不在本 Spec Set 中授权的事项

- 新增或改变 Teaching Strategy、TeachingStage、TeachingAction、提示与答案暴露规则；
- 新增 mastery threshold 或在前端自行判断“已掌握”；
- 让 UI、API handler 或 LLM 修改 LearningPlan、ReviewSchedule、LearnerState；
- 新增学习目标创建/确认、计划编辑或复习时间修改命令；
- 引入新的生产依赖、状态 owner、外部服务或遥测平台；
- 把 UI 正常、活跃度、连续天数或会话时长宣称为学习效果；
- 跳过已冻结 Vertical Slice/active EXEC 直接修改产品代码。

## 7. 实施流程

```text
FROZEN UI SPEC
→ UI-01 Vertical Slice + EXEC-015
→ UI-01 DONE gate
→ UI-02A Library/Knowledge Map + EXEC-016
→ UI-02A DONE gate
→ UI-02B1 Material-to-Learning Launch + EXEC-025
→ UI-02B1 DONE gate
→ UI-02B Goals/Path/Evidence + independent EXEC
→ UI-02B DONE gate
→ UI-03 Vertical Slice + independent EXEC
→ UI-03 DONE gate
```

UI-01、UI-02A 与 UI-02B1 已 DONE。完整 UI-02B/UI-03 仍受严格串行门禁约束，不得由 UI-02B1 暗含扩展。
