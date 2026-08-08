# Askora UI-01 — Learning Shell and Compatibility Tutor Workspace Completion Report

> Status：DONE
>
> Engineering Gate：PASS
>
> Policy Correctness / Ownership Regression Gate：PASS
>
> Learning Evidence Gate：LEARNING_EVIDENCE_INSUFFICIENT
>
> Evidence Date：2026-08-08
>
> Implementation Commit：与本报告同一原子本地提交；hash 以 Git 历史与交付回执为准

## 1. 结论

冻结的 UI Redesign Spec Set、UI-01 Vertical Slice 与 EXEC-015 已完成。Askora 的默认入口由 chat-first 页面迁移为 learning-loop-first Shell；现有 dialog session 只作为明确标注的“兼容快速学习”保留。当前没有 canonical current-user Goal/Plan/Activity Query 或 activity↔session link，因此 UI 不展示虚构目标、计划、掌握结论，也不把 `activityId` 当 `sessionId`。

本报告只证明 UI-01 的工程、接口、ownership 与可访问性门禁通过，不证明新 UI 或兼容导师工作台改善真人学习效果：

```text
LEARNING_EVIDENCE_INSUFFICIENT
```

## 2. Frozen Contract / Implementation

- UI contract：`docs/specs/ui/README.md` 及同目录五份冻结规范；
- Vertical Slice：`docs/specs/vertical-slices/ui-01-learning-shell-workspace.md`；
- execution contract：`docs/exec-plans/completed/EXEC-015-ui-01-learning-shell-workspace.md`；
- Today Query：`GET /api/v1/workspace/today?timezone=<IANA timezone>`；
- canonical routes：`/today`、`/history`、`/settings`、`/learn/:activityId`；
- compatibility route：`/quick/:sessionId`；
- deferred UI-02 routes：`/goals`、`/path`、`/library`、`/evidence` 只显示诚实不可用状态。

## 3. Data / Ownership Evidence

Today response 使用 strict immutable v1.0 contract、timezone-aware `generated_at`、correlation ID 与 `Cache-Control: private, no-store`，并绑定当前授权用户。

| Source | UI-01 behavior | Boundary |
|---|---|---|
| SYS06 | `MISSING / OWNER_QUERY_UNAVAILABLE` | 不扫描无法安全绑定当前用户的 plan/activity records |
| SYS07 | 展示 latest 且 `next_due_at <= now` 的 due candidates | 只读，不修改 ReviewSchedule |
| SYS03 | 无 current activity 时 `NOT_APPLICABLE / NO_CURRENT_ACTIVITY` | 不任意选择 mastery entry |
| LEGACY_COMPATIBILITY | 当前用户最近 dialog sessions | 明确标记兼容来源，不冒充 LearningActivity |

`/quick/:sessionId` 继续使用既有 dialog detail/messages/send ownership check 与 RichMessage；前端不从 legacy hint level、strategy、turn count 或 mastery 字段推导 canonical TeachingAction、evidence 或 learner state。

## 4. UI / Accessibility Evidence

- 一级导航固定为今天、学习目标、学习路径、资料库、学习证据、历史记录、设置，不含“对话学习”；
- `/`、`/profile`、`/knowledge`、`/account` 无副作用跳转至 canonical route；
- Today 覆盖 loading、partial、empty、error、unauthorized 与兼容创建失败状态；
- History 支持空态、错误态、只读列表与恢复已有会话；
- Settings 明确“退出只清除本地令牌/缓存，不删除服务端学习数据”；
- mobile drawer 具有 accessible name、焦点约束、Escape close 与 focus return；
- reduced-motion 样式关闭非必要动画；icon-only control 均有 accessible name；
- 桌面长消息使用内部滚动区，composer 与 context inspector 保持可见；移动端保持单列自然文档流。

真实浏览器连接本地前后端验收结果：

| Viewport | Result |
|---|---|
| 1440×900 | Today 和三栏工作台可用；工作台 body 不滚动、消息区内部滚动 |
| 1024×768 | Today/工作台无横向溢出，composer 与 inspector 可见 |
| 768×1024 | responsive drawer 初始隐藏；打开后首链接获焦；Escape 关闭并返回触发器 |
| 360×800 | Today/工作台单列，无页面横向溢出；composer/inspector 可访问 |

