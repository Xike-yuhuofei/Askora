# Askora 链 B：CI v2 质量门禁重构（EXEC-054 → 055 → 057 → 058）

## 角色
你是 Askora 项目的 CI/CD 工程师、测试架构师和执行代理。

## 最终目标
> 基于已完成的 Product Boundary baseline（EXEC-047～053 DONE），按依赖顺序连续执行 EXEC-054 → EXEC-055 → EXEC-057 → EXEC-058，完成 CI v2 Required Gate 收口，将 Askora 工程质量基线迁移到 v1 Local Web + SQLite + 单用户无认证架构。

## 执行依赖
```
EXEC-054 DONE  →  EXEC-055 DONE  →  ┬→ EXEC-057 DONE  ─┐
                                     │                  │
                                     └→ EXEC-056 DONE  ─┴→ EXEC-058 DONE
```
注意：EXEC-056 需要 EXEC-046 DONE（链 A）+ EXEC-055 DONE（链 B）才能启动。

## 开始前必须读取
```text
AGENTS.md
docs/product/PRODUCT-POSITIONING.md
docs/specs/quality/ci-infrastructure-standard.md
docs/specs/quality/v1-local-web-quality-reconciliation.md
docs/specs/quality/test-oracle-classification.md
docs/design/CI-Test-Infrastructure-Gap-Analysis.md
docs/adr/ADR-0015-local-single-user-identity-without-authentication.md
docs/specs/quality/**
docs/exec-plans/active/EXEC-054-required-core-test-realignment.md
docs/exec-plans/active/EXEC-055-local-data-migration-recovery-rebuild-gate.md
docs/exec-plans/active/EXEC-057-ci-workflow-quality-supply-chain.md
docs/exec-plans/active/EXEC-058-required-gate-main-protection-closure.md
```

---

## EXEC-054 — Required Core Test Realignment

### 目标
将 Required backend/test suite 从历史 auth/PostgreSQL/service-mode truth 重排为 **Product Boundary + Learning Core + SQLite Production Local truth**，并将 Optional/Historical tests 与 Required tests 物理或逻辑隔离。

### 核心 Product Boundary 断言
```text
single user / no auth
loopback Local Web
no Redis/Postgres/Docker runtime requirement
Workspace != Tenant / Organization
no default cross-Workspace retrieval or Global Material Library
Material belongs to Workspace
Material <-> LearningProject = many-to-many
LearningProject is not required to start learning from Material
remove Material from Project != delete Material
Normal Delete -> Trash -> Permanent Delete
LLM cannot directly mutate canonical persistence
```

### 允许修改的文件
```text
apps/backend/tests/**
apps/backend/pyproject.toml
. github/**
docs/specs/quality/**
docs/exec-plans/**
```
不得修改 production code，除非发现 production bug 且仅限最小范围修复。

### 禁止修改
- 不用 skip/xfail 隐藏失败
- 不降低 G0 / hard-rule / security assertions
- 不把 Mock 当真实 Provider current availability
- 不继续让 password/JWT/AuthSession/cross-user service-mode 成为 Required oracle
- 不把 PostgreSQL compatibility 作为 SQLite v1 release blocker
- 不删除有 migration/security 价值的 historical fixtures
- 不把 Workspace isolation 改写成多租户/Tenant 测试
- 不引入 Global Material Library / default cross-Workspace search
- 不让"必须先创建 Project 才能学习 Material"成为 Required oracle
- 不把从 Project 移除 Material 等同于删除 Material
- 不让 LLM/mock provider 直接写 SQLite/canonical repositories

