# EXEC-051 — Local Identity Acceptance & Release Closure

> Status：**DONE**（2026-08-10）  
> Governing：ADR-0015、`LID-*`、Authentication Removal Vertical Slice  
> Dependency：EXEC-050 DONE  
> Unlocks：UI-03 EXEC-043～046

## Objective

完成 Authentication Removal 的跨层验收、死代码/文档残留清理、发布证据与队列收口，证明 Askora 已真正成为 local single-user / no-auth product，而不是“隐藏 Login 的旧账号系统”。

## Dependencies

- EXEC-047～050 DONE；
- frontend/backend/schema 均已切换并完成 targeted tests；
- 当前工作树只包含本 release closure 所需改动。

## Required Specs

- ADR-0015
- `LID-AC-001..013`
- Authentication Removal Vertical Slice acceptance summary
- testing / observability / definition-of-done specs
- UI-03 dependency contracts

## Allowed Files

```text
apps/backend/**
apps/frontend/**
docs/CODE_WIKI.md
docs/document-inventory.md
docs/product-gap-register-p1-p2.md
docs/specs/**
docs/exec-plans/**
docs/releases/**
README.md
```

本 EXEC 只允许删除 dead auth residue、补验收测试/文档/证据；发现需要新的产品或 schema 设计时必须 `BLOCKED_BY_SPEC_GAP`。

## Forbidden Changes

- 不新增功能；
- 不实施 UI-03 页面重构；
- 不修改教学算法；
- 不通过删除失败测试伪造 PASS；
- 不保留 auto-login/demo-token shortcut；
- 不把“本地”表述成可安全 LAN/公网访问；
- 不改变 Learning Evidence 状态。

## Implementation Tasks

1. repo-wide inventory auth/account/login/password/JWT/session/recovery-kit/delete-account production references；
2. 删除确定 dead 的 auth files/imports/tests/fixtures/dependencies；
3. 对语义上仍有价值的 `recovery`（P1-07）与 `data erasure` 做人工分类，禁止关键词误删；
4. 执行 `LID-AC-001..013` 全量 acceptance；
5. cold-start browser E2E：无 login → canonical product route；
6. Settings E2E：无 account semantics，data export/erasure/recovery center 可用；
7. network boundary test：loopback allowed、0.0.0.0/LAN rejected；
8. legacy DB migration E2E：单 learner history retained；ambiguous fixture fail closed；
9. DecisionTrace/replay/learning path regression；
10. full frontend/backend gates；
11. 更新 CODE_WIKI/document inventory/spec/exec indexes；
12. 写 release report，归档 EXEC-047～051；
13. 更新 UI-03 dependency：只有本 EXEC DONE 后 EXEC-043 才可开始。

## Acceptance Criteria

- `E051-AC-001`：`LID-AC-001..013` PASS；
- `E051-AC-002`：repo production path 不存在 Account/Login/JWT/AuthSession/RecoveryKit 语义；
- `E051-AC-003`：保留的 `recovery` 仅属于错误恢复/数据恢复语义，有明确 owner；
- `E051-AC-004`：frontend `npm test` + build PASS；
- `E051-AC-005`：backend full pytest + ruff + mypy PASS；
- `E051-AC-006`：migration + browser E2E + network gate PASS；
- `E051-AC-007`：P1-03/P1-07 regression PASS；
- `E051-AC-008`：DecisionTrace/TeachingAction/LearnerState 语义无变化；
- `E051-AC-009`：release docs 明确 Engineering / Policy-Ownership PASS，Learning Evidence=`NOT_APPLICABLE_TO_IDENTITY_REMOVAL`；
- `E051-AC-010`：EXEC-043 dependency 已改为 requires EXEC-1062 + EXEC-051 DONE。

## Required Tests

### Frontend

```text
npm test
npm run build
```

### Backend

```text
pytest
ruff check .
mypy app
```

并必须包含：local owner、no-auth API、WebSocket origin、network bind、migration、data-control、recovery center、DecisionTrace/replay、browser E2E。

## Completion Report Format

Release report 至少包含：

- Design/ADR/Spec/EXEC traceability；
- removed auth surfaces；
- retained local identity/data-governance surfaces；
- migration evidence；
- loopback security evidence；
- frontend/backend gate results；
- known non-blocking debt；
- final commit SHA；
- `EXEC-047～051 DONE`；
- UI-03 unlocked status。
