# Askora Implementation Specifications

> 状态：规范层导航（完整清单与权威链见 [`../README.md`](../README.md)）
> 当前有效规范 = 以下文件；旧碎片规范已归档至 `../archive/specs/`

## 规范文件

| 规范 | 内容 |
|---|---|
| [architecture.md](architecture.md) | 系统架构、State Ownership、Dependency Rules |
| [domain.md](domain.md) | 领域模型、Decision/Event Contract、生命周期状态机 |
| [systems/01-content-knowledge.md](systems/01-content-knowledge.md) | SYS01 内容与知识（含 Material 管理、粒度、发布流水线） |
| [systems/02-retrieval.md](systems/02-retrieval.md) | SYS02 检索 |
| [systems/03-learner-model.md](systems/03-learner-model.md) | SYS03 学习者建模 |
| [systems/04-assessment.md](systems/04-assessment.md) | SYS04 评估 |
| [systems/05-teaching-policy.md](systems/05-teaching-policy.md) | SYS05 教学策略 |
| [systems/06-learning-planner.md](systems/06-learning-planner.md) | SYS06 学习规划（含 Goal/Activity/知识映射/诊断引导） |
| [systems/07-review-scheduler.md](systems/07-review-scheduler.md) | SYS07 复习调度 |
| [systems/08-ai-orchestration.md](systems/08-ai-orchestration.md) | SYS08 AI 编排（含 Model Configuration） |
| [interfaces/api.md](interfaces/api.md) | API / 错误 / Schema 版本化 |
| [interfaces/content.md](interfaces/content.md) | 内容摄取 / 渲染边界 |
| [interfaces/persistence-and-data-control.md](interfaces/persistence-and-data-control.md) | 持久化 / Material 生命周期 / 数据控制与擦除 |
| [interfaces/message-and-note.md](interfaces/message-and-note.md) | Learning Conversation Message / UserNote |
| [interfaces/recovery-and-onboarding.md](interfaces/recovery-and-onboarding.md) | 恢复控制 / 首次引导 |
| [platform.md](platform.md) | 身份 / Workspace / Course 选择 / LocalSecretStore |
| [quality.md](quality.md) | 测试 / CI / 可观测性 / DoD / 安全 |
| [ui.md](ui.md) | UI / UX 实现合同（含 frontend read-model） |

## 权威链

```text
PRODUCT-STRATEGY → PRODUCT-POSITIONING → PRODUCT-DEFINITION
→ Canonical Design → DECISIONS.md / archive/adr/
→ 本目录 specs/ → Code / Tests
```

## 维护规则

1. 规范只使用 MUST / MUST NOT / SHOULD 等规范语言，声明 lifecycle；
2. 新增/合并规范必须先更新 `../README.md` 的当前文档清单；
3. 旧规范文件一律 `git mv` 归档至 `../archive/specs/`，不物理删除；
4. requirement ID（`LID-* / WSP-* / LSS-* / MATLIFE-* / API-* / UI-*` 等）在合并时原样保留，不重编号。
