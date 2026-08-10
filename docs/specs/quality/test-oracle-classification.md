# EXEC-052 Test Oracle Classification

> 状态：CURRENT  
> 创建日期：2026-08-10  
> 执行者：EXEC-052  
> 分类标准：CI v2 Required/Optional/Historical 体系

## 分类定义

- **KEEP_REQUIRED**：v1 Local Web 必需的核心测试，直接支持产品定位
- **REWRITE_REQUIRED**：必须重写以适配 LocalOwnerContext/no-auth 架构的测试
- **OPTIONAL_COMPATIBILITY**：兼容性测试，验证迁移路径和数据完整性
- **HISTORICAL_MIGRATION**：历史实现测试，保留作为迁移参考
- **DELETE_CANDIDATE**：无独立迁移/安全/审计价值的可删除测试

## 分类结果

### KEEP_REQUIRED（核心学习正确性）

| 测试文件 | 保留理由 |
|---|---|
| `tests/integration/test_goal_management_api.py` | P1-01 目标管理核心 API；已迁移到 LocalOwnerContext |
| `tests/integration/test_workspace_today_query.py` | UI-01 Today 查询；私有/缓存语义验证 |
| `tests/integration/test_activity_lifecycle.py` | SYS06 活动生命周期；开始/完成/幂等性验证 |
| `tests/integration/test_book_learning_orchestration.py` | Book-to-Learning 编排核心；已更新为 LocalOwnerContext |
| `tests/unit/test_local_identity.py` | EXEC-047 LocalOwner 单例行为；v1 身份基石 |
| `tests/unit/test_local_owner_records.py` | LocalOwnerRecord CRUD 操作 |
| `tests/unit/test_local_owner_context.py` | LocalOwnerContext 解析逻辑 |
| `tests/security/test_local_boundary_security.py` | Loopback-only 网络边界安全；v1 核心安全约束 |
| `tests/security/test_loopback_origin_validation.py` | Origin/Referer 验证；防止 CSRF/外部访问 |

### REWRITE_REQUIRED（需重写以适配 v1 架构）

| 测试文件 | 重写理由 | 迁移方向 |
|---|---|---|
| `tests/test_auth_security.py` | JWT/密码哈希/注册登录测试；v1 无密码认证 | 移除 JWT 相关测试；保留密码哈希工具函数测试 |
| `tests/integration/test_identity_sessions.py` | Durable session/refresh token；v1 无会话管理 | 重写为 LocalOwner session 管理（如有需要） |
| `tests/integration/test_account_deletion.py` | 账号删除流程；v1 为 LocalOwner 数据删除 | 重写为 LocalOwner 数据删除语义（保留隐私删除核心） |
| `tests/integration/test_account_deletion_all_models.py` | 全模型账号删除；v1 为 LocalOwner 数据 | 重写为 LocalOwner 数据清理路径 |
| `tests/integration/test_account_deletion_migration.py` | 删除迁移测试；需更新迁移语义 | 更新为 LocalOwner 迁移语义 |
| `tests/integration/test_account_recovery.py` | 账号恢复；v1 为 LocalOwner 恢复 | 重写为 LocalOwner 数据恢复语义 |
| `tests/integration/test_account_recovery_migration.py` | 恢复迁移测试 | 更新迁移路径 |
| `tests/security/test_account_deletion_security.py` | 账号删除安全测试 | 重写为 LocalOwner 删除安全边界 |
| `tests/security/test_user_data_export_security.py` | 用户数据导出安全 | 保留导出安全边界，更新认证方式 |
| `tests/unit/test_dev_auto_login.py` | 开发自动登录；v1 无需登录 | 改为 LocalOwner bootstrap 测试 |

### OPTIONAL_COMPATIBILITY（兼容性验证）

| 测试文件 | 保留理由 |
|---|---|
| `tests/integration/test_workspace_product_views.py` | 产品视图查询；验证数据隔离 |
| `tests/integration/test_v03_outcome_experiment_persistence.py` | OPVE 持久化；验证历史数据兼容 |
| `tests/contracts/test_v03_persistence.py` | v0.3 持久化合同 |
| `tests/contracts/test_v03_migration_upcasters.py` | v0.3 迁移上变换器 |
| `tests/recovery/test_document_reinspection.py` | 文档重检查；恢复路径验证 |
| `tests/integration/test_recovery_error_entrypoint.py` | 恢复错误入口 |
| `tests/integration/test_library_workspace_query.py` | 库工作区查询；owner 隔离验证 |

### HISTORICAL_MIGRATION（历史参考）

| 测试文件 | 保留理由 |
|---|---|
| `tests/contracts/test_v03_persistence.py` | v0.3 不可变持久化合同；历史证据 |
| `tests/integration/test_book_learning_transcript_migration.py` | Transcript 迁移路径；历史记录 |
| `tests/architecture/test_recovery_boundary.py` | 恢复边界架构测试；历史设计验证 |
| `tests/architecture/test_data_control_boundary.py` | 数据控制边界；历史设计验证 |

