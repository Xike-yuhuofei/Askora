# Askora Mac App Electron 打包方案

## 一、项目现状分析

### 当前技术栈
| 层级 | 技术 | 版本 |
|------|------|------|
| 前端框架 | React | 18.3.1 |
| 构建工具 | Vite | 5.3.5 |
| 路由 | React Router DOM | 6.26.0 |
| HTTP 客户端 | Axios | 1.7.2 |
| 图标库 | Lucide React | 0.424.0 |
| 后端 | FastAPI (Python) | Docker 运行中 |

### 当前前端架构
- `index.html` — 入口 HTML，含内联样式（CSS Variables 主题）
- `src/main.jsx` — React 应用入口，使用 BrowserRouter
- `src/App.jsx` — 路由配置（Login / Chat / Profile / Knowledge / Account）
- `src/api/client.js` — Axios 实例，baseURL 为 `/api/v1`，开发态通过 Vite proxy 转发到 `localhost:8000`
- `src/hooks/useAuth.jsx` — 认证管理，localStorage 存储 token
- `src/components/` — Sidebar, NoticeModal, ProtectedRoute
- `src/pages/` — Chat, Login, Profile, Knowledge, Account

### 关键约束
1. `package.json` 已声明 `"type": "module"`，Electron 主进程必须使用 `.cjs`（CommonJS）格式
2. 项目无 `.gitignore`，需要创建
3. API baseURL 为相对路径 `/api/v1`，生产打包后需切换为绝对 URL
4. 当前前端无打包配置，需要从零搭建

---

## 二、实施步骤

### Step 1：创建 Electron 主进程文件

#### 1.1 `apps/frontend/electron/main.cjs`
Electron 主进程入口，负责：
- 创建主窗口（BrowserWindow）
- 加载 React 前端（开发态：Vite dev server；生产态：`dist/index.html`）
- 安全配置（webPreferences, contextIsolation, nodeIntegration: false）
- 开发/生产模式切换
- 窗口生命周期管理
- 应用菜单（Cmd+Q 退出, Cmd+R 刷新, DevTools）
- 进程间通信（IPC）

```
核心配置：
- width: 1200, height: 800
- minWidth: 960, minHeight: 600
- webPreferences: {
    contextIsolation: true,
    nodeIntegration: false,
    preload: path.join(__dirname, 'preload.cjs'),
    webSecurity: false  // 生产态可改为 true 配合 webRequest
  }
```

#### 1.2 `apps/frontend/electron/preload.cjs`
Preload 安全桥接脚本，暴露有限 API 给渲染进程：
- `window.electronAPI.getPlatform()` — 获取当前平台
- `window.electronAPI.getAppVersion()` — 获取应用版本
- 后续可扩展：文件选择、原生对话框等

#### 1.3 `apps/frontend/electron/app-menu.cjs`
应用菜单配置：
- 应用菜单（关于 Askora, 偏好设置, 退出）
- 编辑菜单（撤销, 重做, 剪切, 复制, 粘贴）
- 视图菜单（刷新, 全屏, 开发者工具）
- 窗口菜单（最小化, 缩放, 置前）

---

### Step 2：更新 package.json

#### 2.1 添加依赖
```devDependencies:
- electron ^33.0.0
- electron-builder ^25.0.0
```

#### 2.2 添加脚本
```json
"scripts": {
  "dev": "vite",                          // 现有开发命令
  "build": "vite build",                  // 现有构建命令
  "preview": "vite preview",              // 现有预览命令
  "electron:dev": "electron .",           // 开发模式：加载 Vite dev server
  "electron:build": "npm run build && electron-builder",  // 打包 Mac App
  "electron:build:mac": "npm run build && electron-builder --mac"  // 仅打 macOS
}
```

#### 2.3 添加 Electron 配置段
```json
"main": "electron/main.cjs",
"build": {
  "appId": "com.askora.mac-client",
  "productName": "Askora",
  "files": [
    "electron/**/*",
    "dist/**/*",
    "package.json"
  ],
  "directories": {
    "output": "release",
    "buildResources": "assets"
  },
  "mac": {
    "target": ["dmg", "zip"],
    "category": "public.app-category.education",
    "icon": "assets/icon.icns",
    "hardenedRuntime": false,
    "gatekeeperAssess": false
  },
  "dmg": {
    "contents": [
      { "x": 130, "y": 220 },
      { "x": 410, "y": 220, "type": "link", "path": "/Applications" }
    ],
    "format": "UDRW"
  }
}
```

---

### Step 3：修改 Vite 配置

#### 3.1 `vite.config.js` 更新
添加 `base` 配置和 Electron 兼容处理：
```javascript
export default defineConfig({
  base: './',  // 使用相对路径，支持 file:// 协议加载
  plugins: [react()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: { ... }
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true
  }
})
```

#### 3.2 关键改动说明
- `base: './'` — 确保打包后静态资源使用相对路径，Electron 通过 `file://` 协议加载时能正确找到资源
- 无需新增插件，保持现有 Vite 配置简洁

