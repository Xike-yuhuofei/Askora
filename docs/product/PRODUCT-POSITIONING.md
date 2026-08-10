# Askora PRODUCT-POSITIONING

> 文档状态：Frozen Baseline  
> 适用范围：Askora v1 及其后续 Canonical Design / ADR / SPEC / EXEC  
> 文档性质：上位产品定位、产品边界与工程约束  
> 不包含：导航、首页职责、页面布局、交互入口等设计系统决策

---

## 1. 文档目的

本文件定义 Askora 的产品本质、v1 范围、运行模型、数据边界、AI 权限、学习内核边界、可靠性要求与明确 Non-goals。

后续所有 Canonical Design、ADR、SPEC、EXEC 和代码实现必须服从本文件。若下位设计与本文件冲突，应先修改并重新冻结本文件，而不是由下位文档或实现自行突破产品边界。

---

## 2. 一句话产品定位

> **Askora 是一个面向单用户、长期个人学习的本地运行 AI 学习工具。Askora v1 仅提供简体中文 Local Web Application，通过浏览器访问运行于用户设备上的 Local Server；不依赖 Askora 官方中心服务器，不提供官方云同步，核心数据默认保存在本机，用户自行配置 AI API Key，并通过互联网调用外部 AI 服务。Askora 的核心目标是建立可验证的长期学习闭环，而不是成为 ChatGPT、通用知识管理工具或团队协作平台。**

---

## 3. 产品本质

### 3.1 Askora 是什么

Askora 是：

- 个人长期学习工具；
- AI 辅助教学系统；
- 以用户主动提供的学习材料为主要知识边界的学习环境；
- 以 Learning Goal、Learning Evidence、Learner State、Teaching Policy 等学习领域对象为核心的产品；
- 以真实学习效果为首要目标，而非以使用时长、对话轮数或互动量为首要目标。

核心学习链路：

```text
学习材料
→ 内容解析与知识建模
→ 学习目标
→ Learner State
→ Teaching Policy
→ Teaching Action
→ 作答 / 练习 / 评估
→ Learning Evidence
→ Learner State 更新
→ 复习与下一轮教学决策
```

### 3.2 Askora 不是什么

Askora 不是：

- ChatGPT 类通用聊天产品；
- 通用知识管理工具；
- Notion / Obsidian / Zotero 替代品；
- 企业知识库；
- 团队协作产品；
- SaaS 多租户平台；
- 以 RAG 问答为产品本体的 AI 知识库。

对话可以是教学交互界面，但 `Conversation / Message / Prompt` 不得成为 Askora 的核心领域模型。

---

## 4. v1 产品形态与运行模型

### 4.1 客户端形态

Askora v1：

- 仅支持 Web UI；
- 暂不提供 macOS 原生客户端；
- 暂不提供 Windows 原生客户端；
- 暂不提供 iOS / Android 客户端；
- UI 仅支持简体中文；
- 正式支持环境以 Chromium 系浏览器为主，优先 Chrome / Edge；
- Safari / Firefox 在 v1 不承诺完整兼容。

“Web”在 Askora 中特指 **Local Web Application**，不等同于公网 SaaS。

### 4.2 Local Web Application

推荐运行模型：

```text
Browser
   ↓
http://127.0.0.1:<port>
   ↓
Askora Local Server
├── Application
├── Learning Engine
├── Content Pipeline
├── Retrieval
├── SQLite
├── Local Files
├── Background Jobs
└── AI Provider
        ↓
    Internet
        ↓
External AI APIs
```

Askora v1：

- 需要在用户设备上运行 Local Server；
- 不需要 Askora 官方中心服务器；
- Local Server 默认仅绑定 localhost / `127.0.0.1`；
- 默认不允许公网访问；
- 默认不作为 LAN Server 使用。

### 4.3 启动体验

最终用户不应依赖开发者命令启动 Askora。

目标运行体验：

```text
启动 Askora
→ 启动 Local Server
→ 检查数据目录与 Schema
→ 执行必要 Migration
→ 恢复必要任务状态
→ 自动打开浏览器
→ 使用 Askora
```

### 4.4 基础设施边界

Askora v1 最终用户运行环境不得要求：

- Docker；
- Redis；
- PostgreSQL；
- Kubernetes；
- Kafka；
- Elasticsearch 集群；
- 任何独立分布式基础设施。

这些技术可以用于开发、CI 或未来版本，但不得成为 v1 最终用户运行前提。

---

