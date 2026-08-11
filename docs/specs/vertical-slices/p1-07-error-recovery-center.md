# P1-07 Error Recovery Center Vertical Slice

> Status: FROZEN  
> Product Traceability: `CAP-07`、`CAP-08`；`PD-REQ-0701`、`PD-REQ-0802`；`PD-RULE-010/011`；`PD-NFR-001/003/004/005`  
> Frozen date: 2026-08-09  
> Governing: `PRODUCT-DEFINITION.md`、ADR-0012、current recovery/error/security contracts  
> Historical implementation entry: EXEC-037；实时状态以 Linear 与 current `main` 为准

## 0. Acceptance Ownership

本 Slice 冻结“用户理解并恢复本地产品故障”的 recovery UX / technical control plane；它不拥有新的 Product Scope。

- `In scope / Out of scope` 只表示 P1-07 implementation-slice scope；
- `P107-AC-*` 属于 **Technical / Recovery / UX Vertical Slice Acceptance**，不自动成为 `PD-AC-*`；
- “系统故障不得伪造成 learner failure / mastery change”等产品语义来自 `PD-RULE-010`；
- OCR、Desktop host、provider 等具体 recovery adapter 是否属于 current v1 正常产品路径，必须服从 Product Definition、current supersession 与对应 Specs，不能因本历史 Slice 出现而自动成为 Product Requirement；
- Recovery Engineering PASS 不自动证明 `CAP-07` 或 `CAP-08` 已完整 Product Accepted。

## 1. Objective

让本地单用户从统一入口理解并恢复 provider、资料、任务、数据库和启动故障，同时保证重试不重复副作用、失败不污染学习证据、敏感诊断不泄漏。

具体 host/bootstrap adapter 由 current platform contract 决定；历史 Electron/Desktop mechanics 仅在仍有兼容价值时作为 implementation evidence，不定义当前 v1 Product Shape。

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
local runtime/bootstrap failure
→ current bootstrap diagnostic contract
→ startup recovery surface
→ single-flight retry
→ readiness success
→ normal App
```

## 3. In scope

本节只定义 Recovery Center slice scope：

- complete error envelope and stable catalog；
- provider timeout/rate/key/model/output failure classification；
- current Material/document issue projection；
- outbox waiting/exhausted/handler-unavailable projection and allowlisted recovery；
- migration/database/bootstrap diagnostics；
- Recovery Center page, Settings station and global indicator；
- retry budget/wait/result/audit/idempotency；
- negative learning-evidence firewall；
- responsive/accessibility/restart E2E。

历史 OCR-review / Desktop-specific recovery adapter 若仍存在，必须按 current Product Definition / supersession 判断是否 normal-v1 reachable、optional compatibility 或 historical only。

## 4. Out of scope

本节 OUT 不等于 Askora 总体 Non-goal：

- Recovery Center 直接修复数据库、编辑文件、改模型密钥或 patch owner ORM；
- 未知/非幂等 task 的 generic replay；
- 自动解除 quarantine 或发布低置信内容；
- 把 resolved 当作资料正确、学习完成或 mastered；
- 云端监控、多人运维后台或远程支持上传。

## 5. Product-facing Recovery Semantics

以下是对上游 Product Rules 的 recovery UX 具体化，不是新的 Product Definition：

- 每张问题卡固定显示“发生了什么 / 数据是否安全 / 现在能做什么 / 重试说明”；
- blocking first，其次 waiting/warning；同 resource/code 合并为一个 versioned issue；
- command 执行中禁用重复点击，刷新后按同 idempotency result 恢复；
- rate limit 显示服务端 next eligible time，Key 无效只导航到模型设置；
- file missing 不承诺自动找回；只有 owner 已实现真实替换/恢复 command 才提供对应 action；
- provider issue 可返回关联的 canonical activity，但导航本身不重放调用；
- 没有问题时显示最近一次检查时间，不制造“系统绝对安全”的承诺；
- 技术详情折叠展示 code/correlation/ref，不显示 stack/path/secret；
- runtime/provider/storage failure 不得转换为 learner failure、mastery promotion/demotion 或伪完成证据。

任何 OCR-specific recovery UI 必须额外服从 current Product Definition 的 no-OCR-core / UI exposure 边界；本 Slice 的历史条款不授予其 v1 normal-path scope。

## 6. Dependencies and integration gate

执行或重新验收本 Slice 时必须从 current truth 验证：

- current error/recovery owner contracts；
- applicable provider / Material / task / data-control capabilities；
- current bootstrap/runtime architecture；
- canonical activity / evidence firewall；
- current Linear dependencies/status。

依赖尚未闭合时必须报告明确 unavailable / blocked 状态；不允许通过 mock-only、disabled button 或历史 EXEC completion 宣称 current closure。

## 7. Technical / Recovery / UX Acceptance Criteria

以下 AC 不创建新的 Product Acceptance：

- `P107-AC-001`：RECOVERY-AC-001..007 中仍适用于 current v1 的合同全部满足；
- `P107-AC-002`：provider 主要错误类型有稳定 code/action/budget，且 accepted transcript、Attempt、mastery/review/activity 不产生错误副作用；
- `P107-AC-003`：current document/task failures 能从 owner facts 呈现，不以 UI 状态伪造 recovery truth；
- `P107-AC-004`：所有 command LocalOwner/current-scope、versioned、幂等、bounded、audited；
- `P107-AC-005`：migration/database/local runtime unavailable 能通过 current bootstrap diagnostic contract 呈现和 single-flight retry；
- `P107-AC-006`：刷新/App 重启后 issue/result 一致，不重复 task/run/transition；
- `P107-AC-007`：真实浏览器覆盖适用 provider failure recovery、document recovery、bootstrap recovery；
- `P107-AC-008`：360px、200% zoom、keyboard/focus/live region 通过；
- `P107-AC-009`：Engineering、Policy/Ownership、Security/Privacy PASS；Learning Evidence 保持 `LEARNING_EVIDENCE_INSUFFICIENT`。

若某历史 OCR/Desktop acceptance 不再属于 current v1 normal path，应按 supersession 归类而不是为了满足旧 AC 恢复产品暴露。

## 8. Completion rule

只有 applicable current technical gates、真实浏览器路径和依赖 owner actions 都有 current evidence 时才能将 P1-07 technical contract 标为 DONE。

如果进一步声称用户已经获得完整 recovery 产品能力，还必须单独核对 applicable `CAP-07 / CAP-08` Product Acceptance。单有错误页面、API tests、mock provider、历史 Desktop evidence 或可点击但无后端 command 的按钮均不算 Product Acceptance。
