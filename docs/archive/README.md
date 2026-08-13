# Askora 文档归档

> 状态：ARCHIVE — 历史证据，不再作为 current truth
> 归档原则：所有历史文档以 `git mv` 归档（保留 git 历史），内容不修改、链接不强制维护

## 目录

| 路径 | 内容 |
|---|---|
| `adr/` | 26 个 ADR 原文（immutable 决策记录；当前有效结论见 [`../decisions/DECISIONS.md`](../decisions/DECISIONS.md)） |
| `design/` | 历史设计基线与 Delta（Learning Core 设计稿、UX/交互 Delta、features Delta 等） |
| `specs/` | 合并前的碎片规范与历史 vertical-slices（`systems/`、`interfaces/`、`ui/`、`vertical-slices/` 等） |

## 规则

1. 归档文件不被 `check_docs.py` 校验链接（历史快照）；
2. 读取历史文档仅用于回答"为什么这样变化"或迁移溯源，不得覆盖 current truth；
3. 归档路径不改变文档当时的内容与声明。
