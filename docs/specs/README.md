# Askora Implementation Specifications

> 状态：Canonical Implementation Contract Index  
> 当前版本：v0.3 Adaptive Teaching Loop Spec Delta

## 1. Purpose

`docs/specs/**` 将已冻结 Canonical Design 与 Accepted ADR 转换为可直接约束实现、测试、迁移、replay 与 release 的合同。

v0.3 authoritative formation chain：

```text
Research Synthesis
→ Canonical Design
→ Accepted ADR-0001 / ADR-0002
→ Updated v0.3 Specs
→ Vertical Slice
→ EXEC
→ Implementation
```

一旦本次 Spec Delta 通过 gate，实现必须服从 updated Spec；发现 Spec 与 Accepted ADR/Canonical Design 冲突时，MUST 先做 Spec gap/upstream conflict closure，MUST NOT 让代码或旧 Spec 反向修改 ADR 语义。

## 2. Spec Index

### Domain

- `domain/domain-model.md` — canonical objects、ontology、TeachingContext、PolicyBundle、Outcome/Experiment、migration
- `domain/decision-contract.md` — DecisionTrace v0.3、probability、replay
- `domain/event-contract.md` — LearningEvent、assistance/outcome/experiment event semantics
- `domain/lifecycle-state-machines.md` — lifecycle contracts（按需引用）

### Architecture

- `architecture/state-ownership.md` — SYS01～SYS08 single-writer ownership
- `architecture/system-architecture.md`
- `architecture/dependency-rules.md`

### Systems

- `systems/01-content-knowledge.md`
- `systems/02-retrieval.md`
- `systems/03-learner-model.md`
- `systems/04-assessment.md`
- `systems/05-teaching-policy.md`
- `systems/06-learning-planner.md`
- `systems/07-review-scheduling.md`
- `systems/08-ai-orchestration.md`

### Quality

- `quality/testing-standard.md` — L0～L6 + OPVE/G0/G1/G2
- `quality/observability-standard.md` — decision/outcome observability + learning outcome hierarchy
- `quality/definition-of-done.md` — Engineering/Policy/Learning Evidence release gates
- other quality/security/versioning specs remain applicable unless explicitly superseded

### Historical Vertical Slice

- `vertical-slices/v0.2-learning-loop.md` — v0.2 historical implementation slice. Where it conflicts with v0.3 ontology/support/probability contracts, v0.3 canonical specs supersede it; it MUST NOT be used to reintroduce old canonical truth.

## 3. v0.3 Canonical Decisions → ADR → Spec Traceability

| Canonical Decision | ADR | Canonical Spec Requirements |
|---|---|---|
| `V03-CD-002` six Strategy Families | ADR-0001 | `DOMAIN-083/086`, `SYS05-201` |
| `V03-CD-003` four-layer ontology | ADR-0001 | `DOMAIN-083..085`, `SYS05-202/203` |
| `V03-CD-005` TeachingContext | ADR-0002 | `DOMAIN-088`, `SYS05-210..212` |
| `V03-CD-006` ErrorType | — | `DOMAIN-072..074`, `SYS04-210..214` |
| `V03-CD-007` hard/soft/experiment | ADR-0002 | `SYS05-240..242`, `DECISION-240` |
| `V03-CD-008` support/exposure | ADR-0001 | `DOMAIN-061/062`, `SYS05-220/221`, `SYS04-200/201` |
| `V03-CD-009` validation obligation | — | `DOMAIN-091`, `SYS05-222`, `SYS03-230/231`, `SYS04-220..222` |
| `V03-CD-010` deterministic policy | ADR-0002 | `SYS05-230/231`, `SYS05-290/291`, `DECISION-210` |
| `V03-CD-011` anti-oscillation | ADR-0002 | `SYS05-280..285`, `TEST-240..242` |
| `V03-CD-012` PolicyBundle | ADR-0002 | `DOMAIN-089`, `SYS05-300..303` |
| `V03-CD-013` DecisionTrace probability/replay | ADR-0002 | `DECISION-200..222`, `SYS05-310..312` |
| `V03-CD-014` Outcome data model | — | `DOMAIN-111..113`, `OBS-200..221` |
| `V03-CD-015` OPVE / outcome hierarchy | — | `TEST-200..281`, `OBS-210..213` |
| `V03-CD-017` release gate | — | `DOD-200..260` |

## 4. SD-01～SD-11 Resolution Matrix

| SD | Status | Primary Specs |
|---|---|---|
| SD-01 Strategy Ontology | RESOLVED | domain-model, SYS05 |
| SD-02 TeachingContext | RESOLVED | domain-model, SYS05, DecisionTrace |
| SD-03 Assessment | RESOLVED | domain-model, SYS04 |
| SD-04 Error Diagnosis | RESOLVED | domain-model, SYS04, SYS03/SYS05 boundary |
| SD-05 Support/Hint/Exposure/Assistance | RESOLVED | domain-model, SYS02/03/04/05/08, events |
| SD-06 Anti-Oscillation | RESOLVED | SYS05, testing |
| SD-07 PolicyBundle / Policy Stack | RESOLVED | domain-model, SYS05 |
| SD-08 DecisionTrace v0.3 | RESOLVED | decision-contract, SYS05 |
| SD-09 Outcome / Experiment | RESOLVED | domain-model, event, ownership, observability |
| SD-10 Testing / OPVE | RESOLVED | testing-standard |
| SD-11 Observability / DoD / Release Gate | RESOLVED | observability-standard, definition-of-done |

