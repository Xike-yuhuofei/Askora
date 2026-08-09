# Askora P1-03 Data Control and Recovery Completion Report

> Status：DONE
> 日期：2026-08-09
> 实现合同：ADR-0103 / DATA-001..081 / EXEC-1031～1034
> Implementation commits：`23e2c51`、`cfed3e6`、`4588543`、`d0cff3a`

## 1. Release 结论

```text
Engineering Gate: PASS
Policy / Ownership / Security Gate: PASS
Desktop Recovery E2E Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

P1-03 已交付 macOS 私人桌面 SQLite 的加密恢复点、完整重开校验、离线分阶段恢复、current-user 可读导出、owner-coordinated 四范围永久删除及删除后 no-resurrection 防线。Data Control 只协调各 owner 和恢复制品，不成为第九业务 truth。

本 Release 证明工程、合同、ownership、安全和真实桌面恢复流程满足冻结标准，不证明功能改善真人学习效果。

## 2. 交付边界

- Recovery Key 与平台 KEK 分离；恢复包使用 versioned manifest、chunked AEAD、路径/大小/文件数限制和私有权限，排除 provider key、JWT、日志、缓存与 `.env`。
- 桌面按 24 小时策略创建 `SCHEDULED` verified point；支持 `MANUAL`、`PRE_MIGRATION`、`PRE_RESTORE`、`POST_ERASURE`，并执行保留策略与可选外部副本。
- Restore 先完整验证，再进入 private staging、schema compatibility/forward migration、owner/checkpoint reconciliation 和 journaled atomic activation；失败保留或恢复 rescue dataset。
- Export 使用显式 allowlist、current-user scope、15 分钟一次性下载和可选资料原件；导出 ZIP 明确不可用于数据库恢复。
- Erasure 覆盖 `DOCUMENT`、`LEARNING_RECORDS`、`MODEL_EXECUTION`、`ALL_PERSONAL_DATA`，要求 expiring preview/token、精确短语、幂等 key、owner receipts、checkpoint 和 VERIFIED `POST_ERASURE` 基线；pending/partial 状态 fail closed。
- Managed old backup、event replay 和 projection rebuild 均受 erasure checkpoint/barrier 约束，不得复活已删除事实。

## 3. Acceptance Criteria Matrix

| AC | 结果 | 证据摘要 |
|---|---|---|
| DATA-AC-001 | PASS | App 可创建 VERIFIED 加密恢复点并显示保护状态、时间和范围边界 |
| DATA-AC-002 | PASS | wrong key/tamper/truncate/path/limit 在 active data 变化前拒绝 |
| DATA-AC-003 | PASS | staging、schema/file/owner/checkpoint reconciliation 与 rescue rollback tests |
| DATA-AC-004 | PASS | destructive migration 缺少 VERIFIED `PRE_MIGRATION` 时 fail closed |
| DATA-AC-005 | PASS | current-user allowlist export，secret/internal/grader/other-user leakage 为 0 |
| DATA-AC-006 | PASS | 四范围 preview/confirm/idempotency/report；partial 不显示完成 |
| DATA-AC-007 | PASS | managed old backup、replay、projection rebuild no-resurrection tests |
| DATA-AC-008 | PASS | registry/coverage 与 architecture tests 阻止跨 owner direct patch |
| DATA-AC-009 | PASS | Settings 覆盖保护、导出、删除、partial/error/success 与 live status |
| DATA-AC-010 | PASS | 真实打包 Electron backup→mutate→restore 与 typed maintenance bridge |
| P103-AC-001..006 | PASS | 四 EXEC、release evidence、README、secret-safe/ownership/learning boundary 全部收口 |

## 4. Verification Evidence

| Gate | 当前结果 |
|---|---|
| P1-03 backend targeted suite | 38 passed；12 个 Alembic legacy config deprecation warnings |
| Erasure-focused suite | 15 passed |
| backend full pytest | 378 passed，2 skipped，16 个既有 deprecation warnings |
| Ruff `app tests` | PASS |
| mypy `app` | PASS；168 source files，仅既有 untyped-body notes |
| Black repository baseline | PASS；300 files unchanged |
| frontend Vitest | 15 files / 59 tests PASS；含四范围 UI preview 与 packaged startup serialization regression |
| frontend production build / Node syntax | PASS |
| npm audit high | PASS；0 vulnerabilities |
| packaged macOS arm64 build | PASS；App、DMG、ZIP 生成；本地签名身份不可用，因此产物未签名 |
| packaged desktop E2E | PASS；verified backup→新增会话→offline restore→清除本地 session |
| restored data query | PASS；新增会话 `b26cc690-c70f-42f2-9523-b2c162ab9944` 恢复后 count=0 |
| recovery report/catalog | PASS；report `COMPLETED`，自动生成 VERIFIED `PRE_RESTORE` rescue point |
| private permissions | PASS；data root `0700`，local secrets/recovery key `0600` |
| `git diff --check` | PASS |

首次 PR CI 暴露两个合并门禁债务：知识发布事件未复用已冻结的 deterministic legacy user identity adapter，以及 3 个工作区文件未满足 Black。最终合并门禁提交复用 `canonical_user_id()` 并只执行机械格式化；全仓 pytest、Ruff、mypy 和 Black repository baseline 随后全部通过，没有扩大 ignore 或建立第二 identity truth。

## 5. 真实桌面验收

在隔离临时用户数据目录启动实际打包 `Askora.app`，注册合成私人账号并执行：

```text
Settings 创建 VERIFIED 恢复点
→ Today 创建备份后学习会话
→ Settings 选择该恢复点并执行离线恢复
→ backend stop / staging verify / PRE_RESTORE rescue / atomic activation / restart
→ App 清除本地认证缓存并回到登录页
→ SQLite 只读查询确认备份后会话不存在
```

验收过程中发现 macOS `activate` 会在首个异步 maintenance 尚未完成时重复进入 `createWindow()`，导致多个 maintenance/backend 进程。实现增加单一 `windowCreationPromise` 并补回归测试；重新打包后仅保留一个 Electron main 和预期单一 backend 实例，真实恢复随后通过。

## 6. SPEC GAP 与后续边界

Blocking SPEC GAP：none。

代码签名/公证与自动更新属于 P2-06/P2-07，不属于 P1-03 私人本地数据可靠性合同；当前未签名产物不影响本次本机功能验收，但不得作为公开分发就绪证据。P1-05 账号生命周期可复用本次 erasure foundation，但必须继续由独立 Identity/Privacy 合同治理，不能让 Data Control 接管 credential owner。
