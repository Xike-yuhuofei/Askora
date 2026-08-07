# 八类技术系统：ITS 与学习者建模证据

> 阶段：B｜统一研究资料库

## 1. 研究问题

1. ITS 的经典 Domain/Learner/Pedagogical/Tutoring Model 对 Askora 有何架构意义？
2. BKT、IRT、PFA、DKT/SAKT 等分别解决什么问题？
3. 单次评估结果与长期学习者状态应如何分离？
4. Adaptive Testing、Cognitive Diagnosis、Open Learner Models 何时值得采用？

## 2. ITS 的结构性启示

### 2.1 模型分离，而非“一个 LLM Tutor”

`学术共识` + `Askora 设计选择`

经典 ITS 通常区分：

- Domain Model：要学什么；
- Learner/Student Model：学习者当前状态；
- Pedagogical/Tutoring Model：如何选择教学动作；
- Interface/Interaction：如何执行教学交互。

对 Askora 的关键意义不是照搬命名，而是**知识事实、学习者估计、教学决策和语言生成必须分离**。

因此：

```text
内容模型 ≠ 学习者模型
评估结果 ≠ 掌握状态
教学策略 ≠ LLM 临场生成
Agent 执行 ≠ 教学决策所有权
```

### 2.2 ITS 效果总体积极，但“智能化”不是充分条件

Ma 等（2014）的元分析显示 ITS 相比多类常规教学条件总体具有积极学习效果。近年的 K-12 系统综述仍显示总体积极趋势，但效果受比较条件、学科、干预时长与系统设计影响。

- 证据等级：`研究证据`
- 教育上有效：总体积极
- 对 Askora 的含义：不能把“使用 AI/LLM”本身当成效果证据；必须测量学习结果。

## 3. Knowledge Tracing 与掌握估计

### 3.1 BKT（Bayesian Knowledge Tracing）

`研究证据`

Corbett & Anderson 的 Knowledge Tracing 用隐变量表示一个知识技能是否已掌握，并通过答题结果更新后验概率。经典参数包括：

```text
P(L0) 初始掌握概率
P(T)  学习转移概率
P(G)  猜对概率
P(S)  失误概率
```

**优势**：

- 可解释；
- 在线更新简单；
- 数据量较小时可工作；
- 适合知识点级状态追踪；
- 可回放、可审计。

**局限**：

- 经典模型假设较强；
- KC 标注质量决定上限；
- 默认知识点独立，难处理复杂跨知识依赖；
- 参数未校准时，概率不应被解释为客观真值。

**Askora 设计选择**：MVP 把 BKT 作为 `MasteryEstimate` 的可解释基线，但增加：

- 证据类型权重；
- 提示依赖；
- 延迟时间；
- 题目难度；
- 迁移证据；
- 置信度/有效样本数。

BKT 的状态只能由 4.3 更新，4.4 只提交观察证据。

### 3.2 IRT（Item Response Theory）

`学术共识`（教育测量领域）

IRT 用潜在能力与题目参数解释作答概率，常见参数：

- 难度；
- 区分度；
- 猜测参数（部分模型）。

**适合**：

- 题库已积累足够作答数据；
- 需要跨题比较能力；
- Adaptive Testing；
- 题目难度校准。

**不适合直接承担**：

- 细粒度学习过程状态更新；
- 开放式概念误区；
- 无稳定题库的冷启动阶段。

**Askora 设计选择**：

- MVP 不要求全面 IRT 校准；
- 当题库获得稳定样本后，用 IRT 校正 item difficulty/ability；
- IRT 输出是测量证据，不直接取代知识点级 MasteryEstimate。

### 3.3 PFA（Performance Factors Analysis）

`研究证据`

PFA 用练习次数、成功与失败历史建模表现，具有较强可解释性，是 BKT 之外的重要基线。

**Askora 含义**：作为离线 benchmark 很有价值，可检验“更复杂学习者模型是否真的优于简单历史特征”。

### 3.4 DKT / SAKT / Transformer KT

`研究证据`

DKT、SAKT、SAINT 等用深度序列模型学习长程交互依赖，在若干公开数据集上提高预测性能。

**技术可行**：高  
**工程成熟**：中  
**教育状态可解释性**：低于 BKT/PFA  
**Askora 当前适用**：低到中

关键限制：

1. 高 AUC 不等于掌握估计具有因果或教学解释；
2. 数据分布变化可能导致失效；
3. 需要大量、稳定、同质的交互数据；
4. 知识点标签、题目复用模式可能造成预测捷径；
5. 很难把某次状态改变解释给用户或审计系统。

`Askora 设计选择`：在存在足够真实交互历史前，不把 Deep KT 作为主状态模型。成熟阶段可以作为：

- 预测型 challenger；
- 状态先验/辅助特征；
- 与可解释模型做 ensemble；

而不是直接成为不可审计的唯一真相源。

## 4. Cognitive Diagnosis

`研究证据`

认知诊断模型试图估计学习者对多个细粒度属性/技能的掌握组合，通常依赖 Q-matrix（题目—技能映射）。

**价值**：比单一总分更适合找具体知识缺口。

**限制**：

- Q-matrix 错误会系统性污染诊断；
- 标注与参数校准成本高；
- 属性空间过细会导致稀疏；
- 对开放式知识与动态材料不易维护。

`Askora 设计选择`：当前优先使用 KnowledgeUnit/KC 级可解释状态 + 评估证据，不急于引入复杂 CDM。只有题库与属性映射稳定后再作为 challenger。

## 5. Adaptive Testing

`学术共识`（测量方法）

