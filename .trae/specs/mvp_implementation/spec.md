# Askora MVP Implementation - Product Requirement Document

## Overview
- **Summary**: 本项目旨在为 Askora 苏格拉底式教学 App 构建 MVP (Minimum Viable Product) 核心能力。基于架构设计文档，将在现有后端骨架（TEI、Orchestrator）之上，实现苏格拉底引擎的六大核心子模块、知识追踪（BKT）、基础 RAG 流水线、以及补充 Drill（练习）和 Inquiry（探究）两个教学引擎，从而形成完整的"诊断-学习-验证-练习"闭环，验证苏格拉底教学法的技术可行性。
- **Purpose**: 验证苏格拉底教学法的有效性，构建最小可用的教学闭环，支撑初期用户测试。
- **Target Users**: K12 学生、终身学习者。

## Goals
- **G1**: 实现苏格拉底引擎内部的七大核心子模块，确保所有 AI 输出经过教学法过滤。
- **G2**: 建立基础的知识追踪能力（BKT），支持自适应提示级别调整。
- **G3**: 搭建基础 RAG 流水线，结合 pgvector 提供领域知识检索能力。
- **G4**: 扩展教学引擎矩阵，支持 Drill（练习）和 Inquiry（探究）场景。
- **G5**: 建立 MVP 版本的策略库（30+ 核心学科模板）。

## Non-Goals (Out of Scope)
- **NG1**: 不实现多 Agent 编排架构（StateGraph），单引擎内部逻辑调用即可。
- **NG2**: 不实现 DKT 深度知识追踪模型，仅采用 BKT 或简化规则。
- **NG3**: 不实现 Neo4j 知识图谱，仅使用关系型数据库或内存结构模拟图谱关联。
- **NG4**: 不实现完整的评估服务（Assessment Service）独立部署。
- **NG5**: 不实现 Kubernetes 部署与完整监控体系。
- **NG6**: 不实现 Prompt 版本管理与 A/B 测试框架。

## Background & Context
- **Existing System**: 当前代码库已具备 TEI (Teaching Engine Interface) 接口定义、LearningFlowOrchestrator 调度器、以及 SocraticEngine (适配器)、ExplainEngine、QuizEngine 三个引擎的骨架。
- **Technical Landscape**: 采用 Python 3.11 + FastAPI + PostgreSQL + Redis + pgvector 技术栈。
- **Architecture Reference**: 参考 `docs/architecture/socratic-app-architecture/socratic-app-architecture.html`。

## Functional Requirements

### 苏格拉底引擎核心子模块 (`app/engines/socratic/`)
- **FR-1 (Input Parser)**: 实现输入解析模块，支持意图识别、知识点定位、困惑识别、情感状态推断。
- **FR-2 (Strategy Library)**: 建立三级分类的策略库（元认知目标 -> 认知技能 -> 学科情境），内置 30+ 核心模板。
- **FR-3 (Strategy Selector)**: 实现策略选择器，根据掌握度、对话历史、情感状态加权选择最佳提问策略。
- **FR-4 (Graduated Hinting)**: 实现五级渐次提示生成器（元认知->概念->策略->结构->定向），支持动态升降级调整。
- **FR-5 (Reflection Trigger)**: 实现反思触发模块，支持事后反思、过程中反思、自我解释三种模式。
- **FR-6 (Output Guardrail)**: 实现三层输出验证（规则引擎/Schema验证/LLM分类器），确保答案零容忍。

### 教学引擎扩展 (`app/engines/`)
- **FR-7**: 实现 `DrillEngine`（练习引擎），支持变式练习和错题巩固。
- **FR-8**: 实现 `InquiryEngine`（探究引擎），支持基于问题的探究式学习。

### AI 服务层 (`app/services/`)
- **FR-9 (Knowledge Tracing)**: 实现基于 BKT 模型的知识追踪服务，提供 `get_mastery` 和 `update_mastery` 接口。
- **FR-10 (RAG Service)**: 实现基础 RAG 服务，支持文档摄取、向量化（pgvector）、相似度检索。

### 数据与模型 (`app/models/`, `app/models/knowledge.py`)
- **FR-11**: 扩展数据模型，支持 `strategy_templates`（策略模板）和 `learning_materials`（学习素材）的存储。

## Non-Functional Requirements
- **NFR-1 (Performance)**: 单次 `step()` 调用端到端延迟 P95 < 5s。
- **NFR-2 (Compliance)**: 严格遵守 PII 与学习数据物理隔离原则，引擎内不处理用户真实身份。
- **NFR-3 (Extensibility)**: 所有新引擎必须通过 `@register_engine` 装饰器注册，遵循 TEI 接口规范。
- **NFR-4 (Testability)**: 核心策略选择和提示生成逻辑必须单元测试覆盖。

## Constraints
- **Technical**: 必须兼容现有 Python 3.11 + FastAPI 环境；Redis 作为会话缓存唯一存储。
- **Business**: 开发周期 1-3 个月，需快速迭代。
- **Dependencies**: 依赖 `pgvector` 扩展进行向量存储。

## Assumptions
- **A1**: 现有 `socratic_engine.py` 中的旧逻辑将被新子模块替换，但 `socratic_adapter.py` 的对外接口保持不变。
- **A2**: MVP 阶段使用伪数据或固定题库进行演示，暂不依赖复杂的外部知识图谱数据源。

## Acceptance Criteria

### AC-1: 输入解析功能
- **Given**: 用户输入 "我不太理解为什么要移项"
- **When**: 调用 `InputParser.parse()`
- **Then**: 返回 `intent="confusion_expression"`, `knowledge_points=["kp_algebra_transposition"]`, `confusion_type="conceptual_misunderstanding"`
- **Verification**: `programmatic`

### AC-2: 策略选择与提示
- **Given**: 当前掌握度 p=0.3（低），用户连续回答错误 2 次
- **When**: `StrategySelector` 结合 `HintingGenerator` 进行决策
- **Then**: 选择适合低掌握度的策略，并将提示级别提升至 Level 3 或更高
- **Verification**: `programmatic`

### AC-3: 输出验证（防答案泄露）
- **Given**: LLM 生成的回复中包含 "答案是 x=3"
- **When**: `OutputGuardrail.validate()` 检测该回复
- **Then**: 验证不通过，触发重新生成或降级策略
- **Verification**: `programmatic`

### AC-4: BKT 知识追踪
- **Given**: 用户对知识点 `kp_1` 的掌握度初始为 0.5
- **When**: 用户连续答对 3 次
- **Then**: `get_mastery("kp_1")` 返回的掌握度值应显著提升（>0.8）
- **Verification**: `programmatic`

### AC-5: 引擎注册与路由
- **Given**: 系统已加载 `DrillEngine` 和 `InquiryEngine`
- **When**: `LearningFlowOrchestrator` 处理 `FlowStage.DRILL` 请求
- **Then**: `can_handle()` 返回评分最高的引擎应为 `DrillEngine`
- **Verification**: `programmatic`

## Open Questions
- [ ] RAG 索引的初始化数据来源是什么？（手动导入还是预置 JSON？）
- [ ] BKT 模型的初始参数（p_init, p_transit, p_slip, p_guess）如何设定？