## 5. 用户、账号与设备模型

### 5.1 用户模型

Askora v1：

- 单用户；
- 无注册；
- 无登录；
- 无账号体系；
- 无 Organization；
- 无 Tenant；
- 无 RBAC；
- 无多人协作。

Workspace 不得被误建模为 Tenant 或 Organization。

### 5.2 设备模型

Askora v1：

- 以单设备使用为前提；
- 不支持多设备实时同步；
- 不解决跨设备冲突；
- 不建设 CRDT 或同步协议。

未来多设备能力通过版本演进和 Migration 引入，不提前为其增加高复杂度基础设施。

---

## 6. Workspace、Project 与 Material

### 6.1 Workspace

Askora 允许用户建立多个独立学习空间。

Workspace 是高层数据隔离边界，默认包含：

```text
Workspace
├── Materials
├── LearningProjects
├── LearningGoals
├── LearnerState
├── LearningHistory
├── UserNotes
└── Search / Retrieval Scope
```

默认原则：

- 不同 Workspace 的学习状态互不影响；
- 不同 Workspace 的资料关系互相隔离；
- 默认不跨 Workspace 搜索；
- v1 不设独立全局资料库。

### 6.2 Project

Learning Project：

- 必须归属于某个 Workspace；
- 是长期学习组织单位；
- 不是开始学习的强制门禁；
- 一个 Project 可以包含多个 Learning Goal；
- 用户可以直接基于 Material 开始学习，再决定是否组织进 Project。

### 6.3 Material

Material：

- 必须归属于 Workspace；
- 与 Project 为多对多关系；
- 同一 Material 可以属于同一 Workspace 内的多个 Learning Project；
- 从 Project 中移除 Material，只解除关系，不删除 Material 本体。

推荐概念关系：

```text
Workspace
├── Material
│   └── SourceFile
└── LearningProject
    └── ProjectMaterial
        └── Material
```

v1 不建设跨 Workspace 的 Global Material Library。

---

## 7. 数据归属与本地存储

### 7.1 Local-first

Askora 的核心学习数据以本地为权威源。

默认技术方向：

- SQLite：结构化数据；
- 本地文件系统：原始资料与其他文件资产；
- 本地索引：检索派生数据；
- 内存：临时缓存。

### 7.2 原始资料保存

用户导入资料时：

> **Import = ingest + copy，而不是仅记录原始文件路径。**

Askora 应将原始学习资料复制并保存到自己的本地数据目录，后续使用不依赖用户最初导入路径持续存在。

示意：

```text
AskoraData/
├── askora.db
├── files/
├── indexes/
├── cache/
├── jobs/
└── logs/
```

用户可以选择 Askora 数据目录的位置，但内部目录结构由 Askora 管理。

### 7.3 数据权利

用户拥有其学习数据。

Askora 应提供：

- 完整本地备份；
- 恢复能力；
- 数据导出能力。

内部 SQLite Schema 不属于稳定公开 API，用户直接编辑数据库或内部文件不属于正式支持能力。

---

## 8. Durable Data 与 Derived Data

### 8.1 Durable / Canonical Data

不得因缓存清理、索引重建或 AI 故障而丢失的数据，包括但不限于：

- Source Files；
- Workspace；
- Learning Project；
- Learning Goal；
- User Note；
- Learning Evidence；
- Assessment；
- Learning History；
- 用户配置；
- 其他明确属于用户真实业务状态的数据。

### 8.2 Derived / Rebuildable Data

应允许删除并重建的数据，包括但不限于：

- Chunks；
- Embeddings；
- Vector Index；
- Search Index；
- Cached Retrieval Results；
- 可重新生成的 AI Summary；
- Derived Learner State；
- 其他从 Durable Data 推导出的状态。

工程原则：

> **如果 Derived Data 被删除，Askora 应能够从 Durable Data 恢复到正确状态。**

Embedding、Vector Index、BM25 Index 等不得被视为不可替代的权威数据。

---

## 9. 删除、回收站与恢复

Askora 不采用“普通删除 = 立即永久删除”。

### 9.1 两阶段删除

```text
Normal
→ Trash
→ Permanent Delete
```

普通删除进入本地回收站。

永久删除：

- 必须由用户明确触发，或
- 由预定义本地清理周期执行。

建议默认允许一定保留期，例如 30 天；具体 UX 与周期可在后续规范中配置。

### 9.2 Project 与 Material 删除语义

必须区分：

