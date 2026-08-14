import './LearningShell.css'

// LearningShell 仅作为学习域内容的上下文容器。
// 常驻分面导航（目标/路径/进展/历史）因违反 EXP-IA-003 / UI-NAV-003 已移除；
// 这些页面仅作为兼容/上下文入口可达，由页面内部提供上下文入口。
export default function LearningShell({ children }) {
  return (
    <div className="learning-shell">
      <div className="learning-shell__content">
        {children}
      </div>
    </div>
  )
}