# Askora Documentation Governance

> 状态：Current Documentation Governance
> 适用范围：`README*`、`docs/**` 以及会引用正式文档路径的工程说明与校验脚本
> 目标：保证同一长期事实只有一个 current canonical owner，并让新文档有可判定的归属与生命周期

## 1. Source of Truth

Askora 的长期事实遵循：

```text
PRODUCT-STRATEGY
→ PRODUCT-POSITIONING
→ PRODUCT-DEFINITION
→ Canonical Design
→ Accepted ADR
→ Canonical Specs
→ Planning / Linear
→ Code / Migration / Executable Tests
→ Release Evidence / Research / Archive
```

这不是说上位产品文档直接规定 API 或数据库，而是说下位文档和实现不得突破上位产品意义。不同层发生冲突时：

- Product 文档之间按 Strategy → Positioning → Definition 处理，并使用对应 GAP protocol；
- Product Definition 与 Design / ADR / Spec 冲突时，下位层收敛或先形成上位 Delta；
- Design / ADR 与 Spec 冲突时，先修复治理链，不让实现自行选边；
- Spec 与代码冲突时，默认是 implementation drift；
- Release、Gap Analysis、EXEC、Research 只代表证据、历史或工作状态，不能覆盖 current canonical truth；
- Linear 是实时 work-management truth，不是长期产品、设计或技术合同。

## 2. 文档类型与归属

| 类型 | 负责回答 | 放置位置 | 绝对不应包含 |
|---|---|---|---|
| Research | 为什么相信某个问题、证据、假设或候选方案 | `research/` | 未经决策即成为产品或实现合同 |
| Product Strategy | Why / Who / Problem / Value / Success | `product/PRODUCT-STRATEGY.md` | Feature、页面、schema、API |
| Product Positioning | Category / Product Shape / Hard Boundary / Non-goal | `product/PRODUCT-POSITIONING.md` | 实现 mechanics |
| Product Definition | Product Objects / Capabilities / Rules / Requirements / Product Acceptance | `product/PRODUCT-DEFINITION.md` 或必要的 `product/features/` | route、component、算法、数据库字段 |
| Experience Design | 用户如何理解、导航、交互和完成任务 | `design/experience/` | 自行新增 Product Scope |
| Learning / Canonical Design | 教学、学习、领域等共享语义如何成立 | `design/learning/` | 当前任务状态或直接 API/schema 合同 |
| Feature Canonical Design | 跨 UX、领域和系统的已冻结 Feature 语义 | `design/features/` | 未冻结的产品范围 |
| Architecture / ADR | 系统边界与具有长期影响的决策、备选与理由 | `architecture/` | 普通任务记录、实时 backlog |
| Spec | 可直接约束实现、迁移、测试和质量门禁的规范性合同 | `specs/` | 市场假设、历史报告、已完成任务日志 |
| Engineering Guide | 如何理解、开发、构建或维护代码 | `engineering/` | 第二套 Product / Architecture truth |
| Quality / Test | 可执行质量、风险与验收合同 | `specs/quality/` 或相关系统 Spec | 单次测试运行结果冒充长期标准 |
| Operations | 运行、备份、恢复、incident、release process | 有真实 current 内容时再建立 `operations/` | 仅有一次性 release report 就预建空目录 |
| Planning | 仍可执行的 EXEC 与执行提示 | `planning/` | 已完成证据、Canonical Design、实时状态副本 |
| Historical / Archive | 已完成、superseded、带 SHA 的 audit 与 release evidence | `archive/` | 被 current implementation 当作默认入口 |

## 3. Research → Canonical Formation

```text
Research Question
→ Evidence / Literature Review
→ Findings / Synthesis
→ Explicit Decision
→ Canonical Product / Design / ADR / Spec
→ Implementation / Verification
```

Research 可以保留相互冲突的证据与假设；Canonical 文档必须给出当前被接受的结论。设计已冻结后，不应让结论长期只存在于 Research，也不应复制一份平行 canonical truth。

## 4. 什么才有资格叫 Spec

文件只有同时满足以下条件，才进入 `specs/`：

