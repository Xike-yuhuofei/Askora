# P1-06 事实驱动的首次学习旅程设计

> 状态：Canonical Design / Accepted for P1-06
> 日期：2026-08-09
> 授权：用户明确采纳推荐方案，并要求最终真正关闭 P1-06、通过相关测试
> 关联决策：ADR-0106；Course-centric route / completion destination 由 ADR-0022 修订

## 1. 目标

让第一次使用 Askora 的私人 macOS 用户不需要理解内部系统、ID 或工程流程，即可完成：

```text
了解数据与模型边界
→ 在 App 内配置并真实验证模型
→ 导入一份自己的资料
→ 说出并确认学习目标
→ 完成必要的起点检查
→ 开始、恢复并完成第一项 LearningActivity
→ 返回当前课程，看见可恢复的下一项 LearningActivity
```

页面只呈现“模型、资料、目标、第一节”四个主步骤。diagnostic、mapping、plan、activity
selection 继续由既有 Book Learning 主链协调，不暴露为要求用户理解的工程步骤。

## 2. 产品原则

### 2.1 不建立平行流程

Onboarding 不新增第二套模型设置、上传、Goal、Planner、Activity、transcript 或 recovery 逻辑。
它只读取并解释 P1-02、SYS01、SYS06、SYS08、P1-03 与 P1-07 已发布的事实和动作。

### 2.2 事实决定完成，偏好只决定是否展示

持久化 `OnboardingPreferenceV1` 只记录：

- journey/version；
- `ACTIVE|DISMISSED` 展示偏好；
- 已确认的数据与模型说明版本；
- dismiss reason 与更新时间。

它不保存 step completion、document/goal/plan/activity/transcript ref、模型 Key 或业务状态副本。
步骤状态每次从 owner facts 重新计算；配置清除、资料删除、Goal 归档或 activity supersede 后必须
如实回退。

### 2.3 一个主动作，服务端选择语义

`OnboardingJourneyViewV1` 每次只返回一个确定性的 `next_action`。前端只呈现服务端给出的
action/route/resource ref，不按数组顺序、创建时间或本地缓存猜选业务对象。若存在多个无法由
owner link 唯一确定的资料、目标或活动，服务端返回“选择”动作并导航到真实列表页，不替用户
隐式选择。

## 3. 状态模型

### 3.1 展示偏好 owner

`Platform Experience Preference` 是 presentation-only platform capability，不属于 SYS01～SYS08，
也不取得任何学习业务写入权。它是 `OnboardingPreferenceV1` 的唯一 writer；React、路由 guard、
read-model assembler 与 localStorage 都不是 writer。

命令只有：

```text
ACKNOWLEDGE_BOUNDARIES
DISMISS
REOPEN
FINISH_AND_DISMISS
```

`FINISH_AND_DISMISS` 只有当同一请求重新验证当前 journey 已 COMPLETE 时才允许执行。它只把
展示偏好改为 dismissed，不创建或保存“完成首次学习”的事实。

### 3.2 首次完成判定

第一节完成只由 SYS06 的 `FirstActivityCompletionProjectionV1` 证明：current-user 的 exact
`LearningActivityStateV1=completed`，并携带该 transition 已验证的 accepted transcript source ref。
模型调用成功、看到回复、消息轮数、停留时间、plan ready 或前端按钮点击均不算完成。

SYS06 投影按最早完成时间、activity id 稳定 tie-break 返回首个合格 completion；它是只读投影，
不新增 lifecycle writer，也不改写 mastery、review 或 learning evidence。

### 3.3 四步派生

- 模型：P1-02 summary 为 ACTIVE，`runtime_ready=true`，且 runtime revision 与 verified profile
  revision 相同；只配置但未真实验证不算完成。
- 资料：SYS01 至少存在 current-user、current revision、可进入 Book Learning 的资料；processing、
  quarantined、failed、deleted、stale projection 不算 READY。
- 目标：SYS06 存在 current-user confirmed/current Goal，并保留其 canonical source mapping；draft、
  archived、superseded 或无法验证来源不算完成。
- 第一节：仅使用 3.2 的 SYS06 completion projection。

每步为 `NOT_STARTED|IN_PROGRESS|COMPLETE|BLOCKED|STALE`。跨 source 缺失时返回 PARTIAL/STALE，
不得转成 false 或假 READY。

## 4. 路由与恢复

- 新增 `/welcome` protected route；
- 只有默认入口 `/` 在 `visibility=ACTIVE` 且 journey 未完成时进入 `/welcome`；`/today`、`/learning`
  先按 ADR-0022 做无副作用 legacy compatibility resolution，再应用同一 onboarding guard；
- `/library`、`/book-learning/:documentId`、`/learn/:activityId` 等直接 deep link 永远不被
  onboarding guard 改写；
- readiness 请求失败时保留用户 intended route，不把失败当作完成；页面提供可恢复提示与
  Settings 重开入口；
- “稍后再说”只执行 DISMISS；Settings 固定提供 REOPEN；
- 刷新、重登、App 重启后重新查询 owner facts，不重放已成功的上传、Goal、diagnostic、start 或
  complete command；
- provider、资料、版本冲突和执行错误只呈现 P1-07 服务端允许的 recovery action。

## 5. 既有用户迁移

迁移创建 preference table 时，把迁移事务内已存在的用户写为：

```text
visibility=DISMISSED
dismissed_reason=LEGACY_EXISTING_USER_BACKFILL
```

不从 legacy message、event recency、localStorage 或注册时间猜测其完成状态。迁移后首次查询仍无
preference row 的新用户才创建 ACTIVE v1。既有用户可从 Settings 显式 REOPEN；重新打开后页面
仍显示当前事实，而不是 backfill 的假完成。

## 6. 数据、模型与样例边界

首次页必须明确：资料与学习记录位于 Askora 本地数据范围；远程模型调用只发送当前任务所需的
最小目标、问题与可见资料片段；Key 不进入 Prompt、日志、frontend persistence 或普通导出。
数据位置只链接 P1-03 的真实控制入口，不返回本地绝对路径。

v1 不提供样例资料。没有冻结 bundled source、license/checksum/version、current-user copy 与删除
合同前，任何“先体验样例”入口必须保持不存在或禁用，不得用 mock/sample state 完成步骤。

## 7. 错误与信任

页面固定回答：发生了什么、数据是否安全、现在能做什么。错误分支只依据 stable code、
source availability 与 `RecoveryActionV1`；不得匹配自由文本。系统/provider/storage 失败不得产生
learner failure、0 分、mastery decrease、review failure 或 activity completion。

## 8. 交付拆分

### P1-06A / EXEC-1061

冻结并实现 preference persistence、existing-user backfill、SYS06 first completion projection、
readiness assembler、strict API/error/security contracts和迁移/架构测试。

### P1-06B / EXEC-1062

实现 `/welcome`、默认入口/deep-link 规则、Settings 重开、真实四步主链、恢复/无障碍/响应式、
deterministic + real-provider + App restart 验收、release report 与 gap closure。

## 9. 完成声明边界

P1-06 DONE 只证明 Engineering、Security/Privacy、Product Usability 与真实首次学习产品路径通过。
它不证明用户掌握、长期记忆、真人学习效果或模型回答质量；Learning Evidence 继续为
`LEARNING_EVIDENCE_INSUFFICIENT`。
