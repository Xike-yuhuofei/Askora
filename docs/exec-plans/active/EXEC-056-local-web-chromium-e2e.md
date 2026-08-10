# EXEC-056 — Local Web Chromium E2E

> Status：FROZEN / BLOCKED_BY_DEPENDENCY_GATE  
> Governing：PRODUCT-POSITIONING、CI-*、QUAL-V1-*  
> Dependency：EXEC-055 DONE + EXEC-046 DONE  
> Next：EXEC-058

## Objective

建立 Askora v1 真正的产品级 Required E2E：Chromium 访问 loopback Local Server，使用隔离 AskoraData 和 SQLite，在不依赖真实 AI Key 的条件下验证核心 Local Web journey 与 restart persistence。

## Dependencies

- EXEC-055 DONE；
- UI-03 EXEC-046 DONE，避免在旧 routes/shell 上冻结新的浏览器 E2E；
- production-local startup 已稳定。

## Required Product Positioning

必须读取 Web UI、Local Web Application、启动体验、Chrome/Edge support、Workspace/Material/Learning Session、offline/local data sections。

## Required Specs

- `CI-500..503`
- `QUAL-V1-102/103/500`
- current UI contracts after UI-03
- Content Ingestion / Learning launch / Activity lifecycle contracts

## Current Reality

当前 frontend CI 仅有 Vitest + Vite build；没有真实浏览器 → Local Server → SQLite/Local Files 的 Required E2E。

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
docs/exec-plans/**
```

只允许测试基础设施、test hooks 和不改变产品语义的最小 testability 改动。

## Forbidden Changes

- 不通过 Electron/native shell 完成 v1 E2E；
- 不要求 Safari/Firefox matrix；
- 不依赖真实用户 API Key；
- 不把网络上的实时内容作为关键 fixture；
- 不直接操作 production SQLite 绕过真实 UI/API journey；
- 不为测试增加 demo-login/auth shortcut；
- 不在 test mode 使用用户真实 AskoraData。

## Implementation Tasks

1. 引入适合当前 frontend 的 Chromium E2E runner（优先 Playwright 或等价成熟方案）；
2. 测试启动独立 Local Server，绑定 ephemeral loopback port；
3. 为每次 run 创建临时隔离 AskoraData；
4. 使用 deterministic EPUB/PDF/Markdown/TXT fixture 中至少一种核心格式；
5. 验证 import 时 source 被复制进 Askora-managed data dir；
6. 验证 Workspace / Material / learning launch 的当前 canonical UI/API journey；
7. 持久化一项 durable learning state；
8. graceful stop Local Server；
9. 使用同一测试 AskoraData 重启 Local Server；
10. browser reconnect 后 durable state 仍存在；
11. 至少一个 partial pipeline failure / retry 场景在适用时可被 integration/E2E 验证；
12. CI artifact 只保留必要 screenshot/trace，不能泄露 secret/private fixture。

## Acceptance Criteria

- `E056-AC-001`：Chromium → loopback Local Server smoke PASS；
- `E056-AC-002`：无 Authorization token；
- `E056-AC-003`：测试不依赖 Redis/Postgres/Docker；
- `E056-AC-004`：测试不依赖真实 AI API key；
- `E056-AC-005`：source import copy semantics 可证明；
- `E056-AC-006`：核心 Local Web journey PASS；
- `E056-AC-007`：Local Server restart 后 durable state preserved；
- `E056-AC-008`：每个 E2E 使用独立临时 AskoraData；
- `E056-AC-009`：失败 artifact 不包含 secret / 私密用户数据；
- `E056-AC-010`：E2E 可在 GitHub-hosted runner deterministic 重复执行。

## Required Tests

- Chromium E2E；
- frontend unit/build；
- backend Required smoke；
- test isolation negative check；
- docs gate。

## Completion Report Format

报告：E2E runner、journey、test data isolation、restart evidence、artifact policy、CI command、commit SHA、`E056 DONE` 或 blocker。