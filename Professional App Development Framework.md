# Professional App Development Framework

从第一性原理看，一个专业 App 的开发不是“写软件”，而是在持续完成四件事：

> **确定做什么 → 设计如何实现价值 → 构建可靠系统 → 在真实世界中验证并持续演化。**

因此，不建议把 Product、UX、Frontend、Testing、CI/CD 等全部平铺成同一级概念。更稳定的划分方式是：

**10 个生命周期一级模块 + 一组贯穿全生命周期的质量属性。**

这是我建议作为长期标准使用的框架。

---

# 1. 顶层框架

## Professional App Development Framework

| # | 一级模块 | 核心问题 |
|---|---|---|
| 1 | **Product Strategy & Discovery** | 为什么做？为谁做？解决什么问题？ |
| 2 | **Product Definition & Planning** | 到底做什么？边界是什么？如何验收？ |
| 3 | **Experience & Interface Design** | 用户如何理解、操作和完成任务？ |
| 4 | **Architecture & Technical Design** | 软件内部应该如何组织和运行？ |
| 5 | **Engineering Implementation** | 如何把设计变成可运行软件？ |
| 6 | **Quality Engineering & Risk Control** | 如何证明它正确、安全、稳定、可用？ |
| 7 | **Engineering Platform & Delivery** | 如何高质量、可重复地开发和交付？ |
| 8 | **Release & Production Operations** | 如何安全发布，并让生产环境长期可靠运行？ |
| 9 | **Measurement & Product Learning** | 产品实际效果如何？下一步该做什么？ |
| 10 | **Governance, Documentation & Evolution** | 如何保证几年之后系统仍然可理解、可维护、可演进？ |

这里的一个关键原则是：

**Security / Privacy / Performance / Accessibility / Reliability / Observability 并不是单独某个阶段，而是 Cross-cutting Quality Attributes。**

例如安全不能等到测试阶段才做。NIST SSDF明确建议将安全开发实践嵌入整个 SDLC；ISO/IEC 25010:2023 也把软件质量定义为需要在设计、测试、质量控制与验收阶段被明确规定和评价的属性。

---

# 2. 十个一级模块

## 01. Product Strategy & Discovery

**核心目标**

确认“值得做什么”，而不是立即讨论功能。

**主要工作**

- Idea / Opportunity
- 用户研究
- 市场与竞品研究
- 用户任务 / Pain Point
- Problem Definition
- Product Vision
- Value Proposition
- 商业目标
- 产品定位
- 风险与假设
- 技术可行性初步研究
- Success Metrics

**典型产物**

- Product Vision
- Product Positioning
- Research Findings
- Problem Statement
- Target Users
- JTBD / User Needs
- Product Principles
- KPI / North Star Metric
- Assumption List

**主要负责人**

Product Lead / Founder / PM，配合 UX Research、Engineering Lead、Data。

**输入**

Idea、市场机会、用户反馈。

**输出**

> **经过验证的问题空间。**

---

# 02. Product Definition & Planning

解决：

> **我们具体要构建什么？**

这和 UX 必须严格区分。

**主要工作**

- Product Scope
- Feature Definition
- Capability Model
- Information Architecture
- Requirement Definition
- User Story / Use Case
- Business Rules
- Functional Requirements
- Non-functional Requirements
- Acceptance Criteria
- MVP 边界
- Priority
- Roadmap
- Release Scope
- Dependencies

**典型产物**

- PRD
- Product Spec
- Feature Spec
- Requirement Backlog
- Acceptance Criteria
- Product Roadmap
- Domain Vocabulary

**负责人**

PM / Product Lead。

**输入**

Strategy & Discovery。

**输出**

> **明确的软件产品定义。**

---

# 03. Experience & Interface Design

这是完整的 **Product Experience Design**。

包含：

```text
Experience Design
├── UX
├── Information Architecture
├── Interaction Design
├── User Flow
├── Navigation
├── Wireframe
├── UI Design
├── Visual Design
├── Content Design
├── Accessibility Design
└── Design System
```

