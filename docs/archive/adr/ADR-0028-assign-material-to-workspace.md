# ADR-0028 — Assign Unassigned Material to a Workspace

Status: accepted
Date: 2026-08-13
Decision owners: user-authorized Journey 001/004 implementation
Upper authority: PRODUCT-DEFINITION、ADR-0026、`WSP-021`、`D01-003`
Does not amend: Product Capability、Conversation identity、Chat-is-not-L0

## Context

上传必须只创建资料。当时 writer 仍隐式挂到 default Workspace，也没有公开归属 command。「加入学习空间 / 马上开始学习」无法诚实实现。

## Decision

1. 默认上传创建 `workspace_id=null` 的 unassigned Material。
2. `AssignMaterialToWorkspaceV1` 是唯一归属 writer；已归属不得改挂。
3. 「马上开始学习」可以自动建空间再归属；没有 SYS06 Activity 时进入空间空态，不前端开聊。

## Alternatives Considered

### A. Keep implicit default Workspace on upload

Rejected。与「上传不创建空间」冲突。

### B. One composite start-learning command that also writes Activity

Rejected。Activity 仍由 SYS06 拥有；本轮不打包假交易。
