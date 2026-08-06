# Askora AI 学习系统：算法与教学内核设计

> 状态：阶段性设计基线  
> 更新时间：2026-08-07  
> 目标：定义 Askora 相对于普通 RAG 聊天工具与 DeepTutor 等通用 AI 学习平台的核心差异。

## 1. 核心定位

Askora 不应被定义为“能够读取资料并回答问题的 AI 聊天工具”，而应定位为：

> **以长期保持、独立完成和迁移能力为目标的个人自适应学习系统。**

系统不以对话量、即时正确率或课程完成率作为最高目标，而应优化：

- 延迟一段时间后仍能回忆；
- 不依赖提示完成任务；
- 将知识迁移到陌生情境；
- 用尽可能少的学习时间获得稳定能力。

完整学习闭环：

```text
学习目标
→ 内容与知识结构建模
→ 先备知识诊断
→ 学习者状态估计
→ 教学策略选择
→ 学习任务执行
→ 行为证据采集
→ 掌握状态更新
→ 间隔复习与迁移验证
→ 动态重新规划
```

---

## 2. 教学策略的决策变量

教学策略可抽象为：

```text
教学策略 = f(
  学习目标,
  先备知识,
  内容复杂度,
  错误类型,
  学习阶段
)
```

这些变量不是系统天然知道的事实，而是持续更新的估计值。每个维度都应保存：

```text
当前估计值 + 证据来源 + 置信度 + 更新时间
```

### 2.1 学习目标

由用户输入和系统结构化确认获得，包括：

- 学习主题；
- 目标能力层级；
- 应用场景；
- 截止时间；
- 时间预算；
- 成功标准。

LLM 可以负责从自然语言中抽取目标，但最终目标必须可编辑、可确认，不能完全由模型猜测。

### 2.2 先备知识

通过以下证据估计：

- 自适应诊断题；
- 概念解释；
- 代表性任务；
- 历史学习记录；
- 前置知识图谱。

第一阶段可使用 BKT 估计知识点掌握概率，后续用 IRT 校正题目难度和用户能力。

### 2.3 内容复杂度

应区分：

- 内容固有复杂度；
- 相对于当前学习者的复杂度。

主要变量包括：

- 前置知识数量；
- 依赖深度；
- 同时交互的概念数量；
- 推理步骤数量；
- 抽象程度；
- 用户已掌握的相关知识。

### 2.4 错误类型

错误至少应区分：

- 知识缺失；
- 概念误解；
- 条件遗漏；
- 方法选择错误；
- 执行错误；
- 记忆提取失败；
- 迁移失败；
- 表达不完整；
- 元认知错误。

错误识别建议采用：

```text
确定性规则
→ 误区模式库
→ 诊断追问
→ LLM 语义分类
→ 后续题验证
```

### 2.5 学习阶段

学习阶段应根据行为证据推导，而不是按课程进度机械计算：

```text
未诊断
→ 知识断层
→ 初步建模
→ 有提示模仿
→ 无提示应用
→ 延迟保持
→ 迁移掌握
```

---

## 3. 上传一本书后的工作流程

以上传《哥德尔、艾舍尔、巴赫》EPUB 为例，Askora 不应直接从第一章开始总结，而应执行以下流程。

### 3.1 明确学习目标

例如：

- 理解全书主要思想；
- 理解形式系统、自指与不完备性；
- 能解释哥德尔证明的核心结构；
- 能将怪圈概念迁移到程序、AI 或意识问题中。

不同目标对应不同学习路径。

### 3.2 解析 EPUB

提取：

- 目录和章节；
- 段落和脚注；
- 插图与案例；
- 定义、论证、谜题和练习；
- 原文位置和引用锚点。

### 3.3 构建知识结构

示意：

```text
符号与规则
→ 形式系统
→ 对象语言与元语言
→ 自指
→ 对角化
→ 哥德尔编码
→ 不完备性
→ 怪圈、意识与智能
```

机器抽取的概念和关系只能作为候选，需要经过：

- 同义词合并；
- 原文证据绑定；
- 循环依赖检查；
- 置信度标记；
- 人工修正。

### 3.4 诊断先备知识

系统用少量高信息增益题目判断：

- 是否理解公理与定理；
- 是否理解系统与元系统；
- 是否能操作简单形式规则；
- 是否理解自指和悖论；
- 是否具备基础逻辑知识。

### 3.5 生成概念路径

学习路径不必等于原书目录顺序：

```text
建立直觉
→ 掌握形式机制
→ 理解不完备性
→ 建立跨领域联系
→ 完成迁移任务
```

### 3.6 动态教学

针对同一知识点，根据学习状态采用不同策略：

- 完全陌生：直接讲解 + 完整示例；
- 有初步理解：苏格拉底追问；
- 会模仿：示例褪去 + 半完成题；
- 能独立完成：变式练习；
- 已稳定掌握：延迟测试 + 迁移任务。

---

## 4. AI 学习工具的八类技术系统

### 4.1 内容解析与知识建模

解决“材料中有什么、这些内容如何组织、哪些内容能够成为教学与评估对象”。

该系统不是普通 RAG 的预处理器。普通文档系统只需生成可检索文本块；Askora 必须进一步生成可审计、可编辑、可用于诊断和路径规划的教育内容模型。

核心边界：

- 本系统负责描述材料、知识对象及其关系；
- 不直接判断用户是否掌握；
- 不直接选择当前教学策略；
- 不把 LLM 生成的解释自动视为原材料事实；
- 不允许无法定位原文证据的机器推断直接进入已发布知识库。

最终产物应同时服务于：

- 原文检索与精确引用；
- 学习路径规划；
- 先备知识诊断；
- 教学任务生成；
- 题目与提示生成；
- 错误和误区诊断；
- 内容版本更新；
- 人工审核与算法审计。

#### 4.1.1 分层内容模型

内容模型建议分为八层：

```text
RawAsset
→ MaterialRevision
→ DocumentNode
→ SourceSpan
→ KnowledgeObject
→ KnowledgeRelation
→ PedagogicalAsset
→ IndexProjection
```

各层职责如下。

| 层 | 含义 | 主要职责 |
|---|---|---|
| `RawAsset` | 原始文件 | 保存原文件、校验和、MIME、文件大小和安全扫描结果 |
| `MaterialRevision` | 材料版本 | 固化某次导入或更新后的不可变版本 |
| `DocumentNode` | 文档结构节点 | 表示卷、章、节、段落、表格、图片、公式、代码块、脚注等 |
| `SourceSpan` | 最小证据片段 | 为知识对象和关系提供可复现的原文锚点 |
| `KnowledgeObject` | 可学习知识对象 | 表示概念、命题、规则、过程、事实、方法等 |
| `KnowledgeRelation` | 知识关系 | 表示前置、组成、推导、对比、应用、例证等关系 |
| `PedagogicalAsset` | 教学素材 | 表示定义、解释、例子、反例、练习、解答、提示、误区等 |
| `IndexProjection` | 检索与图计算投影 | 生成全文索引、向量索引、检索块和图结构，不作为事实源 |

关系数据库中的规范化内容模型应作为唯一事实源。向量库、全文索引和图数据库均属于可重建投影。

#### 4.1.2 总体处理流水线

```text
文件导入与校验
→ 文件类型识别
→ 格式解析
→ 文本与结构规范化
→ 版面及多模态恢复
→ 文档结构树生成
→ 语义单元切分
→ 知识对象候选抽取
→ 实体消歧与同义词合并
→ 知识关系及前置关系推断
→ 教学素材抽取
→ 证据绑定与置信度计算
→ 规则校验和模型复核
→ 人工审核或自动发布
→ 生成检索与图索引投影
```