## 5. Breaking Change Register — Spec Resolution

| BC | Resolution |
|---|---|
| BC-001 Strategy enum | six StrategyFamily is only v0.3 canonical top-level enum; old nine values read-only/audit |
| BC-002 TeachingAction semantics | immutable four-layer action contract + exact context/bundle pinning |
| BC-003 Support / exposure | canonical orthogonal scaffold/hint/exposure/assistance model |
| BC-004 Policy configuration | immutable/versioned PolicyBundle; no executable/free-form rules |
| BC-005 DecisionTrace probability / replay | deterministic `action_propensity=null`; assignment probability separated; explicit replayability |
| BC-006 Legacy Socratic selector | bounded move/provider/adapter only; SYS05 owns final TeachingAction |

All six are **RESOLVED IN SPEC**. Implementation migration remains a later phase and MUST follow these contracts.

## 6. Migration Candidate Register — Contract Resolution

| Candidate | Canonical target | Compatibility read | Classification / ambiguity | Replayability | Retirement condition |
|---|---|---|---|---|---|
| historical strategy records | six StrategyFamily | legacy audit allowed | ambiguous mapping must be explicit | FULL/PARTIAL by refs | supported history migrated/archived |
| historical TeachingAction | v0.3 immutable action | read adapter | non-lossless semantics marked | usually PARTIAL when fields absent | no active v0.2 workflow |
| old `scaffold_level` | `scaffold_control` | read adapter | lossy/unknown marked | PARTIAL if inference required | no active writer + migrated history |
| old `hint_level` | `hint_specificity` | read adapter | lossy/unknown marked | PARTIAL if inference required | no active writer + migrated history |
| old answer exposure scale | `answer_exposure` | read adapter | lossy mapping marked | PARTIAL if inference required | no active writer + migrated history |
| legacy Socratic selector/state machine | bounded InteractionMove provider/legacy adapter | bounded compatibility | never final owner | replay only behind fixed SYS05 contract | canonical path covers supported flows |
| old policy config | immutable PolicyBundle | audit/import only | executable config never executed | exact bundle required for FULL | migrated/retired configs |
| old DecisionTrace propensity | separated assignment/action probability | raw audit allowed | ambiguous → null/unknown + reason | PARTIAL | historical migrator complete |
| historical replay | exact historical refs | best effort | missing versions never guessed | FULL/PARTIAL/NON_REPLAYABLE | explicit status retained |

All nine migration candidates have canonical target、compatibility read、ambiguity、replayability 与 retirement semantics。Permanent dual truth is forbidden。

## 7. Spec-ID Governance

Existing requirement IDs MUST NOT be reused to change meaning. Superseded v0.2 IDs remain visible in each affected Spec's superseded/legacy register; v0.3 additions use new unused ranges (principally `*-2xx/3xx`).

## 8. v0.3 Canonical Invariants

```text
Knowledge truth / relations     → SYS01
EvidenceBundle                  → SYS02
LearnerState / MasteryEstimate  → SYS03
AssessmentResult                → SYS04
TeachingAction                  → SYS05
LearningPlan / Activity         → SYS06
ReviewSchedule / next_due       → SYS07
Model / Tool execution          → SYS08
```

And:

```text
TeachingStage != LearnerState
DecisionTrace != OutcomeObservation
Experiment assignment probability != action selection propensity
SYS08/SYS02 may tighten but may not expand TeachingAction envelope
LLM/Agent never owns final TeachingAction or canonical learner/assessment/plan/review truth
```

## 9. Versioned Parameters

mastery threshold、failure ceiling、minimum dwell、switch margin、hint sequence、scaffold fade amount、diagnostic confidence cutoff、transfer novelty threshold、delay windows、policy weights、practical harm margin MUST remain versioned/traceable configurable parameters. No Spec may claim arbitrary fixed values are universal learning-science constants.

## 10. v0.3 Out of Scope

Contextual Bandit、Offline RL、Online RL、Deep KT canonical truth、complex IRT-CAT、open-world misconception discovery、school-level population A/B、multi-agent teaching control、automatic learned reward、synthetic learner as learning evidence、free-form LLM TeachingAction ownership、generic Productive Failure strategy、always-on Socratic tutor、generic executable policy DSL。

B2 LLM selector MAY only be experiment baseline behind the same hard shield/action vocabulary.

## 11. Spec Delta Gate

v0.3 Spec Delta PASS requires：

```text
ADR-0001 fully reflected
ADR-0002 fully reflected
SD-01..SD-11 resolved
No duplicate truth source
Six breaking changes have migration semantics
Nine migration candidates resolved
All new public objects have owner/semantics
All policy layers testable
Decision probability semantics unambiguous
Legacy Socratic ownership bounded
No fixed pseudo-scientific parameters
No blocking SPEC GAP
```

When all conditions are met, next phase is **v0.3 Vertical Slice**. This index MUST NOT itself create EXEC or implementation work.