- **从 Project 移除**：只删除 Project-Material 关系；
- **删除 Material**：删除资料本体；
- 如果 Material 仍被其他 Project 引用，系统必须明确提示。

### 9.3 Undo 与版本历史

Askora v1：

- 不建设通用 Undo 系统；
- 不建设 Command History；
- 不建设全局 Ctrl+Z 语义；
- 不建设通用版本历史；
- 删除恢复通过回收站完成，而不是通过全局 Undo 完成。

---

## 10. 学习目标、学习路径与状态模型

### 10.1 Learning Goal

一个 Learning Project 可以包含多个 Learning Goal。

v1 支持：

```text
Goal
└── Subgoal
```

只支持两级目标结构，不建设无限层级目标树。

### 10.2 Learning Path

用户可以手动调整学习路径。

系统可以根据学习证据动态调整路径，但调整必须：

- 可解释；
- 可追溯；
- 受明确 Teaching Policy 或业务规则约束。

不允许“LLM 觉得这样更好”作为无结构的路径改写理由。

### 10.3 Learner State

Learner State：

- 是派生状态；
- 应尽可能能够由 Learning Evidence 重建；
- 不由用户直接修改；
- 不由 LLM 直接写入。

推荐至少考虑：

```text
LearnerState
├── mastery_estimate
├── confidence
├── evidence_count
├── last_assessed_at
├── retention_state
├── independence_level
└── transfer_evidence
```

UI 可以显示统一“掌握度”，但底层不得只保留一个单一分数。

### 10.4 用户自评

用户不能直接把掌握度改为某个百分比。

用户可以提交自评，例如：

- 完全不会；
- 有点熟悉；
- 基本掌握；
- 非常熟悉。

自评形成 `SelfAssessmentEvidence`，其权重应低于独立作答、延迟测试、迁移测试等行为证据。

---

## 11. Learning Evidence 与 Assessment

### 11.1 Learning Evidence

Learning Evidence 是 Learner State 的事实基础。

核心原则：

> **Conversation ≠ Learning Evidence。**

用户说“我懂了”不能直接证明掌握。

有效 Learning Evidence 应来自结构化评估，例如：

```text
Attempt
→ Assessment
→ LearningEvidence
→ LearnerState
```

### 11.2 Assessment

Assessment：

- 是独立领域对象；
- 不等同于 Assistant Message；
- 不要求所有学习活动都必须测验；
- 由 Teaching Policy 决定何时需要评估。

### 11.3 删除学习证据

允许删除单条学习记录或 Evidence。

如果被删除 Evidence 曾影响 Learner State：

> 系统必须重新计算相关 Learner State，而不能继续保留旧状态。

---

## 12. 学习进度与效果指标

Askora 不把“读了多少页”当作核心学习进度。

必须区分：

```text
Content Progress
Learning Progress
Mastery Progress
```

核心优先级：

1. 学习目标完成情况；
2. Knowledge Unit 掌握状态；
3. 独立作答能力；
4. 延迟保持；
5. 迁移能力；
6. 单位学习时间能力增益。

以下指标不得成为主要学习目标：

- engagement；
- 对话轮次；
- 点赞；
- 单纯使用时长；
- 阅读百分比。

---

## 13. Learning Session

Learning Session 是一次连续学习活动，不是聊天会话的同义词。

它可以包含：

```text
LearningSession
├── Explanation
├── SocraticQuestion
├── Exercise
├── Attempt
├── Assessment
├── Feedback
├── SourceReference
└── Reflection
```

Session：

- 必须归属于 Workspace；
- 不必须绑定 Learning Project；
- 可以直接基于 Material 开始。

---

## 14. Review Scheduling

延迟复习属于 Askora 核心学习能力。

v1 不应仅依赖固定：

```text
1d → 3d → 7d → 30d
```

建议 Review Scheduling 至少考虑：

- Learning Evidence；
- 遗忘风险；
- 学习目标优先级；
- 当前状态不确定性；
- 历史错误；
- 最近评估结果。

v1 优先采用确定性、可解释规则，不要求复杂 ML 或 RL。

---

## 15. Knowledge Model

### 15.1 Knowledge Unit

Knowledge Unit 是学习状态与评估的基本粒度。

允许的类型可包括：

- Concept；
- Fact；
- Principle；
- Procedure；
- Relationship；
- Skill。

这些属于类型，而非六套完全独立的数据体系。

内容层级可以表现为：

```text
Chapter
→ Topic
→ KnowledgeUnit
```

