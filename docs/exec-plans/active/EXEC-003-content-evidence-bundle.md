# EXEC-003 — Content + EvidenceBundle

> Priority：P0  
> Status：READY_AFTER_EXEC-002  
> Depends on：EXEC-001, EXEC-002

## Objective

把现有文档解析/RAG 收敛为 SYS01/SYS02 合同：PDF/Markdown 可形成稳定 SourceSpan；教学检索返回结构化 EvidenceBundle；资料引用可回原文；答案暴露受 TeachingAction 控制。

## Required Specs

- `systems/01-content-knowledge.md`
- `systems/02-retrieval.md`
- `domain/domain-model.md`
- `architecture/dependency-rules.md`
- `quality/security-standard.md`
- `vertical-slices/v0.2-learning-loop.md`

## Current Reality

主要 legacy：

```text
app/services/documents/document_service.py
app/services/documents/parsers.py
app/services/documents/rag_service.py
app/services/documents/embedding_service.py
app/services/documents/security_scanner.py
app/services/knowledge_graph/kg_service.py
app/models/document.py
app/models/knowledge.py
```

目前 `documents/` 同时承载内容与检索，需要按职责拆分，但本任务禁止大爆炸重命名全部文件。

## Allowed Files

上述 legacy 路径，以及：

```text
app/domains/content_knowledge/**
app/domains/retrieval/**
app/contracts/**
app/infrastructure/**
tests/**document**
tests/**rag**
tests/**retrieval**
tests/**citation**
tests/**security**
```

## Forbidden Changes

- 不引入独立图数据库作为 truth；
- 不默认所有请求 GraphRAG；
- 不让 RAG 自己选 TeachingAction；
- 不修改 mastery；
- 不用模型常识补造“来自资料”的事实。

## Implementation Tasks

### T1 — Revision + SourceSpan

PDF/Markdown 导入形成：checksum、MaterialRevision、parser version、稳定 SourceSpan anchor。

### T2 — SourceChunk Projection

从 SourceSpan 派生可重建 SourceChunk；segmentation version/index version 可追踪。

### T3 — Minimal Knowledge Binding

首条切片只建立足以把 KnowledgeUnit 与 SourceSpan/Chunk 关联的最小 canonical 模型，不要求完整大型图谱。

### T4 — Retrieval Contract

建立 `BuildEvidenceBundle`：TeachingAction/evidence requirements + source scope + exposure → structured EvidenceBundle。

### T5 — Hybrid Baseline

优先复用现有能力，实现/确认 lexical + dense → RRF → policy filter → optional rerank → dedup/compression。

### T6 — Citation Validation

所有 learner-visible materials claim 的 citation 至少能定位 document revision + SourceSpan。

### T7 — Exposure

实现 L0-L4/allowed_use filter。grader-only reference 与 learner-visible 严格隔离。

### T8 — Failure

missing evidence、invalid anchor、stale index、embedding/reranker failure 使用结构化 error/signal；允许 lexical-only 等安全降级。

### T9 — Security

恶意文档指令不能改变 retrieval policy、TeachingAction 或 tool permissions；quarantined 文档不得进索引。

## Acceptance Criteria

- `EXEC003-AC-001`：`SYS01-AC-001/002/005/006` 通过。
- `EXEC003-AC-002`：`SYS02-AC-001/002/004/005/006` 通过。
- `EXEC003-AC-003`：上传 PDF/Markdown 后 citation 可回放原文。
- `EXEC003-AC-004`：index 可删除后由 canonical records 重建。
- `EXEC003-AC-005`：无提示 assessment 请求不能取得 L4 learner-visible evidence。
- `EXEC003-AC-006`：embedding/reranker 故障可安全降级，missing evidence 不伪造。

## Required Tests

```bash
cd apps/backend
pytest tests -k "document or rag or retrieval or citation or injection"
pytest
ruff check app tests
mypy app
```

新增固定 malicious-document fixture 和 citation replay fixture。

## Completion Report

额外报告：

- canonical content truth 的具体存储；
- 哪些 index 是 projection；
- current `rag_service.py` 还剩哪些 legacy 跨界职责。