处理应具备幂等性。同一文件、同一解析器版本和同一配置重复执行时，应得到相同的稳定标识和等价结果。

建议处理状态：

```text
uploaded
→ validated
→ parsed
→ modeled
→ review_required / publishable
→ published
```

异常状态：

```text
rejected
failed
partially_parsed
superseded
```

`processing_status` 不应只表示“是否完成分块”，而应能区分解析完成、知识建模完成、等待复核和已发布。

#### 4.1.3 文件适配器与解析要求

当前优先支持 Markdown、TXT、EPUB、PDF、DOCX，后续扩展 HTML、网页快照、幻灯片、音频和视频转写稿。

文件类型不能只依据扩展名判断，应综合：

- 文件签名；
- MIME；
- 容器结构；
- 扩展名；
- 解析探测结果。

各格式最低解析要求：

| 格式 | 必须保留的结构 | 主要风险 |
|---|---|---|
| Markdown | 标题层级、段落、列表、表格、引用、代码块、公式 | 正则切分破坏代码块和嵌套结构 |
| TXT | 段落、空行、可能的章节标题 | 缺少显式结构，需要结构推断 |
| EPUB | `spine`、TOC、章节、标题、脚注、图片、内部链接、EPUB CFI | 直接去除 HTML 会丢失章节和引用锚点 |
| PDF | 页码、文本框、阅读顺序、标题、表格、公式、图片、脚注 | 多栏错序、扫描页、页眉页脚污染、字符编码错误 |
| DOCX | 标题样式、段落、列表、表格、图片、题注、脚注、公式 | 只读取段落会丢失表格与样式语义 |

PDF 解析采用分级策略：

```text
原生文本提取
→ 版面分析与阅读顺序恢复
→ 局部 OCR
→ 整页 OCR
→ 低置信度人工复核
```

OCR 只应在无文本层、文本层明显损坏或局部图像包含关键文字时启用，避免对正常数字 PDF 重复识别。

#### 4.1.4 统一文档中间表示

所有解析器必须输出统一的 `DocumentIR`，而不是只输出 `full_text + chunks`。

示意结构：

```json
{
  "material_id": "mat_xxx",
  "revision_id": "rev_xxx",
  "source_type": "epub",
  "checksum": "sha256:...",
  "language": "zh-CN",
  "parser": {
    "name": "epub_parser",
    "version": "2.0.0"
  },
  "nodes": [
    {
      "node_id": "node_xxx",
      "parent_id": "node_parent",
      "node_type": "section",
      "order": 12,
      "title": "形式系统",
      "text": "...",
      "anchor": {
        "kind": "epub_cfi",
        "value": "epubcfi(...)"
      },
      "attributes": {
        "heading_level": 2
      }
    }
  ]
}
```

`DocumentNode.node_type` 至少包括：

```text
document
part
chapter
section
paragraph
list
list_item
table
figure
caption
equation
code
blockquote
footnote
exercise
solution
```

设计要求：

- 原始文本不可被后续摘要覆盖；
- 清洗文本、OCR 文本和原始文本应可区分；
- 每个节点必须有稳定顺序；
- 尽可能提供页码、DOM 路径、EPUB CFI、字符偏移等锚点；
- 解析器升级产生新 `MaterialRevision`，不得静默覆盖旧版本；
- 派生字段必须记录生成器和版本。

#### 4.1.5 原文证据与定位锚点

`SourceSpan` 是所有知识建模结果的证据基础。

建议字段：

```text
span_id
revision_id
node_id
start_offset
end_offset
quoted_text
page_number
anchor_type
anchor_value
content_hash
```

锚点优先级：

```text
结构化原生锚点
> 页码 + 文本框坐标
> 节点路径 + 字符偏移
> 文本指纹匹配
```

知识对象、关系、例子、题目和误区均应绑定一个或多个 `SourceSpan`。用户点击引用时，系统必须能够回到对应页、章节或段落，而不是只返回一个不可验证的向量检索块。

当材料版本更新导致偏移变化时，可使用：

- 内容哈希；
- 前后文指纹；
- 结构路径；
- 相邻节点；

重新定位旧锚点。

#### 4.1.6 语义分块与多粒度内容单元

Askora 不应使用一种固定 Token 长度同时承担检索、教学和引用。

建议建立三种粒度：

| 粒度 | 目标 | 典型范围 |
|---|---|---|
| `EvidenceSpan` | 精确引用和证据绑定 | 一句话到一个短段落 |
| `SemanticUnit` | 表达一个相对完整的语义或论证步骤 | 通常 150～600 Token |
| `RetrievalChunk` | 提高检索召回率的索引投影 | 通常 300～900 Token，可少量重叠 |

切分顺序：

```text
文档显式结构
→ 段落和列表边界
→ 论证与话题边界
→ 句子边界
→ Token 上限兜底
```

硬约束：

- 代码块、公式、表格行组、题目与其条件不得随意截断；
- 标题必须与其直接内容建立结构关系；
- 定义句和被定义术语尽量位于同一语义单元；
- 例题题干、图表、解题步骤和答案应保持可关联；
- 章节标题不能作为独立无语义检索块；
- 重叠文本只存在于 `RetrievalChunk` 投影，不能形成重复知识事实。

语义边界评分可综合：

```text
结构边界权重
+ 话题变化
+ 指代连续性
+ 句法完整性
+ 长度惩罚
+ 特殊内容完整性约束
```

初期可采用规则和嵌入相似度结合，不能把所有分块工作交给 LLM。

#### 4.1.7 知识对象模型

知识对象应表达“学习者需要掌握什么”，而非简单名词抽取。

核心类型：

| 类型 | 含义 | 示例 |
|---|---|---|
| `concept` | 概念或术语 | 形式系统、自指、相变潜热 |
| `proposition` | 可判断真假的命题 | 完备系统中的某类命题可被证明或证伪 |
| `principle` | 规律、原理或约束 | 能量守恒、鸽巢原理 |
| `procedure` | 有步骤的操作或推理过程 | 哥德尔编码、解一元二次方程 |
| `method` | 可选择的策略或方法 | 反证法、变量替换法 |
| `fact` | 稳定事实或材料内陈述 | 人名、时间、定义域条件 |
| `representation` | 表达系统或表征形式 | 真值表、状态图、几何图示 |
| `skill` | 可观测能力 | 识别自指结构、构造反例 |

建议字段：

```text
knowledge_object_id
canonical_name
object_type
description
aliases
scope
language
abstraction_level
intrinsic_difficulty
estimated_reasoning_steps
status
confidence
created_by
extractor_version
```

其中：

- `canonical_name` 用于稳定标识，不等于某一本书的原始措辞；
- `description` 是规范化描述，必须绑定来源或标记为系统归纳；
- `scope` 区分材料内局部概念、学科概念和跨学科概念；
- `intrinsic_difficulty` 是材料侧估计，不代表特定用户感受到的难度；
- `status` 至少区分候选、机器验证、待审核、已批准、已废弃。

知识对象和原文提及应拆分：

```text
KnowledgeObject：规范化概念“形式系统”
KnowledgeMention：本书第 3 章中出现的“形式系统”及其原文位置
```

这样同一知识对象可以连接多本材料，同时保留每本材料的表述差异。

#### 4.1.8 教学素材模型

教学素材不是知识对象本身，而是用于教授、练习或评估知识对象的载体。

类型至少包括：

```text
definition
explanation
example
counterexample
analogy
case
exercise
solution
hint
rubric
misconception
warning
summary
```

关键关系示例：

