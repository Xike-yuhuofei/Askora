# Askora docs 决策/规范层塌缩重构方案

> 状态：方案（待执行）
> 日期：2026-08-13
> 性质：`docs/` 内部结构重构，不涉及代码

---

## 1. 背景与问题诊断

`docs/` 下现有 170 个 Markdown 文件、14 个一级目录，但「搞清楚当前状态」需要跨 5–7 个文件拼出 current truth。核心病灶有三处：

1. **ADR 过重**：26 个独立 ADR 文件共 4302 行，其中 9 个已 superseded/mixed，靠 `docs/architecture/README.md` 里的 supersession matrix 才能判断哪个还生效——这是「决策文档过多、搞不清楚」的主因。
2. **历史从未真正归档**：`docs/archive/` 目录是空的，superseded 的 ADR、过时的 engineering wiki 都还留在 current 目录里，只贴了「partially superseded」标签。
3. **权威链重复**：`docs/README.md`、根目录 `AGENTS.md`、以及 product/design/architecture/specs 各层 README 都在重复同一套 7 层 authority chain。

**现状盘点（经探索确认）**：

| 维度 | 现状 | 结论 |
|---|---|---|
| Product 3 文件 | STRATEGY 579 + POSITIONING 497 + DEFINITION 715 = 1791 行，被约 64 个文件、180 处引用 | 是权威链骨架，**不合并** |
| ADR | 26 文件 / 4302 行，21 accepted + 4 partially-superseded + 1 mixed | **合并成 1 份决策日志** |
| Spec | 63 个：约 55 current + 4 mixed 措辞 + 4 DONE 记录 | 迁移基本完成，只需清理 4 处措辞 |
| Design | experience 3 个 current；learning 3 个（2 设计基线 + 1 FROZEN Delta） | Delta 属历史追溯 |
| engineering wiki | 1 文件，8 月 8 日生成，已过时（仍写 Electron/PostgreSQL/Redis 默认） | 归档 |
| 代码栈 | 默认 SQLite、无 Electron、PG/Redis/Kafka 仅兼容性保留 | 与 v1 目标一致 |

---

## 2. 重构目标

把「7 层模糊状态」塌缩成「3 层清晰生命周期」，让 Codex/TraeCode 能从一个入口直接拿到当前有效约束，让人能一眼看清「现在是什么」。

**3 层生命周期**：

- **CURRENT（当前生效）**：`product/`、`design/`、`architecture/`、`specs/`
- **PLANNING（进行中）**：`planning/`
- **ARCHIVE（历史）**：`archive/`

`research/` 与 `ui-reverse-engineering/` 是支持证据输入，不属于权威链三层。

**状态二值化**：文件要么在 current 目录（生效），要么在 archive（历史），消灭「partially superseded」「mixed」等中间态。

**方法论依据**（对齐业界最佳实践）：

1. 当前 / 历史二分，消灭中间态；
2. 决策日志 > 每决策一长文件（Nygard ADR：短、只记「决定 + 背景 + 后果」，不写长篇）；
3. 单一导航入口，authority chain 只写一次；
4. 按读者目的组织（Diátaxis），不是按文档类型；
5. 可机械校验（docs-as-code + check 脚本）> 依赖自觉维护 supersession matrix。

---

## 3. 目标结构

```
docs/
├── README.md                     # 唯一导航入口（重写精简）
├── product/                      # [CURRENT] 产品权威 —— 3 文件保留
├── design/                       # [CURRENT] 设计 —— experience 3 + learning 2
├── architecture/
│   ├── README.md                 # [CURRENT] 精简为「决策日志入口 + ADR 何时新建」
│   └── decisions/
│       └── DECISION-LOG.md       # [CURRENT] 新：合并 26 个 ADR 的决策日志
├── specs/                        # [CURRENT] 规范 —— 清理 4 处陈旧措辞
├── planning/                     # [PLANNING] EXEC
├── research/                     # [SUPPORTING] 证据 —— 保留不动
├── ui-reverse-engineering/       # [SUPPORTING] 逆向证据 —— 保留不动
└── archive/                      # [ARCHIVE] 真正启用
    ├── adr/                      # 26 个 ADR 原文（git mv，文件名不变）
    └── engineering/              # 过时 Code Wiki（git mv）
```

---

## 4. 执行步骤

### Step 1 — 创建决策日志 `docs/architecture/decisions/DECISION-LOG.md`

读 26 个 ADR 原文，产出一份合并视图（约 1000–1200 行）：

