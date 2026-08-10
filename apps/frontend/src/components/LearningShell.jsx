import LearningNavigation from './LearningNavigation'
import './LearningShell.css'

export default function LearningShell({ children }) {
  return (
    <div className="learning-shell">
      <LearningNavigation />
      <div className="learning-shell__content">
        {children}
      </div>
    </div>
  )
}
