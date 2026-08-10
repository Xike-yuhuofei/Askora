# Askora 链 A：UI-03 前端交互架构重构（EXEC-043 → 044 → 045 → 046）

## 角色
你是 Askora 项目的前端架构师、交互工程师和执行代理。

## 最终目标
> 基于已完成的 no-auth LocalOwner baseline（EXEC-047～051 DONE），按依赖顺序连续执行 EXEC-043 → EXEC-044 → EXEC-045 → EXEC-046，完成 UI-03 交互架构收口，将 Askora 前端收敛到 Today/Learning/Library 三大域 + 无账号语义。

## 执行依赖
```
EXEC-043 DONE  →  EXEC-044 DONE  →  EXEC-045 DONE  →  EXEC-046 DONE
```
每个 EXEC 必须在前一个完成并归档后才能启动。

## 开始前必须读取
```text
AGENTS.md
docs/product/PRODUCT-POSITIONING.md
docs/adr/ADR-0014-user-job-driven-interaction-architecture.md
docs/adr/ADR-0015-local-single-user-identity-without-authentication.md
docs/specs/ui/interactive-element-system.md
docs/specs/ui/information-architecture.md
docs/specs/ui/screen-contracts.md
docs/specs/ui/visual-system.md
docs/specs/ui/quality-and-migration.md
docs/specs/vertical-slices/ui-03-interactive-element-system-refactor.md
docs/exec-plans/active/EXEC-043-ui-03a-shell-routes-learning-domain.md
docs/exec-plans/active/EXEC-044-ui-03b-today-primary-hierarchy.md
docs/exec-plans/active/EXEC-045-ui-03c-library-progressive-disclosure.md
docs/exec-plans/active/EXEC-046-ui-03d-settings-legacy-release-closure.md
```

---

## EXEC-043 — UI-03A Shell, Routes and Learning Domain

### 目标
把全局产品导航收敛为 **Today / Learning / Library**，建立 Learning L1 facets，将旧 Goals/Path/Evidence/History routes 无副作用迁移到 `/learning/**`。

### 允许修改的文件
```text
apps/frontend/src/App.jsx
apps/frontend/src/router.jsx
apps/frontend/src/components/AppShell.jsx
apps/frontend/src/components/Sidebar.jsx
apps/frontend/src/components/LearningNavigation.*   # 可新增
apps/frontend/src/components/LearningShell.*        # 可新增
apps/frontend/src/pages/Goals.jsx / GoalDetail.jsx / GoalEditor.jsx
apps/frontend/src/pages/LearningPath.jsx
apps/frontend/src/pages/Evidence.jsx
apps/frontend/src/pages/History.jsx
apps/frontend/src/pages/Learning.jsx               # 可新增
apps/frontend/src/pages/Learning.css              # 可新增
apps/frontend/src/test/**route** / **Sidebar** / **Learning**
docs/exec-plans/ 中的 EXEC-043 相关文件
```

### 禁止修改
- backend/domain/API/schema
- Today Quick Start 重设计
- Library 批量/OCR 重设计
- Settings 业务页面重构
- TeachingAction/LearnerState/Plan 语义
- 删除 `/quick/:sessionId` 兼容 workspace
- 恢复 Login/ProtectedRoute/AuthProvider/AuthSession
- 将 Workspace 建模为 Tenant/Organization
- 通过 Learning shell 默认聚合跨 Workspace 的 Goal/Evidence/History/LearnerState
- 让 Learning Project 成为 Material 学习的强制门禁

### 验收标准（11 项）
1. Sidebar/Product Nav 只有 Today/Learning/Library；Settings/Recovery 明确 utility 分组
2. Learning 四 facets 可达且 facet navigation 无业务写入
3. Goal create/detail/edit/draft 在新 route 行为不变
4. legacy routes 保留参数，只 redirect
5. `/welcome` 和 explicit deep-link preservation 不回归
6. 360/768/1024/1440 下 navigation 可操作；keyboard focus 可见
7. 无 backend/public schema change
8. ADR-0015 no-auth LocalOwner baseline 不回归
9. Workspace 仍是高层学习数据隔离边界，不出现 Tenant/Organization 语义
10. Learning Project 仍为可选组织单位，不阻止直接从 Material 进入学习

