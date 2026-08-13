/*
  Single source of dummy data for the TraeWork chat view replica.
  Content matches TraeWork-chat.png exactly (OCR + pixel measurement).
  mt = margin-top (px) measured from the reference screenshot.
*/

export type ChatMessage =
  | { type: "meta"; text: string; mt: number }
  | { type: "ai"; text: string; mt: number }
  | { type: "tool"; text: string; note?: string; mt: number }
  | { type: "status"; text: string; mt: number }
  | { type: "user"; text: string; mt: number }
  | { type: "user-gray"; text: string; mt: number }
  | { type: "reference"; text: string; mt: number }

export const CHAT_TASK_NAME = "上传可复用资产到 Figma"
export const CHAT_TIME = "昨天 18:45"
export const CHAT_OPEN_IN = "在 … 中打开"
export const CHAT_MODEL = "Kimi-K2.7-Code"
export const CHAT_PLACEHOLDER =
  "帮你编写代码、调试 Bug、优化性能等开发工作，交付生产级代码产物。"
export const CHAT_GENERATED_BY = "由AI生成"
export const CHAT_STOP_BTN = "手动终止输出"

export const CHAT_MESSAGES: ChatMessage[] = [
  { type: "meta", text: "已读取2个文件，搜索1次文件", mt: 21 },
  { type: "ai", text: "现在让我检查 Figma 连接状态，并读取关键的设计资产清单文件。", mt: 21 },
  { type: "tool", text: "检查 Figma MCP 连接状态并确认目标文档", mt: 17 },
  { type: "tool", text: "盘点可复用资产：SVG 图标、设计令牌、组件合约、UI Kit 预览截图", mt: 24 },
  { type: "tool", text: "在 Figma 中创建资产组织页面", note: "（Icons / Design Tokens / Components 分区）", mt: 24 },
  { type: "status", text: "任务暂停，正在处理新请求", mt: 24 },
  {
    type: "user-gray",
    text: "继续创建更多颜色样式（Brand 扩展色、代码色、强调色）和 Monospace 文本样式，并在 Design Tokens 页面创建色板展示框架。",
    mt: 46,
  },
  { type: "meta", text: "已调用8次 MCP", mt: 23 },
  { type: "status", text: "已切换到新请求", mt: 37 },
  { type: "user", text: "tokens icons components 是不是应该上传到“Assets”？", mt: 53 },
  { type: "reference", text: "TraeWork", mt: 66 },
  { type: "reference", text: "参考内容", mt: 24 },
  { type: "status", text: "思考过程", mt: 24 },
  {
    type: "ai",
    text: "好建议！让我把三个页面统一重命名为“Assets”前缀的结构，并继续构建色板展示框架。",
    mt: 19,
  },
  { type: "meta", text: "已读取1个文件，调用6次 MCP", mt: 22 },
  {
    type: "ai",
    text: "页面重命名成功！现在在 Assets - Design Tokens 页面创建色板展示 Section，并创建代码色样式、代码字体样式和 Mono 文本样式。",
    mt: 21,
  },
  { type: "meta", text: "已调用8次 MCP", mt: 23 },
  { type: "tool", text: "检查 Figma MCP 连接状态并确认目标文档 & 盘点可复用资产：SVG 图标、设计令牌、组件合约、UI Kit 预览", mt: 21 },
  { type: "tool", text: "截图 & 在 Figma 中创建资产组织页面", note: "（Assets - Tokens / Icons / Components）导入设计令牌：核心…", mt: 2 },
  { type: "status", text: "任务已手动终止", mt: 22 },
]
