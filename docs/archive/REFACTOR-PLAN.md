# Askora「决策/规范」文档体系重构方案

> 状态：Proposal（待审批，未执行）
> 范围：`docs/` 中决策/规范类文档（ADR / Spec / Design）的结构性重构
> 原则：单一权威视图、按系统组织、编号收敛、历史可追溯（`git mv` 归档，不物理删除）

---

## 一、背景与问题

当前 `docs/` 中决策/规范类文档约 **96 个**（26 ADR + 63 Spec + 7 Design），"搞不清楚"的根因有四点：

1. **决策结论多处复述**：ADR 是决策叙事，Spec 是当前规范，两者映射被 `architecture/README.md` §6–9 与 `specs/README.md` §7–8 各复述一遍，同一事实散落三处。
2. **一个系统拆多份 Spec**：`specs/systems/` 里 SYS01 拆 4 份、SYS06 拆 5 份、SYS08 拆 2 份；`interfaces/` 12 份。
3. **四个入口各说各话**：`docs/README`、`architecture/README`、`specs/README`、`design/README` 无单一权威入口。
4. **编号体系过多**：`CAP-*/PD-*/ADR-*/LID-*/WSP-*/LSS-*/MATLIFE-*/SYS*/UI-*` 十几套编号，无统一 mental map。

已确认方向：**推倒重建 + ADR 全归档只留视图 + Spec 按系统合并**。

---

## 二、目标与设计原则

- **单一权威视图**：任何"现在系统是怎么决定/怎么实现"的问题，都能在 1-2 跳内定位到唯一 current 文档。
- **分层清晰**：产品层（是什么）→ 决策层（为什么这样决定）→ 规范层（怎么实现）→ 归档层（历史）。
- **按系统组织**：规范以 SYS01–SYS08 为主线，每系统一份。
- **编号收敛**：不破坏代码引用（条款 ID 原样保留），只收敛"文件/文档入口"。
- **历史可追溯**：旧文档一律 `git mv` 归档，不物理删除。

---

## 三、目标目录结构

```text
docs/
├── README.md                        # 唯一入口：task-oriented 导航 + 当前文档清单
├── product/                         # 产品层（不动）
│   ├── PRODUCT-STRATEGY.md
│   ├── PRODUCT-POSITIONING.md
│   └── PRODUCT-DEFINITION.md
├── decisions/
│   └── DECISIONS.md                 # 决策权威视图（唯一 truth）
├── specs/
│   ├── architecture.md              # ← 3 份合并
│   ├── domain.md                    # ← 4 份合并
│   ├── systems/
│   │   ├── 01-content-knowledge.md  # ← 4 份合并
│   │   ├── 02-retrieval.md
│   │   ├── 03-learner-model.md
│   │   ├── 04-assessment.md
│   │   ├── 05-teaching-policy.md
│   │   ├── 06-learning-planner.md   # ← 5 份合并
│   │   ├── 07-review-scheduler.md
│   │   └── 08-ai-orchestration.md   # ← 2 份合并
│   ├── interfaces/                  # ← 12 份合并为 5 份
│   │   ├── api.md
│   │   ├── persistence-and-data-control.md
│   │   ├── content.md
│   │   ├── message-and-note.md
│   │   └── recovery-and-onboarding.md
│   ├── platform.md                  # ← 4 份合并
│   ├── quality.md                   # ← 6 份合并
│   └── ui.md                        # ← 5 份合并
├── design/experience/               # 保留 3 份 current
├── research/                        # 不动
├── archive/
│   ├── adr/                         # ← 26 个 ADR 原文
│   ├── specs/                       # ← 合并前碎片 + vertical-slices
│   └── design/                      # ← 旧 design delta
└── engineering/ planning/ ui-reverse-engineering/   # 不动
```

**收敛效果**：96 份 → 约 **21 份 current**（1 决策视图 + 14 Spec + 3 Design + 3 Product）。

---

## 四、编号体系收敛

