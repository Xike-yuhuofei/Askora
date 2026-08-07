# Askora Codex Execution Contract

> 适用对象：Codex 及其他代码执行代理  
> 状态：强制执行入口  
> 原则：Codex 负责实现，不负责重新设计 Askora。

## 1. 开始任务前的读取顺序

执行任何非纯机械修改前，必须按以下顺序读取与任务相关的规范：

1. `AGENTS.md`
2. `docs/specs/README.md`
3. `docs/specs/architecture/` 下与任务相关的规范
4. `docs/specs/domain/` 下与任务相关的领域合同
5. `docs/specs/systems/` 下对应系统 Spec
6. `docs/specs/interfaces/`、`docs/specs/quality/` 下与任务相关的规范
7. 当前 `docs/exec-plans/active/` 中明确指定的执行计划
8. 仅在需要理解设计理由时读取 `docs/design/`

`docs/design/research/` 是证据与研究层，不得被当作实现接口合同。

## 2. 权威优先级

发生冲突时按以下优先级处理：

```text
1. docs/specs/
2. docs/adr/
3. docs/design/ 中的 Canonical Design
4. 当前代码、数据库迁移和测试
5. Codex 自主推断
```

现有代码与 Spec 冲突时，默认视为实现偏差，不得反向修改规范来迁就现有代码。

## 3. Codex 的职责

Codex 必须：

- 严格按照 Spec 和 EXEC Plan 实现；
- 只修改任务允许的文件范围；
- 为每项关键行为补充可追踪测试；
- 保留已有公共行为，除非 Spec 明确要求变更；
- 遇到旧代码越过系统边界时，通过 adapter/迁移逐步收敛；
- 在提交结果中列出修改文件、执行测试、未完成项和 SPEC GAP；
- 对公共 Schema、迁移、状态所有权和跨模块依赖保持最小变更。

## 4. Codex 没有的设计权限

除非 Spec/ADR/EXEC 明确授权，Codex 禁止自行改变：

- bounded context 与八类技术系统边界；
- 状态唯一写入者；
- 公共领域对象语义；
- API、Command、Event、Decision Schema；
- 数据库领域模型和迁移语义；
- 算法 baseline、模型升级或训练路线；
- 教学策略规则；
- 复习模型语义；
- 错误、重试、降级和幂等语义；
- 安全、隐私和 Prompt Injection 防线；
- 技术栈、基础设施和生产依赖；
- 跨模块调用方向。

## 5. Codex 可以自行决定的范围

在不改变公共行为、领域语义和依赖边界的前提下，可以自行决定：

- 局部变量、私有函数和测试 fixture 命名；
- 单模块内部私有函数拆分；
- 等价的小型重构；
- 不改变错误类型/错误码的错误文案；
- Spec 明确标记为 `MAY` 的实现选项。

## 6. SPEC GAP 协议

出现以下任一情况必须标记 `SPEC GAP`，不得猜测：

- 两份高权威规范冲突；
- 实现要求改变状态所有权；
- 公共 Schema 或关键错误语义缺失；
- 为完成任务必须新增生产依赖、服务或基础设施；
- 存在多个会造成不同业务结果的合理方案，而规范未选择；
- 必须违反任一 `MUST NOT` 才能完成任务。

处理方式：

1. 继续完成不受该缺口影响的部分；
2. 不做隐式架构选择；
3. 在结果中输出 `SPEC GAP`、受影响规则、候选方案和最小待决策问题；
4. 等待 Spec/ADR 更新后再实现缺口部分。

## 7. 八类系统的不可越权规则

```text
4.1 内容解析与知识建模      → 知识事实、规范概念与关系发布
4.2 检索与知识供给          → EvidenceBundle 最终选择
4.3 学习者建模              → LearnerState / MasteryEstimate
4.4 评估与错误诊断          → AssessmentResult / 单次错误诊断
4.5 教学策略选择            → TeachingAction / 提示与暴露上限
4.6 学习路径与任务调度      → LearningPlan / LearningActivity
4.7 记忆保持与复习调度      → ReviewSchedule / next_due_at
4.8 LLM/Agent 编排与可信控制 → 会话执行、模型/工具路由、事件与审计执行
```

任何模块不得直接写入其他系统拥有的业务状态。

特别禁止：

- Assessment 模块直接修改 mastery；
- LLM/Agent 直接修改 learner state、plan、teaching action 或 review schedule；
- Planner 计算新的 memory schedule；
- Teaching Policy 重排长期课程目标；
- Retrieval 在 TeachingAction 允许范围之外扩大答案暴露；
- 检索失败后由 LLM 自行补造用户资料中的事实。

## 8. Legacy Code

当前代码结构是迁移起点，不是最终领域边界。以下现有目录可能跨越未来多个系统：

- `apps/backend/app/engines/`
- `apps/backend/app/services/dialog/`
- `apps/backend/app/services/dkt/`
- `apps/backend/app/services/kt/`
- `apps/backend/app/services/documents/`
- `apps/backend/app/services/knowledge_graph/`
- `apps/backend/app/services/assessment/`

规则：

- 不得因历史目录存在而授予新的状态所有权；
- 新能力必须朝 `docs/specs/architecture/system-architecture.md` 的目标边界收敛；
- 允许临时 adapter/compatibility layer，但必须有删除条件；
- 禁止形成两套长期并存的事实源或两条默认教学主链路。

## 9. 默认工程验证

后端任务在适用时至少运行：

```bash
cd apps/backend
pytest
ruff check app tests
```

修改类型标注、公共接口或核心领域代码时应额外运行：

```bash
mypy app
```

前端任务在适用时至少运行：

```bash
cd apps/frontend
npm run build
```

如果某命令因当前仓库既有问题无法通过，必须区分：

- 本次变更新增失败；
- 与本次变更无关的既有失败。

不得通过删除测试、弱化断言或扩大 ignore 来伪造通过。

## 10. 完成定义

Codex 只有在以下条件全部满足时才能把任务标记为完成：

- 所有明确 Acceptance Criteria 已满足；
- 未违反状态所有权和依赖规则；
- 必要数据库迁移可前向执行并有明确回滚/兼容策略；
- 新增关键行为存在自动化测试；
- 错误、重试、幂等和观测行为符合 Spec；
- 无未声明的公共 API/Schema 变化；
- 所有 SPEC GAP 已显式报告；
- 没有占位实现、`TODO` 伪完成或仅 Mock 的“真实模型可用”结论。
