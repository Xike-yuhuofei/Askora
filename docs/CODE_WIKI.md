# Askora Code Wiki

> 生成时间：2026-08-08
> 版本：v0.3 Adaptive Teaching Loop
> 项目性质：私人自用、本地优先的 AI 学习应用

---

## 目录

- [1. 项目概述](#1-项目概述)
- [2. 整体架构](#2-整体架构)
- [3. 八类技术系统](#3-八类技术系统)
- [4. 后端架构](#4-后端架构)
  - [4.1 目录结构](#41-目录结构)
  - [4.2 核心配置](#42-核心配置)
  - [4.3 公共合同层 (Contracts)](#43-公共合同层-contracts)
  - [4.4 领域层 (Domains)](#44-领域层-domains)
  - [4.5 编排层 (Orchestration)](#45-编排层-orchestration)
  - [4.6 教学引擎层 (Engines)](#46-教学引擎层-engines)
  - [4.7 服务层 (Services)](#47-服务层-services)
  - [4.8 数据模型层 (Models)](#48-数据模型层-models)
  - [4.9 API 层](#49-api-层)
  - [4.10 基础设施层 (Infrastructure)](#410-基础设施层-infrastructure)
- [5. 前端架构](#5-前端架构)
  - [5.1 目录结构](#51-目录结构)
  - [5.2 技术栈](#52-技术栈)
  - [5.3 关键组件](#53-关键组件)
  - [5.4 路由系统](#54-路由系统)
  - [5.5 API 客户端](#55-api-客户端)
  - [5.6 Electron 桌面壳](#56-electron-桌面壳)
- [6. 数据库设计](#6-数据库设计)
- [7. 依赖关系](#7-依赖关系)
- [8. 项目运行方式](#8-项目运行方式)
  - [8.1 环境要求](#81-环境要求)
  - [8.2 后端运行](#82-后端运行)
  - [8.3 前端运行](#83-前端运行)
  - [8.4 桌面版构建](#84-桌面版构建)
  - [8.5 Docker 部署](#85-docker-部署)
  - [8.6 测试与验证](#86-测试与验证)
- [9. 核心业务流程](#9-核心业务流程)
- [10. 规范与约束](#10-规范与约束)

---

## 1. 项目概述

**Askora** 是一个私人自用、不公开发布的本地 AI 学习 App。仓库包含 FastAPI 后端、React/Vite 前端和 macOS Electron 桌面壳；默认运行边界是单用户、单设备、本地优先，而不是多租户 SaaS 或公共互联网服务。

### 核心特性

- **八大技术系统**：内容解析、检索供给、学习者建模、评估诊断、教学策略、路径调度、记忆复习、LLM 编排
- **确定性教学策略**：B3 确定性单决策内核，支持六类策略家族
- **多模型路由**：支持通义千问、DeepSeek、豆包三家国产大模型
- **文档知识库**：支持 EPUB、PDF、DOCX 等多种文档格式的解析和向量化
- **自适应教学循环**：v0.3 版本实现完整的 Adaptive Teaching Loop

### 当前基线状态

```
Engineering Gate: PASS
Policy Correctness Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

---

## 2. 整体架构

### 架构原则

| 原则 | 说明 |
|------|------|
| **Learning Loop, Not Chat-first** | Canonical 主链是学习闭环，不是闲聊 |
| **Decision vs Generation** | LLM 只生成候选，不拥有最终决定权 |
| **Single Writer** | 每类 canonical truth 有唯一 owner |
| **Immutable History** | 关键事件、决策均为不可变版本化记录 |
| **Local-first** | 单用户、单设备、本地优先 |
| **Baseline Before Advanced** | 高级算法必须有透明 baseline |

### 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                     Askora 应用层                        │
├─────────────┬───────────────────────────┬───────────────┤
│  前端 Web/Electron  │    FastAPI 后端    │   桌面壳 (Electron)  │
├─────────────┼───────────────────────────┼───────────────┤
│             │  API 路由层 (api/v1)      │               │
│             ├───────────────────────────┤               │
│             │  Contracts 公共合同层       │               │
│             ├───────────────────────────┤               │
│             │  Orchestration 编排层      │               │
│             ├───────────────────────────┤               │
│             │  Domains 领域层 (SYS01-07) │               │
│             ├───────────────────────────┤               │
│             │  Engines 教学引擎层         │               │
│             ├───────────────────────────┤               │
│             │  Services 服务层            │               │
│             ├───────────────────────────┤               │
│             │  Infrastructure 基础设施   │               │
│             ├───────────────────────────┤               │
│             │  Models 数据模型层          │               │
├─────────────┼───────────────────────────┼───────────────┤
│             │  PostgreSQL / SQLite      │               │
│             │  Redis                    │               │
└─────────────┴───────────────────────────┴───────────────┘
```

### 教学主链路

```text
TeachingContext + PolicyBundle
→ SYS05 TeachingAction / DecisionTrace
→ SYS02 EvidenceBundle
→ SYS08 受约束执行
→ SYS04 Attempt / AssessmentResult
→ SYS03 LearnerEvidence / MasteryEstimate
→ SYS07 ReviewSchedule
→ SYS06 在触发时重规划
```

---

## 3. 八类技术系统

| 系统编号 | 系统名称 | 核心所有者 | 关键对象 |
|---------|---------|-----------|---------|
| SYS01 | 内容解析与知识建模 | `content_knowledge/` | `SourceDocument`, `KnowledgeUnit`, `Concept`, `PrerequisiteRelation`, `Misconception` |
| SYS02 | 检索与知识供给 | `retrieval/` | `EvidenceBundle`, `RetrievalTrace` |
| SYS03 | 学习者建模 | `learner_model/` | `LearnerState`, `MasteryEstimate`, `LearnerEvidence`, `MisconceptionHypothesis` |
| SYS04 | 评估与错误诊断 | `assessment/` | `AssessmentItem`, `Attempt`, `AssessmentResult`, `MisconceptionEvidence` |
| SYS05 | 教学策略选择 | `teaching_policy/` | `TeachingAction`, `PolicyBundle`, `TeachingContext`, `DecisionTrace` |
| SYS06 | 学习路径与任务调度 | `learning_planner/` | `LearningPlan`, `LearningActivity`, `LearningGoal` |
| SYS07 | 记忆保持与复习调度 | `review_scheduler/` | `ReviewSchedule`, `next_due_at` |
| SYS08 | LLM/Agent 编排与可信控制 | `orchestration/`, `engines/` | Session 执行状态, ModelRoute, ToolCall, PromptVersion |

### 策略家族 (StrategyFamily)

```text
EXPLICIT_INSTRUCTION    — 直接讲解
GUIDED_PRACTICE         — 引导式练习
FADING_PRACTICE         — 渐隐练习
RETRIEVAL_PRACTICE      — 检索练习
ERROR_REMEDIATION       — 错误补救
TRANSFER_CHALLENGE      — 迁移挑战
```

### 辅助维度

```text
scaffold_control  = NONE|LOW|MEDIUM|HIGH
hint_specificity  = NONE|ORIENTATION|CONCEPTUAL_STRATEGIC|SUBGOAL|PARTIAL_STEP|BOTTOM_OUT
answer_exposure   = NONE|PARTIAL|COMPLETE
```

---

## 4. 后端架构

### 4.1 目录结构

```
apps/backend/app/
├── api/                          # API 路由层
│   └── v1/
│       ├── auth.py               # 认证接口
│       ├── dialog.py             # 对话接口
│       ├── documents.py          # 文档管理接口
│       ├── orchestrator.py       # 编排器调试接口
│       ├── users.py              # 用户接口
│       ├── workspace.py          # 工作区接口
│       └── ws.py                 # WebSocket 接口
├── contracts/                    # 公共合同层（跨系统共享）
│   ├── adaptive.py               # v0.3 自适应合同
│   ├── assessment.py             # 评估合同
│   ├── base.py                   # 合同基类
│   ├── content.py                # 内容/知识合同
│   ├── decisions.py              # 决策合同
│   ├── events.py                 # 事件合同
│   ├── learning.py               # 学习合同
│   ├── planning.py               # 规划合同
│   ├── rendering.py              # 渲染合同
│   ├── v03_migration.py          # v0.3 迁移合同
│   └── workspace.py              # 工作区查询合同
├── core/                         # 核心基础设施
│   ├── config.py                 # 应用配置
│   ├── database.py               # 数据库连接管理
│   ├── encryption.py             # 加密工具
│   ├── exceptions.py             # 异常定义
│   ├── logging.py                # 日志配置
│   └── redis_client.py           # Redis 客户端
├── data/                         # 静态种子数据
│   ├── knowledge/                # 知识库种子
│   └── strategies/               # 策略 YAML/JSON
├── domains/                      # 领域层（八大系统实现）
│   ├── assessment/               # SYS04 评估
│   ├── content_knowledge/        # SYS01 内容与知识
│   ├── learner_model/            # SYS03 学习者建模
│   ├── learning_planner/         # SYS06 学习规划
│   ├── retrieval/                # SYS02 检索
│   ├── review_scheduler/         # SYS07 复习调度
│   └── teaching_policy/          # SYS05 教学策略
├── engines/                      # 教学引擎层
│   ├── _registry.py              # 引擎注册表
│   ├── base.py                   # TEI 基类
│   ├── orchestrator.py           # LearningFlowOrchestrator
│   ├── repository.py             # 引擎持久化仓库
│   ├── state_graph.py            # 状态机引擎
│   ├── drill_engine.py           # Drill 引擎
│   ├── explain_engine.py         # Explain 引擎
│   ├── inquiry_engine.py         # Inquiry 引擎
│   ├── quiz_engine.py            # Quiz 引擎
│   ├── socratic/                 # Socratic 引擎子目录
│   └── socratic_adapter.py       # Socratic 适配器
├── gateway/                      # 网关中间件
├── infrastructure/               # 基础设施持久化
│   ├── adaptive_records.py       # v0.3 自适应记录
│   ├── learning_records.py       # 学习记录
│   ├── ledger.py                 # 账本
│   ├── outbox.py                 # Outbox 模式
│   └── planning_records.py       # 规划记录
├── models/                       # ORM 数据模型
├── orchestration/                # 编排层
│   ├── adaptive_execution.py     # 自适应执行服务
│   ├── learning_facade.py        # LearningOrchestrationFacade
│   └── review_planning.py        # 复习规划
├── queries/                      # 只读查询边界
├── services/                     # 服务层
│   ├── assessment/               # 评估服务
│   ├── auth/                     # 认证服务
│   ├── dialog/                   # 对话服务
│   ├── documents/               # 文档服务
│   ├── dkt/                      # DKT 知识追踪
│   ├── kt/                       # KT 知识追踪
│   ├── knowledge_graph/          # 知识图谱
│   ├── llm/                      # LLM 模型路由
│   ├── storage/                  # 本地存储
│   └── websocket/                # WebSocket 管理
├── workers/                      # 后台任务 Workers
├── main.py                       # FastAPI 应用入口
├── metrics.py                    # Prometheus 指标
├── observability.py              # 可观测性
└── security.py                   # 安全相关
```

### 4.2 核心配置

**文件**: [config.py](../apps/backend/app/core/config.py)

`Settings` 类基于 `pydantic-settings`，从 `.env` 文件加载配置：

| 配置项 | 类型 | 默认值 | 说明 |
|-------|------|--------|------|
| `app_env` | `AppEnv` | `DEVELOPMENT` | 运行环境 |
| `host` | `str` | `127.0.0.1` | 监听地址 |
| `port` | `int` | `8000` | 监听端口 |
| `database_url` | `str` | `postgresql+asyncpg://...` | 数据库连接 |
| `redis_url` | `str` | `redis://localhost:6379/0` | Redis 连接 |
| `jwt_secret_key` | `str` | `change-me-in-production` | JWT 密钥 |
| `llm_default_provider` | `LLMProvider` | `QWEN` | 默认 LLM 供应商 |
| `llm_qwen_api_key` | `str` | `""` | 通义千问 API Key |
| `llm_deepseek_api_key` | `str` | `""` | DeepSeek API Key |
| `llm_doubao_api_key` | `str` | `""` | 豆包 API Key |
| `embedding_model` | `str` | `text-embedding-v2` | Embedding 模型 |

**环境枚举**: `LOCAL`, `DEVELOPMENT`, `TEST`, `STAGING`, `PRODUCTION`

### 4.3 公共合同层 (Contracts)

**目录**: [contracts/](../apps/backend/app/contracts/)

Contracts 是跨八大系统共享的唯一公共合同入口，所有系统间通信通过这里定义的类型进行：

| 文件 | 核心类型 | 说明 |
|------|---------|------|
| `adaptive.py` | `TeachingContextV03`, `TeachingActionV03`, `PolicyBundleV03`, `EvidenceBundleV03` | v0.3 自适应教学核心合同 |
| `learning.py` | `LearningPlan`, `LearningActivity`, `MasteryEstimate`, `ReviewSchedule` | 学习与掌握合同 |
| `decisions.py` | `DecisionTraceV03`, `DecisionFeatureV03`, `HardConstraintResultV03` | 决策追踪合同 |
| `events.py` | `LearningEventEnvelopeV03`, `ActualAssistanceRecordedPayloadV03` | 事件合同 |
| `content.py` | `KnowledgeUnit`, `SourceSpan`, `SourceChunk`, `PrerequisiteRelation` | 内容知识合同 |
| `assessment.py` | `AssessmentItemV1`, `AssessmentAttempt`, `AssistanceSnapshot` | 评估合同 |
| `planning.py` | `LearningGoalV1`, `DiagnosticNeedV1`, `GoalKnowledgeMappingV1` | 规划合同 |
| `rendering.py` | `RenderPayloadV1`, `markdown_render_payload` | 渲染合同 |
| `workspace.py` | `LibraryWorkspaceResponseV1`, `TodayWorkspaceResponseV1` | 工作区查询合同 |
| `v03_migration.py` | `MigrationCandidate`, `MigrationProjection`, `upcast_v03_compatibility` | v0.3 迁移工具 |

### 4.4 领域层 (Domains)

#### SYS05 - 教学策略 (teaching_policy)

**核心文件**: [kernel.py](../apps/backend/app/domains/teaching_policy/kernel.py)

**`TeachingPolicyKernel`** — B3 确定性单决策内核

决策流程：
```text
validate_policy_input 输入校验
→ evaluate_hard_constraints 硬约束评估
→ derive_teaching_stage 推导教学阶段
→ generate_candidates 生成候选动作
→ build_candidate_features 构建特征
→ score_candidate 打分
→ select_stably 确定性选择
→ 生成 TeachingActionV03 + DecisionTraceV03
```

关键依赖模块：

| 文件 | 功能 |
|------|------|
| `candidates.py` | 候选动作表与生成 |
| `constraints.py` | 硬约束评估 |
| `features.py` | 特征构建 |
| `scoring.py` | 归一化加权打分 |
| `stages.py` | 教学阶段推导 |
| `models.py` | `PolicyRuntimeProfile`, `PolicyDecision`, `PolicyDecisionError` |
| `sequential.py` | 顺序过渡策略 |
| `validation.py` | 输入校验 |

#### SYS01 - 内容与知识 (content_knowledge)

| 文件 | 功能 |
|------|------|
| `publication.py` | 知识发布流水线 |
| `projections.py` | 内容投影 |
| `epub_structure.py` | EPUB 结构解析 |
| `revision_builder.py` | 修订构建 |
| `safety.py` | 内容安全检查 |

#### SYS02 - 检索 (retrieval)

| 文件 | 功能 |
|------|------|
| `evidence_service.py` | 标准证据检索 |
| `adaptive_evidence_service.py` | v0.3 自适应证据检索 |

#### SYS03 - 学习者建模 (learner_model)

| 文件 | 功能 |
|------|------|
| `projector.py` | 学习者状态投影 |
| `state_projector.py` | 状态投影器 |
| `adaptive_eligibility.py` | 自适应资格判断 |

#### SYS04 - 评估 (assessment)

| 文件 | 功能 |
|------|------|
| `service.py` | 评估服务 |
| `adaptive_service.py` | 自适应评估服务 |

#### SYS06 - 学习规划 (learning_planner)

| 文件 | 功能 |
|------|------|
| `planner.py` | 学习规划器 |
| `diagnostic.py` | 诊断规划 |
| `goal_mapping.py` | 目标-知识映射 |

#### SYS07 - 复习调度 (review_scheduler)

| 文件 | 功能 |
|------|------|
| `scheduler.py` | 复习调度器 |

### 4.5 编排层 (Orchestration)

#### LearningOrchestrationFacade

**文件**: [learning_facade.py](../apps/backend/app/orchestration/learning_facade.py)

这是整个应用的生产入口，所有普通和流式传输都通过它执行：

```python
class LearningOrchestrationFacade:
    async def run_turn(self, request: CanonicalTurnRequest) -> CanonicalTurnResult
    async def stream_turn(self, request: CanonicalTurnRequest) -> AsyncIterator[CanonicalStreamEvent]
```

**核心请求/响应类型**：

| 类型 | 说明 |
|------|------|
| `CanonicalTurnRequest` | 单轮请求，包含用户输入、会话信息、可选的 v0.3 自适应字段 |
| `CanonicalTurnResult` | 单轮结果，包含回复文本、引擎信息、决策追踪等 |
| `CanonicalStreamEvent` | 流式事件（content/final） |

**双路径执行逻辑**：
- 如果请求中包含完整的 v0.3 自适应字段（`teaching_context_v03` + `policy_bundle_v03` + `policy_profile_v03` + `adaptive_retrieval_candidates`），走 v0.3 自适应路径
- 否则走 legacy v0.2 兼容路径

#### AdaptiveExecutionService

**文件**: [adaptive_execution.py](../apps/backend/app/orchestration/adaptive_execution.py)

v0.3 自适应执行服务，负责：
- 调用 LLM 生成教学内容
- 约束输出符合 `TeachingAction` 信封
- 记录实际协助状态
- 生成渲染载荷

### 4.6 教学引擎层 (Engines)

#### TEI (Teaching Engine Interface)

**基类**: [base.py](../apps/backend/app/engines/base.py)

所有教学引擎必须实现 TEI 接口的四个方法：

| 方法 | 说明 |
|------|------|
| `can_handle(flow_stage, shared_ctx)` | 返回引擎对当前阶段的处理能力评分 |
| `step(learner_input, flow_stage, shared_ctx, engine_state)` | 执行一步教学交互 |
| `build_initial_state(shared_ctx)` | 构建引擎初始私有状态 |
| `on_enter(shared_ctx)` | 引擎被激活时的生命周期钩子 |
| `on_exit(shared_ctx)` | 引擎被切出时的生命周期钩子 |

#### LearningFlowOrchestrator

**文件**: [orchestrator.py](../apps/backend/app/engines/orchestrator.py)

教学引擎编排器，核心调度层：

```python
class LearningFlowOrchestrator:
    async def ensure_session(session_id, **kwargs) -> SharedContext
    async def create_session(session_id, ...) -> SharedContext
    async def run_turn(session_id, learner_turn, ...) -> OrchestratorTurnResult
```

**核心职责**：
- 持有 per-session 的 `SharedContext` + 各引擎私有状态快照
- 每轮调用当前引擎的 `step()`
- 处理引擎切换（STAY / SWITCH_TO / SWITCH_AND_RETURN / END_FLOW）
- 应用引擎建议的副作用到 `SharedContext`
- 唯一的 `SharedContext` 写入权限

#### 引擎注册表

**文件**: [_registry.py](../apps/backend/app/engines/_registry.py)

使用 `@register_engine` 装饰器自动注册引擎：

```python
ENGINE_REGISTRY: dict[str, type[TeachingEngine]]
def register_engine(engine_id: str): ...
def list_registered_engines() -> list[str]: ...
```

#### 已实现引擎

| 引擎 ID | 文件 | 说明 |
|---------|------|------|
| `socratic` | `socratic/` + `socratic_adapter.py` | 苏格拉底式提问引擎 |
| `explain` | `explain_engine.py` | 讲解引擎 |
| `quiz` | `quiz_engine.py` | 测验引擎 |
| `drill` | `drill_engine.py` |  Drill 练习引擎 |
| `inquiry` | `inquiry_engine.py` | 探究引擎 |

#### SharedContext

引擎间共享的上下文数据结构：

```python
@dataclass
class SharedContext:
    subject: str
    knowledge_point_id: Optional[str]
    current_flow_stage: FlowStage
    mastery_vector: dict[str, float]
    mastery_confidence: dict[str, float]
    identified_gaps: list[KnowledgeGap]
    recent_wrong_streak: int
    last_hint_level_used: int
    explained_concept_ids: set[str]
    produced_assets: list[ProducedAsset]
    current_engine_id: Optional[str]
    learner_persona: str
    extras: dict[str, Any]
    engine_trace: list[TransitionRecord]
```

### 4.7 服务层 (Services)

#### DialogService

**文件**: [dialog_service.py](../apps/backend/app/services/dialog/dialog_service.py)

对话传输适配器，连接 API 层与 `LearningOrchestrationFacade`：

```python
class DialogService:
    async def create_session(user, subject, knowledge_point_id) -> DialogSession
    async def get_session(session_id) -> Optional[DialogSession]
    async def get_user_sessions(user_id, limit, offset) -> list[DialogSession]
    async def get_session_messages(session_id, limit, offset, latest) -> list[DialogMessage]
    async def send_message(session, user, content, ...) -> dict
    async def stream_message(session, user, content, ...) -> AsyncGenerator
    async def end_session(session) -> DialogSession
```

#### ModelRouter

**文件**: [model_router.py](../apps/backend/app/services/llm/model_router.py)

多模型供应商路由层：

| 供应商类 | 说明 |
|---------|------|
| `QwenProvider` | 通义千问（主力模型） |
| `DeepSeekProvider` | DeepSeek（数学专项） |
| `DoubaoProvider` | 豆包（低成本备选） |

**`ModelRouter`** 核心方法：
- `route_for_subject(subject)` — 按学科路由（数学 → DeepSeek）
- `route_for_cost(cost_sensitivity)` — 按成本敏感度路由
- `chat_completion_with_fallback(messages, subject)` — 带降级的对话补全

#### 其他服务

| 服务目录 | 文件 | 说明 |
|---------|------|------|
| `services/auth/` | `auth_service.py`, `token_service.py`, `dependencies.py` | JWT 认证与授权 |
| `services/documents/` | `document_service.py`, `embedding_service.py`, `rag_service.py` | 文档解析与 RAG |
| `services/assessment/` | `assessment_service.py`, `canonical_service.py` | 评估服务 |
| `services/kt/` | `knowledge_tracing_service.py`, `canonical_projector.py` | 知识追踪 |
| `services/dkt/` | `dkt_service.py` | Deep Knowledge Tracing |
| `services/knowledge_graph/` | `kg_service.py` | 知识图谱服务 |
| `services/storage/` | `local_storage.py` | 本地文件存储 |
| `services/websocket/` | `ws_manager.py` | WebSocket 连接管理 |

### 4.8 数据模型层 (Models)

**目录**: [models/](../apps/backend/app/models/)

核心 ORM 模型：

| 文件 | 核心模型 | 说明 |
|------|---------|------|
| `user.py` | `User`, `UserRole`, `UserStatus` | 用户 |
| `profile.py` | `UserProfile` | 用户画像 |
| `dialog.py` | `DialogSession`, `DialogMessage`, `MessageRole` | 对话会话与消息 |
| `document.py` | `UserDocument`, `DocumentChunk`, `ProcessingStatus` | 文档与分块 |
| `knowledge.py` | `KnowledgePoint`, `LearningMaterial` | 知识点与材料 |
| `assessment.py` | `AssessmentItem`, `AssessmentResult` | 评估项与结果 |
| `planning.py` | `LearningGoalRecord`, `LearningPlanRecord`, `LearningActivityRecord` | 学习目标与计划 |
| `adaptive.py` | `TeachingActionV03Record`, `TeachingContextRecord`, `PolicyBundleRecord` | v0.3 自适应记录 |
| `ledger.py` | `DecisionTraceRecord`, `LearningEventRecord`, `OutboxTaskRecord` | 账本与事件 |

### 4.9 API 层

**目录**: [api/v1/](../apps/backend/app/api/v1/)

#### API 路由表

| 路由前缀 | 路由器 | 说明 |
|---------|--------|------|
| `/api/v1` | `auth_router` | 登录、注册、Token 刷新 |
| `/api/v1` | `dialog_router` | 创建会话、发送/流式消息 |
| `/api/v1` | `users_router` | 用户信息、昵称修改 |
| `/api/v1` | `documents_router` | 文档上传、列表、删除 |
| `/api/v1` | `workspace_router` | 工作区查询（Today/Library） |
| `/api/v1` | `ws_router` | WebSocket 对话通道 |
| `/api/v1` | `orchestrator_router` | 编排器调试（仅非生产） |

#### 关键端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/auth/login` | 用户登录 |
| `POST` | `/auth/refresh` | 刷新 Token |
| `POST` | `/dialog/sessions` | 创建对话会话 |
| `GET` | `/dialog/sessions` | 获取会话列表 |
| `POST` | `/dialog/sessions/{id}/messages` | 发送消息（非流式） |
| `POST` | `/dialog/sessions/{id}/stream` | 发送消息（流式 SSE） |
| `GET` | `/workspace/today` | Today 视图数据 |
| `GET` | `/workspace/library` | 图书馆数据 |
| `POST` | `/documents/uploads` | 上传文档 |
| `GET` | `/documents` | 文档列表 |
| `GET` | `/health` | 健康检查 |
| `GET` | `/health/config` | 配置状态 |

### 4.10 基础设施层 (Infrastructure)

**目录**: [infrastructure/](../apps/backend/app/infrastructure/)

| 文件 | 功能 |
|------|------|
| `adaptive_records.py` | v0.3 自适应记录持久化 |
| `learning_records.py` | 学习记录持久化 |
| `ledger.py` | 事件账本 |
| `outbox.py` | Outbox 模式实现（可靠事件传递） |
| `planning_records.py` | 规划记录持久化 |

**Workers** — 后台任务处理：

| 文件 | 功能 |
|------|------|
| `task_queue.py` | 任务队列 |
| `handlers.py` | 任务处理器 |
| `durable_outbox.py` | 持久化 Outbox Worker |
| `__main__.py` | Worker 启动入口 |

---

## 5. 前端架构

### 5.1 目录结构

```
apps/frontend/
├── electron/                     # Electron 桌面壳
│   ├── main.cjs                  # Electron 主进程
│   ├── preload.cjs               # 预加载脚本
│   └── app-menu.cjs              # 应用菜单
├── resources/
│   └── backend/                  # 后端二进制打包目录
├── src/
│   ├── api/                      # API 客户端
│   │   ├── client.js             # Axios 实例与拦截器
│   │   ├── auth.js               # 认证 API
│   │   ├── dialog.js             # 对话 API
│   │   ├── documents.js          # 文档 API
│   │   ├── users.js              # 用户 API
│   │   └── workspace.js          # 工作区 API
│   ├── components/               # 可复用组件
│   │   ├── messages/
│   │   │   ├── RichMessage.jsx   # 富文本消息渲染
│   │   │   └── SafeMarkdown.jsx  # 安全 Markdown 渲染
│   │   ├── AppShell.jsx          # 应用外壳布局
│   │   ├── Sidebar.jsx           # 侧边导航栏
│   │   ├── ProtectedRoute.jsx    # 路由保护
│   │   ├── NoticeModal.jsx       # 通知弹窗
│   │   └── SourceStatus.jsx      # 源状态组件
│   ├── hooks/
│   │   └── useAuth.jsx           # 认证 Hook
│   ├── pages/                    # 页面组件
│   │   ├── Login.jsx             # 登录页
│   │   ├── Today.jsx             # Today 工作区
│   │   ├── Library.jsx           # 图书馆
│   │   ├── History.jsx           # 历史记录
│   │   ├── TutorWorkspace.jsx    # 教学工作区
│   │   ├── Settings.jsx          # 设置
│   │   ├── Profile.jsx           # 个人资料
│   │   ├── Account.jsx           # 账户
│   │   └── Unavailable.jsx       # 功能未开放页
│   ├── styles/
│   │   └── global.css            # 全局样式
│   ├── test/                     # 前端测试
│   ├── App.jsx                   # 应用根组件
│   ├── main.jsx                  # 入口文件
│   └── router.jsx                # 自定义路由系统
├── assets/                       # 静态资源
├── index.html                    # HTML 入口
├── vite.config.js                # Vite 配置
└── package.json                  # 依赖与脚本
```

### 5.2 技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| 框架 | React | 18.3.1 |
| 构建工具 | Vite | 8.2.0 |
| HTTP 客户端 | Axios | 1.7.2 |
| Markdown 渲染 | react-markdown | 10.1.0 |
| 数学公式 | KaTeX + remark-math + rehype-katex | - |
| 图标 | lucide-react | 0.424.0 |
| 桌面壳 | Electron | 43.3.0 |
| 打包 | electron-builder | 26.15.3 |
| 测试 | Vitest + Testing Library | 4.1.10 |

### 5.3 关键组件

#### AppShell

**文件**: [AppShell.jsx](../apps/frontend/src/components/AppShell.jsx)

应用外壳布局，提供两种变体：
- `standard` — 标准页面布局（带侧边栏）
- `workspace` — 教学工作区布局

#### RichMessage

**文件**: [RichMessage.jsx](../apps/frontend/src/components/messages/RichMessage.jsx)

富文本消息渲染组件，支持：
- Markdown 渲染
- LaTeX 数学公式
- 代码高亮
- 安全降级（SafeMarkdown 组件）

#### Sidebar

**文件**: [Sidebar.jsx](../apps/frontend/src/components/Sidebar.jsx)

侧边导航栏，提供页面导航入口。

### 5.4 路由系统

**文件**: [router.jsx](../apps/frontend/src/router.jsx)

基于 Hash 的自定义路由系统：

```javascript
// 核心 API
RouterProvider     // 路由上下文提供者
useLocation()      // 获取当前路径
useNavigate()      // 导航函数
Navigate           // 声明式导航组件
NavLink            // 导航链接组件
```

**路由映射**：

| 路径 | 页面 | Shell 变体 |
|------|------|-----------|
| `/login` | Login | - |
| `/today` | Today | standard |
| `/library` | Library | standard |
| `/history` | History | standard |
| `/settings` | Settings | standard |
| `/quick/:sessionId` | TutorWorkspace | workspace |
| `/learn/:activityId` | Unavailable | workspace |

### 5.5 API 客户端

**文件**: [client.js](../apps/frontend/src/api/client.js)

基于 Axios 的 API 客户端：

**核心功能**：
- 自动 Token 附加（Bearer Auth）
- 设备指纹绑定
- 401 自动刷新 Token
- 系统级错误全局弹窗

```javascript
// API 实例
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

// 请求拦截器：附加 Token + 设备指纹
api.interceptors.request.use(async (config) => { ... })

// 响应拦截器：401 自动刷新
api.interceptors.response.use(null, async (error) => { ... })
```

**前端 API 模块**：

| 文件 | 函数 | 说明 |
|------|------|------|
| `auth.js` | `login`, `refreshToken` | 认证 |
| `dialog.js` | `createSession`, `sendMessage`, `streamMessage` | 对话 |
| `documents.js` | `uploadDocument`, `listDocuments` | 文档 |
| `users.js` | `getProfile`, `updateNickname` | 用户 |
| `workspace.js` | `getTodayData`, `getLibraryData` | 工作区 |

### 5.6 Electron 桌面壳

**文件**: [main.cjs](../apps/frontend/electron/main.cjs)

macOS 桌面壳，核心功能：
- 内嵌 Python 后端（PyInstaller 打包）
- 预加载 API 桥接（`preload.cjs`）
- 原生应用菜单（`app-menu.cjs`）

**构建脚本**：
```bash
npm run electron:build:mac:with-backend
```

---

## 6. 数据库设计

### 数据库类型

| 模式 | 数据库 | 说明 |
|------|--------|------|
| 本地开发 | SQLite | 零配置、文件级权限保护 |
| 生产/容器 | PostgreSQL 16 | 完整 RDBMS 功能 |
| 缓存 | Redis 7 | 会话缓存、降级到内存 |

### 核心数据表

#### 用户与认证
- `users` — 用户表
- `user_profiles` — 用户画像

#### 对话系统
- `dialog_sessions` — 对话会话
- `dialog_messages` — 对话消息

#### 文档与知识
- `user_documents` — 用户文档
- `document_chunks` — 文档分块
- `knowledge_points` — 知识点
- `learning_materials` — 学习材料

#### 评估系统
- `assessment_items` — 评估项
- `assessment_results` — 评估结果

#### v0.3 自适应
- `teaching_contexts` — 教学上下文
- `teaching_actions_v03` — v0.3 教学动作
- `policy_bundles` — 策略包
- `teaching_episodes` — 教学插曲
- `learning_trajectories` — 学习轨迹
- `outcome_observations` — 结果观测
- `experiment_assignments` — 实验分配

#### 规划与复习
- `learning_goals` — 学习目标
- `learning_plans` — 学习计划
- `learning_activities` — 学习活动
- `review_schedules` — 复习调度
- `diagnostic_needs` — 诊断需求

#### 账本
- `decision_traces` — 决策追踪
- `decision_trace_inputs` — 决策输入
- `learning_events` — 学习事件
- `outbox_tasks` — Outbox 任务

### 数据库迁移

使用 Alembic 进行版本化迁移：

```bash
cd apps/backend
uv run alembic upgrade head
uv run alembic check
```

迁移脚本目录：`apps/backend/alembic/versions/`

---

## 7. 依赖关系

### 后端依赖 (pyproject.toml)

#### 核心运行时

| 包名 | 版本 | 说明 |
|------|------|------|
| `fastapi` | >=0.110.0 | Web 框架 |
| `uvicorn[standard]` | >=0.27.0 | ASGI 服务器 |
| `sqlalchemy[asyncio]` | >=2.0.0 | ORM |
| `alembic` | >=1.13.0 | 数据库迁移 |
| `asyncpg` | >=0.29.0 | PostgreSQL 异步驱动 |
| `aiosqlite` | >=0.20.0 | SQLite 异步驱动 |
| `redis` | >=5.0.0 | Redis 客户端 |
| `pydantic` | >=2.6.0 | 数据校验 |
| `pydantic-settings` | >=2.2.0 | 配置管理 |
| `PyJWT[crypto]` | >=2.10.1 | JWT |
| `passlib[bcrypt]` | >=1.7.4 | 密码哈希 |
| `cryptography` | >=42.0.0 | 加密 |
| `httpx` | >=0.27.0 | HTTP 客户端 |
| `prometheus-client` | >=0.20.0 | Metrics |
| `structlog` | >=24.1.0 | 结构化日志 |
| `jieba` | >=0.42.1 | 中文分词 |
| `ebooklib` | >=0.18 | EPUB 解析 |
| `pdfplumber` | >=0.11.0 | PDF 解析 |
| `python-docx` | >=1.1.0 | DOCX 解析 |

#### 开发依赖

| 包名 | 版本 | 说明 |
|------|------|------|
| `pytest` | >=8.0.0 | 测试框架 |
| `pytest-asyncio` | >=0.23.0 | 异步测试 |
| `pytest-cov` | >=4.1.0 | 覆盖率 |
| `black` | >=24.2.0 | 代码格式化 |
| `ruff` | >=0.3.0 | Linter |
| `mypy` | >=1.8.0 | 类型检查 |
| `factory-boy` | >=3.3.0 | 测试工厂 |
| `faker` | >=23.0.0 | 假数据生成 |

### 前端依赖 (package.json)

| 包名 | 版本 | 说明 |
|------|------|------|
| `react` | ^18.3.1 | React 框架 |
| `react-dom` | ^18.3.1 | React DOM |
| `axios` | ^1.7.2 | HTTP 客户端 |
| `react-markdown` | ^10.1.0 | Markdown 渲染 |
| `katex` | ^0.18.1 | 数学公式渲染 |
| `lucide-react` | ^0.424.0 | 图标库 |
| `remark-gfm` | ^4.0.1 | GFM 支持 |
| `remark-math` | ^6.0.0 | 数学语法 |
| `rehype-katex` | ^7.0.1 | KaTeX 编译 |

### 系统依赖关系图

```text
                    ┌─────────────┐
                    │  FastAPI App  │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
     ┌────────▼───┐  ┌────▼────┐  ┌───▼────────┐
     │ API Routes  │  │  Core   │  │  Workers   │
     └────────┬───┘  └────┬────┘  └───┬────────┘
              │            │            │
              │     ┌──────▼──────┐     │
              │     │  Contracts  │     │
              │     └──────┬──────┘     │
              │            │            │
     ┌────────▼─────────────▼────────────▼──┐
     │        LearningOrchestrationFacade    │
     └────────────────┬────────────────────┘
                      │
     ┌────────────────┼────────────────────┐
     │                │                    │
┌────▼────┐   ┌───────▼──────┐   ┌────────▼─────────┐
│Engines  │   │  Domains     │   │   Services       │
│(TEI)    │   │ (SYS01-07)   │   │ (LLM/Auth/Docs)  │
└────┬────┘   └───────┬──────┘   └────────┬─────────┘
     │                │                    │
     └────────────────┼────────────────────┘
                      │
            ┌─────────▼─────────┐
            │  Infrastructure    │
            │  (Outbox/Ledger)   │
            └─────────┬─────────┘
                      │
            ┌─────────▼─────────┐
            │  Models (ORM)      │
            └─────────┬─────────┘
                      │
            ┌─────────▼─────────┐
            │  PostgreSQL/SQLite │
            │  Redis             │
            └───────────────────┘
```

---

## 8. 项目运行方式

### 8.1 环境要求

| 组件 | 版本要求 |
|------|---------|
| Python | 3.11 或 3.12 |
| uv | 0.9.5 |
| Node.js | 22（最低 20.19+） |
| npm | 最新 |
| PostgreSQL | 16（可选，本地用 SQLite） |
| Redis | 7（可选，不可用时降级） |
| Docker | 最新（可选） |
| Xcode CLT | 构建 macOS 桌面版时需要 |

### 8.2 后端运行

```bash
cd apps/backend

# 1. 安装依赖
python -m pip install uv==0.9.5
uv sync --frozen --extra dev --extra desktop

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，设置：
#   - APP_ENV=local
#   - LLM Keys（需要真实模型时填写）
#   - 数据库密码、JWT Key 等

# 3. 数据库迁移
uv run alembic upgrade head

# 4. 启动服务
uv run python -m app.main

# 或者使用 uvicorn 直接启动
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

服务启动后：
- API 根路径：`http://127.0.0.1:8000`
- Swagger 文档：`http://127.0.0.1:8000/docs`
- 健康检查：`http://127.0.0.1:8000/health`

### 8.3 前端运行

```bash
cd apps/frontend

# 1. 安装依赖
npm ci

# 2. 启动开发服务器
npm run dev

# 开发页面：http://127.0.0.1:5173
# API 默认：http://127.0.0.1:8000/api/v1
```

### 8.4 桌面版构建

```bash
cd apps/frontend

# 构建包含后端的 macOS 桌面版
npm run electron:build:mac:with-backend

# 产物位置：apps/frontend/release/
```

### 8.5 Docker 部署

```bash
# 1. 配置环境
cp .env.example .env
# 设置随机数据库密码、JWT/KEK 密钥、LLM Key

# 2. 配置检查
docker compose config

# 3. 启动所有服务
docker compose up --build
```

### 8.6 测试与验证

#### 后端测试

```bash
cd apps/backend

# 运行全部测试
uv run pytest tests --cov=app --cov-report=term-missing --cov-fail-under=45

# Ruff 代码检查
uv run ruff check app tests scripts

# Mypy 类型检查
uv run mypy app --no-error-summary

# Black 格式检查
uv run python ../../.github/workflows/check_black_baseline.py

# Alembic 迁移检查
uv run alembic check

# 单独的集成测试
uv run python test_document_service.py
uv run python test_optimizations.py
```

#### 前端构建

```bash
cd apps/frontend

# 生产构建
npm run build

# 依赖安全审计
npm audit --audit-level=high
```

#### 文档检查

```bash
python3 .github/workflows/check_docs.py
```

---

## 9. 核心业务流程

### v0.3 自适应教学流程

```text
1. 用户发起学习请求
   └→ 通过 API /dialog/sessions/{id}/messages 进入

2. DialogService.send_message()
   └→ 调用 LearningOrchestrationFacade.run_turn()

3. LearningOrchestrationFacade._execute_turn()
   ├── 检测输入是否包含 v0.3 自适应字段
   │   ├── 是 → _execute_adaptive_turn()
   │   └── 否 → _execute_legacy_turn()

4. v0.3 自适应路径
   ├── TeachingPolicyKernel.decide()
   │   ├── validate_policy_input()
   │   ├── evaluate_hard_constraints()
   │   ├── derive_teaching_stage()
   │   ├── generate_candidates()
   │   ├── build_candidate_features()
   │   ├── score_candidate()
   │   └── 生成 TeachingActionV03 + DecisionTraceV03
   │
   ├── AdaptiveEvidenceRetriever.build()
   │   └→ 构建 EvidenceBundleV03
   │
   └── AdaptiveExecutionService.execute()
       ├── 约束 TeachingAction 信封
       ├── 调用 LLM 生成内容
       ├── 记录 ActualAssistance
       └── 返回渲染后的结果

5. Legacy v0.2 兼容路径
   ├── LearningFlowOrchestrator.run_turn()
   │   ├── 获取/创建会话
   │   ├── 选择当前引擎
   │   ├── 调用引擎 step()
   │   ├── 应用副作用
   │   └── 处理引擎切换
   │
   └── 返回 CanonicalTurnResult
```

### 引擎切换流程

```text
当前引擎执行 step()
  → 返回 EngineStepResult（含 transition suggestion）
  → Orchestrator 处理 transition：
      ├── STAY: 留在当前引擎
      ├── SWITCH_TO: 切换到目标引擎
      │   ├── on_exit(from_engine)
      │   ├── 记录 TransitionRecord
      │   ├── build_initial_state(to_engine)
      │   └── on_enter(to_engine)
      ├── SWITCH_AND_RETURN: 切换并完成后返回
      │   └── 压栈当前引擎，完成后自动返回
      └── END_FLOW: 结束当前流程
```

### 文档处理流程

```text
用户上传文档
  → DocumentService 接收
  → ProcessingWorker 异步处理
      ├── 格式检测（EPUB/PDF/DOCX）
      ├── 文本提取与解析
      ├── 分块（Chunking）
      ├── Embedding 向量化
      └── 存储到 DocumentChunk
  → 处理完成后可供检索使用
```

---

## 10. 规范与约束

### 权威优先级

```text
1. docs/specs/
2. docs/adr/
3. docs/design/ 中的 Canonical Design
4. 当前代码、数据库迁移和测试
5. Codex 自主推断
```

### 八类系统不可越权规则

- **SYS05 (教学策略)** 是 `TeachingAction` 的唯一 owner
- **SYS03 (学习者建模)** 是 `MasteryEstimate` 的唯一 owner
- **SYS04 (评估)** 是 `AssessmentResult` 的唯一 owner
- **SYS08 (LLM 编排)** 不得直接写 LearnerState/Plan/ReviewSchedule
- **SYS02 (检索)** 不得扩大或自行改变 TeachingAction
- **任何模块** 不得直接写入其他系统拥有的业务状态

### 禁止的架构实践

- 同时拥有八类决策的 TutorAgent
- direct chat 与 canonical teaching 两条默认主链并存
- 跨 owner 写入
- SYS08/SYS02 扩大 action envelope
- 为架构美观大爆炸重写
- 永久双写两套事实源

### 版本化配置参数

以下参数必须保持 versioned/traceable configurable：
- mastery threshold
- failure ceiling
- minimum dwell
- switch margin
- hint sequence
- scaffold fade amount
- diagnostic confidence cutoff
- transfer novelty threshold
- delay windows
- policy weights
- practical harm margin

### 完成定义 (Definition of Done)

1. 所有明确 Acceptance Criteria 已满足
2. 未违反状态所有权和依赖规则
3. 必要数据库迁移可前向执行并有明确回滚策略
4. 新增关键行为存在自动化测试
5. 错误、重试、幂等和观测行为符合 Spec
6. 无未声明的公共 API/Schema 变化
7. 所有 SPEC GAP 已显式报告
8. 没有占位实现或伪完成

---

> **文档维护说明**：本 Wiki 应随代码演进持续更新。当核心模块发生结构性变化时，请同步更新对应章节。