计算机自适应测试通过当前能力估计选择信息量更高的题目，可在较少题目下获得较精确测量，但需要：

- 校准题库；
- 题目暴露控制；
- 内容平衡；
- 终止规则；
- 公平性与安全约束。

van der Linden 等关于受约束 CAT 的研究说明，自适应题目选择不能只追求信息量，还必须满足内容/题型等约束。

**Askora 设计含义**：

MVP 的“诊断题选择”应先使用：

```text
前置覆盖
+ 不确定性
+ 题目难度分级
+ 未使用/暴露约束
+ 少量信息增益启发式
```

等题库完成校准后，再引入 IRT-CAT。

## 6. 误区诊断

`Askora 设计选择`，受 ITS/Cognitive Diagnosis 研究支持

误区必须分为三层：

```text
Misconception             规范误区定义
AssessmentResult          本次作答出现的误区证据
LearnerState              当前“用户存在该误区”的概率/假设
```

错误分类流程建议：

```text
确定性判分/规则
→ 已知误区模式匹配
→ LLM 结构化语义分类
→ 诊断追问/鉴别题
→ 学习者模型更新
```

LLM 首次判断只能生成 `hypothesis`，不能直接把用户永久标记为存在某误区。

## 7. Open Learner Models（OLM）

`研究证据` + `行业实践`

Open Learner Model 让学习者查看系统对自身知识状态的估计；可进一步支持可编辑、可协商 learner model。相关综述指出 OLM 可支持反思、元认知和自我调节，但界面与交互设计影响效果。

**Askora 设计含义**：

用户至少应能看到：

- 系统认为我掌握/未掌握什么；
- 判断依据；
- 置信度；
- 最近证据；
- 允许“这项判断不对”并触发复核。

用户纠错不应直接把概率改成 0/1，而应生成 `FeedbackSignal`，通过复测、证据权重调整或状态重算处理。

## 8. “真正掌握”的证据模型

`Askora 设计选择`

掌握不是某个算法输出的单一概率，而是多个证据维度：

```text
MasteryEstimate = {
  competence_probability,
  confidence,
  independent_success_count,
  hint_dependency,
  last_independent_success_at,
  delayed_recall_evidence,
  transfer_evidence,
  active_misconceptions,
  evidence_count,
  model_version
}
```

推荐状态门槛：

```text
稳定掌握 =
  掌握估计达到阈值
  AND 足够无提示独立成功
  AND 至少一次延迟提取证据
  AND 无高置信活跃误区
```

```text
迁移掌握 =
  稳定掌握
  AND 至少一次足够新颖的迁移任务独立成功
```

阈值本身是 `Askora 设计选择`，必须通过数据校准，不应伪装为学术定律。

## 9. 模型比较与推荐路线

| 模型 | 可解释性 | 数据要求 | 在线更新 | 当前推荐 |
|---|---:|---:|---:|---|
| 简单加权证据 | 高 | 低 | 高 | 必须作为 baseline |
| BKT | 高 | 低-中 | 高 | MVP 主模型 |
| PFA | 高 | 中 | 高 | 离线基线/challenger |
| IRT | 高 | 中-高 | 中 | 题库校准后引入 |
| Cognitive Diagnosis | 中高 | 高 | 中 | 暂缓 |
| DKT/SAKT/SAINT | 低-中 | 高 | 中 | 数据成熟后 challenger |

## 10. 参考资料（核心 10 项）

1. Corbett, A. T. & Anderson, J. R. *Knowledge tracing: Modeling the acquisition of procedural knowledge*. User Modeling and User-Adapted Interaction. https://doi.org/10.1007/BF01099821
2. Pavlik, P. I., Cen, H., & Koedinger, K. R. (2009). *Performance Factors Analysis*. https://doi.org/10.3233/978-1-60750-028-5-531
3. Piech, C. et al. (2015). *Deep Knowledge Tracing*. NeurIPS. https://proceedings.neurips.cc/paper_files/paper/2015/hash/bac9162b47c56fc8a4d2a519803d51b3-Abstract.html
4. Pandey, S. & Karypis, G. (2019). *A Self-Attentive Model for Knowledge Tracing*. https://arxiv.org/abs/1907.06837
5. Choi, Y. et al. (2020). *Towards an Appropriate Query, Key, and Value Computation for Knowledge Tracing*. https://arxiv.org/abs/2002.07033
6. ETS (2020). *An Introduction to Item Response Theory*. https://www.ets.org/research/policy_research_reports/publications/report/2020/kbxx.html
7. van der Linden, W. J. (2005). *Linear Models for Optimal Test Design*. https://doi.org/10.1111/j.1745-3984.2005.00015.x
8. Ma, W. et al. (2014). *Intelligent Tutoring Systems and Learning Outcomes: A Meta-Analysis*. Journal of Educational Psychology. https://doi.org/10.1037/a0037123
9. Conati, C., Porayska-Pomsta, K., & Mavrikis, M. (2018). *AI in Education needs interpretable machine learning*. https://arxiv.org/abs/1807.00154
10. *Intelligent tutoring systems in K-12 education: a systematic review* (2025). npj Science of Learning. https://doi.org/10.1038/s41539-025-00320-7

## 11. 证据缺口

- Askora 的开放式问答、苏格拉底对话和多材料学习比传统 KT 数据更复杂，经典模型需要扩展。
- “提示依赖”“迁移能力”尚缺统一标准测量模型，应保留独立证据维度而非硬塞入单一概率。
- Deep KT 在 Askora 自身真实数据上的增益未知；上线前必须与简单模型/BKT/PFA 进行时间切分和用户切分比较。