# Askora P1 / P2 产品缺口清单

> 状态：Current Product Gap Register
> 校准日期：2026-08-09
> 当前实现基线：UI-02B Goals / Path / Evidence 已完成；UI-02C Activity Lifecycle 已冻结但被依赖阻塞
> 用途：记录产品完整性审计中仍未关闭的 P1、P2 问题
> 权威边界：本文件是产品优先级与验收清单，不是 Spec、ADR 或 EXEC；实现前仍须按 `AGENTS.md` 完成治理闭环

## 1. 总览

| 优先级 | 总数 | 完全未修复 | 部分改善 | 已关闭 |
|---|---:|---:|---:|---:|
| P1 — 可靠的私人产品 | 7 | 5 | 2 | 0 |
| P2 — Apple 级体验精修 | 8 | 6 | 2 | 0 |

本清单不包含仍在推进的 P0。当前 P0 仍包括：提交 durable activity transcript / policy-bound Book Learning 依赖，并实施 [EXEC-030](exec-plans/active/EXEC-030-ui-02c-canonical-activity-lifecycle.md)，闭合“开始 → 恢复 → 完成 → 下一项”。

状态词：

- `OPEN`：尚无可交付产品能力；
- `PARTIAL`：存在基础能力，但未满足本项完整验收标准；
- `DONE`：已通过冻结合同、实现、测试、真实体验与发布证据门禁。

## 2. P1 — 让 Askora 成为可靠的私人产品

### P1-01 目标管理

**状态：PARTIAL**

当前已有只读 Goals、Path 与 Evidence 页面，但目标写入仍主要绑定单份资料启动流程。[Goals 页面](../apps/frontend/src/pages/Goals.jsx) 不提供编辑动作。

仍缺：

- 跨多份资料创建一个目标；
- 多个 target 的用户明确选择；
- 暂停、恢复和归档目标；
- 修改时间预算、截止时间和成功标准；
- 显式 replan、版本冲突与变更影响说明。

完成标准：用户可在不理解内部 ID 的前提下管理完整目标生命周期；所有写入由 SYS06 owner command 完成，版本、幂等、replan 和 rollback/forward-fix 语义明确。

### P1-02 模型设置体验

**状态：OPEN**

[Settings 页面](../apps/frontend/src/pages/Settings.jsx) 当前只能读取“AI 模型已配置/未配置”，用户仍需在 App 外编辑环境配置。

仍缺：

- Key 的安全录入、更新和清除；
- provider / model 选择；
- 连接测试与真实错误反馈；
- 本地 fallback、超时、限流和费用边界说明；
- 配置失败后的恢复动作；
- secret 不进入日志、Prompt、前端持久化或普通导出。

完成标准：首次使用者可以只在 App 内安全完成模型配置和验证，并能理解失败原因与数据发送边界。

### P1-03 数据控制与恢复

**状态：OPEN**

根 [README](../README.md) 仍明确说明仓库没有自动备份/恢复服务，需要自行备份数据库、文档目录和 `.env`。

仍缺：

- 自动本地备份与保留策略；
- 可验证的恢复演练；
- 用户数据导出；
- migration 前快照与失败恢复；
- 按范围删除资料、学习记录、模型执行记录和账号数据；
- 加密、完整性校验、兼容版本与恢复报告。

完成标准：用户可以在 App 内备份、验证、恢复、导出和删除数据；恢复后 canonical owner state、文件与 projection 一致，不重新生成已删除事实。

### P1-04 资料管理

**状态：PARTIAL**

[Library 页面](../apps/frontend/src/pages/Library.jsx) 已支持上传、处理状态、精确学科筛选、删除、知识地图和 SourceSpan 检查。

仍缺：

- 标题与正文搜索；
- 标签、集合和自定义分类；
- 重命名与元数据编辑；
- 重复资料识别与安全合并建议；
- 批量操作；
- 扫描 PDF / OCR 产品能力及其低置信度复核流程。

