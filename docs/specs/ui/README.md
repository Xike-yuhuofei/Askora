# Askora UI Specification Set

> 状态：`FROZEN — ADR-0014 Interaction Architecture Baseline`  
> 权威性：Canonical UI Implementation Contract  
> Governing Design：`docs/design/Interactive-Element-System-Canonical-Design-Delta.md`  
> Governing ADR：`docs/adr/ADR-0014-user-job-driven-interaction-architecture.md`

## 1. Purpose

本目录定义 Askora 的产品呈现、Information Architecture、Interactive Element semantics、screen behavior、UI read models、visual system 与 migration/quality gates。

目标不是给现有 UI 换皮，而是让 UI 与 Askora 的长期学习闭环一致：

```text
Today next action
→ LearningActivity
→ Tutor / Task / Assessment
→ Evidence / Review / Plan update
→ Next action
```

UI 不得改变 SYS01～SYS08 状态所有权、TeachingAction、AssessmentResult、MasteryEstimate、LearningPlan 或 ReviewSchedule 语义。

## 2. ADR-0014 Frozen Product Decisions

1. UI 推导顺序固定为：

```text
User Job
→ Domain Meaning
→ Information Architecture
→ Interaction Semantics
→ Interaction Pattern
→ Visual Component
```

2. L0 Product Domain 固定为：

```text
今天 / 学习 / 资料库
```

3. Learning L1 facets 固定为：

```text
目标 / 路径 / 进展 / 历史
```

4. Settings / Recovery / Search 属于 App Utility，不与 Product Domain 等权。
5. Chat/Tutor 是 LearningActivity interaction mode，不是 Product Domain。
6. Today 在 canonical activity 可用时只允许一个 Primary Learning Task；Quick Start 降为 fallback/secondary。
7. Interactive Element 顶层 semantic primitives 固定为 7 类：Navigation、Action、Control、Selection、Disclosure、InteractiveContent、StatusFeedback。
8. Card/Button/Toolbar/Menu/Modal 是 pattern/component，不是 semantic role。
9. Library 保持 Product Domain，但 batch/OCR/duplicate/advanced actions 使用 progressive disclosure。
10. Settings landing 使用 hierarchical category navigation，不再是 giant control grid。

## 3. Spec Index

- [Interactive Element System](interactive-element-system.md)：7 类 semantic primitives、L0～L5 hierarchy、pattern qualification、cross-platform mapping 与 anti-patterns。
- [Information Architecture](information-architecture.md)：3-domain navigation、Learning facets、routes、legacy redirects、shell 与 responsive IA。
- [Screen Contracts](screen-contracts.md)：Today/Learning/Goal/Plan/Progress/History/Workspace/Library/Settings 的 task/state/action contracts。
- [UI Data Contracts](data-contracts.md)：领域来源、UI Read Model、Query/API 与兼容边界。
- [Visual System](visual-system.md)：semantic-before-component、tokens、hierarchy、rows/cards、contextual actions 与 accessibility。
- [Quality and Migration](quality-and-migration.md)：ADR-0014 migration、EXEC dependency、tests、responsive/security/claim gates。

## 4. Authority

UI implementation 必须遵守：

```text
Canonical Domain/System/Interface Specs
→ Accepted ADR-0014
→ 本 UI Spec Set
→ Frozen Vertical Slice
→ Active EXEC
→ Code/Test
```

若 UI Spec 与更高权威的 domain/system/security contract 冲突，必须登记 `SPEC GAP`，不得用视觉或 frontend-only state 绕过 owner truth。

## 5. Upstream Traceability

| UI Area | Primary Upstream | UI 只允许决定 |
|---|---|---|
| Interactive Elements / IA | ADR-0014、System Architecture | semantic role、navigation、hierarchy、pattern |
| Today / Goal / Plan | SYS06、SYS07、Goal/Activity lifecycle | owner state 的组合、解释、入口 |
| Tutor / Focus | SYS04、SYS05、SYS08 | 同 activity execution 的呈现与 user request |
| Library | SYS01、SYS02、Library Management | document/knowledge/source 呈现与 contextual commands |
| Progress | SYS03、State Ownership | canonical evidence projection、uncertainty、source |
| Settings | P1-02/P1-03/P1-05/P1-07 contracts | category/navigation/presentation，不改变 security semantics |
| Rich Response | RENDER、Security | typed payload layout 与 safe fallback |
| Quality | TEST、DOD、Security | UI-specific gates、migration、claims |

## 6. Current Implementation Baseline

当前 main 已具有：

- Today、Goals、LearningPath、Evidence、History、Library、Settings；
- canonical activity lifecycle 与 TutorWorkspace；
- P1-01 Goal management；
- P1-02 model configuration；
- P1-03 data control/recovery；
- P1-04 library organization/dedup/OCR；
- P1-05 account lifecycle；
- P1-07 recovery center；
- RichMessage / citations；
- P1-06 onboarding foundation，Product Closure 仍由 `EXEC-1062` 管理。

这些代码是 migration starting point，不决定新的 IA。

## 7. Implementation Gate

ADR-0014 implementation 必须等待 `EXEC-1062` DONE，因为其 Allowed Files 与本次 refactor 在 `App.jsx`、Settings、route tests、UI specs 上重叠。

冻结队列：

```text
EXEC-1062 DONE
→ UI-03 Interactive Element System Refactor
→ dedicated EXEC
→ Release Evidence
```

`EXEC-042` 是独立 backend/policy closure，可在不扩大 scope 时并行。

## 8. Explicit Non-goals

本次 Interaction Architecture 不授权：

- 改变 Teaching Strategy / TeachingAction；
- frontend mastery threshold；
- Plan manual reorder/replan；
- LearnerState direct edit；
- persistent notes；
- 新的 global search backend；
- 新生产依赖或 telemetry；
- 重写 P1-02/03/05/07 security/data flows；
- 把 UI 改善称为学习效果改善。

## 9. Legacy UI-03 Candidate

2026-08-08 Spec 中曾描述“UI-03 Focus and Adaptive Presentation Polish”候选，但未形成独立 frozen Vertical Slice/EXEC。

ADR-0014 后该未执行候选被本次新的 UI-03 Interaction Architecture Slice supersede；未来 Focus 专项如仍必要，必须重新冻结独立 Slice，不得从旧候选文字直接实施。