真实页面还验证了 `/learn/activity-ui01-check` 仅显示不可启动状态与“返回今天”，History/Settings 可读取，浏览器控制台无 warning/error。验收没有发送导师消息、没有创建兼容会话。

## 5. EXEC-015 Acceptance Matrix

| AC | Result | Evidence |
|---|---|---|
| EXEC015-AC-001 | PASS | UI01-VSLICE-AC-001..012 全部映射至本报告与测试 |
| EXEC015-AC-002 | PASS | strict v1.0、timezone/current-user/private-no-store integration test |
| EXEC015-AC-003 | PASS | SYS06/SYS07/legacy source status 与 architecture boundary tests |
| EXEC015-AC-004 | PASS | Login render/phone validation/auth 与 explicit dev auto-login tests |
| EXEC015-AC-005 | PASS | 七项导航、legacy redirects、unknown recovery tests |
| EXEC015-AC-006 | PASS | 真实兼容 session history/RichMessage 页面与 ownership regression |
| EXEC015-AC-007 | PASS | `/learn/:activityId` identity 分离与安全不可启动页面 |
| EXEC015-AC-008 | PASS | component states + 1440/1024/768/360 browser acceptance |
| EXEC015-AC-009 | PASS | frontend/backend/docs/diff gates 见下节 |
| EXEC015-AC-010 | PASS | 无迁移/新依赖/cross-owner write/blocking SPEC GAP；learning evidence 不变 |

## 6. Verification

| Command / check | Result |
|---|---|
| backend targeted workspace suites | 6 passed |
| `uv run pytest` | 255 passed, 1 protected real-model test skipped |
| `uv run ruff check app tests` | PASS |
| `uv run mypy app --no-error-summary` | PASS；仅既有 untyped-body notes |
| `uv run black --check app/contracts/workspace.py app/queries/workspace.py` | PASS；本 Slice 新增后端文件已格式化 |
| `uv run alembic check` | PASS；No new upgrade operations detected |
| `npm test -- --run` | 9 files / 31 tests passed |
| `npm run build` | PASS |
| `npm audit --audit-level=high` | 0 vulnerabilities |
| real browser responsive/keyboard/console check | PASS |
| `python3 .github/workflows/check_docs.py` | PASS（归档后） |
| `git diff --check` | PASS |

Pytest 输出有 4 条 deprecation warning；其中 workspace 非法时区测试触发了既有 `ValidationInputError` 的 Starlette 422 常量 warning。没有 warning 被隐藏或通过弱化测试处理。

额外执行 repo-wide `check_black_baseline.py` 时仍返回非零：`app/api/v1/dev_auth.py`、`app/services/auth/demo_user.py`、`tests/unit/test_dev_auto_login.py` 三份 HEAD 中既有文件不符合 Black，且均不在 EXEC-015 Allowed Files；本次没有越界格式化或扩大 ignore/baseline。该既有门禁债务不影响上表 EXEC-015 明确要求的 pytest/ruff/mypy/alembic/frontend/docs/diff gates，但不能被描述为 repo-wide Black PASS。

## 7. Deferred Scope / Retirement

- canonical Goal/Plan/Activity current-user query、创建/确认命令和 activity↔session link 留待后续冻结 Slice；
- `/quick/:sessionId` 在 canonical activity start/link 全路径可用、旧 session 已迁移或明确只读、相应回归完成后才能退休；
- UI-02 数据页、Focus、dark theme、knowledge map 与 evidence profile 不属于 UI-01；
- 本 Slice 无 DB migration、无 production dependency、无公共教学策略语义变化。
- repo-wide Black baseline 仍需后续授权任务格式化上述 3 份既有开发自动登录文件。

## 8. SPEC GAP

```text
SPEC GAP: none
```

缺失的 activity link 已在冻结 Slice 中被明确设计为不可启动状态，因此不是实现期未决策缺口。

## 9. Final Status

```text
Status: DONE
Engineering Gate: PASS
Policy Correctness / Ownership Regression Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```
