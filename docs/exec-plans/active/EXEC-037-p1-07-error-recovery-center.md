# EXEC-037 — P1-07 Error Recovery Center

> Priority: P1 Reliable Private Product
> Status: FROZEN / ACTIVE
> Governing decision: ADR-0012
> Vertical Slice: P1-07 Error Recovery Center

## Objective

实现双入口、单合同、Owner Command 的统一恢复控制面，并满足 `P107-AC-001..009`。

## Dependencies

- 直接基线：`0f4ebb6` 及后续 durable transcript/policy-bound model dependency commit；
- 集成 gate：P1-02 model settings、P1-03 data recovery、P1-04 OCR owner action；
- UI-02C 可独立推进，但最终 activity/provider recovery E2E 必须在其 canonical route 上复验。

## Required specs

- `AGENTS.md`
- `docs/adr/ADR-0012-unified-recovery-control-plane.md`
- architecture state ownership/system/dependency specs
- `docs/specs/interfaces/error-contract.md`
- `docs/specs/interfaces/recovery-contract.md`
- API/persistence/schema version specs
- SYS01/SYS08 specs
- UI information/screen/data/visual/quality specs
- testing/security/observability/DoD specs
- `docs/specs/vertical-slices/p1-07-error-recovery-center.md`

## Allowed files

```text
docs/adr/ADR-0012-unified-recovery-control-plane.md
docs/adr/README.md
docs/document-inventory.md
docs/product-gap-register-p1-p2.md
docs/specs/** (P1-07 additive updates only)
docs/exec-plans/README.md
docs/exec-plans/active/EXEC-037-p1-07-error-recovery-center.md
docs/exec-plans/completed/EXEC-037-p1-07-error-recovery-center.md
docs/releases/p1-07-error-recovery-center.md
apps/backend/alembic/versions/<exec037_recovery>.py
apps/backend/alembic/versions/<exec037_integration_merge>.py
apps/backend/app/api/v1/recovery.py
apps/backend/app/api/v1/__init__.py
apps/backend/app/application/book_learning.py
apps/backend/app/contracts/recovery.py
apps/backend/app/core/database.py
apps/backend/app/core/exceptions.py
apps/backend/app/core/startup_diagnostics.py
apps/backend/app/infrastructure/outbox.py
apps/backend/app/infrastructure/recovery.py
apps/backend/app/main.py
apps/backend/app/models/__init__.py
apps/backend/app/models/ledger.py
apps/backend/app/orchestration/model_rendering.py
apps/backend/app/queries/recovery.py
apps/backend/app/queries/library.py
apps/backend/app/api/v1/workspace.py
apps/backend/app/services/documents/document_service.py
apps/backend/app/services/documents/processing_worker.py
apps/backend/app/services/llm/provider_errors.py
apps/backend/app/services/recovery.py
apps/backend/app/services/storage/local_storage.py
apps/backend/tests/**/test_*recovery*.py
apps/backend/tests/**/test_*error*.py
apps/backend/tests/**/test_*startup*.py
apps/backend/tests/integration/test_v03_adaptive_execution_loop.py
apps/backend/tests/integration/test_library_workspace_query.py
apps/frontend/electron/main.cjs
apps/frontend/electron/app-menu.cjs
apps/frontend/electron/app-menu-template.cjs
apps/frontend/electron/app-menu-template.test.cjs
apps/frontend/electron/preload.cjs
apps/frontend/electron/bootstrap-diagnostics.cjs
apps/frontend/index.html
apps/frontend/src/App.jsx
apps/frontend/src/api/client.js
apps/frontend/src/api/recovery.js
apps/frontend/src/api/workspace.js
apps/frontend/src/components/AppShell.css
apps/frontend/src/components/AppShell.jsx
apps/frontend/src/components/RecoveryIndicator.jsx
apps/frontend/src/pages/Settings.jsx
apps/frontend/src/pages/RecoveryCenter.jsx
apps/frontend/src/pages/RecoveryCenter.css
apps/frontend/src/pages/Library.jsx
apps/frontend/src/pages/StartupRecovery.jsx
apps/frontend/src/pages/StartupRecovery.css
apps/frontend/src/test/AppRoutes.test.jsx
apps/frontend/src/test/BootstrapDiagnostics.test.js
apps/frontend/src/test/Settings.test.jsx
apps/frontend/src/test/*Recovery*.test.jsx
apps/frontend/src/test/Library.test.jsx
apps/frontend/src/test/Csp.test.js
apps/frontend/src/test/client.test.js
```

`P107-AC-008` 的真实 Electron 200% zoom gate 要求自定义应用菜单保留标准
`resetZoom/zoomIn/zoomOut` 角色；因此允许纯菜单模板、最小接线及 Node 测试，不授权改变
外部链接、系统权限或产品导航语义。

## Forbidden changes

- central recovery writer 直接 patch owner state；
- generic raw DLQ replay、重置 attempt/history 或无限 retry；
- free-text/HTTP-status driven UI recovery；
- secret/path/prompt/provider body/SQL/traceback leakage；
- system failure 写入 learner negative evidence 或完成 activity；
- placeholder/disabled action 冒充 P1-02/03/04 集成完成；
- 修改本目标之外的 P1 产品语义。

## Implementation tasks

1. 落地 strict recovery contracts、stable catalog 与完整 ERROR-002 envelope。
2. 新增 append-only operational incident/action audit migration、repository/query。
3. 分类 provider failure，并在失败事务外安全记录/成功后 resolve；证明无 learning side effect。
4. 投影 document/outbox issues，实现 SYS01 allowlisted retry/reinspect 与 immutable DLQ lineage。
5. 接入 P1-02/03/04 owner actions，无实现时保持 gate 未完成；provider issue 必须回到关联的
   canonical activity，missing-file 不得用 query string 冒充 owner replacement command。
6. 实现 `/settings/recovery`、Settings 入口、全局 indicator 和无障碍状态。
7. 实现 Electron bootstrap diagnostic channel、single-flight retry 与 startup shell。
8. 覆盖 contract/architecture/migration/SQLite/PostgreSQL/restart/security/frontend/browser/desktop tests。
9. 全量门禁、release evidence、更新 gap register、归档并独立提交。

## Required tests

```bash
cd apps/backend
pytest tests/contracts/test_recovery_contract.py tests/architecture/test_recovery_boundary.py
pytest tests/integration/test_recovery_center.py tests/integration/test_recovery_migration.py
pytest tests/recovery/test_recovery_restart.py tests/security/test_recovery_redaction.py
pytest
ruff check app tests
mypy app
alembic check

cd apps/frontend
npm test -- --run
npm run build
npm audit --audit-level=high

cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

真实 gate：Electron backend missing/migration/db failure；真实浏览器 provider failure、document recovery、
reload/restart；至少一次实际配置 provider 的 controlled recovery。Mock-only 不能关闭该 gate。

## Completion report

必须分别报告 Engineering、Policy/Ownership、Security/Privacy、Product Usability、Learning Evidence；
列出 dependency commits、migration/forward-fix、稳定 code、owner action、自动/真实测试、未完成项、
SPEC GAP 与并发工作区保护情况。
