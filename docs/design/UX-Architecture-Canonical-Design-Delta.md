# Askora UX Architecture — Canonical Design Delta

> 状态：**FROZEN — Canonical Design Delta Record**
>
> 冻结日期：2026-08-10
>
> 审查基线：GitHub `main@771750bb1a9daefe520135ffd36f2dd88082afaa`
>
> 适用范围：Askora Desktop/Web Learning Workspace、Workspace Context、Library v1 Feature Exposure
>
> 用户授权：2026-08-10 明确采纳三栏式学习架构、Workspace 上下文、可隐藏辅助栏、Learning Context Drawer、Learning 去管理化与 Library 去 OCR 暴露
>
> 上位约束：[`../product/PRODUCT-POSITIONING.md`](../product/PRODUCT-POSITIONING.md)
>
> 既有设计基线：[`Interactive-Element-System-Canonical-Design-Delta.md`](Interactive-Element-System-Canonical-Design-Delta.md)
>
> 当前实现合同：[`../specs/ui/`](../specs/ui/)
> 当前实现：`apps/frontend/src/`

---

## 0. Freeze Declaration

本文件冻结 Askora 下一阶段 UX Architecture 的产品级增量设计。

核心目标是把 Askora 从“用户管理 Goal / Plan / Progress 等系统对象”进一步收敛为：

> 用户选择长期学习上下文，在中央完成学习；系统在需要时提供方向、资料和笔记，而不把内部学习系统变成 Dashboard 或管理控制台。

本次冻结只改变 information architecture、interaction architecture 与 feature exposure，不改变 SYS01～SYS08 canonical ownership，也不授权直接修改代码。

标准治理链仍为：

```text
PRODUCT-POSITIONING
→ 本 Canonical Design Delta
→ Accepted ADR / ADR Delta
→ 更新 docs/specs/ui/** 与必要 query/data contracts
→ Vertical Slice / EXEC
→ Frontend / Backend implementation
→ Acceptance
```

在 ADR、Spec 与 EXEC 完成前，任何实现任务必须返回 `BLOCKED_BY_SPEC_GAP`，不得自行决定 Workspace 切换语义、UserNote durable ownership、Context Drawer 数据来源或旧 Learning route 的退役策略。

---

## 1. Current-main Reality and Gap

当前 `main` 已具备：

- L0：Today / Learning / Library；
- Learning L1：Goals / Plan / Progress / History；
- `/learning/**` canonical routes；
- Tutor Workspace 的会话历史左栏与中央对话画布；
- Library 的搜索、导入、资料列表、知识地图、原文检查器及显式 OCR 请求/复核 UI；
- `PRODUCT-POSITIONING` 与 ADR-0016 已冻结 Workspace 为真实高层数据隔离边界，但 durable Workspace implementation 尚未完成。

因此存在以下 Design–Implementation / Design–Design Gap：

| Area | Current frozen/implemented model | This frozen delta |
|---|---|---|
| Learning IA | Goals / Plan / Progress / History 是常驻 L1 管理 Facets | Learning 不再暴露 Goal / Plan / Progress 管理结构 |
| Workspace | UI 仍缺少真实 Workspace context switch | 左栏必须呈现并切换 canonical current Workspace |
| Learning Workspace | 左栏偏会话历史，中央为对话 | 左栏负责 Where，中央负责 Learn，右栏负责 Notes / Reference |
| Goal / Stage / Next | 适合 Inspector 或独立页面 | 降为中央输入区上方默认收起的 Learning Context Drawer |
| Right rail | Learning Context Inspector | V1 改为可隐藏辅助工作区：学习笔记 + 当前资料 |
| Library OCR | compatibility/advanced，可在正确 context 暴露 | v1 正常 UI 不暴露 OCR 入口、状态、复核或发布流程 |

这意味着现有 `UI-IA-*`、`UI-SCREEN-*`、UI-03/EXEC-043/045 与相关 Linear 验收项不能继续作为新方向的直接实现依据，必须先完成合同吸收。

---

## 2. First-principles UX Model

Askora 桌面学习体验固定回答四个问题：

