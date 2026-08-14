# ADR-0029 — Local and Hybrid Material Parse

Status: accepted
Date: 2026-08-13
Decision owners: user-authorized Askora product governance
Decision authority: 用户认可「无 key 用本地解析；有 key 可本地+AI 合用；设置里用开关决定是否用大模型增强解析」
Upper authority:

- `docs/product/PRODUCT-STRATEGY.md`
- `docs/product/PRODUCT-POSITIONING.md`
- `docs/product/PRODUCT-DEFINITION.md`

Product trace: Feature of `CAP-01` + `CAP-08` data-to-provider boundary；does not add/remove a Capability
Affected specs: `docs/specs/systems/01-content-knowledge.md`、`docs/specs/interfaces/content.md`、`docs/specs/systems/08-ai-orchestration.md`、`docs/specs/ui.md`、`docs/specs/interfaces/recovery-and-onboarding.md`、current Experience / Interaction
Does not amend: Conversation ≠ Evidence、LLM 非 canonical owner、OCR-as-core、Offline-only

## Context

Core Journeys 允许没有模型 key 时先上传资料。SYS01 主链已经有本地确定性解析与 `knowledge-candidate-deterministic-v1`；规格却把 schema-constrained LLM extraction 写成 MVP 必选。用户需要两种**解析**模式，而不是两种产品：

1. 仅本地算法解析上传资料；
2. 本地解析之上再用 AI 增强。

设置里用一个开关选择是否把资料发给大模型做解析。教学对话仍可能使用模型；本决策只管资料解析。

## Decision

### 1. Local parse always runs

安全扫描、格式解析、结构恢复、SourceSpan 与确定性知识点抽取 **MUST** 在本机完成，不依赖外部模型。本地解析成功后，资料可以加入空间、打开原文、写笔记，并出现 `001` / `004` 的去向选择。

### 2. AI enhancement is optional and additive

`execution_mode`：

```text
deterministic  仅本地
hybrid         本地结果 + schema-constrained LLM extraction
```

Hybrid **MUST** 叠在本地证据上。`model_inferred` 单独不得发布 hard prerequisite，也不得替换 DocumentIR。

### 3. One Settings Control

用户文案：**用 AI 增强资料解析**。

- 位置：设置，紧挨模型配置；
- 语义：Control，不是 Welcome 主按钮，也不是每次上传的必经问句；
- 无 key / 模型未就绪：开关不可用，强制 `deterministic`，原因可读；
- 有 key：默认开；用户可关；
- 打开开关 **MUST NOT** 自动把已有资料发给模型。

### 4. Explicit re-parse

模型就绪后，对仅本地解析的资料提供 Action **用模型再解析**。这是同一 Material 的增强 run，不是重传，也不是新资料。

### 5. Honest readiness

本地解析完成 ≠ 模型已读懂全书，也 ≠ 可以开始需要生成讲解/出题/反馈的对话。对话仍缺模型时必须说明缺模型、资料是否安全、现在能去设置。

AI 增强失败不得把已成功的本地解析打成整份失败。

## Alternatives Considered

### A. Block upload until a key exists

Rejected。与已冻「先放资料」和现行本地解析主链相反。

### B. Three product modes (local product / AI product / hybrid product)

Rejected。解析偏好不是新 Capability，也不能把教学策略绑进这个开关。

### C. Ask on every upload

Rejected。打断 `001`，把 Control 做成 Wizard。

### D. Flip toggle auto-sends all existing materials

Rejected。无确认外发历史资料，违反最小发送与用户控制。

## Consequences

- `SYS01-031` LLM extraction 从 MVP MUST 降为条件 MAY；
- SYS08 拥有该偏好；SYS01 读取后决定是否调用模型；
- 实现需补 hybrid extractor、「再解析」command，以及处理状态文案；
- 本开关不关闭教学、评估或 Review 对模型的使用。

## Validation

- 无 key 上传可完成本地解析并出现去向选择；
- 有 key 且开关开时 extraction run 记录 `hybrid` 与 model/provider；
- 开关关或模型未就绪时不得为解析调用外部模型；
- 打开开关不自动重跑旧资料；
- 「用模型再解析」不创建第二份 Material identity。
