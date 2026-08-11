# P1-04B Library Deduplication Vertical Slice

> Status: FROZEN / DONE
> Governing: ADR-0008, `LIB-040..044`
> Depends on: P1-04A DONE

## Objective

对 exact/content-similar/revision candidate 给出有证据、可解释、可撤回的处理建议，不自动合并 canonical facts。

## In scope

- raw/content fingerprint backfill；
- upload/process duplicate detection；
- suggestion list/detail/evidence；
- keep/dismiss/archive/restore resolution；
- explicit attach-as-revision safety gate；
- duplicate UI review queue。

## Acceptance criteria

- `P104B-AC-001`：满足 `LIB-AC-004/005`；
- `P104B-AC-002`：同一 pair+policy 幂等，跨用户不可枚举；
- `P104B-AC-003`：archive 不删 raw，restore 恢复列表/projection；
- `P104B-AC-004`：无 KnowledgeUnit/evidence/mastery 自动合并；
- `P104B-AC-005`：真实浏览器处理三类候选和冲突/恢复路径。