### 15.2 Chunk 不等于 Knowledge Unit

必须明确：

> **Chunk ≠ KnowledgeUnit。**

Chunk 是检索基础设施对象，Knowledge Unit 是学习领域对象。

Chunk 策略、长度或版本变化不得直接导致 Learner State 失去语义稳定性。

### 15.3 知识图谱

Askora 可以使用图结构表达关系，例如：

- prerequisite；
- part_of；
- related_to；
- contrasts_with；
- supports。

但 v1 不强制引入专用图数据库。

原则：

> **有图结构，不等于必须有 Graph Database。**

---

## 16. 用户笔记与 AI 提取内容

必须区分：

```text
SourceKnowledge
AIExtractedKnowledge
UserNote
LearningEvidence
```

用户笔记：

- 不是自动可信的知识事实；
- 可以作为教学上下文；
- 可以用于误解诊断；
- 可以用于复习提示。

AI 提取的 Knowledge Unit：

- 不自动等同于原文事实；
- 必须保留来源；
- 必须保留生成/提取版本；
- 建议保留置信度或等价质量信号。

---

## 17. 知识来源与外部知识边界

### 17.1 默认知识边界

Askora v1 的主要知识边界由用户主动提供的学习材料定义。

v1 暂不：

- 主动推荐用户未导入的外部学习资料；
- 自动搜索互联网并决定用户应该学什么；
- 把外部内容无提示混入用户资料。

### 17.2 External Explanation

AI 可以使用模型自身知识辅助解释，但必须区分：

- Source-grounded Knowledge；
- External Model Knowledge。

不得将模型自身知识伪装成用户资料中的内容。

### 17.3 Source-grounded Claim

任何声称“来自用户资料”的事实性内容必须具备 provenance。

例如：

```text
Material
→ Section
→ Passage
```

如果找不到足够依据：

> 必须显式降级、扩大检索或承认资料中暂未找到充分依据，不能伪造引用。

---

## 18. RAG 与 Retrieval

### 18.1 RAG 定位

RAG 是教学系统的知识供给基础设施，不是 Askora 产品本体。

正确依赖方向：

```text
Learning Goal
→ Teaching Policy
→ Knowledge Need
→ Retrieval
→ Knowledge Supply
→ Teaching Action
```

而不是：

```text
Document
→ Chunk
→ Embedding
→ RAG
→ Chat
```

### 18.2 Retrieval Scope

任何检索都必须受 Scope 约束。

建议支持：

```text
RetrievalScope
├── workspace_id
├── project_ids?
├── material_ids?
├── knowledge_unit_ids?
└── session_context?
```

不得默认无边界检索全部 Askora 数据。

---

## 19. AI Provider 与联网模型

### 19.1 BYOK

Askora v1 使用 BYOK（Bring Your Own Key）模式：

- 用户自行填写 AI API Key；
- Askora 不提供官方 AI 额度；
- Askora 不作为用户请求的必经云代理。

### 19.2 网络依赖

Askora 是 Local-first，但不是 Offline-only。

离线时应尽可能允许：

- 启动 Askora；
- 查看已有本地资料；
- 查看已有学习历史；
- 查看本地项目、目标和状态；
- 管理已有本地数据。

以下能力可依赖联网：

- AI Tutor；
- AI 内容理解；
- Knowledge Extraction；
- Embedding；
- AI Assessment；
- 其他外部 AI API 能力。

### 19.3 多 Provider

Askora 应允许多 AI Provider / Model Provider 抽象，例如：

- OpenAI；
- Anthropic；
- Google；
- OpenAI-compatible；
- 未来本地模型。

但 v1 不要求建设完整插件生态。

---

## 20. 扩展性

Askora 允许架构扩展，但 v1 不把通用插件系统作为核心产品能力。

允许：

- 模块化扩展；
- 新增 AI Provider；
- 新增 Embedding Provider；
- 新增 Content Parser；
- 新增 Retriever；
- 新增内部 Adapter。

v1 不要求：

- Plugin Marketplace；
- 第三方开发者生态；
- 通用运行时插件加载系统。

原则：

> **保持可扩展，但不为尚不存在的插件需求提前支付复杂度成本。**

---

## 21. AI 自动化权限与用户控制

### 21.1 Canonical State 写入

禁止：

```text
LLM
→ 直接修改 SQLite / Canonical State
```

推荐：

```text
LLM
→ Structured Proposal
→ Schema Validation
→ Application / Domain Rules
→ Persistent State
```

