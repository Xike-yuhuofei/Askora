# UI-02B1 — Material-to-Learning Launch

> 状态：**FROZEN / EXEC-025 DONE**
>
> 冻结日期：2026-08-08
>
> 上游：UI-02A、SPEC-D04～D06、v0.3 Adaptive Teaching Loop
>
> 范围：从单份资料进入第一轮 canonical 自适应教学

## 1. Objective

为当前用户提供一条真实、可恢复、可审计的最小产品路径：

```text
/library 选择资料
→ /book-learning/:documentId
→ BookLearningReadiness
→ 创建并确认 LearningGoal
→ GoalKnowledgeMapping / GoalSpecificKnowledgeSubgraph
→ prerequisite diagnostic
→ LearningPlan / LearningActivity
→ existing canonical TeachingAction / EvidenceBundle / SYS08 execution
```

本 Slice 只接通既有 Book-to-Learning owner façade；不创建第二 Planner、第二 Assessment、第二 LearnerState、第二 TeachingAction 或 book-specific tutor。

## 2. Scope

IN：

- 资料库中选中资料的“从这份资料开始学习”入口；
- `/book-learning/:documentId` protected route；
- readiness 九态的真实展示与刷新；
- 单资料自然语言 Goal candidate、用户确认、mapping；
- learner-visible prerequisite diagnostic；
- plan generation、next activity selection；
- 当前页面内连续 canonical teaching rounds；
- exact owner refs、idempotency、auth、grader-only isolation、窄屏与键盘测试。

OUT：

- 完整 `/goals`、`/path`、`/evidence` UI-02B；
- Goal 编辑、暂停、恢复、删除或多资料 Goal；
- 多 target Goal 的自动 target 选择；
- durable activity↔dialog-session link、教学消息历史查询或跨重启恢复；
- Focus 模式、笔记、人工知识发布、复习编辑；
- 新教学策略、模型、生产依赖或数据库迁移。

## 3. Route and Presentation Contract

### UI02B1-010

`/library` MAY 只对未处于 `failed|rejected|quarantined` 的当前用户资料提供入口。入口不得根据前端 document status 宣称已可学习；最终状态只由 `GET /api/v1/book-learning/{document_id}/readiness` 决定。

### UI02B1-011

`/book-learning/:documentId` 使用 Standard Shell，是资料 bootstrap/launch 页面，不是第二全局导航或兼容 quick session。页面刷新 MUST 从 readiness + owner refs 重建当前步骤，不得把 React state 当 canonical truth。

### UI02B1-012

教学回合继续调用 `POST /api/v1/book-learning/activities/{activity_id}/start`。当前 Slice MAY 在同一页面展示本次打开期间的 learner/assistant 消息，但 MUST 明示这些展示记录不具备 durable resume/history 合同；不得伪装 activity↔dialog-session link。

## 4. Readiness-driven State Machine

UI MUST 逐字消费后端 `state`、`next_commands`、`reason_codes` 和 exact `owner_refs`，不得自行从资料、Goal、诊断或计划字段推导下一业务状态。`READY_TO_LEARN` MUST 在 SYS06 `LearningActivity` owner ref 中以 `status=selected` 标出 exact selected activity，刷新恢复不得重放 activity-selection command。

| Readiness | UI 行为 |
|---|---|
| `PROCESSING` | 显示处理中与刷新，不发送业务 command |
| `CONTENT_PARTIAL` | 显示资料尚不足以学习与 reason，不让 LLM 兜底 |
| `READY_FOR_GOAL` | 显示自然语言目标表单 |
| `GOAL_CONFIRMATION_REQUIRED` | 读取并展示候选 Goal，只有用户明确确认后调用 confirm |
| `DIAGNOSIS_REQUIRED` | 仅执行后端 `next_commands` 授权的 mapping/diagnostic command |
| `DIAGNOSING` | 展示 learner-visible item 并提交实际回答/assistance |
| `PLAN_READY` | 根据 `next_commands` 生成计划或选择 next activity |
| `READY_TO_LEARN` | 重放 activity selection 获取 exact plan/activity，允许教学输入 |
| `BLOCKED` | 显示稳定、非敏感原因和返回资料库，不提供绕过入口 |

未知 major schema、未知 readiness state、缺关键 owner ref 或 command/payload 不一致 MUST fail closed。

## 5. Goal and Target Boundary

### UI02B1-020

Goal 表单只提交自然语言 `intent`、可选 application context、deadline、weekly budget；UI 不生成 KnowledgeUnit id、success criteria 或 plan。

