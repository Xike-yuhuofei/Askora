# P1-03 Data Control and Recovery Vertical Slice

> 状态：FROZEN  
> 冻结日期：2026-08-09  
> Product Traceability：`CAP-08`；`PD-REQ-0802..0804`；`PD-RULE-008/010/011`；`PD-NFR-001/002/004`  
> Governing：`PRODUCT-DEFINITION.md`、ADR-0103  
> Primary contract：`interfaces/data-control-contract.md`

## 0. Acceptance Ownership

本 Slice 把 `CAP-08 Local Data & AI Control` 中的数据控制部分转化为 backup / restore / export / erasure 的技术与 UX 闭环。

- 本文件 `IN / OUT` 只表示 P1-03 implementation-slice scope，不定义 Askora v1 总体 Product Scope；
- `P103-AC-*` 属于 **Technical / Data-Control / UX Vertical Slice Acceptance**，不自动成为 `PD-AC-*`；
- Product Requirement 与 Product Acceptance 由 `PRODUCT-DEFINITION.md` 或明确 Product Feature Spec 拥有；
- 本文件 2026-08-09 冻结时的 macOS Desktop / Electron / PostgreSQL compatibility mechanics 作为历史技术合同保留；其是否仍属于 current normal-v1 path 必须服从 Product Positioning / Product Definition / current supersession，不能反向定义 v1 Product Shape；
- Engineering / recovery PASS 不自动证明整个 `CAP-08` 已 Product Accepted。

## 1. Objective

在 macOS 私人桌面 SQLite 模式交付可真实使用的数据保护闭环：自动/手动加密备份、可验证离线恢复、migration 前保护、可读导出、按范围删除和防旧恢复点复活。

> Current-v1 interpretation：上述句子保留本 Slice 冻结时的实现语境；当前 v1 Product Shape 为 Local Web，本句不得被解释为 native desktop 是产品前置条件。

## 2. End-to-End Paths

```text
Settings → 初始化 Recovery Key → 手动/自动 backup → reopen verify → VERIFIED
Settings → 选择 recovery point → staging verify/migrate/reconcile → atomic activate → re-login
Settings → 选择 export scope → current-user allowlist package → native save
Settings → erasure preview → explicit confirm → owner workflow → post-erasure baseline/report
App upgrade → PRE_MIGRATION verified → staging migration → activate or unchanged rollback
```

> Supersession note：`re-login` / native-save host mechanics 属于冻结时 implementation wording；Account/Login 产品语义已由 current no-auth authority supersede。保留该文本用于历史技术追溯，不授予新的 Product Scope。

## 3. IN

本节只定义 P1-03 implementation scope：

- Recovery Key/device secure storage bridge；
- encrypted chunked container、manifest、limits、catalog、retention；
- SQLite/documents/KEK consistent offline backup；
- verify、staging restore、forward migration、atomic activation、rescue rollback；
- current-user export allowlist；
- DOCUMENT/LEARNING_RECORDS/MODEL_EXECUTION/ALL_PERSONAL_DATA erase workflow；
- erasure checkpoint、managed restore-point invalidation、post-erasure baseline；
- Settings UI、typed IPC/API、stable errors/reports；
- L0～L5、SQLite/PostgreSQL unsupported contract、frontend/Electron/browser validation。

## 4. OUT

本节 OUT 只约束本 Slice，不等于 Askora 总体 Non-goal：

- PostgreSQL/Docker managed backup implementation；
- cloud sync/off-device automatic upload；
- provider API key backup（P1-02）；
- account password recovery/identity UX（P1-05，调用 ALL_PERSONAL_DATA）；
- arbitrary import of readable user export；
- guarantee for historical packages copied outside Askora managed catalog。

其中 cloud sync / Account 等总体产品边界仍由 Product Positioning / Product Definition 拥有；历史 P1-02/P1-05 引用不恢复其 superseded 产品语义。

## 5. Historical Execution Order

以下保留为历史实施分解，不维护实时工作状态：

1. EXEC-1031：recovery key、backup/container/catalog/retention/pre-migration guard；
2. EXEC-1032：verify/staging restore/migration/reconciliation/rollback；
3. EXEC-1033：current-user readable export；
4. EXEC-1034：owner erasure、checkpoint、Settings/Electron complete UX、full release gate。

原执行约束“每个 EXEC 独立本地 commit；未经用户明确要求不 push；不得混入其他工作区改动”保留为当时 execution evidence 语境，不作为当前实时工作管理规则。当前状态、依赖与执行方式以 Linear / current `main` 为准。

## 6. Technical / Data-Control Acceptance Criteria

以下 AC 不创建新的 Product Acceptance：

- `P103-AC-001`：`DATA-AC-001..010` 全部满足。
- `P103-AC-002`：真实用户数据目录的等价 fixture 完成 backup→mutate→restore，DB/文件/KEK/owner refs 一致。
- `P103-AC-003`：migration failure、wrong key、tamper、missing file、future schema 均在 active data 变化前 fail closed。
- `P103-AC-004`：四类导出/删除 current-user、secret-safe、幂等；删除后 managed restore/rebuild 不复活。
- `P103-AC-005`：设置页不混淆导出、资料删除、学习记录删除和全部个人数据删除（Askora 无登录/退出登录，账号级操作不存在）。
- `P103-AC-006`：Engineering 与 Policy/Ownership Gate PASS；Learning Evidence 保持 `LEARNING_EVIDENCE_INSUFFICIENT`。

`CAP-08 / PD-REQ-0802..0804` 的 Product Acceptance 必须单独根据用户可观察行为与 current Product AC 判断。

## 7. Done Gate

历史 P1-03 technical closure 只有在四个 EXEC 对应实现证据、release evidence 与适用测试/恢复安全合同成立时才可称 Engineering DONE。

如果进一步声称 current v1 Data Control 产品能力已完成，还必须核对 applicable Product Acceptance；历史 Desktop evidence、旧 Gap Register 或 EXEC completion 不能替代 current-main Product conformance。