核心原则：

> **LLM 是推理与生成组件，不是业务状态权威。**

### 21.2 AI 可以自主执行的行为

AI 可以在明确边界内自主执行低风险、局部、可解释的教学动作，例如：

- 解释；
- 苏格拉底式提问；
- 提示；
- 支架增加或撤除；
- 补救练习；
- Teaching Policy 允许的下一步教学行为。

### 21.3 AI 默认不得直接执行的行为

以下能力默认只能建议或必须经过业务规则/用户确认：

- 创建高层 Learning Goal；
- 大规模调整 Learning Plan；
- 删除用户数据；
- 覆盖用户数据；
- 跨 Workspace 批量操作；
- 不可逆操作。

### 21.4 确认原则

强制确认只用于：

1. 不可逆操作；
2. 高影响批量操作；
3. 跨边界操作。

不得对普通低风险操作滥用确认弹窗。

### 21.5 Agent 边界

Askora v1 支持受约束自动化，不支持开放式长期自治 Agent。

不允许：

```text
AI 自行规划无限任务
→ 自行调用任意工具
→ 长期持续运行
→ 自行修改系统核心状态
```

---

## 22. 模型配置、路由与成本治理

### 22.1 用户模型配置

用户可以配置：

- Provider；
- Model；
- Embedding Model；
- 各类任务的默认模型。

高级生成参数不应成为普通用户的核心配置入口。

### 22.2 模型路由

Askora 可以针对不同任务使用不同模型，例如：

```text
KnowledgeExtraction → Model A
TeachingDialogue    → Model B
Assessment          → Model C
Embedding           → Embedding Model
```

模型切换必须受明确配置或确定性策略约束。

### 22.3 Fallback

禁止关键任务发生不可追踪的静默模型切换。

涉及以下任务时，必须记录实际使用模型、版本与 fallback 原因：

- Assessment；
- Knowledge Extraction；
- Learner State 相关关键推导；
- 其他影响核心学习状态的任务。

### 22.4 成本治理

BYOK 不等于无成本约束。

Askora 应能够记录或估计：

- 请求次数；
- input tokens；
- output tokens；
- Provider；
- Model；
- estimated cost。

并允许对高成本或批量 AI 操作提供限制或确认机制。

---

## 23. API Key 与 Secret

API Key：

- 仅保存在本机；
- 优先存入操作系统安全凭据存储；
- 不应明文写入 Workspace / Project 文件；
- 不上传 Askora 官方服务器；
- 不进入默认备份；
- 不进入默认诊断包；
- 不写入日志。

恢复 Askora Backup 后，用户可重新配置 API Key。

---

## 24. 配置分层

建议配置分三层：

```text
Application
↓
Workspace
↓
Project
```

Application：

- 默认 Provider；
- 默认模型；
- 数据目录；
- UI 等应用级设置。

Workspace：

- 工作空间级默认策略；
- 必要的学习偏好；
- 允许覆盖的模型配置。

Project：

- 项目范围资料；
- 项目目标；
- 必要的项目级模型覆盖。

下层只能覆盖明确允许覆盖的字段，不建设无限制配置继承系统。

---

## 25. 内容导入范围

### 25.1 v1 核心格式

Askora v1 核心支持：

- EPUB；
- PDF；
- Markdown；
- TXT。

### 25.2 暂不作为 v1 核心能力

以下能力暂不进入 v1 核心范围：

- 网页 URL 导入；
- Podcast；
- YouTube；
- 原生音频；
- 原生视频；
- RSS；
- DOCX；
- PPTX；
- XLSX；
- 企业数据源；
- Google Drive 团队库；
- Slack；
- 企业 Wiki。

这些能力未来可以通过 Importer / Adapter 演进。

### 25.3 OCR

v1 不建设完整 OCR Pipeline。

文本型 PDF 属于支持范围。

扫描 PDF 可以识别为无法可靠提取文本并提示用户，但不要求 v1 完整实现：

- OCR；
- 版面分析；
- 表格识别；
- 公式识别；
- 全套视觉文档理解。

---

## 26. 导入 Pipeline 与资料状态

资料导入不得仅用 `success / failure` 表达。

推荐采用阶段状态：

```text
Uploaded
→ SourceStored
→ Parsed
→ Structured
→ Indexed
→ KnowledgeModeled
→ Ready
```

整体状态至少应支持：

- pending；
- processing；
- ready；
- partial；
- failed。

允许部分成功。

例如：

