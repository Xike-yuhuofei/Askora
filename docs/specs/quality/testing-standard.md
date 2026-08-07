# Askora Testing Standard

> Spec ID：`TEST-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.1

## 1. 原则

### TEST-001

测试的目标不是验证“代码能跑”，而是验证 Spec 中的业务边界、状态所有权、失败语义和学习闭环。

### TEST-002

新增/修改关键行为必须有自动化测试，并在测试名/docstring/marker 或邻近注释中引用至少一个 Spec/AC ID。

## 2. 测试层级

Askora 采用：

```text
L0 Static / Architecture
L1 Unit
L2 Contract
L3 Integration
L4 End-to-End
L5 Replay / Migration / Recovery
L6 AI Quality / Security Evaluation
```

### TEST-010：L0

验证：lint、type、import/dependency rules、禁止跨 owner repository 写入等。

### TEST-011：L1

纯领域算法/规则使用 deterministic unit tests，不依赖数据库/网络/LLM。

### TEST-012：L2

验证 Command/Event/API/public schema、error code、version compatibility、adapter contract。

### TEST-013：L3

真实 SQLite repository/outbox/worker/orchestration adapter 集成，允许模型/外部依赖 mock。

### TEST-014：L4

验证首个真实教学垂直闭环。至少一个受控 E2E MUST 使用实际配置的真实模型；Mock-only 不算模型接通验收。

### TEST-015：L5

验证：应用重启恢复、event replay、migration、projection rebuild、idempotency、late event、invalidated evidence recompute。

### TEST-016：L6

固定 eval dataset 验证：citation、answer leakage、prompt injection、grader consistency、teaching policy、retrieval quality 等。

## 3. 必测架构不变量

### TEST-020

必须自动验证至少：

- Assessment 不直接写 mastery；
- Orchestrator/LLM 不直接写 mastery/plan/review；
- Planner 不改 ReviewSchedule；
- Retrieval 不扩大 answer exposure；
- replay 不调用在线 LLM；
- ordinary/streaming 使用同 canonical facade。

可以使用 Python AST/monkeypatch/contract fixtures；新增第三方 architecture dependency 需要 Spec/ADR。

## 4. AI 测试规则

### TEST-030：Mock 与真实模型分工

- Unit/大部分 integration：Mock/fixture；
- provider connectivity /真实 structured output / end-to-end：真实模型；
- eval：固定模型 snapshot/config 时尽量稳定记录。

### TEST-031

不得用真实模型替代 deterministic unit test，也不得用 Mock 宣称真实模型可用。

### TEST-032

AI 输出测试应验证结构/约束/grounding，而不是对完整自然语言字符串做脆弱精确匹配。

## 5. Determinism

### TEST-040

Event replay、BKT/learner projection、review update、fixed heuristic planning/policy 等在 fixed inputs/version 下必须 deterministic。

### TEST-041

模型生成的 nondeterminism 必须隔离在 ModelInference；canonical replay 不重新生成。

## 6. Database Tests

至少覆盖：

- SQLite foreign keys/constraints；
- unique aggregate version；
- transactional outbox；
- idempotency；
- concurrency conflict；
- migration representative fixture；
- projection rebuild。

## 7. Failure Tests

每个外部依赖必须至少测试：

```text
timeout
unavailable
invalid response
partial failure
retry exhausted
fallback success/failure
```

并验证这些故障不会被错误记录为 learner failure。

## 8. Security Tests

至少：

- malicious document prompt injection；
- unauthorized tool call；
- answer/rubric leakage；
- citation mismatch；
- cross-user access（服务模式）；
- path traversal/unsafe upload；
- secret leakage/logging。

## 9. Test Data

### TEST-050

测试 fixture 必须标记：synthetic / public / user-provided-local。CI 不得依赖私密用户资料。

### TEST-051

关键学习闭环至少维护一个最小 deterministic curriculum fixture：材料 → KnowledgeUnit → item → responses → evidence → mastery → review。

## 10. 命令基线

后端适用任务至少：

```bash
cd apps/backend
pytest
ruff check app tests
```

修改核心类型/接口时：

```bash
mypy app
```

前端适用任务：

```bash
cd apps/frontend
npm run build
```

具体 CI 可进一步拆分，但不得弱于这些质量意图。

## 11. Existing Failure

### TEST-060

若全量测试存在与本次任务无关的历史失败，Codex 必须：

1. 运行受影响 targeted tests；
2. 运行尽可能完整 suite；
3. 报告新增失败 vs 既有失败；
4. 不删除/skip/弱化测试伪造通过。

## 12. Acceptance Criteria

- `TEST-AC-001`：每个系统 Spec 至少有对应 contract/unit test suite。
- `TEST-AC-002`：首个垂直切片有真实 SQLite E2E。
- `TEST-AC-003`：至少一个 E2E 使用真实配置模型。
- `TEST-AC-004`：event replay 测试证明固定版本确定性。
- `TEST-AC-005`：architecture tests 捕获跨 owner 直接写入。
- `TEST-AC-006`：restart/outbox recovery 测试通过。
- `TEST-AC-007`：prompt injection 和 answer leakage 有固定回归样本。

## 13. Forbidden Implementations

禁止：

- 仅 happy path；
- 仅 Mock E2E；
- 为过 CI 删除测试/改弱断言；
- 用网络实时内容作为无固定版本的关键 fixture；
- AI 自然语言完整字符串脆弱比较；
- 将 provider timeout 测试期望写成 learner answer incorrect。