### UX

决定：

> 用户如何完成任务。

### Interaction Design

决定：

> 点击、拖动、输入、导航、反馈、状态变化如何发生。

### UI

决定：

> 最终界面如何视觉表达。

### Design System

管理：

- Design Tokens
- Typography
- Spacing
- Color
- Components
- States
- Patterns
- Accessibility rules

**典型产物**

- User Journey
- Task Flow
- User Flow
- Navigation Model
- Wireframe
- Prototype
- Interaction Spec
- UI Spec
- Design Tokens
- Component Library Spec
- Design System

**负责人**

Product Designer / UX / UI / Interaction Designer。

**输出**

> **用户看到和操作的软件模型。**

---

# 04. Architecture & Technical Design

这里进入：

> **System Design**

与 Product Design 完全不同。

解决的是：

> 软件内部如何工作？

包括：

```text
System Design
├── System Architecture
├── Domain Model
├── Module Boundaries
├── Client Architecture
├── Backend Architecture
├── API Design
├── Data Architecture
├── Storage
├── State Management
├── Integration Architecture
├── AI Architecture
├── Security Architecture
├── Privacy Architecture
├── Reliability Design
├── Observability Design
└── Deployment Architecture
```

还包括重要的 **Technical Design**：

- API Contract
- Data Schema
- State Machine
- Error Model
- Cache Strategy
- Sync Strategy
- Concurrency
- Failure Handling
- Migration Strategy
- Compatibility
- Performance Budget
- Logging Model

**典型产物**

- Architecture Overview
- System Context
- Component Diagram
- ADR
- API Contract
- Data Model
- Sequence Diagram
- Threat Model
- Technical Spec
- Error Contract
- NFR Specification

**负责人**

Software Architect / Tech Lead / Senior Engineer。

**输出**

> **工程实现的系统蓝图和技术合同。**

---

# 05. Engineering Implementation

这一层才是真正的 Coding。

```text
Implementation
├── Client
│   ├── iOS
│   ├── Android
│   ├── Web
│   └── Desktop
│
├── Backend
│   ├── API
│   ├── Services
│   ├── Jobs
│   └── Integrations
│
├── Data
│   ├── Storage
│   ├── Pipeline
│   └── Data Processing
│
├── AI
│   ├── Model Integration
│   ├── Retrieval
│   ├── Agent
│   ├── Evaluation
│   └── Guardrails
│
└── Infrastructure Code
```

因此：

**Frontend / Backend / AI / Data 不适合作为 App Development 的一级分类。**

它们属于：

> **Engineering Implementation 内部的技术实现轨道。**

AI 同样如此。

如果产品没有 AI，就不存在 AI 模块；因此不能把 AI 与 Product Strategy、Architecture 平级。

对于 AI 产品，还应扩展模型评估、安全、数据治理等实践。NIST 也专门将生成式 AI 开发实践作为 SSDF 的扩展，而不是把 AI 从软件生命周期中完全分离。

---

# 06. Quality Engineering & Risk Control

Testing 只是其中一部分。

```text
Quality Engineering
├── Unit Testing
├── Integration Testing
├── Contract Testing
├── UI Testing
├── End-to-End Testing
├── Regression Testing
├── Compatibility Testing
├── Performance Testing
├── Security Testing
├── Accessibility Testing
├── Reliability Testing
├── Recovery Testing
├── Data Quality Testing
├── AI Evaluation
└── Release Acceptance
```

还包括：

- Test Strategy
- Test Pyramid
- Test Coverage Policy
- Quality Gates
- Bug Severity
- Risk-based Testing
- Test Environment
- Test Data
- Automation

Security 应进一步覆盖：

- Authentication / Authorization
- Secure Storage
- Cryptography
- Network
- Platform Interaction
- Privacy
- Dependency Vulnerability

对于移动 App，OWASP MASVS 就按照 Storage、Crypto、Auth、Network、Platform 等攻击面组织验证要求。

