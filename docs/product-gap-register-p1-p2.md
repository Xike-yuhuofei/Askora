# Askora P1 / P2 产品缺口清单 — Historical Snapshot

> 状态：**HISTORICAL-RETAIN / NOT CURRENT WORK TRUTH**  
> 原快照校准日期：2026-08-09  
> 退役为实时 tracker：2026-08-11  
> 原始完整快照：Git history at/before `adc64f1ed820974387f5d5adeabb75e2a2fd37e0`

本文件曾用于维护 Askora P1 / P2 产品缺口、状态与实施进展。

从 2026-08-11 起，它**不再承担实时 backlog / status 管理职责**。

原因：

1. Askora 已正式使用 Linear 作为工作管理事实源；
2. 静态 Markdown gap register 与 Linear / current `main` 容易产生状态漂移；
3. 本文件已经包含 Desktop、OCR、Account 等被后续 Product Positioning supersede 的历史状态；
4. “已经实现什么”必须重新读取 current `main`、Specs、tests 和 Linear，而不能从旧快照推断。

## Current Sources of Truth

### Product Strategy / Boundary

- [`product/PRODUCT-STRATEGY.md`](product/PRODUCT-STRATEGY.md)
- [`product/PRODUCT-POSITIONING.md`](product/PRODUCT-POSITIONING.md)

### Current Work Status

使用 Linear：

```text
Initiative: Askora
→ workflow-specific Project
→ Milestone / Issue / dependency / status
```

不同工作流应进入对应 Project，例如：

- Askora — Product Strategy & Discovery；
- Askora — UI Redesign；
- Askora — Quality；
- 其他 Architecture / Learning Core 独立工作流。

### Current Implementation Reality

使用：

```text
current GitHub main
+ current Canonical Design / ADR / Specs
+ executable tests / CI
```

## Historical Use

如果需要研究 2026-08-09 当时的 P1 / P2 product-gap 判断，应读取该时间点 Git history，而不是把本文件当前页面解释为实时状态。

历史内容可以用于：

- 理解过去为什么创建某项工作；
- 查看曾经存在的产品缺口；
- 追踪被 supersede 的 Desktop / Account / OCR 等产品路径；
- 审计产品演进。

历史内容不得用于：

- 判断当前 Issue 是否 OPEN / DONE；
- 判断 current `main` 是否仍有相同 gap；
- 覆盖当前 Product Strategy / Positioning；
- 创建重复 Linear Issue；
- 反向恢复已 supersede 的产品语义。

## Governance Rule

新的产品缺口按以下方式处理：

```text
Observed problem / evidence
→ Product Strategy / Positioning check
→ Linear Project / Issue for current work
→ GitHub Canonical Design / ADR / Spec when long-term decision is needed
→ implementation / verification
```

不再恢复本 Markdown 文件作为第二套实时 backlog。
