# 对话学习（`Chat`，**退役页**）

> **页面职责**：**无**。该 legacy 页面已不被 `App.jsx` 引用（不可达），其功能已被「空间内对话」（`LearningActivity`）取代。
> **对应契约**：`EXP-IA-004`（Chat 不是产品域）、`UI-NAV-004`（Chat 不是导航）、`UI-ROUTE-004`（legacy 清理）
> **现状基准**：`apps/frontend/src/pages/Chat.jsx`（legacy，整体为旧版 Chat UI，不可达）

---

## 1. 处置决定

本页面属于已冻结规范明确禁止的 Chat 形态，且已不可达。**建议退役：删除组件与路由引用；不为其做元素规划。** 若因历史 deep-link 仍需保留兼容，仅允许作为 `UI-ROUTE-002` 兼容跳板（跳到对应空间的真实对话），不得恢复其界面。

以下按「退役清单」记录现有元素，供删除/迁移确认，不作为继续实现的规格。

## 2. 现有元素（退役清单）

| 类别 | 现有元素 | 违反契约 | 处置 |
|---|---|---|---|
| 标题 | H1「对话学习」；副标题「通过苏格拉底式提问，引导你主动思考」 | Chat 作为产品心智（`EXP-IA-004`） | 删除；「对话」语义由空间内 LearningActivity 承担 |
| 学科选择 | 学科卡片（数学/语文/英语/物理 + emoji 📐📚🌍⚛️） | 固定学科列表 ≠ 用户资料；无依据学习 | 删除 |
| 对话列表 | 「选择学科开始学习」「最近对话」「新对话」（Plus） | Chat thread manager（`UI-NAV-004`） | 删除；已有对话列表由 Sidebar/Welcome 承担 |
| AI 昵称 | 头像「苏」 | 伪造教师人格 | 删除；教学角色用「Askora」中性表达 |
| 输入 | textarea placeholder「输入你的想法...」aria「对话输入」 | 无 LearningActivity 上下文 | 删除 |
| 发送 | 发送按钮（Send，aria「发送消息」） | — | 删除 |
| 状态 | 「暂无历史对话」「历史会话加载失败」「创建会话失败」「消息发送失败」「这个会话已经结束，请新建会话后继续。」 | 轮次/会话即学习（`LEXP-001`） | 迁移到空间对话的对应诚实状态 |

## 3. 替代规划（若其用户 job 仍需满足）

用户「想开聊」的需求，由以下正式路径承接（均已有规划文档）：

1. 上传/选择资料 → `MaterialDestination`「马上开始学习」→ 空间首段对话（material-destination.md / activity-learning.md）。
2. 对已有空间「继续学习」→ 新开对话（learning-workspace.md）。
3. 恢复已有对话 → Sidebar/Welcome 的已有对话行（sidebar.md / welcome.md）。

## 4. 禁止事项

- 恢复「对话学习」为一级导航或默认目的地（`UI-NAV-004`）。
- 用学科卡片/固定知识点列表引导无依据学习。
- 用 Chat 1/2/3 或轮次计数组织对话（`EXP-WSP-005`）。
- 为保留 Chat 界面而新增第二 transcript/Activity truth（`UI-LRN-002`）。
