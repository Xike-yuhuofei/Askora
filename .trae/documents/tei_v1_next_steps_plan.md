# TEI v1 架构优化落地计划

## 1. 背景与目标

在上一轮迭代中，我们完成了 TEI (Teaching Engine Interface) v1 的核心架构搭建：
*   **统一接口**：实现了 `TeachingEngine` ABC 与 `LearningFlowOrchestrator`。
*   **核心引擎**：落地了 `Socratic` (引导) 和 `Explain` (讲解) 引擎。
*   **编排机制**：实现了 `SWITCH_AND_RETURN` (切换并返回) 逻辑与 `SharedContext` (跨引擎上下文) 传递。

为了让该架构具备生产级可用性，接下来的优化方向将重点聚焦于：
1.  **闭环验证**：引入 `QuizEngine` (测验引擎) 形成教学闭环。
2.  **无缝迁移**：将现有 `DialogService` 平滑接入 Orchestrator 主链路。
3.  **状态持久化**：将会话状态从内存迁移至 Redis，确保服务重启不丢失。

---

## 2. 优化方向详述

### 方向一：实现 QuizEngine (测验引擎)

**目标**：补齐教学闭环的最后一块拼图。当前 `Socratic` 引擎在学生表现良好时建议切换到 `Quiz` 进行微验证 (Micro-validation)，但 Quiz 引擎尚未实现。

**实施步骤**：
1.  **创建文件**：`apps/backend/app/engines/quiz_engine.py`
2.  **实现核心逻辑**：
    *   **`can_handle`**：在 `VALIDATE` 或 `DRILL` 阶段评分最高 (1.0)。
    *   **`build_initial_state`**：从 `SharedContext` 中读取知识点，初始化题库。
    *   **`step`**：
        *   第 1 轮：调用 LLM 根据当前知识点生成 3 道选择题/简答题。
        *   第 2+ 轮：判定用户答案，计算正确率，更新 `SharedContext.mastery_vector`。
        *   结束时：若正确率 > 80%，`TransitionSuggestion` 为 `SWITCH_AND_RETURN` 回 `Socratic` 或 `Explain` 进行深入学习。
3.  **讲解模式**：默认使用 `mode="drill"` (变式练习)，根据 `learner_persona` 调整题目难度。

**涉及文件**：
*   **新建**：`apps/backend/app/engines/quiz_engine.py`
*   **修改**：`apps/backend/app/engines/__init__.py` (导入模块触发注册)

---

### 方向二：DialogService 接入 Orchestrator 主链路

**目标**：将现有的核心对话服务从“直接调用 `SocraticEngine`”重构为“调用 `LearningFlowOrchestrator`”，实现零停机迁移。

**实施步骤**：
1.  **修改 `DialogService.send_message`**：
    *   增加 Session 检查：如果当前 User 会话尚未绑定 Orchestrator Session，则自动创建。
    *   替换引擎调用：将 `socratic_engine.generate_response()` 替换为 `orchestrator.run_turn()`。
2.  **上下文映射**：
    *   将现有 `DialogSession` 的 `subject`、`knowledge_point_id` 映射到 `SharedContext`。
    *   将历史消息映射到 `LearnerTurn`。
3.  **保持向后兼容**：返回的 `DialogResponse` 结构不变，内部填充 Orchestrator 的回复。

**涉及文件**：
*   **修改**：`apps/backend/app/services/dialog/dialog_service.py`
*   **修改**：`apps/backend/app/services/dialog/socratic_engine.py` (保持不动)

---

### 方向三：Orchestrator 状态持久化 (Redis)

**目标**：将 Orchestrator 的会话状态 (`SharedContext`, `EngineStates`) 存储到 Redis，避免服务重启导致的状态丢失。

**实施步骤**：
1.  **封装 Repository 层**：
    *   创建 `apps/backend/app/engines/repository.py`。
    *   实现 `OrchestratorRepository` 类，封装 `load_session(session_id)` 和 `save_session(session_id, data)`。
2.  **修改 Orchestrator**：
    *   在 `LearningFlowOrchestrator` 中移除内存字典 `_sessions`。
    *   改为通过 `OrchestratorRepository` 读写 Redis。
3.  **数据结构**：
    *   Redis Key：`askora:engine:session:{session_id}`
    *   Value：JSON (利用 `orjson` 序列化性能更佳)。

**涉及文件**：
*   **新建**：`apps/backend/app/engines/repository.py`
*   **修改**：`apps/backend/app/engines/orchestrator.py`
*   **依赖**：复用项目现有的 `app.core.redis_client`。

---

## 3. 执行计划与依赖关系

建议的执行顺序如下（从易到难，从闭环到底层）：

1.  **Step 1: 实现 QuizEngine** (闭环验证)
    *   *理由*：纯代码新增，不影响现有逻辑，可独立验证。完成后，可通过 `/orchestrator` 端点测试 `Socratic -> Quiz -> Socratic` 完整链路。
2.  **Step 2: DialogService 接入 Orchestrator** (主链路迁移)
    *   *理由*：在 QuizEngine 就绪后，Orchestrator 的能力更完整，接入主业务价值更大。
3.  **Step 3: Orchestrator 持久化** (基础设施)
    *   *理由*：状态持久化是优化项，可以在功能稳定后进行重构。

## 4. 风险与注意事项

*   **QuizEngine**：需注意题目生成的 Token 消耗，建议使用精简的 Prompt。
*   **DialogService 迁移**：需确保原有的 `StreamResponse` (流式输出) 逻辑在 Orchestrator 下仍能工作。可能需要调整 Orchestrator 接口支持异步生成器。
*   **Redis 持久化**：需处理 `SharedContext` 中的 `enum` 和 `set` 类型的序列化/反序列化。
