# Askora Screen & Navigation Contracts

> 状态：**Canonical UI/UX Implementation Contract — Current Only**  
> 冻结日期：2026-08-11  
> 上游产品定义：`docs/product/PRODUCT-DEFINITION.md`  
> Governing Experience：`docs/design/experience/EXPERIENCE-ARCHITECTURE.md`、`docs/design/experience/INTERACTION-MODEL.md`  
> Governing ADR：ADR-0014、ADR-0015、ADR-0018  
> 技术上游：Workspace / Goal / Activity / Recovery / Onboarding current Specs

---

## 1. Purpose

本文件定义 Askora 当前有效的：

- user-facing Information Architecture；
- Navigation hierarchy；
- route / deep-link behavior；
- shell / screen responsibility；
- page-level loading / empty / error / recovery；
- responsive screen behavior。

本文件只保存**当前有效规则**，不包含已被 ADR-0018 supersede 的旧 Learning four-facet 常驻管理模型。

本文件不拥有 Product Capability、domain ownership、API schema、persistence、Teaching Policy 或 component visual tokens。

---

## 2. Product Definition Traceability

主要映射：

| Area | Product Definition |
|---|---|
| Workspace / Library | `CAP-01`、`CAP-07`、`PD-REQ-0101..0104`、`PD-RULE-006/009/011` |
| Goal / Next Activity | `CAP-02`、`CAP-03`、`CAP-07`、`PD-REQ-0201..0203`、`PD-REQ-0301..0303` |
| Learning Canvas | `CAP-04`、`CAP-05`、`PD-REQ-0401..0403`、`PD-REQ-0501..0503` |
| Review / Validation return | `CAP-06`、`CAP-07`、`PD-REQ-0601..0603`、`PD-REQ-0701..0703` |
| Local data / settings | `CAP-08`、`PD-REQ-0801..0804`、`PD-RULE-008/010/011` |
| Accessibility / usability | `PD-NFR-005` |

UI Acceptance 不自动等同 Product Acceptance 或 Learning Evidence。

---

## 3. Required Screen State Vocabulary

所有依赖 canonical data 的 screen / region 必须区分适用状态：

```text
LOADING
EMPTY
READY
PARTIAL
STALE
ERROR
UNAUTHORIZED
```

附加规则：

- `PARTIAL` / `STALE` 不得显示成完整 READY；
- `MISSING` 可用于特定 optional projection，例如 Context Drawer；
- 局部数据失败优先局部降级，不应无条件让整个学习画布白屏；
- Empty 必须说明“缺什么”和“下一步能做什么”；
- Error 必须基于 stable error / retryability / recovery contract，而不是匹配自由文本；
- 不得用 fake data 填补 Goal、Activity、Evidence、Material 或 Workspace 空态。

---

## 4. Canonical User-facing IA

### UI-NAV-001 — Stable Product Domains

L0 Product Domain 只允许：

```text
今天
学习
资料库
```

### UI-NAV-002 — Utilities

以下属于 App Utility，不与 Product Domain 等权：

```text
设置
恢复中心
Search / Command（仅正式 capability 存在时）
```

Askora v1 无 Login / Register / Account shell。

### UI-NAV-003 — Learning Is Not a Management Center

Learning 主入口不再提供 Goal / Plan / Progress / History 的常驻管理 navigation。

这些 domain truth 继续存在；仅在明确 user job 下通过 contextual task flow / Disclosure / compatibility deep link 进入。

### UI-NAV-004 — Chat Is Not Navigation

Chat / Tutor 不得成为 L0 Product Domain。Conversation 是当前 LearningActivity 的 interaction mode。

---

## 5. Workspace Shell

### UI-SHELL-001 — Shared Workspace Context

Workspace variant 中：

```text
Left = Where
Center = Learn
Right = Reference / Notes
```

三部分必须解析同一 canonical current Workspace。

### UI-SHELL-002 — Left / Where

左侧只承担：

- Product Navigation；
- 当前 Workspace 可见性；
- Workspace selection / switch entry；
- Utility group。

不得放置常驻 Goal/Plan/Progress/Evidence 管理结构。

### UI-SHELL-003 — Center / Learn

中央区域是唯一 Primary Learning Canvas。进入真实学习后不得同时呈现多个等权 Dashboard 或第二套 Tutor surface。

### UI-SHELL-004 — Right / Reference & Notes

右栏可隐藏；v1 只允许：

- Learning Notes；
- Current Material / citation source context。

隐藏后必须仍能完成主任务；重新打开时恢复当前可恢复上下文。

