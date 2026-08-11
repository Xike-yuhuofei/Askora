# Askora UI-02A Canonical Library and Scoped Knowledge Map Completion Report

> Status：DONE
> 日期：2026-08-08
> 实现合同：`EXEC-016` / `UI02A-VSLICE-AC-001..012`
> Implementation commit：本报告与实现同一原子提交，hash 见 Git 历史与交付回执

## 1. Release 结论

```text
Engineering Gate: PASS
Contract / Ownership / Security Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

UI-02A 已交付真实 current-user 资料库、durable/recoverable 文档处理、source-bound deterministic KnowledgeUnit candidates、单文档范围 Knowledge Map 与 SourceSpan Inspector。页面不把文件、章节顺序或旧 KnowledgePoint 冒充已发布知识事实；没有可靠 relation 时返回并显示空关系。

本 Release 只证明 UI Engineering、合同、ownership 与安全边界满足冻结标准，不证明改善真人学习效果。

## 2. Spec / Query 交付

- 新增 strict immutable `LibraryWorkspaceV1`、`KnowledgeMapWorkspaceV1` 与 SourceSpan DTO；拒绝未知字段和 naive datetime。
- `GET /api/v1/workspace/library` 与 `GET /api/v1/workspace/knowledge-map` 强制当前用户、private `no-store`、稳定排序和数量上限。
- Knowledge Map 强制 single-document scope；返回 source/version/availability/audit refs，不返回 storage/internal absolute path。
- legacy `minimal-binding-v1` 明确标为 stale compatibility/pending rebuild；grader-only、quarantined 与 unauthorized 内容不进入 learner-visible map/Inspector。

## 3. Content / Recovery 交付

- `deterministic-structure-v2` 以 checksum、parser 与 extraction version 固化 MaterialRevision identity；显式 Markdown 标题形成稳定 candidate identity，并绑定各自 current revision SourceSpan。
- 资料上传与 document-processing outbox task 在同一事务持久化；移除请求进程内 `asyncio.create_task` 分发。
- durable worker 实现启动 reconciliation、stale processing recovery、bounded retry、dead letter 与 transient database outage 生存；重复执行不重复 canonical revision/projection。
- 无可证关系不生成 edge；未引入 LLM 自动发布、图数据库、外部队列、第二 content truth 或 production dependency。

## 4. UI 与真实验收

- `/library` 提供 desktop 三栏与 `<=768px` 单列布局：资料上传/筛选/状态/删除、候选节点、关系文本等价视图与 SourceSpan Inspector。
- 覆盖 loading、empty、ready、partial、stale、error、unauthorized 与 live processing；上传后持续刷新，revision/status 变化会同步刷新 map。
- 删除使用二次确认，支持 Escape 关闭与焦点返回；交互控件具备 label/pressed/live-region 语义；页面未引入动画，沿用全局 reduced-motion 行为。
- 真实本地页面完成 `Markdown 上传 → pending → completed → 2 candidates → 0 relations → SourceSpan → 删除`；390×844 实测无水平溢出且浏览器 console 0 error。CSS 同一窄屏分支覆盖 360px，自动化测试覆盖关键交互；desktop 默认视口完成同一路径验证。

## 5. Acceptance Criteria Matrix

| AC | 结果 | 证据摘要 |
|---|---|---|
| UI02A-001 | PASS | current-user 资料 list/upload/status/filter/delete；无 internal path |
| UI02A-002 | PASS | durable outbox、幂等、bounded retry、restart/stale recovery tests |
| UI02A-003 | PASS | v2 candidates 绑定 current MaterialRevision SourceSpan |
| UI02A-004 | PASS | legacy binding 显式 stale/pending rebuild |
| UI02A-005 | PASS | single-document scope、caps、stable ordering、source/version/availability |
| UI02A-006 | PASS | 无可靠 relation 时 edge 为空且 UI 诚实说明 |
| UI02A-007 | PASS | quarantine/grader-only/unauthorized 不泄漏 |
| UI02A-008 | PASS | 三栏/单列与页面状态、live processing 完整 |
| UI02A-009 | PASS | desktop/narrow、keyboard/focus、文本等价、reduced-motion 边界验证 |
| UI02A-010 | PASS | backend/frontend/docs/diff gates 真实通过 |
| UI02A-011 | PASS | 无新生产依赖、第二 truth、跨 owner write 或 blocking SPEC GAP |
| UI02A-012 | PASS | 未把 UI/连通性宣称为学习效果 |

`EXEC016-AC-001..010` 均由上述交付、自动化测试、真实页面路径和完整工程门禁覆盖。

## 6. Verification Evidence

| Gate | 结果 |
|---|---|
| UI-02A targeted backend suite | 20 passed |
| backend full pytest | 263 passed, 1 skipped, 4 warnings |
| Ruff | PASS |
| Black hash-locked baseline gate | PASS；223 files unchanged |
| mypy | PASS；仅既有 untyped-body notes |
| Alembic check | PASS；No new upgrade operations detected |
| frontend Vitest | 10 files / 36 tests PASS |
| frontend production build | PASS |
| npm audit `--audit-level=high` | PASS；0 vulnerabilities |
| real local API/page path | PASS；真实上传、处理、map、Inspector、删除 |
| browser console / narrow overflow | 0 error / none at 390×844 |
| docs check | PASS（归档后执行） |
| `git diff --check` | PASS（提交前执行） |

真实模型不属于 UI-02A 的能力或验收条件，本次未把模型连通性作为资料库可用性证据。

## 7. SPEC GAP 与后续边界

实现阶段发现 Black hash-locked legacy baseline 同时覆盖两个本次合法修改的文件。用户于 2026-08-08 明确授权仅删除这两个已格式化文件的 baseline entry；正式 Black 门禁随后通过。该缺口已解决，未改变 CI 检查策略或业务语义。

Blocking SPEC GAP：none。

UI-02B Goals/Path/Evidence、人工 publish/review、collection/tag/note 与自动关系推断仍未获本 Slice 授权，必须经独立冻结 Spec/EXEC 才能实施。