| Region | User question | Responsibility |
|---|---|---|
| 左栏 | 我在哪里学习？ | Product Navigation + Workspace Context |
| 中栏 | 我正在理解、回答和练习什么？ | Primary Learning Canvas |
| Context Drawer | 我处于什么阶段，接下来大概去哪？ | Lightweight Learning Orientation |
| 右栏 | 我需要记录或对照什么？ | Notes / Current Materials |

正式三栏模型冻结为：

```text
Where                    Learn                         Reference / Notes

Global Navigation       Teaching content             User-authored notes
Current Workspace       Questions                    Current source material
Workspace switch        Learner answers              Citation/source context
                        Feedback
                        Learning Context Drawer
                        Composer
```

三栏必须共享同一个 canonical `current_workspace_id`。切换 Workspace 不是只改变左栏选中态，而是切换中央学习、右栏笔记/资料与 Context Drawer 的全部查询范围。

---

## 3. Left Rail — Navigation and Workspace Context

### 3.1 Stable responsibilities

左栏只承担：

1. 稳定产品导航；
2. 当前 Workspace 可见性；
3. Workspace 切换。

左栏不得承担 Goal、Plan、Progress、Evidence、知识图谱或系统状态详情。

### 3.2 Workspace semantics

- Workspace 必须是 ADR-0016 / `WSP-*` 定义的 durable Workspace，不得使用 subject、route state、session 或前端 local state 冒充；
- 当前 Workspace 名称必须可见；
- 只有一个 Workspace 时不得显示虚假的下拉/切换 affordance；
- 多 Workspace 时提供明确的 Selection pattern；
- 所有 Material、Note、Goal/Plan projection、Learner State、LearningSession 与 retrieval query 必须服从当前 Workspace scope；
- 不得提供默认跨 Workspace 聚合或全局搜索。

### 3.3 Switching safety

切换 Workspace 前必须处理：

- 未提交回答；
- 正在 streaming 的 run；
- 尚未持久化的笔记；
- 当前打开资料与引用位置；
- 可恢复的 active LearningSession。

Spec 必须定义明确的 saved / saving / failed / recoverable 状态；不得通过清空 React state 假装切换成功。

---

## 4. Center — Primary Learning Canvas

中央区域是唯一 Primary Task surface，优先呈现：

- AI 教学内容；
- 当前问题/任务；
- 学习者回答；
- 反馈与下一轮教学；
- streaming、完成、失败与恢复状态；
- 必要 citation、assistance 与 validation obligation。

中央区域不得演变为同时展示 Goal、Plan、Progress、热力图、知识图谱、资料管理和模型状态的 Dashboard。

Today、Library 或恢复入口可以启动/恢复 LearningActivity，但进入学习后必须收敛到同一 Learning Workspace，不建立第二份对话、Attempt、TeachingAction 或 transcript truth。

---

## 5. Learning Context Drawer

### 5.1 Placement and default state

Learning Context Drawer 固定放在中央学习画布底部、composer/输入区正上方。

它不是第四栏，也不占用右侧辅助栏。

默认状态：**收起**。

收起时只显示一行方向信息，例如：

```text
监督学习基础 · 接下来：残差诊断
```

### 5.2 Expanded content

展开后只允许：

- 当前阶段；
- 阶段目标；
- 接下来 1～3 个知识点或教学方向。

禁止在 V1 Drawer 中加入：

- 完整 Goal editor；
- 完整 Learning Plan；
- Progress Dashboard；
- Evidence 管理；
- mastery 编辑；
- ReviewSchedule 编辑；
- TeachingAction/Policy 控制。

### 5.3 Truth and wording

- 所有内容必须来自 canonical/versioned query 或明确的 `MISSING/PARTIAL/STALE` 状态；
- 前端不得根据聊天文本、标题顺序或概率阈值自行推断；
- LLM 不得把语言生成结果直接写成 canonical next knowledge point；
- “接下来”是动态教学方向，不得承诺为不可变计划；
- 当数据不足时应显示“当前阶段信息不足”或隐藏缺失字段，不得补造。

### 5.4 Interaction behavior

