import { BookOpen } from 'lucide-react'
import { useWorkspace } from '../components/WorkspaceContext'
import Alert from '../components/ui/Alert'
import './LearningWorkspace.css'

export default function LearningWorkspace() {
  const workspace = useWorkspace()
  const current = workspace?.current_workspace

  return (
    <div className="learning-canvas" data-workspace-id={current?.workspace_id}>
      <header className="learning-canvas__header">
        <div className="learning-canvas__title">
          <h1>课程</h1>
          <span className="learning-canvas__workspace">
            {current ? current.display_name : '正在读取当前课程…'}
          </span>
        </div>
      </header>
      <section className="learning-canvas__empty" aria-labelledby="learning-canvas-empty-title">
        <BookOpen size={28} aria-hidden="true" />
        <h2 id="learning-canvas-empty-title">从当前学习活动继续</h2>
        <p>学习画布不会自行创建会话、目标或计划。没有可恢复的 LearningActivity 时保持在课程上下文。</p>
        <Alert tone="info" title="当前没有可恢复的学习活动">
          不会从前端生成占位活动或会话。
        </Alert>
      </section>
    </div>
  )
}