```text
Parsed ✅
Indexed ✅
KnowledgeModeling ❌
```

资料仍应尽可能保持可用。

失败阶段可单独重试，不应默认从头重跑所有已成功阶段。

---

## 27. 重复资料

导入时应检测可能重复的资料，例如基于文件 Hash。

发现重复时：

- 可以提示使用已有资料；
- 可以允许用户明确创建新副本；
- 可以取消导入。

原则：

> **Detect duplicate，不强制 Deduplicate。**

---

## 28. 派生数据版本与重建

资料、解析器、Chunker、Embedding、Knowledge Model 等变化可能导致派生数据失效。

建议至少记录：

- source_version；
- parser_version；
- chunker_version；
- embedding_version；
- knowledge_model_version。

发生相关变化时：

```text
version changed
→ mark stale
→ rebuild affected derived data
```

不要求建设复杂 Build System，但必须具备依赖失效思想。

---

## 29. 后台任务

### 29.1 任务模型

Askora 支持本地后台任务，例如：

- EPUB / PDF 导入；
- Parsing；
- Chunking；
- Embedding；
- Knowledge Extraction；
- Indexing；
- Rebuild。

任务状态必须持久化，而不是仅存在内存。

建议状态：

```text
pending
running
succeeded
failed
interrupted
```

### 29.2 并发

后台任务允许有限并行，但必须有并发上限。

需要分别控制：

- Parsing；
- Embedding；
- AI API；
- Indexing；
- 其他高资源任务。

同一 Material 的同类重建任务必须支持去重或互斥。

### 29.3 关闭与恢复

Askora 不要求 Local Server 永久后台常驻。

App 关闭时：

- 任务必须安全中断；
- 下次启动可以 resume / retry / restart；
- 不得因中断破坏 Durable Data。

### 29.4 幂等与局部恢复

后台任务应尽可能：

- 幂等；
- 可去重；
- 可局部恢复；
- 不因下游失败重复执行无变化的上游步骤。

---

## 30. AI API 故障与重试

外部 AI Provider 必须被视为不可靠依赖。

至少区分：

- 429 / Rate Limit；
- 5xx；
- Timeout；
- Authentication Error；
- Invalid Request；
- Invalid Structured Output。

重试原则：

- 429 / 5xx / Timeout：有限重试 + 退避；
- API Key 错误：停止并提示；
- 输入非法：不应盲目重复调用；
- 禁止无限重试。

核心原则：

> **Retry 基于错误类型，而不是“失败就再试”。**

---

## 31. 性能与资源原则

Askora 面向个人长期数据规模，不按企业级多租户极端规模设计。

v1：

- 不给资料数量设置不必要的业务硬上限；
- 不轻易给单文件设置固定业务硬上限；
- 不承诺百万文档或企业级规模；
- 对超大资料允许降级、渐进处理或拒绝；
- 必须有 CPU / 内存 / 并发资源保护。

大型资料优先采用渐进处理：

```text
读取结构
→ 尽快提供可学习部分
→ 后台继续处理剩余内容
```

而不是必须全部 Embedding / Knowledge Modeling 完成后才允许进入学习。

工程优先级：

```text
数据正确性
>
可恢复性
>
教学决策正确性
>
交互响应
>
后台吞吐量
```

后台任务不得长期占满 CPU / 内存而破坏前台可交互性。

---

## 32. 数据备份与恢复

### 32.1 Backup

Backup 的目标：

> **恢复 Askora 本身。**

应定义 Askora 自有、版本化备份格式，例如：

```text
Askora Backup
├── manifest
├── durable database
├── source files
└── backup metadata
```

manifest 至少记录：

- backup_format_version；
- askora_version；
- schema_version；
- created_at；
- workspace scope。

默认不包含：

- API Key；
- 可重建 Cache；
- Embedding / Index 等非必要 Derived Data。

### 32.2 Export

Export 的目标：

> **让用户数据离开 Askora 后仍可使用。**

未来可支持：

- Markdown；
- JSON；
- CSV；
- 原始资料；
- 学习记录；
- 其他可互操作格式。

必须明确：

> **Backup ≠ Export。**

---

## 33. Schema Migration 与升级

### 33.1 Schema Migration

从 v1 开始必须建立正式 Schema Migration 机制：

```text
schema_version
migration_001
migration_002
...
```

不得依赖：

- 手工删除数据库；
- 运行时偷偷修改未知 Schema；
- “字段不存在就 ALTER”式无版本迁移。

