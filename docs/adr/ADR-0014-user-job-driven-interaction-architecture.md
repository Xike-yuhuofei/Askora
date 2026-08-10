# ADR-0014 — User-job-driven Information and Interaction Architecture

Status: accepted  
Date: 2026-08-10  
Decision owners: user-authorized Askora product governance  
Decision authority: explicit user approval on 2026-08-10 to adopt and execute the Interactive Elements redesign  
Affected specs: `docs/specs/ui/information-architecture.md`, `screen-contracts.md`, `visual-system.md`, `quality-and-migration.md`, UI vertical slice / EXEC  
Canonical design input: `docs/design/Interactive-Element-System-Canonical-Design-Delta.md`

## Context

Askora 已从 chat-first UI 迁移到 learning-loop-first UI，但当前一级导航仍采用：

```text
今天 / 学习目标 / 学习路径 / 资料库 / 学习证据 / 历史记录 / 设置
```

这七项并不属于同一 semantic level：Today 是 daily orchestration destination；Goal 是 domain object collection；Path 是 plan projection；Evidence 是 learner-state projection；History 是 past-state projection；Library 是 stable product domain；Settings 是 application utility。

现有 IA 因而存在结构性映射：

```text
Domain Object → Page → Global Navigation Item
```

这要求用户先理解产品内部模型，再找到当前学习任务，与 Askora “个人学习操作系统、对话只是手段”的 Canonical Product Design 不一致。

同时，Today 中 compatibility quick start 与 canonical activity 竞争主层级；Library 与 Settings 暴露过多 always-visible controls，增加 Dashboard / Control Panel 噪声。

## Decision

### 1. Information Architecture 以 User Job 为起点

UI 设计和实现必须遵守：

```text
User Job
→ Domain Meaning
→ Information Architecture
→ Interaction Semantics
→ Interaction Pattern
→ Visual Component
```

禁止将 domain object 自动提升为 page 或 L0 navigation item。

### 2. L0 Product Domains 收敛为 3 个

冻结：

```text
今天
学习
资料库
```

`设置` 保留为 App-level destination/command，不属于 Product Domain Navigation。

### 3. Learning 聚合长期学习 Facets

冻结：

```text
学习
├─ 目标
├─ 路径
├─ 进展
└─ 历史
```

- Goal 保持 LearningGoal canonical semantics；
- Path 保持 LearningPlan projection；
- `进展` 是 Evidence 面向用户的 IA vocabulary，不改变 SYS03/evidence ownership；
- History 保持只读历史与恢复语义。

### 4. Chat/Tutor 不成为 L0

Conversation 是 `LearningActivity Workspace` 的 interaction mode。

旧 chat-first UI 只能作为兼容实现迁移对象，不建立第二条产品主链。

### 5. Today 使用单一 Primary Task

当 canonical next activity 可启动时，Today 的最高视觉和交互层级只能服务该 activity。

Compatibility Quick Start 仅允许：

- 无 canonical Goal/Plan 时作为 fallback；或
- overflow / secondary utility。

### 6. Semantic Interaction Primitives 固定为 7 类

```text
Navigation
Action
Control
Selection
Disclosure
Interactive Content
Status / Feedback
```

`Entry` 不是 primitive。`Contextual Action` 是 Action + contextual rule。Card/Button/Toolbar/Menu/Modal 等属于 interaction/presentation pattern。

### 7. Interaction Hierarchy 固定为 L0～L5

```text
L0 Product Domain Navigation
L1 Domain Facet / Local Navigation
L2 Primary Task / Primary Action
L3 Secondary Action
L4 Object-level Contextual Action
L5 Advanced / Overflow
```

层级越低，默认越不应常驻。

### 8. Library 使用 Progressive Disclosure

Library 继续是 L0 Product Domain，但批量分类、归档、重复处理、OCR、元数据高级编辑、重新安全检查和 destructive actions 应按 selection/context 暴露，不得全部常驻。

### 9. Settings 使用 Hierarchical Settings

Settings landing page 只提供类别导航和 action-required state。长期目标结构：

```text
通用
AI 与模型
学习偏好
外观
数据与隐私
账号与恢复
高级
```

导出、删除、密码、会话、恢复套件、账号删除等进入二级 task destination。

### 10. Route Migration

新 canonical route family：

```text
/today
/learning
/learning/goals
/learning/goals/:goalId
/learning/goals/new
/learning/plan
/learning/progress
/learning/history
/library
/library/:documentId
/learn/:activityId
/settings/...
```