完成标准：资料规模增大后仍可快速找到、整理、纠正和去重；OCR 或模型结果只形成带证据和置信度的候选，不静默覆盖原文事实。

### P1-05 账号生命周期

**状态：DONE**

[认证客户端](../apps/frontend/src/api/auth.js) 当前覆盖注册、登录、刷新令牌和退出。

治理状态：用户已采纳本地优先 durable identity/privacy 方案；ADR-0009、`IDP-*` 与 P1-05 Vertical Slice 已冻结。EXEC-034～036 已串行完成并保留独立提交，完整工程、所有权、迁移、恢复与真实浏览器证据见 [P1-05 Release Evidence](releases/p1-05-account-lifecycle.md)。P1-04 的 EXEC-031～033 未被混入本项文件或提交。

方案边界：

- Platform Identity 唯一拥有 credential version、durable AuthSession/token family 与离线 RecoveryCredential；Redis/前端不是 session truth；
- Platform Privacy 只拥有 deletion request、subject manifest、owner step receipt、tombstone 与 restore barrier，不成为第九学习系统；
- SYS01～SYS08 各自执行 owner erasure；删除账号复用同一数据清除 foundation，不直接 ORM cascade User；
- 首版使用离线恢复套件，不引入短信/邮件第三方身份服务。

实施工作包：

- **EXEC-034 Credential/Session**：Argon2id + bcrypt rehash、修改密码、durable session、refresh-family replay/revoke、会话管理；
- **EXEC-035 Local Recovery**：注册/设置一次性恢复套件、单次使用、限流、恢复后全部 session 撤销和 recovery 轮换；
- **EXEC-036 Account Deletion**：versioned preview、重新认证/确认短语、pending/cancel、durable owner erasure、零残留 reconciliation、去 PII tombstone 与旧快照 restore barrier。

四个动作必须保持不同：退出当前 App 只撤销当前 session；撤销指定 App 只撤销该 token family；删除全部学习数据保留账号；删除账号删除全部用户数据并清除 credential/PII。

完成标准：`IDP-AC-001..012` 与 `P105-AC-001..008` 全部满足；SQLite/PostgreSQL、Redis 故障、并发 refresh/delete、restart recovery、cross-user、文件/outbox/projection、旧快照 barrier、360px/200% zoom/keyboard 和真实浏览器通过；三份 EXEC 独立 commit/release evidence 完成后方可标 `DONE`。

完成回执：上述门禁已于 2026-08-09 通过；Engineering 与 Policy/Ownership 为 `PASS`，Learning Evidence 为 `NOT_APPLICABLE_TO_ACCOUNT_LIFECYCLE`，项目整体学习证据状态保持不变。

### P1-06 首次使用引导

**状态：OPEN**

当前没有完整 onboarding。用户需要自行理解模型配置、资料库、目标、诊断和计划入口。

方案取舍：

| 方案 | 优点 | 主要风险 | 结论 |
|---|---|---|---|
| 一次性全屏 Wizard + 前端勾选 | 实现快、画面集中 | 步骤易与真实配置/资料/活动状态失真，刷新与既有用户迁移困难 | 不采用 |
| 事实驱动的可恢复旅程 | 可复用真实主链，支持跳过、恢复、回退和审计 | 需要先冻结 readiness 与展示偏好合同 | **推荐** |
| 只做页面内提示和空态 | 改动小、干扰低 | 无法保证首次用户完成整条路径，也难以跨页面恢复 | 作为后续补充，不单独关闭 P1-06 |

#### 推荐方案：事实驱动、可恢复的首次学习旅程

Onboarding 不实现一套平行的模型设置、资料导入、Goal、Planner 或教学流程，也不把前端步骤条当作完成事实。它只组合并解释已有 owner 发布的当前状态，把用户带到真实产品入口：

```text
了解数据与模型边界
→ 配置并验证模型
→ 导入一份资料
→ 说出并确认学习目标
→ 完成必要的起点检查
→ 开始并完成第一项 LearningActivity
→ 返回“今天”查看下一步
```