Accessibility 同样需要进入设计和测试，而不是 UI 做完后“检查一下”。例如 WCAG 2.2 明确提供可测试的 Success Criteria。

---

# 07. Engineering Platform & Delivery

这是个人开发者最容易忽视的一整层。

目标不是实现业务功能，而是：

> **让开发行为本身可靠、可重复、可审计。**

包括：

```text
Engineering Platform
├── Repository Strategy
├── Branch Strategy
├── Coding Standards
├── Code Review
├── CI
├── Build System
├── Automated Checks
├── Dependency Management
├── Package Management
├── Secret Management
├── Environment Management
├── Artifact Management
├── Signing
├── Infrastructure Automation
└── Developer Tooling
```

典型 CI Pipeline：

```text
Commit
↓
Lint
↓
Static Analysis
↓
Build
↓
Unit Test
↓
Integration Test
↓
Security Scan
↓
Package
↓
Artifact
```

所以：

**CI/CD 其实横跨两个模块。**

CI 主要属于：

> Engineering Platform

CD / Deployment 更多属于：

> Release Engineering。

---

# 08. Release & Production Operations

“代码完成”不等于“产品完成”。

包括：

### Release Engineering

- Versioning
- Release Candidate
- App Signing
- Store Submission
- Release Notes
- Database Migration
- Feature Flag
- Staged Rollout
- Canary
- Rollback
- Compatibility
- Deprecation

### Production Operations

- Production Configuration
- Runtime Monitoring
- Crash Reporting
- Logging
- Metrics
- Tracing
- Alerting
- Incident Response
- SLO / SLA
- Backup
- Disaster Recovery
- Capacity
- Availability

其中：

```text
Logging ≠ Observability
Crash Reporting ≠ Observability
Monitoring ≠ Observability
```

它们都是 Observability 的组成部分。

现代可观测性通常组合 traces、metrics、logs 等遥测信号；生产可靠性则进一步涉及告警、故障响应与长期服务健康。

---

# 09. Measurement & Product Learning

上线不是终点。

上线意味着：

> **Discovery 的下一轮开始。**

包括：

```text
Measurement
├── Product Analytics
├── Event Tracking
├── Funnel
├── Retention
├── Engagement
├── Performance Metrics
├── Business Metrics
├── Experimentation
├── A/B Testing
├── User Feedback
├── Support Feedback
└── Behavioral Analysis
```

关键产物：

- Event Taxonomy
- Analytics Schema
- KPI Dashboard
- Funnel Report
- Cohort Analysis
- Experiment Report
- Product Insights

形成：

```text
Hypothesis
↓
Build
↓
Release
↓
Measure
↓
Learn
↓
New Hypothesis
```

---

# 10. Governance, Documentation & Evolution

成熟软件和一次性 Demo 最大的区别之一就在这里。

主要管理：

- Documentation
- Architecture Governance
- Technical Debt
- Dependency Lifecycle
- API Lifecycle
- Schema Evolution
- Deprecation
- Compatibility
- Security Updates
- Ownership
- Engineering Standards
- Knowledge Management
- Decision History

特别重要的是：

> **Documentation 不应该只有 README。**

长期产品至少应该形成以下正式资产：

```text
docs/
├── product/
│   ├── product-vision
│   ├── positioning
│   ├── product-principles
│   └── product-spec
│
├── design/
│   ├── information-architecture
│   ├── interaction
│   ├── design-system
│   └── accessibility
│
├── architecture/
│   ├── architecture-overview
│   ├── domain-model
│   ├── API-contracts
│   ├── data-model
│   └── ADR/
│
├── engineering/
│   ├── coding-standards
│   ├── testing-strategy
│   ├── dependency-policy
│   └── development-workflow
│
├── security/
│   ├── security-model
│   ├── threat-model
│   └── privacy-model
│
├── operations/
│   ├── observability
│   ├── runbooks
│   ├── incident-response
│   ├── backup-recovery
│   └── release-process
│
└── analytics/
    ├── metrics-definition
    └── event-schema
```

