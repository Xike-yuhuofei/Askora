# Askora Architecture Decision Records

> `docs/adr/` 记录已经被接受、会改变或解释 Implementation Spec 的重大架构决策。

## 1. 何时必须建立 ADR

以下变化必须先有 ADR，再改 Spec 和代码：

- 八类技术系统职责/所有权变化；
- 公共领域对象语义变化；
- 新的核心状态事实源；
- 模块化单体 → 微服务等部署架构变化；
- 数据库/事件基础设施重大替换；
- baseline 算法被新的生产主算法替换；
- 新增高权限 Agent/tool 执行模型；
- 破坏性公共 Schema/API 演进策略；
- 对安全、隐私、重放或审计不变量的改变。

局部实现细节、私有重构、等价性能优化通常不需要 ADR。

## 2. 权威链

```text
Canonical Design
→ Accepted ADR
→ Updated Implementation Spec
→ EXEC Plan
→ Code/Test
```

ADR 不能长期与 Spec 冲突。ADR 接受后必须同步更新受影响 Spec；Codex 仍以最新 Spec 作为直接实现合同。

## 3. 文件模板

```markdown
# ADR-XXXX — Title

Status: proposed | accepted | superseded | rejected
Date: YYYY-MM-DD
Decision owners: ...
Affected specs: ...

## Context
## Decision
## Alternatives Considered
## Consequences
## Migration / Rollback
## Validation
## Supersedes / Superseded By
```

## 4. Codex 权限

Codex 可以指出需要 ADR 的 `SPEC GAP`，但不得自行创建“accepted” ADR 来授权自己的设计变化。重大架构决策必须先由顶层设计流程确认。