### 33.2 升级安全

推荐升级流程：

```text
检测版本
→ 备份核心数据
→ 执行 Migration
→ 验证
├── success → continue
└── failure → rollback / preserve old data
```

### 33.3 向前迁移

Askora 追求：

> **旧数据可以迁移到新版本。**

不要求新版本运行时永久保持对所有历史 Schema 的直接兼容。

### 33.4 数据目录兼容性

数据目录应记录：

- schema_version；
- minimum_reader_version；
- minimum_writer_version。

程序打开数据目录前必须检查兼容性。

原则：

> **宁可拒绝打开，也不能在不确定兼容时直接写入。**

---

## 34. 日志、诊断与隐私

### 34.1 Local Observability

Askora v1 需要本地可观测性，用于诊断，而不是运营分析。

可以包含：

- Logs；
- Job Status；
- Pipeline State；
- DecisionTrace；
- Model Call Metadata；
- Diagnostics。

v1 默认不依赖远程 Analytics / Observability 才能正常工作。

### 34.2 日志最小化

默认日志应记录：

- error code；
- component；
- task ID；
- duration；
- provider / model；
- token usage；
- pipeline stage；
- 必要诊断元数据。

默认不记录：

- API Key；
- 整本原文；
- 完整用户回答；
- 完整 Prompt；
- 完整聊天记录。

### 34.3 诊断模式

允许显式启用更详细诊断模式，但不得默认永久开启。

### 34.4 诊断包

用户可以主动导出诊断包。

默认诊断包可以包含：

- Askora 版本；
- 系统环境；
- 任务状态；
- 错误日志；
- 配置摘要；
- 模型名称；
- 时间戳。

默认不包含：

- API Key；
- 原始资料全文；
- 完整 Prompt；
- 完整对话；
- User Note 正文。

如确有需要，必须由用户显式选择加入。

---

## 35. 遥测与官方云

Askora v1：

- 不提供 Askora 官方云同步；
- 默认不上传用户学习数据；
- 默认不依赖远程 Feature Flag；
- 默认不依赖远程 Analytics；
- 默认不依赖远程 Sentry / PostHog / Mixpanel / Segment 等服务；
- 不建设必须存在的 Askora 中心服务。

未来如引入官方云能力，必须作为新的产品定位决策重新冻结。

---

## 36. 测试、Replay 与环境隔离

### 36.1 环境隔离

至少逻辑区分：

- Development；
- Testing；
- Production Local。

不同环境应隔离：

- 数据目录；
- SQLite；
- 日志；
- API 配置；
- Test Fixtures。

测试不得默认修改用户真实 AskoraData。

### 36.2 核心逻辑可测试

以下核心系统必须能够脱离浏览器 UI 进行确定性测试：

- Teaching Policy；
- Assessment；
- Learner State Update；
- Review Scheduler；
- Retrieval；
- Content Pipeline。

UI 是 Adapter，不是核心业务逻辑所在地。

### 36.3 Replay

不要求记录所有 UI 点击。

以下关键路径应具备足够的 replay / trace 能力：

- Teaching Decision；
- Assessment；
- Learner State Update；
- Import Pipeline；
- Knowledge Extraction；
- Model Invocation Metadata。

目标是能够回答：

> “当时为什么得到这个教学决策或状态变化？”

---

## 37. 浏览器与部署边界

Askora v1：

- 正式 UI 入口为浏览器；
- 优先支持 Chrome / Edge；
- Local Server 默认绑定 localhost；
- 不以 Docker 作为最终用户前置条件；
- 不以公网部署为产品目标；
- 不保证将 Local Server 直接部署到远程服务器后仍属于受支持产品形态。

---

## 38. v1 Non-goals

以下明确不属于 Askora v1 目标：

- 多用户；
- 登录注册；
- 团队协作；
- SaaS 多租户；
- Askora 官方中心服务器依赖；
- Askora 官方云同步；
- Askora 官方 AI 额度服务；
- 多设备实时同步；
- macOS 原生客户端；
- Windows 原生客户端；
- iOS；
- Android；
- 公网服务；
- LAN Server 产品化；
- 企业知识库；
- 通用知识管理平台；
- ChatGPT 替代品；
- 社交功能；
- 开放式长期自治 Agent；
- Plugin Marketplace；
- 第三方开发者生态作为 v1 必须项；
- 主动推荐用户未导入的外部学习资料；
- 自动互联网探索并决定学习内容；
- 完整 OCR 系统；
- 原生音视频学习 Pipeline；
- Podcast / YouTube / RSS 作为 v1 核心输入；
- Redis 运行依赖；
- PostgreSQL 运行依赖；
- Docker 运行依赖；
- Kubernetes / Kafka / 分布式基础设施；
- 通用版本历史；
- 全局 Undo；
- 为未来云同步提前建设高复杂度同步协议；
- 以 engagement / 对话轮数作为核心学习 KPI。

