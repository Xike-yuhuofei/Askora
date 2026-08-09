# UI-02B Goals, Learning Path and Evidence Vertical Slice

> 状态：Frozen
> 实现入口：EXEC-029
> 冻结日期：2026-08-09
> 用户授权：采纳产品完整性审计建议并开始执行
> 架构决定：ADR-0006

## 1. Objective

把 `/goals`、`/path`、`/evidence` 从工程占位页交付为真实、只读、current-user scoped 的产品页面，并让 `/today` 在存在唯一 canonical current plan 时显示其目标与活动；不存在可靠 owner 数据时保持诚实空态或部分态。

本 Slice 只闭合“看清目标、路径和学习证据”。活动启动/恢复 link、活动完成、目标编辑、重排计划和编辑掌握度均不在本 Slice。

## 2. End-to-End Path

```text
current-user auth
→ latest SYS06 LearningGoal versions
→ explicit goal scope or unique eligible current plan
→ canonical LearningPlan.activity_ids order
→ latest SYS03 MasteryEstimate per KnowledgeUnit
→ optional current-user SYS01 label join
→ /goals + /path + /evidence + truthful /today plan summary
```

## 3. Scope

IN：

- `GET /api/v1/workspace/goals` strict v1.0；
- `GET /api/v1/workspace/path?goal_id=<uuid>` strict v1.0，`goal_id` 可选；
- `GET /api/v1/workspace/evidence` strict v1.0；
- latest-version selection、canonical-user ownership、stable ordering、private/no-store；
- multiple current plans 时要求显式 goal scope，不按时间猜选；
- objective metadata 缺失时 exact ref + null + stable reason；
- `/today` 复用同一 SYS06 read selection，显示唯一 current goal/plan/activity，但不伪造可执行“继续学习”；
- Evidence 只显示 canonical SYS03 fields；SYS01 label 只在 current-user source 可验证时附加；
- loading/empty/ready/partial/error/unauthorized、360px/desktop、keyboard 和可访问状态。

OUT：

- Create/Confirm/Pause/Resume Goal；
- Replan/Reorder/Edit LearningPlan；
- SetMastery/EditEvidence/product-label threshold；
- canonical Activity start/resume/session link/completion；
- durable LearningObjective writer/backfill；
- ReviewSchedule timeline 伪装成 plan；
- 新数据库 migration、生产依赖或外部服务。

## 4. Read Semantics

### 4.1 Goals

- 每个 `goal_id` 只返回最高 version；
- 只匹配 `LearningGoal.user_id == canonical_user_id(current_user.id)`；
- 按 owner `created_at desc, goal_id` 稳定展示；
- title/capabilities/criteria/status/version 原样来自 `LearningGoalV1`。

### 4.2 Path

- 有 `goal_id` 时，先验证当前用户拥有该 goal，再读取该 goal 的 current plan；
- 无 `goal_id` 时，零个 eligible plan 返回 EMPTY，一个返回该 plan，多于一个返回 PARTIAL + `MULTIPLE_CURRENT_PLANS_REQUIRE_GOAL_SCOPE`；
- current plan 只接受最新未 superseded 的 `active|paused` plan；
- activity 顺序严格按照 `LearningPlan.activity_ids`；
- activity title 是稳定的类型展示文案，不是个性化学习事实；
- objective capability/cognitive process/status 在 owner 未发布前为 null，返回 `OBJECTIVE_METADATA_UNAVAILABLE`；
- 不读取 legacy dialog session 形成 activity link。

### 4.3 Evidence

- 每个 knowledge unit 只返回当前用户最高 version `MasteryEstimate`；
- probability/confidence/count/algorithm 缺失即 null，不变成 0；
- `product_label` 与 `product_label_rule_version` 固定为 null，除非未来 SYS03 正式发布；
- label 只可从当前用户文档 current revision 中 exact knowledge-unit id 命中；否则 null；
- legacy profile fields 不进入主列表，compatibility descriptor 默认隐藏。

### 4.4 Today

- 复用相同 plan selection，不维护第二套 current-plan 规则；
- current activity 依次取 canonical plan order 中 `active`、`available`、`planned` 的首项；
- 无 canonical session link 时不得显示可执行“继续学习”；planned/available 标为 `REQUIRES_START_COMMAND`，active 但无 link 标为 `UNAVAILABLE`；
- 多 current plan 时显示“请选择目标查看路径”，不猜选。

## 5. Failure and Security

- 未授权 goal scope 与不存在保持不可枚举；
- query 不返回本地路径、raw 文档、Prompt、grader-only data 或其他用户 label；
- owner payload/record mismatch 视为不变量失败，不降级为跨用户结果；
- 页面局部失败保留可用区域；主 query 失败显示可重试错误；
- response 不允许共享代理缓存。

## 6. Acceptance Criteria

- `UI02B-VSLICE-AC-001`：Goals/Path/Evidence 三页由真实 strict workspace query 驱动，不使用 placeholder/mock 产品数据。
- `UI02B-VSLICE-AC-002`：所有 goal/plan/activity/evidence current-user scoped；跨用户记录与 label 不泄漏。
- `UI02B-VSLICE-AC-003`：latest version、plan activity order 和 tie-break 稳定；前端不重排 canonical plan。
- `UI02B-VSLICE-AC-004`：多 current plan 要求显式 goal scope；objective metadata 缺失保持 null/partial，不推断。
- `UI02B-VSLICE-AC-005`：Evidence 不从 probability 生成掌握标签，不把 missing 变 0，legacy 默认不进入主视图。
- `UI02B-VSLICE-AC-006`：Today 可显示唯一 canonical goal/plan/activity，但无 session link 不提供假“继续学习”。
- `UI02B-VSLICE-AC-007`：API transport only、query read-only、无新 owner/第二 truth/数据库 migration/生产依赖。
- `UI02B-VSLICE-AC-008`：三页覆盖 loading/empty/ready/partial/error/unauthorized，关键状态有文字且键盘可达。
- `UI02B-VSLICE-AC-009`：frontend/backend/docs/diff gates 与独立 clean-commit 验证有真实证据。
- `UI02B-VSLICE-AC-010`：只声明 Engineering/Contract/Security gates；Learning Evidence 保持 `LEARNING_EVIDENCE_INSUFFICIENT`。

## 7. Gate

只有 `UI02B-VSLICE-AC-001..010` 全部满足时 UI-02B 为 DONE。活动完成与 durable activity/session link 必须经独立 ADR/Spec/EXEC，不能在本 Slice 用 UI 状态补写。
