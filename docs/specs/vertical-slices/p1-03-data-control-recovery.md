# P1-03 Data Control and Recovery Vertical Slice

> 状态：FROZEN / READY_AFTER_GOVERNANCE
> 冻结日期：2026-08-09
> 用户授权：最终真正关闭 P1-03 并通过相关测试
> Governing decision：ADR-0103
> Primary contract：`interfaces/data-control-contract.md`

## 1. Objective

在 macOS 私人桌面 SQLite 模式交付可真实使用的数据保护闭环：自动/手动加密备份、可验证离线恢复、migration 前保护、可读导出、按范围删除和防旧恢复点复活。

## 2. End-to-End Paths

```text
Settings → 初始化 Recovery Key → 手动/自动 backup → reopen verify → VERIFIED
Settings → 选择 recovery point → staging verify/migrate/reconcile → atomic activate → re-login
Settings → 选择 export scope → current-user allowlist package → native save
Settings → erasure preview → explicit confirm → owner workflow → post-erasure baseline/report
App upgrade → PRE_MIGRATION verified → staging migration → activate or unchanged rollback
```

## 3. IN

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

- PostgreSQL/Docker managed backup implementation；
- cloud sync/off-device automatic upload；
- provider API key backup（P1-02）；
- account password recovery/identity UX（P1-05，调用 ALL_PERSONAL_DATA）；
- arbitrary import of readable user export；
- guarantee for historical packages copied outside Askora managed catalog。

## 5. Execution Order

1. EXEC-1031：recovery key、backup/container/catalog/retention/pre-migration guard；
2. EXEC-1032：verify/staging restore/migration/reconciliation/rollback；
3. EXEC-1033：current-user readable export；
4. EXEC-1034：owner erasure、checkpoint、Settings/Electron complete UX、full release gate。

每个 EXEC 独立本地 commit；未经用户明确要求不 push。当前工作区既有 Book Learning/real-model 未提交改动不得被纳入 P1-03 commit。

## 6. Acceptance Criteria

- `P103-AC-001`：`DATA-AC-001..010` 全部满足。
- `P103-AC-002`：真实用户数据目录的等价 fixture 完成 backup→mutate→restore，DB/文件/KEK/owner refs 一致。
- `P103-AC-003`：migration failure、wrong key、tamper、missing file、future schema 均在 active data 变化前 fail closed。
- `P103-AC-004`：四类导出/删除 current-user、secret-safe、幂等；删除后 managed restore/rebuild 不复活。
- `P103-AC-005`：设置页不混淆导出、资料删除、学习记录删除和全部个人数据删除（Askora 无登录/退出登录，账号级操作不存在）。
- `P103-AC-006`：Engineering 与 Policy/Ownership Gate PASS；Learning Evidence 保持 `LEARNING_EVIDENCE_INSUFFICIENT`。

## 7. Done Gate

只有四个 EXEC 全部归档、release evidence 含当前测试/桌面验收、根 README 不再声称桌面无自动备份、产品缺口 P1-03 的每条完成标准都有证据时，P1-03 才可标记 `DONE`。