兼容 redirect：

```text
/goals    → /learning/goals
/path     → /learning/plan
/evidence → /learning/progress
/history  → /learning/history
```

Redirect 必须无业务副作用。

## Alternatives Considered

### A. 保留当前 7 项一级导航

未采用。优点是改动小且与现有页面一一对应；缺点是继续把 domain projections 当作 product domains，无法解决 IA 根因。

### B. 仅把 Settings 移出 Sidebar，保留其余 6 项

未采用。能降低少量噪声，但 Goal/Path/Evidence/History 仍然被错误提升为同级 L0。

### C. 使用 Dashboard 首页，通过更多 Card 解决发现性

未采用。它解决的是视觉聚合，不解决 semantic hierarchy，反而会强化 Dashboard Syndrome。

### D. L0 使用「今天 / 学习 / 资料库 / 历史」四项

未采用。History 是 LearningActivity 的过去投影，不是与 Learning 本身独立的稳定产品域。

## Consequences

### Positive

- 用户打开 App 后更快进入下一学习任务；
- 一级 IA 从 7 个异质入口降为 3 个稳定产品域；
- Goal/Plan/Evidence/History 的 canonical semantics 保持不变，只改变 presentation/IA；
- Chat 不再形成独立产品心智模型；
- 为 macOS/iOS 共用 semantic architecture，同时允许平台 pattern 分化；
- Library/Settings 的复杂能力通过 progressive disclosure 降噪。

### Cost / Risk

- 现有路由、Sidebar、页面入口和 E2E 需要迁移；
- deep links 必须保留兼容 redirect；
- Settings 需要拆分二级 route；
- Learning 聚合页需要新的 local navigation shell；
- UI Spec 与当前 implementation baseline 会发生有计划的 breaking presentation change。

## Ownership / Truth Impact

本 ADR **不改变** SYS01～SYS08 canonical ownership，不建立任何第二 truth。

它只改变：

- information architecture；
- route organization；
- interaction hierarchy；
- visual/presentation exposure。

Goal、Plan、Evidence、History、Activity、Recovery 等仍使用原 owner/query/command 合同。

## Security / Privacy / Replay / Idempotency

- 不改变 authentication、privacy、recovery、erasure 或 model credential 安全边界；
- route redirect 不得触发 command 或状态写入；
- progressive disclosure 不得隐藏安全错误、citation、validation obligation 或 destructive confirmation；
- UI 重构不得改变 LearningActivity / Attempt / TeachingAction / DecisionTrace identity；
- legacy route compatibility 不建立第二份 durable state。

## Migration / Rollback

迁移顺序：

1. 更新 `docs/specs/ui/**`；
2. 冻结新的 UI vertical slice / EXEC；
3. 添加 `/learning/*` routes 与无副作用 legacy redirects；
4. 新建 3-domain navigation；
5. 将 Goals/Path/Progress/History 聚合到 Learning domain；
6. 重构 Today hierarchy；
7. 重构 Settings / Library progressive disclosure；
8. 删除未被 route 引用的 legacy chat-first UI；
9. 完成 responsive/keyboard/browser E2E；
10. 在兼容周期结束后再评估旧 route redirect 的退休。

Rollback/forward-fix：若新 shell 存在阻断性问题，可暂时恢复旧 presentation route mapping，但不得恢复 chat-first product semantics 或建立双 truth；数据 schema 无需回滚。

## Validation

至少验证：

- L0 navigation 只有 Today / Learning / Library product domains；
- `/` 仍安全进入 Today / onboarding contract；
- legacy goal/path/evidence/history routes 无副作用 redirect；
- Today canonical activity 可用时只有一个 primary task；
- Quick Start 不与 canonical activity 同级；
- Learning 四个 facets keyboard/pointer/touch 可达；
- Settings 二级 destination 可返回且 destructive flow 不弱化；
- Library selection 后才暴露批量动作；
- 1440×900、1024×768、768×1024、360×800 和 200% zoom 可完成主任务；
- screen reader/keyboard focus order 与 semantic role 一致；
- frontend build、UI unit/integration、browser E2E 通过。

Engineering / Policy / Learning Evidence 结论继续分离。本 ADR 是 presentation/IA change，不产生新的 Learning Evidence 声明。

## Supersedes / Superseded By

本 ADR supersedes 当前 UI Spec 中将 Goals / Path / Evidence / History / Settings 作为同级 L0 Navigation Item 的设计选择；具体条款由同步更新后的 `docs/specs/ui/**` 取代。

Superseded by: none.