- expand/collapse 只改变 presentation state，不触发 owner command；
- 切换 Workspace 或 LearningSession 后重新查询对应 scope；
- presentation-only 的展开状态 MAY 保留；
- Drawer 请求失败不得使中央学习画布整体失败；
- 窄屏变为可访问的 Disclosure/Sheet，不得永久消失。

---

## 6. Right Auxiliary Rail

### 6.1 Purpose

右栏服务“边学边写、边学边对照”，不是状态仪表盘。

右栏整体必须可隐藏；隐藏后中央学习任务仍可完成，重新打开后上下文必须可恢复。

### 6.2 V1 tab set

V1 只允许两类内容：

1. **学习笔记**；
2. **当前资料**。

具体呈现 MAY 包含一个固定“学习笔记”Tab，以及由引用/查看原文动作上下文打开的一个或多个 Material tabs。V1 不提供通用“+”扩展宿主，也不允许用户把任意未来模块加入右栏。

### 6.3 Learning Notes

- 笔记是 user-authored durable data，不是 AI Summary；
- 必须 Workspace-scoped，并保留可追踪的 activity/material anchor（若存在）；
- 必须提供 saving / saved / failed / recoverable feedback；
- 不得在切换 Workspace、隐藏右栏或退出学习时静默丢失；
- AI 可以在用户明确请求时辅助整理，但不得无确认覆盖用户原文；
- UserNote 的 exact object、version、autosave 与 conflict contract 必须在 Spec 中冻结后再实现。

### 6.4 Current Materials

- 用户点击 citation / “查看原文”时，资料在右栏上下文打开，中栏不离开当前学习；
- Material、SourceSpan 与 locator 必须来自当前 Workspace 的 canonical source refs；
- 跨 Workspace ref 必须 fail closed；
- 资料 tab 切换不创建新 LearningActivity，不改变 TeachingAction；
- 缺少可显示 SourceSpan 时诚实显示不可用，不得用摘要或文件名伪造原文；
- 右栏失败只局部降级，除非当前任务的必要证据因此不可验证。

### 6.5 Explicitly forbidden V1 tabs

以下全部为 deferred candidates，不进入 V1、不创建 placeholder、不显示 disabled tab：

```text
大纲
Evidence
知识图谱
Progress
AI Summary
Flashcards
错题本
```

未来加入任何候选都必须有独立 user-job evidence、owner/query contract、隐私与恢复边界，并形成新的 Design Delta / Spec。

---

## 7. Learning Is Not a Management Console

### 7.1 Frozen exposure rule

Learning 主界面不再暴露以下常驻管理结构：

```text
Goals
Plan / Path
Progress
History-as-management-facet
```

这不删除 LearningGoal、LearningPlan、LearnerState、Evidence、ReviewSchedule 或 History 的 canonical truth，也不改变其 owner。

它改变的是用户暴露方式：

- 系统对象继续驱动教学；
- 用户只在当前学习任务需要时看到简洁、可理解的上下文；
- 必要的创建、纠正、确认或审计 MAY 进入独立 task flow / contextual disclosure；
- 不建立长期常驻的系统对象管理中心；
- 不要求用户先管理 Goal/Plan/Progress 才能学习。

### 7.2 Route migration gate

现有 `/learning/goals|plan|progress|history` 不得由实现任务直接删除。

ADR/Spec 必须先决定：

- 哪些 route 退役、redirect、保留为 bounded compatibility 或转为 contextual task flow；
- historical deep link 和 back behavior；
- existing goal commands 的可发现入口；
- 当前 active LearningSession 与旧 History 的恢复入口；
- 无副作用 redirect 与 retirement window。

在该决策冻结前，旧 route 既不能被视为新 UX 的完成证据，也不能被未经治理地移除。

---

## 8. Library V1 Does Not Expose OCR

### 8.1 Frozen UI boundary

Library v1 正常产品 UI 不得暴露：

- “识别扫描 PDF”入口；
- OCR engine/runtime 状态；
- OCR candidate；
- OCR review/publish flow；
- OCR 置信度、bbox、image hash 等实现细节；
- 任何把 OCR 描述为 v1 核心能力的文案。

