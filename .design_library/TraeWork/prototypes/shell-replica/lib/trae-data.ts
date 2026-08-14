/*
  Single source of dummy data for the TraeWork home screen replica.
  Content matches the reference screenshot exactly.
*/

export const WORKSPACE_MODES = ["Work", "Code", "Design"] as const
export type WorkspaceMode = (typeof WORKSPACE_MODES)[number]

export type PrimaryAction = {
  id: string
  label: string
  icon: "new-task" | "plugins" | "automation" | "assistant" | "templates"
  shortcut?: string
}

export const PRIMARY_ACTIONS: PrimaryAction[] = [
  { id: "new-task", label: "新建任务", icon: "new-task", shortcut: "⌘^N" },
  { id: "plugins", label: "插件市场", icon: "plugins" },
  { id: "automation", label: "自动化", icon: "automation" },
  { id: "assistant", label: "办公助理", icon: "assistant" },
  { id: "templates", label: "模板库", icon: "templates" },
]

export const PINNED_ITEMS = [
  { id: "pin-1", title: "生成 Askora 学习消息系统 HTML 预览" },
]

export type TaskFolder = {
  id: string
  name: string
  defaultOpen?: boolean
  tasks: { id: string; title: string }[]
}

export const TASK_FOLDERS: TaskFolder[] = [
  {
    id: "askora",
    name: "Askora",
    defaultOpen: true,
    tasks: [
      { id: "a1", title: "上传可复用资产到 Figma" },
      { id: "a2", title: "Figma MCP 像素级复制图片" },
      { id: "a3", title: "截取 TraeWork 应用界面" },
      { id: "a4", title: "实现 Workspace-scoped Learning …" },
      { id: "a5", title: "对比 Askora 完善项目" },
      { id: "a6", title: "对比 Askora 完善项目" },
      { id: "a7", title: "提交、推送并创建 Draft PR" },
    ],
  },
  {
    id: "default",
    name: "默认",
    defaultOpen: true,
    tasks: [{ id: "d1", title: "在 TraeWork 中安装 Linear MCP" }],
  },
  {
    id: "deeptutor",
    name: "DeepTutor",
    defaultOpen: true,
    tasks: [{ id: "t1", title: "动态教学策略选择算法" }],
  },
  {
    id: "nexus",
    name: "Nexus",
    defaultOpen: true,
    tasks: [
      { id: "n1", title: "搭建设计稿项目" },
      { id: "n2", title: "无痕内衣视觉点胶机架构设计" },
      { id: "n3", title: "查看 Git 变更" },
    ],
  },
]

export type SuggestionChip = {
  id: string
  label: string
  icon: "app" | "understand" | "game" | "script"
}

export const SUGGESTION_CHIPS: SuggestionChip[] = [
  { id: "app", label: "应用开发", icon: "app" },
  { id: "understand", label: "项目理解", icon: "understand" },
  { id: "game", label: "游戏创意", icon: "game" },
  { id: "script", label: "工具脚本", icon: "script" },
]

export const MODEL_NAME = "Kimi-K2.7-Code"
export const ENVIRONMENT_NAME = "本地"
export const PROJECT_NAME = "Askora"
export const COMPOSER_PLACEHOLDER =
  "帮你编写代码、调试 Bug、优化性能等开发工作，交付生产级代码产物。"
