# P1-07 Error Recovery Center Vertical Slice

> Status: FROZEN
> Implementation entry: EXEC-037
> Frozen date: 2026-08-09
> User authorization: 采纳推荐方案并要求真正关闭 P1-07
> Architecture decision: ADR-0012

## 1. Objective

让私人本地用户从统一入口理解并恢复 provider、资料、任务、数据库和启动故障，同时保证重试
不重复副作用、失败不污染学习证据、敏感诊断不泄漏。

## 2. End-to-end paths

```text
runtime failure
→ stable ERROR-002 envelope / owner state
→ global issue indicator
→ /settings/recovery
→ server-allowed owner action
→ idempotent audited result
→ owner state re-query
```

```text
backend startup failure
→ Electron BootstrapDiagnosticV1
→ startup recovery shell
→ single-flight retry
→ /ready success
→ normal protected App
```

## 3. In scope

- complete error envelope and stable catalog；
- provider timeout/rate/key/model/output failure classification；
- failed/quarantined/missing-file/OCR-review document issue projection；
- outbox waiting/exhausted/handler-unavailable projection and allowlisted recovery；
- migration/database/bootstrap diagnostics；
- Recovery Center page, Settings station and global indicator；
- retry budget/wait/result/audit/idempotency；
- negative learning-evidence firewall；
- desktop/360px/200%/keyboard/screen reader and restart E2E。

## 4. Out of scope

- Recovery Center 直接修复数据库、编辑文件、改模型密钥或 patch owner ORM；
- 未知/非幂等 task 的 generic replay；
- 自动解除 quarantine 或发布低置信 OCR；
- 把 resolved 当作资料正确、学习完成或 mastered；
- 云端监控、多人运维后台或远程支持上传。

## 5. Product semantics

- 每张问题卡固定显示“发生了什么 / 数据是否安全 / 现在能做什么 / 重试说明”；
- blocking first，其次 waiting/warning；同 resource/code 合并为一个 versioned issue；
- command 执行中禁用重复点击，刷新后按同 idempotency result 恢复；
- rate limit 显示服务端 next eligible time，Key 无效只导航到模型设置；
- quarantined 只在新策略存在时允许复检；OCR 候选只导航人工复核；
- file missing 不承诺自动找回；只有 SYS01 已实现替换 command 才提供重新选择，否则只提供真实
  数据恢复入口；provider issue 可返回关联的 canonical activity，但导航本身不重放调用；
- 没有问题时显示最近一次检查时间，不制造“系统绝对安全”的承诺；
- 技术详情折叠展示 code/correlation/ref，不显示 stack/path/secret。

## 6. Dependencies and integration gate

- P0 UI-02C 提供 activity 恢复入口，但 P1-07 本身不得等待 activity 才实现错误合同；
- P1-02/P1-03/P1-04 owner capability 若合并较晚，Recovery Center 先使用稳定 navigate/action code，
  最终 DONE gate 必须以对应真实 owner command 替换任何 unavailable placeholder；
- durable transcript/policy-bound model baseline 必须合入后再完成 provider/transcript E2E；
- 不允许通过 mock-only 或 disabled button 宣称上述依赖已闭合。

## 7. Acceptance criteria

- `P107-AC-001`：RECOVERY-AC-001..007 全部满足；
- `P107-AC-002`：provider 六类错误均有稳定 code/action/budget，且 accepted transcript、Attempt、
  mastery/review/activity 不产生错误副作用；
- `P107-AC-003`：document failed/quarantined/missing/OCR、outbox waiting/DLQ 都能从 owner facts 呈现；
- `P107-AC-004`：所有 command current-user scoped、versioned、幂等、bounded、audited；
- `P107-AC-005`：migration/database/backend unavailable 不依赖 API 也能显示和 single-flight retry；
- `P107-AC-006`：刷新、重登、App 重启后 issue/result 一致，不重复 task/run/transition；
- `P107-AC-007`：真实浏览器覆盖至少 provider failure recovery、document recovery、bootstrap recovery；
- `P107-AC-008`：360px、200% zoom、keyboard/focus/live region 通过；
- `P107-AC-009`：Engineering、Policy/Ownership、Security/Privacy PASS；Learning Evidence 保持
  `LEARNING_EVIDENCE_INSUFFICIENT`。

## 8. Completion rule

只有全量门禁、真实桌面/浏览器路径和依赖 owner actions 都有当前证据时才能将 P1-07 标为 DONE。
单有错误页面、API tests、mock provider 或可点击但无后端 command 的按钮均不算完成。
