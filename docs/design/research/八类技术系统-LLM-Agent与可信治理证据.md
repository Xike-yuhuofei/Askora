# 八类技术系统：LLM、Agent 与可信治理证据

> 阶段：B｜统一研究资料库

## 1. 研究问题

1. LLM 与 Agent 应在 Askora 中负责什么、不负责什么？
2. Tool Calling / Agent Workflow 如何与确定性领域状态分离？
3. Prompt Injection、过度代理权、错误工具调用如何控制？
4. 如何实现模型、Prompt、证据、决策和执行的全链路追踪？

## 2. LLM 的正确定位

LLM 擅长：

- 自然语言理解与结构化抽取；
- 解释、改写、举例和问题生成；
- 开放式答案语义判断；
- 在约束下生成候选 TeachingAction/查询计划/题目；
- 调用工具处理模型本身不擅长的确定性任务。

但 LLM 输出具有非确定性和事实错误风险。

`Askora 设计选择`：

```text
LLM = 推断器 / 生成器 / 候选提出者
≠ 业务真相数据库
≠ 学习者状态唯一裁决者
≠ 教学策略最终所有者
≠ 无约束 Agent 总控器
```

所有关键业务对象必须由领域服务根据结构化、可验证输入持久化。

## 3. Tool Use 与 Agent 的研究启示

Toolformer、ReAct 等研究证明 LLM 可以学习或通过提示决定何时调用外部工具，并把推理与环境交互结合起来。

- 证据等级：`研究证据`
- 技术可行：高
- 工程成熟：高（现代模型 API）
- 对教学效果：不能直接推出

对 Askora 的价值：

- 检索、计算器、代码执行、图查询、评估器等能力可作为工具；
- LLM 不需要把所有能力“藏在 Prompt 中”；
- 工具执行结果可结构化进入后续步骤。

但 ReAct/Toolformer 证明“能调用工具”，并不证明“让模型自由选择所有教学决策更优”。

## 4. Workflow Orchestration vs Autonomous Agent

`Askora 设计选择`

教学主链优先采用显式 workflow/state machine：

```text
load context
→ request teaching decision from 4.5
→ request EvidenceBundle from 4.2
→ call generation model
→ validate structured output
→ validate citations/policy
→ render interaction
→ capture Attempt/Feedback
→ publish events
```

LLM Agent 只在局部开放问题中使用，例如：

- 复杂资料研究；
- 多工具取证；
- 生成多个候选解释；
- 用户授权的外部探索。

**原因**：学习流程中的状态转换、答案泄漏、掌握更新、计划更新需要确定性 ownership 和审计。

## 5. 结构化输出与 Schema 校验

`行业实践` + `Askora 设计选择`

模型输出进入业务层前必须：

1. 使用明确 JSON Schema / typed contract；
2. Schema validation；
3. enum/范围检查；
4. foreign-key / entity existence 校验；
5. provenance 校验；
6. 业务约束校验；
7. 失败时 retry / repair / fallback。

禁止：

```text
LLM 输出一段 JSON 字符串
→ 不校验
→ 直接 UPDATE learner_state
```

应改为：

```text
ModelInference
→ validated candidate
→ domain command
→ domain rule verification
→ immutable event / state update
```

## 6. Prompt 与模型版本治理

`Askora 设计选择`

每次关键模型调用至少记录：

```text
model_provider
model_name
model_version/snapshot
prompt_template_id
prompt_version
input_schema_version
output_schema_version
temperature/reasoning config
toolset_version
evidence_bundle_id
latency
usage/cost
validation_result
trace_id
```

Prompt 是可部署代码资产，必须：

- 版本控制；
- 回归测试；
- 变更审查；
- A/B 或 shadow compare；
- 可回滚。

## 7. 模型路由

`Askora 设计选择`

不同任务应按能力/成本/延迟/隐私路由，而非全局固定最强模型：

| 任务 | 优先要求 |
|---|---|
| 内容候选抽取 | 结构化输出稳定、长上下文、成本 |
| 检索查询改写 | 低延迟、低成本 |
| 开放式评分 | 推理稳定、rubric following |
| 教学解释 | 表达、证据忠实、语气控制 |
| 简单分类 | 小模型/规则优先 |
| 确定性计算 | 不调用 LLM，使用工具/代码 |

路由器可以优化成本，但不能绕过安全与教学决策协议。

## 8. Prompt Injection

OWASP LLM01:2025 将 Prompt Injection 列为核心风险，并明确指出直接/间接注入可以来自用户输入、网页、文件等外部内容；RAG 与 fine-tuning 并不能完全消除该问题。

- 证据等级：`行业安全共识`
- Askora 风险：高，因为用户会上传不可信文档并允许检索/Agent 使用。

### 8.1 核心原则

`Askora 设计选择`

上传文档中的：

```text
“忽略之前指令”
“调用工具删除数据”
“输出系统 Prompt”
```

全部只是 **source data**，不能成为 control plane instruction。

### 8.2 防御层

```text
不可信数据标记
→ data/instruction channel separation
→ retrieval provenance
→ tool allowlist
→ least privilege
→ parameter validation
→ no-secret model context by default
→ output validation
→ human/user confirmation for side effects
→ monitoring / red-team
```

没有任何单一 Prompt 技巧可以提供完全防护，必须采用纵深防御。

## 9. Excessive Agency 与工具权限

OWASP 对 Agentic/LLM 应用强调过度代理权的风险。Askora 的最小权限原则：