### 8.2 Honest fallback

扫描 PDF 无可靠文本时，允许显示：

- 无法可靠提取文本；
- partial / unsupported；
- 可采取的非 OCR 核心下一步（例如更换文本型 PDF 或其他受支持格式）。

不得为了“功能完整”要求用户管理 OCR Pipeline。

### 8.3 Runtime boundary

历史/optional OCR code 是否保留由 v1 Product Architecture cleanup 决定。本 Delta 只冻结产品暴露：即使 optional runtime 暂时存在，也不得从正常 v1 Library UI 到达。

---

## 9. Responsive and Accessibility Contract

### 9.1 Desktop

在 1440×900：

```text
Left Rail | Primary Learning Canvas | Optional Right Rail
```

中央区域保持唯一 Primary hierarchy；右栏可隐藏。

### 9.2 Compact and narrow screens

- 1024×768：右栏默认可收起或以 overlay/sheet 打开；
- 768×1024：左栏为 compact rail/drawer，右栏为 sheet；
- 360×800：单列，先学习内容，再 Context Drawer/Composer；Notes/Material 通过可访问 sheet 打开；
- 不允许页面横向滚动；
- 不允许三层关键嵌套滚动；
- keyboard、touch、screen reader 必须能打开/关闭/切换 Rail 与 Drawer；
- focus 返回触发点；
- 右栏隐藏不能隐藏完成任务所需的唯一 citation、安全错误或 validation obligation。

---

## 10. Canonical Decision Register

| ID | Frozen Decision | Status |
|---|---|---|
| `UXA-CD-001` | Askora 学习体验使用 Left Where / Center Learn / Right Notes-Reference 三栏职责 | **FROZEN** |
| `UXA-CD-002` | 三栏共享同一 canonical current Workspace | **FROZEN** |
| `UXA-CD-003` | 左栏包含稳定产品导航与 Workspace Context，不展示学习系统详情 | **FROZEN** |
| `UXA-CD-004` | 中栏是唯一 Primary Learning Canvas，不是 Dashboard | **FROZEN** |
| `UXA-CD-005` | Learning Context Drawer 位于 composer 上方且默认收起 | **FROZEN** |
| `UXA-CD-006` | Drawer 只展示当前阶段、阶段目标与接下来 1～3 项动态方向 | **FROZEN** |
| `UXA-CD-007` | 右栏整体可隐藏，V1 仅学习笔记与当前资料 | **FROZEN** |
| `UXA-CD-008` | citation/查看原文在右栏上下文打开，不中断中央学习 | **FROZEN** |
| `UXA-CD-009` | Learning 不再暴露 Goals/Plan/Progress/History 常驻管理 Facets | **FROZEN** |
| `UXA-CD-010` | canonical Goal/Plan/Evidence/State 继续存在并驱动系统，不建立第二 truth | **FROZEN** |
| `UXA-CD-011` | Library v1 正常 UI 完全不暴露 OCR 入口、状态、复核或发布 | **FROZEN** |
| `UXA-CD-012` | 大纲/Evidence/知识图谱/Progress/AI Summary/Flashcards/错题本全部 deferred | **FROZEN** |
| `UXA-CD-013` | 旧 Learning routes 先由 ADR/Spec 决定迁移，不由实现直接删除 | **FROZEN** |
| `UXA-CD-014` | Workspace 切换必须处理 draft/stream/note/session recovery，不能只改 UI selection | **FROZEN** |

---

## 11. Supersession and Conflict Register