```text
definition --defines--> concept
example --exemplifies--> concept
counterexample --refutes_generalization_of--> proposition
exercise --assesses--> knowledge_object
hint --supports--> procedure_step
misconception --misunderstands--> knowledge_object
solution --solves--> exercise
```

从原文抽取和由模型生成的素材必须分开：

```text
provenance = source_extracted
provenance = system_generated
provenance = user_created
```

系统生成的例子、题目和解释不能伪装为原书内容，且应记录生成时使用的知识对象版本、模型和 Prompt 版本。

练习建议结构化为：

```text
题干
已知条件
任务要求
答案类型
标准答案
解题步骤
评分 Rubric
目标知识对象
前置知识对象
难度参数
提示阶梯
常见错误
来源证据
```

#### 4.1.9 知识关系与前置依赖图

完整知识图谱可以有环，但用于学习路径规划的“硬前置图”应尽量保持有向无环。

关系类型建议分组。

结构关系：

```text
is_a
part_of
has_step
has_property
```

认知依赖关系：

```text
prerequisite_of
depends_on
supports_understanding_of
```

逻辑与语义关系：

```text
entails
derived_from
equivalent_to
contrasts_with
causes
constrains
```

教学关系：

```text
exemplifies
applies_to
assesses
misconception_of
remediates
transfers_to
```

边模型至少保存：

```text
relation_id
source_object_id
target_object_id
relation_type
strength
hardness
scope
evidence_span_ids
confidence
inference_method
extractor_version
review_status
```

方向约定：

```text
A --prerequisite_of--> B
```

表示学习 B 前通常需要掌握 A。

前置关系不能仅凭章节先后推断，应综合：

1. 原文明确表达“先理解 A 才能理解 B”；
2. B 的定义或过程是否引用 A；
3. 不掌握 A 时是否无法完成 B 的代表性任务；
4. A 是否只是有帮助，而非必要；
5. 是否存在更小的真正前置集合。

前置关系分级：

```text
hard：缺失时通常无法学习目标知识
soft：掌握后显著降低学习成本
contextual：只在特定任务或材料表述下需要
```

图构建后执行：

- 自环删除；
- 重复边合并；
- 传递约简；
- 强连通分量检测；
- 环依赖解释；
- 低置信度边降级；
- 孤立节点检查。

若存在真实互相依赖，应先形成“概念簇”或“联合教学单元”，而不是强行删除所有环。

#### 4.1.10 候选抽取与融合算法

知识建模采用混合流水线：

```text
确定性解析器
+ 结构规则
+ 词典与术语识别
+ 嵌入相似度
+ 受约束 LLM 抽取
+ 规则校验
+ 模型复核
+ 人工审核
```

建议分阶段执行。

第一遍：局部候选抽取

- 在章节或语义单元内抽取术语、定义、命题、步骤、例子、练习和显式关系；
- 使用 JSON Schema 约束输出；
- 所有候选必须附带原文片段 ID；
- 不进行跨全书的激进合并。

第二遍：章节级归并

- 合并同一章节中的重复术语；
- 区分同名异义；
- 建立概念与定义、例子、练习的局部关系；
- 检查是否存在无证据对象。

第三遍：文档级实体消歧

- 汇总别名和缩写；
- 识别跨章节重复概念；
- 合并稳定同义项；
- 保留争议项和多义项。

第四遍：关系和前置推断

- 优先抽取显式关系；
- 再通过定义引用、过程依赖和任务依赖推断隐式关系；
- 对硬前置边执行更严格验证。

第五遍：反向验证

对每个高价值对象和关系回答：

```text
原文证据是否真的支持该结论？
是否存在更合理的对象类型？
是否把章节顺序误判成前置关系？
是否把例子中的偶然属性误判成概念属性？
是否错误合并了同名概念？
```

LLM 负责候选生成和语义判断，不负责最终事实裁决。

#### 4.1.11 实体消歧、同义词与跨材料合并

实体归并建议按以下顺序执行：

```text
标准化字符串匹配
→ 明确别名字典
→ 缩写和全称规则
→ 上下文与类型一致性
→ 嵌入候选召回
→ LLM 比较判断
→ 人工确认
```

自动合并必须同时满足：

- 对象类型兼容；
- 定义核心一致；
- 上下文不冲突；
- 不属于不同学科中的同名概念；
- 合并置信度达到阈值。

不能确定时应创建：

```text
possible_same_as
```

而不是直接合并。

建议采用两级命名空间：

```text
Document-local Object
→ Canonical Knowledge Object
```

材料内对象允许保留作者特有定义；规范知识对象用于跨材料聚合。两者通过 `mentions`、`maps_to` 或 `specializes` 连接。

#### 4.1.12 置信度与证据模型

置信度不能直接使用 LLM 自报概率，应由可观测信号组合并通过审核数据校准。

初始可使用可配置评分：

```text
confidence =
  0.35 × evidence_quality
+ 0.25 × extractor_agreement
+ 0.20 × structural_explicitness
+ 0.20 × validator_score
```

其中：

- `evidence_quality`：证据是否直接、完整、可定位；
- `extractor_agreement`：规则、不同模型或不同抽取轮次是否一致；
- `structural_explicitness`：标题、定义句、编号步骤等结构是否明确；
- `validator_score`：反向验证是否通过。

权重只是第一阶段工程默认值，后续应使用人工审核结果进行校准。

每个对象和关系必须同时保存：

```text
当前值
证据来源
抽取方法
置信度
审核状态
模型或规则版本
生成时间
```

低置信度结果可以用于召回和人工提示，但不能用于：

- 硬前置阻断；
- 掌握门槛判定；
- 高风险事实回答；
- 自动生成决定性评分标准。

#### 4.1.13 误区抽取的特殊约束

误区不能仅根据“错误说法看起来合理”自动生成。

误区来源分为：

```text
source_explicit：材料明确指出的常见错误
assessment_observed：从真实答题行为中反复观察到
expert_curated：专家维护
model_hypothesized：模型提出的待验证假设
```

只有前三类或经过后续行为验证的假设，才能成为稳定误区模式。

误区结构建议包括：

```text
misconception_id
错误命题
涉及知识对象
触发条件
典型错误表现
鉴别题
纠正策略
反例
证据来源
状态与置信度
```

作者为了论证而临时提出的错误观点、小说人物的错误陈述、反讽和假设情境，不能直接标记为学习者误区。

#### 4.1.14 质量门禁与发布规则

机器完成抽取不等于知识模型可用。

自动质量检查至少包括：

- 文本覆盖率；
- 结构节点覆盖率；
- 锚点可回放率；
- 无证据知识对象比例；
- 重复对象比例；
- 未连接对象比例；
- 关系冲突；
- 硬前置环；
- 表格、公式、代码块完整性；
- 语言和字符编码异常；
- 引用文本与原文哈希一致性。

第一阶段建议门槛：

```text
已发布知识对象的证据覆盖率 = 100%
高置信度引用锚点可回放率 ≥ 99%
硬前置边必须存在证据或经过人工批准
低置信度硬前置边数量 = 0
严重解析错误数量 = 0
```

状态流转：

```text
candidate
→ machine_verified
→ review_required / approved
→ published
→ superseded / rejected
```

自动发布策略应按材料类型分级：

- 结构清晰、解析质量高的 Markdown 可较多自动发布；
- 普通数字 EPUB 和 DOCX 可抽样复核；
- 多栏 PDF、扫描书、公式密集材料应提高复核比例；
- 低质量 OCR 结果不得直接进入正式知识图谱。

#### 4.1.15 增量更新与版本管理

材料、解析器、抽取 Prompt、模型或规则发生变化时，都可能改变知识模型。