用户主进度只显示“模型、资料、目标、第一节”四步；诊断、mapping、plan 和 activity selection 由既有 Book Learning readiness 自动协调，不作为要求用户理解或点击的工程步骤。

#### 状态与完成语义

- 首次启动不得只根据 `localStorage`、注册时间或“是否看过欢迎页”判断；必须由 current-user scoped read model 聚合模型 readiness、资料状态、Goal/Plan owner refs、latest activity lifecycle 和 accepted transcript facts；
- 新增的 onboarding 持久状态只允许记录展示偏好，例如 `active/dismissed`、上次可见步骤和版本；它不是第九个领域 truth，也不得复制 document、goal、plan、activity 或 transcript 状态；
- 每一步是否完成必须由真实 source ref/version 派生。模型配置被清除、资料被删除、Goal 被归档或 activity 被 supersede 后，页面必须显示当前事实，而不是保留过期勾选；
- “完成首次学习”只由 SYS06 latest `LearningActivityStateV1=completed` 且满足其 accepted transcript completion precondition 证明。看到首条模型回复、停留时长、消息轮数、plan ready 或模型调用成功都不算完成第一节，也不代表掌握；
- 既有用户 backfill 不得从 legacy message、event recency 或前端缓存猜测完成。证据不足时显示“可继续设置/学习”，并允许跳过引导。

#### 入口与恢复体验

- 推荐新增 `/welcome` protected route。登录后的默认 `/today` 仅在引导处于 `active` 且未完成时进入该路由；用户直接打开 `/library`、`/book-learning/:documentId` 或 `/learn/:activityId` 时不得被强制重定向或丢失 deep link；
- 页面始终只有一个主动作，服务端返回确定性的 `next_action`/route/resource ref；UI 不从多个资料、Goal 或 activity 中自行猜选业务对象；
- “稍后再说”只隐藏引导，不创建完成事实；重新打开入口固定放在“设置”。刷新、退出重登、App 重启或跨步骤离开后，重新查询 owner facts 并恢复到最新可行动步骤；
- processing、quarantined、provider timeout/rate limit、Key invalid、version conflict 和 unsupported activity 必须显示“发生了什么、数据是否安全、现在能做什么”，并复用 P1-07 的稳定错误到恢复动作映射；
- 文案只使用“资料、学习目标、起点检查、学习活动、继续学习”等产品词。`canonical`、`SYS01～08`、schema、owner ref 和内部 command 只允许出现在折叠技术详情或审计证据中。

#### 数据与模型边界

- 引导必须明确说明：资料与学习记录保存在本机 Askora 数据范围；若调用远程模型，只发送当前任务所需的最小目标、问题与可见资料片段；Key 不进入 Prompt、日志、前端持久化或普通导出；
- 数据位置说明必须链接 P1-03 的真实数据控制/打开位置入口，不在 API response 中暴露内部绝对路径，也不得用“完全离线”“绝对隐私”等未经证据支持的文案；
- 默认主路径使用用户明确选择的私人资料，不自动插入样例或生成假目标/假进度；
- 若提供“先体验样例”，必须使用显式 opt-in 的本地 bundled/public fixture，记录来源类型、license/checksum/version，并在资料库、目标和学习页持续标记“样例资料”。样例副本必须可删除、current-user scoped，且仍走真实 canonical 学习主链；不得用前端 mock/sample state 冒充已完成第一节。样例来源字段和删除语义未冻结前，该入口保持关闭。

#### 依赖与范围

实现 Gate：

1. P0 UI-02C 已完成，`/learn/:activityId` 可以 start/resume/complete exact activity；
2. P1-02 已冻结并实现 App 内安全 Key 管理、provider/model 选择和真实连接测试；
3. P1-03 已提供可引用的数据保存/控制事实，P1-07 已提供本路径所需的稳定恢复动作；
4. 现有 UI-02A、UI-02B1/B2/B3 的资料、Goal、诊断、计划、真实模型和 transcript 合同继续作为唯一主链。