| Existing decision/contract | Disposition | Required absorption |
|---|---|---|
| `IES-CD-008`：Goal/Path/Progress/History 为 Learning L1 facets | **SUPERSEDED** | 新 ADR + `UI-IA-*` |
| `UI-IA-020..022` Learning facets | **SUPERSEDED** | 重写 Learning domain exposure/navigation |
| `UI-IA-030` `/learning/**` route table | **AMEND / MIGRATION REQUIRED** | 冻结 redirect/compatibility/task-flow strategy |
| `UI-IA-041` Workspace Shell：Activity/History Rail + Context Inspector | **SUPERSEDED IN LAYOUT** | 左栏 Workspace Context；右栏 Notes/Material；Drawer 独立 |
| `UI-SCREEN-020..062` Goals/Plan/Progress/History 常驻页面 | **SUPERSEDED IN DEFAULT EXPOSURE** | 保留 owner semantics，重写 user-facing jobs |
| `UI-SCREEN-070` Learning Context Inspector | **AMEND** | Context Drawer + Notes/Material rail |
| `UI-SCREEN-091` OCR 可 contextual reveal | **SUPERSEDED FOR V1 UI** | OCR 从正常 v1 UI 不可达 |
| UI-03 / EXEC-043 的 Learning four facets AC | **STALE FOR NEW WORK** | 新 Vertical Slice / EXEC，不得直接继续验收为目标状态 |
| EXEC-045 的 OCR advanced/compatibility exposure | **STALE FOR NEW WORK** | 与 v1 cleanup / Library no-OCR UI 对齐 |

未列出的 Product Positioning、Workspace ownership、LearningActivity identity、canonical state ownership、citation/security、recovery 与 local-first hard constraints继续有效。

---

## 12. Required Spec/Query Decisions Before Implementation

下一阶段必须至少冻结：

1. current Workspace query、switch command 与 active Workspace persistence；
2. Workspace list/empty/single/multiple/error/recovery states；
3. Workspace 切换对 draft、streaming、LearningSession 与 Material tabs 的处理；
4. UserNote object、scope、anchor、version、autosave、conflict 与 recovery；
5. Drawer 的 canonical stage/goal/next-direction query 及 `MISSING/PARTIAL/STALE` 语义；
6. Current Material tabs 与 SourceSpan retrieval/cross-workspace rejection；
7. right rail presentation-state persistence 与 narrow-screen pattern；
8. `/learning/**` route migration/compatibility/retirement；
9. Library no-OCR UI 与 scanned-PDF unsupported/partial copy；
10. responsive/keyboard/touch/screen-reader test oracle；
11. Engineering、Policy/Ownership 与 Learning Evidence 分开验收。

如果 durable Workspace / Workspace-scoped learner records 尚未实现，UI implementation 必须依赖对应 Product Architecture Issues，不得先做 frontend-only Workspace truth。

---

## 13. Non-goals

本 Delta 不授权：

- 修改 React、CSS、API、数据库或 migration；
- 删除 Goal/Plan/Evidence/History canonical data；
- 重写 Teaching Policy 或 planner；
- 新建第二 Tutor/Chat/Note/Material truth；
- 建立跨 Workspace Global Library；
- 把 Workspace 建模为 Tenant/Organization/Account；
- 实现 deferred tabs；
- 扩展 OCR；
- 用 UI/合成学习者/模型连通性声称真人学习效果。

---

## 14. Acceptance for Design Freeze

本 Design Delta 只有在以下条件满足时才视为冻结完成：

- 文档进入 GitHub `main` 并加入 Design index；
- 当前 main 的 Spec/Implementation Gap 被明确记录；
- 新旧设计 supersession 边界明确；
- Linear 存在 ADR/Spec 吸收 Issue；
- Linear 存在受该门禁约束的实施 Issue；
- 旧 UI-03/Learning/Library 验收项不再被误当作新方向的完成标准；
- 本阶段没有直接修改产品代码。

---

## 15. Final Frozen Model

```text
Askora
│
├─ Left: Where
│  ├─ Today / Learning / Library
│  └─ Current Workspace / Switch
│
├─ Center: Learn
│  ├─ Teaching / Question / Answer / Feedback
│  ├─ Context Drawer: Stage / Stage Goal / Next
│  └─ Composer
│
└─ Right: Reference / Notes (hideable)
   ├─ Learning Notes
   └─ Current Material tabs
```

最终原则：

> **Askora 负责管理学习系统；用户负责学习。**

Goal、Plan、Evidence、Learner State 与 Review Scheduling 继续作为可信系统事实存在，但不再决定用户必须面对多少页面、栏目和管理动作。
