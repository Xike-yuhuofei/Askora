# Askora PRODUCT-POSITIONING

> 文档状态：Frozen Product Boundary  
> 冻结日期：2026-08-13  
> 适用范围：Askora v1 及后续 Product Definition / Experience Design / Spec / Code  
> 上游战略：[`PRODUCT-STRATEGY.md`](PRODUCT-STRATEGY.md)  
> 文档职责：回答 Category / Is / Is Not / Product Shape / Boundaries  
> 不包含：Product Discovery、页面 UX、领域 schema、API、数据库、任务、重试、日志、测试等实现 mechanics

---

## 1. 文档目的

本文件把 [`PRODUCT-STRATEGY.md`](PRODUCT-STRATEGY.md) 的战略意图转换为 Askora 的**可执行产品边界**。

它回答：

> **Askora 是什么、不是什么、v1 允许做成什么形态、哪些边界不能被下位设计或实现突破？**

本文件必须服从 Product Strategy；Product Definition、Experience Design、Specs 与代码必须服从本文件。Decision Log / ADR 解释选择理由，不能覆盖本文件。

如果实现与本文件冲突，默认属于 Design–Implementation / Product–Implementation Gap，不能用“已经实现了”反向定义产品。

---

## 2. Category Definition

Askora 的产品类别冻结为：

> **个人长期 AI 学习系统（Personal AI Learning System）。**

更具体地说，它是一个：

- 面向个人长期自主学习；
- 以用户学习材料和 Learning Goal 为主要起点；
- 以 Learning Evidence / Learner State 为学习状态基础；
- 以受约束 Teaching Policy 决定下一教学动作；
- 以独立、延迟和迁移能力作为核心学习结果；
- 本地运行、用户控制核心学习数据的 AI 学习产品。

“个人学习操作系统”可以作为设计隐喻，但不是允许无限扩张 Scope 的正式产品类别。

---

## 3. One-sentence Positioning

> **Askora 是一个面向单用户长期个人学习的本地运行 AI 学习系统：它围绕用户自己的学习材料、目标和可审计 Learning Evidence 持续维护学习状态并决定下一步教学行动，核心目标是形成可验证的独立、保持与迁移能力，而不是提供一次性 AI 问答、通用知识管理或团队协作。**

---

## 4. What Askora Is

Askora 是：

- **个人长期学习工具**，而不是一次性任务助手；
- **AI 辅助教学系统**，而不是自由 LLM 对话壳；
- **learning-state-aware system**，需要跨时间维护目标、证据与状态；
- **evidence-driven system**，Learning Evidence 是掌握判断的事实基础；
- **material-grounded learning environment**，用户主动提供的材料构成主要学习知识边界；
- **local-first / locally operated product**，核心数据与产品运行不依赖 Askora 官方中心云；
- **single-user product**，优先服务一个人的长期学习，而不是组织与协作管理；
- **BYOK AI product**，用户自行提供外部 AI Provider 凭据，Askora 不以官方 AI 额度为 v1 前提。

核心学习闭环的现行合同由 Specs 定义，本文件只冻结其产品意义：

```text
Goal
→ Evidence / Learner State
→ Teaching Decision
→ Learning Activity
→ Attempt / Assessment
→ New Evidence
→ Review / Replan
→ Independent / Delayed / Transfer Validation
```

---

## 5. What Askora Is Not

Askora 不是：

- ChatGPT / Claude 类通用 AI Chat 替代品；
- 通用 AI Agent 平台；
- 通用知识管理工具；
- Notion / Obsidian / Zotero 替代品；
- 以 RAG 问答为产品本体的“AI 知识库”；
- 企业知识库；
- LMS / 学校管理系统；
- 团队协作产品；
- SaaS 多租户平台；
- 社交学习网络；
- 以内容消费量、对话时长或 engagement 为核心目标的产品。

`Conversation / Message / Prompt` 可以是交互对象，但不得成为 Askora 的核心产品领域模型。

---

## 6. Strategic Differentiation

Askora 的差异化不是某个单一功能。

以下能力即使存在，也不能单独定义 Askora：

- AI Chat；
- RAG；
- Quiz；
- Flashcard；
- Notes；
- Knowledge Graph；
- Socratic questioning；
- Spaced repetition。

Askora 的产品身份来自它们被组织进同一个长期学习控制闭环：

```text
Persistent Learning Goal
+
Evidence-backed Learner State
+
Explicit Teaching Policy
+
Assistance / Exposure Semantics
+
Independent Validation
+
Delayed Validation
+
Transfer Validation
+
Review / Replan
```

任何新 capability 如果不能明显强化该闭环，不应仅因“学习产品通常会有”而进入核心 Scope。

---

## 7. v1 Product Shape

### 7.1 Local Web Application

Askora v1 的正式交付形态是：

```text
Browser
→ loopback
Askora Local Server
→ local product data / learning core
→ external AI APIs when needed
```