---

## 39. Hard Constraints

以下原则视为 Askora 上位不可违反约束：

1. **Askora 是学习工具，不是 ChatGPT 替代品。**
2. **Askora v1 是单用户 Local Web Application。**
3. **Askora 不依赖官方中心服务器才能运行。**
4. **核心学习数据默认保存在用户本机。**
5. **用户自行提供 AI API Key。**
6. **LLM 不得直接成为 Canonical State 的权威写入者。**
7. **Learning Evidence 是 Learner State 的事实基础。**
8. **Learner State 是可重建的派生状态，而不是用户或 LLM 任意填写的字段。**
9. **任何 Source-grounded Claim 必须可追溯。**
10. **Chunk 不等于 Knowledge Unit。**
11. **Embedding / Index 等 Derived Data 必须允许重建。**
12. **AI Provider 失败不得破坏 Durable Data。**
13. **后台任务必须可恢复、可诊断，并尽可能幂等。**
14. **Schema Migration 是基础设施，不是未来补丁。**
15. **未来能力优先通过 Migration 演进，不提前引入分布式复杂度。**
16. **BYOK 仍然需要模型与成本治理。**
17. **自动化必须有边界、可审计、可解释。**
18. **用户拥有核心产品状态；Teaching Policy 只拥有受约束教学动作。**
19. **Backup 与 Export 必须区分。**
20. **下位 Canonical Design / ADR / SPEC / EXEC 不得擅自突破本文件与 v1 Non-goals。**

---

## 40. Deferred Decisions

以下事项暂不永久冻结，应在未来版本按需求重新评估：

- 是否提供 Askora 官方云；
- 是否支持多设备同步；
- 是否提供原生桌面客户端；
- 是否支持移动端；
- 是否支持更多 UI 语言；
- 是否提供本地模型；
- 是否建设公开插件系统；
- 是否建设 Plugin Marketplace；
- 是否支持网页 / Podcast / YouTube / RSS；
- 是否建设完整 OCR / 多模态文档理解；
- 是否允许跨 Workspace 资料共享；
- 是否引入专用图数据库；
- 是否提供远程访问模式；
- 是否提供官方 AI 服务；
- 是否建设更复杂的模型 Router；
- 是否引入监督学习、Contextual Bandit、Offline RL 或其他策略学习机制。

“暂不实现”不等于“永久禁止”。

---

## 41. 明确不在本文冻结的事项

以下内容统一在 **设计系统 → 交互元素（Interactive Elements）** 中冻结，不属于本 `PRODUCT-POSITIONING.md` 的职责：

- 顶层导航结构；
- 首页职责；
- 首页布局；
- 页面级信息架构；
- 具体页面层级；
- 按钮与入口；
- 搜索入口呈现；
- Chat-like UI 的具体视觉形式；
- 交互控件；
- Design System Components；
- 页面级 UX Flow。

本文件可以约束这些设计不得违背产品定位，但不决定具体 UI/UX 方案。

---

## 42. 下位文档执行规则

所有后续设计和开发任务开始前，应检查是否与本文件冲突。

建议优先级：

```text
PRODUCT-POSITIONING.md
        ↓
Canonical Design
        ↓
ADR
        ↓
SPEC
        ↓
EXEC
        ↓
Code
```

如果下位设计需要突破现有约束：

```text
发现冲突
→ 提出 Product Positioning Delta
→ 明确理由与影响
→ 重新冻结
→ 再修改下位设计
```

禁止：

```text
Codex / AI 认为某方案更方便
→ 擅自突破产品边界
```

---

## 43. 最终工程判断标准

当存在多个技术方案时，应优先选择：

```text
更符合长期学习目标
>
数据正确与可恢复
>
可解释与可测试
>
本地单机简单性
>
未来可演进性
>
当前实现便利
```

Askora v1 不追求“技术栈最先进”或“基础设施最完整”。

目标是：

> **以尽可能少的系统复杂度，构建一个长期正确、可验证、可迁移、可扩展的个人 AI 学习系统。**
