# Askora 前端

> 状态：Web-first / Web-only 开发阶段

`apps/frontend` 包含 React/Vite 前端。当前开发路径为 Web-only。

## 目录

- `src/`：页面、组件、hooks 和 API client；

## Web 开发

先启动后端，再执行：

```bash
npm ci
npm run dev
```

默认页面是 `http://127.0.0.1:5173`，默认 API 是 `http://127.0.0.1:8000/api/v1`。

当前 canonical routes：

- `/today`：Today Workspace 只读聚合与兼容快速学习入口；
- `/library`：current-user 资料、处理状态、范围化知识候选与 SourceSpan 原文检查器；
- `/quick/:sessionId`：明确标记的兼容导师工作台；
- `/learn/:activityId`：在 canonical activity/session link 缺失时保持不可启动；
- `/history`、`/settings`：历史与本地运行/退出边界；
- `/goals`、`/path`、`/evidence`：等待后续独立 Vertical Slice 的诚实不可用页面。

## 验证

```bash
npm ci
npm test -- --run
npm run build
npm audit --audit-level=high
```

Vitest 覆盖路由、认证边界、Today、资料库处理状态联动/上传/删除/审计展示、兼容工作台、History、Settings 与 responsive drawer 键盘焦点；`npm run build` 仍只表示生产构建通过，不能替代行为与真实页面验收。

## API 与认证边界

- 登录、刷新和登出使用 `/api/v1/auth`；
- 对话通过 `/api/v1/dialog` 和 WebSocket transport 进入后端 canonical facade；
- Today 通过 `/api/v1/workspace/today` 聚合 owner-published 只读状态；
- Library 通过 `/api/v1/workspace/library` 与 `/api/v1/workspace/knowledge-map` 读取 SYS01 current revision，不读取或展示本地存储路径；
- 前端展示的 mastery/progress 必须使用后端返回的来源标记，不得自行推导 canonical learner state；
- compatibility session 不等于 LearningActivity，不得混用 session/activity identity；
- 演示或开发认证只能在后端明确授权的本地开发配置下使用，不能把前端 fallback 当成认证成功。