| 层 | 编号 | 处置 |
|---|---|---|
| 产品层 | `CAP-* / PD-RULE-* / PD-REQ-* / PD-AC-*` | 不变（authority 顶端） |
| 决策层 | `DEC-*`（新） | 取代 `ADR-*` 作为 current 引用 |
| 规范层 | `SYS01–08` + `ARCH-* / DOMAIN-* / API-* / PLAT-* / QUAL-* / UI-*` | 文件收敛后沿用 |
| 历史条款 ID | `LID-* / WSP-* / LSS-* / MATLIFE-*` | **合并进对应文档后原样保留为条款编号**，避免连锁改代码 |
| 溯源 | `archive/adr/ADR-XXXX` | 仅作历史溯源链接 |

---

## 五、关键设计：决策权威视图 `decisions/DECISIONS.md`

按主题（Identity / Workspace / Teaching / UI / Data / AI）组织，每条决策含：

- **结论**（当前有效，一句话）；
- **状态**（current / partially-superseded，标注哪些部分仍有效）；
- **指向规范**（唯一 current Spec 位置）；
- **溯源**（链接到 `archive/adr/ADR-XXXX`）。

它取代 `architecture/README.md` §5–9 与 `specs/README.md` §7–8 的全部重复复述，成为"当前有效决策"的唯一权威来源。

---

## 六、关键设计：Spec 合并映射

### systems（16 → 8）

| 新文件 | 吸收旧文件 |
|---|---|
| 01-content-knowledge.md | 01-content-knowledge + 01-library-management + 01-content-granularity + 01-knowledge-publish-pipeline |
| 02-retrieval.md | 02-retrieval |
| 03-learner-model.md | 03-learner-model |
| 04-assessment.md | 04-assessment |
| 05-teaching-policy.md | 05-teaching-policy |
| 06-learning-planner.md | 06-learning-planner + 06-goal-management + 06-goal-knowledge-mapping + 06-prerequisite-diagnostic-bootstrap + 06-activity-lifecycle |
| 07-review-scheduler.md | 07-review-scheduler |
| 08-ai-orchestration.md | 08-ai-orchestration + 08-model-configuration |

### 跨切面

- **domain.md** ← domain-model + decision-contract + event-contract + lifecycle-state-machines（4→1）
- **architecture.md** ← system-architecture + state-ownership + dependency-rules（3→1）
- **platform.md** ← identity-privacy-lifecycle + workspace-project-session-scope + course-workspace-selection + local-secret-store（4→1）
- **quality.md** ← testing-standard + ci-infrastructure-standard + v1-local-web-quality-reconciliation + observability-standard + definition-of-done + security-standard（6→1）
- **ui.md** ← design-system + learning-interaction-contracts + quality-and-regression + screen-and-navigation-contracts（5→1）
- **interfaces/ 5 份**：
  - api.md ← api-contract + error-contract + schema-versioning
  - persistence-and-data-control.md ← persistence-contract + material-lifecycle-contract + data-control-contract
  - content.md ← content-ingestion-contract + render-content-contract
  - message-and-note.md ← learning-conversation-message-system-spec-delta + user-note-source-inspection-contract
  - recovery-and-onboarding.md ← recovery-contract + onboarding-contract

### 归档

- **vertical-slices 11 份** → 全部 `archive/specs/vertical-slices/`（current 语义已进 systems/interfaces/ui）
- **design/learning 3 份**（个人AI辅助学习平台设计方案 / AI学习系统算法与教学内核设计 / v0.3-Canonical-Design-Delta）→ 标注"已被 specs 吸收"后归档
- **ADR 26 份** → `archive/adr/`

---

## 七、实施步骤（5 个 Phase）

1. **冻结蓝图与迁移映射**
   - 产出目标结构 + 编号体系一页蓝图（落为 `docs/archive/REFACTOR-PLAN.md` 供回溯）
   - 产出逐文件迁移映射表（96 → 合并/归档），覆盖全部 current 文档、无遗漏、无重复 truth

2. **决策层重构**
   - `git mv` 26 个 ADR → `archive/adr/`
   - 新建 `decisions/DECISIONS.md`
   - 移除 `architecture/decisions/` 的 current 角色
   - 验收：视图完整覆盖所有 accepted 决策、可回溯、无决策事实丢失

