# Askora 前端与 macOS 桌面壳

> 状态：当前开发、构建与打包说明

`apps/frontend` 包含 React/Vite 前端和 Electron 桌面进程。Web 与桌面版复用 `src/`；Electron 负责本地后端生命周期、窗口和应用资源装配。

## 目录

- `src/`：页面、组件、hooks 和 API client；
- `electron/`：Electron main/preload 与本地后端启动；
- `assets/`：桌面图标和签名配置；
- `resources/backend/`：`backend:build` 生成或更新的桌面后端资源目录；
- `build-backend.sh`：使用后端虚拟环境和 PyInstaller 构建桌面后端；
- `release/`：本地打包产物，不是源代码或项目说明。

## Web 开发

先启动后端，再执行：

```bash
npm ci
npm run dev
```

默认页面是 `http://127.0.0.1:5173`，默认 API 是 `http://127.0.0.1:8000/api/v1`。

## 验证

```bash
npm ci
npm run build
npm audit --audit-level=high
```

项目当前没有独立的前端 lint/test script；不能把 `npm run build` 描述为完整的前端行为测试。

## Electron 开发与打包

```bash
npm run electron:dev
npm run backend:build
npm run electron:build:mac
```

一次性构建前端、后端资源和 macOS 安装包：

```bash
npm run electron:build:mac:with-backend
```

`electron-builder` 当前配置了 hardened runtime，但 `notarize` 默认为 `false`。因此本地生成的 DMG/ZIP 不能自动等同于已签名、已公证、可公开分发的软件。

## API 与认证边界

- 登录、刷新和登出使用 `/api/v1/auth`；
- 对话通过 `/api/v1/dialog` 和 WebSocket transport 进入后端 canonical facade；
- 前端展示的 mastery/progress 必须使用后端返回的来源标记，不得自行推导 canonical learner state；
- 演示或开发认证只能在后端明确授权的本地开发配置下使用，不能把前端 fallback 当成认证成功。
