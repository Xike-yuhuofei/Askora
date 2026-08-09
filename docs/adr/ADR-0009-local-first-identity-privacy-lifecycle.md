# ADR-0009 — Local-first Identity and Privacy Lifecycle

Status: accepted
Date: 2026-08-09
Decision owner: Codex under the user's explicit authorization to close P1-05 and pass the related tests
Decision authority: user-delegated Codex
Authorized objective: 真正关闭 `docs/product-gap-register-p1-p2.md` 的 P1-05 账号生命周期
Affected specs: `docs/specs/platform/identity-privacy-lifecycle.md`, `docs/specs/interfaces/api-contract.md`, `docs/specs/interfaces/error-contract.md`, `docs/specs/interfaces/persistence-contract.md`, `docs/specs/quality/security-standard.md`, `docs/specs/ui/screen-contracts.md`, `docs/specs/vertical-slices/p1-05-account-lifecycle.md`

## Context

Askora 当前有注册、登录、refresh rotation 和当前 access-token 登出，但没有 durable session family、密码修改、离线恢复、会话管理或完整账号删除。Redis/进程内撤销状态不满足本地重启恢复；软删除 `User` 不能处理 SYS01～SYS08、文件和 projection。

账号/隐私不属于八个学习系统中的任意一个。让 API handler 或一个通用 ORM cascade 直接删除所有表，会越过 owner boundary；让每个系统自行解释删除请求又会形成不一致的八套产品流程。

## Decision

1. 建立 Platform Identity & Privacy 横切边界。它不是第九学习系统，不拥有任何学习 truth。
2. Identity 唯一拥有账号 credential version、durable `AuthSession` 和 `RecoveryCredential`。
3. access/refresh token 必须绑定 durable session/token family；Redis 只能缓存。refresh replay 撤销整个 family。
4. 新/修改密码使用 Argon2id；历史 bcrypt 兼容读取并在成功认证时渐进 rehash。新增依赖必须固定版本、进入 lock/audit，并保留 bcrypt rollback compatibility。
5. 忘记密码使用离线高熵恢复套件，不引入短信/邮件供应商；恢复 secret keyed-hash、单次使用、限流并在使用后轮换。
6. Privacy Coordinator 唯一拥有删除 request/manifest/step receipt/tombstone。它通过 owner erasure handler 调用 SYS01～SYS08，不取得普通业务写权限。
7. `DeleteAllLearningDataV1` 是账号保留的数据删除合同；`DeleteAccountV1` 复用同一 owner-erasure foundation，成功后再清除身份，不建立第二套清除逻辑。
8. 删除使用 `ACTIVE → DELETION_PENDING → PURGING → DELETED`；pending 可取消，purging 不可取消，永久 reconciliation 失败保持受限 `DELETION_BLOCKED`。
9. 删除 preview/command strict v1、current-user、versioned、idempotent，并要求 current password、确认短语和 preview version。
10. 删除完成前必须通过 subject manifest/reconciliation 零残留；无法唯一归属的数据 fail closed。
11. 完成 tombstone 不含手机号、昵称、密码、原文、学习内容、模型正文或可逆身份；数据库外 restore barrier 防止 App 管理的旧快照静默复活。

## Alternatives Considered

### 在现有 AuthService 增加几个 endpoint，并继续使用 Redis session

拒绝。重启后 session truth 丢失，logout 无法撤销 refresh family，也不能支持可靠设备管理。

### 直接 ORM cascade 删除 User

拒绝。大量 canonical/ledger 表没有 User FK，文件与 projection 不在 ORM cascade 内；这还会绕过系统 owner。

### 引入短信/邮件恢复服务

拒绝作为 P1-05 首版。它增加外部付费、PII 传输、供应商故障和合规边界，不符合私人本地产品的最小必要范围。

### 永久保留软删除账号及全部历史 ledger

拒绝。它不能满足用户删除受保护内容和 projection 重建要求。允许范围 audit 只能保留去内容、去 PII tombstone。

## Invariants

- Identity/Privacy 不是 LearnerState、Assessment、TeachingAction、Plan、Review 或 Execution truth owner。
- 普通 auth/session 操作不得修改学习数据。
- owner erasure handler 只删除 manifest 中属于目标 subject 且由该 owner 管理的数据。
- 同一 deletion request/step/idempotency key 不产生第二次副作用。
- pending cancellation 不得恢复已进入 purging 的请求。
- account/system failure 不得形成 learner error 或负向学习 evidence。
- 删除后的 outbox/rebuild/restore 不得重新生成已删除事实。

## Migration / Rollback

- additive 新增 identity/privacy tables、User credential/lifecycle fields 与索引；SQLite/PostgreSQL migration 都需代表性 fixture。
- 现有 JWT 缺少 `sid`/credential version，cutover 后拒绝 refresh；旧 access token 最多进入一次明确 `AUTH_SESSION_REQUIRED` 并要求重新登录，不建立永久 compatibility session。
- 历史 bcrypt hash 保留并可验证；成功登录/修改后 rehash 为 Argon2id。回滚版本仍能验证 bcrypt 和已存 Argon2id，优先 forward-fix。
- 历史用户数据在删除 preview 时通过 frozen subject registry 建 manifest；归属不确定则阻断删除，不猜测。
- deletion coordinator 的已完成 receipt/tombstone 不回滚；代码回滚后仍必须拒绝被 barrier 标记的旧身份。数据库迁移优先 forward-fix。

## Security / Privacy

- password/recovery/deletion endpoint server-side rate limit；响应不得泄漏账号是否存在。
- recovery、refresh、deletion-control secret 不写日志、Prompt、普通 export 或前端 user cache。
- 高风险操作重新认证；密码修改/恢复/账号删除撤销相关 session family。
- cross-user session/deletion/manifest 不可枚举。
- subject manifest、step receipt 和 tombstone 只保存完成治理所需最小 metadata。

## Validation

- strict schema/error/idempotency/concurrency/property tests；
- refresh reuse、password change、session revoke 与 Redis/restart tests；
- recovery code one-time/throttling/generic response tests；
- deletion preview stale、cancel boundary、restart resume、owner receipt、文件/projection/outbox/reconciliation tests；
- SQLite/PostgreSQL migration/upgrade/forward-fix 与 old snapshot restore barrier；
- 360px/200% zoom/keyboard/real browser account lifecycle；
- Engineering、Policy/Ownership、Learning Evidence 分开报告。

## Supersedes / Superseded By

本 ADR additive 补充 ADR-0001～0007，不改变八系统学习 truth 所有权。