本项不扩展到：多资料 Goal、完整 Goal 编辑、Planner 重排、mastery 判断、Focus、笔记、备份实现或账号删除；这些仍分别属于 P1-01、P1-03、P1-05、P2-01 和 P2-03。

当前存在 `SPEC GAP`：onboarding preference 的 owner/持久化、readiness 聚合 Query、首次完成判定投影、首次路由/deep-link 规则，以及可选样例资料的来源与删除合同尚未冻结。实施前必须完成 additive Design/ADR、UI/API/Error/Persistence Spec、Vertical Slice 与独立 EXEC；不得先用前端状态实现后再补文档。

#### 验收标准

- clean profile 从首次登录开始，可按真实路径完成“模型验证 → 资料导入与处理 → Goal 明确确认 → 必要诊断 → activity start/resume/complete → Today 下一步”，中途至少一次 App 重启后不重复副作用；
- 每个步骤覆盖 loading/blocked/partial/stale/error/unauthorized、skip/reopen、删除或配置撤销后的事实回退；稳定错误只提供允许的恢复动作；
- 自动化覆盖 read-model source/version、preference 幂等与并发、existing-user backfill、cross-user、secret/log leakage、deep link、360px/200% zoom、键盘/focus/live region；
- deterministic fixture E2E 验证流程可靠性；另以真实配置 provider 完成一次受控主路径，证明模型连接和恢复，不把它称为真人学习效果；
- 由没有项目内部知识的首次用户完成一次无开发者介入的任务验收，并能准确说明数据保存在何处、什么内容会发送给模型、如何稍后继续和去哪里查看下一步；
- Engineering、Security/Privacy、Product Usability 与 Learning Evidence 分开报告；本项完成不改变 `LEARNING_EVIDENCE_INSUFFICIENT`。

完成标准：上述依赖和 SPEC GAP 已闭合，真实首次用户能独立完成第一项 canonical 学习活动并返回下一步；跳过、恢复、重新打开、失败恢复、数据/模型边界和样例区分均有机器验证与人工体验证据。

### P1-07 错误恢复中心

**状态：OPEN**

当前已有部分页面级错误、资料隔离复检和重试能力，但没有统一恢复入口。

仍缺：

- provider 超时、限流、Key 无效和模型不可用；
- 资料解析失败、隔离、OCR 低置信；
- migration、数据库、文件缺失与 outbox/DLQ 问题；
- 稳定错误码到用户动作的统一映射；
- 重试预算、等待状态、恢复结果和审计信息；
- 防止把系统失败记录成学习者错误或负向证据。

完成标准：用户可以看到“发生了什么、数据是否安全、现在能做什么、重试是否会重复副作用”，并能从统一入口完成恢复。

## 3. P2 — Apple 级体验精修

### P2-01 Focus 沉浸模式

**状态：OPEN**

`/focus/:activityId` 尚未实现；[App 路由](../apps/frontend/src/App.jsx) 中 `/learn/:activityId` 当前仍使用 unavailable 页面。

完成标准：Focus 与标准学习工作台共享 exact activity/session/run identity；切换模式不创建第二 TeachingAction、session 或 transcript，也不丢失帮助与答案暴露历史。

### P2-02 暗色模式

**状态：OPEN**

[视觉规范](specs/ui/visual-system.md) 已要求 dark tokens，但当前没有完整 dark theme 产品实现与设置入口。

完成标准：系统跟随、手动选择和持久化行为明确；正文、公式、代码、引用、状态色、hover、focus、disabled 在 light/dark 下均通过对比度和真实页面验收。

### P2-03 笔记、书签与原文标记

**状态：OPEN**

当前没有这些能力的 owner、Schema、版本、SourceSpan 绑定、导出和删除合同。

完成标准：先冻结“临时草稿、持久笔记、书签、原文标记、学习证据”之间的边界；笔记不得自动成为 canonical knowledge 或 mastery evidence。

### P2-04 窄屏与页面密度精修

**状态：PARTIAL**

