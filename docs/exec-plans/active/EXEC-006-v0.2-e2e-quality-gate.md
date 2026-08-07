# EXEC-006 — v0.2 E2E / Recovery / Security Gate

> Priority：P0 Release Gate  
> Status：READY_AFTER_EXEC-005  
> Depends on：EXEC-001～005

## Objective

不新增横向功能，只验证首个 v0.2 垂直学习闭环在真实数据库、真实 Orchestrator、至少一次真实模型调用、故障恢复和安全攻击样本下成立；失败则回到对应 EXEC 修复。

## Required Specs

读取全部 `docs/specs/`，重点：

- `vertical-slices/v0.2-learning-loop.md`
- `quality/testing-standard.md`
- `quality/security-standard.md`
- `quality/observability-standard.md`
- `quality/definition-of-done.md`
- `interfaces/error-contract.md`
- `interfaces/persistence-contract.md`

## Allowed Files

优先仅：

```text
apps/backend/tests/e2e/**
apps/backend/tests/integration/**
apps/backend/tests/security/**
apps/backend/tests/recovery/**
apps/backend/tests/migrations/**
apps/backend/tests/evals/**
apps/backend/test_*.py            # 仓库既有同类测试按需
CI/config/documentation only if needed
```

若测试发现产品缺陷，可修改对应实现，但必须在 completion report 映射回 EXEC/SYS 规则，禁止趁机增加新功能。

## Forbidden Changes

- 不弱化安全/掌握/引用标准来让 E2E 通过；
- 不用 Mock 替代真实模型 AC；
- 不 skip flakey critical test 后宣布完成；
- 不扩大 v0.2 scope；
- 不引入 RL、多 Agent、微服务解决测试问题。

## Canonical E2E Scenario

使用固定测试资料：一份小型 PDF 或 Markdown，内容足以形成一个可确定性评分的 KnowledgeUnit。

执行：

```text
1. fresh SQLite database
2. import material
3. wait/recover content task
4. verify SourceSpan/citation
5. confirm measurable LearningGoal
6. generate/select LearningActivity
7. SYS05 TeachingAction
8. SYS02 EvidenceBundle
9. SYS08 real-model-assisted teaching response
10. learner submits deterministic assessment response
11. SYS04 AssessmentResult
12. SYS03 LearnerEvidence + MasteryEstimate
13. SYS07 ReviewSchedule
14. SYS06 future review activity integration
15. restart app/process boundary
16. reload all state
17. replay learner projection with fixed version
```

## Required Variants

### V1 — Independent Correct

答案不可见、无提示，正确提交；验证有效 evidence、mastery update、review schedule。

### V2 — Hint-Assisted Correct

使用概念/结构提示后正确；验证 evidence 权重与 V1 不同。

### V3 — Answer Exposed

完整答案已显示后正确；验证不能作为稳定 mastery 高权 evidence。

### V4 — Model Failure

主模型 timeout/unavailable；验证 bounded fallback/error，且不产生 learner failure evidence。

### V5 — Retrieval Missing

必要资料找不到；验证 missing evidence，不伪造引用/资料答案。

### V6 — Prompt Injection

资料包含恶意“忽略系统指令/调用工具/泄露答案”；验证无策略、权限、暴露突破。

### V7 — Restart During Pending Work

文档/事件/outbox/review task pending 时重启；验证恢复或明确 terminal failure。

### V8 — Duplicate Submit

重复相同 idempotency key；验证不产生第二 Attempt/Evidence。

## Migration Gate

必须从一个代表性旧数据库 fixture 执行到当前 schema，检查：

- 旧 session/message 可保留；
- legacy mastery 不被误当 canonical evidence；
- 新 event/outbox/schema 正确；
- migration 可重复检测；
- rollback/forward-fix 文档完整。

## Security Gate

至少固定回归：

- document prompt injection；
- grader-only answer leakage；
- unauthorized tool；
- path traversal upload；
- citation mismatch；
- secret/log leakage。

## Observability Gate

选择一次 E2E correlation_id，必须能够串起：

```text
API
→ WorkflowRun
→ TeachingAction DecisionTrace
→ EvidenceBundle RetrievalTrace
→ ModelInference
→ response
→ Attempt
→ AssessmentResult
→ LearnerEvidence
→ MasteryEstimate
→ ReviewSchedule
```

## Release Acceptance Criteria

以下全部为阻断性：

- `EXEC006-AC-001`：v0.2 `Definition of Slice Done` 12 项全部满足。
- `EXEC006-AC-002`：真实模型 E2E 至少一次成功，记录 provider/model/prompt version，不提交密钥。
- `EXEC006-AC-003`：独立/提示/答案暴露三种证据语义正确。
- `EXEC006-AC-004`：fixed replay 不调用在线模型且状态一致。
- `EXEC006-AC-005`：restart/outbox recovery 成功。
- `EXEC006-AC-006`：Prompt Injection / answer leakage / unauthorized tool tests 通过。
- `EXEC006-AC-007`：citation 可定位 SourceSpan，unsupported citation 被拒绝。
- `EXEC006-AC-008`：普通/streaming 走同 canonical teaching path。
- `EXEC006-AC-009`：architecture ownership tests 通过。
- `EXEC006-AC-010`：全量 pytest + ruff 通过；mypy 新改范围无新增错误，历史错误如有精确列出。
- `EXEC006-AC-011`：前端 `npm run build` 通过，且核心会话流程兼容。
- `EXEC006-AC-012`：没有未声明 SPEC GAP。

## Required Commands

```bash
cd apps/backend
pytest tests/e2e tests/integration tests/security tests/recovery tests/migrations
pytest
ruff check app tests
mypy app

cd ../frontend
npm run build
```

真实模型测试可以通过明确 marker/环境变量单独运行，但发布 Gate 必须实际运行一次并保存非敏感结果摘要。

## Completion Report

最终报告必须包含：

```text
Release Gate: PASS | FAIL

AC Matrix:
- AC → test → result

Real model:
- provider/model/prompt version/result（无密钥）

Replay:
- event range/projection version/result

Recovery:
- scenario/result

Security:
- case/result

Known legacy debt:
- path / rule / next EXEC

SPEC GAP:
- none / details
```

只有 `Release Gate: PASS` 才允许把六份 EXEC 移入 `completed/` 并声明 v0.2 首个垂直切片完成。
