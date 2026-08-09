# Askora UI-02B3 Real-model Guided Learning Completion Report

> Status：DONE
>
> 日期：2026-08-08
>
> 实现合同：`EXEC-027` / `UI02B3-AC-001..009`
>
> Decision authority：user-delegated Codex（ADR-0005）

## 1. Release 结论

```text
Engineering Gate: PASS
Policy / Ownership / Security Gate: PASS
Real Browser + Provider + PostgreSQL E2E Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
Current Local Database Activation: a80d4f9c2b61 (head)
```

UI-02B3 已把测试专用真实模型调用收敛为 production SYS08
`PolicyBoundModelRenderer`。真实 EPUB 的浏览器“开始本次学习”动作现在经过 canonical
TeachingAction、learner-visible EvidenceBundle、configured provider、tightening-only validator，
并在同一事务持久化 exact transcript、最小化 ModelInference event 与引用。

## 2. 真实端到端验收

验收对象：

```text
EPUB: 张一鸣管理日志.epub
document_id: 17a0f10d-6a0d-475f-978d-1231b3e36231
goal_id: 7f93b745-f251-5582-a312-66c90b2c64c3
activity_id: 789c37b3-7e8e-582b-9b77-bfc605b620aa
turn_kind: system_start
provider/model: zhipu / glm-4.7-flash
prompt_version: v03-policy-bound-real-render/1.0
inference_id: 19f4058e-df94-5927-8b96-df52f2df9f0f
provider_latency_ms: 22683
token_usage: 252 input / 63 output / 315 total
```

应用内浏览器从资料库进入该 EPUB，真实点击“开始本次学习”后收到非 Mock 的聚焦问题；
UI 展示 `依据资料 · 5 处`，每条均标明已连接原文位置。技术详情显示
`real_model · zhipu · glm-4.7-flash · v03-policy-bound-real-render/1.0`。
后端日志同时记录智谱 chat completion `HTTP/1.1 200 OK` 与 teaching start `200 OK`。

PostgreSQL 当前证据：

| Artifact | 当前数量 | 关键证据 |
|---|---:|---|
| accepted transcript turn | 1 | `turn_number=1`、`turn_kind=system_start`、5 条 evidence |
| corresponding `ModelInferenceCompleted` | 1 | SYS08、同一 inference id、无 raw prompt/response |
| corresponding `ActualAssistanceRecorded` | 1 | 同一 TeachingAction，SYS08 owner |

刷新页面后 reply 文本逐字符一致，5 条引用与 model metadata 均从 durable transcript 恢复。
随后使用完全相同的 user、session 与 idempotency key 重放 API，响应的 reply、inference id、
model metadata 完全相同；上述三类记录仍各为 1，且后端没有第二条 provider HTTP 请求。

## 3. 真实点击发现并修复的阻塞

首次修复后点击仍卡在模型调用之前。PostgreSQL 显示 canonical retrieval 查询把
`UserDocument.moderation_details` 与每个 `DocumentChunk` 联表返回。该 EPUB 有 1,295 个 chunks，
单份发布元数据约 3,122,197 bytes，联表重复传输量约 4,043,245,115 bytes。

EXEC-027 按治理合同追加授权后，将查询改为：

- owner/source scoped documents 读取一次；
- chunks 独立读取；
- 内存中按已授权 document id 关联；
- current revision、publication、visibility、citation 校验保持不变。

修复后同一真实请求可以完成检索、模型调用、校验与事务提交。架构回归测试禁止恢复
`select(DocumentChunk, UserDocument)` 的重复元数据联表。

## 4. Contract、错误与所有权

- 模型只生成 learner-visible text；strategy、move、modifier、assistance/exposure 和 owner refs
  仍由 SYS05/SYS02/SYS08 决定与验证。
- prompt 只包含当前 intent、target capability 与一个 learner-visible evidence item，并用
  `[不可信资料开始/结束]` 包裹；grader-only marker 的自动化测试证明不会进入 prompt。
- provider failure、empty output 与 mock model 均 fail closed；未创建 accepted transcript 或
  ModelInference event。自动化应用测试证明 provider failure 后 transcript/event 数量不变。
- `model_execution` 是 additive optional contract；旧 transcript 仍可读取。
- `ModelInferenceCompleted` 只保存 provider/model/prompt version、引用、延迟和 token usage，
  不保存完整 prompt 或完整 response。
- 无第二 TeachingAction owner、第二 tutor、legacy default path 或 mastery/review/plan 双写。

## 5. Verification Evidence

| Gate | 结果 |
|---|---|
| targeted backend UI-02B3 suite | 26 passed |
| backend full pytest | 359 passed, 2 skipped, 28 warnings |
| Ruff | PASS |
| mypy | PASS；仅既有 untyped-body notes |
| PostgreSQL migration | `a80d4f9c2b61 (head)` |
| `alembic check` | PASS；No new upgrade operations detected |
| production real-model gate | DeepSeek `deepseek-chat` PASS，2048ms |
| production UI real-model call | Zhipu `glm-4.7-flash` PASS，22683ms |
| frontend Vitest | 11 files / 45 tests PASS |
| frontend production build | PASS |
| browser reply/citation/model metadata | PASS |
| refresh exact replay | PASS |
| duplicate API / DB / provider audit | PASS |
| targeted governance/docs files | PASS；repository checker 仅剩既有未跟踪文件问题 |
| `git diff --check` | PASS |

验收期间一次额外智谱门禁调用返回 429；这次 transient failure 正确 fail closed。相同 production
renderer 随后用已配置 DeepSeek 完成真实门禁，真实 UI 智谱调用及其 PostgreSQL 证据此前已成功持久化。

仓库级 `check_docs.py` 仍报告本任务开始前已存在、未跟踪的 `docs/CODE_WIKI.md` 中
`file://` 链接、该文件 inventory 缺项，以及一个既有本地 document data inventory 缺项；
ADR-0005、UI-02B3、EXEC-027 与本 Release 文件没有新增文档门禁错误。本任务未擅自修改这两个
用途未确认的用户文件。

## 6. AC 与证据边界

`UI02B3-AC-001..009` 与 `EXEC027-AC-001..004` 均有当前代码、自动化、真实浏览器、外部 provider、
PostgreSQL、刷新和 duplicate audit 证据。Blocking SPEC GAP：none。

本 Slice 证明真实模型主链的 Engineering、Policy/Ownership 与可恢复性，不证明真人学习效果。
因此 Learning Evidence 继续为 `LEARNING_EVIDENCE_INSUFFICIENT`。