3. **规范层合并**
   - 按 §六 映射逐组合并（条款 ID 原样保留）
   - 旧碎片 `git mv` → `archive/specs/`
   - 验收：每系统仅 1 份 canonical spec，代码引用不被破坏

4. **设计层收敛 + 单一入口**
   - design/learning 归档、design/experience 保留
   - 重写 `docs/README.md` 为唯一入口
   - 降级 `architecture/README`、`specs/README`、`design/README` 索引
   - 验收：从根 README 出发，1-2 跳定位到唯一 current 文档

5. **引用/工具链修复 + 验证**
   - 同步更新 `AGENTS.md` 路径引用
   - 更新代码注释、CI、`planning/execs/` 引用
   - 更新 `check_docs.py`（STALE_PATTERNS、目录断言、archive 豁免）
   - 全量验证：`python3 .github/workflows/check_docs.py` + `git diff --check`

---

## 八、风险与缓解

| 风险 | 缓解 |
|---|---|
| `AGENTS.md` 强依赖旧路径（`docs/specs/...`、`docs/architecture/decisions/...`） | Phase 5 第一步同步改，否则执行代理读到失效路径 |
| 条款 ID（`LID/WSP/LSS/MATLIFE`）与代码/测试断言耦合 | 合并文件但条款 ID 原样保留，不触发连锁改代码 |
| 合并后单文件过大（如 interfaces、domain） | 保持"每系统一份 + 跨切面 5 份"的粒度，不极致合并；大文件内用稳定二级标题导航 |
| 归档后溯源断裂 | 全部 `git mv`（保留 git 历史）+ 决策视图内置 ADR 溯源链接 |

---

## 九、验收标准（整体）

1. 决策/规范 current 文档从 96 收敛到约 21 份；
2. 任何"系统怎么决定/怎么实现"的问题，从 `docs/README.md` 出发 ≤ 2 跳可达唯一 current 文档；
3. `python3 .github/workflows/check_docs.py` 全绿、`git diff --check` 无错、零悬空链接；
4. `AGENTS.md` 与代码/CI 中的路径引用全部指向新结构；
5. 无决策事实与规范条款丢失（可经归档文件 + 决策视图双向回溯）；
6. 所有 current 文档通过 front-matter 元数据校验（`Status` / `Owner` / `Last-verified`），缺失即 CI 失败。

---

## 十、业界最佳实践对齐（补充）

本方案对齐 Diátaxis、docs-as-code、ADR Decision Log 与 agent-first 文档模式，补充以下 4 条硬性规则：

1. **统一 front-matter 元数据（agent-first 硬门槛）**
   每份 current 文档头部强制携带：

   ```text
   Status: current | superseded
   Owner: <负责域>
   Superseded-by: <链接>（可空）
   Last-verified: YYYY-MM-DD
   ```

   由 `check_docs.py` 校验存在性，缺失即 CI 失败——不是"建议标注"，而是防止 agent 读过期文档的硬门槛。

2. **临时/证据文档的生命周期规则**
   `planning/execs/`、`archive/releases/`、audit、gap-analysis 等临时或证据文档必须携带：

   ```text
   Integrates-into: <吸收进哪份 canonical 文档>
   Delete-by: YYYY-MM-DD
   ```

   集成进 canonical 后即归档；否则 agent 会把一次性证据当作 current truth。

3. **决策视图定位为 "decision log"（immutable 原文 / 可变视图分离）**
   `decisions/DECISIONS.md` 不是"重写 ADR"，而是 decision log：ADR 原文 immutable 保留在 `archive/adr/`，仅 `status` 可变；`DECISIONS.md` 是当前有效决策汇总，每条含结论 + status + 溯源链接。

4. **`AGENTS.md` 与 `docs/README.md` 分工明确**
   `AGENTS.md` = agent 的机械入口（权威链、命令、GAP 协议）；`docs/README.md` = 人的导航入口（task-oriented + 当前文档清单）。两者不互相复制，`AGENTS.md` 只链接 `docs/README.md`，不复制其内容。