### 必须通过的测试
```bash
cd apps/frontend
npm test -- --run
npm run build
npm audit --audit-level=high

cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

### 完成后
1. 将 EXEC-043 文件从 `active/` 移动到 `completed/`
2. 状态标记改为 `DONE`
3. 独立 commit 归档

---

## EXEC-044 — UI-03B Today Primary Hierarchy

### 前提条件
- EXEC-043 已 DONE 并归档
- `/today` 与 `/learning/**` routes 当前绿色
- P1-06 onboarding completion/default-entry 行为保持绿色

### 目标
把 `/today` 从"canonical activity + compatibility quick-start dashboard"收敛为 **当前 Workspace 内的 daily learning orchestrator**：
- canonical current/next activity 是 sole Primary Task
- Goal/reason/validation 是 supporting information
- upcoming/review 是 secondary
- Quick Start 只在缺少 canonical activity 时 fallback

### 禁止事项
- 不得跨 Workspace 混合 Learner State/Evidence/Activity
- 不得将 Learning Project 变成开始学习的门禁
- 用户仍可直接基于 Material 进入学习

### 验收标准
1. Today primary task hierarchy 建立并验证
2. canonical current/next activity 是唯一 Primary Task
3. Quick Start 作为 fallback，不抢占 Primary Task 位置
4. Workspace scope 隔离不回归
5. Material 直接学习路径不因 Today OR 重构被门禁化

### 必须通过的测试
```bash
cd apps/frontend
npm test -- --run
npm run build
```

### 完成后
1. 将 EXEC-044 文件从 `active/` 移动到 `completed/`
2. 状态标记改为 `DONE`

---

## EXEC-045 — UI-03C Library Progressive Disclosure

### 前提条件
- EXEC-044 已 DONE 并归档

### 目标
把 `/library` 从 always-visible management console 收敛为 **当前 Workspace 内的 Material 管理与知识上下文界面**：
```
Current Workspace
→ Search / Filter / Import
→ Material List
→ Selected Material / Knowledge Context
→ Contextual Actions
```
批量动作只在 selection 后出现；duplicate、metadata、reinspection 等 advanced actions 按对象上下文暴露。

### 禁止事项
- 不改变 P1-04A/B/C 资料管理、去重、metadata、安全和 owner command 语义
- 不引入跨 Workspace Material 聚合
- 不改变 Material ↔ Learning Project 多对多关系

### 验收标准
1. Library 呈现 Workspace-scoped Material 管理与知识上下文
2. Progressive disclosure：批量动作选择后出现，advanced actions 按上下文暴露
3. Material 仍属于 Workspace，不形成跨 Workspace 聚合
4. Direct Material learning 路径不受影响

### 必须通过的测试
```bash
cd apps/frontend
npm test -- --run
npm run build
```

---

## EXEC-046 — UI-03D Settings Hierarchy, Legacy Cleanup and Release Closure

### 前提条件
- EXEC-045 已 DONE 并归档
- EXEC-051 已 DONE（Authentication Removal release evidence PASS）

### 目标
完成 UI-03 最终闭环：
1. Settings 从 giant control grid 重构为 hierarchical category navigation
2. 保持 模型/BYOK、本地数据治理、Backup/Export、Recovery Center、诊断与本地运行安全 的真实语义
3. 清理无使用者的 legacy chat-first UI
4. 执行完整 responsive/accessibility/security/E2E gate 并形成 release evidence

### 关键约束
- 账号、密码、AuthSession、Recovery Kit、Logout、Delete Account 等旧 SaaS/账号语义 **不得重新引入**
- 以 EXEC-047～051 已完成的 no-auth LocalOwner baseline 为前提

### 必须通过的测试
```bash
cd apps/frontend
npm test -- --run
npm run build
npm audit --audit-level=high

cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

---

## 核心原则

1. **权威优先级**：PRODUCT-POSITIONING > ADR > Spec > EXEC > Code
2. **不等待用户逐 EXEC 确认**：连续执行 043 → 044 → 045 → 046
3. **只在遇到 POSITIONING GAP / SPEC GAP 时停止**
4. **禁止恢复 Login/AuthSession/ProtectedRoute/AuthProvider**
5. **禁止将 Workspace 建模为 Tenant/Organization**
6. **禁止让 Learning Project 成为 Material 学习的强制门禁**
7. **优化目标**：正确性 > 数据安全 > 产品定位一致性 > 自动验证能力 > 可维护性 > 执行效率 > 历史兼容性

## 完成后输出

```text
ASKORA CHAIN A (UI-03) EXECUTION REPORT

1. EXEC-043 状态：DONE/BLOCKED
2. EXEC-044 状态：DONE/BLOCKED
3. EXEC-045 状态：DONE/BLOCKED
4. EXEC-046 状态：DONE/BLOCKED
5. 修改文件清单
6. 测试结果（每个 EXEC 的 targeted tests）
7. SPEC GAP（如有）
8. 下一解锁的 EXEC
```
