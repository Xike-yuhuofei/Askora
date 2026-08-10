# Askora Codex Execution Contract

> 适用对象：Codex 及其他代码执行代理  
> 状态：强制执行入口  
> 原则：Codex 负责设计闭环与实现；在用户明确授权目标或明确委托架构自治时，
> 可代表该目标接受必要架构决定，但必须先完成 Product Positioning / ADR / Spec / EXEC 治理再修改产品代码。

## 1. 开始任务前的读取顺序

执行任何非纯机械修改前，必须按以下顺序读取与任务相关的规范：

1. `AGENTS.md`
2. `docs/product/PRODUCT-POSITIONING.md`
3. `docs/specs/README.md`
4. `docs/specs/architecture/` 下与任务相关的规范
5. `docs/specs/domain/` 下与任务相关的领域合同
6. `docs/specs/systems/` 下对应系统 Spec
7. `docs/specs/interfaces/`、`docs/specs/quality/` 下与任务相关的规范
8. 当前 `docs/exec-plans/active/` 中明确指定的执行计划
9. 仅在需要理解设计理由或形成 Design Delta 时读取 `docs/design/`

`docs/product/PRODUCT-POSITIONING.md` 是产品级最高约束；`docs/design/research/` 是证据与研究层，不得被当作实现接口合同。

## 2. 权威优先级

发生冲突时按以下优先级处理：

```text
1. docs/product/PRODUCT-POSITIONING.md
2. docs/specs/
3. docs/adr/
4. docs/design/ 中的 Canonical Design
5. 当前代码、数据库迁移和测试
6. Codex 自主推断
```

Product Positioning 约束产品本质、v1 Scope、Non-goals 与 Hard Constraints。任何 Canonical Design、ADR、Spec、EXEC 或代码都不得自行 supersede 它。若完成任务必须突破 Product Positioning，必须先形成明确的 Product Positioning Delta，并由用户接受后更新并重新冻结该文件，再同步下位治理文档。

现有代码与 Spec 冲突时，默认视为实现偏差，不得反向修改规范来迁就现有代码。现有 Spec / ADR / Canonical Design 与 Product Positioning 冲突时，默认视为下位治理待收敛项，不得以“既有规范已冻结”为理由反向覆盖产品定位。

## 3. Codex 的职责

Codex 必须：

- 首先验证任务没有突破 `docs/product/PRODUCT-POSITIONING.md`；
- 严格按照 Product Positioning、Spec 和 EXEC Plan 实现；
- 只修改任务允许的文件范围；
- 为每项关键行为补充可追踪测试；
- 保留已有公共行为，除非上位产品定位或 Spec 明确要求变更；
- 遇到旧代码越过系统边界时，通过 adapter/迁移逐步收敛；
- 在提交结果中列出修改文件、执行测试、未完成项和 SPEC GAP / POSITIONING GAP；
- 对公共 Schema、迁移、状态所有权和跨模块依赖保持最小变更；
- 当已获用户明确目标授权且现有规范不足时，主动完成 Design/ADR/Spec/EXEC 闭环，
  不得把可由治理闭环解决的问题长期留作阻塞；
- 自主接受的重大决定必须记录授权来源、备选方案、选择理由、不变量、迁移/回滚、
  验证证据和影响范围。

## 4. 用户委托下的架构自治

当用户明确授权一个产品/工程目标，或明确授权 Codex 自行接受重大架构决定时，
Codex MAY 为完成该目标自行提出、选择并接受必要的 Design/ADR/Spec/EXEC 变化，
随后修改产品代码。该权限仅限于已授权目标，不是脱离任务范围的永久自由裁量权。

**该架构自治不包含自动修改 Product Positioning 的权限。** 若目标必须改变产品本质、v1 Scope、Non-goals 或 Hard Constraints，Codex MUST 先提出 `POSITIONING GAP` / Product Positioning Delta，只有用户明确接受后才能修改 `docs/product/PRODUCT-POSITIONING.md` 并继续下位治理。

