# XIK-176 CONFORMANCE REPORT

> Verify and close v1 Product Positioning conformance on current `main`
> Independent verification task (Architecture / Product Conformance)

---

## STATUS

**PASS / READY_FOR_ACCEPTANCE**

- `BASE_COMMIT`: `2e2e27885799f64c24cae705969cbaf99143f04d` (origin/main at start)
- `FINAL_COMMIT`: `55b26b0` (`fix(conformance): close v1 product positioning gaps on main (XIK-176)`)

---

## PRODUCT POSITIONING CONFORMANCE MATRIX

| 领域 | 要求 | 当前实现 | 状态 |
|---|---|---|---|
| Runtime | Local Web + loopback + SQLite 默认、无 Docker/Redis/PostgreSQL/JWT 前置 | `main.py` loopback-only；`config.py` 默认 `sqlite+aiosqlite:///{data_dir}/askora.db`；Redis 仅可选降级（try/except） | PASS |
| Identity | No Login / LocalOwner，无 auth 路由注册 | `main.py` 无 auth/account/dev_auth 路由；工作区依赖经 `get_default_workspace`/`get_current_owner_projection` 解析 LocalOwner | PASS |
| Workspace | 持久化 Workspace/Project/Session 聚合，默认 Workspace 确定性迁移 | `Workspace/LearningProject/ProjectMaterial/LearningSession/SourceFile` 模型 + `WorkspaceRepository` 幂等 bootstrap（EXEC-062/063 已验） | PASS |
| Material | Workspace 归属 + managed SourceFile copy | `UserDocument.workspace_id`；`upload_document` 经 `LocalFileStorage` 写入托管副本 | PASS |
| Retrieval | 显式 RetrievalScope（workspace_id 必填） | SYS02 `RetrievalScope` + `rag_service`/`library_management` 强制 workspace_id（EXEC-063 隔离测试 PASS） | PASS |
| Evidence | Workspace 隔离 | LearnerEvidence 写路径 workspace_id 必填（EXEC-062 AC-009 fail-closed）；读路径本次修复 | PASS |
| Mastery | Workspace projection | `MasteryEstimateRecord.workspace_id`；投影/失效按 workspace 隔离 | PASS |
| Review | Workspace schedule | `ReviewScheduleRecord.workspace_id`；schedule 仅用同 workspace 证据 | PASS |
| Delete | 普通删除进 Trash、可恢复；物理删除仅 Data Control | `MaterialLifecycleService.trash`（不删文件）+ Data Control DOCUMENT erasure（EXEC-065 已验） | PASS |
| CI | Required gates 全绿 | backend-tests `-m required` 498 pass；ruff/black/mypy 绿；migration roundtrip 绿 | PASS |

---

## IMPLEMENTATION DRIFT FIXED

1. **`WorkspaceTodayQueryService` 读路径未按 workspace 隔离**（GAP-V1-001/002/004 残留）
   `app/queries/workspace.py` 的 `_latest_goals`、`_latest_mastery_records`、`_knowledge_labels`、`_load_review_due`、`_load_recent_sessions` 原先仅按 `user_id`/`pseudonym_id` 过滤，未按 `workspace_id` 过滤，违反 EXEC067-AC-004（learner evidence/mastery/state/review 不可跨 Workspace 混流）。已为 `WorkspaceTodayQueryService` 增加必填 `workspace_id` 参数，并在全部 5 个内部查询中按精确 Workspace 过滤。

2. **`/goals`、`/path`、`/evidence`、`/today` 端点未解析默认 Workspace**
   `app/api/v1/workspace.py` 这四个读端点原先未注入 `get_default_workspace`，直接构造 owner-global 查询。已注入默认 Workspace 依赖并将 `workspace_id` 传入查询服务（与已正确 scoped 的 `/library`、`/knowledge-map` 保持一致）。

3. **读路径缺少 workspace 隔离 / 必填测试**
   新增 `tests/product_boundary/test_workspace_read_path_isolation.py`，覆盖同 LocalOwner 不同 Workspace 下 evidence/mastery/review/session 完全隔离，以及读查询缺少 workspace_id 时 fail-closed。两个测试均标记 `@pytest.mark.required` 进入 Required CI 门槛。

---

## FILES CHANGED

```text
apps/backend/app/api/v1/workspace.py                         (modified)
apps/backend/app/queries/workspace.py                        (modified)
apps/backend/tests/integration/test_workspace_product_views.py (modified, workspace_id fixtures)
apps/backend/tests/integration/test_workspace_today_query.py  (modified, workspace_id fixtures)
apps/backend/tests/product_boundary/test_workspace_read_path_isolation.py (new)
```

5 files changed, +261 / -16.

未纳入提交（先前遗留、与本任务无关）：`preview/learning-message-system.html` 及若干 untracked 文档/目录。

---

## MIGRATION

- **Alembic head**: 单头 `x174e0e0a002`（XIK-174 / EXEC-065）
- **Fresh migration**: `alembic upgrade head` 成功（空库 → 最新 schema）
- **Legacy migration**: `test_sqlite_migration_gate.py::test_legacy_sqlite_fixture_migrates_to_head` 及 `test_exec062` legacy→default workspace backfill PASS
- **Roundtrip**: `upgrade head → alembic check（无新操作）→ downgrade base → upgrade head` 全部成功
- 本次改动未新增迁移（读路径 scoping 复用既有 workspace_id 列）

---

## TEST RESULTS

| command | result |
|---|---|
| `pytest tests/ -m required`（Required CI 等价） | **498 passed, 3 skipped, 65 deselected** |
| `pytest`（全量本地） | **560 passed, 6 skipped** |
| `ruff check app tests` | All checks passed |
| `black --check app tests` | All done, 378 files unchanged |
| `mypy app` | Success, no issues (200 source files) |
| `alembic upgrade/check/downgrade/upgrade` | Success, single head |
| 迁移/隔离/生命周期专项 | 53 passed, 2 skipped（EXEC-062/063/065 + migrations） |

---

## ACCEPTANCE

- **Runtime**: PASS —— 默认 SQLite、loopback-only、无 auth 路由、Redis 可选降级、无 Docker/PostgreSQL/JWT 前置
- **Workspace isolation**: PASS —— 读写路径均 workspace scoped；新增读路径隔离测试
- **Retrieval isolation**: PASS —— SYS02 RetrievalScope 强制 workspace_id；EXEC-063 "A cannot search B" 通过
- **Learner isolation**: PASS —— evidence/mastery/review 写路径 fail-closed + 读路径本次闭合
- **Material lifecycle**: PASS —— Trash/Restore/Permanent Delete 语义符合；EXEC-065 通过
- **CI**: PASS —— Required 测试集、静态检查、migration roundtrip 全绿

---

## SPEC GAP

None（本次修复在既有 frozen Spec/ADR 边界内，未改变 Teaching Policy、mastery 算法、retrieval ranking 或状态所有权）。

## POSITIONING GAP

None（未修改 Product Positioning，未引入新能力，未扩大 Scope）。

---

## FINAL VERDICT

**XIK-176 READY_FOR_ACCEPTANCE**

- 所有 Conformance Matrix 项 PASS
- Required CI PASS
- 无未解决 Positioning Gap