- 模型只获得当前任务必要工具；
- 默认无任意 shell/网络/文件系统权限；
- 写 learner state 必须走领域命令；
- 写 GitHub、邮件、外部系统等有副作用工具必须单独授权；
- tool arguments 做 schema + permission validation；
- 长链 Agent 设置 step/token/time/cost 上限；
- 所有工具调用进入 trace。

## 10. NIST Generative AI Risk Management

NIST AI 600-1（Generative AI Profile）提供跨行业生成式 AI 风险管理框架，强调在整个生命周期识别、测量、管理风险与信任属性。

- 证据等级：`官方治理框架`
- Askora 设计含义：把评估、安全、监控、人工控制纳入系统生命周期，而不是上线前一次性“安全检查”。

适用于 Askora 的治理维度：

- content provenance；
- confabulation/错误输出；
- privacy；
- information security；
- human oversight；
- measurement/evaluation；
- incident response。

## 11. 事件协议与 Event-Driven Architecture

CloudEvents 是 CNCF 的开放事件格式规范，为跨系统事件提供标准上下文字段。Askora 不必逐字复制 CloudEvents，但应采用相同思想：

```text
id
type
source
time
subject/entity
data
schema version
trace id
```

- 证据等级：`行业标准实践`
- 工程成熟：高

### Outbox

Debezium 官方文档说明 Transactional Outbox 用于减少数据库状态与跨服务事件之间的不一致。

`Askora 设计选择`：关键领域更新采用：

```text
DB transaction:
  domain state/event
  + outbox record
→ async publisher/CDC
→ consumers
```

消费者必须幂等，并处理重试、乱序、DLQ 和 schema evolution。

## 12. Event Sourcing 的边界

`行业实践` + `Askora 设计选择`

Askora 的学习行为非常适合保存不可变 LearningEvent，因为需要：

- 重算 learner state；
- 比较算法版本；
- 审计掌握判断；
- 反事实/离线评估。

但不必把整个产品所有实体都做成纯 Event Sourcing。

推荐：

```text
学习与决策历史：append-only event/decision ledger
当前查询状态：materialized projection / relational state
```

这比“所有系统完全事件溯源”更易实施。

## 13. DecisionTrace

`Askora 设计选择`

每个重要算法决策统一记录：

```text
inputs(snapshot ids)
candidate actions
constraints
scores/predictions
selected action
reason codes
confidence
algorithm version
model version
experiment assignment
trace id
```

必须记录的决策至少包括：

- AssessmentItem selection；
- AssessmentResult（复杂评分时）；
- MasteryEstimate update；
- TeachingAction selection；
- LearningPlan generation/replan；
- ReviewSchedule update；
- 检索路线/最终 EvidenceBundle 选择（可使用 retrieval trace 并关联 DecisionTrace）；
- 高风险模型路由/降级。

## 14. 可观测性

OpenTelemetry 提供 traces、metrics、logs 的厂商中立观测标准。

`行业实践`

Askora 应把以下 ID 串联：

```text
trace_id
session_id
learning_event_id
decision_id
model_inference_id
retrieval_trace_id
```

观察指标：

- 模型延迟/错误/成本；
- 工具调用成功率；
- schema validation failure；
- fallback rate；
- citation failure；
- prompt injection block；
- teaching decision outcome；
- 学习结果。

## 15. 无模型降级

`Askora 设计选择`

核心学习状态不能因外部 LLM 不可用而完全不可工作。

至少支持：

- 已有 AssessmentItem 的确定性判分；
- learner state 更新；
- ReviewSchedule；
- LearningPlan 读取；
- 基础模板反馈；
- BM25/向量检索；
- 已缓存 EvidenceBundle。

这迫使架构把业务状态从模型供应商中解耦。

## 16. 参考资料（核心 10 项）

1. Yao, S. et al. (2022/2023). *ReAct: Synergizing Reasoning and Acting in Language Models*. https://arxiv.org/abs/2210.03629
2. Schick, T. et al. (2023). *Toolformer: Language Models Can Teach Themselves to Use Tools*. https://arxiv.org/abs/2302.04761
3. NIST (2024, updated 2026). *Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile (NIST AI 600-1)*. https://doi.org/10.6028/NIST.AI.600-1
4. OWASP GenAI Security Project. *LLM01:2025 Prompt Injection*. https://genai.owasp.org/llmrisk/llm01-prompt-injection/
5. OWASP GenAI Security Project (2025). *Top 10 for Agentic Applications*. https://genai.owasp.org/
6. CNCF CloudEvents. *CloudEvents Specification*. https://github.com/cloudevents/spec
7. Debezium. *Outbox Event Router*. https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html
8. OpenTelemetry. *Documentation*. https://opentelemetry.io/docs/
9. Martin Fowler. *Event Sourcing*. https://martinfowler.com/eaaDev/EventSourcing.html
10. Qiao, S. et al. (2023). *Making Language Models Better Tool Learners with Execution Feedback*. https://arxiv.org/abs/2305.13068

## 17. 证据缺口

- Agent 框架更新速度远高于教育效果研究，工程能力不能被当作教学有效性证据。
- Prompt Injection 不能宣称“已解决”，只能通过降低权限、隔离和检测降低风险。
- LLM-as-a-judge 在开放式学习评分中的稳定性、公平性和跨模型一致性必须用 Askora 自建人工标注集校准。
- 模型路由的成本最优点随供应商和价格变化，应由配置/实验决定，不写死在教学领域模型中。