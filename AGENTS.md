# Askora Codex Execution Contract

> 适用对象：Codex / TraeCode / 其他代码执行代理  
> 状态：强制执行入口  
> 原则：执行代理负责已冻结设计与工程任务的实现；不得在实现过程中自行重新定义产品战略、产品边界或重大共享语义。

## 1. 开始任务前的读取顺序

执行任何非纯机械修改前，必须按以下顺序读取与任务相关的事实源：

1. `AGENTS.md`
2. `docs/product/PRODUCT-STRATEGY.md`
3. `docs/product/PRODUCT-POSITIONING.md`
4. `docs/specs/README.md`
5. 与任务相关的 current Canonical Design / Accepted ADR
6. `docs/specs/architecture/`、`domain/`、`systems/`、`interfaces/`、`quality/`、`ui/` 中相关合同
7. 对应 Linear Issue / Project 状态
8. 当前 `docs/exec-plans/active/` 中明确指定的 EXEC（如有）
9. 仅在需要理解证据或形成上位 Delta 时读取 `docs/research/` / `docs/design/research/`

职责解释：

- `PRODUCT-STRATEGY.md`：最高产品战略意图，回答 Why / Who / Problem / Value / Success；
- `PRODUCT-POSITIONING.md`：最高可执行产品边界，回答 Category / Product Shape / Constraints / Non-goals；
- Research：支持证据，不是实现接口合同；
- Linear：当前工作状态，不是长期设计事实。

## 2. 权威与冲突处理

```text
PRODUCT-STRATEGY
→ PRODUCT-POSITIONING
→ Canonical Design / Design Delta
→ Accepted ADR
→ Canonical Specs
→ EXEC / Linear Issue
→ Code / Migration / Tests
→ Agent inference
```

注意：`PRODUCT-STRATEGY.md` 不直接规定 API、schema 或实现 mechanics，但任何会改变 Target User、核心 Problem、Value Proposition、Strategic Principles 或 Success Definition 的工作必须先回到 Strategy 层。

发生冲突时：

- Strategy 与 Positioning 冲突：停止下游扩张，报告 `STRATEGY GAP` / Product Delta；
- Positioning 与 Design / ADR / Spec 冲突：下位必须收敛；
- Design / ADR 与 Spec 冲突：先修正治理链，再实现；
- Spec 与代码冲突：默认 implementation drift，不得修改 Spec 迁就现有代码；
- 历史 Research / Release / Gap Analysis 与 current truth 冲突：历史文件保留，但不覆盖 current Canonical docs / current `main`。

## 3. 执行代理职责

执行代理必须：

- 首先确认任务服务 `PRODUCT-STRATEGY.md` 中的 Problem / User / Outcome；
- 确认不突破 `PRODUCT-POSITIONING.md`；
- 严格按照 current Design / ADR / Spec / EXEC 实现；
- 只修改任务允许的 Scope；
- 为关键行为补充可追踪测试；
- 对公共 Schema、迁移、状态所有权和跨模块依赖保持最小必要变更；
- 发现旧实现越过系统边界时，通过明确 adapter / migration / retirement path 收敛；
- 报告修改文件、实际测试、候选 SHA、未完成项与任何 GAP；
- 区分 Engineering / Product / Learning Evidence，不能用工程 PASS 声称真人学习有效。

执行代理不得：

- 因“实现更方便”修改 Product Strategy / Positioning；
- 把未验证用户假设写成已验证事实；
- 擅自扩大目标用户或产品类别；
- 用历史代码存在性恢复已 supersede 的 Account / Electron / OCR-as-core / service-infrastructure 产品语义；
- 先改代码、再用 ADR / Spec 追认既成事实。

## 4. 用户授权下的设计 / 架构自治

当用户明确授权某个已限定产品/工程目标时，执行代理 MAY 为完成该目标提出并接受必要的 Canonical Design / ADR / Spec / EXEC 变化，再进行代码实现。

该授权仅限于目标范围，不是永久架构自由裁量权。

### 不包含的权限

执行代理不能自动修改：

- Primary User；
- 核心 Problem / JTBD；
- Product Vision / Value Proposition；
- Product Success Definition；
- Product Category；
- v1 Strategic Constraints / Non-goals。

若目标需要改变这些内容，必须先报告 `STRATEGY GAP` 或 `POSITIONING GAP`，由 ChatGPT 完成上位研究/设计并由用户明确接受。

### 必须先冻结再实现的共享语义

包括但不限于：

- bounded context / SYS01～SYS08 边界；
- canonical state single-writer；
- 公共领域对象；
- API / Command / Event / Decision Schema；
- 数据库领域模型与迁移语义；
- Teaching Policy / assessment / review semantics；
- 错误、重试、降级、幂等；
- 安全、隐私、Prompt Injection；
- 生产依赖和技术栈；
- 跨模块依赖方向。

自主设计仍必须：

- 不违反 Product Strategy / Positioning；
- 不建立第二套长期 truth 或永久双写；
- 公共 API / Schema / DB 变化版本化、可迁移并有 rollback / forward-fix；
- 不削弱 security / privacy / grader-only / answer-exposure；
- 至少比较一个真实替代方案；
- 具有自动化验证和当前运行证据。

不可恢复数据删除、超出目标的外部付费/采购、改变凭据用途、向新第三方发送个人敏感数据或法律/合规责任变化仍必须请求用户确认。