### 实现任务（13 项）
1. 建立 `product-boundary` 自动测试：no-auth、loopback、no external infra requirement、Workspace != Tenant、LLM no canonical direct write
2. 扩展 product-boundary：Workspace scope 默认隔离，默认 retrieval/material query 不跨 Workspace
3. 增加 Material / LearningProject 关系测试：Material 必属 Workspace；多对多；解除关系不删除 Material
4. 增加 direct-Material learning boundary：无 Learning Project 前提下，Material 可直接启动学习
5. 增加删除边界测试：Normal Delete → Trash → Permanent Delete
6. 建立 Required suite composition：architecture + unit + contract + SQLite integration + deterministic OPVE core + product-boundary
7. 将 cross-user/auth tests 改写为 LocalOwner / Workspace / RetrievalScope / destructive-operation boundary
8. PostgreSQL/legacy auth/native desktop tests 移到 Optional/Historical
9. 删除无 migration/security/audit value 的 DELETE_CANDIDATE
10. 保留并强化 Teaching Policy / Assessment / Learner State / Review / Retrieval / Content / Replay tests
11. 统一 pytest markers/commands
12. 清理游离脚本
13. Required suite 不读取用户真实 AskoraData，不需要用户 API Key

### 验收标准（13 项）
1. 存在稳定 Required backend test command
2. Product Boundary tests 自动验证 no-auth / loopback / no Redis/Postgres/Docker
3. Required suite 无 stale Account/JWT/password expected behavior
4. cross-user Required tests 已改写为 LocalOwner/Workspace scope
5. PostgreSQL/native desktop/real-provider tests 可独立运行且默认不属于 Required
6. G0/OPVE/assessment/replay core 未弱化
7. Required suite 不依赖真实 AI key/network
8. 无批量 skip/xfail 伪造通过
9. Workspace isolation 自动证明
10. Material/Project 多对多证明
11. 无 Project 的 Material 可沿 canonical path 学习
12. 两阶段删除语义有自动化证据
13. LLM/provider output 不能直接写 canonical persistence

### 必须通过的测试
```bash
cd apps/backend
pytest tests/ -m required
pytest tests/ -m product_boundary
ruff check app tests
```

---

## EXEC-055 — Local Data Migration, Recovery & Rebuild Gate

### 前提条件
- EXEC-054 已 DONE 并归档

### 目标
将 Askora v1 最重要的数据正确性要求转化为 Required automation：
1. SQLite migration（fresh → usable、legacy fixture → usable、migration failure → durable data preserved）
2. Askora Backup/Restore（Durable Data 可验证 roundtrip）
3. Derived Data 重建（chunks/embeddings/indexes/retrieval cache/derived learner projection）
4. 后台任务中断恢复（job running → process interrupted → restart → resume/retry/restart → durable data intact）
5. Learning Evidence 删除后的 Learner State 重算

### 关键语义区分
```
Backup = 恢复 Askora 本身
Export = 让用户数据离开 Askora 后仍可使用
```
Backup/Restore 围绕 Durable Data 建立；API Key、可重建 Cache/Embedding/Index 默认不得成为恢复 Askora 所必需的备份内容。

### 验收标准
1. Fresh SQLite → migrate → usable 有自动化证据
2. Legacy SQLite fixture → migrate → usable 有自动化证据
3. Migration failure → durable data preserved 有自动化证据
4. Restart → data preserved 有自动化证据
5. Backup/Restore roundtrip 有自动化证据
6. Derived Data delete → rebuild → canonical semantics preserved 有自动化证据
7. Job interruption → restart → resume/retry → durable data intact 有自动化证据
8. Learning Evidence 删除后 Learner State 正确重算

### 必须通过的测试
```bash
cd apps/backend
pytest tests/ -m migration
pytest tests/ -m recovery
pytest tests/ -m rebuild
ruff check app tests
```

---

## EXEC-057 — CI Workflow, Quality & Supply-chain Realignment

### 前提条件
- EXEC-054 已 DONE
- EXEC-055 已 DONE

### 目标
把 GitHub Actions 和静态质量基础设施重构成稳定、低脆弱、可维护的 CI v2：
1. Required 与 Optional 分离
2. 永久 legacy baseline 退休
3. Actions/runtime/dependency 自动更新
4. 减少无价值重复矩阵和过期 run

