# Library 审查 · 六报告合并问题清单（待确认稿）

- **来源**：00g(40 条) / 00seed(47 条) / 004F(29 节) / 004p(25 条) / 00st(41 条) / 00sp(20 条)，原始共 **202 条**
- **合并后**：**93 个唯一问题**（同报告内重复、跨报告重复均已折叠）
- **已核验 16 个**：✅ 属实 11 / ⚠️ 部分属实 1 / ❌ 误报 4
- **待核验**：77 个
- **报告代号**：G=00g、S=00seed、F=004F、P=004p、T=00st、X=00sp；括号内为该报告定级
- **类型**：【实】= 可客观核验（数值/DOM/路由/选择器）；【判】= 设计判断（核验只能确认其事实基础，真值依赖审美标准）

---

## 一、功能 / 路由（7）

| ID | 问题 | 位置 | 报告分布 | 类型 | 已核验 |
|----|------|------|----------|------|--------|
| J1 | "打开原文"指向不存在路由，点击 404 | Library.jsx:770 | F(P0) | 实 | ✅ 属实（后端无此路由） |
| J2 | 分页仅前后翻页，无首页/末页/跳转/总数 | Library.jsx:961-971 | G(P2)·X(P2) | 实 | ✅ 属实 |
| J3 | 主/子页面布局不一致 | 主页面 vs 工作区子页面 | P(P1) | 判 | ❌ 误报（基于认错窗口的截图） |
| J4 | 标签/集合仅有原生 select，无 Tags UI | Library 批量栏 | F(P2) | 实 | |
| J5 | 归档视图无独立入口 | Library | F(P2) | 实 | |
| J6 | 拖拽上传层 fixed inset:12px 覆盖 sidebar | Library.css:999-1009 | X(P2) | 实 | ✅ 属实 |
| J7 | 无键盘快捷键（仅 Esc） | 全页面 | G(P2) | 实 | |

## 二、按钮（5）

| ID | 问题 | 位置 | 报告分布 | 类型 | 已核验 |
|----|------|------|----------|------|--------|
| B1 | 两套按钮/设计系统并存（40px vs 32px） | global.css:208 vs ds.css:8 | S(P0×2)·F(P1)·X(P1)·G(P2) | 实 | ✅ 属实 |
| B2 | 按钮全系缺 :active（含 a.button 选择器失效） | global.css:206-259 | T(P1)·T(P2) | 实 | ✅ 属实（全前端仅 1 处 :active） |
| B3 | 归档/取消按钮权重不足，破坏性未区分 | Library.jsx:746-754, 989-994 | T(P2)·G(P2×2)·P(P2×2) | 判 | |
| B4 | 点击目标过小（分页 28px/关闭 32px/checkbox 15×15） | Library.css:935, 437, 347 | T(P1)·G(P1×3)·S(P2) | 实 | |
| B5 | 按钮高度 5 种变体无尺寸体系 | 全局 | T(P2) | 实 | |

## 三、输入控件（8）

| ID | 问题 | 位置 | 报告分布 | 类型 | 已核验 |
|----|------|------|----------|------|--------|
| D1 | checkbox 默认 opacity:0，可发现性差 | Library.css:336 | T(P0)·G(P1)·F(P1)·X(P1)·P(P2) | 实 | ✅ 属实（定级 P0~P2 分歧） |
| D2 | 原生 select 未定制（箭头/弹出层暗色冲突） | Library.css:59 + MaterialDestination | T(P1)·G(P1)·F(P2×2)·S(P2)·P(P3) | 实 | |
| D3 | 工具栏控件高度/圆角不统一（34/36/40px、8/9px） | Library.css:60, 89, 107, 979 | S(P1×3)·X(P1)·P(P2)·T(P2) | 实 | ✅ 属实 |
| D4 | 搜索 Enter 提交 vs 筛选即时生效；无清除按钮 | Library.jsx:851-861 | T(P1)·G(P2)·X(P2)·P(P3) | 实 | ✅ 属实 |
| D5 | disabled 仅 cursor/opacity 变化 | global.css + MaterialDestination | T(P2)·G(P3) | 实 | |
| D6 | 元数据编辑器 input border transparent | Library.css:846-851 | G(P2) | 实 | |
| D7 | 搜索图标位置/重心偏差（两份报告说法矛盾） | Library.css:73, 78-95 | T(P3)·S(P2) | 实 | |
| D8 | 批量栏无单项清除快捷 | Library.jsx:979 | G(P3) | 实 | |