## 5. 局部实现自治

在不改变公共行为、领域语义、依赖边界和 Product docs 的前提下，可以自行决定：

- 局部变量、私有函数、fixture 命名；
- 单模块内部私有拆分；
- 等价小型重构；
- 不改变错误类型/错误码的文案；
- Spec 明确标记为 `MAY` 的实现选项。

## 6. GAP Protocol

### `STRATEGY GAP`

出现以下情况必须报告：

- 任务需要改变 Primary User / Non-target User；
- 任务重新定义核心 Problem / JTBD；
- 任务改变 Value Proposition / Differentiation thesis；
- 任务改变 Product Principles 或 Success Definition；
- 新证据明显推翻当前 Strategy assumption。

处理：

```text
New evidence / conflict
→ STRATEGY GAP
→ Product Strategy Delta
→ user acceptance
→ re-freeze Strategy
→ Positioning check / delta
→ downstream work
```

执行代理不得自行关闭 `STRATEGY GAP`。

### `POSITIONING GAP`

包括：

- 任务突破 Product Category、v1 Scope、Non-goals 或 Hard Boundaries；
- 需要改变 Local Web、single-user、Local-first、BYOK、no-central-cloud 等产品级约束；
- 需要新增当前 Positioning 明确排除的核心产品能力；
- 下位文档与 Product Positioning 冲突。

处理：提出 Product Positioning Delta、理由、影响与候选方案；用户明确接受前不得用代码制造既成事实。

### `DESIGN GAP`

包括：

- 产品/学习/交互语义尚未冻结；
- 多种方案会形成不同用户行为或领域语义；
- 现有 Design 与 Product docs 存在未处理冲突。

处理：停止让 Codex自行做产品/交互决定，回到上游 Canonical Design。

### `SPEC GAP`

包括：

- 高权威下位规范冲突；
- 状态所有权、公共 Schema、关键错误语义缺失；
- 新生产依赖或技术 mechanics 未选择；
- 多种实现会造成不同业务结果而 Spec 未冻结；
- 必须违反任一 `MUST NOT` 才能实现。

已获用户明确架构自治授权时，执行代理可以通过 ADR / Spec / EXEC 闭环处理 `SPEC GAP`；未授权则返回上游。

## 7. 八类 Learning Core 不可越权规则

```text
4.1 内容解析与知识建模       → Knowledge truth / relations
4.2 检索与知识供给           → EvidenceBundle / RetrievalTrace
4.3 学习者建模               → LearnerState / MasteryEstimate
4.4 评估与错误诊断           → Attempt / AssessmentResult / diagnosis
4.5 教学策略选择             → TeachingAction / assistance-exposure envelope
4.6 学习路径与任务调度       → LearningGoal / Plan / Activity
4.7 记忆保持与复习调度       → ReviewSchedule / next_due_at
4.8 LLM / Agent 编排与可信控制 → model / tool execution / rendering / audit execution
```

特别禁止：

- Assessment 直接写 mastery；
- LLM / Agent 直接写 LearnerState、Plan、TeachingAction、ReviewSchedule；
- Planner 计算第二份 memory schedule；
- Teaching Policy 偷偷改变高层 Goal；
- Retrieval 在 TeachingAction 允许范围之外扩大答案暴露；
- 检索失败后 LLM 伪造用户资料事实。

## 8. Legacy Code

当前代码结构只是迁移起点，不自动授予 canonical ownership。

例如：

- `apps/backend/app/engines/`
- `apps/backend/app/services/dialog/`
- `apps/backend/app/services/dkt/`
- `apps/backend/app/services/kt/`
- `apps/backend/app/services/documents/`
- `apps/backend/app/services/knowledge_graph/`
- `apps/backend/app/services/assessment/`

规则：

- 新能力向 current Product / Architecture / Specs 收敛；
- 可以存在 temporary adapter / compatibility layer，但必须有退休条件；
- 禁止长期双 truth / 双默认主链；
- 历史目录名不决定当前产品类别或系统 ownership。

## 9. 默认验证

后端任务在适用时至少运行：

```bash
cd apps/backend
pytest
ruff check app tests
```

修改类型标注、公共接口或核心领域代码时额外运行：

```bash
mypy app
```

前端任务在适用时至少运行：

```bash
cd apps/frontend
npm run build
```

文档任务至少运行：

```bash
python3 .github/workflows/check_docs.py
```

如果命令失败，必须区分：

- 本次变更新增失败；
- 与本次变更无关的 existing failure。

不得删除测试、弱化断言或扩大 ignore 来伪造 PASS。

## 10. Completion Definition

执行代理只有在以下条件满足时才能标记任务完成：

- 未违反 `PRODUCT-STRATEGY.md` 与 `PRODUCT-POSITIONING.md`；
- 所有 Acceptance Criteria 满足；
- 未违反 canonical state ownership / dependency rules；
- 必要 migration 可前向执行并有 rollback / compatibility strategy；
- 新增关键行为有自动化测试；
- error / retry / idempotency / observability 符合 Spec；
- 无未声明公共 API / Schema 变化；
- 所有 `STRATEGY GAP` / `POSITIONING GAP` / `DESIGN GAP` / `SPEC GAP` 已显式报告或在正确层关闭；
- 没有占位实现、`TODO` 伪完成或仅 Mock 的“真实能力可用”结论；
- Product / Learning claim 没有超出实际 evidence。
