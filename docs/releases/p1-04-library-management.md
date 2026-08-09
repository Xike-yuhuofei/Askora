# P1-04 Library Management Completion Report

> Date: 2026-08-09
> Scope: EXEC-031～033
> Governing: ADR-0008, SYS01 Library Management Spec, P1-04A/B/C Vertical Slices

## 1. Final gate

```text
Engineering Gate: PASS
Contract / Ownership / Security Gate: PASS
Real Browser + Local OCR Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

P1-04 已关闭。该结论只证明资料管理工程闭环与 owner/security 合同成立，不证明真人学习效果得到改善。

## 2. Delivered behavior

- current-user 标题与 current-revision 正文搜索，稳定排序、范围化摘录与 SourceSpan 引用；
- versioned 元数据编辑、标签、集合、标签/集合筛选与最多 100 项的显式批量整理；
- archive/restore 只改变资料可见性，raw 文件、旧 revision 与审计事实不删除；
- exact、near-content、revision-chain 三类 versioned 重复建议；只有用户显式 resolution 才改变状态，禁止自动 canonical merge；
- local Tesseract durable OCR request/worker/candidate/review/publish；候选携带 page、bbox、image hash、confidence 与 engine/version；
- 未接受 OCR 候选不进入普通 search/retrieval/knowledge map；接受后发布新的可追溯 revision，失败时旧 revision 保持可用；
- Library UI 覆盖搜索、筛选、元数据、标签/集合、批量归档恢复、重复复核和逐页 OCR 对照复核，并保持移动端可用。

## 3. Acceptance evidence

| Slice | Evidence | Result |
|---|---|---|
| P1-04A | current-user query、metadata optimistic concurrency、idempotent labels、batch cap、archive/restore、private no-store、真实浏览器 search/edit/tag/collection/batch/restore | PASS |
| P1-04B | 三类 versioned fingerprints、stable pair/policy idempotency、跨用户不可枚举、显式 keep/archive、无 KnowledgeUnit/mastery 自动合并 | PASS |
| P1-04C | durable outbox/restart、unavailable/timeout/invalid-output fail closed、candidate isolation、人工 accept/edit/reject、new revision 与 search projection | PASS |

真实本地 OCR 证据：Tesseract 5.5.1 对 1 页扫描 PDF 识别出 `THERMODYNAMICS HEAT TRANSFER`；隔离 PostgreSQL 浏览器流程在人工改为 `THERMODYNAMICS HEAT TRANSFER VERIFIED` 并发布前搜索为 0，发布后唯一命中该 PDF。

真实浏览器隔离验收还覆盖：元数据保存、标签/集合创建、两份资料批量分类、exact duplicate 显式归档、归档视图恢复、正文命中摘录、标签/集合筛选、OCR 原页预览与候选置信度、390×844 无横向溢出；浏览器 console warning/error 为 0。隔离临时数据库已删除，临时文件已移入 macOS 废纸篓；现有私人资料未被修改。

## 4. Automated gates

```text
Backend targeted P1-04 + migration tests: PASS
Backend full suite: 379 passed, 3 skipped
Backend ruff: PASS
Backend mypy app: PASS (167 source files)
Alembic heads: d2f0410a33c3 (single head)
Fresh PostgreSQL upgrade / downgrade-to-e30 / re-upgrade: PASS
Alembic check on fresh head: PASS
Frontend tests: 57 passed
Frontend production build: PASS
```

后端全量在并行的 EXEC-030 收口后重新运行，结果为 `379 passed, 3 skipped`，无失败。文档检查器仍报告未跟踪 `docs/CODE_WIKI.md` 的 `file://` 链接和既有私人 storage 文件未登记；P1-04 的 active/completed 链接与发布索引已通过人工核对，本轮未擅自修改这两项任务外文件。

## 5. Ownership and safety conclusion

- SYS01 继续唯一拥有资料元数据、projection、duplicate suggestion 和 OCR candidate/revision 发布；
- OCR 与 duplicate 不写 LearnerState、AssessmentResult、TeachingAction、LearningPlan、ReviewSchedule 或 SYS08 transcript；
- current-user scope、raw preservation、grader-only exclusion、no silent merge、no unreviewed OCR publish 均有自动化回归；
- 未引入外部 OCR 服务或新的网络数据流，Tesseract 使用固定参数与 page/DPI/time/output 上限。

## 6. Repository note

实现所在工作区曾与 EXEC-030/P1-05 改动并行。EXEC-030 已先独立收口；P1-04 只暂存其
精确治理、实现、测试与发布证据，P1-05、CI/Docker 和 Goal 映射改动继续保持未暂存。
P1-04A/B/C 因共用同一 SYS01 service/model/UI 合同，以一个本地依赖基线提交收口；后续
P1-01A/B 仍按各自 Slice 独立提交。