- **Part A「当前有效决策」**：按主题分组（Learning Core / Workspace & Identity / Experience & UI / Local Web & BYOK / Data Control），每条保留 `ADR-XXXX` 编号标题 + Status + 日期 + 20–35 行决策要点 + 「原文：`../archive/adr/ADR-XXXX-*.md`」指针。
- **Part B「历史/已废止索引」**：一张表，列出被 superseded 的 ADR（重点：0008/0009/0013/0014/0018/0019/0103/0106/0107 的替代链），每行「被什么替代 + 归档原文链接」。
- 保留 ADR 编号作为标题锚点，供现有文档引用。

### Step 2 — 归档 ADR 原文

`git mv` 26 个 `docs/architecture/decisions/ADR-*.md` → `docs/archive/adr/`（文件名不变，历史保留）。

### Step 3 — 重写 `docs/architecture/README.md`

从「26 条 ADR + supersession matrix 索引」改为「决策日志入口 + 何时必须新建 ADR + ADR 模板」。删除 supersession matrix（该信息并入 DECISION-LOG.md Part B）。

### Step 4 — 修复 ADR 引用

全仓把所有 `architecture/decisions/ADR-` 链接改为 `archive/adr/ADR-`（纯路径替换，文件名不变）。涉及：`docs/README.md`、`docs/specs/README.md`、`docs/design/README.md`、`AGENTS.md`、各 spec 正文里的 ADR 链接。用 `check_docs.py` 兜底发现遗漏。

### Step 5 — 精简权威链重复（按 Diátaxis 读者目的重排）

- 重写 `docs/README.md`：
  - 保留「从问题出发导航」表格（最有价值）。
  - 用 **Diátaxis 读者目的视角**重排导航：按「代理要做的四件事」分——① 开始新任务前该读什么；② 实现某功能该读什么；③ 查某条约束该读什么；④ 理解为什么这么设计该读什么。而不是按文件类型列目录。
  - 删掉重复的 authority chain 图与 7 层 lifecycle 表，改为简洁的「CURRENT / PLANNING / ARCHIVE 三层」说明。
- 瘦身 `AGENTS.md`：目标是一张**不超过 30 行的读取顺序清单**（只留指路，不堆内容）。读取顺序从 10 步收敛（ADR 改指 DECISION-LOG.md），删除与 docs/README.md 重复的 authority chain 描述与 GAP 协议长文。

### Step 6 — 归档 engineering wiki

`git mv docs/engineering/README.md` → `docs/archive/engineering/README.md`。更新 `docs/README.md` 对 engineering 的引用（改为指向 archive，并注明「代码运行方式见根目录 README」）。

### Step 7 — 清理 4 处陈旧 spec 措辞（只改措辞，不移动、不归档）

- `docs/specs/interfaces/api-contract.md`：删「认证授权」语义 → 改为 defer 到 LID（v1 无 auth）。
- `docs/specs/interfaces/data-control-contract.md`：删「macOS 私人桌面 SQLite」→ 改为现行 Product Positioning 语境。
- `docs/specs/vertical-slices/p1-03-data-control-recovery.md`、`p1-07-error-recovery-center.md`：标注 Electron/PostgreSQL/OCR 段落为「历史技术合同，现行见 X」，不做结构性删除。

---

## 5. 关键文件

- **新建**：`docs/architecture/decisions/DECISION-LOG.md`
- **重写**：`docs/README.md`、`docs/architecture/README.md`、`AGENTS.md`（根目录）
- **移动**：26× `docs/architecture/decisions/ADR-*.md`、`docs/engineering/README.md`
- **编辑**：`api-contract.md`、`data-control-contract.md`、`p1-03-*.md`、`p1-07-*.md`
- **复用现有工具**：`.github/workflows/check_docs.py`（链接校验 + stale 断言）

---

## 6. 验证

1. `python3 .github/workflows/check_docs.py` —— 链接无缺失（重点确认 ADR 引用已全部改为 archive 路径）。
2. `git diff --check` —— 无空白错误。
3. `git status` 确认所有移动都是 `git mv`（重命名可见，非删除+新增）。
4. 人工走查：从 `docs/README.md` 出发，3 步内能定位任意 current 事实（Product 边界 / 当前有效架构决策 / 实现合同），无需读 supersession matrix。
5. 确认 `research/`、`specs/vertical-slices/`、`design/learning/` 未被移动（「先保留」边界）。

---

## 7. 本次不做的事（明确排除）

- 不合并 Product 3 文件；不动 `research/`、`ui-reverse-engineering/`、历史 vertical-slice、`design/learning/` 的 v0.3 文件。
- 不碰根目录杂物（TraeCode Copy / TraeWork / .design_library / demos / Professional App Development Framework.md / dump.rdb 等），另开一批处理。
- 不重写 engineering wiki（只归档，以后再说）。
- 不引入 frontmatter（用「current 目录 vs archive 目录」二值化替代状态矩阵）。