需要保存：

```text
material_revision
parser_version
segmentation_version
extractor_version
prompt_version
schema_version
index_version
```

更新流程：

```text
计算文件和节点差异
→ 匹配未变化节点
→ 只重算受影响语义单元
→ 失效相关知识对象和关系
→ 重新抽取局部子图
→ 执行冲突与回归检查
→ 发布新版本
```

稳定知识对象 ID 不应因为材料重新上传而全部变化。

建议采用：

- 内容哈希识别完全相同节点；
- 结构路径和文本指纹匹配移动节点；
- `supersedes` 表示对象替代关系；
- `tombstone` 保留已删除对象的历史引用；
- 学习记录绑定规范知识对象 ID 和当时版本。

这样即使资料更新，也不会无故丢失用户已有的学习历史。

#### 4.1.16 存储模型与索引投影

建议新增或重构以下核心表：

```text
material_revisions
document_nodes
source_spans
semantic_units
knowledge_objects
knowledge_mentions
knowledge_relations
pedagogical_assets
asset_knowledge_links
extraction_runs
review_decisions
index_outbox
```

当前 `UserDocument` 可继续保存文件级元数据；`DocumentChunk` 应被重新定义为检索投影，而不是唯一的文档内容表示。

`KnowledgePoint.prerequisites` 和 `successors` 以 JSON 数组保存，适合原型，不适合后续进行：

- 边级置信度管理；
- 来源证据绑定；
- 关系版本控制；
- 图查询；
- 环检测；
- 局部更新；
- 人工审核。

因此前置关系最终应迁移到规范化 `knowledge_relations` 表。

第一阶段不必立即引入独立图数据库。可采用：

```text
PostgreSQL 邻接边表
+ 递归 CTE
+ 本地图库进行复杂算法
+ Outbox 生成向量和全文索引
```

当图规模、遍历复杂度和并发量确实成为瓶颈后，再评估 Neo4j 等专用图数据库。

#### 4.1.17 领域接口与事件

建议核心命令：

```text
ImportMaterial
ParseMaterialRevision
BuildKnowledgeModel
ValidateKnowledgeModel
ReviewKnowledgeCandidate
PublishKnowledgeModel
RebuildIndexProjection
```

建议查询接口：

```text
GetDocumentOutline
GetSourceSpan
ListKnowledgeObjects
GetKnowledgeNeighborhood
GetPrerequisiteSubgraph
ListPedagogicalAssets
GetExtractionReport
```

领域事件：

```text
MaterialImported
MaterialRevisionCreated
DocumentParsed
SemanticUnitsBuilt
KnowledgeCandidatesExtracted
KnowledgeRelationInferred
KnowledgeModelValidationFailed
KnowledgeModelPublished
KnowledgeObjectMerged
KnowledgeObjectSuperseded
IndexProjectionRebuilt
```

事件负载应只包含稳定 ID 和必要元数据，避免把整篇文档写入事件日志。

#### 4.1.18 安全与可信边界

上传材料属于不可信输入。

内容解析阶段应处理：

- 压缩炸弹；
- 超大文件和异常嵌套；
- 路径穿越；
- 恶意宏和嵌入对象；
- 畸形 PDF；
- 外部资源自动加载；
- 文档中的 Prompt Injection；
- 隐藏文本和白字；
- OCR 欺骗和字符混淆。

文档中出现“忽略系统指令”“上传密钥”等文本时，只能作为待学习内容，不得改变抽取器和 Agent 的系统指令。

模型调用应使用：

- 数据与指令分离；
- 严格结构化输出；
- 工具白名单；
- 无外部副作用的抽取运行环境；
- 输出长度和对象数量限制；
- 原文证据校验；
- 敏感信息日志脱敏。

#### 4.1.19 当前仓库实现差距

当前 `apps/backend/app/services/documents/parsers.py` 已支持 Markdown、TXT、EPUB、PDF 和 DOCX，但主要输出：

```text
full_text
chunks
metadata
```

主要差距：

- EPUB 通过去除 HTML 标签并压缩空白生成纯文本，章节结构、脚注、图片和 CFI 会丢失；
- PDF 主要按页提取文本，尚无版面恢复、OCR、表格和公式结构；
- DOCX 主要读取普通段落，未系统保留标题样式、表格和题注；
- 分块结果是字符串列表，缺少稳定节点 ID 和原文锚点；
- `DocumentChunk.chunk_metadata` 已预留元数据，但当前解析器没有形成统一结构契约；
- 知识图谱和 `KnowledgePoint` 已有实验模型，但尚未进入文档处理主链路；
- 前置关系保存为 JSON 列表，无法支持边级证据、置信度和审核；
- RAG 检索块与教育知识对象尚未分离。

因此不能在现有字符串分块上直接叠加更多 LLM Prompt，应先建立 `DocumentIR + SourceSpan + KnowledgeObject + KnowledgeRelation` 四个核心模型。

#### 4.1.20 分阶段落地路线

P0：统一文档结构和引用基础

- 新增 `MaterialRevision`、`DocumentNode`、`SourceSpan`；
- 将各格式解析器统一输出 `DocumentIR`；
- 为现有 `ParsedContent` 提供兼容适配器；
- 保留章节、页码和稳定锚点；
- `DocumentChunk` 从 `DocumentIR` 派生；
- 建立解析黄金样本和回归测试。

P1：材料内知识建模闭环

- 新增知识对象、提及、关系和教学素材表；
- 实现章节级候选抽取；
- 实现原文证据强绑定；
- 实现同义词合并、重复检测和关系校验；
- 提供人工审核界面或最小审核 API；
- 输出材料内前置依赖图。

P2：多材料统一知识目录

- 建立材料内对象到规范知识对象的映射；
- 支持跨材料定义对比和冲突保留；
- 将图谱接入学习路径与诊断模块；
- 支持增量更新、版本迁移和 Outbox 索引同步。

P3：复杂文档与自动质量优化

- 加入 PDF 版面分析、OCR、表格、公式和图片理解；
- 用人工审核数据校准置信度；
- 建立自动抽样审核；
- 优化跨材料实体消歧和前置关系推断；
- 根据真实教学效果反向评估知识模型质量。

#### 4.1.21 验收指标

解析质量：

```text
文本覆盖率
结构恢复准确率
阅读顺序准确率
锚点可回放率
表格/公式/代码完整率
OCR 字符错误率
```

知识建模质量：

```text
知识对象准确率与召回率
重复合并准确率
实体消歧准确率
关系准确率
硬前置关系准确率
证据覆盖率
无依据生成率
人工驳回率
```

工程质量：

```text
重复执行一致性
增量重算比例
单页/千 Token 处理成本
处理时延
失败可恢复率
索引重建一致性
版本可追溯率
```

教育有效性：

```text
知识路径是否减少无效前置学习
诊断题是否覆盖关键知识对象
教学引用是否能准确回到原文
由知识图谱生成的任务是否真正测量目标能力
知识模型错误是否导致错误教学决策
```

应建立包含 Markdown、EPUB、数字 PDF、扫描 PDF、DOCX、公式密集材料和表格密集材料的黄金测试集。算法升级必须对该测试集执行回归比较，不能只通过少量人工观感判断质量。

### 4.2 检索与知识供给

解决的不是普通问答中的“哪些文本和用户问题最相似”，而是：

> **为了执行当前教学动作，系统需要向教学策略引擎和生成模型提供哪些知识、证据、示例、误区、前置材料与引用锚点。**

检索与知识供给层位于知识建模层和教学执行层之间：

