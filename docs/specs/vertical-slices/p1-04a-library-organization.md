# P1-04A Library Search and Organization Vertical Slice

> Status: FROZEN / DONE
> Governing: ADR-0008, `LIB-001..033`
> Depends on: UI-02A DONE

## Objective

让用户能在规模增大后按标题/正文/状态/学科/标签/集合找到资料，版本化编辑显示元数据，并安全批量整理；不改变 raw asset、MaterialRevision 或学习状态。

## In scope

- SourceDocument profile fields/version/backfill；
- flat tags/collections and assignments；
- current-revision LibrarySearchProjection；
- Library workspace v1.1 filters/match evidence；
- metadata/tag/collection/batch commands；
- archive/restore product flow；
- desktop/narrow/keyboard/200% zoom states。

## Out of scope

OCR、duplicate resolution、nested/smart collection、permanent deletion、cloud sync、SYS06 goal changes。

## Acceptance criteria

- `P104A-AC-001`～`004`：满足 `LIB-AC-001..003/005`；
- `P104A-AC-005`：search/query private no-store、stable ordering、bounded excerpt、PARTIAL/STALE honest；
- `P104A-AC-006`：真实浏览器完成搜索→编辑→标签/集合→批量→archive/restore；
- `P104A-AC-007`：全量工程/安全/无障碍门禁通过。
