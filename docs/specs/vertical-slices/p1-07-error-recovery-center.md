# P1-07 Error Recovery Center Vertical Slice

> Status: FROZEN  
> Product Traceability: `CAP-07`、`CAP-08`；`PD-REQ-0701`、`PD-REQ-0802`；`PD-RULE-010/011`；`PD-NFR-001/003/004/005`  
> Frozen date: 2026-08-09  
> Governing: `PRODUCT-DEFINITION.md`、ADR-0012、current recovery/error/security contracts  
> Historical implementation entry: EXEC-037；实时状态以 Linear 与 current `main` 为准

## 0. Acceptance Ownership

本 Slice 冻结“用户理解并恢复产品故障”的 recovery UX / technical control plane；它不拥有新的 Product Scope。

- `In scope / Out of scope` 只表示 P1-07 implementation-slice scope；
- `P107-AC-*` 属于 **Technical / Recovery / UX Vertical Slice Acceptance**，不自动成为 `PD-AC-*`；
- “系统故障不得伪造成 learner failure / mastery change”等产品语义来自 `PD-RULE-010`；
- 本文件冻结时包含 OCR review、Electron bootstrap 等具体 adapter mechanics；这些技术合同保留，但其 current-v1 可达性 / 产品暴露必须服从 Product Definition、current supersession 与对应 Specs，不能因本 Slice 存在而自动成为 Product Requirement；
- Recovery Engineering PASS 不自动证明 `CAP-07` 或 `CAP-08` 已完整 Product Accepted。

## 1. Objective

让私人本地用户从统一入口理解并恢复 provider、资料、任务、数据库和启动故障，同时保证重试不重复副作用、失败不污染学习证据、敏感诊断不泄漏。

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

> Current-v1 interpretation：第二条路径保留本 Slice 冻结时的 Desktop/Electron implementation contract。当前 Local Web / no-auth Product Shape 由上游 Product docs 决定；不得据此恢复 native Desktop 或 Auth shell 的产品前置条件。

## 3. In scope

本节只定义 P1-07 implementation scope：

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

本节 OUT 只约束本 Slice，不等于 Askora 总体 Non-goal：

- Recovery Center 直接修复数据库、编辑文件、改模型密钥或 patch owner ORM；
- 未知/非幂等 task 的 generic replay；
- 自动解除 quarantine 或发布低置信 OCR；
- 把 resolved 当作资料正确、学习完成或 mastered；
- 云端监控、多人运维后台或远程支持上传。

## 5. Product-facing Recovery Semantics

以下保留本 Slice 冻结的 recovery UX / safety contract。它们是对上游 Product Rules 的具体化，不成为第二份 Product Definition：

- 每张问题卡固定显示“发生了什么 / 数据是否安全 / 现在能做什么 / 重试说明”；
- blocking first，其次 waiting/warning；同 resource/code 合并为一个 versioned issue；
- command 执行中禁用重复点击，刷新后按同 idempotency result 恢复；
- rate limit 显示服务端 next eligible time，Key 无效只导航到模型设置；
- quarantined 只在新策略存在时允许复检；OCR 候选只导航人工复核；
- OCR 恢复导航必须打开同 owner、同 document/run 的真实复核区，并显示本机渲染原页；为该预览生成的 `blob:` 只允许进入 CSP `img-src`，不得放宽 script/object/connect 等执行或网络边界；
- file missing 不承诺自动找回；只有 SYS01 已实现替换 command 才提供重新选择，否则只提供真实数据恢复入口；provider issue 可返回关联的 canonical activity，但导航本身不重放调用；
- 没有问题时显示最近一次检查时间，不制造“系统绝对安全”的承诺；
- 技术详情折叠展示 code/correlation/ref，不显示 stack/path/secret。

> Supersession note：OCR-specific recovery mechanics 的保留用于技术追溯；当前 Product Definition 已将 full OCR 排除在 core v1，UI normal-path exposure 也有更晚的 no-OCR contract。后续实现不得为了满足本历史 Slice 而恢复已 supersede 的正常 UI 暴露。

## 6. Dependencies and integration gate

- P0 UI-02C 提供 activity 恢复入口，但 P1-07 本身不得等待 activity 才实现错误合同；
- P1-02/P1-03/P1-04 owner capability 若合并较晚，Recovery Center 先使用稳定 navigate/action code，最终 DONE gate 必须以对应真实 owner command 替换任何 unavailable placeholder；
- durable transcript/policy-bound model baseline 必须合入后再完成 provider/transcript E2E；
- 不允许通过 mock-only 或 disabled button 宣称上述依赖已闭合。

以上 dependency 描述保留其技术关系；当前 completion/status 必须重新读取 Linear、current `main` 与 current owner contracts，不能从历史项目编号推断实时状态。

## 7. Technical / Recovery / UX Acceptance Criteria

以下 AC 不创建新的 Product Acceptance：

- `P107-AC-001`：RECOVERY-AC-001..007 全部满足；
- `P107-AC-002`：provider 六类错误均有稳定 code/action/budget，且 accepted transcript、Attempt、mastery/review/activity 不产生错误副作用；
- `P107-AC-003`：document failed/quarantined/missing/OCR、outbox waiting/DLQ 都能从 owner facts 呈现；
- `P107-AC-004`：所有 command current-user scoped、versioned、幂等、bounded、audited；
- `P107-AC-005`：migration/database/backend unavailable 不依赖 API 也能显示和 single-flight retry；
- `P107-AC-006`：刷新、重登、App 重启后 issue/result 一致，不重复 task/run/transition；
- `P107-AC-007`：真实浏览器覆盖至少 provider failure recovery、document recovery、bootstrap recovery；OCR recovery 必须验证原页图像成功解码，不得只断言 `<img>` 或候选文字存在；
- `P107-AC-008`：360px、200% zoom、keyboard/focus/live region 通过；
- `P107-AC-009`：Engineering、Policy/Ownership、Security/Privacy PASS；Learning Evidence 保持 `LEARNING_EVIDENCE_INSUFFICIENT`。

若某条 AC 依赖已经被更高权威 supersede 的 Product/UI path，应按 current supersession 解释，不得为了让历史 AC 继续字面可达而恢复旧 Product Scope。对应 Product Acceptance 必须单独核对 applicable `CAP-07 / CAP-08 / PD-REQ-*`。

## 8. Completion rule

只有全量 applicable technical gates、真实运行路径和依赖 owner actions 都有 current evidence 时才能将 P1-07 technical contract 标为 DONE。

单有错误页面、API tests、mock provider 或可点击但无后端 command 的按钮均不算完成。若进一步声称 current v1 recovery 产品能力已完成，还必须单独核对 Product Acceptance；历史 Desktop/OCR evidence 不能替代 current Product conformance。
