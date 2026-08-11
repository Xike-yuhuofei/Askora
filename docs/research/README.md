# Askora Research 文档索引

> 状态：Research Evidence Index  
> 权威性：Supporting Evidence，不是 Canonical Product / Design / Spec

`docs/research/` 保存跨产品战略、用户问题、替代方案、市场、可行性与后续 Product Learning 的研究资产。

现有 `docs/design/research/` 继续保存 Learning Core / 教学系统形成过程中已经存在的 evidence 与 synthesis；本轮不机械搬迁历史研究，以避免无收益的大规模路径重写。

## 1. 当前结构

```text
docs/research/
├── README.md
└── product-strategy/
    ├── USER-PROBLEM-JTBD-RESEARCH.md
    └── ALTERNATIVES-OPPORTUNITY-RESEARCH.md
```

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
competitor does not advertise feature X
→ therefore competitor definitely cannot do X
```

竞争/替代研究只根据可验证公开事实描述能力，再单独写 Askora 的战略推论。

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