Today、Goals、Path、Evidence 已完成 360×800 无横向溢出验收；兼容导师工作台仍存在大段空白、长纵向结构和信息密度不均。

完成标准：1440、1024、768、360 视口和中文长内容均无结构断裂；主要学习操作保持在清晰视觉路径内，兼容入口不抢占 canonical 主任务。

### P2-05 完整无障碍门禁

**状态：PARTIAL**

当前已有基础语义 heading、label、可见 focus、部分 focus return 和窄屏检查，但尚未执行 UI-03 全矩阵。

仍缺：

- 100% / 200% zoom；
- 全路径键盘操作；
- focus order、focus containment 与 Escape close；
- 屏幕阅读器状态/错误播报；
- light/dark 对比度；
- reduced motion；
- 长公式、长引用和最大合理列表。

完成标准：满足 [UI Quality and Migration](specs/ui/quality-and-migration.md) 的完整 responsive/accessibility gate，而不是只通过单页 happy path。

### P2-06 macOS 签名与公证

**状态：OPEN**

[Electron package 配置](../apps/frontend/package.json) 中 `notarize` 仍为 `false`。

完成标准：明确私人本地构建与可分发构建的边界；签名、公证、entitlements、hardened runtime、安装与升级均有可复现验证，不把本地 DMG 冒充可公开分发版本。

### P2-07 版本升级、自动更新与失败回滚

**状态：OPEN**

当前没有完整 App 更新、版本兼容、下载校验、migration gate、失败回滚和用户提示体验。

完成标准：更新前自动检查备份/兼容性，更新包可验证，数据库 migration 可 forward-fix；失败后 App 与个人数据保持可恢复状态。

### P2-08 真人学习效果验证

**状态：OPEN**

当前 Engineering 与 Policy/Ownership 可通过，但真实学习效果仍为 `LEARNING_EVIDENCE_INSUFFICIENT`。

仍缺：

- 真实用户 no-hint independent outcome；
- delayed independent performance；
- independent transfer；
- active learning time 与污染/归因记录；
- 个体层重复测量或合适的实验设计；
- No Learning Harm 判断与版本化标准。

完成标准：把真人学习证据与 engagement、对话轮数、模型连通性、synthetic learner 和 UI 可用性严格分开；仅在证据条件满足时形成限定范围的学习效果结论。

## 4. 推荐执行顺序

P0 完成后，建议按以下工作包推进：

1. **私人数据可靠性**：P1-03 数据控制与恢复 + P1-07 错误恢复中心；
2. **首次可用性**：先完成 P1-02 安全模型设置，再按 P1-06 的 readiness/引导 UI/真实首次体验门禁串行实施；P1-06 复用已完成的 P1-03、P1-07 与 UI-02C，不重复建设其能力；
3. **长期使用管理**：P1-01 目标管理 + P1-04 资料管理 + P1-05 账号生命周期；
4. **核心体验精修**：P2-01 Focus + P2-04 responsive + P2-05 accessibility + P2-02 dark theme；
5. **个人知识辅助**：P2-03 笔记/书签/原文标记；
6. **可靠分发**：P2-06 macOS 公证 + P2-07 更新/回滚；
7. **效果验证**：P2-08 真人延迟与迁移证据计划。

每个工作包必须独立完成 Design/ADR/Spec/EXEC、实现、自动化测试、真实页面验收和本地 commit。未经明确要求不 push。

## 5. 状态维护规则

- 完成功能代码不等于关闭问题；只有冻结合同与 Acceptance Criteria 全部满足才可标 `DONE`；
- “存在后端能力”不等于“用户能完成任务”；必须验证实际入口、反馈、恢复与数据持久性；
- UI、真实模型连通、OPVE、synthetic learner 和 engagement 不构成真人学习效果证据；
- 每次关闭或降级问题时，记录对应 ADR/Spec/EXEC、implementation commit、测试和 release evidence；
- 如果当前代码与本文件冲突，以 canonical Spec 与当前可执行证据为准，并更新本清单，不反向修改 Spec。