产品级约束：

- v1 使用浏览器 Web UI；
- Local Server 运行于用户自己的设备；
- 核心使用不依赖 Askora 官方中心服务器；
- 默认不作为公网服务或 LAN 产品提供；
- v1 不提供 macOS / Windows 原生客户端；
- v1 不提供 iOS / Android；
- v1 UI 以简体中文为当前正式产品语言。

浏览器版本、端口、进程管理、启动器、installer 等 mechanics 由下游产品定义与技术规范管理。

### 7.2 Single User / Single Device

Askora v1：

- 单用户；
- 单设备为正式使用前提；
- 无注册、登录、账号、密码、AuthSession；
- 无 Organization / Tenant / RBAC；
- 无多人协作；
- 无多设备实时同步。

`LocalOwner` 是本地学习数据归属主体，不是认证账号。

### 7.3 Local-first, Not Offline-only

Askora 的核心产品与学习数据本地优先，但 Askora **不是 Offline-only**。

外部 AI Provider 可以通过互联网提供：

- 教学语言生成；
- 内容理解；
- assessment assistance；
- embedding / extraction 等 AI 能力。

联网失败不应被解释为“用户没有学会”；具体故障、重试和降级由下游技术合同管理。

---

## 8. Data / Privacy / Ownership Boundaries

### 8.1 User-owned Core Learning Data

用户拥有其核心学习数据。

Askora v1 必须保持：

- 核心学习数据以用户本地数据为权威来源；
- 产品能够备份、恢复并导出用户数据；
- 默认不把学习数据上传到 Askora 官方中心云；
- API Key / Secret 不进入普通业务数据、日志、默认备份或默认导出。

具体 Durable / Derived 分类、backup format、schema migration、erasure mechanics 与 SecretStore adapter 由当前 Specs / ADR 定义，不在本文件重复。

### 8.2 No Mandatory Infrastructure Operations

最终用户不应为了使用 Askora 而必须手工部署、启动或维护：

- Docker；
- Redis；
- PostgreSQL；
- Kafka；
- Kubernetes；
- Elasticsearch cluster；
- 远程 backend infrastructure。

这些技术可以作为开发、测试、兼容或未来方案，但不能成为 v1 最终用户产品前置条件。

本约束冻结“产品运行负担”，不冻结具体 persistence / job 技术实现。

---

## 9. Knowledge and Content Boundary

### 9.1 Primary Knowledge Boundary

Askora v1 的主要学习知识边界由用户主动提供的材料定义。

Askora 可以使用模型自身知识进行解释，但必须保持：

```text
Source-grounded Knowledge
!=
External Model Knowledge
```

任何声称“来自用户资料”的事实必须能够追溯到真实来源。

### 9.2 Product Boundary

v1 不把以下方向作为核心产品身份：

- 自动探索互联网并决定用户应该学什么；
- 资讯推荐系统；
- 企业连接器平台；
- 开放内容 marketplace；
- 原生音视频平台。

具体 v1 import formats、parser、OCR、chunk/index 等属于 Product Definition / Technical Specs，不在本文件维护第二份列表。

---

## 10. Learning and AI Authority Boundaries

### 10.1 Learning Evidence Boundary

冻结：

> **Conversation ≠ Learning Evidence。**

以下均不能单独证明掌握：

- 用户说“我懂了”；
- AI 判断“用户懂了”；
- 阅读完成；
- 受助成功；
- answer-exposed success；
- activity completion；
- immediate correctness alone。

Learner State 必须建立在有语义区分的 Learning Evidence 之上。

### 10.2 LLM Authority Boundary

冻结：

> **LLM 是推理、生成与工具执行组件，不是 Canonical State 的最终业务权威。**

LLM / Agent 不得绕过明确业务规则直接成为：

- LearnerState owner；
- Assessment truth owner；
- Learning Goal / Plan owner；
- ReviewSchedule owner；
- high-impact TeachingAction 的无约束 owner；
- 用户数据不可逆操作的自行决定者。

精确 single-writer ownership 与 structured proposal contracts 由当前 Specs 管理；选择理由见 Decision Log / ADR。

### 10.3 User Autonomy Boundary

用户拥有删除数据、请求解释 / 答案 / 跳过、以及是否开始或停止学习等高层产品状态控制。学习目标由系统按产品规则生成并维护，开始学习不要求用户确认目标。

系统可以改变教学动作，但不能为了“尊重用户选择”伪造 evidence semantics。

例如：

> 用户要求完整答案可以被允许，但该次表现不能再被追溯性标记为无提示独立掌握。

---

## 11. Strategic Constraints

以下是 Askora v1 的产品级 Hard Boundaries：