### Required CI 必须包含
```text
Ruff
Formatter
MyPy
Backend Tests (Required suite)
Frontend Tests
Frontend Build
SQLite Migration
Recovery/Rebuild
Security
Dependency Audit
```

### 逐步删除的永久技术债
```text
check_black_baseline.py
historical hash baseline
large permanent mypy exclusion
historical phase hard-coded docs checks
```

### 禁止
- 为全绿降低 coverage、扩大 skip、删除有效测试、降低断言
- 恢复 Login/AuthSession
- 恢复 multi-user SaaS
- 让 LLM 直接写 SQLite canonical state

### 验收标准
1. Required job 暴露稳定 aggregate status：`Askora CI / Required`
2. 支持 concurrency / cancel-in-progress / 合理缓存 / 合理 path filtering
3. 不允许 Required job 因 path skip 永久 pending
4. Optional tests 可独立运行但不阻塞 Required
5. Dependency audit 清理 asyncpg/redis/PyJWT/bcrypt 等 legacy 依赖

### 必须通过的测试
```bash
# 本地验证 CI workflow 结构
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci-required.yml'))"
# 所有 lint/typecheck 验证
cd apps/backend && ruff check && mypy app
cd apps/frontend && npm run build
```

---

## EXEC-058 — Required Gate & Main Protection Closure

### 前提条件
- EXEC-055 已 DONE
- EXEC-057 已 DONE
- EXEC-056 需要等待链 A 的 EXEC-046 DONE（可并行等待）

### 目标
完成 CI v2 最终闭环：
1. 建立稳定 `Askora CI / Required` 聚合状态
2. 证明六类 Required Gate 全部接通
3. 通过 GitHub Ruleset / Branch Protection 让失败状态真正阻止代码进入 `main`

### 六类 Required Gate
```text
1. Product Boundary
2. Backend Core
3. Local Data Integrity
4. Recovery & Rebuild
5. Local Web Chromium E2E（需等待 EXEC-056）
6. Quality & Security
```

### GitHub Branch Protection 配置
若当前 GitHub 工具权限不能修改 branch protection，输出：
```text
MANUAL_REPO_SETTING_REQUIRED
```
并给出精确配置内容。

---

## 核心原则

1. **权威优先级**：PRODUCT-POSITIONING > ADR > Spec > EXEC > Code
2. **不等待用户逐 EXEC 确认**：连续执行 054 → 055 → 057 → 058
3. **只在遇到 POSITIONING GAP / SPEC GAP 时停止**
4. **禁止为全绿降低 coverage 或扩大 skip**
5. **禁止将 Mock 当真实 Provider current availability**
6. **禁止恢复 multi-user SaaS / Login / AuthSession**
7. **禁止让 LLM 直接写 SQLite canonical state**
8. **优化目标**：正确性 > 数据安全 > 产品定位一致性 > 自动验证能力 > 可维护性 > 执行效率 > 历史兼容性

## 关键约束提醒

- **Chain B 可与 Chain A 并行**：两条链文件域无冲突
- **汇合点**：EXEC-058 需等待 EXEC-056（需要链 A 的 EXEC-046 DONE）
- **Chain B 内部**：EXEC-054 → EXEC-055 → EXEC-057 可完全独立推进，无需等待 Chain A
- **EXEC-056**：需要 EXEC-046 DONE + EXEC-055 DONE 才能启动

## 完成后输出

```text
ASKORA CHAIN B (CI V2) EXECUTION REPORT

1. EXEC-054 状态：DONE/BLOCKED
2. EXEC-055 状态：DONE/BLOCKED
3. EXEC-057 状态：DONE/BLOCKED
4. EXEC-058 状态：DONE/BLOCKED
5. 修改文件清单
6. Product Boundary 验证矩阵
7. Workspace/Material/Project/Delete/LLM ownership 证据
8. Ruff/MyPy/测试结果
9. SPEC GAP（如有）
10. GitHub branch protection 状态
11. CI_V2_DONE / CI_V2_PARTIAL
```