1. 有明确上位 Product / Design / ADR 依据；
2. 使用可验证的规范性语言，例如 MUST / MUST NOT / SHOULD 或稳定 requirement ID；
3. 定义实现者需要遵守的对象、边界、状态、接口、错误、迁移或质量语义；
4. 能映射到自动化测试、迁移验证或明确人工验收；
5. 声明版本、兼容、supersession 或 lifecycle；
6. 不是 Research、Gap Analysis、EXEC、Release Report 或一次性方案记录。

Vertical Slice 只有仍承担 current、跨合同、可重复验证的实现约束时保留在 `specs/vertical-slices/`；已被后续合同吸收或仅表示当时交付范围的文件进入 `archive/specs/vertical-slices/`。

## 5. ADR 规则

ADR 只记录具有长期架构意义、存在真实替代方案、会影响共享 ownership / migration / security / compatibility 的决策与理由。ADR 必须包含 Context、Decision、Alternatives、Consequences、Migration/Rollback、Validation 与 Supersession。

以下内容不创建 ADR：普通任务进度、单模块私有重构、已经由 current Spec 唯一决定的机械实现、未经冻结的 Product Scope。

## 6. Current 与 Archive

Current 目录只保留当前有效入口；历史文件按性质进入：

- `archive/audits/`：Gap Analysis、conformance audit、带 commit/time 边界的诊断；
- `archive/design/`：已被 current canonical design 吸收或 supersede 的设计；
- `archive/specs/`：已被 current contract 取代的规范或 slice；
- `archive/exec-plans/`：完成、取消或 superseded 的 EXEC；
- `archive/releases/`：候选 SHA 的 release / completion evidence。

Archive 保留证据，不参与默认权威链。判断当前状态必须重新核对 current `main`、current canonical docs、测试与 Linear。

## 7. 新文档放置决策

```text
它是在收集证据或验证假设？
├─ 是 → research/
└─ 否
   ├─ 改变 Why / Who / Value / Scope？ → product/，并执行上位 change control
   ├─ 决定用户如何理解或操作？ → design/experience/
   ├─ 冻结教学、领域或跨层 Feature 语义？ → design/learning/ 或 design/features/
   ├─ 记录长期架构选择与备选？ → architecture/decisions/
   ├─ 直接约束实现或质量门禁？ → specs/
   ├─ 说明代码与开发工作流？ → engineering/
   ├─ 是仍可执行任务合同？ → planning/
   └─ 是快照、完成证据或 superseded 记录？ → archive/
```

如果两个位置都似乎合理，先判断文档的唯一核心问题；无法安全判断的重要文件标记 `REVIEW`，不猜测、不删除。

## 8. 命名与元数据

- 一个文件只承担一个主要职责；标题与目录职责一致；
- 新文件使用稳定、可搜索的英文 kebab-case；已有高价值中文文件不为形式统一而批量改名；
- ADR 使用 `ADR-NNNN-title.md`，EXEC 使用 `EXEC-NNN-title.md`；
- Canonical、Research、Historical 文件必须在开头声明状态、authority/lifecycle 与 supersession（如适用）；
- 路径变更优先 `git mv`，并同步修复 Markdown、README、代码注释、CI 与脚本引用；
- 不建立空目录、占位 README 或第二套索引；目录出现时必须已有真实内容。

## 9. Cross-cutting Quality Attributes

Security、Privacy、Performance、Accessibility、Reliability、Observability 按职责落位：

- 用户可见体验约束 → Experience Design；
- system ownership / trust boundary → Architecture / ADR；
- 可执行阈值与验证合同 → `specs/quality/` 或对应 Spec；
- runtime procedure / incident / recovery runbook → 有真实内容时进入 Operations。

不能因为它们“横切”就各自建立长期一级垃圾桶。

## 10. 维护门禁

任何文档路径、生命周期或权威入口变更后至少运行：

```bash
python3 .github/workflows/check_docs.py
git diff --check
```

并全局搜索旧路径引用。逐文档迁移与处置记录维护在 [`document-inventory.md`](document-inventory.md)。