```text
教学策略引擎
→ 提出知识供给需求
→ 检索规划器生成检索计划
→ 多路召回与图遍历
→ 重排序与证据组合
→ 上下文压缩与引用校验
→ 生成 EvidenceBundle
→ LLM 执行讲解、提问、提示或评估
```

核心边界：

- 教学策略引擎决定“为什么取、需要什么、允许暴露多少”；
- 检索层决定“从哪里取、取哪些、如何组合”；
- LLM 负责基于证据包表达，不应自行决定教学目标；
- 检索结果不能直接修改学习者掌握状态；
- RAG 只负责知识供给，不负责判断当前应该讲解、追问、提示还是测试。

#### 4.2.1 输入：教学检索请求

检索层不应直接把用户最后一句话作为唯一查询，而应接收结构化的 `TeachingRetrievalRequest`：

```text
TeachingRetrievalRequest
├── request_id
├── learning_goal_id
├── target_concept_ids[]
├── prerequisite_concept_ids[]
├── teaching_action
├── learner_stage
├── learner_state_summary
├── misconception_hypotheses[]
├── source_scope
├── allowed_knowledge_types[]
├── answer_leakage_policy
├── context_budget
├── freshness_requirement
└── latency_budget
```

关键字段含义：

- `teaching_action`：讲解、苏格拉底追问、提示、诊断、练习、评分、复习或迁移；
- `learner_stage`：决定材料深度和抽象程度；
- `misconception_hypotheses`：决定是否检索反例、误区解释和诊断题；
- `source_scope`：限定当前书籍、章节、用户知识库或允许的外部来源；
- `allowed_knowledge_types`：限制定义、例题、答案、证明等材料类型；
- `answer_leakage_policy`：控制能否暴露结论、关键步骤和完整答案；
- `context_budget`：限制最终证据包的长度，而不是限制初始召回数量。

示例：同样是用户问“哥德尔编码有什么用”，不同教学动作会产生不同请求：

```text
直接讲解：检索定义 + 机制 + 完整示例 + 原文论证
苏格拉底提问：检索前置概念 + 可观察矛盾 + 引导问题，不取完整结论
一级提示：只检索下一步所需事实，不取后续推导
错误诊断：检索常见误区 + 反例 + 判分标准
迁移练习：检索同一结构在程序、自指语句或编码系统中的异质案例
```

#### 4.2.2 检索对象：从文本块升级为教学知识单元

普通 RAG 的基本对象通常是 `Chunk`。Askora 应同时保存两种对象：

1. `SourceChunk`：忠实对应原文位置的文本或多模态片段；
2. `KnowledgeUnit`：从原文中抽取并绑定证据的教学知识单元。

`KnowledgeUnit` 至少包括：

```text
KnowledgeUnit
├── unit_id
├── unit_type
├── canonical_concept_ids[]
├── content
├── source_chunk_ids[]
├── prerequisite_ids[]
├── related_unit_ids[]
├── difficulty
├── abstraction_level
├── cognitive_load
├── pedagogical_roles[]
├── answer_exposure_level
├── confidence
└── version
```

建议支持的 `unit_type`：

- 定义；
- 命题与事实；
- 机制与因果关系；
- 操作步骤与程序；
- 证明与论证；
- 前置知识；
- 完整示例；
- 半完成示例；
- 反例；
- 类比；
- 常见误区；
- 诊断问题；
- 练习题；
- 评分 Rubric；
- 原始引用证据。

检索粒度不能固定。系统应能够在以下层级间动态切换：

```text
文档
→ 篇章
→ 小节
→ 段落
→ 句子
→ 知识单元
→ 概念关系
```

#### 4.2.3 多索引存储架构

单一向量数据库不足以支撑教学检索。建议建立互补索引：

| 索引 | 主要作用 | 适用场景 |
|---|---|---|
| 倒排索引 | 精确术语、公式、专有名词和关键词匹配 | 定义查找、原文定位 |
| 向量索引 | 语义近似、改写和跨措辞匹配 | 自然语言问题、类比检索 |
| 知识图谱 | 概念依赖、因果、组成、对比和多跳关系 | 前置补全、跨章节推理 |
| 层级页面索引 | 保留目录、章节、小节和页面结构 | PageIndex、范围收缩、引用定位 |
| 结构化题库索引 | 难度、知识点、题型、答案和 Rubric | 练习、诊断、迁移测试 |
| 误区索引 | 错误模式、触发条件、反例和纠正路径 | 错误诊断、反馈生成 |
| 引用映射索引 | 知识单元到原文页码、段落和坐标的映射 | 引用校验、原文跳转 |

逻辑结构：

```text
原始材料库
├── SourceChunk Store
├── KnowledgeUnit Store
├── Lexical Index
├── Dense Vector Index
├── Knowledge Graph
├── Hierarchical Page Index
├── Assessment Item Store
└── Citation Anchor Store
```

用户上传材料、系统生成内容和外部资料应分库或至少分命名空间保存，避免将模型生成内容误当作原始证据。

#### 4.2.4 检索计划生成

检索前先由 `RetrievalPlanner` 将教学请求转换为可执行计划：

```text
TeachingRetrievalRequest
→ 范围解析
→ 概念标准化
→ 查询分解
→ 查询扩展
→ 检索路线选择
→ 过滤条件生成
→ 证据覆盖要求生成
→ 预算分配
```

检索计划可包含多类子查询：

```text
literal_query       精确术语和原文表达
semantic_query      用户问题的语义改写
concept_query       目标概念及同义概念
prerequisite_query  当前解释所需前置知识
misconception_query 可能误区与反例
example_query       与当前阶段匹配的示例
citation_query      精确原文和位置锚点
```

查询扩展必须受知识图谱和材料词表约束，不能让 LLM 无限制扩展，否则容易引入无关概念。

#### 4.2.5 多路召回与候选融合

候选召回建议并行执行：

```text
BM25 / 关键词召回
+ 向量语义召回
+ 知识图谱邻居与路径召回
+ PageIndex 层级召回
+ 结构化题库或误区库召回
```

初始阶段应采用“宽召回、严筛选”，例如每一路召回 Top 20～50，再进入融合和重排序。

多路结果可使用 Reciprocal Rank Fusion：

```text
RRF(d) = Σ 1 / (k + rank_i(d))
```

RRF 的优势是无需先统一 BM25 分数、向量相似度和图距离的量纲。后续有标注数据后，可训练 Learning-to-Rank 模型替代固定融合。

召回阶段必须先应用硬过滤：

- 用户权限；
- 指定材料和章节范围；
- 文档版本；
- 语言；
- 知识单元类型；
- 答案暴露等级；
- 题目是否已使用；
- 来源是否允许进入当前教学会话。

#### 4.2.6 教学感知重排序

普通重排序只计算“与问题有多相关”。Askora 需要计算“与当前教学动作有多适配”。

建议的候选评分：

```text
Score(d) =
  w_semantic      × SemanticRelevance
+ w_lexical       × LexicalRelevance
+ w_graph         × GraphProximity
+ w_goal          × GoalAlignment
+ w_stage         × LearnerStageFit
+ w_type          × PedagogicalRoleFit
+ w_authority     × SourceAuthority
+ w_evidence      × CitationQuality
+ w_novelty       × InformationGain
- w_redundancy    × Redundancy
- w_overload      × CognitiveOverload
- w_leakage       × AnswerLeakageRisk
- w_conflict      × UnresolvedConflictRisk
```

权重不应固定，而应由教学动作决定：

