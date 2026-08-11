# EXEC-056 — Local Web Chromium E2E

> Status：FROZEN / BLOCKED_BY_DEPENDENCY_GATE  
> Governing：PRODUCT-POSITIONING、CI-*、QUAL-V1-*  
> Dependency：EXEC-055 DONE + EXEC-046 DONE  
> Next：EXEC-058

## Objective

建立 Askora v1 真正的产品级 Required E2E：Chromium 访问 loopback Local Server，使用隔离 AskoraData 和 SQLite，在不依赖真实 AI Key 的条件下验证核心 Local Web journey、Workspace isolation、Material 直接学习路径与 restart persistence。

E2E 必须验证的是 PRODUCT-POSITIONING 中真实的个人学习产品，而不是旧 service-mode / account / global-library 产品：单用户、无登录、当前 Workspace 内管理 Material、Project 可选、Material 可直接开始学习、原始资料由 Askora copy 管理、Durable Data 在 Local Server restart 后保持。

## Dependencies

- EXEC-055 DONE；
- UI-03 EXEC-046 DONE，避免在旧 routes/shell 上冻结新的浏览器 E2E；
- production-local startup 已稳定。

## Required Product Positioning

必须读取 Web UI、Local Web Application、启动体验、Chrome/Edge support、Workspace/Project/Material、Learning Session、Import copy、offline/local data、Backup/Derived Data sections。

至少冻结以下 E2E 产品事实：

- browser → loopback Local Server；
- no login / no Authorization token；
- Workspace 是高层数据隔离边界；
- Library/Material 默认不跨 Workspace；
- Material 必须属于 Workspace；
- Learning Project 是可选组织单位；
- 无 Project 时仍可直接基于 Material 开始 Learning Session；
- Import = ingest + copy；
- restart 后 Durable Data preserved；
- E2E 不依赖 Redis/Postgres/Docker/真实 AI Key。

## Required Specs

- `CI-500..503`
- `QUAL-V1-102/103/500`
- current UI contracts after UI-03
- Content Ingestion / Workspace / Material / Learning launch / Activity lifecycle contracts
- LocalOwner / no-auth contract

## Current Reality

当前 frontend CI 仅有 Vitest + Vite build；没有真实浏览器 → Local Server → SQLite/Local Files 的 Required E2E。

如果只验证单一默认 Workspace 的 happy path，仍不足以证明最新 Product Positioning：必须至少构造两个隔离 Workspace，证明 Material/learning state 不发生默认跨 Workspace 泄漏，并证明 Learning Project 不是直接学习的门禁。

## Allowed Files

```text
apps/frontend/**
apps/backend/tests/e2e/**
apps/backend/tests/fixtures/**
apps/backend/scripts/**
.github/**
package*.json
README.md
docs/specs/quality/**
docs/planning/**
```

只允许测试基础设施、test hooks 和不改变产品语义的最小 testability 改动。

## Forbidden Changes

- 不通过 Electron/native shell 完成 v1 E2E；
- 不要求 Safari/Firefox matrix；
- 不依赖真实用户 API Key；
- 不把网络上的实时内容作为关键 fixture；
- 不直接操作 production SQLite 绕过真实 UI/API journey；
- 不为测试增加 demo-login/auth shortcut；
- 不在 test mode 使用用户真实 AskoraData；
- 不建立 Global Material Library / cross-Workspace default search 来简化 fixture；
- 不要求先创建 Learning Project 才能从 Material 开始学习；
- 不把 Workspace 当 Tenant / Account；
- 不通过测试专用后门直接写 canonical learning state；
- 不把 OCR、Safari/Firefox、native desktop、real-provider 变成本 Required E2E 的阻塞项。

## Implementation Tasks

1. 引入适合当前 frontend 的 Chromium E2E runner（优先 Playwright 或等价成熟方案）。
2. 测试启动独立 Local Server，绑定 ephemeral loopback port。
3. 为每次 run 创建临时隔离 AskoraData。
4. 冷启动直接进入 local product flow，证明无 Login/Auth redirect、无 Authorization token requirement。
5. 创建或准备 Workspace A 与 Workspace B，确保两者使用同一 LocalOwner 但数据 scope 独立。
6. 在 Workspace A 使用 deterministic EPUB/PDF/Markdown/TXT fixture 中至少一种核心格式执行真实 Import。
7. 验证 import 时 source 被复制进 Askora-managed data dir，后续 journey 不依赖原始导入路径持续存在。
8. 验证 Workspace A 中可发现该 Material；切换 Workspace B 后默认 Library/search/learning surface 不出现 Workspace A Material，也不泄漏其学习状态。
9. 回到 Workspace A，在 **不创建 Learning Project** 的前提下，直接从 Material 走当前 canonical learning launch / Learning Session journey；不得出现“必须先创建 Project”门禁。
10. 若当前 canonical UI 已支持 Project 关系管理，再补充“同一 Material 可关联 Project、解除关系不删除 Material”的 E2E；若 UI 尚无此入口，由 EXEC-054 domain/integration tests 负责，不得为本 E2E 临时新增产品功能。
11. 持久化一项 Durable learning state（例如 Goal/Evidence/History/Session 中当前 contract 明确的一项）。
12. graceful stop Local Server。
13. 使用同一测试 AskoraData 重启 Local Server。
14. browser reconnect 后 Workspace/Material/source file/所选 Durable learning state 仍存在，Workspace 隔离仍成立。
15. 至少一个 partial pipeline failure / retry 场景在适用时可被 integration/E2E 验证；失败不得破坏已保存 SourceFile/Durable Data。
16. CI artifact 只保留必要 screenshot/trace，不能泄露 secret/private fixture。

## Acceptance Criteria

- `E056-AC-001`：Chromium → loopback Local Server smoke PASS。
- `E056-AC-002`：无 Login/Auth redirect、无 Authorization token。
- `E056-AC-003`：测试不依赖 Redis/Postgres/Docker。
- `E056-AC-004`：测试不依赖真实 AI API key。
- `E056-AC-005`：source import copy semantics 可证明；移除/失效原始导入路径后 Askora-managed source 仍可使用。
- `E056-AC-006`：核心 Local Web journey PASS。
- `E056-AC-007`：Local Server restart 后 Durable state preserved。
- `E056-AC-008`：每个 E2E 使用独立临时 AskoraData。
- `E056-AC-009`：失败 artifact 不包含 secret / 私密用户数据。
- `E056-AC-010`：E2E 可在 GitHub-hosted runner deterministic 重复执行。
- `E056-AC-011`：至少两个 Workspace 的 Material/learning surfaces 默认隔离；不存在跨 Workspace Global Material Library fallback。
- `E056-AC-012`：无 Learning Project 的 Material 可通过真实 UI/API canonical path 直接开始 Learning Session。
- `E056-AC-013`：Workspace 在 E2E 中表现为本地学习数据边界，不出现 Tenant/Account 语义。
- `E056-AC-014`：restart 后 Workspace isolation 与 Askora-managed SourceFile ownership 仍成立。

## Required Tests

- Chromium E2E；
- no-login / no-token cold start；
- Workspace A/B isolation journey；
- direct-Material learning without Project；
- import-copy + original-path independence；
- restart persistence；
- frontend unit/build；
- backend Required smoke；
- test isolation negative check；
- docs gate。

## Completion Report Format

报告：E2E runner、journey、Workspace isolation、direct-Material learning、source-copy evidence、test data isolation、restart evidence、artifact policy、CI command、commit SHA、`E056 DONE` 或 blocker。
