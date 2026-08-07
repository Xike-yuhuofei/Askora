# Askora 文档中心

`docs/` 是 Askora 的产品设计、教学内核设计与研究资产入口。

核心原则：**研究依据、正式设计与实际实现必须分层管理；同一职责边界只能有一个正式设计来源。**

## 1. 快速入口

| 我想了解 | 阅读入口 |
|---|---|
| Askora 是什么、整体产品如何设计 | [`design/个人AI辅助学习平台设计方案.md`](design/个人AI辅助学习平台设计方案.md) |
| AI 教学系统如何工作 | [`design/AI学习系统算法与教学内核设计.md`](design/AI学习系统算法与教学内核设计.md) |
| 八类技术系统的正式设计 | [`design/AI学习系统算法与教学内核设计.md`](design/AI学习系统算法与教学内核设计.md) 第 4 章 |
| 为什么采用这些设计 | [`design/research/`](design/research/) |
| 查看 Deep Research、论文与行业证据 | [`design/research/evidence/`](design/research/evidence/) |
| 查看架构推导与八类系统详细研究稿 | [`design/research/synthesis/`](design/research/synthesis/) |
| 查看 Research 的治理与索引规则 | [`design/research/README.md`](design/research/README.md) |

## 2. 文档体系

```text
docs/
├── README.md
└── design/
    ├── 个人AI辅助学习平台设计方案.md
    ├── AI学习系统算法与教学内核设计.md
    └── research/
        ├── README.md
        ├── evidence/
        └── synthesis/
```

Askora 的设计知识分为三层：

```text
Research
├── Evidence
└── Synthesis
        ↓
Canonical Design
        ↓
Implementation Validation
```

这是一条**知识形成与验证链路**，不是简单的文档等级排序。

## 3. Canonical Design：正式设计基线

Canonical Design 不是单一文件，而是一组按职责边界划分的正式设计文档。不同文档负责不同 bounded context，避免出现多份文档同时定义同一设计结论。

### [`design/个人AI辅助学习平台设计方案.md`](design/个人AI辅助学习平台设计方案.md)

Askora 的产品与整体技术架构基线，负责定义：

- 产品目标、范围与用户体验；
- 系统整体模块及边界；
- 数据、服务、交互与工程架构；
- 产品阶段与实现优先级。

涉及“Askora 整体应该做成什么样”，以该文档为正式设计基线。

### [`design/AI学习系统算法与教学内核设计.md`](design/AI学习系统算法与教学内核设计.md)

Askora 的学习科学、算法与教学内核设计基线，负责定义：

- 学习者建模、知识追踪与掌握度判断；
- 评估、错误诊断与形成性评价；
- 教学策略、学习路径与复习调度；
- RAG、知识图谱、LLM、Agent、Bandit/RL 等技术职责；
- AI 学习工具八类技术系统的职责、状态与决策所有权。

涉及教学内核及八类技术系统，以该文档为正式设计基线。

## 4. Research：研究资产

[`design/research/`](design/research/) 保存“为什么这样设计”的证据、推导与完整研究稿，不作为第二套正式规范。

```text
research/
├── evidence/    # Deep Research、论文、行业实践等证据
└── synthesis/   # 跨证据综合、架构推导、分系统设计研究
```

### `evidence/`

回答：**设计依据是什么、证据强度如何、有哪些边界条件与反例。**

允许与正式设计存在内容重复，因为其价值是证据与论证过程可追溯。

### `synthesis/`

回答：**这些证据对 Askora 的架构和系统设计意味着什么。**

用于保存跨证据综合、架构推导、现状诊断以及八类技术系统的详细研究设计稿。

详细文件索引、重复内容治理和 Deep Research 生命周期见 [`design/research/README.md`](design/research/README.md)。

## 5. 如何判断哪个来源为准

不同来源回答不同问题：

| 问题 | 权威来源 |
|---|---|
| 为什么这样设计？ | `research/evidence/` 与 `research/synthesis/` |
| 产品与系统应该如何设计？ | 对应职责边界的 Canonical Design |
| 当前实际上实现了什么？ | 代码、配置、数据库迁移与可执行测试 |

具体规则：

1. Research 用于提供证据与设计推导，不直接成为实现契约；
2. 被采纳的研究结论必须回写对应 Canonical Design；
3. Research 与正式设计冲突时，以对应 Canonical Design 为准；
4. 判断当前实现状态时，以代码、配置、数据库迁移和可执行测试为准；
5. 若实现与正式设计不一致，应明确这是实现偏差、设计变更还是文档滞后，并随后同步修正。

## 6. 文档治理

新增研究与设计资产统一遵循：

```text
Deep Research / 外部证据
→ research/evidence
→ research/synthesis
→ 被采纳结论回写 Canonical Design
→ Implementation
→ 代码与测试验证
```

正式资产必须按真实产品、系统或知识边界命名，不长期使用 `批次1`、`阶段2`、`最终版2` 等执行过程命名。

Research 层更详细的命名、拆分、去重、保留与溯源规则，以 [`design/research/README.md`](design/research/README.md) 为准。
