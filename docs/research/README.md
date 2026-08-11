# Askora Research 文档索引

> 状态：Research Evidence Index  
> 权威性：Supporting Evidence，不是 Canonical Product / Design / Spec

`docs/research/` 保存跨产品战略、用户问题、替代方案、市场、可行性与后续 Product Learning 的研究资产。

Learning Core / 教学系统形成过程中的 evidence 与 synthesis 统一位于 `docs/research/learning-core/`；研究资产不再嵌在 Canonical Design 目录中。

## 1. 当前结构

```text
docs/research/
├── README.md
├── product-discovery/
│   ├── USER-PROBLEM-JTBD-RESEARCH.md
│   ├── ALTERNATIVES-OPPORTUNITY-RESEARCH.md
│   ├── DISCOVERY-EVIDENCE-SYNTHESIS.md
│   └── PRIMARY-DISCOVERY-PROTOCOL.md
└── learning-core/
    ├── evidence/
    └── synthesis/
```

### Product Strategy Research

- [`USER-PROBLEM-JTBD-RESEARCH.md`](product-discovery/USER-PROBLEM-JTBD-RESEARCH.md)：建立 Problem / Primary User / JTBD 假设与 Primary Discovery protocol。
- [`ALTERNATIVES-OPPORTUNITY-RESEARCH.md`](product-discovery/ALTERNATIVES-OPPORTUNITY-RESEARCH.md)：记录替代产品能力与 Askora 的机会假设。
- [`DISCOVERY-EVIDENCE-SYNTHESIS.md`](product-discovery/DISCOVERY-EVIDENCE-SYNTHESIS.md)：XIK-181 外部经验研究、替代产品、Assessment 边界与 assumption status synthesis；明确哪些结论仍需 Primary Discovery。
- [`PRIMARY-DISCOVERY-PROTOCOL.md`](product-discovery/PRIMARY-DISCOVERY-PROTOCOL.md)：XIK-182 真人 JTBD / behavior / friction / first-value / assessment calibration 执行协议；protocol 本身不算 Primary Evidence。

### Learning Core Research

- [`learning-core/evidence/`](learning-core/evidence/)：教育科学、ITS、检索、教学策略、复习调度与 LLM/Agent 治理的来源证据；
- [`learning-core/synthesis/`](learning-core/synthesis/)：八类系统研究、DR-03 系列、研究综合、候选范围与历史研究议程；
- [`learning-core/README.md`](learning-core/README.md)：Research → Synthesis → Canonical Design / ADR / Spec 的形成链与历史边界。

这些文件可以包含历史架构候选与研究结论；其 current canonical 吸收结果必须从 `docs/design/learning/`、`docs/architecture/decisions/` 与 `docs/specs/` 读取。

## 2. Research 职责

Research 回答：

- 我们为什么相信某个 Problem / User / JTBD；
- 用户现在怎样解决这个问题；
- 现有替代方案已经覆盖了什么；
- 哪些 unmet need 仍然存在；
- 哪些结论是 evidence，哪些只是 hypothesis；
- 哪些假设应该被验证或推翻。

Research 不直接冻结：

- Product Strategy；
- Product Positioning；
- Domain ownership；
- UX / Interaction；
- API / schema / implementation contract。

形成链：

```text
Evidence / Research
→ Synthesis / Decision
→ PRODUCT-STRATEGY or Canonical Design
→ downstream governance
```

## 3. Evidence Rule

每份研究文档应明确区分：

- **Observed / Source-backed**；
- **Repository-supported inference**；
- **Product assumption**；
- **Unresolved research question**。

禁止：

```text
implemented
→ therefore validated user need
```

也禁止：

```text
secondary research supports a problem
→ therefore target users will adopt the product
```

还禁止：

```text
competitor does not advertise feature X
→ therefore competitor definitely cannot do X
```

竞争/替代研究只根据可验证公开事实描述能力，再单独写 Askora 的战略推论。

### Primary vs Secondary Discovery

- 外部论文、官方产品文档和公开行为信号属于 **Secondary Evidence**；
- 真人 retrospective interview、真实 workflow reconstruction、prototype behavior test、longitudinal use 属于 **Primary Discovery Evidence**；
- Secondary Evidence 可以降低假设不确定性，但不能单独把 Primary User / JTBD / willingness assumption 升级为 `Validated`；
- Research Protocol 定义如何收集证据，但 **protocol completion != Primary Evidence**。

## 4. Lifecycle

Research 可以比 Canonical docs 更频繁变化。

当研究改变上位结论时：

```text
New evidence
→ update research
→ explicit Product Strategy / Positioning / Design Delta
→ user accepts
→ freeze canonical change
```

仅更新 Research 不自动改变产品或实现合同。