| 教学动作 | 高权重材料 | 应抑制的材料 |
|---|---|---|
| 直接讲解 | 定义、机制、完整例子、权威原文 | 重复片段、过度细节 |
| 苏格拉底提问 | 前置知识、矛盾点、反例、诊断问题 | 直接结论、完整推导 |
| 分级提示 | 当前卡点、下一步条件、局部示例 | 后续步骤、最终答案 |
| 错误诊断 | Rubric、误区模式、反例、过程证据 | 泛化讲解、无关背景 |
| 练习生成 | 目标知识点、难度模板、变式约束 | 原题复制、答案泄漏 |
| 延迟复习 | 核心线索、检索练习、易混概念 | 完整笔记、直接复述 |
| 迁移测试 | 深层原理、异质情境、边界条件 | 表面相似的重复题 |

第一阶段可采用：

```text
规则权重 + Cross-Encoder 重排序 + LLM 小规模判别
```

LLM 只对 Top 10～20 候选进行教学适配判别，不参与大规模初始召回。

#### 4.2.7 从 Top-K 选择升级为证据集合优化

最终上下文不应简单取重排序后的前 K 个片段，因为前 K 个结果通常高度重复。

应把选择过程建模为带预算的集合优化：

```text
最大化：
相关性 + 概念覆盖 + 教学角色覆盖 + 来源多样性 + 信息增益

约束：
Token 预算
答案泄漏限制
认知负荷限制
引用完整性
来源权限
```

可采用：

- Maximal Marginal Relevance，降低语义重复；
- Set Cover，保证关键概念和前置条件被覆盖；
- Knapsack，在 Token 预算内选择价值最高的证据组合；
- 规则约束，保证至少包含一条原始证据和必要的教学角色。

例如一次概念讲解的证据包可要求：

```text
1 个核心定义
+ 1 个机制说明
+ 1 个适龄示例
+ 0～1 个反例
+ 1 个原文引用
+ 必要的前置知识
```

#### 4.2.8 上下文压缩与知识供给

压缩目标不是单纯缩短文本，而是在预算内保留完成教学动作所需的信息结构。

推荐顺序：

```text
去重
→ 句子级证据抽取
→ 删除旁支信息
→ 按教学角色重组
→ 必要时生成受约束摘要
→ 引用一致性校验
```

优先使用抽取式压缩；只有在原文过长或跨片段整合时才使用生成式压缩。生成式摘要必须保留：

- 对应的源片段 ID；
- 可追溯引用锚点；
- 哪些内容是原文事实，哪些是模型归纳；
- 摘要置信度。

建议将上下文分为三层：

```text
Core Evidence      当前动作不可缺少的证据
Support Evidence   用于例子、反例和补充解释
Reserve Evidence   不进入首轮 Prompt，工具调用时按需追加
```

上下文预算可按教学动作动态分配：

```text
总预算 = 核心证据 + 前置知识 + 教学样例 + 引用信息 + 输出空间
```

系统应为模型预留充足输出空间，不能让检索内容占满上下文窗口。

#### 4.2.9 GraphRAG 与 PageIndex 的职责边界

GraphRAG 和 PageIndex 不是两种互相替代的 RAG，而是解决不同问题。

**GraphRAG 适合：**

- 找某概念的前置知识；
- 进行跨章节、多跳关系检索；
- 找因果链、组成关系和概念对比；
- 发现用户错误所涉及的上游知识断层；
- 为学习路径和迁移任务提供关系结构。

**PageIndex 适合：**

- 保留书籍或长文档的目录结构；
- 先定位章节，再在章节内细检索；
- 避免切块破坏上下文；
- 获取连续论证、表格说明和原文位置；
- 支持用户跳转到准确章节、页码或段落。

推荐路由：

```text
精确术语或局部事实
→ 关键词 + 向量检索

长文档章节定位或连续论证
→ PageIndex + 章节内检索

前置依赖、关系解释或跨章节问题
→ GraphRAG + 文本证据回填

复杂问题
→ PageIndex 缩小范围 + GraphRAG 扩展关系 + 混合检索取证
```

不应对所有请求默认运行 GraphRAG 和 PageIndex，否则会增加延迟、成本和噪声。

#### 4.2.10 EvidenceBundle：知识供给协议

检索层最终输出的不是若干文本，而是结构化 `EvidenceBundle`：

```json
{
  "request_id": "req_001",
  "teaching_action": "SOCRATIC_QUESTION",
  "target_concepts": ["godel_numbering"],
  "coverage": {
    "required": ["symbol_encoding", "meta_language"],
    "covered": ["symbol_encoding", "meta_language"]
  },
  "evidence": [
    {
      "evidence_id": "ev_01",
      "knowledge_unit_id": "ku_102",
      "pedagogical_role": "PREREQUISITE",
      "content": "...",
      "source_anchor": {
        "document_id": "doc_01",
        "chapter": "第八章",
        "paragraph_id": "p_318"
      },
      "relevance": 0.91,
      "confidence": 0.96,
      "answer_exposure_level": 1,
      "allowed_use": ["ASK", "HINT"]
    }
  ],
  "conflicts": [],
  "missing_evidence": [],
  "bundle_confidence": 0.90,
  "retrieval_trace_id": "trace_001"
}
```

`EvidenceBundle` 应明确：

- 每条证据承担什么教学角色；
- 证据来自哪里；
- 是否允许用于直接回答；
- 是否存在冲突；
- 哪些必要信息尚未找到；
- 整个证据包的置信度。

这样可以把检索、教学决策和语言生成解耦，并允许后续独立替换模型。

#### 4.2.11 引用、来源与冲突处理

Askora 的引用系统应实现：

```text
生成句子
→ Evidence ID
→ KnowledgeUnit
→ SourceChunk
→ 文档、章节、页码、段落或页面坐标
```

引用锚点必须在内容解析阶段创建，不能在回答完成后临时猜测。

来源选择原则：

- 当学习目标是理解指定材料时，以该材料为主证据；
- 外部资料只能作为补充解释、纠错或迁移材料；
- 系统生成的摘要、例题和解释不能伪装成原文；
- 同一事实存在冲突时，不能静默合并；
- 应返回冲突组、来源版本、时间和可信度；
- 用户上传材料中的指令文本一律视为数据，不能覆盖系统教学规则。

冲突处理流程：

```text
发现冲突
→ 判断是否为版本、定义范围或观点差异
→ 保留各自证据
→ 标注适用条件
→ 无法消解时向教学层声明不确定性
```

#### 4.2.12 答案泄漏控制

教学检索与普通问答最大的差异之一，是有些高相关材料不应该被提供给当前生成步骤。

建议定义答案暴露等级：

```text
L0：仅题目条件和已知事实
L1：方向性线索
L2：下一步所需知识或局部步骤
L3：关键推导结构
L4：完整解答或结论
```

教学策略引擎为每次请求指定最高允许等级。检索层必须在候选过滤、重排序和证据组合三个阶段执行限制，而不能只依靠 Prompt 告诉 LLM“不要泄漏答案”。

例如：

```text
无提示测试：只允许 L0
一级提示：最高 L1
二级提示：最高 L2
示例讲解：可允许 L3～L4，但示例不能与当前测试题同构到只需替换数字
评分阶段：Rubric 可见，参考答案对评分模型可见，对学习者输出受限
```

#### 4.2.13 缓存、增量更新与版本控制

建议设置分层缓存：

```text
查询标准化缓存
候选召回缓存
重排序缓存
EvidenceBundle 缓存
会话级 Reserve Evidence 缓存
```

缓存键至少包含：

- 材料版本；
- 索引版本；
- Embedding 模型版本；
- 重排序模型版本；
- 教学动作；
- 答案泄漏策略；
- 学习者阶段摘要。

材料更新时优先进行增量解析和局部索引重建。知识单元、引用锚点和图关系必须版本化，避免旧引用指向新内容。

