# P1-04C Scanned PDF OCR Review Vertical Slice

> Status: FROZEN / DONE
> Governing: ADR-0008, `LIB-050..055`
> Depends on: P1-04A DONE, P1-04B DONE

## Objective

把扫描 PDF 从“完成但无正文”升级为本地 OCR→证据化候选→人工复核→新 MaterialRevision 的可恢复闭环。

## In scope

- local Tesseract adapter and availability；
- page rendering/digital-text detection；
- durable OCR run/candidate persistence；
- candidate query, correction, accept/reject；
- accepted OCR MaterialRevision/SourceSpan/search/knowledge rebuild；
- side-by-side review UI and recovery states。

## Out of scope

cloud OCR、handwriting guarantee、formula semantic recognition、automatic low-confidence acceptance、OCR learning-effect claim。

## Acceptance criteria

- `P104C-AC-001`～`003`：满足 `LIB-AC-006..008`；
- `P104C-AC-004`：engine unavailable/timeout/invalid output/worker restart fail safely；
- `P104C-AC-005`：未接受候选不出现在普通搜索/检索/知识地图；
- `P104C-AC-006`：真实本地扫描 PDF 完成 request→review→accept→new revision→search；
- `P104C-AC-007`：安全、隐私、响应式、无障碍与全量门禁通过。