## 四、Typography（9）

| ID | 问题 | 位置 | 报告分布 | 类型 | 已核验 |
|----|------|------|----------|------|--------|
| A1 | 字号档位过多无 type scale | Library.css 全文件 | T(P1)·G(P2)·F(P2×2)·P(P2) | 实 | ✅ 属实（实测 15 档，报告写 13 档） |
| A2 | font-weight 650 非标准字重 | Library.css:274, 680 | T(P2)·G(P2)·P(P2) | 实 | ✅ 属实 |
| A3 | KPI 26px 过大/层级倒置（>标题 18px） | Library.css:550 vs 423 | X(P2)·F(P3)·T(P3)·S(P3) | 实 | ✅ 属实 |
| A4 | 页面标题↔副标题层级跳跃 | Library.jsx:804-806, L25 | S(P2)·P(P2) | 判 | |
| A5 | secondary/muted 混用无规则 | Library.css 多处 | T(P2) | 实 | |
| A6 | `<small>` 叠加缩小至约 9.2px | Library.jsx:599, 953 | T(P2) | 实 | |
| A7 | 模态框标题 18px 层级偏弱 | Library.css:423 | P(P3) | 判 | |
| A8 | relation h3 全大写+字距，与中文风格不统一 | Library.css:701 | S(P2) | 判 | |
| A9 | Loading `<p>` 无 typography 规范 | Library.jsx:530 | S(P3) | 判 | |

## 五、图标 / 徽章（5）

| ID | 问题 | 位置 | 报告分布 | 类型 | 已核验 |
|----|------|------|----------|------|--------|
| C1 | 文件徽章：比例失真(28×34/44×52)+9px 小字+纯文字 | Library.css:245-259, 409-413 | X(P2)·F(P2)·S(P1)·P(P2)·G(P3) | 实 | |
| C2 | 图标尺寸 9 种未规范为 3 档 | Library.jsx 全文件 | T(P2) | 实 | |
| C3 | 空态图标尺寸不一/偏隐 | Library.jsx:884, 892 等 | X(P3)·G(P3)·S(P3×2) | 实 | |
| C4 | 图标与文字基线未视觉对齐 | global.css:210 | T(P3) | 判 | |
| C5 | Network 图标语义不匹配 | Library.jsx:556 | S(P2) | 判 | |

## 六、间距 / 对齐（8）

| ID | 问题 | 位置 | 报告分布 | 类型 | 已核验 |
|----|------|------|----------|------|--------|
| E1 | 间距值 20+ 种，违反 8pt/4pt 栅格 | 全文件 | T(P1)·P(P2)·X(P2)·S(P3)·G(P2) | 实 | |
| E2 | modal scroll 顶部 padding 仅 2px | Library.css:462-470 | T(P2)·S(P2)·P(P2)·G(P2) | 实 | |
| E3 | dt 固定 52px 宽度 | Library.css:571-596 | T(P3)·F(P3) | 实 | |
| E4 | KPI strip gap 32px 过疏 | Library.css:534-541 | G(P3)·S(P3) | 判 | |
| E5 | 卡片 148px/描述 32px min-height 魔数 | Library.css:218-231, 291-300 | G(P3)·P(P2) | 实 | |
| E6 | modal header 基线不齐 / 5vh 贴顶 | Library.css:358-369, 400-435 | T(P3)·G(P3) | 判 | |
| E7 | 分页器间距不稳 | Library.css pagination | F(P3) | 判 | |
| E8 | section 间距无统一规则 | 全局 | T(P3) | 判 | |

## 七、容器 / 视觉层级（3）

| ID | 问题 | 位置 | 报告分布 | 类型 | 已核验 |
|----|------|------|----------|------|--------|
| F1 | modal 内多区块同背景色，语义区隔消失 | Library.css:473-530 | T(P1×2)·G(P2×3)·S(P1)·P(P1) | 判 | |
| F2 | banner 状态信息冗余/同屏重复 | Library.jsx:683-689, 710-714 | G(P2)·F(P2)·X(P2) | 实 | |
| F3 | 关系强度 pill 比容器还暗 | Library.css:720, 743 | G(P2) | 实 | |

## 八、弹窗 / 浮层（10）

