# EXEC-044 — UI-03B Today Primary Hierarchy

> Status: **FROZEN / BLOCKED_BY_DEPENDENCY_GATE**  
> Priority: P0 Interaction Architecture  
> Governing: `docs/product/PRODUCT-POSITIONING.md`, ADR-0014, `UI-IES-*`, `UI-IA-050..051`, `UI-SCREEN-010..017`, UI-03 Vertical Slice  
> Depends on: `EXEC-043 DONE`

## Objective

把 `/today` 从“canonical activity + compatibility quick-start dashboard”收敛为当前 Workspace 内的 daily learning orchestrator：canonical current/next activity 是 sole Primary Task；Goal/reason/validation 是 supporting information；upcoming/review 是 secondary；Quick Start 只在缺少 canonical activity 时 fallback，或进入 secondary/overflow。

Today 不得因为“今日学习”便利性而突破 PRODUCT-POSITIONING：不得跨 Workspace 混合 Learner State / Evidence / Activity，不得把 Learning Project 变成开始学习的门禁；用户仍可以直接基于 Material 进入学习。

## Dependency Gate

- EXEC-043 已 DONE 并归档；
- `/today` 与 `/learning/**` routes 当前绿色；
- P1-06 onboarding completion/default-entry 行为保持绿色。

未满足返回 `BLOCKED_BY_DEPENDENCY`。

## Required Product Positioning

必须读取 `docs/product/PRODUCT-POSITIONING.md`，至少核对：

- Today/学习活动必须属于明确 Workspace scope；
- Learning Session 必须归属于 Workspace，但不必须绑定 Learning Project；
- Learning Project 不是直接从 Material 开始学习的强制门禁；
- Learner State 是由 Learning Evidence 推导的状态，frontend 不得自行推断 mastery/next_due；
- engagement、对话轮次、单纯使用时长不得成为主要学习目标。

## Required Specs

- `AGENTS.md`
- `docs/product/PRODUCT-POSITIONING.md`
- ADR-0014
- `UI-IES-*`
- `UI-IA-050..051`
- `UI-SCREEN-010..017`
- `UI-VIS-070..071`
- `UI-QUAL-*`
- UI-03 Vertical Slice
- SYS06 activity lifecycle / workspace data contracts

## Current Reality

当前 `Today.jsx` 已正确优先读取 canonical `active_goal/current_activity`，但在同一页面继续永久显示大型“快速学习”表单和 recent compatibility sessions，使兼容能力与 canonical task 竞争视觉层级。

Today 的重构还必须明确：所谓“当前/下一项”只能来自当前 Workspace 的 owner data；如果没有 Project，不能把“没有 Project”误当成“没有可学习内容”。

## Allowed Files

```text
apps/frontend/src/pages/Today.jsx
apps/frontend/src/pages/Today.css
apps/frontend/src/components/SourceStatus.*                 # only if presentation-only adjustment required
apps/frontend/src/test/**Today**
apps/frontend/src/test/**today**
docs/exec-plans/active/EXEC-044-ui-03b-today-primary-hierarchy.md
docs/exec-plans/completed/EXEC-044-ui-03b-today-primary-hierarchy.md
docs/exec-plans/README.md
docs/exec-plans/completed/README.md
```

## Forbidden Changes

- workspace/backend query semantic changes；
- planner/review/evidence calculation；
- Goal creation semantics；
- Quick Start compatibility API retirement；
- Learning/Library/Settings page refactor；
- fabricated recommendation copy；
- front-end mastery or next_due inference；
- 跨 Workspace 聚合 current/next activity、ReviewDue、Evidence 或 Learner State；
- 将 Learning Project 是否存在作为 Today 可否开始学习的判断条件；
- 用阅读量、会话数、使用时长替代真实学习进度。

## Implementation Tasks

1. 记录 baseline + current Today DOM/state tests。
2. 先写 RED tests：canonical activity → one primary task；no activity → honest fallback；Quick Start demotion；review semantics；Workspace scope；direct-Material fallback。
3. 重组 Today content hierarchy，不改变 owner data/query。
4. canonical activity 可执行时只保留一个 primary `开始/继续学习`。
5. 将 Goal title、reason、duration、validation obligation 作为 supporting content。
6. upcoming planned activities 和 ReviewDue 进入 secondary section，保持两者语义区分。
7. Quick Start 在 canonical activity 存在时变为 secondary/overflow；无 canonical activity 时可作为标记清晰的 fallback。
8. recent compatibility sessions 不得比 canonical activity 更显著。
9. 验证所有 displayed/recommended activity 均属于当前 Workspace；不存在跨 Workspace fallback。
10. 验证无 Learning Project 但存在可学习 Material 时，Today/Quick Start 仍可进入合法直接学习路径，不显示虚假的“必须先创建 Project”门禁。
11. 覆盖 READY/PARTIAL/EMPTY/ERROR、multiple plans、launch-state cases。
12. 验证 360/768/1024/1440、keyboard/focus；运行 gates；独立 commit/归档。

## Acceptance Criteria

- `EXEC044-AC-001`：`UI03-AC-006..007` PASS。
- `EXEC044-AC-002`：canonical activity 可执行时只有一个 Primary Learning Action。
- `EXEC044-AC-003`：Quick Start 不与 canonical activity 同层；无 activity 时仍可发现且明确 compatibility。
- `EXEC044-AC-004`：ReviewDue 与 planned review activity 不混淆。
- `EXEC044-AC-005`：reason copy 仅来自 owner reason mapping，无 LLM/frontend fabrication。
- `EXEC044-AC-006`：Today 数据/query/API 无语义变化。
- `EXEC044-AC-007`：responsive/keyboard/error/empty/partial states PASS。
- `EXEC044-AC-008`：Today 的 current/next/review/compatibility session 均不突破当前 Workspace scope。
- `EXEC044-AC-009`：Learning Project 非学习启动门禁；无 Project 的 Material 仍可沿现有合法路径直接开始学习。
- `EXEC044-AC-010`：Today 不新增以 engagement、对话轮次、阅读百分比或使用时长为核心的学习进度表达。

## Required Tests

```bash
cd apps/frontend
npm test -- --run
npm run build
npm audit --audit-level=high

cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

至少提供 Today hierarchy、Workspace isolation、direct-Material learning、review semantics、responsive/keyboard 与 owner-data regression evidence。

## Completion Report Format

报告：修改文件、before/after hierarchy、各 Today state 测试、Workspace/direct-Material evidence、UI03/EXEC AC、responsive/keyboard evidence、build/audit/docs 结果、commit、SPEC GAP。