### UI-SHELL-005 — Learning Context Drawer

Drawer 固定在 Composer/输入区域上方，默认收起。

收起：当前阶段 + 接下来的一行方向信息。  
展开：仅 stage / stage goal / next 1..3。

不得加入 Goal editor、完整 Plan、Progress Dashboard、Evidence 管理、mastery / ReviewSchedule / TeachingAction 控制。

---

## 6. Route Contract

### UI-ROUTE-001 — Stable Destinations

稳定产品目的地：

```text
/today
/learning
/library
/settings
/settings/recovery
/welcome            # supporting route, not L0
```

Workspace-scoped route 可以提供：

```text
/workspaces/:workspaceId
/workspaces/:workspaceId/today
/workspaces/:workspaceId/learn
/workspaces/:workspaceId/library
```

具体 router implementation（hash/history/native bridge）不是本合同 Authority。

### UI-ROUTE-002 — Learning Activity Deep Links

现有 activity/session deep link 可以保留兼容：

```text
/learn/:activityId
/quick/:sessionId
```

但必须进入同一 canonical LearningActivity / dialog facade，不得创建第二 transcript / Attempt / TeachingAction truth。

### UI-ROUTE-003 — Contextual Learning Management Routes

以下旧/兼容路径可以在迁移期保留：

```text
/learning/goals/**
/learning/plan
/learning/progress
/learning/history
/goals/**
/path
/evidence
/history
/profile
```

它们不得再构成 Learning 常驻管理 IA。

允许用途：

- explicit goal create / correction / audit；
- plan explanation；
- evidence/progress explanation；
- history recovery / audit；
- bounded compatibility deep link。

### UI-ROUTE-004 — No-side-effect Navigation

Redirect / route change / facet-like presentation change不得自动：

- 创建 Goal / Activity / Session；
- 修改 focused/persisted business state；
- 写 Evidence；
- 触发 replan；
- 清空未提交工作。

### UI-ROUTE-005 — Deep-link Preservation

历史 deep link 在 retirement condition 满足前必须可解释地迁移。删除兼容 route 前需有测试证明：

- no business side effect；
- back / reload 行为正确；
- active/resumable learning 不丢失；
- focus 落到新页面语义起点。

---

## 7. Today Contract

### UI-TODAY-001 — Purpose

Today 首先回答：

1. 现在最值得做的 LearningActivity 是什么；
2. 为什么现在安排它（存在可靠 reason 时）；
3. 用户如何开始/继续。

### UI-TODAY-002 — Single Primary Task

canonical current/next activity 可执行时，首屏只能有一个最高层级 Primary Learning Task 与对应 Primary Action。

Quick Start、History、完整 Plan、Evidence、ReviewDue 不得与其形成等权主区块。

### UI-TODAY-003 — Supporting Context

可显示：

- Goal / stage 简要上下文；
- reason summary；
- validation obligation；
- 1–3 个后续活动或 Review candidate（存在可靠数据时）。

不得把 ReviewDue candidate 伪装成已进入 LearningPlan 的复习任务。

### UI-TODAY-004 — No Reliable Next Activity

无可靠 canonical activity 时必须诚实显示缺失状态，可提供被 Product Definition / current owner contracts 明确允许的下一步；不得生成假计划或假推荐。

---

## 8. Learning Contract

### UI-LEARN-001 — Learning Landing

`/learning` 是进入当前学习上下文的稳定入口，不是 Goal/Plan/Progress/History dashboard。

在没有可直接恢复 Activity 时，可以提供明确的 continuation / Today 路径；不得前端自行创建 Session/Goal/Plan。

### UI-LEARN-002 — Same Activity Across Presentation Changes

Learning Workspace、兼容 Tutor、Focus/窄屏 presentation 只允许改变呈现，不得重新生成 canonical Activity / Attempt / TeachingAction / transcript。

### UI-LEARN-003 — Required Learning State

中央学习画布必须能够呈现：

- current task / teaching content；
- learner input / Attempt；
- feedback；
- streaming / completed / failed / recoverable state；
- 必要 citation / assistance / validation obligation。

学习消息与具体行为由 `learning-interaction-contracts.md` 管理。

---

## 9. Library Contract

### UI-LIB-001 — Purpose

Library 让用户管理当前产品支持的 Material、理解来源状态，并进入 material-grounded learning。

### UI-LIB-002 — Default Hierarchy

默认优先：

```text
Import
Search / Filter
Material list
Selected material context
```

重复 Material 默认 row/list；批量/低频操作只在 selection/context 下出现。

### UI-LIB-003 — No OCR Exposure in v1 Normal UI

