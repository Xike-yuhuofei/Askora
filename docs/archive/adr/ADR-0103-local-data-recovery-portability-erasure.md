# ADR-0103 — Local Data Recovery, Portability and Erasure

Status: accepted
Date: 2026-08-09
Decision owner: Codex under the user's explicit authorization to close P1-03
Decision authority: user-delegated Codex
Affected specs: `docs/specs/interfaces/data-control-contract.md`, `persistence-contract.md`, `schema-versioning.md`, `api-contract.md`, `error-contract.md`, `security-standard.md`, UI data/screen contracts, P1-03 Vertical Slice

## Context

Askora 桌面数据同时存在 SQLite、原始资料文件、可重建 projection 和本地 secrets。当前没有自动备份/恢复/导出能力；资料删除只软删一行再删除文件，无法证明关联 event、inference、state 与 projection 已处理，也无法防旧恢复点复活已删除事实。

直接复制 userData 不能保证跨数据库/文件一致性。让一个 data-control service 直接删除所有 owner table 又会破坏 single-writer。恢复还必须保留数据库内受 KEK 保护字段的可读性，同时不得恢复旧 JWT 会话或导出供应商 secret。

## Decision

1. P1-03 正式产品范围为 macOS 私人桌面 SQLite；PostgreSQL/Docker 使用独立运维 adapter，不由桌面 UI 冒充支持。
2. 恢复使用 versioned encrypted recovery package，包含 consistent SQLite snapshot、managed raw assets、manifest/checksums、必要 KEK material 与 erasure checkpoint；不包含浏览器 cache/log/Redis/provider keys。
3. Recovery Key 是独立随机 secret。设备副本由 platform secure storage 保护；跨设备恢复由用户提供 key。恢复包绝不包含可直接解密自己的明文 key。
4. backup/restore 在 desktop maintenance mode 中运行。恢复只在 staging 校验/迁移/reconcile 后原子切换；失败保持或恢复原数据。
5. pre-migration verified snapshot 是 destructive migration 的硬前置；失败阻止 migration。Alembic downgrade 不作为首选数据恢复方案。
6. 用户导出与 recovery package 分离。导出 current-user readable data，不含 secret、password hash、内部 Prompt、grader-only 或本地路径，也不能直接 import 为 canonical DB。
7. `DataErasureWorkflowV1` 只协调 owner commands 和文件适配器，不成为第九 owner。删除 scope 固定为 DOCUMENT、LEARNING_RECORDS、MODEL_EXECUTION、ALL_PERSONAL_DATA。
8. 删除完成写最小 ErasureCheckpoint/Receipt，旧 managed recovery point 必须被 checkpoint 阻断或失效，再创建 verified post-erasure baseline。恢复先应用 current checkpoint，projection rebuild 不得重新生成已删事实。
9. JWT secret 在恢复时重新生成；数据库 PII 解密所需 KEK 必须恢复。Provider keys 由 P1-02 管理，不进入 P1-03 普通 recovery/export。
10. 每个 backup/export/restore/erasure command 都必须 versioned、owner/current-user scoped（适用时）、幂等、带稳定错误码和可读报告。

## Alternatives Considered

- **Whole-directory copy**：拒绝；没有 transaction boundary、内容 manifest、密钥策略、兼容性或恢复验证。
- **只做数据库备份**：拒绝；会丢原始资料并产生 dangling SourceSpan/projection。
- **恢复时逐 owner 重建全部 canonical truth**：拒绝；会扩大迁移范围且可能调用新算法重解释历史。
- **单事务跨 owner hard delete**：拒绝；违反 single-writer，且文件副作用无法与数据库可靠原子提交。
- **保留所有旧恢复点并在 UI 警告**：拒绝；不能满足删除后不复活事实。

## Ownership and Invariants

- Recovery Package/Catalog/Report 是 infrastructure/control artifacts，不是 learner/content/plan truth。
- Physical snapshot 不授予 recovery code 改写 owner payload 的权力；只允许确定性 migration/reconciliation/invalidation。
- Erasure coordinator 只能调用公开 owner erase/invalidate commands；不得跨域直接 ORM patch canonical state。
- Restore/replay 不调用在线 LLM，不用 current mutable state 猜历史缺失字段。
- `restore succeeded` 不等于所有学习结论仍 scientifically valid；只证明合同内数据一致性。

## Migration / Rollback

新增 additive data-control contracts、catalog/report storage 与必要 migration。旧桌面数据第一次启用时创建 Recovery Key 与 recovery catalog，不改写 canonical facts。首次 verified baseline 成功前 UI 保持 `NOT_PROTECTED`。

产品升级顺序为 preflight → verified pre-migration recovery point → staging migration/validation → activation。失败删除 staging 并保留当前数据；已激活但 readiness 失败使用 rescue snapshot forward-fix/restore。旧客户端忽略新 API/IPC，不形成双写。

## Security and Privacy

- AEAD authenticated encryption、per-package salt/nonces、versioned KDF/key derivation；
- safe extraction、size/count/compression limits、path/symlink checks；
- secret 只通过受控 process environment/IPC memory 传递，不写日志、argv、manifest 或 export；
- recovery report 只含状态、计数、hash/ref 和 reason code，不含用户内容；
- destructive erasure 必须 preview + expiring confirmation + explicit user action。

## Validation

- container round trip、wrong key、tamper、truncation、duplicate/traversal/symlink/zip-bomb tests；
- SQLite online/offline snapshot integrity、raw asset manifest、missing/corrupt file；
- older supported schema forward migration、future/unknown schema rejection、migration failure rollback；
- restore staging/atomic activation/rescue rollback/readiness；
- current-user export allowlist 与 secret/grader/internal-field zero leakage；
- four erasure scopes、owner coordination、idempotency、partial failure recovery、projection rebuild、old-backup resurrection prevention；
- Electron IPC allowlist、360px/keyboard/error/recovery report、packaged backend maintenance smoke；
- Engineering、Policy/Ownership、Learning Evidence 分别报告。

## Supersedes / Superseded By

本 ADR additive 落实 `PERSIST-080`、`PERSIST-090`、`STATE-023` 与 `EVENT-071`，不改变 SYS01～SYS08 业务状态所有权。未来跨设备同步或服务模式 managed backup 需要独立 ADR/adapter。