| ID | 问题 | 位置 | 报告分布 | 类型 | 已核验 |
|----|------|------|----------|------|--------|
| G1 | 两弹窗遮罩一暗一亮互斥 | Library.css:366 vs MaterialDestination.css:8 | T(P0)·G(P1)·F(P2×2)·S(P2)·X(P2) | 实 | ⚠️ 属实但引用不精确（实为 text-primary 32%，非 white 32%） |
| G2 | z-index 无体系（16 处 0~1100） | 全站 CSS | T(P2)·G(P2)·S(P2)·X(P2) | 实 | ✅ 属实 |
| G3 | 详情弹窗缺 focus trap | Library.jsx:362-376 | T(P1)·G(P1) | 实 | |
| G4 | 去向弹窗缺 X 关闭按钮 | MaterialDestination.jsx:223 | T(P1) | 实 | |
| G5 | footer 硬分割/无渐变/按钮溢出风险 | Library.css:491-499 | T(P3)·P(P2)·S(P2)·F(P2) | 实 | |
| G6 | backdrop blur(3px)：G 说感知弱、S 说性能差（角度相反） | Library.css:358-367 | G(P2)·S(P3) | 判 | |
| G7 | 两弹窗垂直对齐策略不同 | Library.css vs MaterialDestination.css | G(P2) | 实 | |
| G8 | 遮罩点击关闭无视觉提示 | Library.jsx:652-654 | P(P2) | 实 | |
| G9 | batch bar 遮挡卡片/移动端 sticky 失效 | Library.css:942-958 | P(P2)·S(P2) | 实 | |
| G10 | 弹窗动画 ease-out 缺弹性曲线 | Library.css:389-398 | P(P3) | 判 | |

## 九、状态反馈（10）

| ID | 问题 | 位置 | 报告分布 | 类型 | 已核验 |
|----|------|------|----------|------|--------|
| H1 | status-pill 多套定义/命名/padding 不一 | global.css:276-315 vs Library.css:872-921 | G(P2)·P(P2)·S(P2)·X(P2)·T(P2) | 实 | |
| H2 | pill 对比度：muted 4.7:1 边界 / success<3:1 | Library.css:873, 911 | S(P2)·S(P1) | 实 | |
| H3 | 卡片 hover 反馈过弱（#242424→#252525） | Library.css:195-207 | G(P2)·S(P2) | 实 | |
| H4 | is-open 选中态不明显（ring 弱/被覆盖/被遮挡） | Library.css:203-216 | T(P2)·G(P2)·F(P2)·G(P3) | 实 | |
| H5 | 知识列表选中指示弱（2px 竖线+空心圆点） | Library.css:632-668 | X(P2)·P(P3) | 实 | |
| H6 | 加载/刷新反馈不足（footer 跳变/无骨架/静默/spinner 线性） | Library.jsx:526-559, 274-282, 830 | T(P2×2)·G(P2)·G(P3)·T(P3) | 实 | |
| H7 | 空态设计（虚线边框/图标比例/无匹配引导/两空态不一） | Library.css:122-135 | P(P2)·F(P3)·T(P3)·S(P3) | 判 | |
| H8 | announcer 显隐致布局跳动 | Library.css:36-42 | X(P3) | 实 | |
| H9 | 过渡 0.12-0.18s 偏快 | Library.css:200 | G(P3) | 判 | |
| H10 | check hover 过渡与卡片不同步 | Library.css:322 | S(P3) | 实 | |

## 十、可访问性（13）

