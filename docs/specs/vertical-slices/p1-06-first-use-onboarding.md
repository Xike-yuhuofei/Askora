# P1-06 — Fact-driven First-use Onboarding Vertical Slice

> 状态：FROZEN
> 日期：2026-08-09
> Governing：ADR-0106、`ONBOARD-*`
> Decision authority：user-delegated Codex

## 1. Objective

在私人 macOS App 内闭合：

```text
首次登录 → 边界说明 → 模型真实验证 → 私人资料 → confirmed Goal/diagnostic/plan
→ canonical activity start/resume/complete → Today next action
```

路径可 dismiss/reopen/restart，步骤完全由 owner facts 派生，错误使用 P1-07 恢复动作。

## 2. Scope

### Included

- presentation-only onboarding preference 与 existing-user backfill；
- SYS06 first accepted-transcript activity completion projection；
- current-user journey query、single next action、strict API/error schema；
- `/welcome`、default entry/deep-link rules、Settings reopen；
- P1-02 model summary、P1-03 data-control route/capability、P1-07 recovery action 集成；
- 真实 UI-02A/B/C 与 Book Learning 主链；
- deterministic、real-provider、App restart、accessibility、首次用户验收；
- release report、gap register DONE。

### Excluded

- 多资料 Goal/完整 Goal 编辑与 replan；
- 新 planner/mastery/review/policy 逻辑；
- Focus、笔记、备份/删除实现、账号生命周期实现；
- 样例资料；
- learning efficacy claim。

## 3. Execution Split

```text
EXEC-1061: preference + backfill + completion/readiness query foundation
→ independent commit/gate
EXEC-1062: welcome UX + dependency integration + real product closure
→ independent commit/gate
```

EXEC-1062 MUST NOT 在 EXEC-1061 未归档或 P1-02/P1-03/P1-07 所需真实能力未形成可集成 commit 前
修改 onboarding 产品代码。

## 4. Acceptance Criteria

- `P106-AC-001`：`ONBOARD-AC-001..009` 全部有当前证据。
- `P106-AC-002`：clean profile 完成真实 model→material→goal→activity→Today，App restart 后续接且
  不重复副作用。
- `P106-AC-003`：撤销配置、删除资料、归档 Goal、supersede activity 后步骤按 current facts 回退。
- `P106-AC-004`：dismiss/reopen、existing-user backfill、换用户、并发和 deep link 不失真或泄漏。
- `P106-AC-005`：所有错误显示 what/safety/action，且只执行 server-allowed recovery。
- `P106-AC-006`：360/768/1024/1440、200% zoom、keyboard/focus/live region 通过。
- `P106-AC-007`：无内部知识首次用户可说明数据位置、模型发送边界、稍后继续和 Today 下一步。
- `P106-AC-008`：full backend/frontend/electron/security/docs/migration gates PASS。
- `P106-AC-009`：两份 EXEC 独立 commit/release evidence 后才把 P1-06 标 DONE。

## 5. Dependency Gate

- UI-02C DONE，exact activity 可 start/resume/complete；
- P1-02 DONE，App 内模型配置/真实验证/重启恢复可用；
- P1-03 至少发布 current data-control capability/route，且不会暴露路径；
- P1-07 发布稳定 RecoveryAction 并对本路径错误有真实 owner action；
- P1-02/P1-07 重复 ADR-0012 编号已在集成历史中消歧，不以歧义编号作为合同引用。

## 6. Completion Rule

Mock、只读页面、frontend wizard、只看到模型回复、无真实依赖 action、无 restart/deep-link/首次用户
证据均不能关闭 P1-06。Engineering、Security/Privacy、Product Usability 与 Learning Evidence 必须
分开报告；Learning Evidence 保持 `LEARNING_EVIDENCE_INSUFFICIENT`。