1. **Askora 是个人长期学习系统，不是通用 AI Chat。**
2. **Askora 的核心优化目标是真实学习结果，不是 engagement。**
3. **Askora v1 是 single-user / single-device Local Web Application。**
4. **核心产品运行不依赖 Askora 官方中心服务器。**
5. **核心学习数据默认由用户本地持有。**
6. **AI 使用 BYOK；Askora v1 不要求官方 AI 额度服务。**
7. **用户提供的学习材料是主要知识边界；来源事实必须可追溯。**
8. **Learning Evidence 是 Learner State 的事实基础。**
9. **受助表现、答案暴露和独立表现必须保持不同证据语义。**
10. **LLM / Agent 不得成为核心 canonical learning state 的无约束权威。**
11. **系统按产品规则维护高层学习目标；开始学习不要求用户确认目标。Teaching Policy 只在受约束范围内控制教学动作。用户仍拥有数据删除、跳过与请求帮助 / 答案等产品状态控制。**
12. **最终用户不需要运维 Docker / Redis / PostgreSQL / 分布式基础设施才能正常使用。**
13. **系统复杂度必须与个人长期学习价值成比例。**
14. **下位 Design / ADR / Specs / EXEC 不得擅自突破本文件。**

这些约束决定“允许设计什么”，不定义具体实现方法。

---

## 12. v1 Non-goals

以下明确不属于 Askora v1 的正式目标：

### User / Organization

- 多用户；
- 注册登录；
- 账号体系；
- 团队协作；
- Organization / Tenant / RBAC；
- 学校或企业管理后台。

### Cloud / Distribution

- Askora 官方中心服务器作为产品运行前提；
- 官方云同步；
- 多设备实时同步；
- 公网 SaaS；
- LAN Server 产品化；
- 原生桌面或移动客户端。

### Product Category Expansion

- ChatGPT 替代品；
- 通用知识管理平台；
- 企业知识库；
- 社交产品；
- 内容 marketplace；
- 开放式长期自治 Agent 平台；
- Plugin Marketplace / 第三方开发者生态作为 v1 必需能力。

### Learning / AI

- 以 engagement / message count / session length 作为核心学习 KPI；
- 让自由 LLM 自行决定所有教学状态与高层计划；
- 用 synthetic learner 或工程 PASS 声称已经证明真人学习效果；
- 默认使用复杂 RL / multi-agent 作为核心 Teaching Policy 前提。

### Infrastructure

- Redis / PostgreSQL / Docker / Kafka / Kubernetes 等作为最终用户运行必需条件；
- 为未来云同步、多租户或企业规模提前建设高复杂度分布式系统。

---

## 13. Deferred Strategic Decisions

以下事项没有被永久禁止，但不属于当前 v1 Frozen Boundary：

- 官方云服务；
- 多设备同步；
- 原生桌面客户端；
- 移动端；
- 多语言 UI；
- 本地模型；
- 公开插件系统；
- 更多外部内容来源；
- 更广泛的自动 content discovery；
- 跨 Workspace 共享；
- 复杂模型 router；
- learned Teaching Policy / Contextual Bandit / Offline RL；
- 面向多用户或机构的产品形态。

任何 Deferred Decision 要进入正式 Scope，必须重新经过：

```text
Discovery / Evidence
→ Product Strategy check
→ Product Positioning Delta
→ 用户接受并重新冻结
→ 下游 Design / ADR / Spec
```

“当前不做”不等于“永久禁止”。

---

## 14. Downstream

本文件的直接下游是 [`PRODUCT-DEFINITION.md`](PRODUCT-DEFINITION.md)。Experience Design、Specs、Decision Log 与代码的入口见 [`../README.md`](../README.md)。

如果下游文档与 Product Positioning 冲突，应收敛下游；不得把 retry、schema、job state、logging fields 等复制回本文件。

---

## 15. Authority and Change Control

本文件下游是 [`PRODUCT-DEFINITION.md`](PRODUCT-DEFINITION.md)。完整权威顺序见 [`../README.md`](../README.md) 与仓库根 `AGENTS.md`。

如果下位工作需要突破本文件：

```text
发现 Product Boundary Conflict
→ 检查是否同时影响 Product Strategy
→ 提出 Product Positioning Delta
→ 说明新证据、理由与影响
→ 用户明确接受
→ 更新并重新冻结
→ 再修改下游 Experience Design / Specs / implementation
```

禁止：

```text
实现已经存在
或
AI / Codex 认为某方案更方便
→ 自动把它提升为 Product Requirement
```

---

## 16. Product Decision Test

任何新的大功能、架构或产品建议，在进入下游前至少必须通过四个问题：

1. **它是否直接强化 Askora 的长期学习闭环？**
2. **它是否服务当前 Primary User，而不是抽象的“所有用户”？**
3. **它是否改善独立能力、保持、迁移、可信状态或下一步教学决策？**
4. **它带来的产品与系统复杂度是否明显小于创造的长期学习价值？**

如果四个问题都无法给出明确答案，默认不进入核心 Scope。
