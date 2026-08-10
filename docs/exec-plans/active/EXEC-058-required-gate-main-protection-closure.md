# EXEC-058 — Required Gate & Main Protection Closure

> Status：FROZEN / BLOCKED_BY_DEPENDENCY_GATE  
> Governing：PRODUCT-POSITIONING、CI-*、QUAL-V1-*  
> Dependency：EXEC-056 DONE + EXEC-057 DONE  
> Next：CI v2 Release Evidence / archive

## Objective

完成 CI v2 最终闭环：建立稳定 `Askora CI / Required` 聚合状态，证明六类 Required Gate 全部接通，并通过 GitHub Ruleset / Branch Protection 让失败状态真正阻止代码进入 `main`。

## Dependencies

- EXEC-056 Local Web Chromium E2E DONE；
- EXEC-057 Workflow / Quality / Supply-chain DONE；
- 当前 `main` 无未解决 blocking SPEC GAP；
- Required commands 在本地/CI runner 均有当前证据。

## Required Product Positioning

必须读取 PRODUCT-POSITIONING 全文，并以产品边界、数据正确与可恢复、可解释与可测试、本地单机简单性作为最终判断顺序。

## Required Specs

- `CI-950..952`
- `CI-AC-001..015`
- `QUAL-V1-500..502`
- Definition of Done retained Engineering / Policy / Learning Evidence separation

## Current Reality

当前 `main` branch protection 关闭，Required status contexts 为空；即使 workflow 失败也不能构成 merge gate。

## Allowed Files

```text
.github/**
docs/specs/quality/**
docs/releases/**
docs/exec-plans/**
docs/document-inventory.md
README.md
```

若需要 GitHub repository settings / Ruleset API，允许使用仓库管理权限执行；不得通过修改产品代码完成本任务。

## Forbidden Changes

- 不通过把失败 job 改 `continue-on-error` 伪造 aggregate green；
- 不将 Optional PostgreSQL/Docker/real-provider compatibility 接入 Required aggregate；
- 不以 branch protection 无权限为由宣称 DONE；
- 不删除失败测试换取 merge gate；
- 不让 skipped path-aware job 导致 Required status pending；
- 不把 Engineering Gate PASS 宣称为学习效果已验证。

## Implementation Tasks

1. 建立稳定 job/status：`Askora CI / Required`；
2. aggregate 必须覆盖：Product Boundary、Backend Core、Local Data Integrity、Recovery & Rebuild、Local Web E2E、Quality & Security；
3. 对 path-aware skip 建立明确 success/neutral aggregation semantics；
4. 运行 Required workflow 并保存当前成功证据；
5. 人为制造或使用安全 test branch 验证任一 Required child failure 会使 aggregate fail；
6. 配置 `main` GitHub Ruleset / Branch Protection：合并前要求 `Askora CI / Required` success；
7. 禁止直接绕过 Required status 的普通 merge path；具体 admin/bypass policy 必须显式记录；
8. 验证 Optional workflow failure 不影响 Required aggregate；
9. 更新 CI docs / document inventory / release evidence；
10. 将 EXEC-052～058 完成后归档并记录最终 CI v2 topology。

## Acceptance Criteria

- `E058-AC-001`：存在稳定 `Askora CI / Required` status；
- `E058-AC-002`：六类 Required Gate 均被 aggregate覆盖；
- `E058-AC-003`：任一 Required child failure → aggregate failure；
- `E058-AC-004`：Optional failure → aggregate仍按 Required children 判定；
- `E058-AC-005`：`main` branch `protected=true` 或等价 Ruleset 有效；
- `E058-AC-006`：Required status check context包含 `Askora CI / Required`；
- `E058-AC-007`：失败 Required status 无法通过普通 merge path进入 main；
- `E058-AC-008`：Production Local / Chromium / migration / recovery evidence均来自当前 commit；
- `E058-AC-009`：CI docs 与 workflow topology 一致；
- `E058-AC-010`：Engineering/Policy/Learning Evidence状态继续独立报告。

## Required Tests

- full `Askora CI / Required` run；
- intentional Required failure merge-block evidence；
- Optional failure isolation evidence；
- branch/ruleset configuration readback；
- docs gate。

## External-setting Failure Semantics

若执行环境无权限修改 GitHub Ruleset / Branch Protection：

```text
BLOCKED_BY_GITHUB_REPOSITORY_PERMISSION
```

必须返回待配置的准确 status name、当前 protection readback、所需设置；不得标记 `E058 DONE`。

## Completion Report Format

报告：aggregate topology、successful run、negative failure evidence、Ruleset/branch protection readback、Optional isolation、commit SHA、最终 `E058 DONE` 或明确 blocker。