学习者状态变化通常不需要重新生成底层向量，只需要重新执行过滤、重排序和证据组合。

#### 4.2.14 失败检测与降级策略

检索层必须显式识别失败，而不是始终返回看似合理的内容。

主要失败类型：

- 无结果；
- 只有低相关结果；
- 缺少必要前置证据；
- 多来源冲突；
- 引用无法定位；
- 上下文超预算；
- 检索到答案但当前禁止暴露；
- 材料中不存在用户要求的内容；
- 文档解析质量过低；
- 外部内容包含 Prompt Injection。

推荐降级顺序：

```text
精确知识单元
→ 同小节 SourceChunk
→ 上级章节
→ 知识图谱相邻概念
→ 同一知识库其他材料
→ 经用户授权的外部来源
→ 明确声明证据不足
```

低置信度时系统应降低回答确定性、缩小教学动作，或先执行诊断，而不是由 LLM 补全不存在的事实。

#### 4.2.15 可观测性与检索事件

每次检索应生成可审计轨迹：

```text
RetrievalRequested
QueryPlanned
CandidatesRetrieved
CandidatesFiltered
CandidatesReranked
EvidenceSelected
ContextCompressed
CitationVerified
RetrievalFailed
EvidenceBundleDelivered
```

建议记录：

- 各检索路线耗时；
- 候选数量；
- 过滤原因；
- 每阶段分数；
- 最终证据覆盖率；
- Token 使用量；
- 缓存命中率；
- 引用校验结果；
- 后续教学表现。

检索轨迹必须与最终学习事件关联，才能分析某种证据供给是否真正提高了学习效果。

#### 4.2.16 评估指标

检索系统不能只用回答是否流畅来评估。

**传统检索指标：**

- Recall@K；
- Precision@K；
- MRR；
- nDCG；
- 重排序胜率；
- 端到端延迟；
- 单次检索成本。

**可信性指标：**

- 引用精确率；
- 引用覆盖率；
- 无证据陈述率；
- 引用位置正确率；
- 冲突检出率；
- 低置信度识别率。

**教学专用指标：**

- 教学角色覆盖率；
- 前置知识充分率；
- 学习阶段适配率；
- 答案泄漏率；
- 上下文冗余率；
- 认知负荷超限率；
- 误区证据命中率；
- 练习与原题重复率；
- 迁移材料表面相似度与深层结构一致性。

**最终效果指标：**

- 使用该证据包后下一题的独立成功率；
- 提示依赖是否下降；
- 延迟保持是否提升；
- 迁移任务是否成功；
- 单位学习时间的掌握增益。

检索模型的离线最优不等于教学效果最优。最终应以学习结果验证检索策略。

#### 4.2.17 第一阶段工程实现

第一阶段不需要一次性实现完整 GraphRAG。建议按以下顺序落地。

**MVP：**

```text
BM25
+ 向量检索
+ 元数据过滤
+ RRF 融合
+ Cross-Encoder 重排序
+ MMR 去重
+ 引用锚点
+ EvidenceBundle
```

必须首先支持：

- 指定材料和章节范围；
- 定义、前置知识、示例和误区等知识类型；
- 教学动作感知的重排序；
- 答案泄漏等级；
- 原文引用定位；
- 检索失败显式返回；
- 完整检索轨迹。

**第二阶段：**

- 引入知识图谱邻居和多跳路径召回；
- 引入 PageIndex 长文档层级检索；
- 实现覆盖约束和 Token 背包选择；
- 建立冲突检测和来源可信度模型；
- 建立教学检索标注集。

**第三阶段：**

- 根据学习者状态动态学习重排序权重；
- 使用历史教学结果训练 Learning-to-Rank；
- 对检索路线使用 Contextual Bandit；
- 优化长期保持、独立完成和迁移结果，而不是只优化点击或即时满意度。

推荐模块边界：

```text
retrieval/
├── contracts/
│   ├── teaching_retrieval_request
│   └── evidence_bundle
├── planner/
├── retrievers/
│   ├── lexical
│   ├── dense
│   ├── graph
│   ├── page_index
│   └── assessment
├── fusion/
├── reranker/
├── selector/
├── compressor/
├── citation/
├── policy/
│   └── answer_leakage
├── evaluation/
└── observability/
```

#### 4.2.18 示例：《哥德尔、艾舍尔、巴赫》的知识供给

用户正在学习“哥德尔编码如何使形式系统能够间接谈论自身”，学习阶段为“初步建模”，教学策略选择苏格拉底追问。

检索请求：

```text
目标概念：哥德尔编码、自指
前置概念：对象语言、元语言、符号串编码
教学动作：苏格拉底追问
答案暴露上限：L1
材料范围：当前书籍相关章节
预算：1 个前置解释 + 1 个简单编码例子 + 2 个引导问题
```

系统不应直接提供不完备性证明，而应供给：

1. “把符号串映射为数字”的原文定义；
2. 一个不涉及哥德尔定理的简单编码例子；
3. 对象语言与元语言的最小区别；
4. 可引出“关于公式的陈述变成关于数字的陈述”的问题；
5. 精确章节和段落锚点。

输出给教学层的核心结构：

```text
前置事实：公式可以被唯一编码为数字
局部例子：符号序列 → 数字序列 → 单一编码
认知冲突：如果公式是数字，系统中的算术命题能否间接描述公式？
禁止内容：不直接给出对角引理和不完备性结论
```

这体现了 Askora 的检索目标：不是找到“最完整的答案”，而是找到“最适合当前学习步骤的证据”。

### 4.3 学习者建模

解决“用户当前掌握了什么”。

包括：

- BKT；
- IRT；
- DKT；
- PFA；
- Elo 评分；
- 掌握概率；
- 记忆强度；
- 提示依赖；
- 迁移能力；
- 状态置信度。

### 4.4 评估与错误诊断

解决“用户为什么错，以及当前表现是否足以证明掌握”。

包括：

- 程序化判分；
- 数学等价判断；
- 代码测试；
- Rubric 评分；
- 解题过程分析；
- 误区识别；
- 变式题；
- 延迟题；
- 迁移题。

### 4.5 教学策略选择

解决“当前应该讲解、提问、提示还是练习”。

包括：

- 状态机；
- 规则引擎；
- 加权评分；
- 决策树；
- Contextual Bandit；
- 强化学习；
- 受约束策略优化。

### 4.6 学习路径与任务调度

解决“下一步学什么，今天学什么”。

包括：

- 知识图谱拓扑排序；
- 前置依赖约束；
- 优先级队列；
- 时间背包；
- 遗忘风险排序；
- 动态路径重规划；
- 多目标优化。

### 4.7 记忆保持与复习调度

解决“什么时候复习”。

包括：

- SM-2；
- FSRS；
- Leitner；
- 半衰期回归；
- 遗忘概率模型；
- 主动回忆；
- 混合练习；
- 个性化复习调度。

### 4.8 LLM 生成、Agent 编排与可信控制

解决“如何执行并表达教学决策”。

包括：

- Prompt 模板；
- 模型路由；
- Tool Calling；
- Agent 编排；
- 输出验证；
- 引用校验；
- Guardrails；
- 日志与可观测性；
- Prompt Injection 防护。

---

## 5. DeepTutor 与 Askora 的判断

### 5.1 DeepTutor 的优势

DeepTutor 当前是成熟度较高的通用 AI 学习工作台，强项包括：

- 文档解析；
- 多种 RAG；
- 知识库；
- Book Engine；
- Chat、Quiz、Research、Solve、Visualize；
- Agent 和 Tool 框架；
- 多模型接入；
- 记忆系统；
- Mastery Path；
- 间隔复习；
- 前端、部署和工程生态。