正常 v1 UI 不暴露：

- OCR action；
- OCR engine/status；
- OCR candidate / review / publish；
- OCR confidence/bbox/hash 等实现细节。

扫描 PDF 无可靠文本时显示 `unsupported / partial extraction` 和可行动建议。

### UI-LIB-004 — Deferred Candidates

大纲、Evidence 管理中心、知识图谱管理 UI、Progress Dashboard、AI Summary、Flashcards、错题本不得建立 placeholder/disabled tab。

若 Product Definition 未来纳入，先更新上游 Product/Experience，再进入 UI Spec。

---

## 10. Settings / Recovery Contract

### UI-SET-001 — Utility Hierarchy

Settings 使用 category navigation / secondary destination，而不是 giant control grid。

### UI-SET-002 — Current Product Boundary

不得恢复已退役的 Account/Login/Password/AuthSession UI。

Local data、BYOK、Recovery 的用户行为必须服从 current Product Definition 与 security/data-control contracts。

### UI-SET-003 — Recovery Presentation

Recovery 不新增 Product Domain。存在 action-required issue 时可显示紧凑全局状态/入口；恢复 action 必须使用 owner 提供的合法 RecoveryAction，不得由 frontend 发明 command。

---

## 11. First-use / Welcome

### UI-WELCOME-001

`/welcome` 是 supporting route，不是 L0。

first-use 只呈现用户必须完成/理解的事实步骤，例如模型能力、材料、目标、首次 Activity；内部 diagnostic/planner/system stage 不得成为用户必须学习的工程流程。

### UI-WELCOME-002

显式 deep link 应尽量保留；Welcome redirect / dismiss 不产生额外业务副作用，也不得依赖 localStorage 冒充 readiness truth。

---

## 12. Responsive / Input Screen Rules

至少验证：

```text
1440×900
1024×768
768×1024
360×800
200% zoom
```

### UI-RESP-001

窄屏允许：Sidebar → drawer/compact rail；Right Rail → accessible sheet/section；Drawer → compact disclosure/sheet。

语义职责不得改变。

### UI-RESP-002

页面不得出现阻断任务的横向滚动。公式/代码等局部内容 MAY 自身滚动，但页面整体必须保持可用。

### UI-RESP-003

避免页面 + conversation + drawer 三层关键嵌套滚动。

### UI-RESP-004

关键 Navigation、Drawer、Right Rail、Workspace switch、Material tabs 必须有 keyboard/touch 等价路径；关闭 transient surface 后恢复合理 focus。

---

## 13. Forbidden Implementations

禁止：

- Domain object count → navigation count；
- 恢复 Goal/Plan/Progress/History 常驻管理中心；
- `/` 或 `/learning` 直接退化为 chat-first picker；
- route change 产生隐藏 business write；
- 用 frontend state 冒充 Workspace/Plan/Evidence/UserNote truth；
- 新增第二 Tutor / transcript；
- 为 deferred capability 建空页面/disabled tab；
- 用 OCR pipeline 复杂度占据 v1 Library；
- 用 Account/Auth UI 反向改变 Local Single-User 产品定义；
- 因窄屏隐藏完成任务所需唯一 citation/error/assistance/validation 信息。

---

## 14. Acceptance Criteria

- `UI-SN-AC-001`：L0 只有 Today / Learning / Library，Utility 明确分组；
- `UI-SN-AC-002`：Learning 无常驻 Goal/Plan/Progress/History 管理导航；
- `UI-SN-AC-003`：Workspace shell 三栏解析同一 current Workspace；
- `UI-SN-AC-004`：Today canonical activity 存在时只有一个 Primary Learning Task；
- `UI-SN-AC-005`：compatibility routes/deep links 无业务副作用且不会创建第二 truth；
- `UI-SN-AC-006`：Library normal v1 UI 无 OCR 暴露且 deferred candidates 无 placeholder；
- `UI-SN-AC-007`：Settings/Recovery 保持 Utility 语义且无 Account/Auth residue；
- `UI-SN-AC-008`：LOADING/EMPTY/PARTIAL/STALE/ERROR 等不会伪装 READY；
- `UI-SN-AC-009`：1440/1024/768/360 与 200% zoom 下主要用户任务可完成；
- `UI-SN-AC-010`：keyboard/touch/focus/deep-link/back/reload 的关键路径可验证；
- `UI-SN-AC-011`：无静默丢失 draft/stream/note/session/material context；
- `UI-SN-AC-012`：UI Acceptance 不被描述为 Product Acceptance 或 Learning Evidence。