| ID | 问题 | 位置 | 报告分布 | 类型 | 已核验 |
|----|------|------|----------|------|--------|
| I1 | "label+input 嵌套在 button 内，HTML 语义错误" | Library.jsx:923-955 | S(P0) | 实 | ❌ 误报（label 与 button 为兄弟节点） |
| I2 | "checkbox 与卡片按钮事件冒泡冲突" | Library.jsx:919-956 | X(P1) | 实 | ❌ 误报（无冒泡路径） |
| I3 | "键盘 Tab 至 checkbox 无视觉反馈" | Library.css:324-345 | T(P0) | 实 | ❌ 误报（:focus-within→opacity:1 已覆盖） |
| I4 | 知识列表键盘导航缺失/focus-ring 圆角错位 | Library.css:637-658 | T(P2)·P(P2) | 实 | |
| I5 | details/summary：focus 重叠/兼容性/动画不一致/SR 忽略 | Library.css:797-828 + Library.jsx:732 | T(P2)·X(P3)·S(P3)·G(P2)·F(P2) | 实 | |
| I6 | 拖拽 a11y（浮层 aria-hidden/无 aria-label） | Library.jsx:999-1004 | T(P2)·G(P3) | 实 | |
| I7 | label 嵌套 checkbox，VoiceOver 关联不稳 | Library.jsx:923-930 | T(P2) | 实（需运行时） | |
| I8 | 状态变化无 aria-live / 混用 role=alert | Library.jsx:828, 949-953 | G(P2)·S(P3) | 实 | |
| I9 | 卡片 button focus ring 对比度不足 | Library.css:233 | S(P2) | 实 | |
| I10 | 文件 input 键盘可达性 | Library.jsx:808 | S(P2) | 实 | |
| I11 | checkbox aria-label 过长 | Library.jsx:923 | S(P3) | 判 | |
| I12 | Sidebar tabs 缺 aria-controls | Sidebar.jsx:150 | S(P2) | 实 | |
| I13 | focus-within 时 badge 颜色未同步 | Library.css:261 | S(P3) | 实 | |

## 十一、一致性 / 设计系统（5）

| ID | 问题 | 位置 | 报告分布 | 类型 | 已核验 |
|----|------|------|----------|------|--------|
| K1 | 圆角值 11 种无 token | 全站 | X(P2)·S(P2) | 实 | |
| K2 | --border == --surface-container（#2c2c2c），边框不可见 | global.css:21 | S(P1) | 实 | |
| K3 | 通用组件样式散落在页面 CSS | Library.css | S(P1) | 判 | |
| K4 | color-mix() 旧版浏览器不支持 | Library.css 多处 | S(P3) | 实 | |
| K5 | .surface 样式重复定义 | MaterialDestination.jsx:156 + .css:11-19 | X(P3) | 实 | |

## 十二、响应式 / 布局（3）

| ID | 问题 | 位置 | 报告分布 | 类型 | 已核验 |
|----|------|------|----------|------|--------|
| R1 | grid minmax(270px) 宽屏拉伸/单行空白 | Library.css:186 | F(P2)·P(P2) | 判 | |
| R2 | 1100px 断点基于视口/中宽度体验差 | Library.css:1047-1051 | G(P2)·F(P3) | 实 | |
| R3 | 右栏隐藏时中栏与 sidebar 间距缓冲 | AppShell.css:68 | S(P2) | 判 | |

## 十三、子页面 BookLearningLaunch 等（7）

| ID | 问题 | 位置 | 报告分布 | 类型 | 已核验 |
|----|------|------|----------|------|--------|
| SUB1 | 按钮 40px vs 44px 混用 | BookLearningLaunch.jsx | F(P2) | 实 | |
| SUB2 | 进度条连线视觉不完整 | BookLearningLaunch.css | F(P3) | 实 | |
| SUB3 | 技术详情暴露 provider/model/prompt_version 等实现细节 | BookLearningLaunch.jsx | F(P2) | 实 | |
| SUB4 | RichMessage 懒加载致文本闪烁 | BookLearningLaunch.jsx:429 | F(P3) | 实 | |
| SUB5 | radio 原生样式未定制 | BookLearningLaunch.jsx:480 | F(P3) | 实 | |
| SUB6 | learning-step box-shadow 深色下不可见 | BookLearningLaunch.css:116-123 | G(P3) | 实 | |
| SUB7 | 返回链接用 brand 紫色，语义不符 | BookLearningLaunch.css:22-31 | G(P3) | 判 | |

---

## 附录：报告自认无效条目（不计入核验）

- **00seed M2**："弹窗缺少 role=\"dialog\""——报告原文自认"已在 L656 提供，属冗余检查"，列为问题但实质无效。

## 合并时发现的定级分歧（核验时按事实统一裁定）

| 问题 | 定级跨度 |
|------|----------|
| D1 checkbox 隐藏 | T=P0 vs G/F/X=P1 vs P=P2 |
| G1 遮罩互斥 | T=P0 vs G=P1 vs F/S/X=P2 |
| D2 原生 select | T/G=P1 vs F/S=P2 vs P=P3 |
| C1 文件徽章 | S=P1 vs X/F/P=P2 vs G=P3 |