### UI02B1-021

本 Slice 只自动推进恰好一个 `selected_target_id` 的 mapping。若 target 为零或多于一个，必须显示 `UI02B1_SINGLE_TARGET_REQUIRED`，不得由前端挑选或排序 target。多 target 选择留待独立 owner contract。

## 6. Learner-visible Diagnostic Contract

### UI02B1-030 — Additive Payload

`GET /api/v1/book-learning/goals/{goal_id}/diagnostic` 在 active diagnostic 时 MUST 在既有 `payload.need` 旁返回：

```yaml
learner_item:
  item_ref:
    entity_type: AssessmentItem
    entity_id: uuid
    version: string
  need_id: uuid
  need_version: integer
  item_type: exact|multiple_choice
  prompt: string
  options: [string]
```

`learner_item` 是 SYS04 exact AssessmentItem 的安全只读投影，不是第二 AssessmentItem truth。

### UI02B1-031 — Isolation

该 payload MUST NOT 包含 `answer_key`、correct answer、rubric、explanation、grader prompt、内部路径或 hidden metadata。Item 不存在、版本不匹配或不属于该 current-user active need 时必须 stable error/fail closed。

### UI02B1-032 — Assistance

无提示诊断回答必须提交 explicit independent assistance snapshot；UI 不得把缺失 assistance 当 independent，也不得在当前 Slice 暴露未冻结的 hint/exposure controls。

## 7. Identity, Idempotency and Recovery

- 每个 command 使用在同一资源/version/操作范围内稳定的 idempotency key；网络重试不得创建第二事实。
- readiness 的 owner refs 是 goal/mapping/need/plan/activity 恢复入口；前端 local/session storage 不得保存 canonical domain object。
- 历史本地用户若仍使用非 UUID primary key，owner command/query MUST 复用 `askora:legacy-user:{id}` 的 deterministic UUID projection；不得修改旧 User 主键或产生随机 identity。
- teaching `session_id` 与 turn counter MAY 保存在 `sessionStorage` 作为当前打开期间的 transport identity；它们不是 canonical activity/session link。
- command 成功或失败后 MUST 重新获取 readiness；409/version conflict 必须以 owner 最新状态恢复，不在前端强行覆盖。

## 8. Security and Privacy

- 所有 query/command 继续使用 current-user auth；跨用户 document/goal/need 必须 fail closed。
- 页面错误只展示稳定短文案与 request/correlation id；不得展示 stack、文件路径、grader-only 数据或内部安全规则。
- learner/assistant 文本只在当前页面内保留；本 Slice 不新增浏览器 durable message store。
- Teaching response 复用 SafeMarkdown/RichMessage 安全回退，不渲染 raw HTML 或 unsafe URL。

## 9. Acceptance Criteria

- `UI02B1-AC-001`：资料库可进入 current-user scoped launch route，最终 readiness 不由前端推断。
- `UI02B1-AC-002`：页面刷新可从 readiness/owner refs 恢复 Goal、diagnostic、plan 或 ready state。
- `UI02B1-AC-003`：Goal 必须由用户明确确认；UI 不生成 KU/plan truth。
- `UI02B1-AC-004`：多 target mapping fail closed，不由前端选择业务 target。
- `UI02B1-AC-005`：active diagnostic 返回真实 learner-visible prompt/options，grader-only 字段为零泄漏。
- `UI02B1-AC-006`：diagnostic response 经现有 SYS04→SYS03→SYS06 path，system failure 不记 learner failure。
- `UI02B1-AC-007`：plan/activity 由现有 SYS06 owner command 生成/选择。
- `UI02B1-AC-008`：教学请求进入 existing SYS05/SYS02/SYS08 canonical path，不创建 book tutor。
- `UI02B1-AC-009`：重复 command/teaching retry 不创建第二 canonical fact/event。
- `UI02B1-AC-010`：unknown/blocked/partial/unauthorized/version conflict 均 fail closed。
- `UI02B1-AC-011`：360px、keyboard、loading/error/live-status 与 protected deep link 有自动化或人工验收证据。
- `UI02B1-AC-012`：Engineering/UI Contract Gate 与 `LEARNING_EVIDENCE_INSUFFICIENT` 分开报告。

## 10. Freeze Decision

`UI-02B1`：**FROZEN / EXEC-025 DONE**。任何多 target 自动选择、durable activity/session link、完整 Goals/Path/Evidence 页面或公共 diagnostic grading 语义变化，必须进入后续独立 Spec/EXEC。
