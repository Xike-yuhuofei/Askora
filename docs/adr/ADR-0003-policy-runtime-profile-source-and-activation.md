# ADR-0003 — Policy Runtime Profile Source and Activation Resolution

Status: accepted
Date: 2026-08-08
Decision owners: Askora Spec Owner（2026-08-08 明确批准）
Affected specs: `docs/specs/systems/05-teaching-policy.md`, `docs/specs/vertical-slices/book-to-adaptive-learning.md`, `docs/specs/interfaces/persistence-contract.md`

## Context

SYS05 已冻结 `PolicyBundle` 的不可变发布、原子激活和 exact-bundle replay，但此前只有测试 fixture 提供 `PolicyRuntimeProfile` 数值，生产路径没有规范化 profile 来源，也没有从 active activation 解析 exact bundle/profile 的默认 resolver。EXEC-023 因此无法在不猜测生产配置的情况下进入 canonical Teaching Policy。

该缺口不改变 SYS05 的 TeachingAction 所有权、算法层次、TeachingStage、anti-oscillation 或既有 Adaptive Teaching Loop；它只补齐既有 PolicyBundle 合同的生产配置来源和解析规则。

## Decision

1. 首个生产 `PolicyRuntimeProfile` 使用已验证的 EXEC-009 fixture 行为参数，赋予生产身份 `askora-v03-default-1`，并作为仓库内不可变 JSON artifact 管理。测试 fixture 不是生产配置来源。
2. Profile digest 的唯一算法为：移除顶层 `content_digest` 后，将完整 JSON 对象按 key 升序、UTF-8、无多余空白（`separators=(",", ":")`）序列化，再计算 SHA-256，写为 `sha256:<lowercase hex>`。artifact 自带 digest、PolicyBundle `content_digest` 与运行时重算值必须完全一致。
3. 生产 resolver 必须按 `activated_at DESC, activation_id DESC` 读取最新 `PolicyBundleActivation`，再解析 exact `PolicyBundle` 和与 manifest 全字段匹配的不可变 profile。缺失 activation、bundle、artifact、digest 不一致或版本不匹配均 fail closed，不得回退到测试 fixture、最新文件或 LLM 推断。
4. 默认 bundle 和 activation 通过确定性、幂等的数据 migration bootstrap；已有历史 activation 不被覆盖。后续 activation 只影响新 TeachingAction。
5. Replay 必须继续使用 TeachingAction/DecisionTrace 已固定的 exact bundle/profile；不得通过当前 active activation 重解释历史动作。

## Alternatives Considered

- 将 fixture 直接作为生产来源：拒绝，因为测试资产会成为隐式 production truth，无法形成清晰发布边界。
- 在环境变量中散列阈值与权重：拒绝，因为无法保证 exact digest、审计和 replay。
- 在首次请求时自动创建 bundle/activation：拒绝，因为 read path 产生隐式状态写入，且并发与失败语义不清晰。
- 缺少 active profile 时使用代码默认值：拒绝，因为会绕过 atomic activation 和 fail-closed 合同。

## Consequences

- 数值仍属于 versioned policy profile，不被宣称为学习科学常数。
- 更改任一参数必须发布新 artifact、新 digest、新 PolicyBundle，并原子激活；不得原地修改已发布 profile。
- 生产启动/迁移缺失时会显式不可用，而不会偷偷使用测试配置。
- 不新增生产依赖、服务、状态 owner 或第二条 Teaching Loop。

## Migration / Rollback

- Upgrade 仅插入确定 ID 的默认 PolicyBundle 和 activation；相同内容可重复执行，不同内容必须冲突失败。
- 空数据库可回滚删除该 activation/bundle；若已有 TeachingAction 引用默认 bundle，回滚必须 fail closed，保留历史 provenance，改走 forward-fix。
- SQLite 与 PostgreSQL 使用相同业务语义。

## Validation

- artifact canonical digest 测试；
- migration upgrade/idempotency/rollback guard 测试；
- active activation 稳定排序和 exact match 测试；
- missing/mismatch fail-closed 测试；
- Book-to-Learning 走默认 production resolver 到 canonical TeachingAction/EvidenceBundle 的集成测试。

## Supersedes / Superseded By

不 supersede 既有 ADR；本 ADR 补充 ADR-0002 的 PolicyBundle publish/activation 生产解析合同。