### 5.2 DeepTutor 的主要短板

其核心短板集中在教育算法：

- 掌握度主要使用最近答题的加权正确率；
- 题目难度未充分校准；
- 提示后答对和独立答对未严格区分；
- 概念型知识较依赖 LLM 定性判断；
- 教学策略主要由 LLM 临场决定；
- 学习路径主要按模块和知识点顺序推进；
- 复习间隔主要采用固定规则；
- 延迟保持和迁移尚未成为完整硬门槛。

总体判断：

```text
DeepTutor =
优秀的知识与 Agent 基础设施
+
可用的掌握式学习闭环
+
相对基础的教育算法
```

### 5.3 Askora 的优势方向

Askora 应重点增强：

- 学习目标结构化；
- 精细学习者模型；
- 独立教学策略引擎；
- 行为证据系统；
- 提示依赖追踪；
- 动态学习路径；
- 个性化遗忘模型；
- 延迟保持门槛；
- 迁移掌握门槛；
- 学习事件溯源。

### 5.4 推荐工程路线

不建议完全从零重做 DeepTutor 已有的成熟基础设施。

更合理的方案是：

> **参考或复用成熟项目的文档、RAG、模型接入和前端能力，重新设计 Askora 的教学内核。**

优先重写：

1. 学习者模型；
2. 证据模型；
3. 教学策略引擎；
4. 动态路径规划器；
5. 复习调度器；
6. 掌握门槛；
7. 教学效果评估。

---

## 6. Askora 建议采用的算法架构

### 6.1 掌握度模型

第一阶段采用：

```text
BKT + 题目难度分级 + 证据权重
```

后续逐步引入：

- IRT；
- 个性化参数；
- 置信区间；
- 跨知识点关联更新。

不同证据使用不同权重：

```text
看答案后复述：极低
强提示后答对：低
轻提示后答对：中
无提示相似题成功：较高
延迟后独立回忆：高
陌生任务迁移成功：最高
```

### 6.2 教学策略算法

第一阶段不直接采用完整强化学习，而使用：

```text
硬规则过滤 + 状态机 + 加权评分
```

策略输入：

```text
学习目标
先备知识
掌握概率
状态置信度
内容复杂度
错误类型
提示历史
挫败信号
时间预算
```

策略输出：

```text
教学模式
提示等级
预期学习证据
退出条件
选择理由
```

积累数据后再引入：

- Contextual Bandit，用于局部个性化；
- 受约束强化学习，用于长期教学序列优化。

规则负责教学安全底线，强化学习不能自由探索所有动作。

### 6.3 动态任务优先级

任务优先级综合：

```text
目标相关性
+ 知识缺口
+ 遗忘风险
+ 前置价值
+ 截止时间紧迫度
+ 状态不确定性
- 学习成本
```

同时满足：

- 前置知识约束；
- 今日时间预算；
- 新学、复习和迁移比例；
- 认知负荷限制；
- 学习任务多样性。

### 6.4 掌握门槛

稳定掌握建议定义为：

```text
掌握概率达到阈值
AND 至少两次无提示独立成功
AND 至少一次延迟回忆成功
AND 不存在活跃稳定误区
```

迁移掌握建议定义为：

```text
稳定掌握
AND 陌生情境任务成功
AND 未使用关键提示
```

### 6.5 事件溯源

所有学习行为保存为不可变事件，例如：

```text
MaterialImported
GoalConfirmed
QuestionPresented
HintRequested
AttemptSubmitted
AnswerRevised
MisconceptionDetected
DelayedRecallCompleted
TransferTaskCompleted
ReviewCompleted
StrategyFeedbackSubmitted
```

学习者状态由事件投影计算。

收益：

- 替换算法后重算历史状态；
- 审计掌握判断；
- 回滚错误推断；
- 进行离线算法比较；
- 支持未来训练策略模型。

---

## 7. 对话气泡反馈系统

建议在每条教学气泡下设计情境化反馈入口。

### 7.1 基础入口

```text
有帮助
没理解
换种讲法
调整难度
更多
```

### 7.2 讲解反馈

```text
太抽象
信息太多
太简单
例子不合适
内容可能有误
和问题无关
```

### 7.3 练习反馈

```text
题目太难
题目太简单
题意不清
缺少条件
超出范围
题目可能有误
```

### 7.4 提示反馈

```text
提示太弱
提示太强
已经暴露答案
没有解决卡点
```

### 7.5 评分反馈

```text
评分有误
没有理解我的答案
错误原因判断不准
参考答案有问题
```

### 7.6 直接教学控制

```text
换一个例子
拆成更小步骤
先补前置知识
让我自己再试一次
直接解释
改用苏格拉底提问
提高难度
降低难度
```

### 7.7 反馈数据分类

后台应将反馈分为三类：

1. 体验反馈：表达、长度、例子和风格；
2. 教学反馈：策略、提示强度和难度；
3. 质量反馈：事实错误、题目错误和评分争议。

不能把用户点赞直接视为教学有效。

### 7.8 反馈的正确用途

显式反馈只用于提出假设，例如：

- 用户可能不适合当前抽象讲解；
- 用户可能需要更强提示；
- 当前题目可能偏难；
- 当前评分可能存在争议。

真正验证策略效果的证据仍然是：

- 下一题是否独立成功；
- 提示依赖是否下降；
- 是否能自行解释；
- 延迟后是否能回忆；
- 是否能完成迁移题。

完整信号：

```text
显式反馈
+ 即时行为反馈
+ 后续学习表现
+ 延迟保持结果
```

---

## 8. 强化学习的适用边界

强化学习的潜在收益包括：

- 学习不同用户的个体差异；
- 优化长期结果而非即时正确率；
- 自动发现复杂教学策略组合；
- 学习何时撤除提示；
- 平衡探索与利用；
- 优化多步教学序列。

主要风险是奖励函数错位。

若奖励设置为点赞、完成率、活跃度或即时正确率，系统可能学会：

- 降低难度；
- 过度提示；
- 直接给答案；
- 避免挑战；
- 追求满意而非真实学习。

建议的长期奖励重点包含：

```text
延迟保持
+ 独立完成
+ 迁移成功
- 提示依赖
- 重复误区
- 无效学习时间
```

落地顺序建议：

```text
专家规则
→ Contextual Bandit
→ 群体预训练与个人适配
→ 有限的长期强化学习
```

---

## 9. 当前阶段结论

Askora 可以在教学算法层面设计得比 DeepTutor 更严格，但当前不应声称产品整体已经优于 DeepTutor。

准确判断是：

> **DeepTutor 是更成熟的现成 AI 学习平台；Askora 应成为更强调学习成果、学习证据和教学决策的自适应教学系统。**

Askora 下一阶段不应继续优先增加更多 RAG、Agent 或模型入口，而应优先实现：

1. 统一知识点模型；
2. 学习事件模型；
3. 学习者状态模型；
4. 教学策略引擎；
5. 掌握门槛；
6. 动态任务调度；
7. 对话气泡反馈体系；
8. 延迟复习和迁移测试；
9. 算法离线评估框架。

## 10. 推荐下一步文档拆分

当前文档作为总体设计基线。进入实现阶段后，建议拆分为：

```text
docs/design/01-产品定位与学习闭环.md
docs/design/02-八类算法与技术框架.md
docs/design/03-学习者模型与证据系统.md
docs/design/04-教学策略与动态路径规划.md
docs/design/05-反馈系统与强化学习.md
docs/research/DeepTutor对比分析.md
```