涉及下列事项时，Codex MUST 先更新并接受相应 ADR/Spec/EXEC，再修改代码：

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

自主决策 MUST 同时满足：

- 不违反 Product Positioning 的 v1 Scope、Non-goals 与 Hard Constraints；
- 不隐式建立第二 truth 或永久双写；若改变 owner，必须有迁移、reconciliation 和退休条件；
- 公共 API/Schema/数据库变化必须版本化、可迁移并有 rollback 或 forward-fix；
- 安全、隐私、Prompt Injection、grader-only、answer exposure 不得因体验优化而弱化；
- 决策必须列出至少一个真实备选方案及未采用原因；
- 每项关键行为必须有可追踪自动化测试和当前运行证据；
- Engineering、Policy/Ownership 与 Learning Evidence 结论继续分开。

若用户没有明确目标授权，Codex 仍不得借普通修复或审查任务扩大架构范围。

## 5. 局部实现自治

在不改变公共行为、领域语义、依赖边界和 Product Positioning 的前提下，可以自行决定：

- 局部变量、私有函数和测试 fixture 命名；
- 单模块内部私有函数拆分；
- 等价的小型重构；
- 不改变错误类型/错误码的错误文案；
- Spec 明确标记为 `MAY` 的实现选项。

## 6. POSITIONING GAP / SPEC GAP 协议

出现以下任一情况必须标记 GAP，不得隐式猜测：

### `POSITIONING GAP`

- 任务要求突破 v1 Scope 或 Non-goals；
- 下位 Spec / ADR / Canonical Design 与 Product Positioning 冲突；
- 为完成任务必须改变 Local Web、单用户、Local-first、BYOK、无官方中心服务器等产品级 Hard Constraint；
- 需要新增当前 Product Positioning 明确排除的产品能力。

处理方式：提出 Product Positioning Delta、理由、影响与候选方案；在用户明确接受前不得修改该定位或用代码制造既成事实。

### `SPEC GAP`

- 两份高权威下位规范冲突；
- 实现要求改变状态所有权；
- 公共 Schema 或关键错误语义缺失；
- 为完成任务必须新增生产依赖、服务或基础设施，但未违反 Product Positioning；
- 存在多个会造成不同业务结果的合理方案，而规范未选择；
- 必须违反任一下位 `MUST NOT` 才能完成任务。

处理方式：

1. 继续完成不受该缺口影响的部分；
2. 输出 GAP、受影响规则、候选方案、推荐选择和验证路径；
3. `POSITIONING GAP` 必须等待用户明确接受 Product Positioning Delta；
4. `SPEC GAP` 在已获第 4 节用户委托时，可由 Codex 选择推荐方案，显式创建并接受所需 ADR、更新 Spec、冻结 EXEC 后继续实现；
5. 未获对应委托时，等待用户或顶层设计流程完成选择；
6. 无论由谁选择，都不得先改代码、再用文档追认既成事实。

即使已获架构自治，以下事项仍必须在执行动作前请求用户确认：不可恢复的数据删除、
超出目标的外部付费/采购、提取或改变凭据用途、向新第三方发送个人敏感数据，或法律/合规责任变化。

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
- 新能力必须同时朝 `docs/product/PRODUCT-POSITIONING.md` 与 `docs/specs/architecture/system-architecture.md` 的目标边界收敛；
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

- 未违反 `docs/product/PRODUCT-POSITIONING.md`；
- 所有明确 Acceptance Criteria 已满足；
- 未违反状态所有权和依赖规则；
- 必要数据库迁移可前向执行并有明确回滚/兼容策略；
- 新增关键行为存在自动化测试；
- 错误、重试、幂等和观测行为符合 Spec；
- 无未声明的公共 API/Schema 变化；
- 所有 POSITIONING GAP / SPEC GAP 已显式报告；
- 没有占位实现、`TODO` 伪完成或仅 Mock 的“真实模型可用”结论。