---

### Step 4：修改 API 客户端

#### 4.1 `src/api/client.js` 更新
添加生产环境 API Base URL 支持：
```javascript
const getBaseURL = () => {
  // 生产环境：读取 VITE_API_BASE_URL 环境变量，默认指向云端 API
  // 开发环境：使用相对路径，走 Vite proxy
  if (import.meta.env.PROD) {
    return import.meta.env.VITE_API_BASE_URL || 'https://api.askora.com/api/v1'
  }
  return '/api/v1'
}

const api = axios.create({
  baseURL: getBaseURL(),
  timeout: 30000,
})
```

#### 4.2 环境变量
在 `apps/frontend/` 下创建 `.env.production`：
```
VITE_API_BASE_URL=https://api.askora.com/api/v1
```

---

### Step 5：创建资源文件

#### 5.1 创建 `.gitignore`
```
node_modules/
dist/
release/
.DS_Store
.env
.env.local
*.log
```

#### 5.2 创建图标占位
- `assets/icon.png` — 1024x1024 源图标
- `assets/icon.icns` — macOS 图标（从 png 转换）

> 注：首次实施可暂用占位图标，后续替换正式品牌图标。图标生成命令：
> `iconutil -c icns assets/icon.iconset`（需先准备 iconset 目录）

---

### Step 6：本地验证流程

#### 6.1 开发模式验证
```bash
cd apps/frontend
npm install
npm run electron:dev
```
验证点：
- [ ] Electron 窗口正常打开
- [ ] 前端页面正常加载（Vite dev server）
- [ ] API 请求正确转发到后端（localhost:8000）
- [ ] 登录/对话功能正常

#### 6.2 生产构建验证
```bash
cd apps/frontend
npm run electron:build:mac
```
验证点：
- [ ] `release/` 目录生成 `.app` 和 `.dmg`
- [ ] 双击 `.app` 正常打开
- [ ] 通过 `file://` 协议加载页面正常
- [ ] API 请求连接到正确的后端 URL
- [ ] 无 "无法打开" 警告（首次可忽略 notarization）

---

## 三、文件变更清单

| 操作 | 文件路径 | 说明 |
|------|----------|------|
| **新建** | `apps/frontend/electron/main.cjs` | Electron 主进程 |
| **新建** | `apps/frontend/electron/preload.cjs` | Preload 安全桥接 |
| **新建** | `apps/frontend/electron/app-menu.cjs` | 应用菜单配置 |
| **新建** | `apps/frontend/.gitignore` | Git 忽略规则 |
| **新建** | `apps/frontend/.env.production` | 生产环境变量 |
| **新建** | `apps/frontend/assets/icon.png` | 应用图标（占位） |
| **新建** | `apps/frontend/assets/icon.icns` | macOS 图标（占位） |
| **修改** | `apps/frontend/package.json` | 添加 Electron 依赖、脚本、build 配置 |
| **修改** | `apps/frontend/vite.config.js` | 添加 `base: './'` |
| **修改** | `apps/frontend/src/api/client.js` | 支持环境变量 API Base URL |

---

## 四、风险与应对

| 风险 | 影响 | 应对方案 |
|------|------|----------|
| **API 跨域问题** | 生产态 Electron 加载 `file://` 协议，请求远程 API 会触发 CORS | 方案 A：主进程启用 `webSecurity: false`（MVP 快速方案）；方案 B：主进程内建立 HTTP 代理转发 |
| **模块系统冲突** | `"type": "module"` 导致 Electron 主进程 `require` 报错 | 主进程/Preload 使用 `.cjs` 扩展名 |
| **图标格式问题** | `.icns` 生成不当导致打包失败 | 首次实施用在线工具生成标准 icns，或从配置中临时移除 icon 字段 |
| **ELECTRON_MIRROR 不稳定** | 国内网络下载 Electron 二进制缓慢 | 配置镜像：`ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/` |
| **本地后端未启动** | 开发模式下 API 不可用 | 已实现 Demo 模式降级（登录失败自动使用演示账号） |
| **文件协议加载问题** | 打包后 `file://` 加载 React Router 可能出现白屏 | `vite.config.js` 设置 `base: './'`；history fallback 需处理（可在 main.cjs 中拦截未匹配路径重定向到 index.html） |

---

## 五、后续扩展方向（非本次实施范围）

1. **本地后端打包**：使用 PyInstaller 将 FastAPI 打包为二进制，Electron 主进程以子进程方式启动
2. **自动更新**：集成 electron-updater 实现版本检测和热更新
3. **系统托盘**：最小化到菜单栏，支持快速唤起
4. **快捷键绑定**：Cmd+K 打开对话、Cmd+N 新建会话
5. **Notarization**：Apple 公证，消除首次打开警告
6. **CI/CD**：GitHub Actions 自动构建与发布
7. **Windows 支持**：同一套代码通过 electron-builder 生成 `.exe`/`.msi`