---

# 3. 各概念到底处于什么层级

这是最容易混乱的地方。

```text
Product
├── Product Strategy
├── Product Discovery
└── Product Definition

Experience Design
├── UX
├── Interaction Design
├── UI
└── Design System

System Design
├── Architecture
├── Data Architecture
├── Security Architecture
├── AI Architecture
└── Technical Design

Engineering
├── Frontend
├── Backend
├── Data Engineering
├── AI Engineering
└── Infrastructure

Quality
├── Testing
├── Security Verification
├── Performance
└── Accessibility

Delivery
├── CI/CD
├── Build
├── Release
└── Deployment

Production
├── Logging
├── Crash Reporting
├── Observability
├── Reliability
└── Incident Management

Product Learning
├── Analytics
├── Experimentation
└── User Feedback
```

---

# 4. 编码之前必须完成什么？

不是所有设计都必须 100% 完成才能开始 Coding。

但以下内容原则上必须明确。

## Hard Prerequisites

### Product

- Problem Definition
- Target User
- Product Goal
- MVP / Scope
- Core Requirements
- Acceptance Criteria

### UX

至少明确：

- Information Architecture
- Primary User Flow
- Main Interaction Model

### Architecture

至少明确：

- System Boundary
- Module Boundary
- Domain Model
- Data Ownership
- Key Interfaces
- API Contract
- Critical Technology Decisions

### Quality

至少明确：

- NFR
- Security / Privacy Constraints
- Performance Requirements
- Quality Gates

否则非常容易出现：

> 一边编码，一边重新定义产品和系统。

---

# 5. 哪些可以并行？

专业开发不是 Waterfall。

典型并行关系：

```text
                    ┌─ UX / Interaction
Research ─ Product ─┼─ Architecture
                    ├─ Security Analysis
                    └─ Technical Spike
```

产品主流程确定之后：

```text
UX
├── UI
├── Design System
└── Accessibility

Architecture
├── Client Design
├── Backend Design
├── Data Design
└── AI Design
```

接口稳定后：

```text
Implementation
├── Client
├── Backend
├── Data
├── AI
├── Test Automation
└── CI
```

Testing 也不是最后才开始：

```text
Requirement
↓
Acceptance Criteria
↓
Test Design
↓
Implementation
↓
Automated Verification
```

---

# 6. 明确的上下游依赖

真正的主干依赖关系是：

```text
Idea
↓
Problem
↓
Product Definition
↓
Experience Model
↓
System Model
↓
Technical Contracts
↓
Implementation
↓
Verification
↓
Release
↓
Production
↓
Measurement
↓
Learning
↓
Product Definition V2
```

但真实项目会形成多个重叠循环，而不是单一瀑布。

---

# 7. 完整端到端开发流程

我建议最终采用：

```text
Idea
↓
Opportunity Discovery
↓
User / Market Research
↓
Problem Definition
↓
Product Strategy
↓
Product Definition
↓
Scope / Requirements
↓
UX / Information Architecture
↓
Interaction Design
↓
UI / Design System
↓
Architecture
↓
Technical Design
↓
Engineering Planning
↓
Implementation
↓
Continuous Verification
↓
Release Readiness
↓
Release
↓
Production
↓
Observability
↓
Analytics
↓
User Feedback
↓
Product Learning
↓
Iteration
↓
Continuous Improvement
```

实际上可以压缩成六个循环阶段：

```text
DISCOVER
↓
DEFINE
↓
DESIGN
↓
BUILD
↓
OPERATE
↓
LEARN
↺
```

---

# 8. 必须先完成 / 可以并行 / 持续贯穿