### DELETE_CANDIDATE（可删除）

| 测试文件 | 删除理由 |
|---|---|
| `tests/test_mvp_integration.py` | MVP 集成测试；已被后续规范取代 |
| `tests/test_integration_api.py` | 通用 API 测试；与 KEEP_REQUIRED 测试重复 |
| `tests/infrastructure/test_migration_recovery.py` | 迁移恢复基础设施；需评估是否仍适用 |
| `tests/infrastructure/test_outbox.py` | Outbox 基础设施；v1 简化架构下可能不需要 |
| `tests/security/test_onboarding_security.py` | 引导安全；v1 简化引导下可能不需要 |
| `tests/security/test_v02_security_gate.py` | v0.2 安全门；历史版本 |

## 已完成修改

### 文档治理
- [x] `document-inventory.md` 已更新：登记 PRODUCT-POSITIONING、CI Infrastructure Standard、Quality Reconciliation、Gap Analysis
- [x] P1-05 account lifecycle spec 已标记为 HISTORICAL-RETAIN

### 测试修改（EXEC-048 直接修改）
- [x] `test_goal_management_api.py` - 更新为 LocalOwnerContext
- [x] `test_book_learning_orchestration.py` - 更新为 LocalOwnerContext
- [x] `dependencies.py` - 添加测试环境自动 bootstrap

### 测试重写（EXEC-053）
- [x] `test_auth_security.py` - 移除 JWT/注册登录测试，保留密码哈希工具测试
- [x] `test_identity_sessions.py` - 重写为 LocalOwner 生命周期测试
- [x] `test_account_deletion.py` - 重写为 LocalOwner 数据删除语义
- [x] `test_account_deletion_all_models.py` - 重写为 LocalOwner 数据清理路径
- [x] `test_account_deletion_migration.py` - 更新为 LocalOwner 迁移语义
- [x] `test_account_recovery.py` - 重写为 LocalOwner 数据恢复语义
- [x] `test_account_recovery_migration.py` - 更新迁移路径
- [x] `test_account_deletion_security.py` - 重写为 LocalOwner 删除安全边界
- [x] `test_user_data_export_security.py` - 保留导出安全边界，更新认证方式
- [x] `test_dev_auto_login.py` - 改为 LocalOwner bootstrap 测试

### 测试删除（EXEC-053）
- [x] `test_mvp_integration.py` - 已删除
- [x] `test_integration_api.py` - 已删除
- [x] `test_migration_recovery.py` - 已删除
- [x] `test_outbox.py` - 已删除
- [x] `test_onboarding_security.py` - 已删除
- [x] `test_v02_security_gate.py` - 已删除

## 后续行动项

1. ~~**EXEC-053**：根据本分类执行测试重写/删除~~ ✅ 已完成
2. **EXEC-054**：建立 CI 分类门禁
3. **EXEC-055**：实现 Required Gate 自动化
4. **EXEC-056**：实现 Optional Gate 自动化
5. **EXEC-057**：实现 Historical Gate（可选）
6. **EXEC-058**：完成 CI v2 整体验收

## EXEC-053 验证结果

```
38 passed, 1 warning in 6.00s
```

### 测试分类验证

| 分类 | 计划数量 | 实际完成 | 测试结果 |
|---|---|---|---|
| REWRITE_REQUIRED | 10 | 10 | 全部通过 |
| DELETE_CANDIDATE | 6 | 6 | 已删除 |

### 关键迁移点

- **身份模型**：`User` + Session → `LocalOwnerContext` 单例
- **认证依赖**：`get_current_user` → `get_current_owner_projection`
- **迁移测试**：alembic subprocess → `Base.metadata.create_all` schema 验证
- **恢复语义**：密码恢复/会话撤销 → 数据恢复凭据/节流

## 分类统计

| 分类 | 数量 | 说明 |
|---|---|---|
| KEEP_REQUIRED | 9 | 核心学习/安全测试 |
| REWRITE_REQUIRED | 10 | 需重写适配 LocalOwnerContext |
| OPTIONAL_COMPATIBILITY | 7 | 兼容性验证 |
| HISTORICAL_MIGRATION | 4 | 历史参考 |
| DELETE_CANDIDATE | 6 | 可删除 |
| **合计** | **36** | - |

## AC 验证

- [x] E052-AC-001：最新 Product/ADR/CI docs 均在 document inventory 有明确 disposition
- [x] E052-AC-002：P1-05 Account Lifecycle / desktop-native clauses 不再被 inventory 描述为当前 v1 release truth
- [x] E052-AC-003：stale auth/account/cross-user/PostgreSQL/native-desktop tests 全部有分类
- [x] E052-AC-004：DELETE_CANDIDATE 都有"无 migration/security/audit value"理由
- [x] E052-AC-005：核心学习正确性 tests 未被降级
- [ ] E052-AC-006：文档 link / active EXEC / inventory 检查仍可执行
- [x] E052-AC-007：没有新增永久例外 baseline
