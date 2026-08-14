# 学习（`/learning`，**重定向占位页**）

> **页面职责**：**无 UI**。纯路由重定向：`/learning` → `/learning/goals`（兼容旧 deep-link）。
> **对应契约**：`UI-ROUTE-002`（兼容跳板）、`EXP-IA-001`
> **现状基准**：`apps/frontend/src/pages/Learning.jsx`（纯 `navigate('/learning/goals')`，无渲染）

---

## 1. 处置决定

保持现状：`Learning.jsx` 仅执行重定向，不渲染任何可见 UI、不显示 loading 文案。

## 2. 路由映射

| 原路由 | 跳转目标 | 说明 |
|---|---|---|
| `/learning` | `/learning/goals` | 兼容跳板；避免空白落地 |

## 3. 禁止事项

- 在此页添加任何可见 UI、说明文字或 loading（无意义中间态）。
- 恢复「学习」为 L0 心智（`EXP-IA-001`）。