| 类型 | 内容 |
|---|---|
| **前置主链** | Strategy → Product Definition → Core UX → Architecture → Implementation → Release |
| **可并行** | UX / Architecture / Technical Spike / UI / Backend / Client / Test Development |
| **持续贯穿** | Security |
| **持续贯穿** | Privacy |
| **持续贯穿** | Performance |
| **持续贯穿** | Accessibility |
| **持续贯穿** | Testing |
| **持续贯穿** | Documentation |
| **持续贯穿** | Observability |
| **持续贯穿** | Analytics |
| **持续贯穿** | Technical Debt Management |

这里尤其不要建立：

> 开发完 → 测试 → 安全 → 性能 → 可访问性

这样的流程。

它会把质量问题拖到成本最高的位置。

---

# 9. 最容易出现的职责混乱

建议彻底重新定义三个词。

### Product Design

不要把它理解成“画 App”。

准确含义：

> **产品应该如何为用户创造价值。**

---

### Experience Design

解决：

> **用户如何感知和操作产品。**

包括 UX / Interaction / UI。

---

### System Design

解决：

> **软件内部如何实现产品行为。**

包括 Architecture / Technical Design / API / Data / Security 等。

于是形成非常清晰的三层：

```text
Product Definition
WHAT & WHY

↓

Experience Design
HOW USER USES IT

↓

System Design
HOW SOFTWARE WORKS
```

这是整个框架最重要的边界之一。

---

# 10. 最终总览树

```text
App Development
│
├── 01 Product Strategy & Discovery
│   ├── Idea
│   ├── Research
│   ├── Problem Definition
│   ├── Product Vision
│   ├── Positioning
│   └── Success Metrics
│
├── 02 Product Definition & Planning
│   ├── Scope
│   ├── Requirements
│   ├── Capabilities
│   ├── Business Rules
│   ├── Acceptance Criteria
│   └── Roadmap
│
├── 03 Experience & Interface Design
│   ├── UX
│   ├── Information Architecture
│   ├── User Flow
│   ├── Interaction Design
│   ├── UI
│   └── Design System
│
├── 04 Architecture & Technical Design
│   ├── System Architecture
│   ├── Domain Model
│   ├── Client Architecture
│   ├── Backend Architecture
│   ├── API
│   ├── Data
│   ├── AI
│   ├── Security
│   └── Technical Design
│
├── 05 Engineering Implementation
│   ├── Client
│   ├── Backend
│   ├── Data
│   ├── AI
│   └── Infrastructure
│
├── 06 Quality Engineering & Risk Control
│   ├── Testing
│   ├── Security Verification
│   ├── Performance
│   ├── Accessibility
│   ├── Reliability
│   └── Quality Gates
│
├── 07 Engineering Platform & Delivery
│   ├── Repository
│   ├── Code Review
│   ├── CI
│   ├── Build
│   ├── Dependency Management
│   └── Developer Tooling
│
├── 08 Release & Production Operations
│   ├── CD
│   ├── Release
│   ├── Deployment
│   ├── Logging
│   ├── Crash Reporting
│   ├── Observability
│   ├── Incident Response
│   └── Reliability
│
├── 09 Measurement & Product Learning
│   ├── Analytics
│   ├── Metrics
│   ├── Experiments
│   ├── User Feedback
│   └── Product Learning
│
└── 10 Governance, Documentation & Evolution
    ├── Documentation
    ├── ADR
    ├── Standards
    ├── Technical Debt
    ├── Dependency Lifecycle
    ├── API / Schema Evolution
    ├── Deprecation
    └── Knowledge Management
```

## 最后可以把整个体系记成一句话

> **Strategy 决定 Why，Product 决定 What，UX 决定用户如何使用，Architecture 决定系统如何工作，Engineering 将其实现，Quality 证明其可靠，Delivery 将其交付，Operations 保证其运行，Analytics 验证其价值，Governance 保证其能够长期演进。**

这套 **10 模块结构**比“需求→设计→开发→测试→上线”更适合作为一个真实、长期维护 App 的顶层开发框架，也适合作为后续拆解项目目录、文档体系、AI Agent 职责和研发工作流的基础。